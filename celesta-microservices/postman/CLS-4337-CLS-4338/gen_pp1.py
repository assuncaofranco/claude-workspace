"""Generates the CLS-4337-CLS-4338 pp1 collection: entry points only, plus one human step in the game."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BO = "{{BO_baseUrl}}/api/gateway/domain/{{domainId}}"


def req(name, method, url, body=None, test="", auth=None, pre=""):
    h = [{"key": "Content-Type", "value": "application/json"}] if body is not None else []
    if auth == "bo":
        h.append({"key": "Authorization", "value": "Bearer {{BO_access_token}}"})
    if auth == "gw":
        h.append({"key": "Authorization", "value": "Bearer {{access_token}}"})
    r = {"name": name, "request": {"method": method, "header": h, "url": url}, "event": []}
    if body is not None:
        r["request"]["body"] = {"mode": "raw", "raw": body if isinstance(body, str) else json.dumps(body, indent=2)}
    if test:
        r["event"].append({"listen": "test", "script": {"type": "text/javascript", "exec": test.strip().split("\n")}})
    if pre:
        r["event"].append({"listen": "prerequest", "script": {"type": "text/javascript", "exec": pre.strip().split("\n")}})
    return r


ok = "pm.test('status 200', () => pm.response.to.have.status(200));\n"
bo_token = req("BO token", "POST", "{{BO_baseUrl}}/oauth/2.0/token", {
    "grant_type": "password", "client_id": "{{BO_oauth_client_id}}", "client_secret": "{{BO_oauth_client_secret}}",
    "username": "{{BO_username}}", "password": "{{BO_password}}"},
    ok + "pm.collectionVariables.set('BO_access_token', pm.response.json().access_token);")
gw_token = req("Player token", "POST", "{{baseUrl}}/oauth/2.0/token", {
    "grant_type": "player", "username": "{{username}}", "password": "{{password}}",
    "client_id": "{{oauth_client_id}}", "client_secret": "{{oauth_client_secret}}",
    "deviceInformation": {"ip": "{{launchIp}}", "userAgent": "Mozilla/5.0"}},
    ok + "pm.collectionVariables.set('access_token', pm.response.json().access_token);")

WALLETS = BO + "/player/{{playerId}}/wallets"
by_cur = "const w = c => pm.response.json().find(x => x.currency === c);\nconsole.log(JSON.stringify(pm.response.json()));\n"

f1 = {"name": "1 BO: USD free-round bonus offered to the EUR player", "item": [
    bo_token,
    req("player wallets before", "GET", WALLETS, None, ok + by_cur + """
pm.test('EUR wallet exists', () => pm.expect(w('EUR')).to.be.ok);
pm.collectionVariables.set('eurRealBefore', w('EUR').realBalance);
const pad = n => String(n).padStart(2, '0');
const d = new Date(Date.now() - 60 * 1000);
pm.collectionVariables.set('testFrom', `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`);
console.log('testFrom', pm.collectionVariables.get('testFrom'));""", auth="bo"),
    req("create free-round bonus configuration in USD (CGA game)", "POST", BO + "/bonus_configuration", {
        "name": "{{runTag}} CGA fr USD", "displayName": "{{runTag}} CGA fr USD", "type": "free_rounds",
        "model": "direct", "offeringMethod": "manual", "currency": "{{bonusCurrency}}", "reason": "test",
        "validDuringDays": 3, "offerValidFor": 2, "claimingEvent": "direct",
        "freeRoundConfiguration": {"freeRoundsGameGateway": "{{gameGatewayId}}", "freeRoundsGameStudio": "{{gameStudioId}}",
                                   "gameIds": [{"id": "{{gameId}}"}], "amount": "{{freeRoundBet}}"}},
        ok + "pm.collectionVariables.set('bonusConfigId', pm.response.json().id);", auth="bo",
        pre="if (!pm.collectionVariables.get('runTag')) pm.collectionVariables.set('runTag', 'CLS-4338-' + Date.now());"),
    req("enable it", "PATCH", BO + "/bonus_configuration/{{bonusConfigId}}", {"status": "enabled"},
        ok + "pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));", auth="bo"),
    req("offer it to the player", "POST", BO + "/player/{{playerId}}/bonus_configuration/{{bonusConfigId}}/offer",
        {"playerId": "{{playerId}}", "freeRoundsRoundCount": "{{roundCount}}", "message": "QA CLS-4338"},
        ok + "const j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\n"
             "pm.collectionVariables.set('bonusId', j.id);\nconsole.log('bonusId', j.id);", auth="bo"),
]}

f2 = {"name": "2 GW: player claims it and launches the CGA game in EUR", "item": [
    gw_token,
    req("list bonuses", "GET", "{{baseUrl}}/bonuses", None, ok + """
const list = pm.response.json().bonus || pm.response.json();
const want = String(pm.collectionVariables.get('bonusId'));
const b = list.find(x => String(x.id) === want || String(x.id).endsWith('_' + want));
pm.test('bonus listed', () => pm.expect(b).to.not.be.undefined);
if (b) pm.collectionVariables.set('gwBonusId', String(b.id));""", auth="gw"),
    req("claim it", "POST", "{{baseUrl}}/bonuses/claim", {"bonusIds": ["{{gwBonusId}}"]},
        ok + "pm.test('claimed', () => pm.expect(pm.response.json()[0].status).to.eql('claimed'));", auth="gw"),
    req("launch the game (open gameUrl in a browser and play every free round)", "POST",
        "{{baseUrl}}/en/game/{{gameId}}/launch",
        {"ip": "{{launchIp}}", "device": "desktop", "lobbyUrl": "http://localhost", "depositUrl": "http://localhost"},
        ok + """
const m = (pm.response.json().html || '').match(/src="([^"]+)"/);
pm.test('game url in launch response', () => pm.expect(m).to.not.be.null);
if (m) { const url = m[1].replace(/&amp;/g, '&'); pm.collectionVariables.set('gameLaunchUrl', url); console.log('OPEN IN BROWSER:', url); }""",
        auth="gw"),
]}

f3 = {"name": "3 BO: claim created the USD wallet", "item": [
    bo_token,
    req("player wallets after claim", "GET", WALLETS, None, ok + by_cur + """
pm.test('USD wallet created by the claim', () => pm.expect(w('USD')).to.be.ok);
pm.test('EUR wallet still there', () => pm.expect(w('EUR')).to.be.ok);""", auth="bo"),
]}

GAME_TX = """
const txs = pm.response.json();
console.log(JSON.stringify(txs.map(t => ({id: t.id, type: t.type, status: t.status, amount: t.amount, currency: t.currency, errors: t.errors}))));
pm.test('no failed transaction in the free-round rounds', () => pm.expect(txs.filter(t => t.status === 'failure')).to.have.length(0));
pm.test('the free-round credit is there and succeeded', () => pm.expect(txs.filter(t => t.status === 'success' && t.type !== 'bet').length).to.be.above(0));"""

f4 = {"name": "4 BO verify (after playing the free rounds)", "item": [
    bo_token,
    req("player rounds of the game since the test started", "POST", BO + "/game-rounds",
        '{\n  "limit": 50,\n  "order": {"field": "id", "direction": "desc"},\n  "filter": {\n'
        '    "playerIds": [{{playerId}}],\n    "createdAtRanges": [{"from": "{{testFrom}}", "to": "{{testTo}}"}]\n  }\n}',
        ok + """
const rounds = pm.response.json().filter(r => !r.game || String(r.game.id) === String(pm.collectionVariables.get('gameId')));
console.log('rounds', rounds.map(r => `${r.id} ${r.game && r.game.name}`).join(' | '));
pm.test('player has rounds of the game in the window', () => pm.expect(rounds.length).to.be.above(0));
pm.collectionVariables.set('roundIds', JSON.stringify(rounds.map(r => r.id)));""", auth="bo", pre="""
const pad = n => String(n).padStart(2, '0');
const fmt = d => `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
if (!pm.variables.get('testTo')) pm.collectionVariables.set('testTo', fmt(new Date(Date.now() + 600 * 1000)));"""),
    req("transactions of those rounds", "POST", BO + "/game-transactions", '{\n  "filter": {"gameRoundIds": {{roundIds}}}\n}',
        ok + GAME_TX, auth="bo"),
    req("player wallets: win landed on the USD bonus, EUR untouched", "GET", WALLETS, None, ok + by_cur + """
pm.test('EUR real balance unchanged', () => pm.expect(w('EUR').realBalance).to.eql(Number(pm.variables.get('eurRealBefore'))));
console.log('USD wallet after', JSON.stringify(w('USD')));""", auth="bo"),
]}

defaults = {
    "BO_baseUrl": "", "baseUrl": "", "domainId": "56", "playerId": "282570", "launchIp": "87.32.0.1",
    "gameId": "72631", "gameGatewayId": "52", "gameStudioId": "1765", "bonusCurrency": "USD",
    "freeRoundBet": "1", "roundCount": "10",
}
captured = ["runTag", "BO_access_token", "access_token", "bonusConfigId", "bonusId", "gwBonusId", "gameLaunchUrl",
            "testFrom", "testTo", "eurRealBefore", "roundIds"]
c = {
    "info": {"name": "CLS-4337-CLS-4338 pp1 free-round win for a bonus in another currency",
             "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
    "item": [f1, f2, f3, f4],
    "variable": [{"key": k, "value": v} for k, v in defaults.items()] + [{"key": k, "value": ""} for k in captured],
}
with open(os.path.join(HERE, "CLS-4337-CLS-4338.pp1.postman_collection.json"), "w") as f:
    json.dump(c, f, indent=2)
