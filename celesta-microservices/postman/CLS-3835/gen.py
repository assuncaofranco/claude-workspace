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
bad="pm.test('status 400', () => pm.response.to.have.status(400));\n"
# limit=1000 is accepted: every "reference" request below uses it.
over=bad+"pm.test('error is on limit', () => pm.expect(Object.keys(pm.response.json().errors)).to.eql(['limit']));"
BO='{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
GW='{{baseUrl}}'
skip_if_enough="if (Number(pm.collectionVariables.get('toOffer')) <= 0) pm.execution.skipRequest();"

ptok=req('Player token','POST',GW+'/oauth/2.0/token',{"grant_type":"player","username":"{{username}}","password":"{{password}}","client_id":"{{oauth_client_id}}","client_secret":"{{oauth_client_secret}}","deviceInformation":{"ip":"127.0.0.1","userAgent":"Mozilla/5.0"}},
  ok+"""const t = pm.response.json().access_token;
pm.collectionVariables.set('access_token', t);
const b64 = t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
const claims = JSON.parse(CryptoJS.enc.Base64.parse(b64).toString(CryptoJS.enc.Utf8));
pm.collectionVariables.set('playerId', String(claims.sub));
pm.collectionVariables.set('domainId', String(claims.domain_id));
pm.collectionVariables.set('currency', claims.customer.currency);""")
botok=req('BO token','POST','{{BO_baseUrl}}/oauth/2.0/token',{"grant_type":"password","client_id":"{{BO_oauth_client_id}}","client_secret":"{{BO_oauth_client_secret}}","username":"{{BO_username}}","password":"{{BO_password}}"},
  ok+"pm.collectionVariables.set('BO_access_token', pm.response.json().access_token);",pre=skip_if_enough)

# The full list (explicit limit 1000) is the reference every default-page check is compared against.
ids="const ids = pm.response.json().bonus.map(b => String(b.id));\n"
full=lambda var: "JSON.parse(pm.collectionVariables.get('"+var+"'))"

f0={'name':'0 Baseline: how many bonuses the player has','item':[ptok,
  req('GET /bonuses?limit=1000','GET',GW+'/bonuses?limit=1000',None,
    ok+ids+"pm.collectionVariables.set('toOffer', String(Math.max(0, Number(pm.variables.get('minBonuses')) - ids.length)));\nconsole.log('player has ' + ids.length + ' bonuses, offering ' + pm.collectionVariables.get('toOffer'));",bo=False)]}

f1={'name':'1 BO setup: top the player up to minBonuses (skipped when already there)','item':[botok,
  req('POST bonus_configuration (free, manual)','POST',BO+'/bonus_configuration',
    {"name":"qa3835-{{$timestamp}}","displayName":"qa3835","type":"free","model":"wager","wageringMultiplier":"5.00","maxWinMultiplier":"10","offeringMethod":"manual","currency":"{{currency}}","reason":"test","validDuringDays":3,"offerValidFor":2,"claimingEvent":"direct"},
    ok+"pm.collectionVariables.set('rcId', pm.response.json().id);",bo=True,pre=skip_if_enough),
  req('PATCH enable','PATCH',BO+'/bonus_configuration/{{rcId}}',{"status":"enabled"},
    ok+"pm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True,pre=skip_if_enough),
  req('POST offer (loops until toOffer is 0)','POST',BO+'/player/{{playerId}}/bonus_configuration/{{rcId}}/offer',
    {"playerId":"{{playerId}}","amount":1,"message":"QA CLS-3835"},
    ok+"pm.test('offered', () => pm.expect(pm.response.json().status).to.eql('offered'));\nconst left = Number(pm.collectionVariables.get('toOffer')) - 1;\npm.collectionVariables.set('toOffer', String(left));\nif (left > 0) pm.execution.setNextRequest(pm.info.requestName);",bo=True,pre=skip_if_enough)]}

f2={'name':'2 GW /bonuses','item':[ptok,
  req('reference: ?limit=1000 (whole list)','GET',GW+'/bonuses?limit=1000',None,
    ok+ids+"pm.test('player has more than 50 bonuses', () => pm.expect(ids.length).to.be.above(50));\npm.collectionVariables.set('fullIds', JSON.stringify(ids));",bo=False),
  req('no params -> first 50, same order','GET',GW+'/bonuses',None,
    ok+ids+"const all = "+full('fullIds')+";\npm.test('exactly 50', () => pm.expect(ids.length).to.eql(50));\npm.test('same first 50 as the whole list', () => pm.expect(ids).to.eql(all.slice(0, 50)));",bo=False),
  req('?limit=60 -> 60','GET',GW+'/bonuses?limit=60',None,
    ok+ids+"const all = "+full('fullIds')+";\npm.test('min(60, total)', () => pm.expect(ids).to.eql(all.slice(0, 60)));",bo=False),
  req('?offset=50 -> next page of up to 50','GET',GW+'/bonuses?offset=50',None,
    ok+ids+"const all = "+full('fullIds')+";\npm.test('rows 51..100', () => pm.expect(ids).to.eql(all.slice(50, 100)));",bo=False),
  req('?limit=2&offset=51 -> 2','GET',GW+'/bonuses?limit=2&offset=51',None,
    ok+ids+"const all = "+full('fullIds')+";\npm.test('rows 52 and 53', () => pm.expect(ids).to.eql(all.slice(51, 53)));",bo=False),
  req('?limit= (blank) -> default 50','GET',GW+'/bonuses?limit=',None,
    ok+ids+"const all = "+full('fullIds')+";\npm.test('same as no limit', () => pm.expect(ids).to.eql(all.slice(0, 50)));",bo=False),
  req('?limit=1001 -> 400 on limit','GET',GW+'/bonuses?limit=1001',None,over,bo=False),
  req('?limit=0 -> 400','GET',GW+'/bonuses?limit=0',None,bad,bo=False),
  req('?limit=-1 -> 400','GET',GW+'/bonuses?limit=-1',None,bad,bo=False),
  req('?limit=abc -> 400','GET',GW+'/bonuses?limit=abc',None,bad,bo=False),
  req('?offset=-1 -> 400','GET',GW+'/bonuses?offset=-1',None,bad,bo=False),
  req('reference: statuses[]=offered&limit=1000','GET',GW+'/bonuses?statuses[]=offered&limit=1000',None,
    ok+ids+"pm.collectionVariables.set('offeredIds', JSON.stringify(ids));",bo=False),
  req('statuses[]=offered, no limit -> filter applied before the cut','GET',GW+'/bonuses?statuses[]=offered',None,
    ok+"const list = pm.response.json().bonus;\nconst all = "+full('offeredIds')+";\npm.test('only offered', () => list.forEach(b => pm.expect(b.status).to.eql('offered')));\npm.test('first min(50, offered)', () => pm.expect(list.map(b => String(b.id))).to.eql(all.slice(0, 50)));",bo=False),
  req('reference: statuses[]=claimed&limit=1000','GET',GW+'/bonuses?statuses[]=claimed&limit=1000',None,
    ok+ids+"pm.collectionVariables.set('claimedIds', JSON.stringify(ids));",bo=False),
  req('statuses[]=claimed, no limit -> under 50 comes back whole','GET',GW+'/bonuses?statuses[]=claimed',None,
    ok+ids+"const all = "+full('claimedIds')+";\npm.test('fewer than 50 claimed (precondition)', () => pm.expect(all.length).to.be.below(50));\npm.test('all of them', () => pm.expect(ids).to.eql(all));",bo=False)]}

f3={'name':'3 GW /reward/bonuses','item':[ptok,
  req('reference: ?limit=1000','GET',GW+'/reward/bonuses?limit=1000',None,
    ok+ids+"pm.test('more than 50', () => pm.expect(ids.length).to.be.above(50));\npm.collectionVariables.set('rewardIds', JSON.stringify(ids));",bo=False),
  req('no params -> first 50','GET',GW+'/reward/bonuses',None,
    ok+ids+"const all = "+full('rewardIds')+";\npm.test('exactly 50', () => pm.expect(ids.length).to.eql(50));\npm.test('same first 50', () => pm.expect(ids).to.eql(all.slice(0, 50)));",bo=False),
  req('?limit=60 -> 60','GET',GW+'/reward/bonuses?limit=60',None,
    ok+ids+"const all = "+full('rewardIds')+";\npm.test('min(60, total)', () => pm.expect(ids).to.eql(all.slice(0, 60)));",bo=False),
  req('?limit=0 -> 400','GET',GW+'/reward/bonuses?limit=0',None,bad,bo=False),
  req('?limit=1001 -> 400 on limit','GET',GW+'/reward/bonuses?limit=1001',None,over,bo=False)]}

vars={'baseUrl':'http://localhost:93','BO_baseUrl':'http://localhost:84','minBonuses':'60'}
cap=['playerId','domainId','currency','access_token','BO_access_token','toOffer','rcId','fullIds','offeredIds','claimedIds','rewardIds']
c={'info':{'name':'CLS-3835 gateway default bonus list page size 50','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
   'item':[f0,f1,f2,f3],'variable':[{'key':k,'value':v} for k,v in vars.items()]+[{'key':k,'value':''} for k in cap]}
json.dump(c,open('CLS-3835.postman_collection.json','w'),indent=2)
