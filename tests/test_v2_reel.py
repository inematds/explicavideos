"""Testes do modo reel (2.4.3): perfil, abertura em "start", legenda curta, SRT sem sobreposição, mídia local."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine' / 'v2'))
import build_block as B  # noqa: E402

SCENES = [{'speech': 'A IA parou de esperar ordens. Você diz o destino e o agente trabalha por horas.'}]
WORDS = [{'word': w, 'start': i * 0.4, 'end': i * 0.4 + 0.35} for i, w in enumerate(SCENES[0]['speech'].split())]


class Reel(unittest.TestCase):
    def setUp(self):
        self.t = B.Timing(SCENES, WORDS)

    def test_profile_loads_from_makeshorts_contract(self):
        r = B.reel_of({'reel_profile': 'divulgacao'})
        self.assertEqual(r['captions']['max_words'], 3)
        self.assertEqual(r['duration']['max'], 59)
        self.assertIsNone(B.reel_of({'profile': '/perfil/heygen'}))   # "profile" do HeyGen não liga o reel

    def test_unknown_profile_is_error(self):
        with self.assertRaises(B.BuildError):
            B.reel_of({'reel_profile': 'viral-total'})

    def test_hook_at_start_is_frame_zero(self):
        spec = {'shots': [{'type': 'hook', 'at': 'start', 'text': 'A IA parou'},
                          {'type': 'keyword', 'at': 'Você diz', 'text': 'destino'}]}
        shots = B.resolve_scene(self.t, 0, 0.0, spec, [], 1, True)
        self.assertEqual(shots[0]['at'], 0.0)
        self.assertGreater(shots[1]['at'], 0.0)

    def test_captions_max_three_words(self):
        caps = B.captions(self.t, [0], [1], 10.0, max_words=3, max_chars=22)
        self.assertTrue(all(len(g['w']) <= 3 for g in caps))
        self.assertTrue(all(sum(len(w['w']) + 1 for w in g['w']) <= 23 or len(g['w']) == 1 for g in caps))

    def test_default_captions_unchanged_outside_reel(self):
        caps = B.captions(self.t, [0], [1], 10.0)
        self.assertTrue(any(len(g['w']) > 3 for g in caps))

    def test_srt_has_no_overlap(self):
        caps = B.captions(self.t, [0], [1], 10.0, max_words=3, max_chars=22)
        txt = B.srt(caps, 0.5)
        ts = [l.split(' --> ') for l in txt.splitlines() if '-->' in l]
        sec = lambda s: int(s[:2]) * 3600 + int(s[3:5]) * 60 + float(s[6:].replace(',', '.'))
        for (a1, b1), (a2, _) in zip(ts, ts[1:]):
            self.assertLessEqual(sec(b1), sec(a2) + 1e-6)

    def test_media_is_copied_and_video_refused(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            img = d / 'print.png'; img.write_bytes(b'\x89PNG fake')
            rel = B.copy_media(str(img), d / 'bloco', 1, 0)
            self.assertTrue(rel.startswith('assets/media/') and rel.endswith('-print.png'))
            self.assertTrue((d / 'bloco' / rel).exists())
            # mesmo nome em outra pasta não sobrescreve (nome leva hash do conteúdo)
            (d / 'b').mkdir(); img2 = d / 'b/print.png'; img2.write_bytes(b'\x89PNG outro')
            self.assertNotEqual(B.copy_media(str(img2), d / 'bloco', 1, 1), rel)
            mp4 = d / 'clip.mp4'; mp4.write_bytes(b'x')
            with self.assertRaises(B.BuildError):
                B.copy_media(str(mp4), d / 'bloco', 1, 0)
            with self.assertRaises(B.BuildError):
                B.copy_media(str(d / 'nao-existe.png'), d / 'bloco', 1, 0)

    def test_start_marker_only_for_hook(self):
        # "start" em shot que não é hook continua deixa comum (procura a palavra na fala) — fala sem "start" → erro
        spec = {'shots': [{'type': 'keyword', 'at': 'start', 'text': 'x'}]}
        with self.assertRaises(B.BuildError):
            B.resolve_scene(self.t, 0, 0.0, spec, [], 1, True)
        spec = {'shots': [{'type': 'hook', 'at': '@start', 'text': 'x'}]}
        self.assertEqual(B.resolve_scene(self.t, 0, 0.0, spec, [], 1, True)[0]['at'], 0.0)

    def test_effects_do_not_count_as_content_change(self):
        shots = [{'type': 'hook', 'at': 0.0, 'punch_at': 1.5}, {'type': 'keyword', 'at': 6.0, 'sub_at': 7.0}]
        self.assertEqual(B.all_times(shots, words=False, effects=False), [0.0, 6.0, 7.0])
        self.assertIn(1.5, B.all_times(shots, words=False))

    def test_srt_coincident_groups_merge(self):
        caps = [{'s': 1.0, 'e': 1.4, 'w': [{'w': 'a'}]}, {'s': 1.0, 'e': 1.8, 'w': [{'w': 'b'}]}, {'s': 2.0, 'e': 2.5, 'w': [{'w': 'c'}]}]
        txt = B.srt(caps, 0.5)
        self.assertEqual(txt.count('-->'), 2)
        self.assertIn('a b', txt)

    def test_reel_requires_vertical(self):
        with self.assertRaises(B.BuildError):
            B.reel_of({'reel_profile': 'divulgacao'}) and B.aspect_of({'aspect': '4:3'})

    def test_word_reveals_do_not_count_as_visual_change(self):
        shots = [{'type': 'statement', 'at': 0.5, 'wt': [1, 2, 3, 4, 5, 6, 7, 8]}]
        self.assertEqual(B.all_times(shots, words=False), [0.5])
        self.assertGreater(len(B.all_times(shots)), 1)


if __name__ == '__main__':
    unittest.main()
