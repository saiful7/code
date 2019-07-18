years=[2015,2016,2017,2018]
months=[1,2,3,4,5,6,7,8,9,10,11,12]
import requests
from bs4 import BeautifulSoup as bsp
a2m=lambda ahi:{
'game':ahi.parent.h2.text,
'time':ahi.previousSibling.previousSibling.text,
'url':ahi['href'],
'tvalue': ahi.parent.parent.h3.text
}
def saveobjs(objs,at="./export.csv"):
	'''db handler, csv for now'''
	with open(at,'a') as f:
		f.write('\n'.join([','.join(map(str,x)) for x in objs])+'\n')
	return 1
def scrapeHomePage():
	rh=requests.get('https://sattakingdarbar.com/')
	sp=bsp(rh.text,'html.parser')
	ahrefs=filter(lambda a:a.text=="Record Chart",sp.findAll('a'))
	temps={d['url']:[d['game'],d['time'],d['tvalue']] for d in map(a2m,ahrefs)}
	return temps

def urlpath(url):
	import sys
	if sys.version_info[0] < 3:
		import urllib
		return urllib.splitquery(url)[0]
	else:
		from urllib.parse import urlparse,urlunparse
		return urlunparse(list(urlparse(url))[:3]+['']*3)
		
def scrapeThisPage(url):
	objs=[]
	hitu=urlpath(url)+"?month={}&year={}"
	for y in years:
		for m in months:
			ri=requests.get(hitu.format(m,y))
			spi=bsp(ri.text,'html.parser')
			dates=spi.findAll('td',attrs={'class':'day'})
			vals=spi.findAll('td',attrs={'class':'number'})
			names=spi.findAll('th',attrs={'class':'name'})
			ln,ld=len(names),len(dates)
			for i,iv in enumerate(vals):
				objs.append([dates[i//ln].text,m,y,names[i%ln].text,iv.text,''])
	return objs

def scrapAll():
	allobjs=[]
	alllinks=scrapeHomePage()
	for u in alllinks:
		allobjs+=scrapeThisPage(u)
		if len(allobjs)>500 and saveobjs(allobjs):allobjs=[]
scrapAll()