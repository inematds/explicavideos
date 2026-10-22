#!/usr/bin/env python3
"""Imagens de uma produção do bot pelo Codex image_gen (assinatura, nunca API). Molde: thwaites-juizo-final/media/gerar.py.

Uso: python3 bot/imagens.py <pasta-de-media> <itens.json>
itens.json = {"capa": {"fmt": "16x9", "cena": "..."}, "capa-v": {"fmt": "9x16", "cena": "..."}, ...}
Grava <pasta-de-media>/<nome>.png (pula as que já existem), 3 de cada vez, e corrige o amarelado
(refazvideo/ferramentas/cor_neutra.py). Última linha: FIM_IMAGENS ok=N falhou=M.
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = ("Use a ferramenta de geração de imagem (image_gen) para criar UMA imagem {fmt}. Estilo: fotojornalismo documental "
        "fotorrealista, dramático, luz NEUTRA, balanço de branco neutro, NUNCA amarelado, dourado ou sépia, sem cara de CGI. "
        "Todo texto na imagem em PORTUGUÊS DO BRASIL, com acentos corretos, letras grandes e legíveis, sem erros de grafia; "
        "nenhum outro texto além do pedido. Nenhum logotipo, nenhuma marca d'água, nenhuma pessoa reconhecível. "
        "Salve o arquivo final exatamente como ./arte.png neste diretório e responda só 'ok'.\n\nCena: {cena}")
FMT = {"16x9": "horizontal 16:9 (1536x864 ou próximo)", "9x16": "vertical 9:16 (864x1536 ou próximo)"}
ENV = {**os.environ, "PATH": f"{Path.home()}/.npm-global/bin:{os.environ.get('PATH', '')}"}


def gera(media, nome, item):
    out = media / f"{nome}.png"
    if out.exists():
        return nome, "já existe"
    d = media / "work" / nome
    d.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox", "-"],
                           input=BASE.format(fmt=FMT[item.get("fmt", "16x9")], cena=item["cena"]), cwd=d,
                           capture_output=True, text=True, timeout=1500, env=ENV)
    except subprocess.TimeoutExpired:
        return nome, "FALHOU (25 min sem imagem)"
    if (d / "arte.png").exists():
        os.replace(d / "arte.png", out)
        return nome, "OK"
    return nome, "FALHOU " + (r.stderr or r.stdout)[-300:].replace("\n", " ")


def main():
    if len(sys.argv) != 3:
        sys.exit("uso: imagens.py <pasta-de-media> <itens.json>")
    media = Path(sys.argv[1]).resolve()
    media.mkdir(parents=True, exist_ok=True)
    itens = json.loads(Path(sys.argv[2]).read_text())
    ok = falhou = 0
    with ThreadPoolExecutor(3) as ex:
        for nome, st in ex.map(lambda kv: gera(media, *kv), itens.items()):
            print(nome, st, flush=True)
            falhou += st.startswith("FALHOU")
            ok += not st.startswith("FALHOU")
    novas = [str(media / f"{n}.png") for n in itens if (media / f"{n}.png").exists()]
    cor = Path.home() / "projetos/refazvideo/ferramentas/cor_neutra.py"
    if novas and cor.exists():
        subprocess.run([sys.executable, str(cor), "corrigir", *novas], check=False)
    print(f"FIM_IMAGENS ok={ok} falhou={falhou}")


if __name__ == "__main__":
    main()
