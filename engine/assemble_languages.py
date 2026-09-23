"""Join verified rendered blocks and offset SRT timestamps for each full lesson."""
from pathlib import Path
import json,subprocess,re
from settings import ROOT,REPO,CFG,LANGUAGES
def ts(s):
 h,m,rest=s.split(':');sec,ms=rest.split(',');return int(h)*3600+int(m)*60+int(sec)+int(ms)/1000
def stamp(t):
 n=round(t*1000);return f'{n//3600000:02d}:{n//60000%60:02d}:{n//1000%60:02d},{n%1000:03d}'
def assemble(lang):
 blocks=[b for b in json.loads((ROOT/'blocos/manifest.json').read_text()) if b['language']==lang]
 if not (ROOT/'verification/production.json').exists():return None
 states=json.loads((ROOT/'verification/production.json').read_text());keys=[f"{lang}-b{b['part']:02d}" for b in blocks]
 if not all(states.get(k,{}).get('status')=='rendered' for k in keys):return None
 dest=ROOT/'final'/f"{CFG['id']}-{lang}.mp4";receipt=ROOT/'verification'/f'assembled-{lang}.json'
 if receipt.exists() and dest.exists():return dest
 listing=ROOT/'final'/f'concat-{lang}.txt';listing.write_text(''.join(f"file '{k}.mp4'\n" for k in keys))
 subprocess.run(['ffmpeg','-v','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart','-y',str(dest)],check=True)
 subs=[];offset=0;chapter=[]
 for k,b in zip(keys,blocks):
  project=ROOT/'final'/k;alignment=json.loads((project/'alignment.json').read_text())
  for n,t in zip(b['scenes'],alignment['starts']):chapter.append({'scene':n,'time':round(offset+t,3)})
  for item in (project/'captions.srt').read_text().strip().split('\n\n'):
   lines=item.splitlines();a,z=lines[1].split(' --> ');subs.append(f'{len(subs)+1}\n{stamp(ts(a)+offset)} --> {stamp(ts(z)+offset)}\n'+ '\n'.join(lines[2:])+'\n')
  offset+=states[k]['duration']
 (ROOT/'final'/f"{CFG['id']}-{lang}.srt").write_text('\n'.join(subs))
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(dest)]))
 assert abs(duration-offset)<1
 with (ROOT/'verification'/f'decode-full-{lang}.log').open('w') as log:
  subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],stderr=log,check=True)
 receipt.write_text(json.dumps({'file':str(dest),'duration':duration,'blocks':keys,'chapters':chapter,'bytes':dest.stat().st_size},indent=2))
 print(lang,'assembled',duration,flush=True);return dest
if __name__=='__main__':
 for lang in LANGUAGES:assemble(lang)
