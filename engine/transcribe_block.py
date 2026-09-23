"""Transcribe generated avatar audio with real word timestamps; runtime credentials only."""
import json,subprocess,os,sys,time
from pathlib import Path
import requests
from settings import ROOT,REPO,CFG,LANGUAGES
def transcribe(key,language):
 dest=ROOT/'verification'/f'transcript-{key}.json'
 if dest.exists():return json.loads(dest.read_text())
 video=ROOT/'assets'/f'nei-{key}.mp4';audio=ROOT/'assets'/f'nei-{key}.mp3'
 subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vn','-ar','16000','-ac','1','-b:a','64k','-y',str(audio)],check=True)
 secret=None
 for p in [Path.home()/'projetos/openpcbotv2/.env',Path.home()/'projetos/wifi/.env']:
  if not p.exists():continue
  for line in p.read_text().splitlines():
   if line.startswith('GROQ_API_KEY='):secret=line.split('=',1)[1].strip().strip('\"\'');break
  if secret:break
 assert secret,'Missing runtime credential'
 for attempt in range(3):
  with audio.open('rb') as f:
   r=requests.post('https://api.groq.com/openai/v1/audio/transcriptions',headers={'Authorization':'Bearer '+secret},files={'file':(audio.name,f,'audio/mpeg')},data={'model':'whisper-large-v3','language':language,'response_format':'verbose_json','timestamp_granularities[]':'word'},timeout=180)
  if r.status_code==200:break
  if r.status_code not in [429,500,502,503]:raise RuntimeError('Transcription HTTP '+str(r.status_code))
  time.sleep(20)
 r.raise_for_status();d=r.json();assert len(d.get('words',[]))>100,'Incomplete transcript'
 dest.write_text(json.dumps(d,ensure_ascii=False,indent=2));return d
if __name__=='__main__':
 d=transcribe(sys.argv[1],sys.argv[2]);print('words',len(d['words']),'duration',d.get('duration'))
