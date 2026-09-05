"""Check remaining linked public targets and recursively referenced static assets."""
import concurrent.futures as futures
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, unquote
spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
e=json.loads((a.OUT/'evidence.json').read_text()); pages=json.loads((a.OUT/'live-pages.json').read_text())
responses={r['url']:r for r in e['endpoints']+pages}
urls=sorted(set(e['live']['internal_links'])-set(responses))
extra=[]
with futures.ThreadPoolExecutor(max_workers=4) as pool:
 for r,data in pool.map(a.fetch,urls):
  if 'text/html' in str(r.get('chain',[])) and data:
   p=a.Page(data.decode(errors='replace'));r.update(title=p.titles,robots=p.meta['robots'],canonical=p.meta['canonical'],h1=[v for k,v in p.headings if k=='h1'])
  extra.append(r);responses[r['url']]=r
assets=set(e['live']['assets'])
for p in pages: assets.update(p['meta'].get('og:image',[]))
scanned=set();asset_records=[]
while assets-scanned:
 current=sorted(assets-scanned);scanned.update(current)
 missing=[u for u in current if u not in responses]
 with futures.ThreadPoolExecutor(max_workers=4) as pool:
  for r,data in pool.map(a.fetch,missing): responses[r['url']]=r
 for u in current:
  r=responses[u];asset_records.append(r)
  if r.get('status')!=200 or not urlsplit(u).path.endswith(('.js','.css')): continue
  body=Path(r['cache_file']).read_text(errors='replace')
  refs=re.findall(r'''["']((?:\.{0,2}/)?(?:_assets/)?[\w./-]+\.(?:js|css|woff2|webp|svg))["']''',body)
  refs+=re.findall(r'''url\(["']?([^\s)'";]+)["']?\)''',body)
  for ref in refs:
   if ref.startswith('data:'):continue
   target=urljoin(a.BASE if ref.startswith('_assets/') else u,ref)
   if urlsplit(target).netloc=='deep20bench.com':assets.add(target)
local_missing=[]
for u in e['local']['internal_links']:
 path=unquote(urlsplit(u).path).lstrip('/'); f=a.ROOT/'docs'/path
 if not f.is_file() and not (f/'index.html').is_file(): local_missing.append(u)
episodes=[r for r in extra if '/episodes/' in r['url']]
for r in e['endpoints']:
 if r['url'].startswith(a.BASE) and '/episodes/' in r['url']:episodes.append(r)
result={'remaining_internal_target_count':len(extra),'remaining_internal_statuses':dict(Counter(r.get('status','error') for r in extra)),'remaining_internal_failures':[r for r in extra if r.get('status')!=200],'episode_count':len(episodes),'episode_unique_path_count':len({urlsplit(r['url']).path for r in episodes}),'episode_query_variant_count':sum(bool(urlsplit(r['url']).query) for r in episodes),'episode_noindex_count':sum('noindex' in ','.join(r.get('robots',[])) for r in episodes),'assets_count':len(asset_records),'asset_failures':[r for r in asset_records if r.get('status')!=200],'local_missing_link_targets':local_missing,'internal_targets':extra,'assets':asset_records}
(a.OUT/'extended-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('internal_targets','assets')},indent=2))
