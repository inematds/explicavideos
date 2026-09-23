"""Adapt OSWork authorial content or import a reviewed scene JSON without truncation."""
import json,runpy,re,shutil,hashlib,subprocess,ast
from pathlib import Path
from bs4 import BeautifulSoup
from settings import CFG,ROOT,REPO,PROJECT,LANGUAGES

def pack(scenes,limit):
 blocks=[];current=[];size=0
 for i,s in enumerate(scenes,1):
  n=len(s['speech'])
  if n>limit:raise ValueError(f'Scene {i} exceeds limit; split its narration before submitting')
  if current and size+n+1>limit:blocks.append(current);current=[];size=0
  current.append(i);size+=n+1
 if current:blocks.append(current)
 return blocks

def excerpt(text,limit=230):
 text=re.sub(r'\s+',' ',text).strip()
 return text if len(text)<=limit else text[:limit].rsplit(' ',1)[0]+'…'

def oswork():
 data=runpy.run_path(str(REPO/'conteudo/modulos.py'));scenes=[];coverage=[]
 tree=ast.parse((REPO/'scripts/build.py').read_text());snippets=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SNIPPETS' for t in n.targets))
 def add(title,chapter,speech,labels,source,svg=None):
  speech=re.sub(r'\s+',' ',speech).strip()
  scenes.append(dict(title=title,chapter=chapter,speech=speech,labels=labels,source=source,svg=svg,kind='diagram' if svg else 'steps',takeaway=title if any('\n' in x for x in labels) else (labels[-1] if labels else title)))
 add('Organize seu sistema de trabalho','OSWORK · CURSO COMPLETO','Bem-vindo ao OSWork completo. Eu sou Nei Maldaner. Vamos percorrer os oito módulos, com os quarenta e oito tópicos, exemplos e exercícios. O objetivo é organizar um sistema de trabalho com inteligência artificial, do primeiro pedido até a operação contínua. Pause quando chegar aos exercícios e faça os testes na sua pasta de treino. Este vídeo acompanha a edição do curso de setembro de dois mil e vinte e seis; nomes, acessos e preços podem mudar.', ['Modelo e interface','Arquivos e instruções','Versionamento e operação'],'index.html')
 for mi,m in enumerate(data['MODULES']):
  source=f'curso/trilha{mi//2+1}/modulo-{mi//2+1}-{mi%2+1}.html';chapter=f"MÓDULO {mi+1:02d} · {m['title']}"
  soup=BeautifulSoup((REPO/source).read_text(),'html.parser');figs=iter(soup.select('figure.module-figure svg'))
  add(m['title'],chapter,f"Módulo {mi+1}. {m['title']}. Nosso objetivo é {m['goal']} Ao final, vamos fazer o exercício: {m['lab']}.",[t['title'] for t in m['topics'][:3]],source)
  for ti,t in enumerate(m['topics'],1):
   svg=None
   if (mi,ti) in data['FIGURES']:
    el=next(figs);svg=str(el).replace('viewbox=','viewBox=')
   labels=[x.strip().rstrip('.') for x in t['keys'].split(';')]
   # Semantic labels stay separate from full narration, avoiding walls of text.
   if len(labels)==1:labels=[t['title'],'Por que importa','Aplicação no trabalho']
   add(t['title'],chapter,f"{t['title']}. {t['what']} Por que isso importa? {t['why']} Pontos para lembrar: {t['keys']}",labels,source,svg)
   add('Na prática: '+t['title'],chapter,f"Vamos a um exemplo. {t['example']} Agora é sua vez. {t['action']}",['Exemplo\n'+excerpt(t['example']), 'Sua ação\n'+excerpt(t['action'])],source)
   coverage.append({'module':mi+1,'topic':ti,'title':t['title'],'scenes':[len(scenes)-1,len(scenes)],'fields':['what','why','keys','example','action']})
  add(m['lab'],chapter,'Vamos ao laboratório. '+m['lab']+'. '+' '.join(f"Passo {i+1}. {x}" for i,x in enumerate(m['steps'])),['Prepare a entrada','Execute na pasta de treino','Compare com os critérios'],source)
  scenes[-1]['code']=snippets[mi][1]
  add('Confira o que aprendeu',chapter,f"Antes de avançar, pense nesta pergunta. {m['check']} A resposta é: {m['answer']} Se você consegue explicar isso com suas palavras e mostrar o resultado do exercício, pode seguir para a próxima etapa.",['Pergunta de revisão','Evidência do exercício','Explique com suas palavras'],source)
 add('Seu sistema, funcionando','OSWORK · PRÓXIMOS PASSOS','Concluímos os oito módulos. Você percorreu modelos, interfaces, terminal, organização de arquivos, instruções, habilidades, memória, Git, GitHub, Telegram e operação em servidor. O próximo passo é escolher uma tarefa pequena, definir entrada e saída, executar, conferir e registrar o que aprendeu. Volte aos módulos e aos materiais sempre que precisar. O sistema melhora quando você registra as decisões e corrige o ponto certo.', ['Uma tarefa pequena','Uma saída verificável','Um registro para retomar'],'index.html')
 assert len(coverage)==48
 return scenes,coverage

def prepare():
 manifest=ROOT/'blocos/manifest.json'
 if manifest.exists() and any(b.get('id') or b.get('status')!='prepared' for b in json.loads(manifest.read_text())):raise RuntimeError('Generation started; do not replace its source manifest')
 for d in ['docs','blocos','assets','verification','final']: (ROOT/d).mkdir(parents=True,exist_ok=True)
 jobs=[]
 for lang in LANGUAGES:
  if CFG.get('scene_files'):
   scenes=json.loads(Path(CFG['scene_files'][lang]).read_text());coverage=[]
  else:
   assert lang=='pt','Other languages require reviewed scene_files';scenes,coverage=oswork()
  (ROOT/f'docs/lesson-{lang}.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2))
  (ROOT/f'docs/coverage-{lang}.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2))
  for part,ids in enumerate(pack(scenes,CFG['max_chars']),1):
   speech=' '.join(scenes[i-1]['speech'] for i in ids);file=ROOT/f'blocos/{lang}-b{part:02d}.txt';file.write_text(speech)
   jobs.append(dict(language=lang,part=part,title=f"EXPLICA-{CFG['id'].upper()}-{lang.upper()}-B{part:02d}-v1",scenes=ids,chars=len(speech),file=str(file),sha256=hashlib.sha256(speech.encode()).hexdigest(),status='prepared'))
  assert ' '.join((ROOT/f'blocos/{lang}-b{b["part"]:02d}.txt').read_text() for b in jobs if b['language']==lang)==' '.join(s['speech'] for s in scenes)
 for f in (PROJECT/'assets').iterdir():shutil.copy2(f,ROOT/('assets/'+f.name if f.suffix not in ['.json'] else f.name))
 manifest.write_text(json.dumps(jobs,ensure_ascii=False,indent=2))
 (ROOT/'BRIEF.md').write_text('---\nworkflow: general-video\nflow: automation\nstoryboard: no\n---\n# OSWork completo\nReutilizar estilo aprovado Astra e OSWork Quick. Avatar Nei, voz INEMATIME, HeyGen Avatar III via assinatura, 1080p, legendas reais. Narração sem música para clareza. Fontes e cobertura em docs/. Publicar após verificação e avisar bot v3.\n')
 print(json.dumps({'blocks':len(jobs),'scenes':len(scenes),'topics':len(coverage),'chars':sum(b['chars'] for b in jobs)}))
if __name__=='__main__':prepare()
