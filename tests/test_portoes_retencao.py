"""2.27.11 (Nei 13/11/2026, "aplica"): os portões da Retenção barram. Sem claude -p (crítica em cache) e sem vídeo real."""
import hashlib, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

V2 = Path(__file__).resolve().parents[1] / 'engine/v2'
sys.path.insert(0, str(V2))
import critico_chamada as CC  # noqa: E402


def pasta_com_critica(d, nota, sim=True):
    p = Path(d)
    (p / 'roteiro-pt.json').write_text(json.dumps([{'speech': 'Você perde uma semana por mês.', 'labels': ['VOCÊ PERDE UMA SEMANA']}]))
    fala = 'Você perde uma semana por mês.'
    pedido = CC.PEDIDO.format(titulo='(sem título ainda)', manchete='VOCÊ PERDE UMA SEMANA', abertura=fala, fala=fala,
                              nucleo='(sem chamada.json)', metodo='nenhum')
    c = {k: sim for k in CC.PERGUNTAS}
    c.update(nota=nota, resumo='teste', hash=hashlib.sha1(pedido.encode()).hexdigest())
    (p / 'chamada-critica.json').write_text(json.dumps(c))
    return p


def roda(p, **env):
    e = {k: v for k, v in os.environ.items() if k != 'CRITICO_SEGUE'}
    e.update(env)
    return subprocess.run([sys.executable, str(V2 / 'critico_chamada.py'), str(p)], capture_output=True, text=True, env=e, timeout=60)


class CriticoBarra(unittest.TestCase):
    def test_nota_baixa_barra(self):
        with tempfile.TemporaryDirectory() as d:
            r = roda(pasta_com_critica(d, 5))
            self.assertEqual(r.returncode, 1)
            self.assertIn('chamada fraca: reescreva com outro gatilho (ver PADRAO-VIRAL Retenção)', r.stdout)

    def test_pergunta_nao_barra(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(roda(pasta_com_critica(d, 8, sim=False)).returncode, 1)

    def test_escape_consciente(self):
        with tempfile.TemporaryDirectory() as d:
            r = roda(pasta_com_critica(d, 5), CRITICO_SEGUE='1')
            self.assertEqual(r.returncode, 0)
            self.assertIn('CRITICO_SEGUE=1', r.stdout)

    def test_nota_boa_passa(self):
        with tempfile.TemporaryDirectory() as d:
            r = roda(pasta_com_critica(d, 8))
            self.assertEqual(r.returncode, 0)
            self.assertIn('chamada forte', r.stdout)


class QaAreaLisa(unittest.TestCase):
    """vídeo sintético: fundo preto com um retângulo de ruído (~1/4 da tela) que anda: não é 'vazio' (> 90%) nem
    'parado', mas ~75% do quadro é liso o tempo todo"""

    def video(self, d, w, h):
        f = Path(d) / f'liso-{w}x{h}.mp4'
        bw, bh = w // 2, h // 2
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', f'color=c=black:s={w}x{h}:d=8:r=10',
                        '-f', 'lavfi', '-i', f"nullsrc=s={bw}x{bh}:d=8:r=10,geq=lum='random(1)*255':cb=128:cr=128",
                        '-filter_complex', f"[0][1]overlay=x='mod(t*{w // 8},{w - bw})':y={h // 4}:shortest=1",
                        '-pix_fmt', 'yuv420p', str(f)], check=True)
        return f

    def test_liso_reprova_16x9_e_avisa_9x16(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, str(V2 / 'qa_viral.py'), str(self.video(d, 640, 360)), f'--saida={d}'],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn('área lisa em', r.stdout)
            rel = json.loads(Path(d, 'qa-viral-liso-640x360.json').read_text())
            self.assertGreater(rel['liso_pct'], 0.5)
            r = subprocess.run([sys.executable, str(V2 / 'qa_viral.py'), str(self.video(d, 360, 640)), f'--saida={d}'],
                               capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn('no 9:16 só avisa', r.stdout)


if __name__ == '__main__':
    unittest.main()
