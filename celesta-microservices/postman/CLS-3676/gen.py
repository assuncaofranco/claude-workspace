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
ok="if (pm.response.code !== 200) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 400));\npm.test('status 200', () => pm.response.to.have.status(200));\n"
BO='{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
botok=req('BO token','POST','{{BO_baseUrl}}/oauth/2.0/token',{"grant_type":"password","client_id":"{{BO_oauth_client_id}}","client_secret":"{{BO_oauth_client_secret}}","username":"{{BO_username}}","password":"{{BO_password}}"},
  ok+"pm.environment.set('BO_access_token', pm.response.json().access_token);")
ptok=req('Player token','POST','{{baseUrl}}/oauth/2.0/token',{"grant_type":"player","username":"{{username}}","password":"{{password}}","client_id":"{{oauth_client_id}}","client_secret":"{{oauth_client_secret}}","deviceInformation":{"ip":"127.0.0.1","userAgent":"Mozilla/5.0"}},
  ok+"pm.environment.set('access_token', pm.response.json().access_token);")

# ---- 0 precondition (wallet rejects every claim while EUR withdrawable is negative)
pre_bal=req('GW player balance (precondition)','GET','{{baseUrl}}/wallet/balances',None,
  ok+"const eur = (pm.response.json().balances || []).find(b => b.currency === 'EUR');\nconst w = Number(eur ? eur.withdrawable : 0);\npm.environment.set('fixAmount', w < 0 ? String(Math.ceil(-w) + 50) : '');",bo=False)
fix=req('BO adjustment_up if withdrawable is negative','POST',BO+'/player/{{playerId}}/wallet/transaction',
  {"type":"adjustment_up","amount":"{{fixAmount}}","currency":"EUR","note":"QA CLS-3676 precondition","reason":"payment_provider_issue"},
  ok,bo=True,pre="if (!pm.environment.get('fixAmount')) pm.execution.skipRequest();")
f0={'name':'0 Precondition: player withdrawable not negative','item':[ptok,pre_bal,botok,fix]}

# ---- 1 BO setup: two reward configurations, two deposit_tier configurations (A and B) with the same automatic reward
def rc(name,var,claiming):
    return [req(f'POST reward-configuration {name}','POST',BO+'/reward-configuration',
      {"name":"{{runTag}} "+name,"displayName":"{{runTag}} "+name,"type":"free","model":"direct","offeringMethod":"manual","currency":"{{currency}}","validDuringDays":"7","claimingEvent":claiming,"offerAmount":"10","offerValidFor":14},
      ok+f"pm.environment.set('{var}', pm.response.json().id);",bo=True),
    req(f'PATCH enable {name}','PATCH',BO+'/reward-configuration/{{'+var+'}}',{"status":"enabled"},
      ok+"pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True)]
def pc(tag,var):
    return [req(f'POST promotion-configuration deposit_tier {tag}','POST',BO+'/promotion-configuration',
      {"name":"{{runTag}} "+tag,"currency":"{{currency}}","startDate":"{{startDate}}","endDate":"{{endDate}}","segmentIds":[],"engagementModel":"manual","engagementCode":"{{runTag}}-"+tag,"type":"deposit_tier","playerPromotionLimit":6},
      ok+f"pm.environment.set('{var}', pm.response.json().id);",bo=True),
    req(f'POST tier aggregator 0-100 {tag}','POST',BO+'/promotion-configuration/{{'+var+'}}/reward-aggregators',
      [{"type":"tier","options":{"minAmount":0,"maxAmount":100},"rewards":[]}],
      ok+f"const j = pm.response.json(); const a = Array.isArray(j) ? j[0] : j;\npm.environment.set('ag{tag}', a.id);",bo=True),
    # the tier pays the rewards hung on the aggregator, not the ones at configuration level
    req(f'POST reward free_bonus -> rc auto, on the tier {tag}','POST',BO+'/promotion-configuration/{{'+var+'}}/reward-aggregator/{{ag'+tag+'}}/reward',
      {"type":"free_bonus","rewardConfigurationId":"{{rcAutoId}}","quantity":10,"options":{"upToAmount":10}},
      ok+"pm.test('reward linked', () => pm.expect(pm.response.json().type).to.eql('free_bonus'));",bo=True),
    req(f'PATCH enable {tag}','PATCH',BO+'/promotion-configuration/{{'+var+'}}',{"status":"enabled"},
      ok+"pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True)]
dates="""if (!pm.environment.get('runTag')) {
  const t = Date.now(); pm.environment.set('runTag', 'qa3676-' + t);
  const d = n => new Date(t + n*86400000).toISOString().slice(0,10);
  pm.environment.set('startDate', d(-1) + ' 00:00:00'); pm.environment.set('endDate', d(30) + ' 23:59:59');
}"""
setup=[botok]+rc('rc auto','rcAutoId','automatic')+rc('rc direct','rcDirectId','direct')+pc('A','pcA')+pc('B','pcB')
setup[1]['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':dates.split('\n')}})
f1={'name':'1 BO setup','item':setup}

# ---- 2 GW player opts in to A and B by engagement code
f2={'name':'2 GW player opts in','item':[ptok,
  req('PUT optin A','PUT','{{baseUrl}}/promotion-configuration/optin/{{runTag}}-A',None,ok,bo=False),
  req('PUT optin B','PUT','{{baseUrl}}/promotion-configuration/optin/{{runTag}}-B',None,ok,bo=False)]}

# ---- verify folders (run.sh pushes the deposit jobs and runs the consumer between them)
def promos(var,rewarded):
    return req(f'GET {var} promotions: {rewarded} rewarded, 1 engaged','GET',BO+'/promotion-configuration/{{'+var+'}}/promotions',None,
      ok+"const j = pm.response.json(); const list = [j.promotions, j.data, j].find(Array.isArray) || [];\n"
      "const by = s => list.filter(p => p.status === s).length;\n"
      f"pm.test('{var} rewarded = {rewarded}', () => pm.expect(by('rewarded')).to.eql({rewarded}));\n"
      f"pm.test('{var} engaged = 1 (re-engaged)', () => pm.expect(by('engaged')).to.eql(1));",bo=True)
def bonuses(claimed):
    return req(f'GET bonuses of rc auto: {claimed} claimed','GET',BO+'/bonuses?filter[ownerIds][]={{playerId}}&filter[bonusModelIds][]={{rcAutoId}}&filter[statuses][]=offered&filter[statuses][]=claimed&limit=50',None,
      ok+"const list = pm.response.json();\n"
      f"pm.test('claimed bonuses = {claimed}', () => pm.expect(list.filter(b => b.status === 'claimed').length).to.eql({claimed}));\n"
      "pm.test('no bonus left offered', () => pm.expect(list.filter(b => b.status === 'offered').length).to.eql(0));",bo=True)
def verify(n,title,rewarded):
    return {'name':f'{n} BO verify: {title}','item':[botok,promos('pcA',rewarded),promos('pcB',rewarded),bonuses(2*rewarded)]}
f3=verify(3,'tx1 delivered twice -> each configuration rewarded once (cells 1, 11)',1)
f4=verify(4,'tx2 (distinct deposit) -> rewarded again (cell 12)',2)
f5=verify(5,'tx3 initiated, pending, success -> rewarded (cell 13)',3)
f6=verify(6,'tx4 initiated, tx5 success, tx4 success -> both rewarded (cell 13a)',5)

# ---- 7 item 2: repeated claim answers 409; canceled and unknown stay 404
offer=lambda var: req(f'POST offer rc direct -> {var}','POST',BO+'/reward/bonus/{{rcDirectId}}/offer',
  {"playerId":"{{playerId}}","message":"QA CLS-3676","amount":10},
  ok+f"const j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\npm.environment.set('{var}', j.id);",bo=True)
cancel=req('POST cancel bonusE','POST',BO+'/reward/bonus/{{bonusE}}/cancel',{"playerId":"{{playerId}}"},
  ok+"pm.test('canceled', () => pm.expect(pm.response.json().status).to.eql('canceled'));",bo=True)
listgw=req('GW GET /reward/bonuses -> capture claim id of D','GET','{{baseUrl}}/reward/bonuses',None,
  ok+"const j = pm.response.json(); const list = [j.bonus, j.bonuses, j.data, j].find(Array.isArray) || [];\n"
  "const want = String(pm.environment.get('bonusD'));\n"
  "const b = list.find(x => String(x.id) === want || String(x.id).endsWith('_' + want));\n"
  "pm.test('D listed as offered', () => pm.expect(b).to.not.be.undefined);\n"
  "if (b) pm.environment.set('claimD', String(b.id));",bo=False)
def claim(name,ids,code,extra=''):
    return req(name,'POST','{{baseUrl}}/reward/bonuses/claim',{"rewardIds":ids},
      f"pm.test('status {code}', () => pm.response.to.have.status({code}));\n"+extra,bo=False)
# DEV-ONLY: the 409 lives on promotion's endpoint (what the money-path sheet checks); the gateway still wraps every
# promotion 4xx into 404, so the player-facing call keeps answering 404 until the gateway is changed.
guard="""const url = pm.variables.replaceIn(pm.request.url.toString());
const m = url.match(/^https?:\\/\\/([^\\/:]+)(?::(\\d+))?([^?]*)/);
const method = pm.request.method.toUpperCase();
let signed = method + m[1] + decodeURIComponent(m[3]);
if (['POST','PUT','PATCH'].includes(method)) signed += CryptoJS.MD5(pm.variables.replaceIn(pm.request.body.raw)).toString();
pm.request.headers.upsert({ key: 'x-guard-secret', value: CryptoJS.HmacSHA256(signed, pm.environment.get('guardKey')).toString() });"""
promo_claim=req('DEV-ONLY promotion: POST claim D again -> 409 (cell 17)','POST','{{promotionUrl}}/api/domain/{{domainId}}/player/{{playerId}}/reward/bonuses/claim',
  {"rewardIds":["{{rcDirectId}}_{{bonusD}}"]},
  "console.log('409 body: ' + pm.response.text());\npm.test('status 409', () => pm.response.to.have.status(409));",pre=guard)
f7={'name':'7 claim twice: 409 on the second (cells 17, 18, 19)','item':[botok,offer('bonusD'),offer('bonusE'),cancel,ptok,listgw,
  claim('POST claim D -> 200 claimed',["{{claimD}}"],200,"pm.test('claimed', () => pm.expect(JSON.stringify(pm.response.json())).to.include('claimed'));"),
  promo_claim,
  claim('GW POST claim D again -> 404 (gateway wraps the 409)',["{{claimD}}"],404),
  claim('POST claim canceled E -> 404 (cell 18)',["{{rcDirectId}}_{{bonusE}}"],404),
  claim('POST claim unknown bonus -> 404 (cell 19)',["{{rcDirectId}}_999999999"],404),
  botok,
  req('GET bonuses of rc direct: D claimed once, E canceled','GET',BO+'/bonuses?filter[ownerIds][]={{playerId}}&filter[bonusModelIds][]={{rcDirectId}}&filter[statuses][]=offered&filter[statuses][]=claimed&filter[statuses][]=canceled&limit=50',None,
    ok+"const list = pm.response.json(); const st = v => (list.find(x => String(x.id) === String(pm.environment.get(v))) || {}).status;\n"
    "pm.test('D claimed', () => pm.expect(st('bonusD')).to.eql('claimed'));\npm.test('E canceled', () => pm.expect(st('bonusE')).to.eql('canceled'));\n"
    "pm.test('exactly one claimed', () => pm.expect(list.filter(b => b.status === 'claimed').length).to.eql(1));",bo=True)]}

vars={'BO_baseUrl':'http://localhost:84','baseUrl':'http://localhost:93','promotionUrl':'http://localhost:99','domainId':'1','playerId':'1','currency':'EUR'}
cap=['runTag','startDate','endDate','BO_access_token','access_token','fixAmount','rcAutoId','rcDirectId','pcA','pcB','agA','agB','bonusD','bonusE','claimD']
c={'info':{'name':'CLS-3676 money-path idempotency: duplicated deposit, repeated claim','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
   'item':[f0,f1,f2,f3,f4,f5,f6,f7],'variable':[{'key':k,'value':v} for k,v in vars.items()]+[{'key':k,'value':''} for k in cap]}
json.dump(c,open('CLS-3676.postman_collection.json','w'),indent=2)
