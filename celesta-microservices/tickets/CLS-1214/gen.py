"""CLS-1214 collections. `python3 -I gen.py` writes both files next to this script.

CLS-1214.postman_collection.json            entry points only (gateway + backoffice); PO-runnable.
CLS-1214.dev-only.postman_collection.json   one direct call to payment (guard-signed); rejected before any write.

Nothing here carries a credential: the runner passes them as variables at run time.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'


def ev(kind, code):
    return {'listen': kind, 'script': {'type': 'text/javascript', 'exec': code.strip('\n').split('\n')}}


def req(name, method, url, body=None, test='', pre='', auth=None, query=None):
    h = [{'key': 'Content-Type', 'value': 'application/json'}] if body is not None else []
    if auth == 'bo':
        h.append({'key': 'Authorization', 'value': 'Bearer {{BO_access_token}}'})
    if auth == 'gw':
        h.append({'key': 'Authorization', 'value': 'Bearer {{access_token}}'})
    r = {'name': name, 'request': {'method': method, 'header': h, 'url': url}, 'event': []}
    if body is not None:
        r['request']['body'] = {'mode': 'raw', 'raw': body if isinstance(body, str) else json.dumps(body, indent=2)}
    if pre:
        r['event'].append(ev('prerequest', pre))
    if test:
        r['event'].append(ev('test', test))
    return r


# ---------------------------------------------------------------- shared JS
LOG_NON_200 = (
    "if (pm.response.code >= 400) console.log(pm.request.method + ' ' + pm.request.url.getPath() + ' -> '"
    " + pm.response.code + ' ' + pm.response.text().slice(0, 400));\n"
)
OK = LOG_NON_200 + "pm.test('status 200', () => pm.response.to.have.status(200));\n"
SET = (
    "const set = (k, v) => { const x = v === undefined || v === null ? '' : String(v); pm.collectionVariables.set(k, x);\n"
    "  try { pm.environment.set(k, x); } catch (e) { /* no environment selected: the collection variable carries it */ } };\n"
)
GET = "const get = k => pm.variables.get(k);\n"

# Poll helper. A request that polls re-queues itself until `done` or pollMax; assertions only run on the last try.
POLL_PRE = """
const key = 'poll_' + pm.info.requestName.replace(/[^A-Za-z0-9]/g, '_').slice(0, 60);
const attempt = Number(pm.variables.get(key) || 0);
if (attempt > 0) { setTimeout(function () {}, Number(pm.variables.get('pollDelayMs') || 5000)); }
"""


def poll_test(done_js, asserts_js):
    """done_js: JS expression (may use consts defined before it through `prep`); asserts_js: pm.test(...) calls."""
    return (
        "const key = 'poll_' + pm.info.requestName.replace(/[^A-Za-z0-9]/g, '_').slice(0, 60);\n"
        "const attempt = Number(pm.variables.get(key) || 0);\n"
        "const max = Number(pm.variables.get('pollMax') || 150);\n"
        + SET + GET +
        "let settled = false; let ctx = {};\n"
        "if (pm.response.code === 200) { try { ({ settled, ctx } = (function () {\n"
        + done_js +
        "\n})()); } catch (e) { console.log('poll parse error: ' + e.message); } }\n"
        "if (!settled && attempt < max) {\n"
        "  set(key, attempt + 1);\n"
        "  postman.setNextRequest(pm.info.requestName);\n"
        "} else {\n"
        "  set(key, 0);\n"
        "  pm.test('settled before the poll limit (' + attempt + ' retries)', () => pm.expect(settled).to.eql(true));\n"
        + asserts_js +
        "\n}\n"
    )


# ---------------------------------------------------------------- auth
BO = '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
GW = '{{baseUrl}}'

bo_token = lambda: req(
    'BO token', 'POST', '{{BO_baseUrl}}/oauth/2.0/token',
    {'grant_type': 'password', 'client_id': '{{BO_oauth_client_id}}', 'client_secret': '{{BO_oauth_client_secret}}',
     'username': '{{BO_username}}', 'password': '{{BO_password}}'},
    OK + SET + "set('BO_access_token', pm.response.json().access_token);")

player_token = lambda: req(
    'Player token', 'POST', '{{baseUrl}}/oauth/2.0/token',
    {'grant_type': 'player', 'username': '{{username}}', 'password': '{{password}}',
     'client_id': '{{oauth_client_id}}', 'client_secret': '{{oauth_client_secret}}',
     'deviceInformation': {'ip': '127.0.0.1', 'userAgent': 'Mozilla/5.0'}},
    OK + SET + "set('access_token', pm.response.json().access_token);")

# ---------------------------------------------------------------- 0 discovery (read-only) + balance precondition
discover = req(
    'GW payout configurations: pick Bank Transfer (auto), a second one, another method', 'GET',
    GW + '/payout/configurations?currency={{currency}}', None,
    OK + SET +
    """
const list = pm.response.json().list || [];
const on = list.filter(c => c.enabled !== false);
const auto = on.filter(c => c.method === 'bank_transfer_auto');
// methods the payout-delay command never picks up (PayoutDelayCommand::EXCLUDED_PAYOUT_METHODS)
const manual = ['manual', 'bank_transfer_manual', 'crypto_manual', 'inpay'];
const others = on.filter(c => c.method !== 'bank_transfer_auto');
const other = others.find(c => !manual.includes(c.method)) || others[0];   // prefer one the command pays on its own
pm.test('a Bank Transfer (auto) payout configuration exists in {{currency}}', () => pm.expect(auto.length).to.be.above(0));
if (!auto.length) { return; }
set('cfgA', auto[0].id);
set('cfgB', auto[1] ? auto[1].id : '');          // same method, other configuration: cell is skipped when absent
set('cfgOther', other ? other.id : '');          // other payout method: cell is skipped when absent
set('eAuto', other && !manual.includes(other.method) ? 'yes' : 'no');   // yes: E is paid on its own; no: E must stay validated
const used = [auto[0], auto[1], other].filter(Boolean);
const minLimit = Math.max(10, ...used.map(c => Math.ceil(Number(c.minLimit || 0))));
const maxLimit = Math.min(...used.map(c => c.maxLimit == null ? Infinity : Number(c.maxLimit)));
// distinct amounts per run, so the player history can tell the requests apart from older ones
const cents = (Date.now() % 89) + 10;
const amt = k => (minLimit + k + cents / 100).toFixed(2);
['D', 'A', 'B', 'C', 'E', 'G', 'F'].forEach((n, i) => set('amt' + n, amt(i)));
pm.test('amounts fit every configuration limit', () => pm.expect(Number(amt(6))).to.be.at.most(maxLimit));
set('needed', (7 * minLimit + 30).toFixed(2));
console.log('cfgA=' + auto[0].id + ' cfgB=' + (auto[1] ? auto[1].id : '-') + ' cfgOther=' + (other ? other.id + ':' + other.method : '-'));
""", auth='gw')

balance = req(
    'GW balance: how much to top up', 'GET', GW + '/wallet/balances', None,
    OK + SET + GET +
    """
const b = (pm.response.json().balances || []).find(x => x.currency === get('currency'));
const w = Number(b ? b.withdrawable : 0);
const need = Number(get('needed'));
set('topUp', w < need ? Math.ceil(need - w) : '');
""", auth='gw')

topup = req(
    'BO adjustment_up when the withdrawable balance is short', 'POST', BO + '/player/{{playerId}}/wallet/transaction',
    {'type': 'adjustment_up', 'amount': '{{topUp}}', 'currency': '{{currency}}', 'note': 'QA CLS-1214 balance',
     'reason': 'payment_provider_issue'},
    OK, auth='bo', pre="if (!pm.variables.get('topUp')) { pm.execution.skipRequest(); }")

f0 = {'name': '0 Auth and discovery (read-only), balance', 'item': [player_token(), discover, balance, bo_token(), topup]}


# ---------------------------------------------------------------- 1 player requests the withdrawals
def withdraw(var, label, cfg, amt, skip_if_empty=None):
    pre = ''
    if skip_if_empty:
        pre = "if (!pm.variables.get('%s')) { pm.execution.skipRequest(); }" % skip_if_empty
    return req(
        'GW withdraw %s: %s' % (var, label), 'POST', GW + '/wallet/withdrawal',
        '{\n  "paymentInformation": { "paymentConfigurationId": {{%s}} },\n  "amount": {{%s}},\n  "ip": "127.0.0.1"\n}' % (cfg, amt),
        OK + SET +
        "const j = pm.response.json();\n"
        "pm.test('request created', () => pm.expect(j.id).to.not.be.undefined);\n"
        "set('wdr%s', j.id);\n" % var, pre=pre, auth='gw')


f1 = {'name': '1 GW player requests withdrawals', 'item': [
    player_token(),
    # D first: its id is below the group's, so the lead (lowest id of the group) is not simply "the first created"
    withdraw('D', 'stays pending, never validated (stand-in for on hold)', 'cfgA', 'amtD'),
    withdraw('A', 'bank_transfer_auto', 'cfgA', 'amtA'),
    withdraw('B', 'bank_transfer_auto', 'cfgA', 'amtB'),
    withdraw('C', 'bank_transfer_auto', 'cfgA', 'amtC'),
    withdraw('E', 'other payout method', 'cfgOther', 'amtE', skip_if_empty='cfgOther'),
    withdraw('G', 'bank_transfer_auto, other configuration', 'cfgB', 'amtG', skip_if_empty='cfgB'),
]}


# ---------------------------------------------------------------- 2 backoffice validates
def validate(var, skip_if_empty=None):
    pre = ("if (!pm.variables.get('%s')) { pm.execution.skipRequest(); }" % skip_if_empty) if skip_if_empty else ''
    return req(
        'BO validate %s' % var, 'PATCH', BO + '/player/{{playerId}}/withdrawal_request/{{wdr%s}}' % var,
        {'status': 'validated'},
        OK +
        "const j = pm.response.json();\n"
        "pm.test('validated', () => pm.expect(j.status).to.eql('validated'));\n"
        # the PATCH answers with the wallet's own serialisation: the group column must not leak through it
        "pm.test('payout group column not exposed', () => pm.expect(JSON.stringify(j)).to.not.match(/payout_?group/i));",
        pre=pre, auth='bo')


f2 = {'name': '2 BO validates (the lowest id of A, B, C is the lead)', 'item': [
    bo_token(), validate('A'), validate('B'), validate('C'), validate('E', 'cfgOther'), validate('G', 'cfgB'),
]}

# ---------------------------------------------------------------- 3 BO verify: whole group paid or error together
IDS_BODY = "pm.request.body.update(JSON.stringify({ filter: { ids: ['A','B','C','D','E','G'].map(n => pm.variables.get('wdr' + n)).filter(Boolean).map(Number) }, limit: 50 }));"

group_done = """
const rows = pm.response.json();
const by = {}; rows.forEach(r => by[String(r.id)] = r);
const id = n => String(pm.variables.get('wdr' + n));
const term = s => s === 'paid' || s === 'error';
const g = ['A','B','C'].map(n => by[id(n)]);
const gOk = g.every(r => r && term(r.status));
const gSingle = !pm.variables.get('wdrG') || (by[id('G')] && term(by[id('G')].status));
const eOk = !pm.variables.get('wdrE') || pm.variables.get('eAuto') !== 'yes' || (by[id('E')] && term(by[id('E')].status));
return { settled: gOk && gSingle && eOk, ctx: { by, id } };
"""
group_asserts = """
const { by, id } = ctx;
if (!settled) { return; }
const A = by[id('A')], B = by[id('B')], C = by[id('C')], D = by[id('D')];
const sts = [A, B, C].map(r => r.status);
pm.test('A, B and C ended in the same status (the whole group)', () => pm.expect(new Set(sts).size).to.eql(1));
pm.test('the group is paid or error', () => pm.expect(['paid', 'error']).to.include(sts[0]));
// criteria 4 and 5 are conditional (success -> all paid, failure -> all error): they are only pinned when the run says
// which branch it is on. Without expectedGroupStatus the run proves the group moves together, nothing more.
const want = pm.variables.get('expectedGroupStatus');
if (want === 'paid') { pm.test('criterion 4: the combined payout succeeded, every request is paid', () => pm.expect(sts).to.eql(['paid', 'paid', 'paid'])); }
else if (want === 'error') { pm.test('criterion 5: the combined payout failed, every request is in error', () => pm.expect(sts).to.eql(['error', 'error', 'error'])); }
else { console.log('expectedGroupStatus not set: criteria 4 and 5 checked for consistency only (group ended ' + sts[0] + ')'); }
// each request keeps its own amount
['A', 'B', 'C'].forEach(n => pm.test(n + ' keeps its own amount', () => pm.expect(Number(by[id(n)].amount)).to.eql(Number(pm.variables.get('amt' + n)))));
pm.test('D (never validated) is still pending, not in the group', () => pm.expect(D.status).to.eql('pending'));
if (pm.variables.get('wdrE')) {
  if (pm.variables.get('eAuto') === 'yes') { pm.test('E (other method, paid automatically) was paid on its own, not with the group', () => pm.expect(['paid', 'error']).to.include(by[id('E')].status)); }
  else { pm.test('E (manual method) is never picked up by the command: still validated', () => pm.expect(by[id('E')].status).to.eql('validated')); }
}
set('grpStatus', sts[0]);
const sum = (k) => ['A','B','C'].reduce((s, n) => s + Number(by[id(n)][k] || 0), 0);
set('grpPayoutAmount', sum('payoutAmount').toFixed(2));
const fees = ['A','B','C'].map(n => by[id(n)].fee);
set('grpFee', fees.every(f => f === null || f === undefined) ? 'null' : sum('fee').toFixed(2));
"""
verify_group = req(
    'BO list A..G: wait for the group to settle', 'POST', BO + '/withdrawal_requests', '{}',
    poll_test(group_done, group_asserts), pre=POLL_PRE + IDS_BODY, auth='bo')

f3 = {'name': '3 BO verify: the group settles together, each request keeps its amount', 'item': [bo_token(), verify_group]}

# ---------------------------------------------------------------- 4 player history stays one line per request
history = req(
    'GW wallet transactions: one withdraw per request', 'GET', GW + '/wallet/transactions?type[]=withdraw&currency={{currency}}',
    None,
    OK + GET +
    """
const j = pm.response.json();
const list = Array.isArray(j) ? j : (j.transactions || j.data || []);
const amounts = list.map(t => Math.abs(Number(t.amount)).toFixed(2));
['A', 'B', 'C'].forEach(n => pm.test('request ' + n + ' still has its own withdraw transaction', () => pm.expect(amounts).to.include(Number(get('amt' + n)).toFixed(2))));
// the status the player sees, per request: the status of that request's own withdraw transaction
const statusOf = n => (list.find(t => Math.abs(Number(t.amount)).toFixed(2) === Number(get('amt' + n)).toFixed(2)) || {}).status;
const pst = ['A', 'B', 'C'].map(statusOf);
['A', 'B', 'C'].forEach((n, i) => pm.test('request ' + n + ' shows its own status to the player (' + pst[i] + ')', () => pm.expect(pst[i]).to.be.a('string')));
pm.test('the group settled together on the player side too', () => pm.expect(new Set(pst).size).to.eql(1));
if (get('grpStatus') === 'paid') { pm.test('a paid group shows success on every withdraw transaction', () => pm.expect(pst).to.eql(['success', 'success', 'success'])); }
const total = ['A', 'B', 'C'].reduce((s, n) => s + Number(get('amt' + n)), 0).toFixed(2);
pm.test('no transaction for the summed amount: the player history is not merged', () => pm.expect(amounts).to.not.include(total));
""", auth='gw')

f4 = {'name': '4 GW player history: still one line per request', 'item': [player_token(), history]}

# ---------------------------------------------------------------- 5 BO report: one payout line with every id
REPORT_BODY = '{\n  "filter": { "playerId": "{{playerId}}" },\n  "limit": 100,\n  "order": { "field": "id", "direction": "desc" }\n}'

report_done = """
const lines = pm.response.json();
const L = Array.isArray(lines) ? lines : (lines.data || []);
const ids = ['A','B','C'].map(n => Number(pm.variables.get('wdr' + n))).sort((a, b) => a - b);
const lead = ids[0];
const line = L.find(l => Number(l.withdrawRequestId) === lead && l.type === 'withdraw');
const gId = pm.variables.get('wdrG');
const gLine = gId ? L.find(l => Number(l.withdrawRequestId) === Number(gId) && l.type === 'withdraw') : true;
const eId = pm.variables.get('wdrE');
const eLine = eId && pm.variables.get('eAuto') === 'yes' ? L.find(l => Number(l.withdrawRequestId) === Number(eId) && l.type === 'withdraw') : true;
return { settled: !!line && !!gLine && !!eLine, ctx: { L, ids, lead, line, gLine, eLine } };
"""
report_asserts = """
const { L, ids, lead, line, gLine, eLine } = ctx;
if (!settled) { return; }
const mentions = n => L.filter(l => (l.withdrawRequestIds || []).map(Number).includes(Number(n)));
pm.test('the payout line carries every combined id, ascending', () => pm.expect(line.withdrawRequestIds.map(Number)).to.eql(ids));
pm.test('withdrawRequestId is the lead (lowest id), unchanged', () => pm.expect(Number(line.withdrawRequestId)).to.eql(lead));
ids.forEach(n => pm.test('request ' + n + ' appears in exactly one report line', () => pm.expect(mentions(n).length).to.eql(1)));
['B', 'C'].forEach(n => pm.test(n + ' has no payout line of its own', () => pm.expect(L.filter(l => Number(l.withdrawRequestId) === Number(get('wdr' + n))).length).to.eql(0)));
['D', 'E'].forEach(n => { if (get('wdr' + n)) pm.test(n + ' is not in the combined line', () => pm.expect(line.withdrawRequestIds.map(Number)).to.not.include(Number(get('wdr' + n)))); });
pm.test('one payout for the total amount', () => pm.expect(Number(line.amount)).to.be.closeTo(Number(get('grpPayoutAmount')), 0.01));
const feeWant = get('grpFee');
pm.test('fee is the sum of the members fees, null when none has one', () => {
  if (feeWant === 'null') { pm.expect(line.fee === null || line.fee === undefined).to.eql(true); }
  else { pm.expect(Number(line.fee)).to.be.closeTo(Number(feeWant), 0.01); }
});
const wantLine = get('grpStatus') === 'paid' ? 'success' : 'failure';
pm.test('line status follows the group (' + get('grpStatus') + ' -> ' + wantLine + ')', () => pm.expect(line.status).to.eql(wantLine));
if (get('wdrE') && get('eAuto') === 'yes') {
  pm.test('E (other payout method) is paid in its own payout, never combined', () => pm.expect(eLine.withdrawRequestIds.map(Number)).to.eql([Number(get('wdrE'))]));
}
if (get('wdrG')) {
  pm.test('G (other configuration) is paid in its own payout', () => pm.expect(gLine.withdrawRequestIds.map(Number)).to.eql([Number(get('wdrG'))]));
}
"""
report = req(
    'BO transaction report: the payout line of the group', 'POST', BO + '/finance/transaction_reports', REPORT_BODY,
    poll_test(report_done, report_asserts), pre=POLL_PRE, auth='bo')

f5 = {'name': '5 BO report: one payout line exposing every combined id', 'item': [bo_token(), report]}

# ---------------------------------------------------------------- 6/7 a group of one, paid as today
f6 = {'name': '6 Group of one: request and validate F (alone, after the first run)', 'item': [
    player_token(), withdraw('F', 'bank_transfer_auto, alone', 'cfgA', 'amtF'), bo_token(), validate('F')]}

single_done = """
const rows = pm.response.json();
const r = rows.find(x => String(x.id) === String(pm.variables.get('wdrF')));
const term = s => s === 'paid' || s === 'error';
return { settled: !!r && term(r.status), ctx: { r } };
"""
single_asserts = """
const { r } = ctx;
if (!settled) { return; }
pm.test('F keeps its own amount', () => pm.expect(Number(r.amount)).to.eql(Number(get('amtF'))));
set('fPayoutAmount', r.payoutAmount);
set('fFee', r.fee === null || r.fee === undefined ? 'null' : r.fee);
set('fStatus', r.status);
"""
single_status = req(
    'BO list F: wait for the single request to settle', 'POST', BO + '/withdrawal_requests', '{}',
    poll_test(single_done, single_asserts),
    pre=POLL_PRE + "pm.request.body.update(JSON.stringify({ filter: { ids: [Number(pm.variables.get('wdrF'))] }, limit: 5 }));",
    auth='bo')

single_done_r = """
const lines = pm.response.json();
const L = Array.isArray(lines) ? lines : (lines.data || []);
const f = Number(pm.variables.get('wdrF'));
const line = L.find(l => Number(l.withdrawRequestId) === f && l.type === 'withdraw');
return { settled: !!line, ctx: { L, f, line } };
"""
single_asserts_r = """
const { L, f, line } = ctx;
if (!settled) { return; }
pm.test('single payout lists only its own id', () => pm.expect(line.withdrawRequestIds.map(Number)).to.eql([f]));
pm.test('amount is the request payout amount', () => pm.expect(Number(line.amount)).to.be.closeTo(Number(get('fPayoutAmount')), 0.01));
pm.test('fee is the request fee (null when none)', () => {
  if (get('fFee') === 'null') { pm.expect(line.fee === null || line.fee === undefined).to.eql(true); }
  else { pm.expect(Number(line.fee)).to.be.closeTo(Number(get('fFee')), 0.01); }
});
pm.test('F is not part of the first payout', () => pm.expect(L.filter(l => (l.withdrawRequestIds || []).map(Number).includes(f)).length).to.eql(1));
"""
single_report = req(
    'BO transaction report: the payout line of F', 'POST', BO + '/finance/transaction_reports', REPORT_BODY,
    poll_test(single_done_r, single_asserts_r), pre=POLL_PRE, auth='bo')

f7 = {'name': '7 Group of one: settles and reports as today', 'item': [bo_token(), single_status, single_report]}

VARS = {
    'BO_baseUrl': 'http://localhost:84', 'baseUrl': 'http://localhost:93', 'domainId': '1', 'playerId': '1',
    'currency': 'EUR', 'pollMax': '150', 'pollDelayMs': '5000', 'expectedGroupStatus': '',
}
CAPTURED = ['BO_access_token', 'access_token', 'cfgA', 'cfgB', 'cfgOther', 'amtA', 'amtB', 'amtC', 'amtD', 'amtE', 'amtF',
            'amtG', 'eAuto', 'needed', 'topUp', 'wdrA', 'wdrB', 'wdrC', 'wdrD', 'wdrE', 'wdrF', 'wdrG', 'grpStatus',
            'grpPayoutAmount', 'grpFee', 'fPayoutAmount', 'fFee', 'fStatus']
CREDENTIALS = ['BO_oauth_client_id', 'BO_oauth_client_secret', 'BO_username', 'BO_password',
               'oauth_client_id', 'oauth_client_secret', 'username', 'password']

main = {
    'info': {'name': 'CLS-1214 combine withdrawal requests into one payout (entry points only)', 'schema': SCHEMA,
             'description': 'Gateway (player) and backoffice only. Credentials are runner variables, never in the file.'},
    'item': [f0, f1, f2, f3, f4, f5, f6, f7],
    'variable': [{'key': k, 'value': v} for k, v in VARS.items()]
    + [{'key': k, 'value': ''} for k in CREDENTIALS + CAPTURED],
}
json.dump(main, open(os.path.join(HERE, 'CLS-1214.postman_collection.json'), 'w'), indent=2)

# ---------------------------------------------------------------- DEV-ONLY: payment rejects a list over 512 characters
GUARD = """
const url = pm.variables.replaceIn(pm.request.url.toString());
const m = url.match(/^https?:\\/\\/([^\\/:]+)(?::(\\d+))?([^?]*)/);
const method = pm.request.method.toUpperCase();
let signed = method + m[1] + decodeURIComponent(m[3]);
if (['POST', 'PUT', 'PATCH'].includes(method)) { signed += CryptoJS.MD5(pm.variables.replaceIn(pm.request.body.raw)).toString(); }
pm.request.headers.upsert({ key: 'x-guard-secret', value: CryptoJS.HmacSHA256(signed, pm.variables.get('guardKey')).toString() });
"""
# 70 nine-digit ids: the stored JSON ([a,b,...], no spaces) is 70 * 10 + 1 = 701 characters, over the 512 of the column
BIG = [900000001 + i for i in range(70)]
too_long = req(
    'DEV-ONLY payment: payout with 70 request ids -> 400, nothing written', 'POST',
    '{{paymentUrl}}/domain/{{domainId}}/payment-configuration/{{cfgA}}/payout',
    {'payoutInformation': {}, 'amount': 100, 'fee': None, 'clientId': '{{playerId}}',
     'additionalData': {'withdrawRequestId': str(BIG[0]), 'withdrawRequestIds': BIG}},
    "console.log('400 body: ' + pm.response.text().slice(0, 600));\n"
    "pm.test('status 400', () => pm.response.to.have.status(400));\n"
    "pm.test('the violation is on withdrawRequestIds', () => pm.expect(pm.response.text()).to.include('withdrawRequestIds'));",
    pre=GUARD)
no_lead = req(
    'DEV-ONLY payment: lead not in the list -> 400, nothing written', 'POST',
    '{{paymentUrl}}/domain/{{domainId}}/payment-configuration/{{cfgA}}/payout',
    {'payoutInformation': {}, 'amount': 100, 'fee': None, 'clientId': '{{playerId}}',
     'additionalData': {'withdrawRequestId': '900000999', 'withdrawRequestIds': [900000001, 900000002]}},
    "pm.test('status 400', () => pm.response.to.have.status(400));", pre=GUARD)
dev = {
    'info': {'name': 'CLS-1214 DEV-ONLY: payment rejects an invalid combined list', 'schema': SCHEMA,
             'description': 'Direct calls to payment, guard-signed. Both are rejected by the form before any lock, row or provider call. Not PO-runnable: payment is not reachable from preprod.'},
    'item': [{'name': 'DEV-ONLY payment payout form', 'item': [too_long, no_lead]}],
    'variable': [{'key': 'paymentUrl', 'value': 'http://localhost:82'}, {'key': 'domainId', 'value': '1'},
                 {'key': 'playerId', 'value': '1'}, {'key': 'cfgA', 'value': '1'}, {'key': 'guardKey', 'value': ''}],
}
json.dump(dev, open(os.path.join(HERE, 'CLS-1214.dev-only.postman_collection.json'), 'w'), indent=2)
print('ok')
