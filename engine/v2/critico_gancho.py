#!/usr/bin/env python3
"""Crítico do GANCHO + PROMESSA (Nei, 20/11/2026), em MODO SOMBRA: grava a nota, não barra nada.

Pedido do Nei: "a capa, os 5 primeiros segundos, a chamada viral (fazer as pessoas pararem e querer ver o vídeo) é o
que falha, mesmo que passe na crítica. Isso é fundamental o revisor garantir." Análise com Astra e Fable
(~/projetos/wifi/revisor-pesos-2026-11-20/SINTESE.md): o critico_chamada.py não vê imagem, não julga os 5 s, lê a fala
inteira antes de julgar o começo e reprova quase sempre pelo corpo (65 de 66 notas baixas elogiam a abertura).

Dois vereditos separados, cada um com 3 leituras em paralelo (CRITICO_VOTOS):
  GANCHO (portão principal). Juiz CEGO: recebe só o que o feed mostra — título, texto da capa, 1ª frase (~5 s) e o
  resto dos ~15 s. Nunca a fala inteira, o fecho ou o núcleo do autor. Com --entrega (pasta com os mp4 e thumb.jpg),
  também olha o quadro 0 e o quadro de 3 s de cada formato e a thumb. Pesos aprovados pelo Nei (20/11):
      capa 25 · primeira frase 30 · título 15 · público 15 · 5 a 15 s 15
  Cada aspecto 0 (falha), 1 (passa) ou 2 (forte), mediana das leituras. Nota = soma(peso × pontos) / 2, de 0 a 100.
  Passa com nota ≥ 70 e capa e 1ª frase com pelo menos 1 ponto.
  PROMESSA. Lê a fala inteira. Só BLOQUEIA fato falso/exagerado e título/abertura em pergunta sem resposta no fecho.
  Prova e entrega fracas não reprovam o gancho: viram uma ordem de correção que aponta ONDE consertar (corpo,
  pesquisa), nunca "só na abertura". Jargão e catálogo viram sugestão.

Uso: critico_gancho.py <pasta> [--entrega <pasta-com-mp4>] [--barrar]
  Lê roteiro-pt.json, yt.txt e pedido.json da pasta (a persona do canal vem do critico_chamada.py, D29).
  Grava <pasta>/gancho-critica.json. Sem --barrar sai sempre 0 (sombra); com --barrar sai 1 se não passou.
"""
import argparse
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from critico_chamada import abertura, persona_de   # noqa: E402  (mesma persona por canal e mesmo corte dos 15 s)

VOTOS = max(1, int(os.environ.get("CRITICO_VOTOS", "3")))
PESOS = {"capa": 25, "frase": 30, "titulo": 15, "publico": 15, "escada": 15}
MINIMO = 70
SEM_ZERO = ("capa", "frase")

GANCHO = """Você é {persona}. Está rolando o feed no celular, com pressa. Você NÃO sabe nada deste vídeo além do que
está abaixo: é exatamente o que o feed mostra antes de você decidir parar ou passar.

TÍTULO: {titulo}
TEXTO DA CAPA (o que está escrito no 1º quadro, um item por linha):
{capa}
PRIMEIRA FRASE FALADA (~5 primeiros segundos): {frase}
O QUE VEM DEPOIS, ATÉ ~15 s: {resto}
{imagens}
A isca faz parte do jogo: provocação forte é bom se for verdade. Julgue cada aspecto com 0 (falha: eu passo direto),
1 (passa: eu paro) ou 2 (forte: eu não consigo não ver):
- capa: em 1 segundo, sem som, entendo QUEM e O QUÊ, e é do meu mundo? Texto enigmático, sem sujeito ou imagem que
  não diz nada = 0.{capa_img}
- frase: a 1ª frase me dá um motivo para ficar (dor, perda, desejo, surpresa) em frase de gente? Slogan comprimido,
  frase morna de introdução ("hoje vamos falar"), tese abstrata = 0.
- titulo: o título promete o mesmo que a capa, claro e concreto, e me faz querer a resposta?
- publico: é dor ou desejo de alguém como eu, não assunto técnico dos outros?
- escada: de 5 a 15 s, cada frase aumenta o peso da anterior (prova, agrava, promete para mim), sem abrir outro assunto,
  e eu sei o que ganho ou perco?
Para cada aspecto diga o motivo em uma frase e, se for 0 ou 1, o conserto concreto (o texto novo, não um conselho).

Responda SÓ com JSON numa linha:
{{"capa": {{"pontos": 0, "motivo": "", "conserto": ""}}, "frase": {{...}}, "titulo": {{...}}, "publico": {{...}},
"escada": {{...}}, "pararia": true|false, "resumo": "<uma frase: eu paro ou passo, e por quê>"}}"""

IMAGENS = """
IMAGENS (abra cada uma com a ferramenta Read e olhe como no celular, sem som):
{lista}
"""

PROMESSA = """Você é {persona}. Você assistiu a este vídeo inteiro.

TÍTULO: {titulo}
TEXTO DA CAPA: {capa}
FALA COMPLETA: {fala}
FECHO (última cena): {fecho}

Julgue só a PROMESSA, não o estilo:
- falso: alguma afirmação é falsa ou exagerada além do que o próprio vídeo sustenta? Cite o trecho.
- sem_resposta: o título ou a 1ª frase fazem uma pergunta/provocação que o fecho NÃO responde com todas as letras?
- prova: 0 (afirma sem quem fez, sem número, sem fonte), 1 (tem alguma prova), 2 (prova concreta: quem, número, onde).
- entrega: 0 (o corpo é óbvio, genérico, ou volta a método antigo), 1 (útil), 2 (algo que eu não saberia sozinho).
- onde: se prova ou entrega < 2, diga ONDE está o defeito: "pesquisa" (falta fato que só a fonte tem: quem fez, número),
  "corpo" (cenas do meio, diga quais), "fecho", ou "pauta" (o assunto não serve a este público; reescrever não resolve).
- conserto: o que fazer, concreto. Se for "pesquisa", diga que fato buscar. Nunca mande mexer na abertura para
  consertar prova ou entrega.
- sugestoes: jargão, catálogo, desvio pequeno (lista curta; não reprova nada).

Responda SÓ com JSON numa linha:
{{"falso": false, "falso_trecho": "", "sem_resposta": false, "prova": 0, "entrega": 0, "onde": "", "conserto": "",
"sugestoes": [], "resumo": "<uma frase>"}}"""


def ler_json(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def primeira_frase(palavras, teto=20):
    for i in range(min(len(palavras), teto)):
        if i >= 4 and palavras[i].endswith((".", "?", "!")):
            return i + 1
    return min(len(palavras), teto)


def quadros(entrega, tmp):
    """quadro 0 e de 3 s de cada mp4 final (sem o 720p) + thumb.jpg."""
    out = []
    e = Path(entrega)
    for mp4 in sorted(e.glob("*.mp4")):
        if "720p" in mp4.name:
            continue
        fmt = "9x16" if "916" in mp4.name else "16x9"
        for t in ("0.1", "3"):
            png = Path(tmp) / f"{fmt}-{t}s.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", str(mp4), "-frames:v", "1",
                            "-vf", "scale=540:-2" if fmt == "9x16" else "scale=640:-2", str(png)], timeout=120)
            if png.exists():
                out.append((f"{fmt}, quadro em {t} s", png))
    if (e / "thumb.jpg").exists():
        out.append(("thumb do 16:9 no YouTube", e / "thumb.jpg"))
    return out


def pedir(texto, com_imagem):
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}   # só pela assinatura
    cmd = ["claude", "-p", "--output-format", "json"]
    cmd += ["--allowedTools", "Read", "--max-turns", "12"] if com_imagem else ["--max-turns", "2"]
    return subprocess.Popen(cmd + ["--", texto], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            stdin=subprocess.DEVNULL, env=env)


def colher(procs):
    votos, erros = [], []
    for pr in procs:
        try:
            out, _ = pr.communicate(timeout=900)
            res = json.loads(out)["result"].strip()
            votos.append(json.loads(res[res.index("{"): res.rindex("}") + 1]))
        except Exception as e:
            pr.kill()
            erros.append(str(e)[:160])
    if len(votos) * 2 <= len(procs):
        raise RuntimeError("; ".join(erros) or "sem resposta")
    return votos


def do_meio(votos, chave):
    """o voto cujo valor é a mediana (o motivo da maioria, não o do mais duro)."""
    med = statistics.median_low(int(v[chave]) if not isinstance(v[chave], dict) else int(v[chave]["pontos"]) for v in votos)
    for v in votos:
        x = v[chave] if not isinstance(v[chave], dict) else v[chave]["pontos"]
        if int(x) == med:
            return med, v
    return med, votos[0]


def juntar_gancho(votos):
    g = {"aspectos": {}}
    for k in PESOS:
        med, v = do_meio(votos, k)
        g["aspectos"][k] = {"pontos": med, "peso": PESOS[k], "motivo": v[k].get("motivo", ""),
                            "conserto": v[k].get("conserto", ""), "votos": [int(x[k]["pontos"]) for x in votos]}
    g["nota"] = round(sum(a["peso"] * a["pontos"] for a in g["aspectos"].values()) / 2)
    g["passa"] = g["nota"] >= MINIMO and all(g["aspectos"][k]["pontos"] >= 1 for k in SEM_ZERO)
    g["pararia"] = sum(bool(v.get("pararia")) for v in votos) * 2 > len(votos)
    g["resumo"] = [v.get("resumo", "") for v in votos]
    return g


def juntar_promessa(votos):
    p = {k: sum(bool(v.get(k)) for v in votos) * 2 > len(votos) for k in ("falso", "sem_resposta")}
    for k in ("prova", "entrega"):
        p[k], _ = do_meio(votos, k)
    pior = min(votos, key=lambda v: int(v["prova"]) + int(v["entrega"]))
    _, meio = do_meio(votos, "entrega")
    p["onde"], p["conserto"] = meio.get("onde", ""), meio.get("conserto", "")
    p["falso_trecho"] = next((v.get("falso_trecho") for v in votos if v.get("falso") and v.get("falso_trecho")), "")
    p["sugestoes"] = sorted({s for v in votos for s in (v.get("sugestoes") or [])})[:12]
    p["bloqueia"] = p["falso"] or p["sem_resposta"]
    p["corrigir"] = (not p["bloqueia"]) and (p["prova"] == 0 or p["entrega"] == 0)
    p["resumo"] = [v.get("resumo", "") for v in votos]
    p["pior_leitura"] = pior.get("resumo", "")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--entrega")
    ap.add_argument("--barrar", action="store_true")
    a = ap.parse_args()
    p = Path(a.pasta)
    cenas = ler_json(p / "roteiro-pt.json")
    cenas = cenas.get("cenas", cenas) if isinstance(cenas, dict) else cenas
    if not cenas:
        sys.exit(f"sem roteiro-pt.json em {p}")
    ped = ler_json(p / "pedido.json")
    persona = persona_de(ped)
    yt = p / "yt.txt"
    titulo = yt.read_text().splitlines()[0] if yt.exists() and yt.read_text().strip() else "(sem título ainda)"
    capa = "\n".join(str(x) for x in (cenas[0].get("labels") or [])) or "(sem texto)"
    fala = " ".join(str(c.get("speech") or "") for c in cenas)
    pal = fala.split()
    n1 = primeira_frase(pal)
    quinze = abertura(pal).split()
    frase, resto = " ".join(pal[:n1]), " ".join(quinze[n1:])
    fecho = str(cenas[-1].get("speech") or "")

    with tempfile.TemporaryDirectory() as tmp:
        imgs = quadros(a.entrega, tmp) if a.entrega else []
        bloco = IMAGENS.format(lista="\n".join(f"- {d}: {f}" for d, f in imgs)) if imgs else ""
        capa_img = (" Olhe as imagens: a capa de verdade é o quadro 0 de cada formato e a thumb; julgue pelo pior."
                    if imgs else "")
        tg = GANCHO.format(persona=persona, titulo=titulo, capa=capa, frase=frase, resto=resto or "(nada)",
                           imagens=bloco, capa_img=capa_img)
        tp = PROMESSA.format(persona=persona, titulo=titulo, capa=capa.replace("\n", " · "), fala=fala, fecho=fecho)
        h = hashlib.sha1((tg + tp + "".join(f.read_bytes().hex()[:2000] for _, f in imgs)).encode()).hexdigest()
        arq = p / "gancho-critica.json"
        velho = ler_json(arq)
        if velho.get("hash") == h:
            c = velho
        else:
            pg = [pedir(tg, bool(imgs)) for _ in range(VOTOS)]
            pp = [pedir(tp, False) for _ in range(VOTOS)]
            try:
                c = {"gancho": juntar_gancho(colher(pg)), "promessa": juntar_promessa(colher(pp))}
            except Exception as e:
                print(f"erro: crítico do gancho não respondeu: {str(e)[:240]}")
                sys.exit(2 if a.barrar else 0)
            c.update(hash=h, com_imagem=bool(imgs), frase=frase, modo="barra" if a.barrar else "sombra")
            arq.write_text(json.dumps(c, ensure_ascii=False, indent=1))

    g, pr = c["gancho"], c["promessa"]
    asp = " · ".join(f"{k} {v['pontos']}" for k, v in g["aspectos"].items())
    print(f"gancho {g['nota']}/100 ({'passa' if g['passa'] else 'NÃO passa'}; {asp})"
          f"{' com imagem' if c.get('com_imagem') else ' só texto'} · promessa: prova {pr['prova']} entrega {pr['entrega']}"
          + (" · BLOQUEIA: " + ("fato falso " + pr["falso_trecho"] if pr["falso"] else "pergunta sem resposta") if pr["bloqueia"] else "")
          + (f" · corrigir em {pr['onde']}: {pr['conserto']}" if pr["corrigir"] else ""))
    ok = g["passa"] and not pr["bloqueia"]
    if a.barrar and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
