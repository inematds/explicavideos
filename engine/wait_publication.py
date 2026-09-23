import time,json,subprocess,sys
from settings import ROOT,PROJECT,LANGUAGES
from publish_finished import publish
for attempt in range(720):
 if all((ROOT/f'verification/assembled-{l}.json').exists() for l in LANGUAGES):
  publish()
  # Portal receipt is produced only after all three catalog pushes.
  while not (PROJECT/'docs/portal-publication.json').exists():time.sleep(60)
  subprocess.run(['node',str(PROJECT/'engine/send_final_v3.mjs')],check=True);break
 time.sleep(60)
else:raise RuntimeError('Publication deadline exceeded: inspect stage state')
