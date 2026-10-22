#!/usr/bin/env python3
"""Configs da produção pedida pelo bot (/explicavideo no inemaccbot, 22/10/2026).

Uso: python3 bot/configs.py <pasta-do-bot>
Lê <pasta>/pedido.json (escrito pela fase `ficha`) e grava <pasta>/v1.json, v2.json (16:9) e v2-916.json (9:16),
só os formatos pedidos. Os valores fixos são os da Thwaites (21/10/2026) e do cancelei-anim (9:16), que deram certo.
Imprime os caminhos gravados. Sai 1 se o pedido estiver incompleto.
"""
import json
import re
import sys
from pathlib import Path

OUTPUT = Path.home() / "projetos/output"
PERFIL_HEYGEN = str(Path.home() / ".cache/inemaccbot/perfil-heygen")
FORMATOS = {"16x9", "9x16"}


def falha(msg):
    print(f"erro: {msg}")
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        falha("uso: configs.py <pasta-do-bot>")
    pasta = Path(sys.argv[1]).resolve()
    try:
        p = json.loads((pasta / "pedido.json").read_text())
    except (OSError, ValueError) as e:
        falha(f"pedido.json ilegível: {e}")
    for campo in ("id", "titulo", "formatos", "marca"):
        if not p.get(campo):
            falha(f"pedido.json sem '{campo}'")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,60}", p["id"]):
        falha(f"id inválido '{p['id']}' (minúsculas, números e hífen)")
    formatos = set(p["formatos"])
    if not formatos or not formatos <= FORMATOS:
        falha(f"formatos {p['formatos']} — aceito: 16x9, 9x16")
    roteiro = pasta / "roteiro-pt.json"
    if not roteiro.exists():
        falha("sem roteiro-pt.json")

    out = OUTPUT / p["id"]
    base = {"id": p["id"], "title": p["titulo"], "source_repo": str(out), "languages": ["pt"],
            "github_repo": "inematds/explicavideos", "release_tag": f"video-{p['id']}", "hyperframes": "0.8.77"}
    v1 = {**base, "output": str(out / "v1"), "scene_files": {"pt": str(roteiro)},
          "template": "TEMPLATE-AVATAR16", "profile": PERFIL_HEYGEN, "max_chars": 4400,
          "transcriber": "whisper-local", "balanced_blocks": True,
          "whisper_prompt": p.get("whisper_prompt") or "Nei Maldaner, INEMA, inema ponto club."}
    v2 = {**base, "engine": "v2", "v1_output": str(out / "v1"), **({} if p.get("perfil") == "aula" else {"profile_visual": "viral"}),
          "marca": p["marca"], **({"selo_topo": p["selo_topo"]} if p.get("selo_topo") else {})}
    gravados = [("v1.json", v1)]
    if "16x9" in formatos:
        gravados.append(("v2.json", {**v2, "output": str(out / "v2"), "aspect": "16:9"}))
    if "9x16" in formatos:
        gravados.append(("v2-916.json", {**v2, "profile_visual": "viral", "output": str(out / "v2-916"),
                                         "aspect": "9:16", "avatar_916": "pip", "pip_cena": 2, "pip_move": True,
                                         "capa_segura": True}))
    for nome, cfg in gravados:
        (pasta / nome).write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n")
        print(pasta / nome)


if __name__ == "__main__":
    main()
