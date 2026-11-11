import json,sys
d=json.load(open(''+__import__('os').path.join(__import__('os').path.dirname(__file__),'../../data/events.json')+''))
keep=['id','date','time','title','venue','address','cat','price','priceMin','soldOut','few','note','url','moreShows','shows','addedAt','home','away','league']
ev=[{k:e[k] for k in keep if e.get(k) not in (None,'',False,[])} for e in d['events']]
t=open(__import__('os').path.join(__import__('os').path.dirname(__file__),'app.template.html')).read()
t=t.replace('/*DATA*/',json.dumps(ev,ensure_ascii=False,separators=(',',':'))).replace('/*UPDATED*/',json.dumps(d['meta']['updatedAt']))
open(__import__('os').path.join(__import__('os').path.dirname(__file__),'kaskjerda-glass.html'),'w').write(t)
print(len(t))
