"""2.34.12 (Nei 20/11/2026, EV#187–191): o portão do material e do plano barra o "guia de ícones" com a foto real
sumindo aos 30 s, antes do avatar (plano) e antes do render (visual). Sem vídeo real: composições sintéticas."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

V2 = Path(__file__).resolve().parents[1] / 'engine/v2'
sys.path.insert(0, str(V2))
import checar_material as CM  # noqa: E402


def saida_visual(d, cenas):
    """cenas = [(dur, [(at, type, src)])] → v2/verification/build + final/pt-b01/compositions como o build grava."""
    s = Path(d) / 'v2'
    (s / 'verification').mkdir(parents=True)
    comp = s / 'final/pt-b01/compositions'
    comp.mkdir(parents=True)
    t0, rel = 0.0, []
    for n, (dur, shots) in enumerate(cenas, 1):
        rel.append({'scene': n, 'start': t0, 'dur': dur, 'shots': []})
        js = {'n': n, 'dur': dur, 'shots': [{'type': t, 'at': a, **({'src': f'assets/media/0123456789-{x}'} if x else {})}
                                             for a, t, x in shots]}
        (comp / f'scene-{n:03d}.html').write_text(f'<script>V2.scene("scene-{n:03d}", {json.dumps(js)});</script>')
        t0 += dur
    (s / 'verification/build-v2-pt-b01.json').write_text(json.dumps({'scenes': rel}))
    return s


def roda(*a, **env):
    e = {k: v for k, v in os.environ.items() if k != 'MATERIAL_SEGUE'}
    e.update(env)
    return subprocess.run([sys.executable, str(V2 / 'checar_material.py'), *map(str, a)], capture_output=True, text=True,
                          env=e, timeout=60)


class Nomes(unittest.TestCase):
    def test_raiz_do_nome(self):
        self.assertEqual(CM.nome_base('assets/media/85badcaecd-facebook-1.jpg'), 'facebook-1')
        self.assertEqual(CM.nome_base('assets/media/0123456789-02-facebook-1.poster.jpg'), 'facebook-1')
        self.assertTrue(CM.eh_real('x/clipe-3.mp4', None))
        self.assertFalse(CM.eh_real('x/abrigo.png', None))


class Visual(unittest.TestCase):
    def test_guia_de_icones_reprova(self):
        # o padrão dos tornados: foto real só nos primeiros 25 s, depois 135 s de ilustração e peça de código
        with tempfile.TemporaryDirectory() as d:
            cenas = [(25, [(0, 'foto', 'facebook-1.jpg'), (12, 'foto', 'facebook-4.jpg')])]
            cenas += [(20, [(0, 'foto', f'ilustra-{i}.png'), (10, 'bignum', None)]) for i in range(7)]
            r = roda('visual', saida_visual(d, cenas))
            self.assertEqual(r.returncode, 1, r.stdout)
            self.assertIn('o real some aos', r.stdout)
            self.assertIn('seguidos sem material real', r.stdout)

    def test_real_espalhado_passa(self):
        with tempfile.TemporaryDirectory() as d:
            cenas = [(16, [(0, 'foto', f'real-0{i}-a.jpg'), (8, 'foto', f'gerada-{i}.png')]) for i in range(1, 6)]
            r = roda('visual', saida_visual(d, cenas))
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn('visual ok', r.stdout)

    def test_escape_do_nei(self):
        with tempfile.TemporaryDirectory() as d:
            cenas = [(60, [(0, 'foto', 'facebook-1.jpg'), (5, 'bignum', None)])]
            r = roda('visual', saida_visual(d, cenas), MATERIAL_SEGUE='1')
            self.assertEqual(r.returncode, 0)
            self.assertIn('MATERIAL_SEGUE', r.stdout)


def pasta_plano(d, trechos, fala_chars=1300, itens=2, pedida=None, fonte=''):
    p = Path(d)
    (p / 'roteiro-pt.json').write_text(json.dumps([{'speech': 'a' * fala_chars}]))
    (p / 'pedido.json').write_text(json.dumps({'perfil': 'viral'}))
    (p / 'material.json').write_text(json.dumps({'pedido_tem_material': True, 'itens': [
        {'arquivo': f'/m/real-0{i}-x.jpg', 'tipo': 'foto', 'real': True} for i in range(1, itens + 1)]}))
    (p / 'plano.json').write_text(json.dumps({'duracao_alvo_s': 72, 'duracao_pedida_s': pedida,
                                              'duracao_pedida_fonte': fonte, 'trechos': trechos}))
    return p


def t(origem, arq=None):
    return {'deixa': 'frase', 'tela': 'algo', 'origem': origem, 'arquivos': [arq] if arq else []}


class Plano(unittest.TestCase):
    BOM = [t('real', '/m/real-01-x.jpg'), t('codex'), t('real', '/m/real-02-x.jpg'), t('codigo'), t('codex'),
           t('real', '/m/real-01-x.jpg')]

    def test_plano_bom_passa(self):
        with tempfile.TemporaryDirectory() as d:
            r = roda('plano', pasta_plano(d, self.BOM))
            self.assertEqual(r.returncode, 0, r.stdout)

    def test_fala_longa_reprova(self):
        # 3.095 caracteres (EV#191) ≈ 172 s > teto 100 s
        with tempfile.TemporaryDirectory() as d:
            r = roda('plano', pasta_plano(d, self.BOM, fala_chars=3095))
            self.assertEqual(r.returncode, 1)
            self.assertIn('teto 100 s', r.stdout)

    def test_duracao_do_lead_sem_fonte_reprova(self):
        with tempfile.TemporaryDirectory() as d:
            r = roda('plano', pasta_plano(d, self.BOM, fala_chars=3000, pedida=170))
            self.assertEqual(r.returncode, 1)
            self.assertIn('frase do NEI', r.stdout)

    def test_real_so_no_comeco_reprova(self):
        with tempfile.TemporaryDirectory() as d:
            ruim = [t('real', '/m/real-01-x.jpg'), t('real', '/m/real-02-x.jpg')] + [t('codex')] * 6
            r = roda('plano', pasta_plano(d, ruim))
            self.assertEqual(r.returncode, 1)
            self.assertIn('último quarto', r.stdout)

    def test_pedido_com_link_sem_material_reprova(self):
        with tempfile.TemporaryDirectory() as d:
            r = roda('plano', pasta_plano(d, [t('codex')] * 6, itens=0))
            self.assertEqual(r.returncode, 1)
            self.assertIn('peça o arquivo ao Nei', r.stdout)

    def test_sem_plano_sai_2(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(roda('plano', d).returncode, 2)


if __name__ == '__main__':
    unittest.main()
