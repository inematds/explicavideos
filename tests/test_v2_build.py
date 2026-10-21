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

    def test_frame_default_is_16_9(self):
        self.assertEqual(B.frame({}), (1920, 1080, ''))
        self.assertEqual(B.frame({'aspect': '16:9'}), (1920, 1080, ''))

    def test_frame_9_16_vertical(self):
        self.assertEqual(B.frame({'aspect': '9:16'}), (1080, 1920, 'v916'))
        with self.assertRaises(B.BuildError):
            B.frame({'aspect': '4:3'})

    def test_templates_carry_frame_placeholders(self):
        self.assertIn('data-width="__W__" data-height="__H__"', B.INDEX)
        self.assertIn('class="__MODE__"', B.INDEX)
        self.assertIn('class="v2-scene {mode}"', B.SCENE)
        self.assertIn('class="v2-fit"', B.SCENE)

    def test_statement_word_times_follow_speech(self):
        gi, _ = B.find_cue(self.t, 0, 'Vamos percorrer', self.t.bounds[0])
        wt = B.word_times(self.t, 0, 'os **oito** módulos', gi, 0.0)
        self.assertEqual(len(wt), 3)
        self.assertEqual(wt, sorted(wt))


if __name__ == '__main__':
    unittest.main()


class V2Diagrama(unittest.TestCase):
    """diagrama (2.14): deixas aninhadas resolvidas, refs checadas, passos contam no ritmo."""
    def setUp(self):
        self.t = B.Timing(SCENES, WORDS)

    def spec(self, **extra):
        sh = {'type': 'diagrama', 'at': 'Bem-vindo',
              'nos': [{'id': 'a', 'label': 'OSWORK', 'at': 'Bem-vindo'}, {'id': 'b', 'label': 'NEI', 'at': 'Eu sou'}],
              'ligacoes': [{'de': 'a', 'para': 'b', 'at': 'Eu sou'}],
              'passos': [{'at': 'Vamos percorrer', 'foco': 'b', 'pacote': {'de': 'a', 'para': 'b', 'texto': 'x'}},
                         {'at': 'oito módulos', 'estado': {'a': 'ok'}, 'nota': {'no': 'a', 'texto': 'oito'}}]}
        sh.update(extra)
        return sh

    def resolve(self, sh):
        shots = B.resolve_scene(self.t, 0, 0.0, {'shots': [sh]}, [], 1, True)
        w = []
        B.check_diagrama(shots[0], 1, 0, w)
        return shots[0], w

    def test_ok_and_steps_count_for_rhythm(self):
        sh, w = self.resolve(self.spec())
        self.assertEqual(w, [])
        ts = B.all_times([sh], words=False, effects=False)
        self.assertIn(sh['passos'][1]['at'], ts)
        self.assertGreater(sh['passos'][1]['at'], sh['passos'][0]['at'])

    def test_bad_refs_rejected(self):
        for bad in ({'ligacoes': [{'de': 'a', 'para': 'zz', 'at': 'Eu sou'}]},
                    {'passos': [{'at': 'Eu sou', 'foco': 'zz'}]},
                    {'passos': [{'at': 'Eu sou', 'pacote': {'de': 'b', 'para': 'zz'}}]},
                    {'nos': [{'id': 'a', 'label': 'X', 'at': 'Bem-vindo'}, {'id': 'a', 'label': 'Y', 'at': 'Eu sou'}]}):
            with self.assertRaises(B.BuildError):
                self.resolve(self.spec(**bad))

    def test_long_label_warns(self):
        _, w = self.resolve(self.spec(nos=[{'id': 'a', 'label': 'UM RÓTULO COMPRIDO DEMAIS AQUI', 'at': 'Bem-vindo'},
                                           {'id': 'b', 'label': 'NEI', 'at': 'Eu sou'}]))
        self.assertTrue(any('22 caracteres' in x for x in w))


class Interface(unittest.TestCase):
    """Perfil interface (2.15): tokens, probs, arcos e etapas — deixas resolvidas e referências conferidas."""

    def setUp(self):
        self.t = B.Timing(SCENES, WORDS)

    def resolve(self, sh):
        shots = B.resolve_scene(self.t, 0, 0.0, {'shots': [sh]}, [], 1, True)
        w = []
        B.check_iface(shots[0], 1, 0, w)
        return shots[0], w

    def test_types_registered(self):
        self.assertTrue({'tokens', 'probs', 'arcos', 'etapas'} <= B.SHOT_TYPES)

    def test_tokens_cues_and_pieces(self):
        sh, w = self.resolve({'type': 'tokens', 'at': 'Bem-vindo', 'linhas': [
            {'texto': 'strawberry', 'pedacos': ['str', 'aw', 'berry'], 'at': 'Bem-vindo', 'corta_at': 'Eu sou', 'ids_at': 'Vamos percorrer'}]})
        ln = sh['linhas'][0]
        self.assertEqual(w, [])
        self.assertLess(ln['at'], ln['corta_at'])
        self.assertLess(ln['corta_at'], ln['ids_at'])
        self.assertIn(ln['corta_at'], B.all_times([sh], words=False, effects=False))
        with self.assertRaises(B.BuildError):   # pedaços que não formam o texto
            self.resolve({'type': 'tokens', 'at': 'Bem-vindo', 'linhas': [{'texto': 'abc', 'pedacos': ['a', 'x'], 'at': 'Bem-vindo'}]})

    def test_probs_sum_and_range(self):
        ok = {'type': 'probs', 'at': 'Bem-vindo', 'contexto': 'A capital é', 'opcoes': [{'texto': 'A', 'p': 0.6}, {'texto': 'B', 'p': 0.3}], 'escolhe_at': 'Eu sou'}
        sh, w = self.resolve(ok)
        self.assertEqual(w, [])
        for bad in ([{'texto': 'A', 'p': 0.8}, {'texto': 'B', 'p': 0.5}], [{'texto': 'A', 'p': 0.5}]):
            with self.assertRaises(B.BuildError):
                self.resolve(dict(ok, opcoes=bad))

    def test_arcos_words_must_exist(self):
        base = {'type': 'arcos', 'at': 'Bem-vindo', 'frase': 'sentei no banco perto do rio',
                'passos': [{'at': 'Eu sou', 'foco': 'banco', 'arcos': [{'para': 'rio', 'peso': 0.9}]},
                           {'at': 'Vamos percorrer', 'frase': 'pedi no banco um empréstimo', 'foco': 'banco', 'arcos': [{'para': 'emprestimo', 'peso': 0.9}]}]}
        _, w = self.resolve(base)
        self.assertEqual(w, [])
        bad = json_copy(base); bad['passos'][1]['arcos'][0]['para'] = 'rio'   # "rio" não está na frase trocada
        with self.assertRaises(B.BuildError):
            self.resolve(bad)

    def test_etapas_atual_range(self):
        _, w = self.resolve({'type': 'etapas', 'at': 'Bem-vindo', 'itens': ['A', 'B', 'C'], 'atual': 2})
        self.assertEqual(w, [])
        with self.assertRaises(B.BuildError):
            self.resolve({'type': 'etapas', 'at': 'Bem-vindo', 'itens': ['A', 'B', 'C'], 'atual': 4})


def json_copy(o):
    import json
    return json.loads(json.dumps(o))
