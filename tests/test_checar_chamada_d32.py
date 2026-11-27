"""D32 (D20 revista, 27/11/2026): público que já sabe → dor pelo outro lado."""
import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "v2"))
from checar_chamada import checar

ROT = [{"speech": "Pare de perder tokens. Você vai ver o passo a passo do método Poupa Token agora."},
       {"speech": "O método Poupa Token corta o desperdício."},
       {"speech": "Quanto você gasta por dia? Está grátis no inema ponto club."}]


def rodar(**ch):
    base = {"dor_ou_desejo": "desejo", "quem": "você", "nucleo": "você para de perder tokens",
            "por_que_importa": "o limite acaba", "metodo": "Poupa Token", "formato": "fim_da_perda"}
    base.update(ch)
    with tempfile.TemporaryDirectory() as d:
        Path(d, "roteiro-pt.json").write_text(json.dumps(ROT))
        Path(d, "chamada.json").write_text(json.dumps({k: v for k, v in base.items() if v is not None}))
        Path(d, "yt.txt").write_text("Pare de perder tokens com o Poupa Token\n")
        return checar(d)


class D32(unittest.TestCase):
    def test_sabe_com_perda_virada_passa(self):
        e, _ = rodar(publico_ja_sabe="sim")
        self.assertEqual(e, [])

    def test_sabe_com_dor_descrita_barra(self):
        e, _ = rodar(publico_ja_sabe="sim", dor_ou_desejo="dor", formato="acusacao")
        self.assertTrue(any("outro lado" in x for x in e), e)

    def test_sabe_com_dor_justificada_passa(self):
        e, _ = rodar(publico_ja_sabe="sim", dor_ou_desejo="dor", formato="perda", por_que_dor="caso real do Nei")
        self.assertEqual(e, [])

    def test_leigo_com_dor_passa(self):
        e, _ = rodar(publico_ja_sabe="nao", dor_ou_desejo="dor", formato="perda")
        self.assertEqual(e, [])

    def test_sem_campo_so_avisa(self):
        e, a = rodar(publico_ja_sabe=None, dor_ou_desejo="dor", formato="acusacao")
        self.assertEqual(e, [])
        self.assertTrue(any("publico_ja_sabe" in x for x in a), a)

    def test_valor_invalido(self):
        e, _ = rodar(publico_ja_sabe="talvez")
        self.assertTrue(any("'sim' ou 'nao'" in x for x in e), e)


if __name__ == "__main__":
    unittest.main()
