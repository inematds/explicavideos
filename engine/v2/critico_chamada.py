#!/usr/bin/env python3
"""Crítico da CHAMADA (D20, Nei 12/11/2026): julga ATENÇÃO, não só forma. Complementa checar_chamada.py.

"Não adianta estar claro e correto se não chama atenção, não mexe na dor ou desejo." O checar_chamada.py confere o
que é objetivo (abertura proibida, 'você', nome do método, título, CTA). Este pergunta como quem rola o feed: nos
primeiros 15 s eu sei o problema, que é comigo, por que importa e o nome da solução? A fala é de gente ou de máquina?

Uso: critico_chamada.py <pasta> [--roteiro arquivo]   (lê roteiro-pt.json, yt.txt, chamada.json)
Grava <pasta>/chamada-critica.json (com hash da entrada: mudou o roteiro, critica de novo). Chama `claude -p` pela
assinatura (como o r7ex.py plano). Sai 0 se passou (nota ≥ 7 e as 5 perguntas sim), 1 se não passou, 2 se o crítico
não respondeu. NÃO bloqueia o avatar: quem chama decide (a ficha reescreve até 2 vezes e depois segue com a nota no
RESUMO.md; lição 21/10: estilo vira sugestão, o Nei decide se refaz).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PEDIDO = """Você é uma pessoa de 35 a 50 anos rolando o feed do YouTube/Instagram. Usa ChatGPT ou outra IA no trabalho,
não é programador, tem pouco tempo e pula vídeo que não fala da sua vida nos primeiros segundos.
Você não sabe como este vídeo foi feito. Julgue só o que está abaixo.

TÍTULO: {titulo}

MANCHETE DA CAPA (texto grande do 1º quadro): {manchete}

PRIMEIROS ~15 SEGUNDOS DA FALA: {abertura}

FALA COMPLETA: {fala}

O QUE O AUTOR QUERIA (núcleo da chamada): {nucleo} · método: {metodo}

Responda às perguntas pensando SÓ no título e nos primeiros 15 s (a fala completa é para julgar jargão e lista):
1. problema: eu já sei qual é o problema?
2. comigo: eu sinto que é COMIGO (minha dor ou meu desejo), não um assunto técnico dos outros?
3. importa: eu sei por que isso importa para mim (o que eu perco ou ganho)?
4. nome: se há método, eu já ouvi o NOME da solução? (sem método: responda true)
5. manchete: lendo SÓ a manchete da capa, sem som, eu entendo a informação (quem + o que acontece)? Enigmática
   ("IA COM PROVA") ou sem sujeito = false; clara e completa ("SUA IA DIZ 'PRONTO' SEM TER FEITO") = true.
A 1ª fala é frase completa, como se fala com alguém (quem faz o quê, em que condição), ou slogan comprimido que eu
tenho que decifrar? Slogan ('nunca mais diz pronto sem prova') = nota ≤ 6; frase de gente ('o seu agente nunca mais vai
dizer pronto se não tiver provado. É isso que este método faz. Vou explicar como.') é o certo.
Depois: liste palavras/expressões de máquina na fala (rótulo técnico sem explicação comum, sigla, nome de função) e
diga se a fala vira catálogo (lista de mais de 3 itens). Nota 0–10: "eu continuo assistindo?".

Responda SÓ com JSON numa linha:
{{"problema": true|false, "comigo": true|false, "importa": true|false, "nome": true|false, "manchete": true|false, "nota": 0-10,
"jargao": ["..."], "catalogo": true|false, "melhorar": "<abertura reescrita em 1-2 frases, na voz do Nei, ou vazio se nota >= 9>", "manchete_melhor": "<manchete clara, até 9 palavras, ou vazio>",
"resumo": "<uma frase>"}}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--roteiro")
    a = ap.parse_args()
    p = Path(a.pasta)
    rot = Path(a.roteiro) if a.roteiro else p / "roteiro-pt.json"
    cenas = json.loads(rot.read_text())
    fala = " ".join(str(c.get("speech") or "") for c in cenas)
    yt = p / "yt.txt"
    titulo = yt.read_text().splitlines()[0] if yt.exists() and yt.read_text().strip() else "(sem título ainda)"
    ch = json.loads((p / "chamada.json").read_text()) if (p / "chamada.json").exists() else {}
    manchete = " · ".join(str(x) for x in (cenas[0].get("labels") or [])) if cenas else ""
    pedido = PEDIDO.format(titulo=titulo, manchete=manchete or "(sem)", abertura=" ".join(fala.split()[:45]), fala=fala,
                           nucleo=ch.get("nucleo") or "(sem chamada.json)", metodo=ch.get("metodo") or "nenhum")
    h = hashlib.sha1(pedido.encode()).hexdigest()
    arq = p / "chamada-critica.json"
    c = json.loads(arq.read_text()) if arq.exists() else {}
    if c.get("hash") != h:
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}   # só pela assinatura
        r = subprocess.run(["claude", "-p", "--output-format", "json", "--max-turns", "2", "--", pedido],
                           capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL, env=env)
        try:
            res = json.loads(r.stdout)["result"].strip()
            c = json.loads(res[res.index("{"): res.rindex("}") + 1])
            int(c["nota"])
        except Exception as e:
            print(f"erro: crítico da chamada não respondeu direito: {str(e)[:160]} {r.stderr[-160:]}")
            sys.exit(2)
        c["hash"] = h
        arq.write_text(json.dumps(c, ensure_ascii=False, indent=1))
    sim = [k for k in ("problema", "comigo", "importa", "nome", "manchete") if c.get(k)]
    ok = int(c["nota"]) >= 7 and len(sim) == 5
    print(f"crítico da chamada: nota {c['nota']} · sim: {', '.join(sim) or 'nenhuma'}"
          + (f" · jargão: {', '.join(c.get('jargao') or [])}" if c.get("jargao") else "")
          + (" · CATÁLOGO" if c.get("catalogo") else "") + f" — {c.get('resumo', '')}")
    if not ok:
        print(f"melhorar: {c.get('melhorar', '')}")
        if c.get("manchete_melhor"):
            print(f"manchete: {c['manchete_melhor']}")
        print("chamada fraca (nota < 7 ou alguma pergunta 'não'): reescreva a abertura/título")
        sys.exit(1)
    print("chamada forte")


if __name__ == "__main__":
    main()
