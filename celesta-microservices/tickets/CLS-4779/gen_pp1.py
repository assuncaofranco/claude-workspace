import json
# CLS-4779 on preprod-1: automatic refund of a Paytech card deposit, through the entry points only
# (gateway for the player, backoffice for the operator). Credentials come from the vault at run time
# (run_pp1.sh); nothing secret is written here. The card is Paytech's public sandbox test card
# "not enrolled for 3-D Secure, successful authorization", so no redirect is needed.

def req(name, method, url, body=None, test='', pre='', auth=None):
    h = [{'key': 'Content-Type', 'value': 'application/json'}] if body is not None else []
    if auth == 'player':
        h.append({'key': 'Authorization', 'value': 'Bearer {{access_token}}'})
    if auth == 'bo':
        h.append({'key': 'Authorization', 'value': 'Bearer {{BO_access_token}}'})
    r = {'name': name, 'request': {'method': method, 'header': h, 'url': url}, 'event': []}
    if body is not None:
        r['request']['body'] = {'mode': 'raw', 'raw': json.dumps(body, indent=2)}
    if pre:
        r['event'].append({'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': pre.strip().split('\n')}})
    if test:
        r['event'].append({'listen': 'test', 'script': {'type': 'text/javascript', 'exec': test.strip().split('\n')}})
    return r

def folder(name, items):
    return {'name': name, 'item': items}

LOG = "if (pm.response.code >= 300) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 800));\n"
OK = LOG + "pm.test('status 200', () => pm.response.to.have.status(200));\n"
FINAL = "['success', 'failure', 'timeout', 'fraud']"

# Poll helper: repeats the current request every {{pollMs}} ms until done() or {{pollMax}} attempts.
def poll(counter, done_expr, on_done, on_give_up):
    return f"""
const n = Number(pm.collectionVariables.get('{counter}') || 0) + 1;
pm.collectionVariables.set('{counter}', n);
if ({done_expr}) {{
    pm.collectionVariables.set('{counter}', 0);
{on_done}
}} else if (n < Number(pm.collectionVariables.get('pollMax'))) {{
    setTimeout(() => {{}}, Number(pm.collectionVariables.get('pollMs')));
    postman.setNextRequest(pm.info.requestName);
}} else {{
    pm.collectionVariables.set('{counter}', 0);
{on_give_up}
}}
"""

player_token = req('Player token', 'POST', '{{baseUrl}}/oauth/2.0/token',
    {"grant_type": "player", "username": "{{username}}", "password": "{{password}}",
     "client_id": "{{oauth_client_id}}", "client_secret": "{{oauth_client_secret}}",
     "deviceInformation": {"ip": "127.0.0.1", "userAgent": "Mozilla/5.0"}},
    OK + "pm.collectionVariables.set('access_token', pm.response.json().access_token);")

bo_token = req('BO token', 'POST', '{{BO_baseUrl}}/oauth/2.0/token',
    {"grant_type": "password", "client_id": "{{BO_oauth_client_id}}", "client_secret": "{{BO_oauth_client_secret}}",
     "username": "{{BO_username}}", "password": "{{BO_password}}"},
    OK + "pm.collectionVariables.set('BO_access_token', pm.response.json().access_token);")

def balance(tag, var):
    return req(f'Player balance ({tag})', 'GET', '{{baseUrl}}/wallet/balances', None,
        OK + f"""
const eur = (pm.response.json().balances || []).find(b => b.currency === 'EUR') || {{}};
console.log('balance {tag}: ' + JSON.stringify(eur));
pm.collectionVariables.set('{var}', JSON.stringify(eur));
""", auth='player')

def deposit(amount_var, uid_var):
    return req(f'Paytech card deposit ({{{{{amount_var}}}}} EUR)', 'POST', '{{baseUrl}}/payment',
        {"paymentInformation": {"paymentConfigurationId": "{{paytechVisaConfigurationId}}", "holder": "{{cardHolder}}",
                                "number": "{{cardNumber}}", "expirationDate": {"month": "{{cardMonth}}", "year": "{{cardYear}}"},
                                "cvv": "{{cardCvv}}", "reusable": False},
         "amount": f"{{{{{amount_var}}}}}", "ip": "138.199.14.138", "userAgent": "Mozilla/5.0",
         "successUrl": "https://example.com/callback/success", "failureUrl": "https://example.com/callback/failure",
         "additionalData": {"seonSession": "{{seonSession}}", "browserAcceptHeader": "text/html", "browserJavaEnabled": True,
                            "browserLanguage": "en", "browserColorDepth": "24", "browserScreenHeight": "1200",
                            "browserScreenWidth": "1920", "browserTimezone": "0"}},
        OK + f"""
const b = pm.response.json();
console.log('deposit: ' + JSON.stringify(b).slice(0, 600));
pm.test('deposit accepted by Paytech (no 3DS redirect, no error)', () => {{
    pm.expect(b.redirectionHtml || null, 'a 3DS redirect came back: use a card not enrolled for 3DS').to.equal(null);
    pm.expect(['success', 'pending']).to.include(b.status);
}});
pm.collectionVariables.set('{uid_var}', b.id);
""", auth='player')

def find_deposit(uid_var, id_var):
    return req(f'Find the deposit in the transaction report ({{{{{uid_var}}}}})', 'POST',
        '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}/finance/transaction_reports',
        {"filter": {"internalId": f"{{{{{uid_var}}}}}"}, "limit": 1, "offset": 0},
        LOG + "pm.test('status 200', () => pm.response.to.have.status(200));\n"
        + "const row = (pm.response.json() || [])[0];\n"
        + poll(f'poll_{id_var}', "row && row.status === 'success'",
            f"""    console.log('deposit row: ' + JSON.stringify(row));
    pm.collectionVariables.set('{id_var}', row.id);
    pm.test('the report shows a successful Paytech visa sale (what the refund modal reads)', () => {{
        pm.expect(row.provider).to.equal('paytech');
        pm.expect(row.paymentMethod).to.equal('visa');
        pm.expect(row.type).to.equal('sale');
    }});""",
            "    pm.test('deposit reached success in the report', () => pm.expect.fail('last row: ' + JSON.stringify(row)));"),
        auth='bo')

def refund(name, id_var, amount_var, rtype, ref_var):
    return req(name, 'POST', f'{{{{BO_baseUrl}}}}/api/gateway/domain/{{{{domainId}}}}/payment/refund/{{{{{id_var}}}}}',
        {"amount": f"{{{{{amount_var}}}}}", "refundType": rtype, "message": "CLS-4779 preprod check"},
        OK + f"""
const r = pm.response.json();
console.log('{ref_var} answer at ' + new Date().toISOString() + ': ' + JSON.stringify(r).slice(0, 600));
pm.test('a refund transaction came back', () => {{
    pm.expect(r.type).to.equal('refund');
    pm.expect(['initiated', 'pending', 'success']).to.include(r.status);
}});
pm.collectionVariables.set('{ref_var}', r.id);
pm.collectionVariables.set('{ref_var}_at', Date.now());
""", auth='bo')

def wait_final(ref_var, expected):
    return req(f'Refund status until final ({{{{{ref_var}}}}})', 'GET',
        f'{{{{BO_baseUrl}}}}/api/gateway/domain/{{{{domainId}}}}/payment/player/{{{{playerId}}}}/transaction-history/{{{{{ref_var}}}}}',
        None,
        LOG + "pm.test('status 200', () => pm.response.to.have.status(200));\n"
        + "const st = (pm.response.json() || []).filter(h => h.type === 'status');\n"
        + "const last = st.length ? st[st.length - 1].valueAfter : null;\n"
        + poll(f'poll_{ref_var}', f"{FINAL}.includes(last)",
            f"""    const secs = Math.round((Date.now() - Number(pm.collectionVariables.get('{ref_var}_at'))) / 1000);
    console.log('{ref_var} final: ' + last + ' after ~' + secs + ' s; history: ' + JSON.stringify(st));
    pm.test('{ref_var} ends {expected}', () => pm.expect(last).to.equal('{expected}'));""",
            f"""    const secs = Math.round((Date.now() - Number(pm.collectionVariables.get('{ref_var}_at'))) / 1000);
    console.log('{ref_var} still ' + last + ' after ~' + secs + ' s; history: ' + JSON.stringify(st));
    pm.test('{ref_var} reached a final status within the polling window (re-check later: timeout job runs after 15 min)', () => pm.expect.fail('still ' + last));"""),
        auth='bo')

over_refund = req('Automatic refund beyond what is left -> 400', 'POST',
    '{{BO_baseUrl}}/api/gateway/domain/{{domainId}}/payment/refund/{{depositId}}',
    {"amount": "1", "refundType": "automatic", "message": "CLS-4779 preprod check"},
    LOG + """
pm.test('rejected with 400', () => pm.response.to.have.status(400));
console.log('over refund answer: ' + pm.response.text().slice(0, 400));
""", auth='bo')

balance_check = req('Player balance back to where it started', 'GET', '{{baseUrl}}/wallet/balances', None,
    OK + """
const eur = (pm.response.json().balances || []).find(b => b.currency === 'EUR') || {};
const before = JSON.parse(pm.collectionVariables.get('balanceBefore') || '{}');
console.log('balance before: ' + JSON.stringify(before) + ' / now: ' + JSON.stringify(eur));
pm.test('deposit fully refunded: EUR balance equals the starting one', () => pm.expect(Number(eur.amount)).to.eql(Number(before.amount)));
""", auth='player')

c = {
    'info': {'name': 'CLS-4779 pp1: Paytech card automatic refund',
             'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
    'item': [
        folder('1 Player: Paytech card deposit', [
            player_token, balance('before', 'balanceBefore'), deposit('depositAmount', 'depositUid'),
        ]),
        folder('2 Backoffice: automatic refunds of the deposit', [
            bo_token, find_deposit('depositUid', 'depositId'),
            refund('Automatic partial refund', 'depositId', 'partialAmount', 'automatic', 'refund1Id'),
            wait_final('refund1Id', 'success'),
            refund('Automatic refund of the rest', 'depositId', 'restAmount', 'automatic', 'refund2Id'),
            wait_final('refund2Id', 'success'),
            over_refund,
        ]),
        folder('3 Player: balance after the refunds', [player_token, balance_check]),
        folder('4 Manual refund still works on a Paytech card deposit', [
            player_token, deposit('manualDepositAmount', 'manualDepositUid'),
            bo_token, find_deposit('manualDepositUid', 'manualDepositId'),
            refund('Manual refund', 'manualDepositId', 'manualDepositAmount', 'manual', 'refund3Id'),
            wait_final('refund3Id', 'success'),
        ]),
    ],
    'variable': [{'key': k, 'value': v} for k, v in [
        ('baseUrl', 'https://gateway.preprod-1.octopodev.com'),
        ('BO_baseUrl', 'https://backend-api.preprod-1.octopodev.com'),
        ('domainId', '56'),
        ('playerId', '307847'),
        ('paytechVisaConfigurationId', '7875'),
        ('cardHolder', 'John Doe'),
        ('cardNumber', '4000000000000408'),
        ('cardMonth', '12'),
        ('cardYear', '2030'),
        ('cardCvv', '123'),
        ('seonSession', ''),
        ('depositAmount', '20'),
        ('partialAmount', '5'),
        ('restAmount', '15'),
        ('manualDepositAmount', '10'),
        ('pollMs', '5000'),
        ('pollMax', '36'),
        ('access_token', ''), ('BO_access_token', ''),
        ('balanceBefore', ''), ('depositUid', ''), ('depositId', ''), ('manualDepositUid', ''), ('manualDepositId', ''),
        ('refund1Id', ''), ('refund2Id', ''), ('refund3Id', ''),
    ]],
}
json.dump(c, open('CLS-4779.pp1.postman_collection.json', 'w'), indent=2)
