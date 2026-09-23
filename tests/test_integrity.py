import unittest,sys,json,runpy,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'engine'))
from prepare import pack
from settings import ROOT,REPO
class Integrity(unittest.TestCase):
 def test_pack_keeps_every_scene_once(self):
  scenes=[{'speech':'a'*n} for n in [1200,1300,2100,100,4300]]
  blocks=pack(scenes,4400)
  self.assertEqual([i for b in blocks for i in b],list(range(1,6)))
  for b in blocks:self.assertLessEqual(len(' '.join(scenes[i-1]['speech'] for i in b)),4400)
 def test_oversized_scene_is_rejected(self):
  with self.assertRaises(ValueError):pack([{'speech':'x'*4500}],4400)
 def test_course_coverage_includes_every_field(self):
  scenes=json.loads((ROOT/'docs/lesson-pt.json').read_text());speech=' '.join(s['speech'] for s in scenes)
  data=runpy.run_path(str(REPO/'conteudo/modulos.py'))
  for module in data['MODULES']:
   for topic in module['topics']:
    for field in ['what','why','keys','example','action']:self.assertIn(' '.join(topic[field].split()),speech)
   for step in module['steps']:self.assertIn(' '.join(step.split()),speech)
   self.assertIn(module['check'],speech);self.assertIn(module['answer'],speech)
 def test_manifest_preserves_complete_order(self):
  scenes=json.loads((ROOT/'docs/lesson-pt.json').read_text());blocks=json.loads((ROOT/'blocos/manifest.json').read_text())
  self.assertEqual([i for b in blocks for i in b['scenes']],list(range(1,len(scenes)+1)))
  self.assertEqual(' '.join(Path(b['file']).read_text() for b in blocks),' '.join(s['speech'] for s in scenes))
 def test_prepare_refuses_inflight_manifest(self):
  import prepare
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'blocos').mkdir();(root/'blocos/manifest.json').write_text('[{"status":"submitting"}]')
   with patch.object(prepare,'ROOT',root),self.assertRaises(RuntimeError):prepare.prepare()
 def test_assembly_waits_for_missing_state(self):
  import assemble_languages
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'blocos').mkdir();(root/'blocos/manifest.json').write_text('[{"language":"pt","part":1}]')
   with patch.object(assemble_languages,'ROOT',root):self.assertIsNone(assemble_languages.assemble('pt'))
if __name__=='__main__':unittest.main()
