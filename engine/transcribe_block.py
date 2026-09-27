"""Transcribe generated avatar audio with real word timestamps; runtime credentials only."""
import json,subprocess,os,sys,time
from pathlib import Path
import requests
from settings import ROOT,REPO,CFG,LANGUAGES
def local(audio,language):
 """Whisper large-v3 on this machine; one process at a time (GB10 unified memory)."""
 import fcntl,gc
 with open('/tmp/explicavideos-whisper.lock','w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  import whisper,torch
  model=whisper.load_model(CFG.get('whisper_model','large-v3'))
  try:r=model.transcribe(str(audio),language=language,word_timestamps=True,condition_on_previous_text=False,initial_prompt=CFG.get('whisper_prompt','Nei Maldaner, INEMA.'))
  finally:
   del model;gc.collect()
   if torch.cuda.is_available():torch.cuda.empty_cache()
 words=[{'word':w['word'].strip(),'start':float(w['start']),'end':float(w['end'])} for s in r['segments'] for w in s.get('words',[]) if w['word'].strip()]
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)]))
 return {'text':r['text'],'language':language,'duration':duration,'words':words,'transcriber':'whisper-local'}
def transcribe(key,language):
 dest=ROOT/'verification'/f'transcript-{key}.json'
 if dest.exists():return json.loads(dest.read_text())
 video=ROOT/'assets'/f'nei-{key}.mp4';audio=ROOT/'assets'/f'nei-{key}.mp3'
 subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vn','-ar','16000','-ac','1','-b:a','64k','-y',str(audio)],check=True)
 if CFG.get('transcriber')=='whisper-local':
  d=local(audio,language);assert len(d['words'])>100,'Incomplete transcript'
  dest.write_text(json.dumps(d,ensure_ascii=False,indent=2));return d
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
