import json

# CLS-3540 (cms #281): regression run for the rewritten content block filter, translation mapper and T&C locales.
# Everything goes through BO and GW, so it runs in pp1. Cells: tickets/CLS-3540/matrix.md.

def req(name, method, url, body=None, test='', auth=None, pre=''):
    h = [{'key': 'Content-Type', 'value': 'application/json'}] if body is not None else []
    if auth:
        h.append({'key': 'Authorization', 'value': 'Bearer {{' + auth + '}}'})
    r = {'name': name, 'request': {'method': method, 'header': h, 'url': url}, 'event': []}
    if body is not None:
        r['request']['body'] = {'mode': 'raw', 'raw': body if isinstance(body, str) else json.dumps(body, indent=2)}
    if test:
        r['event'].append({'listen': 'test', 'script': {'type': 'text/javascript', 'exec': test.strip().split('\n')}})
    if pre:
        r['event'].append({'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': pre.strip().split('\n')}})
    return r

def status(code):
    return (f"if (pm.response.code !== {code}) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 400));\n"
            f"pm.test('status {code}', () => pm.response.to.have.status({code}));\n")
def save(var, expr='pm.response.json().id'):
    return f"pm.collectionVariables.set('{var}', {expr});\n"
def v(name):
    return f"pm.collectionVariables.get('{name}')"

BO = '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
CB = BO + '/content_block'
RUNTAG = "if (!pm.collectionVariables.get('runTag')) pm.collectionVariables.set('runTag', 'cls3540-' + Date.now());"

# ── 0 tokens and data discovery ──
gw_token = req('GW player token', 'POST', '{{baseUrl}}/oauth/2.0/token',
    {'grant_type': 'player', 'username': '{{username}}', 'password': '{{password}}', 'client_id': '{{oauth_client_id}}',
     'client_secret': '{{oauth_client_secret}}', 'deviceInformation': {'ip': '127.0.0.1', 'userAgent': 'Mozilla/5.0'}},
    status(200) + save('access_token', 'pm.response.json().access_token') + """
const p = JSON.parse(atob(pm.response.json().access_token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
pm.test('player id in token', () => pm.expect(p.sub).to.be.ok);
pm.collectionVariables.set('playerId', String(p.sub));""", pre=RUNTAG)

bo_token = req('BO token', 'POST', '{{BO_baseUrl}}/oauth/2.0/token',
    {'grant_type': 'password', 'client_id': '{{BO_oauth_client_id}}', 'client_secret': '{{BO_oauth_client_secret}}',
     'username': '{{BO_username}}', 'password': '{{BO_password}}'},
    status(200) + save('BO_access_token', 'pm.response.json().access_token'), pre=RUNTAG)

LANGS = status(200) + """
const d = pm.response.json();
const sec = d.secondaryLanguage ? (Array.isArray(d.secondaryLanguage) ? d.secondaryLanguage : [d.secondaryLanguage]) : [];
const langs = [...new Set([d.language || 'en', ...sec].filter(Boolean))];
pm.test('languages read', () => pm.expect(langs.length).to.be.above(0));
console.log('domain languages: ' + langs.join(','));
pm.collectionVariables.set('langs', JSON.stringify(langs));
pm.collectionVariables.set('lang1', langs[0]);
pm.collectionVariables.set('lang2', langs[1] || '');"""

SEGS = status(200) + """
const j = pm.response.json(); const rows = [j, j.data, j.items].find(Array.isArray) || [];
const row = rows.find(r => String(r.playerId) === pm.collectionVariables.get('playerId'));
const ids = row ? row.segmentIds : [];
console.log('player segments: ' + JSON.stringify(ids));
pm.collectionVariables.set('segIn', ids.length ? String(ids[0]) : '');"""

f0 = {'name': '0 tokens, domain languages, player segment', 'item': [
    gw_token, bo_token,
    req('GET domain (languages)', 'GET', BO, None, LANGS, auth='BO_access_token'),
    req('POST player segments', 'POST', '{{BO_baseUrl}}/api/gateway/player/segments', '{"filter": {"playerIds": [{{playerId}}]}, "limit": 10, "offset": 0}', SEGS,
        auth='BO_access_token'),
]}

# ── 1 BO setup: two tags, six blocks, all enabled ──
def content(var, version):
    return f"""const langs = JSON.parse({v('langs')} || '["en"]');
const c = {{}}; langs.forEach(l => c[l] = '{version} ' + {v('runTag')} + ' ' + pm.info.requestName.split(' ')[1] + ' ' + l);
pm.collectionVariables.set('{var}', JSON.stringify(c));"""

def cb_body(slug, visibility, segments, tags, cvar='cbContent', status_=None):
    seg = '' if segments is None else f',\n  "segments": {segments}'
    st = '' if status_ is None else f',\n  "status": "{status_}"'
    return ('{\n  "name": "{{runTag}} ' + slug + '",\n  "slug": "{{runTag}}-' + slug + '",\n  "visibility": "' + visibility + '",\n'
            '  "content": {{' + cvar + '}},\n  "countries": []' + seg + ',\n  "contentTagIds": ' + tags + st + '\n}')

BLOCKS = [  # slug, visibility, segments, tags
    ('any', 'IS_AUTHENTICATED_ANONYMOUSLY', '[]', '[{{tagT}}]'),
    ('user', 'ROLE_USER', '[]', '[{{tagT}}, {{tagT2}}]'),
    ('segin', 'ROLE_USER', '[{{segIn}}]', '[{{tagT}}]'),
    ('segout', 'ROLE_USER', '[999999999]', '[{{tagT}}]'),
    ('country', 'ROLE_VISIBLE_BY_COUNTRY', None, '[{{tagT}}]'),
    ('other', 'ROLE_USER', '[]', '[{{tagT2}}]'),
]
SKIP_NO_SEG = "if (!pm.collectionVariables.get('segIn')) { console.log('player has no segment: segin cell not run'); pm.execution.skipRequest(); }"

setup = [
    req('POST content_tag T', 'POST', BO + '/content_tag', {'name': '{{runTag}} T', 'backgroundColor': '#ff0000'},
        status(200) + save('tagT'), auth='BO_access_token'),
    req('POST content_tag T2', 'POST', BO + '/content_tag', {'name': '{{runTag}} T2', 'backgroundColor': '#00ff00'},
        status(200) + save('tagT2'), auth='BO_access_token'),
]
for slug, vis, segs, tags in BLOCKS:
    pre = content('cbContent', 'v1') + ('\n' + SKIP_NO_SEG if slug == 'segin' else '')
    setup.append(req(f'POST {slug} block', 'POST', CB, cb_body(slug, vis, segs, tags), status(200) + save('cb_' + slug),
                     auth='BO_access_token', pre=pre))
    if slug != 'user':  # user is enabled by its PUT below
        setup.append(req(f'PATCH {slug} enabled', 'PATCH', CB + '/{{cb_' + slug + '}}', {'status': 'enabled'},
                         status(200) + "pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",
                         auth='BO_access_token', pre=SKIP_NO_SEG if slug == 'segin' else ''))

PER_LANG = """const body = JSON.stringify(pm.response.json());
JSON.parse(pm.collectionVariables.get('langs')).forEach(l => pm.test('content stored for ' + l, () =>
  pm.expect(body).to.include('%s ' + pm.collectionVariables.get('runTag') + ' user ' + l)));"""

setup += [
    req('PUT user block: v2 content, tags [T], enabled', 'PUT', CB + '/{{cb_user}}',
        cb_body('user', 'ROLE_USER', '[]', '[{{tagT}}]', status_='enabled'), status(200), auth='BO_access_token',
        pre=content('cbContent', 'v2')),
    req('GET user block: v2 in every language, only tag T', 'GET', CB + '/{{cb_user}}', None, status(200) + PER_LANG % 'v2' + """
const tags = (pm.response.json().contentTags || []).map(t => String(t.id));
pm.test('tags replaced by [T]', () => pm.expect(tags).to.eql([String(pm.collectionVariables.get('tagT'))]));""",
        auth='BO_access_token'),
]
f1 = {'name': '1 BO setup: tags and blocks (cells 5, 6)', 'item': [bo_token] + setup}

# ── 2 GW player reads (cells 1, 2, 3) ──
def expect(visible, hidden, lang_var, version_of=lambda s: 'v2' if s == 'user' else 'v1'):
    vis = json.dumps(visible); hid = json.dumps(hidden); ver = json.dumps({s: version_of(s) for s in visible})
    return status(200) + f"""
const rt = {v('runTag')}; const lang = {v(lang_var)};
const list = pm.response.json()['content-block'];
pm.test('content-block list', () => pm.expect(list).to.be.an('array'));
const by = {{}}; list.forEach(b => by[b.slug] = b);
const visible = {vis}.filter(s => s !== 'segin' || pm.collectionVariables.get('segIn'));
visible.forEach(s => pm.test('sees ' + s, () => pm.expect(by[rt + '-' + s], JSON.stringify(Object.keys(by))).to.be.ok));
{hid}.forEach(s => pm.test('does not see ' + s, () => pm.expect(by[rt + '-' + s]).to.be.undefined));
const ver = {ver};
visible.forEach(s => pm.test(s + ' content in ' + lang, () => pm.expect(by[rt + '-' + s].content).to.eql(ver[s] + ' ' + rt + ' ' + s + ' ' + lang)));"""

PLAYER_SEES = ['any', 'user', 'segin']
PLAYER_HIDDEN = ['segout', 'country', 'other']
SKIP_NO_LANG2 = "if (!pm.collectionVariables.get('lang2')) { console.log('domain has one language: cell 3 not run'); pm.execution.skipRequest(); }"
GW = '{{baseUrl}}/cms/content-blocks'
f2 = {'name': '2 GW player reads (cells 1, 2, 3)', 'item': [
    gw_token,
    req('GET by tag name, lang1', 'GET', GW + '?language={{lang1}}&contentTagNames[]={{runTag}} T', None,
        expect(PLAYER_SEES, PLAYER_HIDDEN, 'lang1'), auth='access_token'),
    req('GET by tag id, lang1', 'GET', GW + '?language={{lang1}}&contentTagIds[]={{tagT}}', None,
        expect(PLAYER_SEES, PLAYER_HIDDEN, 'lang1'), auth='access_token'),
    req('GET by tag name, lang2', 'GET', GW + '?language={{lang2}}&contentTagNames[]={{runTag}} T', None,
        expect(PLAYER_SEES, PLAYER_HIDDEN, 'lang2'), auth='access_token', pre=SKIP_NO_LANG2),
    req('GET by tag name T2: only other', 'GET', GW + '?language={{lang1}}&contentTagNames[]={{runTag}} T2', None,
        expect(['other'], ['any', 'user', 'segin', 'segout', 'country'], 'lang1'), auth='access_token'),
]}

# ── 3 GW visitor (application token, cell 4) ──
f3 = {'name': '3 GW visitor with application token (cell 4)', 'item': [
    req('GW application token', 'POST', '{{baseUrl}}/oauth/2.0/token',
        {'grant_type': 'client_credentials', 'client_id': '{{oauth_client_id}}', 'client_secret': '{{oauth_client_secret}}'},
        status(200) + save('app_token', 'pm.response.json().access_token')),
    req('GET by tag name as visitor', 'GET', GW + '?language={{lang1}}&contentTagNames[]={{runTag}} T', None,
        expect(['any', 'country'], ['user', 'segin', 'segout', 'other'], 'lang1'), auth='app_token'),
]}

# ── 4 BO T&C draft (cell 7). Never publish in a shared preprod: it locks every player of the domain. ──
TC = BO + '/terms_and_conditions'
TC_LANG = """const body = JSON.stringify(pm.response.json());
JSON.parse(pm.collectionVariables.get('langs')).forEach(l => pm.test('T&C content for ' + l, () =>
  pm.expect(body).to.include('%s ' + pm.collectionVariables.get('runTag') + ' tc ' + l)));"""
def tc_content(version):
    return f"""const langs = JSON.parse({v('langs')} || '["en"]');
const c = {{}}; langs.forEach(l => c[l] = '{version} ' + {v('runTag')} + ' tc ' + l);
pm.collectionVariables.set('tcContent', JSON.stringify(c));"""
f4 = {'name': '4 BO terms and conditions draft (cell 7, never publish)', 'item': [
    req('POST draft', 'POST', TC, '{\n  "content": {{tcContent}}\n}', status(200) + save('tcId') + TC_LANG % 'QA draft do not publish v1',
        auth='BO_access_token', pre=tc_content('QA draft do not publish v1')),
    req('PUT draft', 'PUT', TC + '/{{tcId}}', '{\n  "content": {{tcContent}}\n}', status(200) + TC_LANG % 'QA draft do not publish v2',
        auth='BO_access_token', pre=tc_content('QA draft do not publish v2')),
    req('GET terms_and_conditions list', 'GET', TC, None, status(200), auth='BO_access_token'),
]}

# ── 5 cleanup ──
f5 = {'name': '5 BO cleanup', 'item': [
    req(f'DELETE {slug} block', 'DELETE', CB + '/{{cb_' + slug + '}}', None, status(200), auth='BO_access_token',
        pre=SKIP_NO_SEG if slug == 'segin' else '') for slug, *_ in BLOCKS
] + [
    req('DELETE content_tag T', 'DELETE', BO + '/content_tag/{{tagT}}', None, status(200), auth='BO_access_token'),
    req('DELETE content_tag T2', 'DELETE', BO + '/content_tag/{{tagT2}}', None, status(200), auth='BO_access_token'),
]}

VARS = {'BO_baseUrl': 'http://localhost:84', 'baseUrl': 'http://localhost:93', 'domainId': '1'}
CAPTURED = ['runTag', 'access_token', 'app_token', 'BO_access_token', 'playerId', 'langs', 'lang1', 'lang2', 'segIn',
            'tagT', 'tagT2', 'cbContent', 'tcContent', 'tcId'] + ['cb_' + s for s, *_ in BLOCKS]
collection = {
    'info': {'name': 'CLS-3540 cms coverage refactor', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
    'item': [f0, f1, f2, f3, f4, f5],
    'variable': [{'key': k, 'value': val} for k, val in VARS.items()] + [{'key': k, 'value': ''} for k in CAPTURED],
}
json.dump(collection, open('CLS-3540.postman_collection.json', 'w'), indent=2)
