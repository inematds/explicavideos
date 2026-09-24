import json,urllib.request,urllib.error,sys,time
from pathlib import Path
cfg={}
for line in (Path.home()/'projetos/openpcbotv2/.env').read_text().splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1);cfg[k.strip()]=v.strip().strip('\"\'')
def get(path):
 req=urllib.request.Request('https://api.heygen.com'+path,headers={'X-Api-Key':cfg['HEYGEN_API_KEY']})
 for attempt in range(3):
  try:
   with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
  except urllib.error.HTTPError as e:
   if e.code not in [429,500,502,503,504]:return {'status':e.code,'error':'HTTP error'}
  except (TimeoutError,urllib.error.URLError,ConnectionError):pass
  if attempt<2:time.sleep(5*(attempt+1))
 return {'status':'unavailable','error':'Read-only status temporarily unavailable'}
