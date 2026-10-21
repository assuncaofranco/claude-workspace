import json

def req(name, method, url, body=None, test='', auth=None, pre=''):
    h = [{'key': 'Content-Type', 'value': 'application/json'}] if body is not None else []
    if auth == 'bo': h.append({'key': 'Authorization', 'value': 'Bearer {{BO_access_token}}'})
    if auth == 'gw': h.append({'key': 'Authorization', 'value': 'Bearer {{access_token}}'})
    r = {'name': name, 'request': {'method': method, 'header': h, 'url': url}, 'event': []}
    if body is not None:
        r['request']['body'] = {'mode': 'raw', 'raw': body if isinstance(body, str) else json.dumps(body, indent=2)}
    if test: r['event'].append({'listen': 'test', 'script': {'type': 'text/javascript', 'exec': test.strip().split('\n')}})
    if pre: r['event'].append({'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': pre.strip().split('\n')}})
    return r

def status(code): return f"pm.test('status {code}', () => pm.response.to.have.status({code}));"
def save(var, expr='pm.response.json().id'): return f"pm.collectionVariables.set('{var}', {expr});"

BO = '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
RUNTAG = "if (!pm.collectionVariables.get('runTag')) pm.collectionVariables.set('runTag', 'cls505-' + Date.now());"

bo_token = req('BO token', 'POST', '{{BO_baseUrl}}/oauth/2.0/token',
    {"grant_type": "password", "client_id": "{{BO_oauth_client_id}}", "client_secret": "{{BO_oauth_client_secret}}",
     "username": "{{BO_username}}", "password": "{{BO_password}}"},
    status(200) + "\n" + save('BO_access_token', 'pm.response.json().access_token'), pre=RUNTAG)
gw_token = req('Player token', 'POST', '{{baseUrl}}/oauth/2.0/token',
    {"grant_type": "player", "username": "{{username}}", "password": "{{password}}", "client_id": "{{oauth_client_id}}",
     "client_secret": "{{oauth_client_secret}}", "deviceInformation": {"ip": "127.0.0.1", "userAgent": "Mozilla/5.0"}},
    status(200) + "\n" + save('access_token', 'pm.response.json().access_token'), pre=RUNTAG)

# Guard signature, DEV-ONLY: only signs calls to the local cms port.
GUARD = r"""
(() => {
const url = pm.variables.replaceIn(pm.request.url.toString());
const m = url.match(/^https?:\/\/([^\/:]+)(?::(\d+))?([^?]*)/);
const method = pm.request.method.toUpperCase();
let data = method + m[1] + decodeURIComponent(m[3]);
if (['POST','PUT','PATCH'].includes(method)) {
  const body = (pm.request.body && pm.request.body.raw) ? pm.variables.replaceIn(pm.request.body.raw) : '';
  data += CryptoJS.MD5(body).toString();
}
pm.request.headers.upsert({key: 'x-guard-secret', value: CryptoJS.HmacSHA256(data, pm.environment.get('guardKey')).toString()});
})();
"""

# Reads the domain's languages so every content map carries one key per language.
LANGS = """
pm.test('status 200', () => pm.response.to.have.status(200));
const d = pm.response.json();
const sec = d.secondaryLanguage ? (Array.isArray(d.secondaryLanguage) ? d.secondaryLanguage : [d.secondaryLanguage]) : [];
const langs = [...new Set([d.language || 'en', ...sec].filter(Boolean))];
pm.test('languages read', () => pm.expect(langs.length).to.be.above(0));
pm.collectionVariables.set('primaryLang', langs[0]);
pm.collectionVariables.set('langs', JSON.stringify(langs));
"""
domains = req('GET domain (languages)', 'GET', BO, None, LANGS, auth='bo')

def content_map(var, text):
    return f"""const langs = JSON.parse(pm.collectionVariables.get('langs') || '["en"]');
const c = {{}}; langs.forEach(l => c[l] = '{text} ' + pm.collectionVariables.get('runTag') + ' ' + l);
pm.collectionVariables.set('{var}', JSON.stringify(c));"""

def collection(name, items, vars, cap):
    return {'info': {'name': name, 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
            'item': items,
            'variable': [{'key': k, 'value': v} for k, v in vars.items()] + [{'key': k, 'value': ''} for k in cap]}

def dump(c, path): json.dump(c, open(path, 'w'), indent=2)

ENTRY = {'BO_baseUrl': 'http://localhost:84', 'baseUrl': 'http://localhost:93', 'domainId': '1'}

# ───────────────────────────── CLS-3288 game ─────────────────────────────
relax = lambda action: '{{gameUrl}}/webhook/relax/' + action
def relax_body(extra):
    b = {"customerid": "{{playerId}}", "cashiertoken": "{{cashiertoken}}", "currency": "{{currency}}", "gameid": "casino",
         "gameref": "{{externalGameId}}", "channel": "web", "clientid": ""}
    b.update(extra)
    return b
TXID = "pm.collectionVariables.set('txBase', pm.collectionVariables.get('txBase') || String(Date.now()));"
ok_balance = status(200) + "\npm.test('balance is a number', () => pm.expect(pm.response.json().balance).to.be.a('number'));"

g1 = {'name': '1 GW launch Relax game', 'item': [gw_token,
    req('GET player information', 'GET', '{{baseUrl}}/player/information', None,
        status(200) + "\nconst j = pm.response.json();\nconst id = j.id || j.playerId || j.customerId;\npm.test('player id', () => pm.expect(id).to.not.be.undefined);\n" + save('playerId', 'String(id)'), auth='gw'),
    req('POST launch (real) -> cashiertoken', 'POST', '{{baseUrl}}/en/game/{{gameId}}/launch',
        {"ip": "127.0.0.1", "device": "desktop", "lobbyUrl": "http://localhost", "depositUrl": "http://localhost"},
        status(200) + "\nconst m = pm.response.text().match(/ticket=([^&\"\\\\]+)/);\npm.test('ticket in launch url', () => pm.expect(m).to.not.be.null);\nif (m) pm.collectionVariables.set('cashiertoken', decodeURIComponent(m[1]));", auth='gw'),
]}
g1b = {'name': '1b LOCAL ONLY top up player (fixtures leave a negative balance)', 'item': [bo_token,
    req('POST adjustment_up 500', 'POST', BO + '/player/{{playerId}}/wallet/transaction',
        {"type": "adjustment_up", "amount": "500", "currency": "{{currency}}", "note": "QA CLS-505", "reason": "technical_issue"}, status(200), auth='bo'),
]}
g2 = {'name': '2 Relax webhooks: bet, win, bet + rollback (provider callback)', 'item': [
    req('getBalance -> start balance', 'POST', relax('getBalance'), relax_body({}),
        ok_balance + "\n" + save('balanceStart', 'pm.response.json().balance'), pre=TXID),
    req('withdraw 10 (round A)', 'POST', relax('withdraw'),
        relax_body({"txid": "{{txBase}}1", "amount": 10, "txtype": "withdraw", "gamesessionid": "{{txBase}}A", "ended": False}),
        ok_balance + "\npm.test('betdistribution', () => pm.expect(pm.response.json().betdistribution).to.be.an('object'));"),
    req('deposit 20 (round A, ended)', 'POST', relax('deposit'),
        relax_body({"txid": "{{txBase}}2", "amount": 20, "txtype": "deposit", "gamesessionid": "{{txBase}}A", "ended": True}), ok_balance),
    req('withdraw 10 again -> 403 already processed', 'POST', relax('withdraw'),
        relax_body({"txid": "{{txBase}}1", "amount": 10, "txtype": "withdraw", "gamesessionid": "{{txBase}}A", "ended": False}), status(403)),
    req('withdraw 15 (round B)', 'POST', relax('withdraw'),
        relax_body({"txid": "{{txBase}}3", "amount": 15, "txtype": "withdraw", "gamesessionid": "{{txBase}}B", "ended": False}), ok_balance),
    req('rollback round B bet', 'POST', relax('rollback'),
        relax_body({"txid": "{{txBase}}4", "originaltxid": "{{txBase}}3", "gamesessionid": "{{txBase}}B"}), ok_balance),
    req('getBalance -> start + 10', 'POST', relax('getBalance'), relax_body({}),
        ok_balance + "\npm.test('net +10 cents', () => pm.expect(pm.response.json().balance).to.eql(Number(pm.collectionVariables.get('balanceStart')) + 10));"),
    req('rollback unknown tx -> declined', 'POST', relax('rollback'),
        relax_body({"txid": "{{txBase}}5", "originaltxid": "{{txBase}}999", "gamesessionid": "{{txBase}}C"}),
        "pm.test('not 2xx', () => pm.expect(pm.response.code).to.be.at.least(400));"),
]}
g3 = {'name': '3 BO game reads', 'item': [bo_token,
    req('GET game', 'GET', BO + '/game/{{gameId}}', None, status(200) + "\npm.test('same id', () => pm.expect(String(pm.response.json().id)).to.eql(String(pm.variables.get('gameId'))));", auth='bo'),
    req('GET unknown game -> 404', 'GET', BO + '/game/999999999', None, status(404), auth='bo'),
]}
g4 = {'name': '4 Free rounds grant + cancel (promotion -> game)', 'item': [bo_token,
    req('POST reward-configuration free_rounds (Relax)', 'POST', BO + '/reward-configuration',
        {"name": "{{runTag}} fr", "displayName": "{{runTag}} fr", "type": "free_rounds", "model": "winnings", "offeringMethod": "manual",
         "currency": "{{currency}}", "validDuringDays": 3, "claimingEvent": "direct", "offerValidFor": 2,
         "freeRoundConfiguration": {"freeRoundsGameGateway": "{{gameGatewayId}}", "freeRoundsGameStudio": "{{gameStudioId}}", "gameIds": [{"id": "{{gameId}}"}], "amount": 1}},
        status(200) + "\n" + save('rcFrId'), auth='bo'),
    req('PATCH enable', 'PATCH', BO + '/reward-configuration/{{rcFrId}}', {"status": "enabled"}, status(200), auth='bo'),
    req('POST offer', 'POST', BO + '/reward/bonus/{{rcFrId}}/offer', {"playerId": "{{playerId}}", "freeRoundsRoundCount": 3, "message": "QA CLS-505"},
        status(200) + "\nconst j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\n" + save('bonusId', 'j.id'), auth='bo'),
    gw_token,
    req('GW GET /reward/bonuses -> find offered', 'GET', '{{baseUrl}}/reward/bonuses', None,
        status(200) + """
const j = pm.response.json(); const list = [j.bonus, j.bonuses, j.rewards, j.data, j].find(Array.isArray) || [];
if (!list.length) console.log('reward bonuses keys', Object.keys(j));
const want = String(pm.collectionVariables.get('bonusId'));
const b = list.find(x => String(x.id) === want || String(x.id).endsWith('_' + want));
pm.test('bonus listed', () => pm.expect(b).to.not.be.undefined);
if (b) pm.collectionVariables.set('claimRewardId', String(b.id));""", auth='gw'),
    req('GW claim -> game grant', 'POST', '{{baseUrl}}/reward/bonuses/claim', {"rewardIds": ["{{claimRewardId}}"]}, status(200), auth='gw'),
    bo_token,
    req('BO cancel bonus -> game cancel', 'POST', BO + '/reward/bonus/{{bonusId}}/cancel', {"playerId": "{{playerId}}"}, status(200), auth='bo'),
]}
dump(collection('CLS-3288 game Symfony 7.4', [g1, g1b, g2, g3, g4],
    {**ENTRY, 'gameUrl': 'http://localhost:89', 'currency': 'EUR', 'gameId': '6', 'externalGameId': '421', 'gameGatewayId': '4', 'gameStudioId': '4'},
    ['runTag', 'BO_access_token', 'access_token', 'playerId', 'cashiertoken', 'txBase', 'balanceStart', 'rcFrId', 'bonusId', 'claimRewardId']),
    'CLS-3288-game.postman_collection.json')

# ───────────────────────────── CLS-3290 contact ─────────────────────────────
c1 = {'name': '1 BO email providers (read only)', 'item': [bo_token,
    req('GET email_providers', 'GET', BO + '/email_providers', None,
        status(200) + "\npm.test('is a list', () => pm.expect(pm.response.json()).to.be.an('array'));", auth='bo'),
    req('PUT unknown provider -> 404 (entity resolution, no write)', 'PUT', BO + '/email_provider/999999999',
        {"enabled": False, "type": "sendgrid", "apiKey": "SG.cls505", "apiKeyId": "cls505"}, status(404), auth='bo'),
]}
c2 = {'name': '2 GW forgot password -> contact /emails', 'item': [gw_token,
    req('POST forgot-password', 'POST', '{{baseUrl}}/forgot-password', {"email": "{{username}}"}, status(200), auth='gw'),
]}
dump(collection('CLS-3290 contact Symfony 7.4', [c1, c2], ENTRY, ['runTag', 'BO_access_token', 'access_token']),
    'CLS-3290-contact.postman_collection.json')

# ───────────────────────────── CLS-3291 cms ─────────────────────────────
CB = BO + '/content_block'
cb_body = lambda extra, slug='cb': '{\n  "name": "{{runTag}} ' + slug + '",\n  "slug": "{{runTag}}-' + slug + '",\n  "visibility": "ROLE_USER",\n  "content": {{cbContent}},\n  "countries": [],\n  "segments": []' + extra + '\n}'
m1 = {'name': '1 BO content tag', 'item': [bo_token, domains,
    req('POST content_tag', 'POST', BO + '/content_tag', {"name": "{{runTag}} tag", "backgroundColor": "#ff0000"},
        status(200) + "\n" + save('tagId'), auth='bo'),
    req('POST content_tags (list) -> contains tag', 'POST', BO + '/content_tags', {"limit": 100, "offset": 0},
        status(200) + "\nconst j = pm.response.json(); const list = j.data || j;\npm.test('tag listed', () => pm.expect(list.some(t => String(t.id) === String(pm.collectionVariables.get('tagId')))).to.be.true);", auth='bo'),
    req('PATCH content_tag', 'PATCH', BO + '/content_tag/{{tagId}}', {"name": "{{runTag}} tag2"},
        status(200) + "\npm.test('renamed', () => pm.expect(pm.response.json().name).to.eql(pm.collectionVariables.get('runTag') + ' tag2'));", auth='bo'),
    req('PATCH unknown tag -> 404', 'PATCH', BO + '/content_tag/999999999', {"name": "x"}, status(404), auth='bo'),
]}
m2 = {'name': '2 BO content block', 'item': [
    req('POST content_block (with tag)', 'POST', CB, cb_body(',\n  "contentTagIds": [{{tagId}}]'),
        status(200) + "\n" + save('cbId'), auth='bo', pre=content_map('cbContent', 'cb')),
    req('GET content_block', 'GET', CB + '/{{cbId}}', None,
        status(200) + "\npm.test('same id', () => pm.expect(String(pm.response.json().id)).to.eql(String(pm.collectionVariables.get('cbId'))));", auth='bo'),
    req('PUT content_block enabled + visibility period', 'PUT', CB + '/{{cbId}}',
        cb_body(',\n  "status": "enabled",\n  "visibilityPeriod": {"fromDate": "2030-01-01 00:00:00", "toDate": "2030-02-01 00:00:00"}'),
        status(200) + "\npm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));", auth='bo'),
    req('PATCH status disabled', 'PATCH', CB + '/{{cbId}}', {"status": "disabled"},
        status(200) + "\npm.test('disabled', () => pm.expect(pm.response.json().status).to.eql('disabled'));", auth='bo'),
    req('PUT invalid status -> 400', 'PUT', CB + '/{{cbId}}', cb_body(',\n  "status": "bogus"'), status(400), auth='bo'),
    req('POST toDate before fromDate -> 400', 'POST', CB,
        cb_body(',\n  "visibilityPeriod": {"fromDate": "2030-02-01 00:00:00", "toDate": "2030-01-01 00:00:00"}', 'cb-bad1'),
        status(400) + "\npm.test('message', () => pm.expect(pm.response.text()).to.include('cannot be greater than the value of toDate'));", auth='bo'),
    req('POST toDate without fromDate -> 400', 'POST', CB,
        cb_body(',\n  "visibilityPeriod": {"fromDate": null, "toDate": "2030-01-01 00:00:00"}', 'cb-bad2'),
        status(400) + "\npm.test('message', () => pm.expect(pm.response.text()).to.include('cannot be null when toDate is provided'));", auth='bo'),
    req('GET unknown content_block -> 404', 'GET', CB + '/999999999', None, status(404), auth='bo'),
    req('DELETE content_block', 'DELETE', CB + '/{{cbId}}', None, status(200), auth='bo'),
    req('GET deleted content_block -> 404', 'GET', CB + '/{{cbId}}', None, status(404), auth='bo'),
    req('DELETE content_tag', 'DELETE', BO + '/content_tag/{{tagId}}', None, status(200), auth='bo'),
]}
TC = BO + '/terms_and_conditions'
m3 = {'name': '3 BO terms and conditions (draft only, never publish on a shared domain)', 'item': [
    req('GET terms_and_conditions', 'GET', TC, None, status(200), auth='bo'),
    req('POST draft', 'POST', TC, '{\n  "content": {{tcContent}}\n}', status(200) + "\n" + save('tcId'), auth='bo', pre=content_map('tcContent', 'QA draft, do not publish')),
    req('PUT draft', 'PUT', TC + '/{{tcId}}', '{\n  "content": {{tcContent}}\n}', status(200), auth='bo', pre=content_map('tcContent', 'QA draft v2, do not publish')),
    req('PUT unknown -> 404', 'PUT', TC + '/999999999', '{\n  "content": {{tcContent}}\n}', status(404), auth='bo'),
    req('POST publish unknown -> 404', 'POST', TC + '/publish/999999999', None, status(404), auth='bo'),
]}
CET = BO + '/custom-email-template'
cet_pre = """const langs = JSON.parse(pm.collectionVariables.get('langs') || '["en"]');
const t = {}; langs.forEach(p => t[p] = {sender: 'no-reply@celesta.io', senderName: 'QA', subject: 'Hi {{player.first_name}}', content: '<p>' + pm.collectionVariables.get('runTag') + '</p>'});
pm.collectionVariables.set('cetTranslations', JSON.stringify(t));"""
m4 = {'name': '4 BO custom email template', 'item': [
    req('POST custom-email-template', 'POST', CET, '{\n  "name": "{{runTag}} cet",\n  "enabled": true,\n  "translations": {{cetTranslations}}\n}',
        status(201) + "\n" + save('cetId'), auth='bo', pre=cet_pre),
    req('GET custom-email-template', 'GET', CET + '/{{cetId}}', None, status(200), auth='bo'),
    req('PATCH name', 'PATCH', CET + '/{{cetId}}', {"name": "{{runTag}} cet2"},
        status(200) + "\npm.test('renamed', () => pm.expect(pm.response.json().name).to.eql(pm.collectionVariables.get('runTag') + ' cet2'));", auth='bo'),
    req('GET unknown -> 404', 'GET', CET + '/999999999', None, status(404), auth='bo'),
]}
CMS = '{{cmsUrl}}/api/domain/{{domainId}}/custom-email-template/{{cetId}}'
m5 = {'name': '5 DEV-ONLY cms direct (no entry point): render, bulk render, send, publish', 'item': [
    req('POST render', 'POST', CMS + '/render', '{"playerId": {{playerId}}}', status(200), pre=GUARD),
    req('POST render/bulk', 'POST', CMS + '/render/bulk', '[{"playerId": {{playerId}}}]',
        status(200) + "\npm.test('one result', () => pm.expect(pm.response.json()).to.have.lengthOf(1));", pre=GUARD),
    req('POST send -> contact /emails', 'POST', CMS + '/send', '{"playerId": {{playerId}}}', status(200), pre=GUARD),
    req('POST publish draft (locks unsigned players of the domain)', 'POST', TC + '/publish/{{tcId}}', None, status(200), auth='bo'),
]}
m6 = {'name': '6 BO cleanup', 'item': [
    req('DELETE custom-email-template', 'DELETE', CET + '/{{cetId}}', None, status(204), auth='bo'),
    req('GET deleted -> 404', 'GET', CET + '/{{cetId}}', None, status(404), auth='bo'),
]}
dump(collection('CLS-3291 cms Symfony 7.4', [m1, m2, m3, m4, m5, m6], {**ENTRY, 'cmsUrl': 'http://localhost:94', 'playerId': '1'},
    ['runTag', 'BO_access_token', 'primaryLang', 'langs', 'tagId', 'cbContent', 'cbId', 'tcContent', 'tcId', 'cetTranslations', 'cetId']),
    'CLS-3291-cms.postman_collection.json')

# ───────────────────────────── CLS-3289 promotion ─────────────────────────────
DATES = """
const pad = n => String(n).padStart(2, '0');
const f = (d, t) => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) + (t ? ' ' + t : '');
const day = n => { const d = new Date(); d.setDate(d.getDate() + n); return d; };
pm.collectionVariables.set('startDate', f(day(1), '00:00'));
pm.collectionVariables.set('startDay', f(day(1), '23:59'));
pm.collectionVariables.set('endDate', f(day(60), '23:59'));
pm.collectionVariables.set('finishDate', f(day(30), '23:59'));
"""
PC = BO + '/promotion-configuration'
p0 = {'name': '0 BO setup: segment', 'item': [bo_token,
    req('POST segments -> pick one', 'POST', BO + '/segments', {"limit": 50, "offset": 0},
        status(200) + """
const j = pm.response.json(); const list = [j.data, j.segments, j].find(Array.isArray) || [];
const s = list.find(x => !x.currency || x.currency === pm.variables.get('currency')) || list[0];
pm.test('segment found', () => pm.expect(s).to.not.be.undefined);
if (s) pm.collectionVariables.set('segmentId', s.id);""", auth='bo', pre=DATES),
]}
p1 = {'name': '1 BO promotion tags', 'item': [
    req('POST promotion-tag', 'POST', BO + '/promotion-tag', {"name": "{{runTag}} ptag", "backgroundColor": "#FF0000"},
        status(200) + "\n" + save('ptagId'), auth='bo'),
    req('POST duplicate name -> 400', 'POST', BO + '/promotion-tag', {"name": "{{runTag}} ptag", "backgroundColor": "#FF0000"}, status(400), auth='bo'),
    req('PATCH promotion-tag', 'PATCH', BO + '/promotion-tag/{{ptagId}}', {"name": "{{runTag}} ptag2"}, status(200), auth='bo'),
    req('PATCH unknown -> 404', 'PATCH', BO + '/promotion-tag/999999999', {"name": "x"}, status(404), auth='bo'),
]}
RC = BO + '/reward-configuration'
rc_manual = {"name": "{{runTag}} rc free", "type": "free", "model": "direct", "offeringMethod": "manual", "currency": "{{currency}}",
             "validDuringDays": "7", "claimingEvent": "direct", "offerAmount": "10", "offerValidFor": 14}
rc_auto = '{\n  "name": "{{runTag}} rc auto", "type": "free", "model": "direct", "offeringMethod": "automatic", "currency": "{{currency}}",\n  "validDuringDays": "7", "claimingEvent": "direct", "offerAmount": "10", "recurrence": "always", "segmentIds": [{"id": {{segmentId}}}]%s\n}'
p2 = {'name': '2 BO reward configuration', 'item': [
    req('POST manual free', 'POST', RC, rc_manual, status(200) + "\n" + save('rcId'), auth='bo'),
    req('GET', 'GET', RC + '/{{rcId}}', None, status(200) + "\npm.test('same id', () => pm.expect(String(pm.response.json().id)).to.eql(String(pm.collectionVariables.get('rcId'))));", auth='bo'),
    req('PATCH enable', 'PATCH', RC + '/{{rcId}}', {"status": "enabled"},
        status(200) + "\npm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));", auth='bo'),
    req('GET unknown -> 404', 'GET', RC + '/999999999', None, status(404), auth='bo'),
    req('POST automatic with segment', 'POST', RC, rc_auto % '', status(200) + "\n" + save('rcAutoId'), auth='bo'),
    req('POST reward-configurations by segment -> contains it', 'POST', BO + '/reward-configurations', '{"limit": 100, "offset": 0, "filter": {"segmentIds": [{{segmentId}}]}}',
        status(200) + """
const j = pm.response.json(); const list = [j.data, j].find(Array.isArray) || [];
const rc = list.find(x => String(x.id) === String(pm.collectionVariables.get('rcAutoId')));
pm.test('listed by segment', () => pm.expect(rc).to.not.be.undefined);
pm.test('segmentIds present', () => pm.expect(rc && (rc.segmentIds || rc.segments)).to.not.be.undefined);""", auth='bo'),
    req('POST validDuringDays 400 -> 400', 'POST', RC, {**rc_manual, "validDuringDays": "400"}, status(400), auth='bo'),
    req('POST daily to before from -> 400', 'POST', RC, rc_auto.replace('"recurrence": "always"', '"recurrence": "daily"') % ', "recurrenceDailyFrom": "18:00", "recurrenceDailyTo": "09:00"', status(400), auth='bo'),
    req('POST weekly to before from -> 400', 'POST', RC, rc_auto.replace('"recurrence": "always"', '"recurrence": "weekly"') % ', "recurrenceWeeklyFrom": {"weekDay": "Friday", "time": "10:00"}, "recurrenceWeeklyTo": {"weekDay": "Monday", "time": "10:00"}', status(400), auth='bo'),
]}
p3 = {'name': '3 BO promotion configuration + tags', 'item': [
    req('POST promotion-configuration deposit_tier', 'POST', PC,
        '{"name": "{{runTag}} promo", "currency": "{{currency}}", "startDate": "{{startDate}}", "endDate": "{{endDate}}", "segmentIds": [{{segmentId}}], "engagementModel": "manual", "type": "deposit_tier", "engagementCode": "{{runTag}}"}',
        status(200) + "\n" + save('pcId'), auth='bo'),
    req('GET', 'GET', PC + '/{{pcId}}', None, status(200), auth='bo'),
    req('PATCH name', 'PATCH', PC + '/{{pcId}}', {"name": "{{runTag}} promo2"}, status(200), auth='bo'),
    req('PATCH invalid status -> 400', 'PATCH', PC + '/{{pcId}}', {"status": "foo"}, status(400), auth='bo'),
    req('PATCH unknown -> 404', 'PATCH', PC + '/999999999', {"name": "x"}, status(404), auth='bo'),
    req('PUT tags', 'PUT', PC + '/{{pcId}}/tags', '{"tagIds": [{{ptagId}}]}', status(200), auth='bo'),
    req('PUT unknown tag -> 400', 'PUT', PC + '/{{pcId}}/tags', {"tagIds": [999999999]}, status(400), auth='bo'),
    req('POST refer_friend with half of a pair -> 400 (BothOrNone)', 'POST', PC,
        '{"name": "{{runTag}} raf", "currency": "{{currency}}", "startDate": "{{startDate}}", "endDate": "{{endDate}}", "segmentIds": [{{segmentId}}], "engagementModel": "automatic", "type": "refer_friend", "options": {"targetBetAmount": 10}}',
        status(400) + "\npm.test('BothOrNone message', () => pm.expect(pm.response.text()).to.include('must be provided together'));", auth='bo'),
]}
SCH = PC + '/{{pcId}}/schedule'
sch = lambda days: '{"firstOccurrence": {"startsAt": "{{startDate}}", "endsAt": "{{startDay}}"}, "recurrence": {"type": "weekly", "interval": 1, "daysOfWeek": ' + days + '}, "finishCondition": {"type": "date", "finishDate": "{{finishDate}}"}, "engagementScope": "global"}'
p4 = {'name': '4 BO weekly schedule', 'item': [
    req('POST weekly Mon/Wed/Fri', 'POST', SCH, sch('["Monday", "Wednesday", "Friday"]'), status(200) + "\n" + save('schId'), auth='bo'),
    req('POST daysOfWeek empty -> 400', 'POST', SCH, sch('[]'),
        status(400) + "\npm.test('message', () => pm.expect(pm.response.text()).to.include('daysOfWeek must be set to at least one day'));", auth='bo'),
    req('POST daysOfWeek Funday -> 400', 'POST', SCH, sch('["Funday"]'),
        status(400) + "\npm.test('message', () => pm.expect(pm.response.text()).to.include('daysOfWeek contains invalid values'));", auth='bo'),
    req('PUT weekly Tuesday', 'PUT', SCH + '/{{schId}}', sch('["Tuesday"]'), status(200), auth='bo'),
    req('DELETE schedule', 'DELETE', SCH + '/{{schId}}', None, "pm.test('2xx', () => pm.expect(pm.response.code).to.be.oneOf([200, 204]));", auth='bo'),
]}
AG = PC + '/{{pcId}}/reward-aggregator'
p5 = {'name': '5 BO reward aggregator', 'item': [
    req('POST tier aggregator', 'POST', PC + '/{{pcId}}/reward-aggregators', [{"type": "tier", "options": {"minAmount": 10, "maxAmount": 100}, "rewards": []}],
        status(200) + "\nconst j = pm.response.json(); const a = Array.isArray(j) ? j[0] : j;\n" + save('agId', 'a.id'), auth='bo'),
    req('PATCH tier', 'PATCH', AG + '/{{agId}}', {"type": "tier", "options": {"minAmount": 10, "maxAmount": 200}}, status(200), auth='bo'),
    req('DELETE tier', 'DELETE', AG + '/{{agId}}', None, "pm.test('2xx', () => pm.expect(pm.response.code).to.be.oneOf([200, 204]));", auth='bo'),
]}
p6 = {'name': '6 offer free bonus to player, GW lists it, BO cancels', 'item': [gw_token,
    req('GET player information', 'GET', '{{baseUrl}}/player/information', None,
        status(200) + "\n" + save('playerId', 'String(pm.response.json().id)'), auth='gw'),
    bo_token,
    req('POST offer', 'POST', BO + '/reward/bonus/{{rcId}}/offer', {"playerId": "{{playerId}}", "message": "QA CLS-505", "amount": 10},
        status(200) + "\nconst j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\n" + save('bonusId', 'j.id'), auth='bo'),
    gw_token,
    req('GW GET /reward/bonuses -> listed', 'GET', '{{baseUrl}}/reward/bonuses', None,
        status(200) + """
const j = pm.response.json(); const list = [j.bonus, j.bonuses, j.data, j].find(Array.isArray) || [];
const want = String(pm.collectionVariables.get('bonusId'));
pm.test('bonus listed', () => pm.expect(list.some(x => String(x.id) === want || String(x.id).endsWith('_' + want))).to.be.true);""", auth='gw'),
    bo_token,
    req('BO cancel bonus', 'POST', BO + '/reward/bonus/{{bonusId}}/cancel', {"playerId": "{{playerId}}"}, status(200), auth='bo'),
]}
p7 = {'name': '7 BO cleanup', 'item': [
    req('DELETE manual rc', 'DELETE', RC + '/{{rcId}}', None, status(200), auth='bo'),
    req('DELETE automatic rc', 'DELETE', RC + '/{{rcAutoId}}', None, status(200), auth='bo'),
    req('GET deleted rc -> 404', 'GET', RC + '/{{rcId}}', None, status(404), auth='bo'),
    req('DELETE promotion-tag', 'DELETE', BO + '/promotion-tag/{{ptagId}}', None, "pm.test('2xx', () => pm.expect(pm.response.code).to.be.oneOf([200, 204]));", auth='bo'),
]}
PROMO = '{{promotionUrl}}/api/domain/{{domainId}}/reward-configuration'
rf = lambda frm: '{"name": "{{runTag}} rf", "type": "free", "model": "direct", "offeringMethod": "automatic", "currency": "{{currency}}", "validDuringDays": 7, "claimingEvent": "direct", "offerAmount": "10", "segmentIds": [{{segmentId}}], "recurrence": "weekly", "recurrenceWeeklyFrom": "' + frm + '", "recurrenceWeeklyTo": "Sunday 10:00"}'
p8 = {'name': '8 DEV-ONLY promotion direct: RecurrenceFormat (BO never sends a bad format)', 'item': [
    req('POST weekly from "Funday 10:00" -> 400 format', 'POST', PROMO, rf('Funday 10:00'),
        status(400) + "\npm.test('RecurrenceFormat message', () => pm.expect(pm.response.text()).to.include('Format not valid'));", pre=GUARD),
    req('POST weekly from "Monday" without time -> 400 format', 'POST', PROMO, rf('Monday'),
        status(400) + "\npm.test('RecurrenceFormat message', () => pm.expect(pm.response.text()).to.include('Format not valid'));", pre=GUARD),
]}
dump(collection('CLS-3289 promotion Symfony 7.4', [p0, p1, p2, p3, p4, p5, p6, p7, p8], {**ENTRY, 'currency': 'EUR', 'promotionUrl': 'http://localhost:99'},
    ['runTag', 'BO_access_token', 'access_token', 'startDate', 'startDay', 'endDate', 'finishDate', 'segmentId', 'ptagId', 'rcId', 'rcAutoId', 'pcId', 'schId', 'agId', 'playerId', 'bonusId']),
    'CLS-3289-promotion.postman_collection.json')
