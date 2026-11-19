"""2.33.12 (Nei 19/11/2026): qa_viral julga o apelo (manchete nos 3 s, assunto na tela, públicos) e barra. Juiz trocado por stub."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

V2 = Path(__file__).resolve().parents[1] / 'engine/v2'
BOM = {"manchete_lida": "QUAL DOS 3 GEMINI USAR?", "manchete_3s": True, "manchete_para": True, "assunto_visivel": True,
       "impacto_visual": True, "fala_forte": True, "compensa": True, "retencao": True, "engajamento": True,
       "publicos": {"canal": True, "jovem": True, "executivo": True, "dona_de_casa": False},
       "imagens_fracas": [], "nota": 8, "manchete_melhor": "", "resumo": "para e segura"}


class QaViral(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = tempfile.mkdtemp()
        cls.mp4 = Path(cls.d, 'v.mp4')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=s=360x640:d=6:r=10',
                        '-pix_fmt', 'yuv420p', str(cls.mp4)], check=True)
        cls.stub = Path(cls.d, 'stub.py')
        cls.stub.write_text('import os; print(os.environ["VEREDITO"])\n')

    def roda(self, veredito, saida, **env):
        e = {k: v for k, v in os.environ.items() if k not in ('VIRAL_SEGUE', 'QA_VIRAL_APELO')}
        e.update(QA_VIRAL_CMD=f'{sys.executable} {self.stub}', VEREDITO=json.dumps(veredito), VIRAL_VOTOS='3', **env)
        return subprocess.run([sys.executable, str(V2 / 'qa_viral.py'), str(self.mp4), f'--saida={saida}', '--tremida-max=999',
                               '--teto-liso=1'], capture_output=True, text=True, env=e, timeout=180)

    def test_aprova_com_manchete_que_para(self):
        with tempfile.TemporaryDirectory() as s:
            r = self.roda(BOM, s)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn('APROVADO no apelo', r.stdout)
            q = json.loads(Path(self.d, 'v.mp4.qa.json').read_text())
            self.assertTrue(q['viral']['ok'])
            self.assertTrue(Path(s, 'abertura-v.jpg').exists() and Path(s, 'folha-v.jpg').exists())

    def test_reprova_sem_manchete_nos_3s(self):
        with tempfile.TemporaryDirectory() as s:
            r = self.roda({**BOM, 'manchete_3s': False, 'manchete_lida': ''}, s)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn('manchete_3s', r.stdout)
            self.assertFalse(json.loads(Path(self.d, 'v.mp4.qa.json').read_text())['ok'])

    def test_reprova_imagem_generica_e_poucos_publicos(self):
        with tempfile.TemporaryDirectory() as s:
            v = {**BOM, 'assunto_visivel': False, 'publicos': {"canal": True, "jovem": False, "executivo": False, "dona_de_casa": False}}
            r = self.roda(v, s)
            self.assertEqual(r.returncode, 1)
            self.assertIn('assunto_visivel', r.stdout)
            self.assertIn('só 1 de 4 públicos', r.stdout)

    def test_juiz_mudo_nao_aprova_e_escape(self):
        with tempfile.TemporaryDirectory() as s:
            self.assertEqual(self.roda('nada', s).returncode, 2)
        with tempfile.TemporaryDirectory() as s:
            self.assertEqual(self.roda('nada', s, VIRAL_SEGUE='1').returncode, 0)

    def test_so_tecnico(self):
        with tempfile.TemporaryDirectory() as s:
            r = self.roda({**BOM, 'manchete_3s': False}, s, QA_VIRAL_APELO='0')
            self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == '__main__':
    unittest.main()
