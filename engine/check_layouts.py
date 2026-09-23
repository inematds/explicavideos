from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess,json,os
from build_final_block import build,ROOT
blocks=json.loads((ROOT/'blocos/manifest.json').read_text())
for b in blocks:build(b['language'],b['part'],True)
def check(b):
 key=f"{b['language']}-b{b['part']:02d}";log=ROOT/f'verification/layout-{key}.log'
 with log.open('w') as f:
  p=subprocess.run(['npx','--yes','hyperframes@0.8.66','check',str(ROOT/'layout-preview'/key)],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'HYPERFRAMES_BROWSER_PATH':'/home/nmaldaner/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux-arm64/chrome-headless-shell'})
 return key,p.returncode
with ThreadPoolExecutor(max_workers=3) as pool:
 results=list(pool.map(check,blocks))
(ROOT/'verification/layout-results.json').write_text(json.dumps(dict(results),indent=2));print(results,flush=True)
