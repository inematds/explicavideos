from settings import LANGUAGES, ROOT
import time, json, sys
from assemble_languages import assemble
STATE = ROOT / 'verification/production.json'
for _ in range(720):
 done=[]
 for lang in LANGUAGES:
  result=assemble(lang)
  if result:done.append(lang)
 if len(done)==len(LANGUAGES):break
 # bloco que falhou no produce_blocks nunca fica pronto: parar em vez de esperar 12 h
 state=json.loads(STATE.read_text()) if STATE.exists() else {}
 bad={k:v.get('error','') for k,v in state.items() if v.get('status')=='failed'}
 if bad:
  print('ASSEMBLY_ABORT blocos com falha:',bad,flush=True);sys.exit(1)
 time.sleep(60)
