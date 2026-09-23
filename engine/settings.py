from pathlib import Path
import json,os
PROJECT=Path(__file__).resolve().parents[1]
CONFIG=Path(os.environ.get('EXPLICAVIDEOS_CONFIG',PROJECT/'examples/oswork.json')).resolve()
CFG=json.loads(CONFIG.read_text())
ROOT=Path(CFG['output']); REPO=Path(CFG['source_repo']); LANGUAGES=CFG['languages']
