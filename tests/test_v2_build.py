"""Testes do motor v2: resolução de deixas faladas, ordem, legendas com texto do roteiro."""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'engine' / 'v2'))
import build_block as B  # noqa: E402

SCENES = [
    {'speech': 'Bem-vindo ao OSWork completo. Eu sou Nei Maldaner. Vamos percorrer os oito módulos.'},
    {'speech': 'Módulo 1. Nosso objetivo é comparar modelos. Ao final, o exercício.'},
]
# transcrição com erros típicos de ASR ("Ossiwork", "Neymar O'Dunner", "8")
ASR = "Bem-vindo ao Ossiwork completo. Eu sou Neymar O'Dunner. Vamos percorrer os 8 módulos. Módulo 1. Nosso objetivo é comparar modelos. Ao final, o exercício."
WORDS = [{'word': w, 'start': i * 0.5, 'end': i * 0.5 + 0.4} for i, w in enumerate(ASR.split())]


class V2Build(unittest.TestCase):
    def setUp(self):
        self.t = B.Timing(SCENES, WORDS)

    def test_alignment_ratio(self):
        self.assertGreater(self.t.ratio, 0.8)

    def test_cue_resolves_to_spoken_time(self):
        gi, back = B.find_cue(self.t, 0, 'Vamos percorrer', self.t.bounds[0])
        self.assertFalse(back)
        self.assertAlmostEqual(self.t.t[gi], WORDS[ASR.split().index('Vamos')]['start'])

    def test_cue_ignores_case_and_accents(self):
        gi, _ = B.find_cue(self.t, 0, 'MODULOS', self.t.bounds[0])
        self.assertEqual(self.t.tokens[gi][0], 'módulos.')

    def test_missing_cue_is_error(self):
        with self.assertRaises(B.BuildError):
            B.find_cue(self.t, 0, 'frase que não existe', self.t.bounds[0])

    def test_strict_rejects_seconds(self):
        spec = {'shots': [{'type': 'keyword', 'at': 3.0, 'text': 'x'}]}
        with self.assertRaises(B.BuildError):
            B.resolve_scene(self.t, 0, 0.0, spec, [], 1, True)

    def test_unknown_type_rejected(self):
        with self.assertRaises(B.BuildError):
            B.resolve_scene(self.t, 0, 0.0, {'shots': [{'type': 'slide', 'at': 'Bem-vindo'}]}, [], 1, True)

    def test_nested_cues_and_order(self):
        spec = {'shots': [
            {'type': 'keyword', 'at': 'Bem-vindo', 'text': 'OSWORK', 'sub_at': 'Eu sou'},
            {'type': 'counter', 'at': 'Vamos percorrer', 'items': [{'value': 8, 'label': 'MÓDULOS', 'at': 'oito módulos'}]},
        ]}
        shots = B.resolve_scene(self.t, 0, 0.0, spec, [], 1, True)
        self.assertLess(shots[0]['at'], shots[0]['sub_at'])
        self.assertLess(shots[1]['at'], shots[1]['items'][0]['at'])

    def test_scene_relative_times(self):
        s0 = self.t.t[self.t.bounds[1]]
        shots = B.resolve_scene(self.t, 1, s0, {'shots': [{'type': 'keyword', 'at': 'Módulo 1', 'text': '1'}]}, [], 7, True)
        self.assertAlmostEqual(shots[0]['at'], 0.0, places=3)

    def test_captions_use_script_spelling(self):
        caps = B.captions(self.t, [0.0], [1, 2], 20.0)
        text = ' '.join(w['w'] for g in caps for w in g['w'])
        self.assertIn('Nei Maldaner.', text)
        self.assertIn('OSWork', text)
        self.assertNotIn('Neymar', text)

    def test_statement_word_times_follow_speech(self):
        gi, _ = B.find_cue(self.t, 0, 'Vamos percorrer', self.t.bounds[0])
        wt = B.word_times(self.t, 0, 'os **oito** módulos', gi, 0.0)
        self.assertEqual(len(wt), 3)
        self.assertEqual(wt, sorted(wt))


if __name__ == '__main__':
    unittest.main()
