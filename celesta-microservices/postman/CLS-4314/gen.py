import json

# Local dev only. Part 1 builds the scenario through BO and Gateway; run.sh then pushes one DepositJob per
# player to the promotion queue and runs the consumer; part 2 compares the per-player and the domain
# rewarding routes on the promotion service (signed calls, dev only).

def req(name, method, url, body=None, test='', auth=None, pre=''):
    h = [{'key': 'Content-Type', 'value': 'application/json'}] if body is not None else []
    if auth:
        h.append({'key': 'Authorization', 'value': 'Bearer {{' + auth + '}}'})
    r = {'name': name, 'request': {'method': method, 'header': h, 'url': url}, 'event': []}
    if body is not None:
        r['request']['body'] = {'mode': 'raw', 'raw': json.dumps(body, indent=2)}
    if test:
        r['event'].append({'listen': 'test', 'script': {'type': 'text/javascript', 'exec': test.strip().split('\n')}})
    if pre:
        r['event'].append({'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': pre.strip().split('\n')}})
    return r

ok = ("if (pm.response.code !== 200) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 400));\n"
      "pm.test('status 200', () => pm.response.to.have.status(200));\n")
BO = '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
PROMO = '{{promotionUrl}}/api/domain/{{domainId}}'

guard = r"""
const url = pm.variables.replaceIn(pm.request.url.toString());
const m = url.match(/^https?:\/\/([^\/:]+)(?::(\d+))?([^?]*)/);
if (m && ['88','99','89'].includes(m[2] || '')) {
  const method = pm.request.method.toUpperCase();
  let data = method + m[1] + decodeURIComponent(m[3]);
  if (['POST','PUT','PATCH'].includes(method)) {
    const body = (pm.request.body && pm.request.body.raw) ? pm.variables.replaceIn(pm.request.body.raw) : '';
    data += CryptoJS.MD5(body).toString();
  }
  pm.request.headers.upsert({ key: 'x-guard-secret', value: CryptoJS.HmacSHA256(data, pm.environment.get('guardKey')).toString() });
}
"""

dates = """if (!pm.environment.get('runTag')) {
  const t = Date.now(); pm.environment.set('runTag', 'qa4314-' + t);
  const d = n => new Date(t + n*86400000).toISOString().slice(0,10);
  pm.environment.set('startDate', d(-1) + ' 00:00:00'); pm.environment.set('endDate', d(30) + ' 23:59:59');
}"""

botok = req('BO token', 'POST', '{{BO_baseUrl}}/oauth/2.0/token',
            {'grant_type': 'password', 'client_id': '{{BO_oauth_client_id}}', 'client_secret': '{{BO_oauth_client_secret}}',
             'username': '{{BO_username}}', 'password': '{{BO_password}}'},
            ok + "pm.environment.set('BO_access_token', pm.response.json().access_token);", pre=dates)

def ptok(var, user):
    return req(f'GW token {user}', 'POST', '{{baseUrl}}/oauth/2.0/token',
               {'grant_type': 'player', 'username': user, 'password': '{{password}}', 'client_id': '{{oauth_client_id}}',
                'client_secret': '{{oauth_client_secret}}', 'deviceInformation': {'ip': '127.0.0.1', 'userAgent': 'Mozilla/5.0'}},
               ok + f"pm.environment.set('{var}', pm.response.json().access_token);")

def setup(cur):
    rc, pc, ag = f'rc{cur}', f'pc{cur}', f'ag{cur}'
    return [
        req(f'POST reward-configuration {cur}', 'POST', BO + '/bonus_configuration',
            {'name': '{{runTag}} ' + cur, 'displayName': '{{runTag}} ' + cur, 'type': 'free', 'model': 'direct',
             'offeringMethod': 'manual', 'currency': cur, 'validDuringDays': '7', 'claimingEvent': 'automatic',
             'offerAmount': '10', 'offerValidFor': 14},
            ok + f"pm.environment.set('{rc}', pm.response.json().id);", auth='BO_access_token'),
        req(f'PATCH enable reward-configuration {cur}', 'PATCH', BO + '/bonus_configuration/{{' + rc + '}}', {'status': 'enabled'},
            ok, auth='BO_access_token'),
        req(f'POST deposit_tier {cur}', 'POST', BO + '/promotion-configuration',
            {'name': '{{runTag}} ' + cur, 'currency': cur, 'startDate': '{{startDate}}', 'endDate': '{{endDate}}',
             'segmentIds': [], 'engagementModel': 'manual', 'engagementCode': '{{runTag}}-' + cur, 'type': 'deposit_tier',
             'playerPromotionLimit': 6},
            ok + f"pm.environment.set('{pc}', pm.response.json().id);", auth='BO_access_token'),
        req(f'POST tier 0-100 {cur}', 'POST', BO + '/promotion-configuration/{{' + pc + '}}/reward-aggregators',
            [{'type': 'tier', 'options': {'minAmount': 0, 'maxAmount': 100}, 'rewards': []}],
            ok + f"const j = pm.response.json(); pm.environment.set('{ag}', (Array.isArray(j) ? j[0] : j).id);",
            auth='BO_access_token'),
        req(f'POST free_bonus on tier {cur}', 'POST',
            BO + '/promotion-configuration/{{' + pc + '}}/reward-aggregator/{{' + ag + '}}/reward',
            {'type': 'free_bonus', 'rewardConfigurationId': '{{' + rc + '}}', 'quantity': 10, 'options': {'upToAmount': 10}},
            ok, auth='BO_access_token'),
        req(f'PATCH enable deposit_tier {cur}', 'PATCH', BO + '/promotion-configuration/{{' + pc + '}}', {'status': 'enabled'},
            ok, auth='BO_access_token'),
    ]

part1 = {'name': '1 Setup: one deposit tier per currency, each player opts in', 'item': (
    [botok] + setup('EUR') + setup('CAD') + [
        ptok('tokenA', '{{userA}}'),
        req('GW player A opts in (EUR)', 'PUT', '{{baseUrl}}/promotion-configuration/optin/{{runTag}}-EUR', None, ok, auth='tokenA'),
        ptok('tokenB', '{{userB}}'),
        req('GW player B opts in (CAD)', 'PUT', '{{baseUrl}}/promotion-configuration/optin/{{runTag}}-CAD', None, ok, auth='tokenB'),
    ])}

keyset = "const key = e => e.transactionId + '|' + e.promotionConfigurationId + '|' + JSON.stringify(e.rewards);\n"
part2 = {'name': '2 Compare per-player and domain routes', 'event': [
    {'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': guard.strip().split('\n')}}], 'item': [
    req('Per-player route, player A, both transactions', 'POST', PROMO + '/player/{{playerA}}/rewarding',
        {'transactionIds': ['{{txA}}', '{{txB}}'], 'event': 'deposit'},
        ok + "const j = pm.response.json(); pm.environment.set('perA', JSON.stringify(j));\n"
        "pm.test('player A gets entries for its own deposit', () => pm.expect(j.length).to.be.above(0));\n"
        "pm.test('player A gets only its own deposit', () => j.forEach(e => pm.expect(e.transactionId).to.eql(Number(pm.environment.get('txA')))));"),
    req('Per-player route, player B, both transactions', 'POST', PROMO + '/player/{{playerB}}/rewarding',
        {'transactionIds': ['{{txA}}', '{{txB}}'], 'event': 'deposit'},
        ok + "const j = pm.response.json(); pm.environment.set('perB', JSON.stringify(j));\n"
        "pm.test('player B gets entries for its own deposit', () => pm.expect(j.length).to.be.above(0));\n"
        "pm.test('player B gets only its own deposit', () => j.forEach(e => pm.expect(e.transactionId).to.eql(Number(pm.environment.get('txB')))));"),
    req('Domain route, both pairs: equals the two per-player calls', 'POST', PROMO + '/rewarding',
        {'transactions': [{'transactionId': '{{txA}}', 'playerId': '{{playerA}}'}, {'transactionId': '{{txB}}', 'playerId': '{{playerB}}'}],
         'event': 'deposit'},
        ok + keyset + "const j = pm.response.json();\n"
        "const expected = JSON.parse(pm.environment.get('perA')).concat(JSON.parse(pm.environment.get('perB'))).map(key).sort();\n"
        "pm.test('same entries as the per-player calls, compared as a set', () => pm.expect(j.map(key).sort()).to.eql(expected));\n"
        "pm.test('same entry shape as the per-player route', () => j.forEach(e => pm.expect(Object.keys(e).sort()).to.eql(['potentialWinnings','promotionConfigurationId','rewards','transactionId'])));"),
    req('Domain route, swapped pairs: empty', 'POST', PROMO + '/rewarding',
        {'transactions': [{'transactionId': '{{txA}}', 'playerId': '{{playerB}}'}, {'transactionId': '{{txB}}', 'playerId': '{{playerA}}'}],
         'event': 'deposit'},
        ok + "pm.test('no entry for a transaction under another player', () => pm.expect(pm.response.json()).to.eql([]));"),
    req('Domain route, other domain: empty', 'POST', '{{promotionUrl}}/api/domain/2/rewarding',
        {'transactions': [{'transactionId': '{{txA}}', 'playerId': '{{playerA}}'}], 'event': 'deposit'},
        ok + "pm.test('no entry from another domain', () => pm.expect(pm.response.json()).to.eql([]));"),
    req('Domain route, empty transactions: 400', 'POST', PROMO + '/rewarding', {'transactions': [], 'event': 'deposit'},
        "pm.test('status 400', () => pm.response.to.have.status(400));\n"
        "pm.test('validation body', () => pm.expect(pm.response.json().code).to.eql('VALIDATION_CONSTRAINT'));"),
    req('Domain route, entry without playerId: 400', 'POST', PROMO + '/rewarding',
        {'transactions': [{'transactionId': '{{txA}}'}], 'event': 'deposit'},
        "pm.test('status 400', () => pm.response.to.have.status(400));"),
]}

json.dump({'info': {'name': 'CLS-4314 local', 'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
           'item': [part1, part2]}, open('CLS-4314.postman_collection.json', 'w'), indent=1)
