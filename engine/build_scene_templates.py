from pathlib import Path
import json,html
from settings import ROOT,REPO,CFG,LANGUAGES;E=html.escape
for lang in LANGUAGES:
 scenes=json.loads((ROOT/f'docs/lesson-{lang}.json').read_text());folder=ROOT/'templates'/lang;folder.mkdir(parents=True,exist_ok=True)
 for i,s in enumerate(scenes,1):
  ident=f'scene-{i:02d}';duration=round(len(s['speech'].split())/145*60+2,2)
  (folder/f'{ident}.html').write_text(f'''<!doctype html><html lang="{lang}"><body><template><div data-composition-id="{ident}" data-duration="{duration}"></div><script>(function(){{const root=document.querySelector('[data-composition-id="{ident}"]');const tl=gsap.timeline({{paused:true}});const q=s=>root.querySelectorAll(s);tl.fromTo(q('.main-title'),{{y:45,opacity:0}},{{y:0,opacity:1,duration:.55,ease:'power3.out'}},.12);tl.fromTo(q('.item'),{{y:30,opacity:0}},{{y:0,opacity:1,duration:.55,stagger:.12,ease:'power3.out'}},.6);tl.fromTo(q('.progress-fill'),{{scaleX:0}},{{scaleX:1,duration:{duration},ease:'none'}},0);window.__timelines['{ident}']=tl;}})();</script></template></body></html>''')
 (ROOT/f'STORYBOARD-{lang.upper()}.md').write_text('# Cenas e fontes\n\n'+'\n\n'.join(f'## Frame {i}\nstatus: animated\nsrc: scene-{i:02d}.html\nrules: spring-pop-entrance; stat-bars-and-fills\n\n{s["chapter"]}: {s["title"]}\nFonte: {s["source"]}\nNarração: {s["speech"]}' for i,s in enumerate(scenes,1)))
