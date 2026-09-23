from settings import LANGUAGES
import time
from assemble_languages import assemble
for _ in range(720):
 done=[]
 for lang in LANGUAGES:
  result=assemble(lang)
  if result:done.append(lang)
 if len(done)==len(LANGUAGES):break
 time.sleep(60)
