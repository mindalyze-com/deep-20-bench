"""Read-only public-site SEO crawl. Writes evidence beside this script, HTML to /tmp."""
from __future__ import annotations
import concurrent.futures as futures
import csv
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, unquote, urldefrag
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CACHE = Path(tempfile.mkdtemp(prefix='deep20-seo-20260905-'))
BASE = 'https://deep20bench.com/'

class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.meta=defaultdict(list); self.links=[]; self.assets=[]; self.ids=[]
        self.titles=[]; self.headings=[]; self.jsonld=[]; self.text=[]; self.main=[]; self.images=[]
        self.scripts=[]; self.lang=''; self.current_heading=None; self.current_title=None; self.current_script=None
        self.feed(html)
    def handle_starttag(self, tag, pairs):
        a=dict(pairs)
        if tag not in ('meta','link','img','br','hr','input','source','wbr','area','base','embed','param','track','col'):
            self.stack.append(tag)
        if tag=='html': self.lang=a.get('lang','')
        if a.get('id'): self.ids.append(a['id'])
        if tag=='meta': self.meta[(a.get('name') or a.get('property') or '').lower()].append(a.get('content',''))
        if tag=='link':
            if 'canonical' in a.get('rel','').split(): self.meta['canonical'].append(a.get('href',''))
            if any(x in a.get('rel','').split() for x in ('stylesheet','modulepreload','preload','icon')): self.assets.append(a.get('href',''))
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='img': self.images.append(a); self.assets.append(a.get('src',''))
        if tag=='script':
            self.current_script=[a.get('type',''),[]]
            if a.get('src'): self.assets.append(a['src']); self.scripts.append(a['src'])
        if tag=='title': self.current_title=[]
        if re.fullmatch('h[1-6]',tag): self.current_heading=[tag,[]]
    def handle_endtag(self, tag):
        if tag=='title' and self.current_title is not None:
            self.titles.append(' '.join(''.join(self.current_title).split())); self.current_title=None
        if self.current_heading is not None and tag==self.current_heading[0]:
            self.headings.append([tag,' '.join(''.join(self.current_heading[1]).split())]); self.current_heading=None
        if tag=='script' and self.current_script:
            if self.current_script[0]=='application/ld+json':
                raw=''.join(self.current_script[1])
                try: self.jsonld.append(json.loads(raw))
                except ValueError: self.jsonld.append({'parse_error':True})
            self.current_script=None
        if tag in self.stack: self.stack=self.stack[:len(self.stack)-1-self.stack[::-1].index(tag)]
    def handle_data(self, data):
        if self.current_title is not None: self.current_title.append(data)
        if self.current_heading is not None: self.current_heading[1].append(data)
        if self.current_script is not None: self.current_script[1].append(data)
        if 'body' in self.stack and not any(x in self.stack for x in ('script','style','noscript')):
            self.text.extend(data.split())
            if 'main' in self.stack: self.main.extend(data.split())

def fetch(url):
    name=hashlib.sha256(url.encode()).hexdigest()[:24]
    body=CACHE/(name+'.body'); headers=CACHE/(name+'.headers')
    proc=subprocess.run(['curl','--silent','--show-error','--location','--max-redirs','8','--compressed','--max-time','35','--dump-header',str(headers),'--output',str(body),'--write-out','%{json}',url],capture_output=True,text=True)
    if proc.returncode: return {'url':url,'error':proc.stderr.strip()},b''
    meta=json.loads(proc.stdout)
    raw=headers.read_text(errors='replace')
    chain=[]
    for block in re.split(r'\r?\n\r?\n',raw):
        lines=block.strip().splitlines()
        if not lines or not lines[0].startswith('HTTP/'): continue
        h={}
        for line in lines[1:]:
            if ':' in line:
                k,v=line.split(':',1); h[k.lower()]=v.strip()
        chain.append({'status':int(lines[0].split()[1]),'headers':{k:v for k,v in h.items() if k in ('location','content-type','x-robots-tag','cache-control','last-modified','content-encoding','content-length')}})
    data=body.read_bytes()
    return {'url':url,'status':meta['http_code'],'final_url':meta['url_effective'],'redirects':meta['num_redirects'],'seconds':round(meta['time_total'],3),'wire_bytes':meta['size_download'],'body_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'chain':chain,'cache_file':str(body)},data

def parse_record(url,data,response=None):
    p=Page(data.decode('utf-8',errors='replace'))
    r=dict(response or {'url':url,'body_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    r.update(title=p.titles,description=p.meta['description'],canonical=p.meta['canonical'],robots=p.meta['robots'],lang=p.lang,h1=[v for k,v in p.headings if k=='h1'],headings=p.headings,word_count=len(p.text),main_word_count=len(p.main),jsonld=p.jsonld,meta=dict(p.meta),image_count=len(p.images),images_without_alt=sum('alt' not in im for im in p.images),duplicate_ids=[x for x,n in Counter(p.ids).items() if n>1],scripts=p.scripts)
    return r,p

def route(url):
    path=unquote(urlsplit(url).path)
    if path.endswith('/index.html'): path=path[:-10]
    return path

def group(path):
    if '/episodes/' in path: return 'episode'
    if '/subjects/' in path: return 'subject'
    if '/runs/' in path: return 'run'
    return 'editorial'

def check_set(records,parsed,sitemap):
    issues=[]; by_url={r['url']:r for r in records}; graph={}; assets=set(); externals=set(); page_links=set()
    for r in records:
        u=r['url']; p=parsed[u]; defects=[]
        if r.get('status',200)!=200: defects.append('http_status')
        if len(r['title'])!=1 or not r['title'][0]: defects.append('title')
        if len(r['description'])!=1 or not r['description'][0]: defects.append('description')
        if r['canonical']!=[u]: defects.append('canonical')
        if len(r['h1'])!=1: defects.append('h1')
        if r['lang']!='en': defects.append('lang')
        if 'noindex' in ','.join(r['robots']).lower(): defects.append('noindex')
        if any('noindex' in h['headers'].get('x-robots-tag','').lower() for h in r.get('chain',[])): defects.append('x_robots_noindex')
        if r['duplicate_ids']: defects.append('duplicate_ids')
        if any(n.get('parse_error') for n in r['jsonld'] if isinstance(n,dict)): defects.append('invalid_jsonld')
        if defects: issues.append({'url':u,'issues':defects})
        destinations=set()
        for link in p.links:
            full=urljoin(u,link); target,frag=urldefrag(full); sp=urlsplit(full)
            if sp.scheme not in ('http','https'): continue
            if sp.netloc=='deep20bench.com':
                page_links.add(target)
                if target in parsed:
                    destinations.add(target)
                    if frag and unquote(frag) not in parsed[target].ids: issues.append({'url':u,'broken_fragment':full})
            elif group(route(u))=='editorial': externals.add(target)
        graph[u]=destinations
        assets.update(urljoin(u,x) for x in p.assets if x)
    depth={BASE:0}; q=deque([BASE])
    while q:
        u=q.popleft()
        for v in graph.get(u,()):
            if v not in depth: depth[v]=depth[u]+1; q.append(v)
    duplicates={}
    for field in ('title','description','h1'):
        groups=defaultdict(list)
        for r in records: groups[tuple(r[field])].append(r['url'])
        duplicates[field]=[{'value':list(v),'urls':us} for v,us in groups.items() if len(us)>1]
    return {'pages':len(records),'page_types':dict(Counter(group(route(r['url'])) for r in records)),'issues':issues,'duplicates':duplicates,'unreachable':sorted(set(sitemap)-set(depth)),'depth_counts':dict(Counter(depth.values())),'depths':depth,'assets':sorted(assets),'editorial_external_links':sorted(externals),'internal_links':sorted(page_links)}

def main():
    evidence={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'cache_directory':str(CACHE)}
    sm_meta,sm=fetch(BASE+'sitemap.xml'); evidence['sitemap_response']=sm_meta
    urls=[n.text for n in ET.fromstring(sm).findall('{*}url/{*}loc')]
    evidence['sitemap_lastmods']=sorted(set(n.text for n in ET.fromstring(sm).findall('{*}url/{*}lastmod')))
    live=[]; parsed={}
    with futures.ThreadPoolExecutor(max_workers=4) as pool:
        for response,data in pool.map(fetch,urls):
            if not data: live.append(response); continue
            r,p=parse_record(response['url'],data,response); live.append(r); parsed[r['url']]=p
            file=ROOT/'docs'/route(r['url']).lstrip('/')/'index.html'
            r['matches_local']=file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest()==r['sha256']
    valid=[r for r in live if r['url'] in parsed]
    evidence['live']=check_set(valid,parsed,urls)
    evidence['live']['fetch_errors']=[r for r in live if r['url'] not in parsed]
    evidence['live']['matches_local_count']=sum(r.get('matches_local',False) for r in live)
    local_urls=[n.text for n in ET.parse(ROOT/'docs/sitemap.xml').findall('{*}url/{*}loc')]
    local=[]; lp={}
    for u in local_urls:
        data=(ROOT/'docs'/route(u).lstrip('/')/'index.html').read_bytes()
        r,p=parse_record(u,data); local.append(r); lp[u]=p
    evidence['local']=check_set(local,lp,local_urls)
    evidence['local_only_urls']=sorted(set(local_urls)-set(urls))
    evidence['live_only_urls']=sorted(set(urls)-set(local_urls))
    episode_files=sorted((ROOT/'docs/runs').glob('*/subjects/*/episodes/*/index.html'))
    evidence['local_episode_policy']={'count':len(episode_files),'without_noindex':[str(f.relative_to(ROOT/'docs')) for f in episode_files if 'noindex' not in ','.join(Page(f.read_text()).meta['robots'])]}
    run=next(u for u in urls if group(route(u))=='run'); subject=next(u for u in urls if group(route(u))=='subject')
    episode=next(urljoin(subject,x) for x in parsed[subject].links if '/episodes/' in x)
    checks=[BASE+'robots.txt','http://deep20bench.com/','http://www.deep20bench.com/','https://www.deep20bench.com/',BASE+'results',BASE+'index.html',BASE+'story/',BASE+'seo-audit-missing-20260905/',episode,BASE+'data/routes.json',BASE+'data/manifest.json',BASE+'data/app-build.json',BASE+'data/deep20bench-v9.schema.json',BASE+'data/deep20bench-v9.json',BASE+'data/leaderboard.csv']
    old='https://mindalyze-com.github.io/deep-20-bench/'
    checks += [old+x for x in ('','results/',route(run).lstrip('/'),route(subject).lstrip('/'),route(episode).lstrip('/'),'data/deep20bench-v9.json','data/deep20bench-v9.schema.json')]
    checks += evidence['live']['assets']
    evidence['endpoints']=[]
    with futures.ThreadPoolExecutor(max_workers=4) as pool:
        for response,data in pool.map(fetch,dict.fromkeys(checks)):
            if 'html' in str(response.get('chain',[])) and data:
                p=Page(data.decode(errors='replace')); response.update(title=p.titles,canonical=p.meta['canonical'],robots=p.meta['robots'])
            if response['url'].endswith('robots.txt'): response['text']=data.decode(errors='replace')
            evidence['endpoints'].append(response)
    evidence['editorial_external_responses']=[]
    with futures.ThreadPoolExecutor(max_workers=3) as pool:
        for response,data in pool.map(fetch,evidence['live']['editorial_external_links']):
            evidence['editorial_external_responses'].append(response)
    (OUT/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    (OUT/'live-pages.json').write_text(json.dumps(live,indent=2)+'\n')
    (OUT/'local-pages.json').write_text(json.dumps(local,indent=2)+'\n')
    for name,records in [('live',live),('local',local)]:
        with (OUT/(name+'-pages.csv')).open('w',newline='') as f:
            fields=['url','status','type','title','title_length','description','description_length','h1','canonical','robots','body_bytes','word_count','main_word_count','depth']
            writer=csv.DictWriter(f,fields); writer.writeheader()
            for r in records:
                row={k:r.get(k,'') for k in fields}
                for k in ('title','description','h1','canonical','robots'): row[k]=' | '.join(r.get(k,[]))
                row.update(type=group(route(r['url'])),title_length=len(row['title']),description_length=len(row['description']),depth=evidence[name]['depths'].get(r['url']))
                writer.writerow(row)
    print(json.dumps({k:{kk:vv for kk,vv in evidence[k].items() if kk in ('pages','page_types','issues','unreachable','depth_counts','matches_local_count','fetch_errors')} for k in ('live','local')},indent=2))
    print('Evidence: '+str(OUT/'evidence.json'))

if __name__=='__main__': main()
