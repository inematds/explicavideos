"""Build a narrated HyperFrames block, aligned to measured speech word timestamps."""
from pathlib import Path
import ast,json,html,re,difflib,unicodedata,shutil,sys
from settings import ROOT,REPO,CFG,LANGUAGES
E=html.escape
def visual(s):
 if s.get('svg'):return '<div class="diagram item">'+s['svg']+'</div>'
 return '<div class="nodes-flow">'+''.join(f'<div class="node item"><b>{i+1:02d}</b>{E(x)}</div>' for i,x in enumerate(s.get('labels',[])))+'</div>'
def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s.lower()).encode('ascii','ignore').decode())
def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}'
def build(lang,part,preview=False):
 key=f'{lang}-b{part:02d}';manifest=json.loads((ROOT/'blocos/manifest.json').read_text());block=next(b for b in manifest if b['language']==lang and b['part']==part)
 lesson=json.loads((ROOT/f'docs/lesson-{lang}.json').read_text());scenes=[lesson[i-1] for i in block['scenes']]
 if preview:
  script_words=' '.join(s['speech'] for s in scenes).split();words=[{'word':w,'start':i*.4,'end':(i+1)*.4-.025} for i,w in enumerate(script_words)];duration=len(words)*.4
 else:
  transcript=json.loads((ROOT/f'verification/transcript-{key}.json').read_text());words=transcript['words']
  duration=json.loads((ROOT/'verification/blocos-downloads.json').read_text())[key]['duration']
 source=[];boundaries=[]
 for s in scenes:boundaries.append(len(source));source.extend(norm(w) for w in s['speech'].split())
 spoken=[norm(w['word']) for w in words];matcher=difflib.SequenceMatcher(None,source,spoken,autojunk=False);mapping={}
 for m in matcher.get_matching_blocks():
  for k in range(m.size):mapping[m.a+k]=m.b+k
 ratio=matcher.ratio();assert ratio>.90,f'Low speech alignment {key}: {ratio}'
 starts=[0.0];evidence=[]
 for boundary in boundaries[1:]:
  near=min(mapping,key=lambda x:abs(x-boundary));assert abs(near-boundary)<=5,'Missing scene boundary'
  idx=mapping[near];t=words[idx]['start'];starts.append(round(t,3));evidence.append({'source_word':boundary,'matched_offset':near-boundary,'time':t})
 starts.append(round(duration,3));assert all(b>a+.1 for a,b in zip(starts,starts[1:]))
 dest=ROOT/('layout-preview' if preview else 'final')/key;(dest/'assets').mkdir(parents=True,exist_ok=True);(dest/'compositions').mkdir(exist_ok=True)
 for name in ['display.ttf','mono.ttf','gsap.min.js']:
  shutil.copy2(ROOT/'assets'/name,dest/'assets'/name)
 target=dest/'assets/avatar.mp4'
 if not preview and not target.exists():target.symlink_to(ROOT/'assets'/f'nei-{key}.mp4')
 shutil.copy2(ROOT/'hyperframes.json',dest/'hyperframes.json');shutil.copy2(ROOT/'package.json',dest/'package.json')
 css=(ROOT/'assets/style.css').read_text()+'''
:root{--accent:#efbe69}.diagram{width:100%;height:440px;display:flex;align-items:center;justify-content:center}.diagram svg{width:100%;height:100%;color:#f7f1e7}.diagram text{opacity:1}.nodes-flow .node{font-size:26px;padding:16px 20px;line-height:1.35}.main-title{font-size:58px;letter-spacing:-1px}.takeaway{font-size:25px!important}

.avatar-video{position:absolute;left:1398px;top:181px;width:450px;height:254px;object-fit:cover;border:2px solid #56616c;border-radius:18px;z-index:3}
.avatar-panel{padding-top:254px}.avatar-desc{font-size:23px}.takeaway{bottom:192px;font-size:29px}.footer{bottom:20px;font-size:19px}
.caption.clip{position:absolute;inset:auto 110px 62px;z-index:8;text-align:center;font-family:Data,monospace;font-size:32px;line-height:1.4;color:#fff;background:#101419;padding:12px 26px;border-radius:10px}
'''
 (dest/'assets/style.css').write_text(css)
 localization={'pt':('GUIA PRÁTICO','CONTROLE DE TOKENS','Narração em português','Exemplo didático · entrada por solicitação · sem cache'),'es':('GUÍA PRÁCTICA','CONTROL DE TOKENS','Narración en español','Ejemplo didáctico · entrada por solicitud · sin caché'),'en':('PRACTICAL GUIDE','TOKEN MANAGEMENT','English narration','Illustrative scenario · input per request · no cache')}[lang]
 hosts=[]
 for i,s in enumerate(scenes):
  number=block['scenes'][i];ident=f'scene-{number:02d}';length=round(starts[i+1]-starts[i],3)
  original=(ROOT/f'templates/{lang}/{ident}.html').read_text()
  # Preserve approved scene motion, replacing only timing and copy.
  script=re.search(r'<script>(.*?)</script>',original,re.S).group(1)
  oldduration=float(re.search(r'data-duration="([\d.]+)"',original).group(1))
  script=script.replace(f'duration:{oldduration}',f'duration:{length}')
  script=re.sub(r'const a=1\.8\+i\*[\d.]+',f'const a=1.8+i*{max(.5,(length-4)/max(len(s.get("labels",[])),1))}',script)
  markup=f'''<!doctype html><html lang="{lang}"><body><template><style>#{ident}-root{{position:absolute;inset:0;width:100%;height:100%;}}</style><div id="{ident}-root" data-composition-id="{ident}" data-width="1920" data-height="1080" data-duration="{length}"><div class="scene-shell"><header class="topline"><span>{E(s['chapter'])}</span><span>INEMA · {localization[0]}</span></header><div class="layout"><main><h1 class="main-title">{E(s['title'])}</h1><div class="visual kind-{s['kind']}">{visual(s).replace('Cenário didático · entrada por solicitação · sem cache',localization[3])}</div></main><aside class="avatar-panel"><p class="avatar-name">Nei Maldaner</p><div class="avatar-desc">{localization[2]}</div></aside></div><div class="takeaway">{E(s['takeaway'])}</div><footer class="footer"><span>{E(CFG['title'].upper())}</span><span>{number:02d} / {len(lesson):02d}</span></footer><div class="progress-track"><div class="progress-fill"></div></div></div></div><script>{script}</script></template></body></html>'''
  (dest/f'compositions/{ident}.html').write_text(markup)
  hosts.append(f'<div id="{ident}" class="clip" data-composition-id="{ident}" data-composition-src="compositions/{ident}.html" data-start="{starts[i]}" data-duration="{length}" data-track-index="1"></div>')
 captions=[];group=[]
 for word in words:
  group.append(word)
  if len(' '.join(w['word'] for w in group))>=65 or len(group)>=11 or re.search(r'[.!?]$',word['word']):captions.append(group);group=[]
 if group:captions.append(group)
 srt=[]
 for i,group in enumerate(captions):
  start=group[0]['start'];next_start=captions[i+1][0]['start'] if i+1<len(captions) else duration;end=min(duration,next_start-.025,max(start+.04,group[-1]['end']));
  if end<=start:continue
  text=' '.join(w['word'] for w in group).strip()
  srt.append(f'{i+1}\n{stamp(start)} --> {stamp(end)}\n{text}\n')
  hosts.append(f'<div id="cap-{i}" class="clip caption" data-start="{start}" data-duration="{end-start:.3f}" data-track-index="3">{E(text)}</div>')
 (dest/'captions.srt').write_text('\n'.join(srt))
 body=''.join(hosts)+f'<video id="avatar" class="clip avatar-video" src="assets/avatar.mp4" muted playsinline data-start="0" data-duration="{duration}" data-track-index="2"></video><audio id="voice" src="assets/avatar.mp4" data-start="0" data-duration="{duration}" data-track-index="4"></audio>'
 if preview:
  body=''.join(hosts[:len(scenes)])+'<div class="avatar-video" style="display:flex;align-items:center;padding:30px;color:#efbe69;font-size:27px">PRÉVIA VISUAL · SEM NARRAÇÃO</div>'
 (dest/'index.html').write_text(f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><link rel="stylesheet" href="assets/style.css"><script src="assets/gsap.min.js"></script></head><body><div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="{duration}">{body}</div><script>window.__timelines["main"]=gsap.timeline({{paused:true}});</script></body></html>')
 (dest/'alignment.json').write_text(json.dumps({'ratio':ratio,'scene_numbers':block['scenes'],'starts':starts,'boundaries':evidence,'duration':duration},indent=2))
 print(key,'alignment',round(ratio,3),'seconds',duration,flush=True);return dest
if __name__=='__main__':build(sys.argv[1],int(sys.argv[2]),'--preview' in sys.argv)
