"""Release only measured, decoded, complete films; preserve course source files."""
from pathlib import Path
import json,subprocess,urllib.request,time,html,re
from settings import ROOT,REPO,CFG,LANGUAGES,PROJECT

def run(args,**kw):return subprocess.run(args,cwd=REPO,check=True,**kw)
def publish():
 receipt=ROOT/'verification/publication.json'
 if receipt.exists():return
 blocks=json.loads((ROOT/'blocos/manifest.json').read_text())
 production=json.loads((ROOT/'verification/production.json').read_text())
 assert len(production)==len(blocks) and all(s['status']=='rendered' for s in production.values())
 receipts={l:json.loads((ROOT/f'verification/assembled-{l}.json').read_text()) for l in LANGUAGES}
 for l,r in receipts.items():
  scenes=json.loads((ROOT/f'docs/lesson-{l}.json').read_text())
  assert Path(r['file']).stat().st_size==r['bytes'] and len(r['chapters'])==len(scenes)
  assert (ROOT/f'verification/decode-full-{l}.log').read_text()==''
  for b in [b for b in blocks if b['language']==l]:
   key=f"{l}-b{b['part']:02d}"
   assert json.loads((ROOT/f'final/{key}/alignment.json').read_text())['ratio']>.90
   assert (ROOT/f'verification/decode-{key}.log').read_text()==''
 tag=CFG['release_tag'];repo=CFG['github_repo'];title=CFG['title'];notes=ROOT/'final/RELEASE.md'
 notes.write_text(title+' — avatar e voz do Nei, todos os tópicos da fonte, ilustrações e legendas sincronizadas.\n\nProdução: https://inematds.github.io/explicavideos/guia/\n\n'+ '\n'.join(f"- {l.upper()}: {int(r['duration']//60)}min{int(r['duration']%60):02d}s" for l,r in receipts.items()))
 if subprocess.run(['gh','release','view',tag,'--repo',repo],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:run(['gh','release','create',tag,'--repo',repo,'--draft','--title',title+' — vídeo completo','--notes-file',str(notes)])
 run(['gh','release','upload',tag,'--repo',repo,'--clobber',*[str(ROOT/f"final/{CFG['id']}-{l}.{ext}") for l in LANGUAGES for ext in ['mp4','srt']]])
 videos={l:{'url':f"https://github.com/{repo}/releases/download/{tag}/{CFG['id']}-{l}.mp4",'srt':f"https://github.com/{repo}/releases/download/{tag}/{CFG['id']}-{l}.srt",'duration':r['duration']} for l,r in receipts.items()}
 folder=REPO/'videos';folder.mkdir(exist_ok=True)
 for l,item in videos.items():
  srt=(ROOT/f"final/{CFG['id']}-{l}.srt").read_text();(folder/f'{l}.vtt').write_text('WEBVTT\n\n'+re.sub(r'(\d\d:\d\d:\d\d),(\d{3})',r'\1.\2',srt))
  scenes=json.loads((ROOT/f'docs/lesson-{l}.json').read_text());chapters=[];seen=set()
  for ch in receipts[l]['chapters']:
   label=scenes[ch['scene']-1]['chapter']
   if label in seen:continue
   seen.add(label);t=int(ch['time']);chapters.append(f'<button type="button" data-time="{t}">{t//60:02d}:{t%60:02d} · {html.escape(label)}</button>')
  page='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__ — vídeo</title><style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#171b20;color:#f7f1e7;font:18px/1.6 system-ui}main{max-width:1200px;margin:auto;padding:32px 24px}a{color:#efbe69}video{width:100%;aspect-ratio:16/9;background:#101419;border-radius:14px}button{display:block;background:#232a31;color:#fff;border:1px solid #56616c;border-radius:8px;padding:12px;margin:8px 0;text-align:left;cursor:pointer;width:100%}:focus-visible{outline:3px solid #efbe69;outline-offset:3px}</style></head><body><main><nav><a href="https://inema.club">INEMA.CLUB</a> · <a href="../index.html">Curso e materiais</a> · <a href="https://inematds.github.io/explicavideos/guia/">Como este vídeo foi produzido</a></nav><h1>__TITLE__</h1><p>Avatar e voz do Nei · curso completo em português · __DURATION__</p><video controls preload="metadata"><source src="__URL__" type="video/mp4"><track default kind="subtitles" src="pt.vtt" srclang="pt" label="Português"></video><p><a href="__URL__">Baixar MP4</a> · <a href="__SRT__">Baixar legendas</a></p><h2>Capítulos</h2>__CHAPTERS__</main><script>document.querySelectorAll('[data-time]').forEach(b=>b.addEventListener('click',()=>{const v=document.querySelector('video');v.currentTime=Number(b.dataset.time);v.play();}));</script></body></html>'''
  for k,v in {'TITLE':html.escape(title),'DURATION':f"{int(item['duration']//60)}min{int(item['duration']%60):02d}s",'URL':item['url'],'SRT':item['srt'],'CHAPTERS':''.join(chapters)}.items():page=page.replace('__'+k+'__',v)
  (folder/('index.html' if l=='pt' else l+'.html')).write_text(page)
 (folder/'delivery.json').write_text(json.dumps(videos,indent=2))
 readme=REPO/'README.md';text=readme.read_text();marker='## Vídeo completo'
 if marker not in text:readme.write_text(text+f'\n\n{marker}\n\n[Assistir ao curso com Nei](https://inematds.github.io/{repo.split("/")[1]}/videos/). Ilustrações, capítulos e legendas. Produzido com [Explicavideos](https://inematds.github.io/explicavideos/guia/).\n')
 run(['git','config','user.name','inematds']);run(['git','config','user.email','inematds@gmail.com']);run(['git','add','videos','README.md'])
 if subprocess.run(['git','diff','--cached','--quiet','--','videos','README.md'],cwd=REPO).returncode:run(['git','commit','-m','feat: publica vídeo completo com capítulos e legendas','--','videos','README.md'])
 run(['git','push','origin','HEAD:main']);run(['gh','release','edit',tag,'--repo',repo,'--draft=false'])
 for v in videos.values():
  with urllib.request.urlopen(urllib.request.Request(v['url'],method='HEAD'),timeout=60) as response:assert response.status==200
 player=f'https://inematds.github.io/{repo.split("/")[1]}/videos/'
 for attempt in range(20):
  try:
   with urllib.request.urlopen(player,timeout=30) as f:page=f.read().decode()
   if videos['pt']['url'] in page:break
  except Exception:pass
  time.sleep(30)
 else:raise RuntimeError('Push and release completed; Pages verification pending')
 receipt.write_text(json.dumps({'release':f'https://github.com/{repo}/releases/tag/{tag}','player':player,'videos':videos},indent=2))
