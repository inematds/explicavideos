"""Publish delivery evidence in the reusable project's guide after the film exists."""
import json,subprocess
from settings import ROOT,PROJECT,CFG

def finalize():
 receipt=json.loads((ROOT/'verification/publication.json').read_text());dest=PROJECT/'docs/video-publication.json'
 dest.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
 p=PROJECT/'guia/index.html';s=p.read_text().replace('OSWork completo em produção','OSWork completo publicado').replace('Produção em andamento.','Vídeo completo disponível, com capítulos e legendas.').replace('href="https://inematds.github.io/oswork/">Abrir curso fonte','href="https://inematds.github.io/oswork/videos/">Assistir ao vídeo')
 s=s.replace('Roteiro preparado. Geração, sincronização e renderização precedem a entrega. O aviso final será enviado pelo bot v3.','Vídeo gerado, sincronizado, verificado e publicado. Acesse o player do OSWork e os arquivos MP4 e SRT.');p.write_text(s)
 p=PROJECT/'README.md';s=p.read_text();s += '' if '## Entrega OSWork' in s else '\n\n## Entrega OSWork\n\n[Assistir ao vídeo completo](https://inematds.github.io/oswork/videos/). Recibo de publicação em docs/video-publication.json.\n';p.write_text(s)
 p=PROJECT/'context/current-state.md';p.write_text('# Concluído\nProjeto publicado no GitHub e nos três catálogos. Vídeo completo verificado e publicado: '+receipt['player']+'\nRecibos: docs/portal-publication.json e docs/video-publication.json.\n')
 p=PROJECT/'tasks/current.md';p.write_text(p.read_text().replace('- [ ] Concluir vídeo, verificar e notificar bot v3','- [x] Concluir vídeo e verificar publicação\n- [ ] Conferir recibo do aviso no bot v3'))
 paths=['docs/video-publication.json','guia/index.html','README.md','context/current-state.md','tasks/current.md']
 def run(args):subprocess.run(args,cwd=PROJECT,check=True)
 run(['git','add',*paths])
 if subprocess.run(['git','diff','--cached','--quiet','--',*paths],cwd=PROJECT).returncode:run(['git','commit','-m','docs: registra entrega do vídeo completo OSWork','--',*paths])
 run(['git','push','origin','HEAD:main'])
