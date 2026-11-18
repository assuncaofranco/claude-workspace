import json
# Preprod deposit through the player entry point (gateway POST /payment). Card data and credentials are
# never written here: they come from the vault / the runner's environment at run time.
def req(name,method,url,body=None,test='',auth=False):
    h=[{'key':'Content-Type','value':'application/json'}] if body is not None else []
    if auth: h.append({'key':'Authorization','value':'Bearer {{access_token}}'})
    r={'name':name,'request':{'method':method,'header':h,'url':url},'event':[]}
    if body is not None: r['request']['body']={'mode':'raw','raw':json.dumps(body,indent=2)}
    if test: r['event'].append({'listen':'test','script':{'type':'text/javascript','exec':test.strip().split('\n')}})
    return r
log="if (pm.response.code >= 300) console.log(pm.request.method + ' ' + pm.request.url + ' -> ' + pm.response.code + ' ' + pm.response.text().slice(0, 600));\n"
ok=log+"pm.test('status 200', () => pm.response.to.have.status(200));\n"
ptok=req('Player token','POST','{{baseUrl}}/oauth/2.0/token',
  {"grant_type":"player","username":"{{username}}","password":"{{password}}","client_id":"{{oauth_client_id}}","client_secret":"{{oauth_client_secret}}","deviceInformation":{"ip":"127.0.0.1","userAgent":"Mozilla/5.0"}},
  ok+"pm.collectionVariables.set('access_token', pm.response.json().access_token);")
bal=lambda tag: req(f'GET /wallet/balances ({tag})','GET','{{baseUrl}}/wallet/balances',None,
  ok+"const eur = (pm.response.json().balances || []).find(b => b.currency === 'EUR') || {};\nconsole.log('" + tag + " EUR: ' + JSON.stringify(eur));",auth=True)
deposit=req('POST /payment (deposit, no bonusIds)','POST','{{baseUrl}}/payment',
  {"paymentInformation":{"paymentConfigurationId":"{{paymentConfigurationId}}","holder":"{{cardHolder}}","number":"{{cardNumber}}",
    "expirationDate":{"month":"{{cardMonth}}","year":"{{cardYear}}"},"cvv":"{{cardCvv}}","reusable":True},
   "amount":"{{depositAmount}}","ip":"138.199.14.138","userAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv: 81.0) Gecko/20100101 Firefox/81.0)",
   "successUrl":"https://example.com/callback/success","failureUrl":"https://example.com/callback/failure",
   "additionalData":{"seonSession":"{{seonSession}}","browserAcceptHeader":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
     "browserJavaEnabled":True,"browserLanguage":"en","browserColorDepth":"24","browserScreenHeight":"1200","browserScreenWidth":"1920","browserTimezone":"-120"}},
  ok+"console.log('payment response: ' + pm.response.text().slice(0, 800));",auth=True)
c={'info':{'name':'CLS-3676 pp1 deposit through the gateway','schema':'https://schema.getpostman.com/json/collection/v2.1.0/collection.json'},
   'item':[ptok,bal('before'),deposit,bal('after')],
   'variable':[{'key':'baseUrl','value':'https://gateway.preprod-1.octopodev.com'},{'key':'depositAmount','value':'10'},{'key':'access_token','value':''}]}
json.dump(c,open('CLS-3676.pp1-deposit.postman_collection.json','w'),indent=2)
