"""Generates the CLS-4337-CLS-4338 wallet collection (DEV-ONLY: wallet is internal)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
W = "{{walletUrl}}/api/domain/{{domainId}}"

SIGN = [
    "['ownerId', 'otherOwnerId', 'bonusA', 'bonusB', 'bonusC', 'bonusUnknown', 'ptx'].forEach(k => {",
    "  if (!pm.collectionVariables.get(k)) pm.collectionVariables.set(k, String(900000000 + Math.floor(Math.random() * 99999999)));",
    "});",
    "const crypto = require('crypto-js');",
    "const url = pm.variables.replaceIn(pm.request.url.toString());",
    "const m = url.match(/^https?:\\/\\/([^\\/:]+)(?::(\\d+))?([^?]*)/);",
    "const guardKey = String(pm.variables.get('guardKey') || '');",
    "if (guardKey && m) {",
    "  const method = pm.request.method.toUpperCase();",
    "  let data = method + m[1] + decodeURIComponent(m[3]);",
    "  if (['POST','PUT','PATCH'].includes(method)) {",
    "    const body = (pm.request.body && pm.request.body.raw) ? pm.variables.replaceIn(pm.request.body.raw) : '';",
    "    data += crypto.MD5(body).toString();",
    "  }",
    "  pm.request.headers.upsert({ key: 'x-guard-secret', value: crypto.HmacSHA256(data, guardKey).toString() });",
    "}",
]

# Wallet of the player in a currency, from the wallets list.
HELPERS = ["const byCur = c => pm.response.json().find(w => w.currency === c);"]


def req(name, method, url, body=None, tests=()):
    r = {"method": method, "header": [{"key": "Content-Type", "value": "application/json"}], "url": url}
    if body is not None:
        r["body"] = {"mode": "raw", "raw": json.dumps(body)}
    item = {"name": name, "request": r}
    if tests:
        item["event"] = [{"listen": "test", "script": {"type": "text/javascript", "exec": list(tests)}}]
    return item


def claim(owner, bonus, currency):
    return {
        "action": "claimed", "bonusId": bonus, "currency": currency, "model": "wager",
        "amount": None, "wageringMultiplier": "35.00", "rewardType": "free_rounds",
    }


def credit(subbalance, currency, ptx, amount="5.00"):
    return {
        "type": "bonus_deposit", "roundId": None, "subBalance": subbalance, "amount": amount,
        "currency": currency, "providerTransactionId": ptx, "gameSessionId": "cls4338",
    }


# JSON can't carry an unquoted {{var}}; placeholders are swapped after dumping.
def raw(body):
    s = json.dumps(body)
    for k in ("bonusA", "bonusB", "bonusC", "bonusUnknown", "ownerId", "otherOwnerId"):
        s = s.replace(f'"@{k}"', "{{%s}}" % k)
    return s


def item(name, method, url, body=None, tests=()):
    it = req(name, method, url, None, tests)
    if body is not None:
        it["request"]["body"] = {"mode": "raw", "raw": raw(body)}
    return it


ok200 = "pm.test('200', () => pm.response.to.have.status(200));"
GAME = W + "/wallet/{{ownerId}}/game-transaction/all"

def wallet(owner, currency):
    return {"ownerId": owner, "realBalance": 100, "depositCount": 1, "currency": currency, "configuration": {
        "bonusOfferAllowed": True, "betAllowed": True, "initialPaidWithdrawalCount": 0,
        "initialPaidWithdrawalAmount": "0", "initialSuccessfulDepositAmount": "0"}}


items = [
    item("setup: player gets EUR and USD wallets, other player EUR", "POST", W + "/initiate-wallets",
         {"wallets": [wallet("@ownerId", "EUR"), wallet("@ownerId", "USD"), wallet("@otherOwnerId", "EUR")]},
         [ok200]),
    item("00. claim free-round bonus A in EUR", "POST", W + "/wallet/{{ownerId}}/bonus-transaction",
         claim("ownerId", "@bonusA", "EUR"), [ok200]),
    item("01. claim free-round bonus B in USD (player now has EUR and USD wallets)", "POST",
         W + "/wallet/{{ownerId}}/bonus-transaction", claim("ownerId", "@bonusB", "USD"), [ok200]),
    item("02. wallets before", "GET", W + "/wallets/{{ownerId}}", None, HELPERS + [
        ok200,
        "pm.test('EUR and USD wallets exist', () => { pm.expect(byCur('EUR')).to.be.ok; pm.expect(byCur('USD')).to.be.ok; });",
        "pm.collectionVariables.set('eurWalletId', byCur('EUR').id);",
    ]),
    item("03. credit bonus A win from the USD session (the bug)", "POST", GAME,
         {**credit("@bonusA", "USD", "{{ptx}}-a")}, [
        ok200,
        "const t = pm.response.json().transactions.find(x => x.type === 'bonus_deposit');",
        "pm.test('booked in bonus A currency (EUR)', () => pm.expect(t.currency).to.eql('EUR'));",
        "pm.test('booked in the EUR wallet', () => pm.expect(String(t.wallet.id)).to.eql(String(pm.collectionVariables.get('eurWalletId'))));",
        "pm.collectionVariables.set('txA', t.id);",
    ]),
    item("04. retry same credit: idempotent", "POST", GAME, {**credit("@bonusA", "USD", "{{ptx}}-a")}, [
        ok200,
        "const t = pm.response.json().transactions.find(x => x.type === 'bonus_deposit');",
        "pm.test('same transaction returned', () => pm.expect(String(t.id)).to.eql(String(pm.collectionVariables.get('txA'))));",
    ]),
    item("05. bonus information: A +5 once, B untouched", "POST", W + "/bonuses/information",
         {"bonusIds": ["@bonusA", "@bonusB"], "ownerIds": ["@ownerId"]}, [
        ok200,
        "const info = id => pm.response.json().find(b => String(b.id) === String(pm.collectionVariables.get(id)));",
        "pm.test('bonus A balance is 5', () => pm.expect(info('bonusA').totalBalance).to.eql(5));",
        "pm.test('bonus B balance is 0', () => pm.expect(info('bonusB').totalBalance).to.eql(0));",
    ]),
    item("06. control: credit bonus B win from the USD session (same currency)", "POST", GAME,
         {**credit("@bonusB", "USD", "{{ptx}}-b")}, [
        ok200,
        "const t = pm.response.json().transactions.find(x => x.type === 'bonus_deposit');",
        "pm.test('booked in USD', () => pm.expect(t.currency).to.eql('USD'));",
    ]),
    item("07. credit an unknown bonus: 404", "POST", GAME, {**credit("@bonusUnknown", "USD", "{{ptx}}-u")}, [
        "pm.test('404', () => pm.response.to.have.status(404));",
    ]),
    item("08. another player claims bonus C in EUR", "POST", W + "/wallet/{{otherOwnerId}}/bonus-transaction",
         claim("otherOwnerId", "@bonusC", "EUR"), [ok200]),
    item("09. credit another player's bonus C: 404", "POST", GAME, {**credit("@bonusC", "EUR", "{{ptx}}-c")}, [
        "pm.test('404', () => pm.response.to.have.status(404));",
    ]),
]

collection = {
    "info": {
        "name": "CLS-4337-CLS-4338 free-round win for a bonus held in another currency",
        "description": "Wallet only (DEV-ONLY, guard signed). Run: ./run.sh",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "event": [{"listen": "prerequest", "script": {"type": "text/javascript", "exec": SIGN}}],
    "variable": [{"key": k, "value": v} for k, v in [
        ("walletUrl", "http://localhost:88"), ("guardKey", ""), ("domainId", "1"),
        ("ownerId", ""), ("otherOwnerId", ""), ("bonusA", ""), ("bonusB", ""), ("bonusC", ""),
        ("bonusUnknown", ""), ("ptx", ""), ("eurWalletId", ""), ("txA", ""),
    ]],
    "item": items,
}

with open(os.path.join(HERE, "CLS-4337-CLS-4338.postman_collection.json"), "w") as f:
    json.dump(collection, f, indent=2)
