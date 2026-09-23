import json,time,sys,urllib.request,subprocess
from pathlib import Path
from settings import ROOT,CFG,PROJECT
from heygen_read import get
root=ROOT;out=root/'verification/blocos-downloads.json'
jobs=json.loads(out.read_text()) if out.exists() else {}
for attempt in range(720):
 blocks=json.loads((root/'blocos/manifest.json').read_text())
 for b in blocks:
  if not b.get('id'):continue
  key=f"{b['language']}-b{b['part']:02d}"
  j=jobs.setdefault(key,{'id':b['id'],'title':b['title']})
  if j.get('downloaded') or j.get('status')=='failed':continue
  try:
   r=get('/v3/videos/'+j['id']);d=r.get('data',r)
   if 'status' not in d:continue
   old=j.get('status');j['status']=d['status']
   if j['status']=='failed':j['failure_message']=d.get('failure_message')
   if j['status']=='completed':
    dest=root/'assets'/f'nei-{key}.mp4'
    if not dest.exists():
     temp=dest.with_suffix('.part.mp4')
     with urllib.request.urlopen(d['video_url'],timeout=300) as src,temp.open('wb') as f:
      while chunk:=src.read(1024*1024):f.write(chunk)
     temp.replace(dest)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type','-of','json',str(dest)]))
    duration=float(probe['format']['duration']);assert duration>60 and any(s['codec_type']=='audio' for s in probe['streams'])
    j.update(downloaded=True,file=str(dest),duration=duration)
   if old!=j['status'] or j.get('downloaded'):print(key,j['status'],j.get('downloaded',False),flush=True)
   j.pop('last_error',None)
  except Exception as e:j['last_error']=type(e).__name__;print(key,type(e).__name__,flush=True)
  tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(jobs,ensure_ascii=False,indent=2));tmp.replace(out)
 if len(jobs)==len(blocks) and all(j.get('downloaded') or j.get('status')=='failed' for j in jobs.values()):break
 time.sleep(60)
