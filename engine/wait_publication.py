import time,json,subprocess,sys
from settings import ROOT,PROJECT,LANGUAGES,CFG
from publish_finished import publish
from finalize_project import finalize
def report_problem():
 if not (ROOT/'verification/telegram-problem.json').exists():subprocess.run(['node',str(PROJECT/'engine/send_final_v3.mjs'),'--problem'],check=True)

for attempt in range(720):
 manifest=json.loads((ROOT/'blocos/manifest.json').read_text())
 if any(not b.get('id') for b in manifest):
  unit=f"explica-{CFG['id']}-submit"
  if subprocess.run(['systemctl','--user','is-active','--quiet',unit]).returncode:
   report_problem();raise RuntimeError('Submission service stopped with unsent blocks')
 for relative in ['blocos/manifest.json','verification/production.json','verification/blocos-downloads.json']:
  f=ROOT/relative
  if not f.exists():continue
  data=json.loads(f.read_text());items=data if isinstance(data,list) else data.values()
  if any(x.get('status') in ['failed','needs_review'] for x in items):
   report_problem();raise RuntimeError('Stage needs review: '+relative)
 if all((ROOT/f'verification/assembled-{l}.json').exists() for l in LANGUAGES):
  try:
   publish()
  except Exception:
   report_problem();raise
  # Portal receipt is produced only after all three catalog pushes.
  while not (PROJECT/'docs/portal-publication.json').exists():time.sleep(60)
  try:
   finalize()
  except Exception:
   report_problem();raise
  subprocess.run(['node',str(PROJECT/'engine/send_final_v3.mjs')],check=True);break
 time.sleep(60)
else:
 report_problem();raise RuntimeError('Publication deadline exceeded: inspect stage state')
