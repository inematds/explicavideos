"""Portões do render (2.4.5): QA por bloco que bloqueia de verdade, recibo preso aos insumos, strict exigido no reel."""
import json, os, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine'))
import render_guard as G  # noqa: E402


def qa_report(tmp, checks):
    p = Path(tmp) / 'qa.json'
    p.write_text(json.dumps({'ok': not any(c[0] == 'FALHA' for c in checks),
                             'checks': [{'status': s, 'item': i, 'detalhe': ''} for s, i in checks]}))
    return p


class QA(unittest.TestCase):
    def test_duration_only_failure_is_tolerated_per_block(self):
        with tempfile.TemporaryDirectory() as t:
            p = qa_report(t, [('OK', 'fps'), ('FALHA', 'duração')])
            self.assertEqual(G.qa_blocking(p, ignore_duration=True), [])

    def test_other_failure_blocks_even_with_many_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            p = qa_report(t, [('FALHA', 'fps'), ('FALHA', 'duração')])
            self.assertEqual(G.qa_blocking(p, ignore_duration=True), ['fps'])

    def test_duration_blocks_whole_video(self):
        with tempfile.TemporaryDirectory() as t:
            p = qa_report(t, [('FALHA', 'duração')])
            self.assertEqual(G.qa_blocking(p, ignore_duration=False), ['duração'])

    def test_missing_or_broken_report_blocks(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertTrue(G.qa_blocking(Path(t) / 'nao-existe.json', ignore_duration=True))
            bad = Path(t) / 'bad.json'
            bad.write_text('{')
            self.assertTrue(G.qa_blocking(bad, ignore_duration=True))


class Fingerprint(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        d = Path(self.t.name)
        self.proj = d / 'pt-b01'
        (self.proj / 'compositions').mkdir(parents=True)
        (self.proj / 'assets').mkdir()
        (self.proj / 'index.html').write_text('<html>v1</html>')
        (self.proj / 'compositions/scene-001.html').write_text('cena 1')
        (self.proj / 'captions.srt').write_text('1\n00:00:00,000 --> 00:00:01,000\nOi\n')
        self.avatar = d / 'nei-pt-b01.mp4'
        self.avatar.write_bytes(b'x' * 100)
        (self.proj / 'assets/avatar.mp4').symlink_to(self.avatar)
        self.params = {'fps': '30', 'reel': 'divulgacao', 'hyperframes': '0.8.77'}

    def tearDown(self):
        self.t.cleanup()

    def test_stable(self):
        self.assertEqual(G.fingerprint(self.proj, self.params), G.fingerprint(self.proj, self.params))

    def test_changes_with_script(self):
        a = G.fingerprint(self.proj, self.params)
        (self.proj / 'compositions/scene-001.html').write_text('cena 1 com roteiro novo')
        self.assertNotEqual(a, G.fingerprint(self.proj, self.params))

    def test_changes_with_reel_mode(self):
        a = G.fingerprint(self.proj, self.params)
        self.assertNotEqual(a, G.fingerprint(self.proj, {**self.params, 'reel': None, 'fps': '25'}))

    def test_changes_with_new_avatar(self):
        a = G.fingerprint(self.proj, self.params)
        self.avatar.write_bytes(b'y' * 120)
        self.assertNotEqual(a, G.fingerprint(self.proj, self.params))

    def test_reuse_needs_matching_fingerprint(self):
        out = Path(self.t.name) / 'pt-b01.mp4'
        out.write_bytes(b'mp4')
        fp = G.fingerprint(self.proj, self.params)
        self.assertTrue(G.can_reuse({'status': 'rendered', 'fingerprint': fp}, out, fp))
        self.assertFalse(G.can_reuse({'status': 'rendered'}, out, fp))            # recibo antigo, sem impressão
        self.assertFalse(G.can_reuse({'status': 'rendered', 'fingerprint': 'outro'}, out, fp))
        self.assertFalse(G.can_reuse({'status': 'qa_failed', 'fingerprint': fp}, out, fp))
        out.unlink()
        self.assertFalse(G.can_reuse({'status': 'rendered', 'fingerprint': fp}, out, fp))


class Strict(unittest.TestCase):
    def test_reel_requires_strict_validation(self):
        self.assertIn('strict', G.build_problem({'warnings': [], 'validation': {'strict': False, 'ok': False}}, reel=True))
        self.assertIn('strict', G.build_problem({'warnings': []}, reel=True))         # build antigo
        self.assertIsNone(G.build_problem({'warnings': [], 'validation': {'strict': True, 'ok': True}}, reel=True))

    def test_fallback_still_blocks_outside_reel(self):
        self.assertIn('fallback', G.build_problem({'warnings': ['cena 3: sem roteiro visual (fallback)']}, reel=False))
        self.assertIsNone(G.build_problem({'warnings': ['cena 3: 12s sem mudança visual']}, reel=False))


class Producer(unittest.TestCase):
    """produce.py de verdade, num diretório falso; o render é trocado por um 'npx' que falha se for chamado."""
    PRODUCE = Path(__file__).resolve().parents[1] / 'engine/v2/produce.py'

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        r = self.root = Path(self.t.name) / 'out'
        for d in ('verification', 'blocos', 'final/pt-b01/compositions', 'logs', 'bin'):
            (r / d).mkdir(parents=True)
        (r / 'blocos/manifest.json').write_text(json.dumps([{'language': 'pt', 'part': 1, 'scenes': [1]}]))
        (r / 'verification/blocos-downloads.json').write_text(json.dumps({'pt-b01': {'duration': 1.0}}))
        (r / 'final/pt-b01/index.html').write_text('v1')
        (r / 'final/pt-b01.mp4').write_bytes(b'mp4 antigo')
        npx = r / 'bin/npx'
        npx.write_text('#!/bin/sh\necho RENDER_CHAMADO >&2\nexit 9\n')
        npx.chmod(0o755)
        self.env = {**os.environ, 'PATH': f'{r / "bin"}:{os.environ["PATH"]}'}

    def tearDown(self):
        self.t.cleanup()

    def run_produce(self, reel, report):
        cfg = Path(self.t.name) / 'cfg.json'
        cfg.write_text(json.dumps({'output': str(self.root), 'languages': ['pt'], **({'reel_profile': 'divulgacao'} if reel else {})}))
        (self.root / 'verification/build-v2-pt-b01.json').write_text(json.dumps(report))
        import subprocess
        return subprocess.run([sys.executable, str(self.PRODUCE)], env={**self.env, 'EXPLICAVIDEOS_CONFIG': str(cfg)},
                              capture_output=True, text=True)

    def state(self, rec):
        (self.root / 'verification/production.json').write_text(json.dumps({'pt-b01': rec}))

    def test_current_receipt_is_skipped_without_render(self):
        report = {'warnings': []}
        rf = json.dumps(report).encode()
        fp = G.fingerprint(self.root / 'final/pt-b01', {'fps': '25', 'reel': None, 'hyperframes': '0.8.77',
                                                       'build_report': G.hashlib.sha256(rf).hexdigest()})
        self.state({'status': 'rendered', 'fingerprint': fp})
        r = self.run_produce(False, report)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse((self.root / 'logs/render-pt-b01.log').exists())

    def test_changed_script_renders_again(self):
        self.state({'status': 'rendered', 'fingerprint': 'impressao-de-antes-da-mudanca'})
        r = self.run_produce(False, {'warnings': []})
        # tentou renderizar de novo: o npx falso grava a marca no log do render e sai com 9
        self.assertIn('RENDER_CHAMADO', (self.root / 'logs/render-pt-b01.log').read_text())
        self.assertIn('exit status 9', r.stderr)

    def test_reel_refuses_build_without_strict(self):
        r = self.run_produce(True, {'warnings': [], 'validation': {'strict': False, 'ok': False}})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('strict', r.stderr)
        self.assertFalse((self.root / 'logs/render-pt-b01.log').exists())


if __name__ == '__main__':
    unittest.main()
