import json,subprocess,os,sys,re,time,hashlib
from pathlib import Path
from settings import ROOT,CFG,PROJECT
from heygen_read import get
root=ROOT;path=root/'blocos/manifest.json'
def save(a):
 t=path.with_suffix('.tmp');t.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');t.replace(path)
subprocess.run(['xdpyinfo','-display',':99'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
a=json.loads(path.read_text())
for j in a:
 if j.get('id'):continue
 assert j['status']=='prepared', 'Needs manual reconciliation: '+j['title']
 assert len(Path(j['file']).read_text().strip())<=4500
 assert hashlib.sha256(Path(j['file']).read_bytes()).hexdigest()==j['sha256'], 'Source changed after preparation'
 # Never automatically repeat a submission whose outcome is ambiguous.
 j['status']='submitting';save(a)
 logfile=root/'verification'/f"submit-{j['language']}-{j['part']:02d}.log"
 cmd=['node',str(PROJECT/'engine/heygen-studio.mjs'),'--titulo',j['title'],'--fala-arquivo',j['file'],'--perfil',CFG['profile'],'--template',CFG['template']]
 try:
  with logfile.open('w') as log:
   p=subprocess.run(cmd,env={**os.environ,'DISPLAY':':99'},stdout=log,stderr=subprocess.STDOUT,timeout=300)
 except subprocess.TimeoutExpired:
  ids=re.findall(r'create-v4/([a-f0-9]{32})',logfile.read_text())
  if ids:j['id']=ids[-1]
  j['status']='needs_review';save(a);raise SystemExit('Browser timed out; reconcile existing job before retry')
 raw=logfile.read_text();ids=re.findall(r'create-v4/([a-f0-9]{32})',raw)
 if ids:j['id']=ids[-1];save(a)
 if p.returncode or not ids:
  j['status']='needs_review';save(a);raise SystemExit('Submission needs review: '+j['title'])
 for attempt in range(6):
  response=get('/v3/videos/'+j['id']);d=response.get('data',response)
  if d.get('status') in ['pending','processing','completed']:break
  time.sleep(10)
 else:
  j['status']='needs_review';save(a);raise SystemExit('Unconfirmed status: '+j['title'])
 j['status']=d['status'];save(a);print(j['title'],j['id'],j['status'],flush=True)
print('All blocks submitted',flush=True)
