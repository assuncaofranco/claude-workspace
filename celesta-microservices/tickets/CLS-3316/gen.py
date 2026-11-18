import json, re
# CLS-3316 reward offering reasons on configurations and bonuses. Entry points only (BO + gateway): nothing here
# writes to a database or calls an internal service. Credentials never go in the file: they come from the vault into
# the runner's environment (run.sh).
#
# Source of the cells: the parent's acceptance criteria, then what the plans decided after them (CLS-4743 #602,
# CLS-4744 #603, CLS-4745 #3336, CLS-4747 #813, CLS-5130 #319 and tickets/CLS-3316/sdd.md). Where a decision changes a
# criterion, the request's description says which one (search "CRITERION CHANGED").

CRIT = 'CRITERION CHANGED: '

def body_json(b):
    s = json.dumps(b, indent=2)
    return re.sub(r'"@@(\w+)@@"', r'{{\1}}', s)  # "@@rA@@" -> {{rA}}: an unquoted number once resolved

def req(name, method, url, body=None, test='', bo=None, pre='', desc='', form=None):
    h = [{'key': 'Content-Type', 'value': 'application/json'}] if body is not None else []
    if bo is True: h.append({'key': 'Authorization', 'value': 'Bearer {{BO_access_token}}'})
    if bo is False: h.append({'key': 'Authorization', 'value': 'Bearer {{access_token}}'})
    r = {'name': name, 'request': {'method': method, 'header': h, 'url': url}, 'event': []}
    if desc: r['request']['description'] = desc
    if body is not None: r['request']['body'] = {'mode': 'raw', 'raw': body_json(body)}
    if form is not None: r['request']['body'] = {'mode': 'formdata', 'formdata': form}
    if test: r['event'].append({'listen': 'test', 'script': {'type': 'text/javascript', 'exec': test.strip().split('\n')}})
    if pre: r['event'].append({'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': pre.strip().split('\n')}})
    return r

log = "if (pm.response.code >= 300) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 600));\n"
def status(code): return log + f"pm.test('status {code}', () => pm.response.to.have.status({code}));\n"
ok = status(200)
setv = lambda k, v: f"pm.collectionVariables.set('{k}', {v});\n"
num = lambda v: f"Number(pm.variables.get('{v}'))"
BO = '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
GW = '{{baseUrl}}'

def skip_if_empty(*vars_):
    c = ' || '.join(f"!pm.variables.get('{v}')" for v in vars_)
    return f"if ({c}) {{ console.log('skipped: {', '.join(vars_)} empty'); if (pm.execution && pm.execution.skipRequest) pm.execution.skipRequest(); }}"

UNKNOWN_ID = 2147483000  # positive, fits INT, no reason has it

# ---- auth
bo_token = lambda: req('BO token', 'POST', '{{BO_baseUrl}}/oauth/2.0/token',
    {"grant_type": "password", "client_id": "{{BO_oauth_client_id}}", "client_secret": "{{BO_oauth_client_secret}}",
     "username": "{{BO_username}}", "password": "{{BO_password}}"},
    ok + setv('BO_access_token', 'pm.response.json().access_token'))
gw_token = lambda: req('Player token', 'POST', '{{baseUrl}}/oauth/2.0/token',
    {"grant_type": "player", "username": "{{username}}", "password": "{{password}}", "client_id": "{{oauth_client_id}}",
     "client_secret": "{{oauth_client_secret}}", "deviceInformation": {"ip": "127.0.0.1", "userAgent": "Mozilla/5.0"}},
    ok + setv('access_token', 'pm.response.json().access_token'))

# ---- reasons
def reason_post(name, var, domain='{{domainId}}', skip_if_set=False):
    pre = ("if (!pm.variables.get('runTag')) { const t = Date.now(); pm.collectionVariables.set('runTag', 'CLS-3316 ' + t); "
               "pm.collectionVariables.set('code', 'cls3316-' + t); "
               "const d = n => new Date(t + n*86400000).toISOString().slice(0,10); "
               "pm.collectionVariables.set('startDate', d(-1) + ' 00:00:00'); pm.collectionVariables.set('endDate', d(7) + ' 23:59:59'); }\n")
    if skip_if_set: pre += f"if (pm.variables.get('{var}')) {{ if (pm.execution && pm.execution.skipRequest) pm.execution.skipRequest(); }}"
    return req(f'POST reason {name} -> {var}', 'POST', '{{BO_baseUrl}}/api/gateway/domain/' + domain + '/reward-offering-reason',
        {"reason": "{{runTag}} " + name},
        ok + "const j = pm.response.json();\npm.test('reason created', () => pm.expect(j.id).to.be.a('number'));\n"
        + setv(var, 'j.id') + setv(var + 'Name', 'j.reason'), bo=True, pre=pre)
def reason_delete(var):
    return req(f'DELETE reason {var}', 'DELETE', BO + '/reward-offering-reason/{{' + var + '}}', None, status(204), bo=True)

# ---- configurations
def free_body(name, claiming='direct', **extra):
    b = {"name": "{{runTag}} " + name, "displayName": "{{runTag}} " + name, "type": "free", "model": "direct",
         "offeringMethod": "manual", "currency": "{{currency}}", "validDuringDays": "7", "claimingEvent": claiming,
         "offerAmount": "1", "offerValidFor": 7, "reason": "goodwill"}
    b.update(extra)
    return b

def cfg_asserts(reason_var=None, expect_legacy='goodwill'):
    """The configuration body returned by the BO: reasonId and reasonName of the reason, the legacy key still there."""
    rid = num(reason_var) if reason_var else 'null'
    rname = f"pm.variables.get('{reason_var}Name')" if reason_var else 'null'
    t = ("const j = pm.response.json();\n"
         f"pm.test('reasonId = {reason_var or 'null'}', () => pm.expect(j.reasonId).to.eql({rid}));\n"
         f"pm.test('reasonName = {reason_var or 'null'}', () => pm.expect(j.reasonName).to.eql({rname}));\n")
    if expect_legacy:
        t += f"pm.test('legacy reason still returned', () => pm.expect(j.reason).to.eql('{expect_legacy}'));\n"
    return t

def cfg_post(name, var, reason_var=None, claiming='direct', omit_reason_id=False, desc='', legacy=True, extra=None):
    b = free_body(name, claiming)
    if not legacy: b.pop('reason')
    if not omit_reason_id: b['reasonId'] = "@@" + reason_var + "@@" if reason_var else None
    if extra: b.update(extra)
    return req(f'POST config {name} -> {var}', 'POST', BO + '/bonus_configuration', b,
        ok + setv(var, 'pm.response.json().id') + cfg_asserts(reason_var, 'goodwill' if legacy else None), bo=True, desc=desc)

def cfg_enable(var):
    return req(f'PATCH enable {var}', 'PATCH', BO + '/bonus_configuration/{{' + var + '}}', {"status": "enabled"},
        ok + "pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));", bo=True)

def refused(field='reasonId', extra_test=''):
    return (log + "pm.test('status 400', () => pm.response.to.have.status(400));\n"
            f"pm.test('error is on {field}', () => pm.expect(pm.response.text()).to.include('{field}'));\n" + extra_test)

def cfg_get(var, reason_var, name):
    return req(name, 'GET', BO + '/bonus_configuration/{{' + var + '}}', None, ok + cfg_asserts(reason_var), bo=True)

def cfg_put(name, var, body_extra, reason_var, desc='', omit=(), legacy_expected='goodwill'):
    b = free_body('edit')
    b['name'] = '{{runTag}} ' + var
    b['displayName'] = '{{runTag}} ' + var
    b['status'] = 'enabled'   # promotion's PUT replaces the whole configuration: without status it comes back disabled
    b.update(body_extra)
    for k in omit: b.pop(k, None)
    return req(name, 'PUT', BO + '/bonus_configuration/{{' + var + '}}', b, ok + cfg_asserts(reason_var, legacy_expected), bo=True, desc=desc)

# ---- bonuses read (BO list; the offer response does not carry the reason, CLS-4743 Q4)
BONUSES = (BO + '/bonuses?filter[ownerIds][]={{playerId}}&filter[bonusModelIds][]={{%s}}'
           '&filter[statuses][]=offered&filter[statuses][]=claimed&filter[statuses][]=played&filter[statuses][]=canceled&limit=100')
def bonus_by(var): return f"const b_{var} = list.find(b => String(b.id) === String(pm.variables.get('{var}')));\npm.test('bonus {var} listed', () => pm.expect(b_{var}).to.not.be.undefined);\n"
def bonus_reason(var, reason_var):
    if reason_var:
        return (f"pm.test('{var}: reasonId = {reason_var}', () => pm.expect(b_{var}.reasonId).to.eql({num(reason_var)}));\n"
                f"pm.test('{var}: reasonName = {reason_var} name', () => pm.expect(b_{var}.reasonName).to.eql(pm.variables.get('{reason_var}Name')));\n")
    return (f"pm.test('{var}: no reason', () => pm.expect(b_{var}.reasonId).to.eql(null));\n"
            f"pm.test('{var}: no reasonName', () => pm.expect(b_{var}.reasonName).to.eql(null));\n")

def poll(cond, asserts, tries=12, wait_ms=5000):
    """Re-runs the same request until cond holds: promotion/bulk workers are asynchronous."""
    pre = ("const k = 'tries_' + pm.info.requestName; const n = Number(pm.variables.get(k) || 0);\n"
           f"if (n > 0) {{ setTimeout(() => {{}}, {wait_ms}); }}")
    t = (log + "const k = 'tries_' + pm.info.requestName; let n = Number(pm.variables.get(k) || 0);\n"
         "const list = pm.response.json();\n"
         f"const found = ({cond});\n"
         f"if (!found && n < {tries}) {{ pm.collectionVariables.set(k, n + 1); postman.setNextRequest(pm.info.requestName); }}\n"
         "else { pm.collectionVariables.set(k, 0);\n" + asserts + "}\n")
    return pre, t

# =============================================================================================================
# 1  Setup: reasons
# =============================================================================================================
setup = [
    bo_token(),
    req('GET active domains -> otherDomainId (another brand)', 'GET', '{{BO_baseUrl}}/api/gateway/domains?limit=50', None,
        ok + "const j = pm.response.json(); const list = [j.data, j.domains, j].find(Array.isArray) || [];\n"
        "const other = list.find(d => String(d.id) !== String(pm.variables.get('domainId')));\n"
        "if (other) { pm.collectionVariables.set('otherDomainId', other.id); }\n"
        "pm.test('another brand found', () => pm.expect(other).to.not.be.undefined);", bo=True,
        pre="if (pm.variables.get('otherDomainId')) { if (pm.execution && pm.execution.skipRequest) pm.execution.skipRequest(); }"),
    reason_post('A', 'rA'), reason_post('B', 'rB'),
    reason_post('X deleted, on nothing', 'rX'), reason_delete('rX'),
    reason_post('Y config own, deleted later', 'rY'),
    reason_post('Z bulk config own, deleted later', 'rZ'),
    reason_post('W promotion config own, deleted later', 'rW'),
    reason_post('V scenario own, deleted later', 'rV'),
    req('GET reasons of the brand: A, B listed; X (deleted) not', 'GET', BO + '/reward-offering-reasons?limit=500', None,
        ok + "const list = pm.response.json(); const live = list.filter(r => !r.deletedAt).map(r => r.id);\n"
        f"pm.test('A and B listed', () => {{ pm.expect(live).to.include({num('rA')}); pm.expect(live).to.include({num('rB')}); }});\n"
        f"pm.test('X (deleted) is not in the selects', () => pm.expect(live).to.not.include({num('rX')}));", bo=True,
        desc='AC: the selects list the brand\'s non-deleted reasons; deleting a reason removes it from all selects.'),
    req('GET reasons of another brand -> otherReasonId', 'GET', '{{BO_baseUrl}}/api/gateway/domain/{{otherDomainId}}/reward-offering-reasons?limit=500', None,
        log + "const list = pm.response.json(); const r = (Array.isArray(list) ? list : []).find(x => !x.deletedAt);\n"
        "if (r) { pm.collectionVariables.set('otherReasonId', r.id); }\n"
        "pm.test('status 200 or 403 (no access to the other brand)', () => pm.expect([200, 403]).to.include(pm.response.code));", bo=True,
        pre=skip_if_empty('otherDomainId')),
    req('POST reason in another brand when it has none -> otherReasonId', 'POST', '{{BO_baseUrl}}/api/gateway/domain/{{otherDomainId}}/reward-offering-reason',
        {"reason": "{{runTag}} other brand"},
        log + "if (pm.response.code === 200) { pm.collectionVariables.set('otherReasonId', pm.response.json().id); }\n"
        "else { console.log('no other-brand reason: the other-brand cells are skipped'); }\n"
        "pm.test('other-brand reason known or not creatable (403)', () => pm.expect([200, 403]).to.include(pm.response.code));", bo=True,
        pre="if (pm.variables.get('otherReasonId') || !pm.variables.get('otherDomainId')) { if (pm.execution && pm.execution.skipRequest) pm.execution.skipRequest(); }"),
]

# =============================================================================================================
# 2  Configurations: reasonId stored, edit semantics, legacy reason still forwarded (CLS-4743, CLS-4745)
# =============================================================================================================
OTHER = skip_if_empty('otherReasonId')
configs = [
    bo_token(),
    cfg_post('rcA with reasonId A and legacy reason', 'rcA', 'rA',
        desc='AC: the configuration Reason field stores reasonId. ' + CRIT + 'the legacy `reason` is still forwarded and returned next to reasonId '
             '(CLS-4745 Q2, removal moves to CLS-4748), so the response must carry both.'),
    cfg_enable('rcA'),
    cfg_post('rcNone without reasonId', 'rcNone', None, omit_reason_id=True,
        desc='AC: reason stays optional. The key is absent from the body: the BO forwards reasonId only when sent (CLS-4745 Q1).'),
    cfg_enable('rcNone'),
    cfg_post('rc legacy only, no reasonId key at all', 'rcLegacy', None, omit_reason_id=True,
        desc='The current front: legacy reason, no reasonId. Saves as today, no reason reference (CLS-4743 edge case).'),
    req('POST config with unknown reasonId -> 400 on reasonId', 'POST', BO + '/bonus_configuration', dict(free_body('unknown'), reasonId=UNKNOWN_ID),
        refused(), bo=True, desc='AC: an unknown reason on a configuration is rejected and nothing is saved (promotion 400 bound to the reasonId field).'),
    req('POST config with deleted reasonId X -> 400', 'POST', BO + '/bonus_configuration', dict(free_body('deleted'), reasonId="@@rX@@"),
        refused(), bo=True, desc='AC: a deleted reason on a (new) configuration is rejected.'),
    req('POST config with another brand\'s reasonId -> 400', 'POST', BO + '/bonus_configuration', dict(free_body('other brand'), reasonId="@@otherReasonId@@"),
        refused(), bo=True, pre=OTHER, desc='AC: an other-brand reason is rejected.'),
    req('POST config with reasonId 0 -> 400, never reaches promotion', 'POST', BO + '/bonus_configuration', dict(free_body('zero'), reasonId=0),
        refused(), bo=True, desc='CLS-4745: the BO form rejects non-positive values before calling promotion.'),
    cfg_get('rcA', 'rA', 'GET rcA: reasonId and reasonName'),
    req('POST bonus_configurations search by the legacy reason: rcA and rcNone found', 'POST', BO + '/bonus_configurations',
        {"filter": {"reasons": ["goodwill"], "status": "enabled", "search": ["{{runTag}}"]}, "limit": 100, "offset": 0},
        ok + "const j = pm.response.json(); const list = [j.data, j].find(Array.isArray) || [];\n"
        f"const ids = list.map(c => String(c.id));\npm.test('rcA found by the legacy filter', () => pm.expect(ids).to.include(String(pm.variables.get('rcA'))));\n"
        "const a = list.find(c => String(c.id) === String(pm.variables.get('rcA')));\n"
        "pm.test('list item carries reasonId and reasonName', () => { pm.expect(a).to.not.be.undefined; pm.expect(a.reasonId).to.eql(" + num('rA') + "); pm.expect(a.reasonName).to.eql(pm.variables.get('rAName')); });", bo=True,
        desc=CRIT + 'with 4745 alone in production the legacy filter must keep finding new configurations (sdd.md review item 1): the front still filters by `reason`.'),
    cfg_put('PUT rcA to reasonId B', 'rcA', {"reasonId": "@@rB@@"}, 'rB', desc='AC: the configuration\'s reason can change.'),
    cfg_put('PUT rcA without the reasonId key -> reason kept (B)', 'rcA', {"displayName": "{{runTag}} rcA edited"}, 'rB', omit=('reasonId',),
        desc='CLS-4745 Q1 / CLS-4743: a body without the key keeps the stored reason. Today the gift edit of the front omits it.'),
    cfg_put('PUT rcA echoing reasonId and reasonName as last read -> 200, reasonId kept', 'rcA', {"reasonId": "@@rB@@", "reasonName": "echoed by the front"}, 'rB',
        desc='CLS-4745: the current non-gift edit echoes the whole configuration, reasonName included; the form drops it.'),
    cfg_put('PUT rcA with reasonId null -> cleared', 'rcA', {"reasonId": None}, None, desc='CLS-4743: null clears the reason.'),
    cfg_put('PUT rcA back to reasonId A (used by the offer cells)', 'rcA', {"reasonId": "@@rA@@"}, 'rA'),
    # gift
    req('POST gift config with reasonId A', 'POST', BO + '/reward_configuration/gift',
        {"name": "{{runTag}} gift", "displayName": "{{runTag}} gift", "currency": "{{currency}}", "offerAmount": 1, "stock": 5, "reason": "goodwill", "reasonId": "@@rA@@"},
        ok + setv('rcGift', 'pm.response.json().id') + cfg_asserts('rA'), bo=True, desc='AC: the Reason field on all 4 types (gift).'),
    req('PUT gift config without reasonId -> kept', 'PUT', BO + '/reward_configuration/gift/{{rcGift}}',
        {"name": "{{runTag}} gift", "displayName": "{{runTag}} gift edited", "currency": "{{currency}}", "offerAmount": 1, "stock": 5, "reason": "goodwill"},
        ok + cfg_asserts('rA'), bo=True, desc='CLS-4745 Q1: the front gift edit omits reasonId; forwarding null would clear every gift reason.'),
    req('PUT gift config with reasonId null -> cleared', 'PUT', BO + '/reward_configuration/gift/{{rcGift}}',
        {"name": "{{runTag}} gift", "displayName": "{{runTag}} gift", "currency": "{{currency}}", "offerAmount": 1, "stock": 5, "reason": "goodwill", "reasonId": None},
        ok + cfg_asserts(None), bo=True),
    req('POST gift config with unknown reasonId -> 400', 'POST', BO + '/reward_configuration/gift',
        {"name": "{{runTag}} gift bad", "currency": "{{currency}}", "offerAmount": 1, "reasonId": UNKNOWN_ID}, refused(), bo=True),
    # the other two types
    req('POST deposit config with reasonId A', 'POST', BO + '/bonus_configuration',
        {"name": "{{runTag}} deposit", "displayName": "{{runTag}} deposit", "currency": "{{currency}}", "reason": "goodwill", "reasonId": "@@rA@@",
         "segmentIds": [], "type": "deposit", "offerPercent": 100, "offerUpToAmount": 200, "model": "wager", "wageringMultiplier": 6,
         "maxWinMultiplier": 10, "offeringMethod": "automatic", "occurrences": 10, "isInfinity": False, "recurrence": "daily",
         "recurrenceDailyFrom": "22:11", "recurrenceDailyTo": "23:59", "validDuringDays": "3", "claimingEvent": "deposit",
         "claimingEventCondition": {"depositAmountMin": 10, "depositAmountMax": 1000}},
        ok + setv('rcDeposit', 'pm.response.json().id') + cfg_asserts('rA'), bo=True, desc='AC: the Reason field on all 4 types (bonus on deposit).'),
    req('POST free rounds config with reasonId A (needs frGameId, frGateway, frStudio)', 'POST', BO + '/bonus_configuration',
        {"name": "{{runTag}} free rounds", "displayName": "{{runTag}} free rounds", "type": "free_rounds", "model": "direct", "offeringMethod": "manual",
         "currency": "{{currency}}", "validDuringDays": "7", "claimingEvent": "direct", "offerValidFor": 7, "reason": "goodwill", "reasonId": "@@rA@@",
         "freeRoundConfiguration": {"freeRoundsGameGateway": "@@frGateway@@", "freeRoundsGameStudio": "@@frStudio@@", "gameIds": [{"id": "@@frGameId@@"}], "amount": 1}},
        ok + setv('rcFreeRounds', 'pm.response.json().id') + cfg_asserts('rA'), bo=True, pre=skip_if_empty('frGameId', 'frGateway', 'frStudio'),
        desc='AC: the Reason field on all 4 types (free rounds). The game triple must come from the same game (postman-reference.md); skipped when empty.'),
]

# =============================================================================================================
# 3  A configuration whose own reason is deleted afterwards (CLS-4743)
# =============================================================================================================
deleted_own = [
    bo_token(),
    cfg_post('rcDel with reasonId Y', 'rcDel', 'rY'), cfg_enable('rcDel'),
    reason_delete('rY'),
    cfg_get('rcDel', 'rY', 'GET rcDel after Y was deleted: reasonId and reasonName still returned'),
    cfg_put('PUT rcDel keeping reasonId Y (deleted) -> 200', 'rcDel', {"reasonId": "@@rY@@", "displayName": "{{runTag}} rcDel edited"}, 'rY',
        desc='AC: saving a configuration that keeps its deleted reason succeeds.'),
    cfg_put('PUT rcDel without reasonId, another field changed -> 200, Y kept', 'rcDel', {"displayName": "{{runTag}} rcDel edited 2"}, 'rY', omit=('reasonId',)),
    req('PUT rcDel to another deleted reason X -> 400, unchanged', 'PUT', BO + '/bonus_configuration/{{rcDel}}',
        dict(free_body('edit'), name='{{runTag}} rcDel', displayName='{{runTag}} rcDel', reasonId="@@rX@@"), refused(), bo=True,
        desc='AC: a deleted reason that is not the configuration\'s own is rejected.'),
    cfg_get('rcDel', 'rY', 'GET rcDel: still Y'),
]

# =============================================================================================================
# 4  Manual offer door (BO): the reason the user submits is what the bonus stores
# =============================================================================================================
def offer(name, cfg, reason, var, desc=''):
    body = {"playerId": "@@playerId@@", "amount": 1, "message": "QA CLS-3316"}
    if reason == 'ABSENT': pass
    elif reason is None: body['reasonId'] = None
    else: body['reasonId'] = reason
    return req(name, 'POST', BO + '/player/{{playerId}}/bonus_configuration/{{' + cfg + '}}/offer', body,
        ok + "const j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\n" + (setv(var, 'j.id') if var else ''),
        bo=True, desc=desc)

def offer_refused(name, cfg, reason, pre='', desc=''):
    return req(name, 'POST', BO + '/player/{{playerId}}/bonus_configuration/{{' + cfg + '}}/offer',
        {"playerId": "@@playerId@@", "amount": 1, "message": "QA CLS-3316", "reasonId": reason}, refused(), bo=True, pre=pre, desc=desc)

count_pre = ("const k = 'tries_' + pm.info.requestName; const n = Number(pm.variables.get(k) || 0); if (n > 0) { setTimeout(() => {}, 0); }")
PLAYER_STATUS_URL = '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}/player/{{playerId}}'
manual = [
    bo_token(),
    # Preparation, idempotent: a previous run can leave the player locked (the fixture scenarios with an enter_segment node and no
    # segment filter fire when our static segment gets the player, and one of them locks it), and a locked player cannot be offered
    # a bonus. DELETE status_stack answers 403 when the player is not locked, so it only runs when the status read says `locked`.
    req('PREP GET player status -> playerStatus', 'GET', PLAYER_STATUS_URL, None,
        ok + "const j = pm.response.json();\npm.test('player has a status', () => pm.expect(j.status).to.be.a('string'));\n"
        + setv('playerStatus', 'j.status'), bo=True,
        desc='Preparation, not a check of the feature: reads the status so the next request only runs when the player is locked.'),
    req('PREP DELETE status_stack, only when the player is locked', 'DELETE', PLAYER_STATUS_URL + '/status_stack', {"message": "unlock after CLS-3316 run"},
        status(200) + "pm.test('player back to a status that can be offered', () => pm.expect(pm.response.json().status).to.not.eql('locked'));\n",
        bo=True,
        pre="if (pm.collectionVariables.get('playerStatus') !== 'locked') { console.log('player not locked: skipped'); if (pm.execution && pm.execution.skipRequest) pm.execution.skipRequest(); }",
        desc='Preparation, idempotent: skipped unless the previous request read `locked`. Unlocks with the same call the backoffice uses (needs the unlock permission).'),
    req('GET bonuses of rcA before the offers -> count', 'GET', BONUSES % 'rcA', None, ok + setv('countBefore', 'pm.response.json().length'), bo=True),
    req('GET bonuses of rcDel before the offers -> count', 'GET', BONUSES % 'rcDel', None, ok + setv('countBeforeDel', 'pm.response.json().length'), bo=True),
    offer('POST offer rcA with reasonId B (config has A) -> M1', 'rcA', '@@rB@@', 'bM1',
        desc='AC: the bonus stores what was submitted, not the configuration\'s reason.'),
    offer('POST offer rcA without reasonId (config has A) -> M2', 'rcA', 'ABSENT', 'bM2',
        desc='AC: the user can clear the pre-filled reason; a manual offer without reasonId has none (CLS-4743 Q1: calls with sourceUserId store the request\'s reason, or none).'),
    offer('POST offer rcA with reasonId null -> M2b', 'rcA', None, 'bM2b'),
    offer('POST offer rcDel with its own deleted reason Y -> M3', 'rcDel', '@@rY@@', 'bM3',
        desc=CRIT + 'the AC rejects a deleted reason on an offer; the decision (CLS-4743, "kept" rule) accepts the configuration\'s OWN deleted reason on a BO user\'s offer, '
             'because the bulk offer sends it. Expect 200 and the bonus stored with Y.'),
    offer_refused('POST offer rcA with an unknown reasonId -> 400', 'rcA', UNKNOWN_ID, desc='AC: an unknown reason on an offer is rejected and nothing is created.'),
    offer_refused('POST offer rcA with deleted reasonId X (not its own) -> 400', 'rcA', "@@rX@@", desc='AC: a deleted reason on an offer is rejected (only the configuration\'s own is the exception).'),
    offer_refused('POST offer rcA with another brand\'s reasonId -> 400', 'rcA', "@@otherReasonId@@", pre=OTHER, desc='AC: an other-brand reason on an offer is rejected.'),
    offer_refused('POST offer rcA with reasonId -1 -> 400 from the BO form', 'rcA', -1),
    req('GET bonuses of rcA: M1 = B, M2 and M2b = none; refusals created nothing', 'GET', BONUSES % 'rcA', None,
        ok + "const list = pm.response.json();\n"
        + bonus_by('bM1') + bonus_reason('bM1', 'rB')
        + bonus_by('bM2') + bonus_reason('bM2', None)
        + bonus_by('bM2b') + bonus_reason('bM2b', None)
        + "pm.test('only the 3 accepted offers created bonuses', () => pm.expect(list.length).to.eql(Number(pm.variables.get('countBefore')) + 3));", bo=True),
    req('GET bonuses of rcDel: M3 = Y with its name; refusals created nothing', 'GET', BONUSES % 'rcDel', None,
        ok + "const list = pm.response.json();\n" + bonus_by('bM3') + bonus_reason('bM3', 'rY')
        + "pm.test('only the accepted offer created a bonus', () => pm.expect(list.length).to.eql(Number(pm.variables.get('countBeforeDel')) + 1));", bo=True,
        desc='AC: bonuses show the name of a deleted reason.'),
    cfg_put('PUT rcA to reasonId B after the offers', 'rcA', {"reasonId": "@@rB@@"}, 'rB'),
    req('GET bonuses of rcA after the configuration changed: bonuses keep their reasons', 'GET', BONUSES % 'rcA', None,
        ok + "const list = pm.response.json();\n" + bonus_by('bM1') + bonus_reason('bM1', 'rB') + bonus_by('bM2') + bonus_reason('bM2', None), bo=True,
        desc='AC: changing a configuration\'s reason after an offer does not change that bonus\'s reason (0 bonuses whose reason changes after a configuration edit).'),
    cfg_put('PUT rcA back to reasonId A', 'rcA', {"reasonId": "@@rA@@"}, 'rA'),
]

# =============================================================================================================
# 5  Bulk CSV door (BO): the BO sends the configuration's own reasonId with every row (CLS-4745)
# =============================================================================================================
def bulk(tag, cfg, reason_var):
    items_pre, items_test = poll("(Array.isArray(list) ? list : [list.data, list.items].find(Array.isArray) || []).length > 0 && (Array.isArray(list) ? list : [list.data, list.items].find(Array.isArray)).every(i => i.status === 'done')",
        "pm.test('every row done', () => { const items = Array.isArray(list) ? list : ([list.data, list.items].find(Array.isArray) || []); pm.expect(items.length).to.be.above(0); pm.expect(items.every(i => i.status === 'done')).to.eql(true); });\n")
    bonus_pre, bonus_test = poll('list.length > 0',
        "pm.test('the row created one bonus', () => pm.expect(list.length).to.eql(1));\n"
        "const bonus = list[0];\n" + bonus_reason_first(reason_var))
    return [
        req(f'POST bulk_action CSV on {cfg} ({tag})', 'POST', BO + '/bulk_action', None,
            ok + "const j = pm.response.json();\n" + setv('bulkId', 'j.id') + "pm.test('bulk created', () => pm.expect(j.id).to.be.a('number'));", bo=True,
            form=[{'key': 'type', 'value': 'offer_free_bonus', 'type': 'text'}, {'key': 'bonusModelId', 'value': '{{' + cfg + '}}', 'type': 'text'},
                  {'key': 'file', 'type': 'file', 'src': 'bulk-offer.csv'}]),
        req(f'POST bulk_action process ({tag})', 'POST', BO + '/bulk_action/{{bulkId}}/process', None, ok, bo=True),
        req(f'GET bulk items until done ({tag})', 'GET', BO + '/bulk_action/{{bulkId}}/items?limit=50', None, items_test, bo=True, pre=items_pre),
        req(f'GET bonuses of {cfg}: {tag}', 'GET', BONUSES % cfg, None, bonus_test, bo=True, pre=bonus_pre),
    ]

def bonus_reason_first(reason_var):
    if reason_var:
        return (f"pm.test('bulk bonus: reasonId = {reason_var}', () => pm.expect(bonus.reasonId).to.eql({num(reason_var)}));\n"
                f"pm.test('bulk bonus: reasonName', () => pm.expect(bonus.reasonName).to.eql(pm.variables.get('{reason_var}Name')));\n")
    return ("pm.test('bulk bonus: no reason', () => pm.expect(bonus.reasonId).to.eql(null));\n")

b1 = bulk('config reason A -> bonus has A', 'rcB1', 'rA')
b2 = bulk('config without reason -> none', 'rcB2', None)
b3 = bulk('config reason Z, deleted -> bonus still has Z', 'rcB3', 'rZ')
b1[3]['request']['description'] = 'AC: bulk CSV offers get the configuration\'s reason at creation (the BO sends it with each row, CLS-4745 Q6); a configuration without a reason gives none.'
b3[3]['request']['description'] = 'AC: bonuses created afterwards from a configuration whose reason was deleted still get it.'
bulk_f = [
    bo_token(),
    cfg_post('rcB1 bulk, reason A', 'rcB1', 'rA'), cfg_enable('rcB1'),
    cfg_post('rcB2 bulk, no reason', 'rcB2', None, omit_reason_id=True), cfg_enable('rcB2'),
    cfg_post('rcB3 bulk, reason Z', 'rcB3', 'rZ'), cfg_enable('rcB3'),
    reason_delete('rZ'),
] + b1 + b2 + b3

# =============================================================================================================
# 6  Promotion door: instant_reward promotion, player opts in, the promotion reward offers the bonus (CLS-4743)
# =============================================================================================================
def promo(tag, rc, idx):
    return [
        req(f'POST promotion-configuration instant_reward {tag}', 'POST', BO + '/promotion-configuration',
            {"name": "{{runTag}} promo " + tag, "currency": "{{currency}}", "startDate": "{{startDate}}", "endDate": "{{endDate}}", "segmentIds": [],
             "engagementModel": "manual", "engagementCode": "{{code}}-" + tag, "type": "instant_reward", "rewardingLimit": 100, "playerPromotionLimit": 1},
            ok + setv('pc' + idx, 'pm.response.json().id'), bo=True),
        req(f'POST reward free_bonus -> {rc} ({tag})', 'POST', BO + '/promotion-configuration/{{pc' + idx + '}}/reward',
            {"type": "free_bonus", "rewardConfigurationId": "@@" + rc + "@@", "quantity": 1, "options": {}},
            ok + "pm.test('reward linked', () => pm.expect(pm.response.json().type).to.eql('free_bonus'));", bo=True),
        req(f'PATCH enable promotion ({tag})', 'PATCH', BO + '/promotion-configuration/{{pc' + idx + '}}', {"status": "enabled"},
            ok + "pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));", bo=True),
    ]

def promo_check(tag, rc, reason_var):
    pre, t = poll('list.length > 0',
        "pm.test('promotion reward created one bonus', () => pm.expect(list.length).to.eql(1));\nconst bonus = list[0];\n" + bonus_reason_first(reason_var))
    return req(f'GET bonuses of {rc}: {tag}', 'GET', BONUSES % rc, None, t, bo=True, pre=pre)

promotion = [
    bo_token(),
    cfg_post('rcP1 promo, reason A', 'rcP1', 'rA', claiming='automatic'), cfg_enable('rcP1'),
    cfg_post('rcP2 promo, no reason', 'rcP2', None, claiming='automatic', omit_reason_id=True), cfg_enable('rcP2'),
    cfg_post('rcP3 promo, reason W', 'rcP3', 'rW', claiming='automatic'), cfg_enable('rcP3'),
    reason_delete('rW'),
] + promo('P1', 'rcP1', '1') + promo('P2', 'rcP2', '2') + promo('P3', 'rcP3', '3')

promotion_gw = [
    gw_token(),
    req('PUT optin P1', 'PUT', GW + '/promotion-configuration/optin/{{code}}-P1', None, ok, bo=False),
    req('PUT optin P2', 'PUT', GW + '/promotion-configuration/optin/{{code}}-P2', None, ok, bo=False),
    req('PUT optin P3', 'PUT', GW + '/promotion-configuration/optin/{{code}}-P3', None, ok, bo=False),
]
promotion_check = [
    bo_token(),
    promo_check('promotion reward copies the configuration\'s reason A', 'rcP1', 'rA'),
    promo_check('configuration without reason -> none', 'rcP2', None),
    promo_check('configuration\'s reason Z deleted -> bonus still has it', 'rcP3', 'rW'),
]
promotion_check[1]['request']['description'] = 'AC: promotions get the configuration\'s reason at creation; a configuration without one gives none.'
promotion_check[3]['request']['description'] = 'AC: bonuses created afterwards from a configuration whose reason was deleted still get it (copied by id, never loaded).'

# =============================================================================================================
# 7  Scenario door (BO -> scenario): the bonus action accepts and validates reasonId at save (CLS-5130)
# =============================================================================================================
def scenario_body(name, options, with_meta=True):
    nodes = [
        {"index": 0, "nodeType": "event", "type": "cron_scheduled", "position": {"x": 200, "y": 300}, "root": True,
         "additionalData": {"cronExpression": "0 0 1 1 *"}},
        {"index": 1, "nodeType": "action", "type": "offer_reward", "position": {"x": 400, "y": 300}, "options": options},
    ]
    b = {"nodes": nodes, "edges": [{"source": 0, "target": 1}]}
    if with_meta: b = {"name": "{{runTag}} " + name, "currency": "{{currency}}", **b}
    return b

def bonus_opts(**kw):
    o = {"rewardType": "bonus", "description": "QA CLS-3316", "rewardConfigurationId": "@@rcNone@@", "amount": "1.00"}
    o.update(kw)
    return o

def stored(var, expect):
    e = num(expect) if expect else 'null'
    return ("const j = pm.response.json(); const act = JSON.stringify(j);\n" + setv(var, 'j.id') +
            "const node = (j.nodes || []).find(n => n.type === 'offer_reward');\n"
            "pm.test('bonus node stored', () => pm.expect(node).to.not.be.undefined);\n"
            f"pm.test('stored options.reasonId = {expect or 'null'}', () => pm.expect(node.options.reasonId).to.eql({e}));\n")

scenario = [
    bo_token(),
    req('POST scenario, bonus action with reasonId A', 'POST', BO + '/scenario', scenario_body('s1', bonus_opts(reasonId="@@rA@@")),
        ok + stored('scA', 'rA'), bo=True, desc='AC: the scenario bonus action stores the reason it was submitted with. The scenario is created inactive and its cron fires once a year.'),
    req('POST scenario, bonus action with reasonId null', 'POST', BO + '/scenario', scenario_body('s2', bonus_opts(reasonId=None)),
        ok + stored('scNull', None), bo=True, desc='AC: the user can clear the reason; the scenario stores what was submitted.'),
    req('POST scenario, bonus action without reasonId', 'POST', BO + '/scenario', scenario_body('s3', bonus_opts()),
        ok + stored('scNone', None), bo=True, desc='AC: reason stays optional on scenarios.'),
    req('POST scenario with an unknown reasonId -> 400 at options.reasonId', 'POST', BO + '/scenario', scenario_body('bad1', bonus_opts(reasonId=UNKNOWN_ID)),
        refused('reasonId', "pm.test('message', () => pm.expect(pm.response.text()).to.include('not a valid reward offering reason'));\n"), bo=True,
        desc='AC: an unknown reason on a scenario is rejected and nothing is saved.'),
    req('POST scenario with another brand\'s reasonId -> 400', 'POST', BO + '/scenario', scenario_body('bad2', bonus_opts(reasonId="@@otherReasonId@@")),
        refused('reasonId', "pm.test('message', () => pm.expect(pm.response.text()).to.include('not a valid reward offering reason'));\n"), bo=True, pre=OTHER,
        desc='AC: an other-brand reason on a scenario is rejected (the reasons list is per domain, so it is absent like an unknown one).'),
    req('POST scenario with deleted reasonId X -> 400 (scenario does not hold it)', 'POST', BO + '/scenario', scenario_body('bad3', bonus_opts(reasonId="@@rX@@")),
        refused('reasonId', "pm.test('message', () => pm.expect(pm.response.text()).to.include('is deleted'));\n"), bo=True,
        desc=CRIT + 'the AC says a scenario that keeps its deleted reason saves; the decision (CLS-5130) accepts a deleted reason only when the STORED scenario already holds it on an offer_reward node. A new scenario with a deleted reason is rejected.'),
    req('POST scenario with reasonId 0 -> 400', 'POST', BO + '/scenario', scenario_body('bad4', bonus_opts(reasonId=0)), refused('reasonId'), bo=True),
    # keep a deleted reason: V is active now, saved, deleted, then the same scenario is saved again
    req('POST scenario holding reasonId V (active) -> scV', 'POST', BO + '/scenario', scenario_body('sV', bonus_opts(reasonId="@@rV@@")), ok + stored('scV', 'rV'), bo=True),
    reason_delete('rV'),
    req('PUT graph of scV keeping the deleted reasonId V -> 200', 'PUT', BO + '/scenario/graph/{{scV}}', scenario_body('sV', bonus_opts(reasonId="@@rV@@"), with_meta=False),
        ok + stored('scV', 'rV'), bo=True, desc='AC: saving a scenario that keeps its deleted reason succeeds (the stored scenario holds it).'),
    req('PUT graph of scV switching to another deleted reasonId X -> 400', 'PUT', BO + '/scenario/graph/{{scV}}', scenario_body('sV', bonus_opts(reasonId="@@rX@@"), with_meta=False),
        refused('reasonId'), bo=True),
    req('PUT graph of scA with reasonId B -> 200', 'PUT', BO + '/scenario/graph/{{scA}}', scenario_body('s1', bonus_opts(reasonId="@@rB@@"), with_meta=False),
        ok + stored('scA', 'rB'), bo=True),
]
scenario_cleanup = [
    bo_token(),
] + [req(f'DELETE scenario {v}', 'DELETE', BO + '/scenario/{{' + v + '}}', None,
         "pm.test('deleted', () => pm.expect([200, 204]).to.include(pm.response.code));", bo=True) for v in ('scA', 'scNull', 'scNone', 'scV')]

# =============================================================================================================
# 9  CLS-4744 prerequisite: bonuses on configurations that only have the legacy key. run.sh then runs the seed and
#    backfill command and reads the database (read-only) to check the result; nothing HTTP happens after this folder.
# =============================================================================================================
backfill_prereq = [
    bo_token(),
    cfg_enable('rcLegacy'),
    offer('POST offer rcLegacy (legacy key only) -> bLegacy', 'rcLegacy', 'ABSENT', 'bLegacy'),
    offer('POST offer rcNone (legacy key only) -> bNone', 'rcNone', 'ABSENT', 'bNone'),
    req('GET bonuses of rcLegacy before the backfill: no reason', 'GET', BONUSES % 'rcLegacy', None,
        ok + "const list = pm.response.json();\n" + bonus_by('bLegacy') + bonus_reason('bLegacy', None), bo=True,
        desc='State before CLS-4744: the configuration has a legacy key and no reasonId, so its bonus has no reason. run.sh runs the command after this folder.'),
]

# =============================================================================================================
# 10/11  Scenario runtime door (DEV-ONLY, local): the scenario really offers the bonus (CLS-5130 + CLS-4743).
#   Trigger: the console command `scenario:trigger:cron-scheduled-event <domain>` (a real command, nothing is written to a
#   database). It is the trigger that needs the fewest services: a cron_scheduled event has no players, so the audience
#   comes from a segment condition on a MANUAL (static) segment that holds the test player; no event has to arrive on
#   SQS from segment, crm or wallet. run.sh runs the command and drains the action queue between folder 10 and folder 11,
#   so the two folders run in two Newman invocations (captured ids are handed over with --env-var).
#   Services: scenario (php + the command + a consumer of its queues), segment (create the segment, hold the player),
#   promotion (the offer; it asks crm for the player's currency), crm, BO (entry point), shared MySQL and local SQS.
#   Not needed: wallet, game, gateway, Elasticsearch (only dynamic segments use it, to confirm on the first run).
#   Cells (one configuration per scenario, so each bonus is unambiguous):
#     S1 config reason A, node reasonId B       -> bonus has B (the node wins over the configuration)
#     S2 config reason A, node without reasonId -> bonus has none (a scenario without a reason gives none)
#     S3 config without reason, node holds U, U deleted after the save and the graph saved again keeping it
#                                                -> the job still offers with U (promotion accepts a deleted reason of the
#                                                   domain on a scenario offer); the bonus keeps U with its name
# =============================================================================================================
def rt_scenario_body(name, cfg_var, node_reason, with_meta=True):
    opts = {"rewardType": "bonus", "description": "QA CLS-3316 runtime", "rewardConfigurationId": "@@" + cfg_var + "@@", "amount": "1.00"}
    if node_reason is not None and node_reason != 'ABSENT': opts['reasonId'] = "@@" + node_reason + "@@"
    nodes = [
        {"index": 0, "nodeType": "event", "type": "cron_scheduled", "position": {"x": 200, "y": 300}, "root": True,
         "additionalData": {"cronExpression": "* * * * *"}},
        {"index": 1, "nodeType": "condition", "type": "segment", "operator": "equal", "value": ["@@segR@@"], "position": {"x": 400, "y": 300}},
        {"index": 2, "nodeType": "action", "type": "offer_reward", "position": {"x": 600, "y": 300}, "options": opts},
    ]
    b = {"nodes": nodes, "edges": [{"source": 0, "target": 1}, {"source": 1, "target": 2}]}
    if with_meta: b = {"name": "{{runTag}} " + name, "currency": "{{currency}}", **b}
    return b

def rt_stored(var, expect):
    e = num(expect) if expect else 'null'
    return ("const j = pm.response.json();\n" + setv(var, 'j.id') +
            "const node = (j.nodes || []).find(n => n.type === 'offer_reward');\n"
            "pm.test('bonus node stored', () => pm.expect(node).to.not.be.undefined);\n"
            f"pm.test('stored options.reasonId = {expect or 'null'}', () => pm.expect(node.options.reasonId == null ? null : node.options.reasonId).to.eql({e}));\n")

def rt_check(cfg, tag, reason_var):
    pre, t = poll('list.length > 0',
        "pm.test('the scenario offered one bonus', () => pm.expect(list.length).to.eql(1));\nconst bonus = list[0];\n" + bonus_reason_first(reason_var))
    return req(f'GET bonuses of {cfg}: {tag}', 'GET', BONUSES % cfg, None, t, bo=True, pre=pre)

rt_setup = [
    bo_token(),
    reason_post('U scenario, deleted after save', 'rU'),
    req('POST manual segment -> segR (static, no criteria)', 'POST', BO + '/segment',
        {"name": "{{runTag}} runtime", "currency": "{{currency}}", "type": "static", "segmentCriterias": []},
        ok + "const j = pm.response.json();\npm.test('segment created', () => pm.expect(j.id).to.be.a('number'));\n" + setv('segR', 'j.id'), bo=True,
        desc='A static segment has no criteria and is never evaluated: its players are the ones appended below. The cron scenario takes its audience from it.'),
    req('POST player into segR', 'POST', BO + '/segment/{{segR}}/players', [{"playerId": "@@playerId@@"}], ok, bo=True),
    cfg_post('rcR1 scenario, reason A', 'rcR1', 'rA'), cfg_enable('rcR1'),
    cfg_post('rcR2 scenario, reason A', 'rcR2', 'rA'), cfg_enable('rcR2'),
    cfg_post('rcR3 scenario, no reason', 'rcR3', None, omit_reason_id=True), cfg_enable('rcR3'),
    req('POST scenario S1: cron every minute, segR, bonus rcR1, node reasonId B -> scR1', 'POST', BO + '/scenario', rt_scenario_body('rt1', 'rcR1', 'rB'),
        ok + rt_stored('scR1', 'rB'), bo=True),
    req('POST scenario S2: same, node without reasonId -> scR2', 'POST', BO + '/scenario', rt_scenario_body('rt2', 'rcR2', 'ABSENT'),
        ok + rt_stored('scR2', None), bo=True),
    req('POST scenario S3: same, node holds reasonId U (active) -> scR3', 'POST', BO + '/scenario', rt_scenario_body('rt3', 'rcR3', 'rU'),
        ok + rt_stored('scR3', 'rU'), bo=True),
    reason_delete('rU'),
    req('PUT graph of scR3 keeping the deleted reasonId U -> 200', 'PUT', BO + '/scenario/graph/{{scR3}}', rt_scenario_body('rt3', 'rcR3', 'rU', with_meta=False),
        ok + rt_stored('scR3', 'rU'), bo=True,
        desc='The scenario that already holds U may save again after U is deleted (CLS-5130). run.sh runs the trigger right after this folder.'),
] + [req(f'PATCH settings of {v}: isActive true (a new scenario starts inactive and the cron command skips it)', 'PATCH', BO + '/scenario/settings/{{' + v + '}}',
         {"isActive": True}, ok + "pm.test('active', () => pm.expect(pm.response.json().isActive).to.eql(true));", bo=True) for v in ('scR1', 'scR2', 'scR3')]
rt_verify = [
    bo_token(),
    rt_check('rcR1', 'node reason B, configuration reason A -> bonus has B', 'rB'),
    rt_check('rcR2', 'node without a reason, configuration reason A -> bonus has none', None),
    rt_check('rcR3', 'node reason U deleted after the save -> bonus still has U', 'rU'),
] + [req(f'DELETE scenario {v}', 'DELETE', BO + '/scenario/{{' + v + '}}', None,
         "pm.test('deleted', () => pm.expect([200, 204]).to.include(pm.response.code));", bo=True) for v in ('scR1', 'scR2', 'scR3')]
rt_verify[1]['request']['description'] = 'AC: a bonus created by a scenario gets the scenario\'s reason; the configuration\'s reason does not leak in.'
rt_verify[2]['request']['description'] = 'AC: a scenario without a reason gives none, even if the configuration has one.'
rt_verify[3]['request']['description'] = 'AC: bonuses created afterwards from a scenario whose reason was deleted still get it; the name is still returned.'

folders = [
    {'name': '1 Setup: reasons (BO)', 'item': setup},
    {'name': '2 Configurations: reasonId, edit semantics, legacy reason (BO)', 'item': configs},
    {'name': '3 Configuration whose reason is deleted afterwards (BO)', 'item': deleted_own},
    {'name': '4 Manual offer door (BO)', 'item': manual},
    {'name': '5 Bulk CSV door (BO)', 'item': bulk_f},
    {'name': '6a Promotion door: setup (BO)', 'item': promotion},
    {'name': '6b Promotion door: player opts in (gateway)', 'item': promotion_gw},
    {'name': '6c Promotion door: bonuses (BO)', 'item': promotion_check},
    {'name': '7 Scenario door: save-time validation (BO)', 'item': scenario},
    {'name': '8 Cleanup: scenarios (BO)', 'item': scenario_cleanup},
    {'name': '9 CLS-4744 prerequisite: bonuses on legacy-only configurations (BO)', 'item': backfill_prereq},
    {'name': '10 Scenario runtime door: setup (BO, DEV-ONLY)', 'item': rt_setup},
    {'name': '11 Scenario runtime door: bonuses and cleanup (BO, DEV-ONLY)', 'item': rt_verify},
]

variables = {'BO_baseUrl': 'http://localhost:84', 'baseUrl': 'http://localhost:93', 'domainId': '1', 'playerId': '1', 'currency': 'EUR',
             'frGameId': '', 'frGateway': '', 'frStudio': ''}
captured = ['runTag', 'code', 'startDate', 'endDate', 'BO_access_token', 'access_token', 'otherDomainId', 'otherReasonId',
            'rA', 'rAName', 'rB', 'rBName', 'rX', 'rXName', 'rY', 'rYName', 'rZ', 'rZName', 'rW', 'rWName', 'rV', 'rVName',
            'rcA', 'rcNone', 'rcLegacy', 'rcGift', 'rcDeposit', 'rcFreeRounds', 'rcDel', 'rcB1', 'rcB2', 'rcB3', 'rcP1', 'rcP2', 'rcP3',
            'pc1', 'pc2', 'pc3', 'bM1', 'bM2', 'bM2b', 'bM3', 'bLegacy', 'bNone', 'countBefore', 'countBeforeDel', 'bulkId', 'scA', 'scNull', 'scNone', 'scV',
            'rU', 'rUName', 'segR', 'rcR1', 'rcR2', 'rcR3', 'scR1', 'scR2', 'scR3', 'playerStatus']
c = {'info': {'name': 'CLS-3316 reward offering reasons on configurations and bonuses',
              'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
     'item': folders,
     # Newman's --export-collection does not carry the values captured at run time; --export-globals does. Mirror every
     # captured collection variable to the globals after each request so run.sh can read them (tokens stay out of the file).
     'event': [{'listen': 'test', 'script': {'type': 'text/javascript', 'exec': [
         "const o = pm.collectionVariables.toObject();",
         "Object.keys(o).forEach(k => { if (!/access_token/.test(k) && o[k] !== '' && o[k] !== null && o[k] !== undefined) { pm.globals.set(k, String(o[k])); } });"]}}],
     'variable': [{'key': k, 'value': v} for k, v in variables.items()] + [{'key': k, 'value': ''} for k in captured]}
json.dump(c, open('CLS-3316.postman_collection.json', 'w'), indent=2)
print('requests:', sum(len(f['item']) for f in folders))
