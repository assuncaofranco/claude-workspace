import json
J={'Content-Type':'application/json'}
def req(name,method,url,body=None,test='',bo=None,pre=''):
    h=[{'key':'Content-Type','value':'application/json'}] if body is not None else []
    if bo is True: h.append({'key':'Authorization','value':'Bearer {{BO_access_token}}'})
    if bo is False: h.append({'key':'Authorization','value':'Bearer {{access_token}}'})
    r={'name':name,'request':{'method':method,'header':h,'url':url},'event':[]}
    if body is not None: r['request']['body']={'mode':'raw','raw':json.dumps(body,indent=2)}
    if test: r['event'].append({'listen':'test','script':{'type':'text/javascript','exec':test.strip().split('\n')}})
    if pre: r['event'].append({'listen':'prerequest','script':{'type':'text/javascript','exec':pre.strip().split('\n')}})
    return r
BO='{{BO_baseUrl}}/api/gateway/domain/{{domainId}}'
botok=req('BO token','POST','{{BO_baseUrl}}/oauth/2.0/token',{"grant_type":"password","client_id":"{{BO_oauth_client_id}}","client_secret":"{{BO_oauth_client_secret}}","username":"{{BO_username}}","password":"{{BO_password}}"},
"pm.test('status 200', () => pm.response.to.have.status(200));\npm.collectionVariables.set('BO_access_token', pm.response.json().access_token);")
ptok=req('Player token','POST','{{baseUrl}}/oauth/2.0/token',{"grant_type":"player","username":"{{username}}","password":"{{password}}","client_id":"{{oauth_client_id}}","client_secret":"{{oauth_client_secret}}","deviceInformation":{"ip":"127.0.0.1","userAgent":"Mozilla/5.0"}},
"pm.test('status 200', () => pm.response.to.have.status(200));\npm.collectionVariables.set('access_token', pm.response.json().access_token);")
def offer(var):
    return req(f'offer free_rounds ({var})','POST',BO+'/player/{{playerId}}/bonus_configuration/{{rcFrId}}/offer',
      {"playerId":"{{playerId}}","freeRoundsRoundCount":3,"message":"QA CLS-2851"},
      f"pm.test('status 200', () => pm.response.to.have.status(200));\nconst j = pm.response.json();\npm.test('offered', () => pm.expect(j.status).to.eql('offered'));\npm.collectionVariables.set('{var}', j.id);",bo=True)
f1={'name':'1 BO setup','item':[botok,
 req('POST bonus_configuration (free_rounds, Relax)','POST',BO+'/bonus_configuration',
  {"name":"{{runTag}} relax fr","displayName":"{{runTag}} relax fr","type":"free_rounds","model":"direct","offeringMethod":"manual","currency":"EUR","reason":"test","validDuringDays":3,"offerValidFor":2,"claimingEvent":"direct",
   "freeRoundConfiguration":{"freeRoundsGameGateway":"{{gameGatewayId}}","freeRoundsGameStudio":"{{gameStudioId}}","gameIds":[{"id":"{{gameId}}"}],"amount":1}},
  "pm.test('status 200', () => pm.response.to.have.status(200));\npm.collectionVariables.set('rcFrId', pm.response.json().id);",bo=True,
  pre="if (!pm.collectionVariables.get('runTag')) pm.collectionVariables.set('runTag', 'qa2851-' + Date.now());"),
 req('PATCH enable','PATCH',BO+'/bonus_configuration/{{rcFrId}}',{"status":"enabled"},
  "pm.test('status 200', () => pm.response.to.have.status(200));\npm.test('enabled', () => pm.expect(pm.response.json().status).to.eql('enabled'));",bo=True),
 offer('bonusA'), offer('bonusB')]}
find="""const j = pm.response.json();
const list = j.bonus || j;
for (const [v, out] of [['bonusA','gwA'],['bonusB','gwB']]) {
  const want = String(pm.collectionVariables.get(v));
  const b = list.find(x => String(x.id) === want || String(x.id).endsWith('_' + want));
  pm.test(v + ' listed', () => pm.expect(b).to.not.be.undefined);
  if (b) pm.collectionVariables.set(out, String(b.id));
}"""
f2={'name':'2 GW player: session, claim','item':[ptok,
 req('launch Relax game (real) -> cashiertoken','POST','{{baseUrl}}/en/game/{{gameId}}/launch',{"ip":"127.0.0.1","device":"desktop","lobbyUrl":"http://localhost","depositUrl":"http://localhost"},
  "pm.test('status 200', () => pm.response.to.have.status(200));\nconst m = pm.response.text().match(/ticket=([^&\"\\\\]+)/);\npm.test('ticket in launch url', () => pm.expect(m).to.not.be.null);\nif (m) pm.collectionVariables.set('cashiertoken', decodeURIComponent(m[1]));",bo=False),
 req('GET /bonuses','GET','{{baseUrl}}/bonuses',None,"pm.test('status 200', () => pm.response.to.have.status(200));\n"+find,bo=False),
 req('POST /bonuses/claim (A only)','POST','{{baseUrl}}/bonuses/claim',{"bonusIds":["{{gwA}}"]},
  "pm.test('status 200', () => pm.response.to.have.status(200));\npm.test('claimed', () => pm.expect(pm.response.json()[0].status).to.eql('claimed'));",bo=False)]}
def relax(name,promo,token,test):
    return req(name,'POST','{{gameUrl}}/webhook/relax/notifyFreespinsCancel',
      {"txid":"{{$timestamp}}","cashiertoken":token,"gameref":"{{externalGameId}}","customerid":"{{playerId}}","freespinid":1,"promocode":promo},test)
err=lambda code,msg: f"pm.test('status 403', () => pm.response.to.have.status(403));\npm.test('{code}', () => pm.expect(pm.response.json().errorcode).to.eql('{code}'));"+ (f"\npm.test('message', () => pm.expect(pm.response.json().errormessage).to.eql('{msg}'));" if msg else '')
f3={'name':'3 Relax webhook notifyFreespinsCancel (provider callback)','item':[
 relax('cancel claimed bonus A -> 200','{{bonusA}}','{{cashiertoken}}',"pm.test('status 200', () => pm.response.to.have.status(200));"),
 relax('repeat cancel A (Relax retry) -> 403 DAILY_TIME_LIMIT (pre-existing mapping)','{{bonusA}}','{{cashiertoken}}',err('DAILY_TIME_LIMIT',None)),
 relax('offered bonus B, no grant -> 403','{{bonusB}}','{{cashiertoken}}',err('CUSTOM_ERROR','Unable to find free round grant')),
 relax('unknown promocode -> 403','999999999','{{cashiertoken}}',err('CUSTOM_ERROR','Unable to find free round grant')),
 relax('invalid token -> ACCESS_DENIED','{{bonusA}}','wrong_session_token',"pm.test('INVALID_TOKEN', () => pm.expect(pm.response.json().errorcode).to.eql('INVALID_TOKEN'));")]}
f4={'name':'4 GW verify','item':[ptok,
 req('GET /bonuses canceled: A canceled, B still offered','GET','{{baseUrl}}/bonuses?statuses[]=canceled&statuses[]=offered',None,
 """pm.test('status 200', () => pm.response.to.have.status(200));
const list = pm.response.json().bonus || pm.response.json();
const a = list.find(x => String(x.id) === pm.collectionVariables.get('gwA'));
const b = list.find(x => String(x.id) === pm.collectionVariables.get('gwB'));
pm.test('A canceled', () => pm.expect(a && a.status).to.eql('canceled'));
pm.test('B untouched (offered)', () => pm.expect(b && b.status).to.eql('offered'));""",bo=False)]}
vars={'BO_baseUrl':'http://localhost:84','baseUrl':'http://localhost:93','gameUrl':'http://localhost:89','domainId':'1','playerId':'1','gameId':'6','externalGameId':'421','gameGatewayId':'4','gameStudioId':'4'}
cap=['runTag','BO_access_token','access_token','rcFrId','bonusA','bonusB','gwA','gwB','cashiertoken']
c={'info':{'name':'CLS-2851 Relax free spins cancel','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
   'item':[f1,f2,f3,f4],'variable':[{'key':k,'value':v} for k,v in vars.items()]+[{'key':k,'value':''} for k in cap]}
json.dump(c,open('CLS-2851.postman_collection.json','w'),indent=2)
