#!/usr/bin/env python3
"""Config-driven production commands; all media stays outside this repository."""
from pathlib import Path
import argparse,os,subprocess,json,sys
ROOT=Path(__file__).resolve().parent
AJUDA='''comandos:
  prepare   monta cenas, blocos (<= 4.400 caracteres) e templates. Não gera nada no HeyGen.
  preview   renderiza o bloco 1 localmente, sem avatar, para conferir o layout.
  start     sobe 5 serviços (submit, monitor, render, assemble, publish).
            ATENÇÃO: o submit GERA VÍDEO no HeyGen. Só rode com APROVADO_HEYGEN
            no output (texto da autorização do Nei com nº de blocos e minutos).
  status    resumo: blocos enviados, baixados, renderizados, publicação.

HeyGen, modelo atual (padrão, em produção):
  gerar      script Playwright no ESTÚDIO (heygen-studio.mjs), pela assinatura,
             com o perfil ~/.cache/inemaccbot/perfil-heygen na tela :99.
  conferir   submit.py e monitor.py leem GET /v3/videos/<id> na API (só leitura).
  baixar     monitor.py baixa o video_url que a API devolve (só leitura).

HeyGen, opção em estudo (NÃO implementada): estúdio de ponta a ponta.
  Conferir e baixar também pelo estúdio, pelo título exato, sem chave de API.
  Ganha: nenhuma API; enxerga o estado real (Draft, fila, pronto, falhou).
  Perde: depende da sessão do perfil e do layout do HeyGen; checagem mais lenta.

Cuidado: a API responde "pending" para RASCUNHO. Bloco "pending" por horas =
olhar Projetos no estúdio antes de qualquer reenvio (caso de 29/09/2026:
3 blocos do OSWork v6.2 estavam em Draft; nada gerado, nada cobrado).
Reenviar = gerar vídeo = só com autorização explícita. Detalhes: README.md,
seção "HeyGen: como o motor gera, confere e baixa (opções)".'''
p=argparse.ArgumentParser(description='Explicavideos: vídeo explicativo com avatar e voz do Nei, dirigido por config.',epilog=AJUDA,formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--config',default=str(ROOT/'examples/oswork.json'),help='config da produção (examples/<nome>.json)')
p.add_argument('command',choices=['prepare','start','status','preview'],help='o que fazer (ver abaixo)');a=p.parse_args()
c=Path(a.config).resolve();cfg=json.loads(c.read_text());env={**os.environ,'EXPLICAVIDEOS_CONFIG':str(c)}
def run(script,*args):subprocess.run([sys.executable,str(ROOT/'engine'/script),*args],env=env,check=True)
if a.command=='prepare':run('prepare.py');run('build_scene_templates.py')
elif a.command=='preview':run('build_final_block.py','pt','1','--preview')
elif a.command=='start':
 if subprocess.run(['xdpyinfo','-display',':99'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
  subprocess.run(['systemd-run','--user','--collect','--unit=explicavideos-display','/usr/bin/Xvfb',':99','-screen','0','1920x1080x24','-nolisten','tcp'],check=True)
  import time
  for _ in range(20):
   if subprocess.run(['xdpyinfo','-display',':99'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:break
   time.sleep(.25)
  else:raise RuntimeError('Virtual display did not start')
 for stage,script in [('submit','submit.py'),('monitor','monitor.py'),('render','produce_blocks.py'),('assemble','wait_assembly.py'),('publish','wait_publication.py')]:
  unit=f"explica-{cfg['id']}-{stage}"
  if subprocess.run(['systemctl','--user','is-active','--quiet',unit]).returncode==0:continue
  subprocess.run(['systemd-run','--user','--collect','--slice=explica.slice','--unit='+unit,'--property=WorkingDirectory='+str(ROOT),'--setenv=EXPLICAVIDEOS_CONFIG='+str(c),sys.executable,str(ROOT/'engine'/script)],check=True)
elif a.command=='status':
 out=Path(cfg['output']);result={}
 for name,file in [('submitted','blocos/manifest.json'),('downloads','verification/blocos-downloads.json'),('production','verification/production.json'),('publication','verification/publication.json'),('notification','verification/telegram-final.json')]:
  f=out/file
  if not f.exists():result[name]='not started';continue
  value=json.loads(f.read_text())
  if name in ['submitted','downloads','production']:
   values=value if isinstance(value,list) else value.values();counts={}
   for item in values:status='downloaded' if item.get('downloaded') else item.get('status','unknown');counts[status]=counts.get(status,0)+1
   result[name]=counts
  else:result[name]=value
 print(json.dumps(result,ensure_ascii=False,indent=2))
