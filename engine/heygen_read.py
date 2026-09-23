import json,urllib.request,urllib.error,sys
from pathlib import Path
cfg={}
for line in (Path.home()/'projetos/openpcbotv2/.env').read_text().splitlines():
 if '=' in line and not line.lstrip().startswith('#'):
  k,v=line.split('=',1);cfg[k.strip()]=v.strip().strip('\"\'')
def get(path):
 req=urllib.request.Request('https://api.heygen.com'+path,headers={'X-Api-Key':cfg['HEYGEN_API_KEY']})
 try:
  with urllib.request.urlopen(req,timeout=25) as r:return json.load(r)
 except urllib.error.HTTPError as e:return {'status':e.code,'error':e.read().decode()[:600]}
