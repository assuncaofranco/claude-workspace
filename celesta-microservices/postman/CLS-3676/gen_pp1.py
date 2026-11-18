import json
# Preprod-1 regression for CLS-4053, entry points only (BO + gateway). Credentials and card data come from the
# vault at run time. Redelivering the same deposit is not reachable from here: each POST /payment is a new
# transaction, so this run checks that real deposits (initiated + success of one transaction) still reward once
# each, and that a repeated claim keeps answering 404 through the gateway.
def req(name,method,url,body=None,test='',bo=None,pre=''):
    h=[{'key':'Content-Type','value':'application/json'}] if body is not None else []
    if bo is True: h.append({'key':'Authorization','value':'Bearer {{BO_access_token}}'})
    if bo is False: h.append({'key':'Authorization','value':'Bearer {{access_token}}'})
    r={'name':name,'request':{'method':method,'header':h,'url':url},'event':[]}
    if body is not None: r['request']['body']={'mode':'raw','raw':json.dumps(body,indent=2)}
    if test: r['event'].append({'listen':'test','script':{'type':'text/javascript','exec':test.strip().split('\n')}})
    if pre: r['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':pre.strip().split('\n')}})
    return r
log="if (pm.response.code >= 300) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 600));\n"
ok=log+"pm.test('status 200', () => pm.response.to.have.status(200));\n"
BO='{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
botok=req('BO token','POST','{{BO_baseUrl}}/oauth/2.0/token',{"grant_type":"password","client_id":"{{BO_oauth_client_id}}","client_secret":"{{BO_oauth_client_secret}}","username":"{{BO_username}}","password":"{{BO_password}}"},
  ok+"pm.collectionVariables.set('BO_access_token', pm.response.json().access_token);")
ptok=req('Player token','POST','{{baseUrl}}/oauth/2.0/token',{"grant_type":"player","username":"{{username}}","password":"{{password}}","client_id":"{{oauth_client_id}}","client_secret":"{{oauth_client_secret}}","deviceInformation":{"ip":"127.0.0.1","userAgent":"Mozilla/5.0"}},
  ok+"pm.collectionVariables.set('access_token', pm.response.json().access_token);")
setv=lambda k,v: f"pm.collectionVariables.set('{k}', {v});"

# ---- 1 BO setup: rc auto (claimed on reward), rc direct (offered, player claims), one deposit_tier
dates="""if (!pm.collectionVariables.get('runTag')) {
  const t = Date.now(); pm.collectionVariables.set('runTag', 'CLS-4053 - test config ' + t); pm.collectionVariables.set('code', 'cls4053-' + t);
  const d = n => new Date(t + n*86400000).toISOString().slice(0,10);
  pm.collectionVariables.set('startDate', d(-1) + ' 00:00:00'); pm.collectionVariables.set('endDate', d(7) + ' 23:59:59');
}"""
def rc(name,var,claiming):
    return [req(f'POST reward-configuration {name}','POST',BO+'/reward-configuration',
      {"name":"{{runTag}} "+name,"displayName":"{{runTag}} "+name,"type":"free","model":"direct","offeringMethod":"manual","currency":"EUR","validDuringDays":"7","claimingEvent":claiming,"offerAmount":"1","offerValidFor":7},
      ok+setv(var,'pm.response.json().id'),bo=True),
    req(f'PATCH enable {name}','PATCH',BO+'/reward-configuration/{{'+var+'}}',{"status":"enabled"},
      ok+"pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True)]
def pcfg(t=''):  # t names a second configuration (cell 11); '' keeps the single-config variable names
    v,a,code,name='pc'+t,'ag'+t,'{{code}}'+('-'+t if t else ''),'{{runTag}}'+(' '+t if t else '')
    return [req(f'POST promotion-configuration deposit_tier {t}','POST',BO+'/promotion-configuration',
      {"name":name,"currency":"EUR","startDate":"{{startDate}}","endDate":"{{endDate}}","segmentIds":[],"engagementModel":"manual","engagementCode":code,"type":"deposit_tier","playerPromotionLimit":5},
      ok+setv(v,'pm.response.json().id'),bo=True),
    req(f'POST tier aggregator 0-100 {t}','POST',BO+'/promotion-configuration/{{'+v+'}}/reward-aggregators',
      [{"type":"tier","options":{"minAmount":0,"maxAmount":100},"rewards":[]}],
      ok+"const j = pm.response.json(); const a = Array.isArray(j) ? j[0] : j;\n"+setv(a,'a.id'),bo=True),
    req(f'POST reward free_bonus -> rc auto, on the tier {t}','POST',BO+'/promotion-configuration/{{'+v+'}}/reward-aggregator/{{'+a+'}}/reward',
      {"type":"free_bonus","rewardConfigurationId":"{{rcAutoId}}","quantity":1,"options":{"upToAmount":1}},
      ok+"pm.test('reward linked', () => pm.expect(pm.response.json().type).to.eql('free_bonus'));",bo=True),
    req(f'PATCH enable deposit_tier {t}','PATCH',BO+'/promotion-configuration/{{'+v+'}}',{"status":"enabled"},
      ok+"pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True)]
pc=pcfg()
setup=[botok]+rc('rc auto','rcAutoId','automatic')+rc('rc direct','rcDirectId','direct')+pc
setup[1]['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':dates.split('\n')}})
f1={'name':'1 BO setup','item':setup}
f2={'name':'2 GW player opts in','item':[ptok,req('PUT optin','PUT','{{baseUrl}}/promotion-configuration/optin/{{code}}',None,ok,bo=False)]}

# ---- 3/4 real deposits, then the BO count (crediting and the reward are asynchronous: wait before reading)
deposit=lambda n: req(f'POST /payment deposit {n} (no bonusIds)','POST','{{baseUrl}}/payment',
  {"paymentInformation":{"paymentConfigurationId":"{{paymentConfigurationId}}","holder":"{{cardHolder}}","number":"{{cardNumber}}",
    "expirationDate":{"month":"{{cardMonth}}","year":"{{cardYear}}"},"cvv":"{{cardCvv}}","reusable":True},
   "amount":"10","ip":"138.199.14.138","userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv: 81.0) Gecko/20100101 Firefox/81.0)",
   "successUrl":"https://example.com/callback/success","failureUrl":"https://example.com/callback/failure",
   "additionalData":{"seonSession":"{{seonSession}}","browserAcceptHeader":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "browserJavaEnabled":True,"browserLanguage":"en","browserColorDepth":"24","browserScreenHeight":"1200","browserScreenWidth":"1920","browserTimezone":"-120"}},
  ok+"console.log('payment " + str(n) + ": ' + pm.response.text().slice(0, 300));",bo=False)
wait="setTimeout(() => {}, 30000);"
def promos(rewarded,pre='',v='pc'):
    return req(f'GET {v} promotions: {rewarded} rewarded, 1 engaged','GET',BO+'/promotion-configuration/{{'+v+'}}/promotions',None,
      ok+"const j = pm.response.json(); const list = [j.promotions, j.data, j].find(Array.isArray) || [];\n"
      "console.log('promotions: ' + JSON.stringify(list.map(p => [p.id, p.status])));\n"
      "const by = s => list.filter(p => p.status === s).length;\n"
      f"pm.test('rewarded = {rewarded}', () => pm.expect(by('rewarded')).to.eql({rewarded}));\n"
      "pm.test('engaged = 1 (re-engaged)', () => pm.expect(by('engaged')).to.eql(1));",bo=True,pre=pre)
# with no wagering a claimed bonus turns played right away in preprod, so a claim is counted as claimed or played
taken="['claimed','played'].includes(b.status)"
def bonuses(n):
    return req(f'GET bonuses of rc auto: {n} taken','GET',BO+'/bonuses?filter[ownerIds][]={{playerId}}&filter[bonusModelIds][]={{rcAutoId}}&filter[statuses][]=claimed&filter[statuses][]=played&limit=50',None,
      ok+f"pm.test('bonuses taken = {n}', () => pm.expect(pm.response.json().filter(b => {taken}).length).to.eql({n}));",bo=True)
f3={'name':'3 deposit 1 -> rewarded once','item':[ptok,deposit(1),botok,promos(1,wait),bonuses(1)]}
f4={'name':'4 deposit 2 (distinct) -> rewarded again','item':[ptok,deposit(2),botok,promos(2,wait),bonuses(2)]}

# ---- 5 repeated claim through the gateway (the 409 is on promotion, which the gateway still wraps into 404)
offer=lambda var: req(f'POST offer rc direct -> {var}','POST',BO+'/reward/bonus/{{rcDirectId}}/offer',
  {"playerId":"{{playerId}}","message":"QA CLS-4053","amount":1},
  ok+f"const j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\n"+setv(var,'j.id'),bo=True)
cancel=req('POST cancel bonusE','POST',BO+'/reward/bonus/{{bonusE}}/cancel',{"playerId":"{{playerId}}"},
  ok+"pm.test('canceled', () => pm.expect(pm.response.json().status).to.eql('canceled'));",bo=True)
listgw=req('GW GET /reward/bonuses -> capture claim id of D','GET','{{baseUrl}}/reward/bonuses',None,
  ok+"const j = pm.response.json(); const list = [j.bonus, j.bonuses, j.data, j].find(Array.isArray) || [];\n"
  "const want = String(pm.collectionVariables.get('bonusD'));\n"
  "const b = list.find(x => String(x.id) === want || String(x.id).endsWith('_' + want));\n"
  "pm.test('D listed as offered', () => pm.expect(b).to.not.be.undefined);\n"
  "if (b) "+setv('claimD','String(b.id)'),bo=False)
def claim(name,ids,code,extra=''):
    return req(name,'POST','{{baseUrl}}/reward/bonuses/claim',{"rewardIds":ids},
      log+f"pm.test('status {code}', () => pm.response.to.have.status({code}));\n"+extra,bo=False)
f5={'name':'5 claim twice through the gateway','item':[botok,offer('bonusD'),offer('bonusE'),cancel,ptok,listgw,
  claim('POST claim D -> 200',["{{claimD}}"],200,"pm.test('claimed', () => pm.expect(JSON.stringify(pm.response.json())).to.include('claimed'));"),
  claim('POST claim D again -> 404 (gateway wraps the 409)',["{{claimD}}"],404),
  claim('POST claim canceled E -> 404',["{{rcDirectId}}_{{bonusE}}"],404),
  claim('POST claim unknown bonus -> 404',["{{rcDirectId}}_999999999"],404),
  botok,
  req('GET bonuses of rc direct: D taken once, E canceled','GET',BO+'/bonuses?filter[ownerIds][]={{playerId}}&filter[bonusModelIds][]={{rcDirectId}}&filter[statuses][]=claimed&filter[statuses][]=played&filter[statuses][]=canceled&limit=50',None,
    ok+"const list = pm.response.json(); const st = v => (list.find(x => String(x.id) === String(pm.collectionVariables.get(v))) || {}).status;\n"
    "pm.test('D taken', () => pm.expect(['claimed','played']).to.include(st('bonusD')));\npm.test('E canceled', () => pm.expect(st('bonusE')).to.eql('canceled'));\n"
    "pm.test('exactly one taken', () => pm.expect(list.filter(b => ['claimed','played'].includes(b.status)).length).to.eql(1));",bo=True)]}

vars={'BO_baseUrl':'https://backend-api.preprod-1.octopodev.com','baseUrl':'https://gateway.preprod-1.octopodev.com','domainId':'56','playerId':'282570'}
cap=['runTag','code','startDate','endDate','BO_access_token','access_token','rcAutoId','rcDirectId','pc','ag','bonusD','bonusE','claimD']
c={'info':{'name':'CLS-4053 pp1: deposit_tier rewards once per deposit, repeated claim','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
   'item':[f1,f2,f3,f4,f5],'variable':[{'key':k,'value':v} for k,v in vars.items()]+[{'key':k,'value':''} for k in cap]}
json.dump(c,open('CLS-4053.pp1.postman_collection.json','w'),indent=2)

# ---- cell 11: one real deposit reaching two deposit_tier configurations rewards each once
s11=[botok]+rc('rc auto','rcAutoId','automatic')+pcfg('A')+pcfg('B')
s11[1]['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':dates.split('\n')}})
optin=lambda t: req(f'PUT optin {t}','PUT','{{baseUrl}}/promotion-configuration/optin/{{code}}-'+t,None,ok,bo=False)
c11={'info':{'name':'CLS-4053 pp1 cell 11: one deposit, two deposit_tier configurations','schema':c['info']['schema']},
   'item':[{'name':'1 BO setup: A and B','item':s11},{'name':'2 GW player opts in to A and B','item':[ptok,optin('A'),optin('B')]},
     {'name':'3 one deposit -> A and B rewarded once each','item':[ptok,deposit(1),botok,promos(1,wait,'pcA'),promos(1,'','pcB'),bonuses(2)]}],
   'variable':[{'key':k,'value':v} for k,v in vars.items()]+[{'key':k,'value':''} for k in cap+['pcA','pcB','agA','agB']]}
json.dump(c11,open('CLS-4053.pp1-cell11.postman_collection.json','w'),indent=2)
