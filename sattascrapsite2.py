from flask import request,Flask,Response,render_template,redirect,send_file,make_response
app = Flask(__name__)
DBLOCATION='./sattasite.db'
ADMINPASS="changeme@line4"
@app.errorhandler(404)
def page_not_found(e):
    return 'Sorry, nothing at this URL.bhag yaha se.', 404

def check_auth(username, password):
    return username == 'admin' and password == ADMINPASS
def authenticate():
    return Response('You have to login with proper credentials for this url', 401,{'WWW-Authenticate': 'Basic realm="Login Required"'})

from functools import wraps
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

from datetime import datetime,timedelta
from pytz import timezone
import sqlite3
def getstor():
    conn = sqlite3.connect('sattasite.db')
    c = conn.cursor()
    try:x=list(c.execute('SELECT key,value from stor'))
    except:
        x=list(c.execute('CREATE TABLE stor(key text,value text)'))
        x=list(c.execute('SELECT key,value from stor'))
    c.close()
    conn.commit()
    conn.close()
    return dict(x)
def setstor(kvps):
    if type(kvps)==type({}):kvps=list(kvps.items())
    old=getstor()
    conn = sqlite3.connect('sattasite.db')
    c = conn.cursor()
    c.executemany('delete from stor where key like ?',[[k] for k,v in kvps if k in old])
    c.executemany('insert into stor values(?,?)', kvps)
    c.close()
    conn.commit()
    conn.close()
    return "stored"
def tb2hm(ct):
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    c.execute('SELECT cthmpgname FROM ctnm where ctblename like ?', [ct])
    rt=c.fetchone()
    if rt == None:
        return 'skip'
    conn.commit()
    #c.close()
    conn.close()    
    return rt[0]
def hm2tb(ct):
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    c.execute('SELECT ctblename FROM ctnm where cthmpgname like ?', [ct])
    rt=c.fetchone()
    #print('tb2hm',ct,'fetch',rt)
    conn.commit()
    #c.close()
    conn.close()    
    return rt[0]
def showHome(dd,mm,yy):
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    for row in c.execute('SELECT * FROM data WHERE mm=? and yy=? and dd=?',[mm,yy,dd]):
        #print("row",row)
        row=list(row)
        row[3]=tb2hm(row[3])
        if row[3] == 'skip':
            continue
        row.append(__import__('urllib').parse.urlencode({"month":mm,"year":yy,"city":row[3]}))
        yield row
    conn.commit()
    conn.close()
    
@app.route('/')
def home():
    now=datetime.now(timezone('Asia/Kolkata'))
    today=now.strftime('%d %m %Y').split(),now.strftime('%B %d, %Y')
    yester=now-timedelta(days=1)
    yester=yester.strftime('%d %m %Y').split(),yester.strftime('%B %d, %Y')
    return render_template("home.html",dataT=showHome(*today[0]),today=today[1],yest=yester[1],dataY=showHome(*yester[0]),showFH=showFor(1))

@app.route('/showFor')
def showFor(hide=0):
    tmm,tyy=datetime.now(timezone('Asia/Kolkata')).strftime('%m %Y').split()
    mm,yy,city=request.args.get('month',tmm),request.args.get('year',tyy),request.args.get('city','')
    if hide==0:hide=request.args.get('hide','no')
    if hide==1:hide=''
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    header=["DATE"]
    if not city:city=list(x[0] for x in c.execute('SELECT cthmpgname FROM ctnm where isspecial="1"'))[0]
    spcities=list(x[0] for x in c.execute('SELECT ctblename FROM ctnm where isspecial="1"'))
    spcities=sorted(spcities,key=lambda k:dict(zip("DSWR FRBD GZBD GALI".split(),range(4))).get(k,-1))#tries to maintain the order
    header+=spcities
    cols=[]
    for spcty in spcities:
        rows=list(c.execute('SELECT dd,count FROM data WHERE mm=? and yy=? and cTname like ?',[mm,yy,spcty]))
        cols.append(sorted(rows,key=lambda dc:int(dc[0])))
    cityT=hm2tb(city)
    if cityT not in spcities:
        header.append(cityT)
        rows=list(c.execute('SELECT dd,count FROM data WHERE mm=? and yy=? and cTname like ?',[mm,yy,cityT]))
        cols.append(sorted(rows,key=lambda dc:int(dc[0])))
    #cols=list([es[0][0]]+[e[1] for e in es] for es in zip(*cols))
    cols=list([sorted([e[0] for e in es])[0]]+[e[1] for e in es] for es in __import__('itertools').zip_longest(*cols,fillvalue=['??']*2))
    cols=sorted(cols,key=lambda x:int(x[0]))
    #cols=[header]+cols
    conn.commit()
    conn.close()
    
    pmm,pyy=int(mm)-1,yy
    if pmm==0:pyy,pmm=str(int(pyy)-1),12
    pmm="{:02}".format(pmm)
    nmm,nyy=int(mm)+1,yy
    if nmm==13:nyy,nmm=str(int(nyy)+1),1
    nmm="{:02}".format(nmm)
    prevU="/showFor?"+__import__('urllib').parse.urlencode({"month":pmm,"year":pyy,"city":city,"hide":hide})
    nextU="/showFor?"+__import__('urllib').parse.urlencode({"month":nmm,"year":nyy,"city":city,"hide":hide})
    prevS,nextS=datetime(*map(int,[pyy,pmm,1])).strftime("%b %Y"),datetime(*map(int,[nyy,nmm,1])).strftime("%b %Y")
    mmS=datetime(*map(int,[yy,mm,1])).strftime("%B")
    if int(nyy+nmm)>int(tyy+tmm):nextU=""
    if int(pyy+pmm)<201501:prevU=""
    nav={"prev_url":prevU,"prev_str":"< {}".format(prevS),"next_url":nextU,"next_str":"{} >".format(nextS)}
    return render_template("showFor.html",hide=request.path=="/",data=cols,header=header,mm=mm,mmS=mmS,yy=yy,city=hide and city,cityT=cityT,nav=nav,search=searchMMDD())

@app.route('/subscribe',methods=['POST'])
def subscribePost():
    if request.method=='POST':
        import time
        name,phno,time,ip=request.form.get("username","-"),request.form.get("phno","-"),time.time(),request.remote_addr
        with open("subscribers.csv","a") as f:
            f.write("{},{},{},{}".format(name,phno,time,ip))
        return redirect("/",code=302)
@app.route('/subscribe',methods=['GET'])
@requires_auth
def subscribeGET():
    if request.method=='GET':
        import pandas as pd
        df=pd.read_csv("subscribers.csv",header=None,names="Name PhoneNo Time I/P".split())
        df['Time']=df.Time.astype("int64")
        return df.to_html()


@app.route('/search',methods=['GET','POST'])
def searchMMDD():
    #autoupdate db-scrap
    warn,updiff="Updated {} seconds ago.",''
    lastupdateToday=getstor().get('lastupdateToday',1)
    if not lastupdateToday:
        updateHomePage()
    else:
        updiff=int(__import__('time').time())-int(lastupdateToday)
        if updiff<60*60*1:#less than 1hr
            pass
        elif updiff<60*60*23 and updiff>60*60*1:#more than 1hr but less than 23hr
            updateHomePage()
            updiff=1
        elif updiff<60*60*24*29:#less than 1month
            #update this+lastmonth+today
            tmm,tyy=datetime.now(timezone('Asia/Kolkata')).strftime('%m %Y').split()
            updatePast(dcity="all",dmm=tmm,dyy=tyy)
            tmm,tyy=("{:02}".format(int(tmm)-1),tyy) if tmm!='01' else ('12',str(int(tyy)-1))
            updatePast(dcity="all",dmm=tmm,dyy=tyy)
            updateHomePage()
            updiff=1
        else:
            warn="Warning: SiteData not autoupdated since last month or more ({}secs). Kindly follow admin guide to update data manually."
    warn=warn.format(updiff)
    if request.method=='POST':
        cty=__import__('urllib').parse.parse_qs(request.referrer).get('city',[''])[0]
        if not cty:
            conn = sqlite3.connect(DBLOCATION)
            c = conn.cursor()
            cty=list(x[0] for x in c.execute('SELECT cthmpgname FROM ctnm where isspecial="1"'))[0]
            conn.commit()
            conn.close()
        mm,yy=request.form.get('month','12'),request.form.get('year','2018')
        return redirect("/showFor?"+(__import__('urllib').parse.urlencode({"month":mm,"year":yy,"city":cty,"hide":""})), code=302)
    months = [datetime(2018, i, i).strftime('%d %B').split() for i in range(1,13)]
    years = list(range(2015,datetime.now(timezone('Asia/Kolkata')).year+1))[::-1]
    return render_template("search.html",months=months,years=years,msg=warn)

def urlpath(url):
    import sys
    if sys.version_info[0] < 3:
        import urllib
        return urllib.splitquery(url)[0]
    else:
        from urllib.parse import urlparse,urlunparse
        return urlunparse(list(urlparse(url))[:3]+['']*3)
def scrapTodayYest():
    import requests
    from bs4 import BeautifulSoup as bsp
    a2m=lambda ahi:{
    'game':ahi.parent.h2.text,
    'time':ahi.previousSibling.previousSibling.text,
    'url':ahi['href'],
    'tvalue': ahi.parent.parent.h3.text
    }
    rh=requests.get('https://satta-king-fast.com/')
    sp=bsp(rh.text,'html.parser')
    ahrefs=filter(lambda a:a.text=="Record Chart",sp.findAll('a'))
    temps=[[d['url'],d['game'],d['time'],d['tvalue']] for d in map(a2m,ahrefs)]
    rt=dict()
    for url,game,time,tv in temps:
        rt[game]=rt.get(game,{'url':urlpath(url),'dt-val-ts':[]})
        rt[game]['dt-val-ts'].append([tv,time])
    dates=[t.findAll('h1')[0].text.split()[-2].replace(',','') for t in sp.findAll('table')[:2]]
    for game in rt:
        rt[game]['dt-val-ts']=list(map(lambda xy:[xy[0]]+xy[1],zip(dates,rt[game]['dt-val-ts'])))
    return rt
@app.route('/updateToday')
def updateHomePage():
    temps=scrapTodayYest()
    #turn temps to rows
    rows=[]
    mmtoday,yytoday=datetime.now(timezone('Asia/Kolkata')).strftime('%m %Y').split()
    for cT,V in temps.items():
        try:cT=hm2tb(cT)
        except TypeError as e:
            if str(e)=="'NoneType' object is not subscriptable":
                #do good
                resetCityListing(confirm="yes")
            cT=hm2tb(cT)
        for dt,val,up in V['dt-val-ts']:
            rows.append([dt,mmtoday,yytoday,cT,val,up])
    #print(rows)
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    #delete overlapping rows: dd,mm,yy,ciTy
    #for dd,mm,yy,ct,val,up in rows:
    #    c.execute('delete from data where dd=? and mm=? and yy=? and cTname like ?',[dd,mm,yy,ct])
    c.executemany('delete from data where dd=? and mm=? and yy=? and cTname like ?',[[dd,mm,yy,ct] for dd,mm,yy,ct,val,up in rows])
    #insert these rows
    c.executemany('INSERT INTO data VALUES (?,?,?,?,?,?)',rows)
    #c.close()
    conn.commit()
    conn.close()
    setstor({"lastupdateToday":int(__import__('time').time())})
    return "Updated"
@app.route('/updateThen')
def updatePast(dmm=None,dcity=None,dyy=None):
    mm,yy,city=(dmm or request.args['month']),(dyy or request.args['year']),(dcity or request.args['city'])
    if city=="all":
        conn = sqlite3.connect(DBLOCATION)
        c = conn.cursor()
        cities=list(x[0] for x in c.execute('SELECT cthmpgname FROM ctnm'))
        c.close()
        conn.close()
        for citi in cities:updatePast(dcity=citi,dmm=dmm,dyy=dyy)
        return "ALLSUCCESS"
    if mm=="all":
        months=["{:02}".format(m) for m in range(1,13)]
        for m in months:updatePast(dmm=m,dcity=city,dyy=dyy)
        return "ALLSUCCESS"
    
    dateobj={"month":mm,"year":yy}
    #find cityurl
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    c.execute('SELECT cturl FROM ctnm where cthmpgname like ?', [city])
    rt=c.fetchone()
    print(rt)
    c.close()
    #conn.commit()
    conn.close()
    if not rt:return resetCityListing("yes") and updatePast(mm,city,yy)
    cityurl=rt[0]
    cityurl=cityurl+"?"+__import__('urllib').parse.urlencode({"month":mm,"year":yy})
    #find special ciTynames
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    specials=c.execute('SELECT ctblename FROM ctnm where isspecial="1"')
    specials=[x[0] for x in specials]
    c.close()
    #conn.commit()
    conn.close()
    #scrap cityurl
    import requests
    from bs4 import BeautifulSoup as bsp
    r=requests.get(cityurl)
    spi=bsp(r.text,'html.parser')
    dates=spi.findAll('td',attrs={'class':'day'})
    vals=spi.findAll('td',attrs={'class':'number'})
    names=spi.findAll('th',attrs={'class':'name'})
    notspecial=names[-1].text if len(names)>len(specials) else ''
    specialcity='' if notspecial else hm2tb(city)
    ln,ld,objs=len(names),len(dates),[]
    for i,iv in enumerate(vals):
        if notspecial:
            if names[i%ln].text==notspecial:
                objs.append([dates[i//ln].text,mm,yy,names[i%ln].text,iv.text,''])
        else:
            if names[i%ln].text==specialcity:
                objs.append([dates[i//ln].text,mm,yy,names[i%ln].text,iv.text,''])
    rows=objs
    #return str(rows)
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    #delete overlapping rows: dd,mm,yy,ciTy
    c.executemany('delete from data where dd=? and mm=? and yy=? and cTname like ?',[[dd,mm,yy,ct] for dd,mm,yy,ct,val,up in rows])
    ##insert these rows
    c.executemany('INSERT INTO data VALUES (?,?,?,?,?,?)',rows)
    c.close()
    conn.commit()
    conn.close()
    return "Success"

@app.route('/resetCityList')
def resetCityListing(confirm=""):
    if request.args.get('confirm',confirm)!="yes":return "As this one truncates scrapped city meta data:GOTO /resetCityList?confirm=yes"
    temps=scrapTodayYest()
    ctdd=[]
    specials={"DESAWAR - DS":"DSWR","FARIDABAD - FB":"FRBD","GHAZIABAD - GB":"GZBD","GALI - GL":"GALI"}
    for t in temps:
        ctdd.append([temps[t]['url'],t,(t[:-4].strip().title() if t not in specials else specials[t]),t in specials])
    corrections={'LUCKY HARUF - LH':'Lucky Huruf',"GALI No.1 - G1":"Gali No. 1"}
    for i in range(len(ctdd)):
        if ctdd[i][1] in corrections:
            ctdd[i][2]=corrections[ctdd[i][1]]
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    #todo:dangerous to drop all, instead only delete those which will be replaced by ctdd#DONE
    try:
        #c.execute("DROP TABLE ctnm")
        c.executemany("DELETE from ctnm where cthmpgname=? or ctblename=?",[[cthm,cttb] for _1,cthm,cttb,_2 in ctdd])
    except:
        pass
    #c.execute('''CREATE TABLE ctnm(cturl text, cthmpgname text, ctblename text, isspecial text)''')
    c.executemany('INSERT INTO ctnm VALUES (?,?,?,?)', ctdd)
    c.close()
    conn.commit()
    conn.close()
    return "resetED. GLHF."

@app.route('/initData')
@requires_auth
def initData():
    if request.args.get('confirm','')!="yes":return "As this one truncates scrapped data:GOTO /initData?confirm=yes"
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    try:c.execute("DROP TABLE data")
    except:pass
    c.execute('''CREATE TABLE data(dd text,mm text,yy text,cTname text,count text,upTs text)''')
    #c.execute('''CREATE TABLE ctnm(cturl text, cthmpgname text, ctblename text, isspecial text)''')
    c.close()
    conn.commit()
    conn.close()
    return "Done. All db.data empty now. :("

@app.route('/downloaddb')
@requires_auth
def downdb():
    return send_file(DBLOCATION, as_attachment=True)

@app.route('/uploaddb',methods=['GET','POST'])
@requires_auth
def updb():
    if request.method=="GET":
        return '<form method="POST" enctype="multipart/form-data"><input type="file" name="db"><input type="submit">'+request.args.get('msg','')
    if 'db' in request.files and request.files['db'] and request.files['db'].filename.endswith('.db'):
        request.files['db'].save(DBLOCATION)
        return "Success"
    return redirect("/uploaddb?msg=Retry!")

@app.route('/site-map.xml')
@app.route('/sitemap.xml')
def sm():
    pages=[]
    months = [datetime(2018, i, i).strftime('%d') for i in range(1,13)]
    years = list(range(2015,datetime.now(timezone('Asia/Kolkata')).year+1))[::-1]
    conn = sqlite3.connect(DBLOCATION)
    c = conn.cursor()
    cities=list(x[0] for x in c.execute('SELECT cthmpgname FROM ctnm'))
    conn.commit()
    conn.close()
    for mm in months:
        for yy in years:
            lastmod=datetime(int(yy), int(mm), 1,tzinfo=timezone('Asia/Kolkata'))+timedelta(days=29)
            if datetime.now(timezone('Asia/Kolkata'))<lastmod:lastmod=datetime.now(timezone('Asia/Kolkata'))
            lastmod=lastmod.isoformat()
            for ctyh in cities:
                url="{}showFor?{}".format(request.url_root,__import__('urllib').parse.urlencode({"month":mm,"year":yy,"city":ctyh}))
                pages.append([url,lastmod])
    sitemap_xml = render_template('sitemap_template.xml', pages=pages)
    response= make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"    
    return response

@app.route('/about')
def about():
	 return render_template("about.html")


@app.route('/blog')
def blog():
	 return render_template("blog.html")


@app.route('/blog/Satta-Matka-is-a-Kind-of-Gamble')
def article1():
	 return render_template("article1.html")


@app.route('/blog/Satta-Matka-2019-is-very-Popular')
def article2():
	 return render_template("article2.html")

@app.route('/blog/Satta-Matka-Satrted-in-India')
def article3():
	 return render_template("article3.html")

@app.route('/knowledge')
def knowledge():
	 return render_template("knowledge.html")

@app.route('/knowledge-world')
def knowledgeword():
	 return render_template("knowledge-world.html")


@app.route('/privacypolicy')
def pravcypolicy():
	 return render_template("pravcypolicy.html")

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=80, debug=True,threaded=True)

