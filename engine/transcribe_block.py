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
  opts=dict(language=language,word_timestamps=True,condition_on_previous_text=False,initial_prompt=CFG.get('whisper_prompt','Nei Maldaner, INEMA.'))
  get=lambda r,off=0:[{'word':w['word'].strip(),'start':float(w['start'])+off,'end':float(w['end'])+off} for s in r['segments'] for w in s.get('words',[]) if w['word'].strip()]
  try:
   r=model.transcribe(str(audio),**opts);words=get(r)
   # Whisper on the full file sometimes skips whole 30 s windows (after short lines like "Agora pause.");
   # the same span transcribes fine alone, but only from some start points. Re-transcribe every gap > 3 s
   # from up to three starts (+0, +1.5, +3 s), keep the richest result and splice the words in.
   pcm=whisper.load_audio(str(audio));end=len(pcm)/16000;edges=[0.0]+[x for w in words for x in (w['start'],w['end'])]+[end]
   for a,b in [(edges[i],edges[i+1]) for i in range(0,len(edges),2) if edges[i+1]-edges[i]>3]:
    extra=[]
    for s in [a+d for d in (0,1.5,3) if a+d<b-2]:
     got=[w for w in get(model.transcribe(pcm[int(s*16000):int(b*16000)],**opts),s) if w['start']>=a-.2 and w['end']<=b+.2]
     if len(got)>len(extra):extra=got
     if len(extra)>=(b-s)*1.5:break
    words.extend(extra);print(f'whisper gap {a:.1f}-{b:.1f}s: +{len(extra)} words',flush=True)
   words.sort(key=lambda w:w['start'])
  finally:
   del model;gc.collect()
   if torch.cuda.is_available():torch.cuda.empty_cache()
 duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(audio)]))
 return {'text':' '.join(w['word'] for w in words),'language':language,'duration':duration,'words':words,'transcriber':'whisper-local'}
def transcribe(key,language):
 dest=ROOT/'verification'/f'transcript-{key}.json'
 if dest.exists():return json.loads(dest.read_text())
 video=ROOT/'assets'/f'nei-{key}.mp4';audio=ROOT/'assets'/f'nei-{key}.mp3'
 subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vn','-ar','16000','-ac','1','-b:a','64k','-y',str(audio)],check=True)
 if CFG.get('transcriber')=='whisper-local':
  d=local(audio,language);assert len(d['words'])>CFG.get('min_words',100),'Incomplete transcript'
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
 r.raise_for_status();d=r.json();assert len(d.get('words',[]))>CFG.get('min_words',100),'Incomplete transcript'
 dest.write_text(json.dumps(d,ensure_ascii=False,indent=2));return d
if __name__=='__main__':
 d=transcribe(sys.argv[1],sys.argv[2]);print('words',len(d['words']),'duration',d.get('duration'))
