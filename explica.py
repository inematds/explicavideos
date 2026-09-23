#!/usr/bin/env python3
"""Config-driven production commands; all media stays outside this repository."""
from pathlib import Path
import argparse,os,subprocess,json,sys
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--config',default=str(ROOT/'examples/oswork.json'));p.add_argument('command',choices=['prepare','start','status','preview']);a=p.parse_args()
c=Path(a.config).resolve();cfg=json.loads(c.read_text());env={**os.environ,'EXPLICAVIDEOS_CONFIG':str(c)}
def run(script,*args):subprocess.run([sys.executable,str(ROOT/'engine'/script),*args],env=env,check=True)
if a.command=='prepare':run('prepare.py');run('build_scene_templates.py')
elif a.command=='preview':run('build_final_block.py','pt','1','--preview')
elif a.command=='start':
 if subprocess.run(['xdpyinfo','-display',':99'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  subprocess.run(['systemd-run','--user','--collect','--unit=explicavideos-display','/usr/bin/Xvfb',':99','-screen','0','1920x1080x24','-nolisten','tcp'],check=True)
  import time
  for _ in range(20):
   if subprocess.run(['xdpyinfo','-display',':99'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
   time.sleep(.25)
  else:raise RuntimeError('Virtual display did not start')
 for stage,script in [('submit','submit.py'),('monitor','monitor.py'),('render','produce_blocks.py'),('assemble','wait_assembly.py'),('publish','wait_publication.py')]:
  unit=f"explica-{cfg['id']}-{stage}"
  if subprocess.run(['systemctl','--user','is-active','--quiet',unit]).returncode==0:continue
  subprocess.run(['systemd-run','--user','--collect','--unit='+unit,'--property=WorkingDirectory='+str(ROOT),'--setenv=EXPLICAVIDEOS_CONFIG='+str(c),sys.executable,str(ROOT/'engine'/script)],check=True)
elif a.command=='status':
 out=Path(cfg['output']);result={}
 for name,file in [('submitted','blocos/manifest.json'),('downloads','verification/blocos-downloads.json'),('production','verification/production.json'),('publication','verification/publication.json'),('notification','verification/telegram-final.json')]:
  f=out/file
  if not f.exists():result[name]='not started';continue
  value=json.loads(f.read_text())
  if name in ['submitted','downloads','production']:
   values=value if isinstance(value,list) else value.values();counts={}
   for item in values:status='downloaded' if item.get('downloaded') else item.get('status','unknown');counts[status]=counts.get(status,0)+1
   result[name]=counts
  else:result[name]=value
 print(json.dumps(result,ensure_ascii=False,indent=2))
