import json
def req(name,method,url,body=None,test='',bo=None,pre=''):
    h=[{'key':'Content-Type','value':'application/json'}] if body is not None else []
    if bo is True: h.append({'key':'Authorization','value':'Bearer {{BO_access_token}}'})
    if bo is False: h.append({'key':'Authorization','value':'Bearer {{access_token}}'})
    r={'name':name,'request':{'method':method,'header':h,'url':url},'event':[]}
    if body is not None: r['request']['body']={'mode':'raw','raw':json.dumps(body,indent=2)}
    if test: r['event'].append({'listen':'test','script':{'type':'text/javascript','exec':test.strip().split('\n')}})
    if pre: r['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':pre.strip().split('\n')}})
    return r
ok="pm.test('status 200', () => pm.response.to.have.status(200));\n"
BO='{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
SB='{{walletUrl}}/api/domain/{{domainId}}/wallet/{{playerId}}/sb'
botok=req('BO token','POST','{{BO_baseUrl}}/oauth/2.0/token',{"grant_type":"password","client_id":"{{BO_oauth_client_id}}","client_secret":"{{BO_oauth_client_secret}}","username":"{{BO_username}}","password":"{{BO_password}}"},
  ok+"pm.environment.set('BO_access_token', pm.response.json().access_token);")
ptok=req('Player token','POST','{{baseUrl}}/oauth/2.0/token',{"grant_type":"player","username":"{{username}}","password":"{{password}}","client_id":"{{oauth_client_id}}","client_secret":"{{oauth_client_secret}}","deviceInformation":{"ip":"127.0.0.1","userAgent":"Mozilla/5.0"}},
  ok+"pm.environment.set('access_token', pm.response.json().access_token);")
def offer(var,amount):
    return req(f'offer free bonus {var} ({amount} EUR)','POST',BO+'/player/{{playerId}}/bonus_configuration/{{rcId}}/offer',
      {"playerId":"{{playerId}}","amount":amount,"message":"QA CLS-2485"},
      ok+f"const j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\npm.environment.set('{var}', j.id);",bo=True)
# GW /bonuses ids are composite (<domain>_<id>); capture them on the player side.
def bostatus(name,expect):
    checks="\n".join(f"pm.test('{v} is {s}', () => pm.expect(st('{v}')).to.eql('{s}'));" for v,s in expect)
    return req(name,'GET',BO+'/bonuses?filter[ownerIds][]={{playerId}}&filter[bonusModelIds][]={{rcId}}&filter[statuses][]=offered&filter[statuses][]=claimed&filter[statuses][]=played&filter[statuses][]=canceled&limit=50',None,
      ok+"const list = pm.response.json();\nconst st = v => (list.find(x => String(x.id) === String(pm.environment.get(v))) || {}).status;\n"+checks,bo=True)

pre_bal=req('GW player balance (precondition)','GET','{{baseUrl}}/wallet/balances',None,
  ok+"const eur = pm.response.json().balances.find(b => b.currency === 'EUR');\nconst w = Number(eur ? eur.withdrawable : 0);\npm.environment.set('fixAmount', w < 0 ? String(Math.ceil(-w) + 50) : '');",bo=False)
fix=req('BO adjustment_up if withdrawable is negative (wallet rejects claims otherwise)','POST',BO+'/player/{{playerId}}/wallet/transaction',
  {"type":"adjustment_up","amount":"{{fixAmount}}","currency":"EUR","note":"QA CLS-2485 precondition","reason":"payment_provider_issue"},
  ok,bo=True,pre="if (!pm.environment.get('fixAmount')) pm.execution.skipRequest();")
f0={'name':'0 Precondition: player 1 withdrawable not negative','item':[ptok,pre_bal,botok,fix]}
f1={'name':'1 BO setup','item':[botok,
  req('POST bonus_configuration (free, manual)','POST',BO+'/bonus_configuration',
    {"name":"{{runTag}} free","displayName":"{{runTag}} free","type":"free","model":"wager","wageringMultiplier":"5.00","maxWinMultiplier":"10","offeringMethod":"manual","currency":"EUR","reason":"test","validDuringDays":3,"offerValidFor":2,"claimingEvent":"direct"},
    ok+"pm.environment.set('rcId', pm.response.json().id);",bo=True,
    pre="if (!pm.environment.get('runTag')) { const t = Date.now(); pm.environment.set('runTag', 'qa2485-' + t); pm.environment.set('roundId', String(Math.floor(t / 1000))); }"),
  req('PATCH enable','PATCH',BO+'/bonus_configuration/{{rcId}}',{"status":"enabled"},
    ok+"pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True),
  offer('bonusR',10), offer('bonusC',5)]}
find="""const list = pm.response.json().bonus || pm.response.json();
for (const [v, out] of [['bonusR','gwR'],['bonusC','gwC']]) {
  const want = String(pm.environment.get(v));
  const b = list.find(x => String(x.id) === want || String(x.id).endsWith('_' + want));
  pm.test(v + ' listed', () => pm.expect(b).to.not.be.undefined);
  if (b) pm.environment.set(out, String(b.id));
}"""
f2={'name':'2 GW player claims both','item':[ptok,
  req('GET /bonuses','GET','{{baseUrl}}/bonuses',None,ok+find,bo=False),
  req('POST /bonuses/claim (R and C)','POST','{{baseUrl}}/bonuses/claim',{"bonusIds":["{{gwR}}","{{gwC}}"]},
    ok+"pm.test('both claimed', () => pm.expect(pm.response.json().map(b => b.status)).to.eql(['claimed','claimed']));",bo=False),
  req('GET /wallet/balances -> bonusBalance','GET','{{baseUrl}}/wallet/balances',None,
    ok+"const eur = pm.response.json().balances.find(b => b.currency === 'EUR');\npm.test('has bonus balance', () => pm.expect(eur.bonus).to.be.above(0));\npm.environment.set('bonusBalance', String(eur.bonus));",bo=False)]}
f3={'name':'3 DEV-ONLY sportsbook bonus bet (wallet, SB provider side)','item':[
  req('POST sb/bonus-bet the whole bonus balance','POST',SB+'/bonus-bet',
    {"amount":"{{bonusBalance}}","currency":"EUR","providerTransactionId":"{{runTag}}-bet","roundId":"{{roundId}}"},
    ok+"pm.test('bonus balance spent', () => pm.expect(pm.response.json().balance.bonusBalance).to.eql(0));")]}
f4={'name':'4 BO verify played (after promotion consumed Depleted)','item':[botok,bostatus('GET bonuses: R and C played',[('bonusR','played'),('bonusC','played')])]}
f5={'name':'5 DEV-ONLY sportsbook rollback (wallet, SB provider side)','item':[
  req('POST sb/rollback the bonus bet','POST',SB+'/rollback/{{runTag}}-bet',
    {"amount":"{{bonusBalance}}","providerTransactionId":"{{runTag}}-rb"},
    "if (pm.response.code !== 200) console.log(pm.response.text());\n"+ok+"pm.test('bonus balance restored', () => pm.expect(String(pm.response.json().balance.bonusBalance)).to.eql(pm.environment.get('bonusBalance')));")]}
f6={'name':'6 BO verify claimed again (after promotion consumed Restored)','item':[botok,bostatus('GET bonuses: R and C claimed',[('bonusR','claimed'),('bonusC','claimed')])]}
f7={'name':'7 BO cancel bonus C','item':[botok,
  req('POST player/{p}/bonus/{C}/cancel','POST',BO+'/player/{{playerId}}/bonus/{{bonusC}}/cancel',{"playerId":"{{playerId}}"},
    ok+"pm.test('canceled', () => pm.expect(pm.response.json().status).to.eql('canceled'));",bo=True),
  bostatus('GET bonuses: C canceled, R still claimed',[('bonusC','canceled'),('bonusR','claimed')])]}

vars={'BO_baseUrl':'http://localhost:84','baseUrl':'http://localhost:93','walletUrl':'http://localhost:88','domainId':'1','playerId':'1'}
cap=['runTag','roundId','BO_access_token','access_token','rcId','bonusR','bonusC','gwR','gwC','bonusBalance']
c={'info':{'name':'CLS-2485 move bonus cleanup: SB rollback and BO cancel','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
   'item':[f0,f1,f2,f3,f4,f5,f6,f7],'variable':[{'key':k,'value':v} for k,v in vars.items()]+[{'key':k,'value':''} for k in cap]}
json.dump(c,open('CLS-2485.postman_collection.json','w'),indent=2)
