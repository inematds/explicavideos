"""Resume-safe assembly and rendering of downloaded blocks. Does not submit HeyGen jobs."""
from pathlib import Path
import json,subprocess,os,time,sys
from transcribe_block import transcribe
from build_final_block import build
from settings import ROOT,REPO,CFG,LANGUAGES;STATE=ROOT/'verification/production.json'
ENV={**os.environ,'HYPERFRAMES_BROWSER_PATH':'/home/nmaldaner/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux-arm64/chrome-headless-shell'}
state=json.loads(STATE.read_text()) if STATE.exists() else {}
def save():
 tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(state,ensure_ascii=False,indent=2));tmp.replace(STATE)
def run(cmd,log):
 with log.open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=ENV,check=True)
for attempt in range(720):
 jobs=json.loads((ROOT/'verification/blocos-downloads.json').read_text()) if (ROOT/'verification/blocos-downloads.json').exists() else {}
 for key,j in jobs.items():
  if not j.get('downloaded') or state.get(key,{}).get('status') in ['rendered','failed']:continue
  lang=key[:2];part=int(key[-2:]);s=state.setdefault(key,{})
  try:
   s['status']='transcribing';save();transcribe(key,lang)
   s['status']='assembling';save();project=build(lang,part)
   cli=['npx','--yes','hyperframes@'+CFG['hyperframes']];logs=ROOT/'verification'
   s['status']='checking';save();run(cli+['check',str(project)],logs/f'check-final-{key}.log')
   alignment=json.loads((project/'alignment.json').read_text());points=','.join(str(round((a+b)/2,2)) for a,b in zip(alignment['starts'],alignment['starts'][1:]))
   run(cli+['snapshot',str(project),'--at',points,'--output',str(logs/f'final-{key}')],logs/f'snapshot-{key}.log')
   s['status']='rendering';save();output=ROOT/'final'/f'{key}.mp4'
   run(cli+['render',str(project),'--fps','25','--quality','delivery','--crf','20','--workers','2','--output',str(output)],logs/f'render-{key}.log')
   probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,width,height','-of','json',str(output)]))
   assert abs(float(probe['format']['duration'])-j['duration'])<1
   assert any(x.get('width')==1920 and x.get('height')==1080 for x in probe['streams']) and any(x['codec_type']=='audio' for x in probe['streams'])
   run(['ffmpeg','-v','error','-i',str(output),'-f','null','-'],logs/f'decode-{key}.log')
   s.update(status='rendered',file=str(output),duration=float(probe['format']['duration']));save();print(key,'rendered',s['duration'],flush=True)
  except Exception as e:
   s.update(status='failed',error=type(e).__name__+': '+str(e)[:200]);save();print(key,s['error'],flush=True)
 if len(state)==len(json.loads((ROOT/'blocos/manifest.json').read_text())) and all(x.get('status') in ['rendered','failed'] for x in state.values()):break
 time.sleep(60)
