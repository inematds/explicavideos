#!/usr/bin/env python3
"""QA VIRAL: o vídeo PARA a pessoa no feed e segura até o fim? (Nei 19/11/2026, 2.33.12)

"qa_viral tem que mudar de nome e criar um qa_viral que valide se tem apelo de gatilho de atenção, de retenção e
engajamento. Tem que criticar justamente a falta de impacto no vídeo. Se a fala tá fraca, compensa no visual
impressionante, viral, provocativo. O portão mais importante: nos primeiros 3 segundos a manchete que para a pessoa
no feed." Caso que gerou: Short Gemini 4 do lives3 (W_o_IfD3gmI) passou com 9/10 no QA técnico e no revisor, com a
manchete "CUSTO POR ENTREGA" e fotos genéricas (mesa, conta, papel) em vez do Gemini 4 Neon que todo mundo mostrava.

Uso: qa_viral.py <video.mp4> [--saida=<pasta>] [--pasta=<pasta da produção>] [--legenda=<srt>] [opções do qa_tecnico]
1. roda o qa_tecnico.py (tela vazia, parada, área lisa, tremida) com as mesmas opções;
2. julga o APELO no MP4 renderizado (não no roteiro): folha dos primeiros 3 s (7 quadros, 0 a 3 s) + folha do vídeo
   inteiro (16 quadros com o segundo escrito) + legenda (SRT ao lado do vídeo, --legenda= ou na --pasta).
   VIRAL_VOTOS leituras (padrão 3) do `claude -p` pela assinatura, em paralelo; maioria por pergunta, nota mediana.
   Público: o do canal (persona_de do critico_chamada.py, pedido.json da --pasta) + jovem, executivo e dona de casa.
REPROVA (código 1) se qualquer um:
- manchete_3s: não há manchete em letras ENORMES, legível no celular, nos primeiros 3 s (O PORTÃO MAIS IMPORTANTE);
- manchete_para: a manchete é rótulo/conceito ("CUSTO POR ENTREGA") e não faz parar (pergunta, conflito, número,
  nome forte do assunto: "QUAL DOS 3 GEMINI USAR?");
- assunto_visivel: as imagens não mostram o assunto de verdade (produto, demo, print, número, a coisa da notícia), só
  ilustração genérica;
- compensa: fala fraca e visual sem impacto ao mesmo tempo;
- menos de 2 dos 4 públicos param; nota < 7.
Código 2 = o juiz não respondeu (não aprova sem ler). Escape consciente: VIRAL_SEGUE=1 (só com ordem do Nei).
Grava viral-<nome>.json, abertura-<nome>.jpg e folha-<nome>.jpg em --saida, e junta o veredito em <video>.qa.json
(campo "viral"; "ok" passa a ser técnico E viral), que o enviar_bot_v3.mjs lê.
QA_VIRAL_CMD troca o comando do juiz (testes). QA_VIRAL_APELO=0 roda só o técnico (produção de rotina sem pessoa).
"""
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

V2 = Path(__file__).resolve().parent
sys.path.insert(0, str(V2))
from critico_chamada import persona_de  # noqa: E402  (público do canal: D29, um lugar só)

PERGUNTAS = ("manchete_3s", "manchete_para", "assunto_visivel", "impacto_visual", "fala_forte", "compensa",
             "retencao", "engajamento")
BARRA = ("manchete_3s", "manchete_para", "assunto_visivel", "compensa")
PUBLICOS = ("canal", "jovem", "executivo", "dona_de_casa")
VOTOS = max(1, int(os.environ.get("VIRAL_VOTOS", "3")))
SEGUE = os.environ.get("VIRAL_SEGUE") == "1"
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PEDIDO = """Você julga se um vídeo curto de rede social PARA a pessoa no feed e segura até o fim. Seja duro: a maioria dos
vídeos é pulada em 1 segundo. Você não sabe como foi feito; julgue só o que vê e lê.

Leia as duas imagens com a ferramenta Read:
- {abertura}: os 7 quadros dos PRIMEIROS 3 SEGUNDOS (0; 0,5; 1; 1,5; 2; 2,5; 3 s), da esquerda para a direita.
- {folha}: 16 quadros do vídeo inteiro, com o segundo escrito em cima de cada um.
Formato: {formato}, {dur:.0f} s. Canal: {canal}.

LEGENDA/FALA (pode faltar): {fala}

Quem está rolando o feed (julgue por cada um):
- canal: {persona}
- jovem: 18 a 25 anos, rola TikTok/Reels sem som, decide em 1 segundo
- executivo: 40 a 55 anos, gestor sem tempo, quer saber o que muda no dinheiro ou na decisão dele
- dona_de_casa: 35 a 60 anos, usa celular para tudo, não é técnica, para por curiosidade, susto ou benefício claro

Perguntas (true/false):
1. manchete_3s: nos primeiros 3 s há uma MANCHETE em letras ENORMES (cada letra com mais de ~5% da altura da tela),
   legível no celular sem som, que aparece até 1 s e fica? Texto pequeno, rótulo de canto, selo ou legenda = false.
2. manchete_para: lendo SÓ essa manchete, a pessoa para? Precisa de gancho: pergunta que é com ela, conflito/versus,
   número que espanta, nome forte do assunto, perda ou ganho. Rótulo de conceito ("CUSTO POR ENTREGA", "GUIA PRÁTICO",
   "COMPARATIVO") = false. Exemplo bom: "QUAL DOS 3 GEMINI USAR?".
3. assunto_visivel: as imagens mostram O ASSUNTO de verdade (o produto, a tela real, a demo, o resultado, o placar, o
   número, a coisa da notícia)? Ilustração genérica (mesa, papel, conta, pessoa no computador, escritório, ícone) na
   maior parte do vídeo = false.
4. impacto_visual: há imagens impressionantes ou provocativas (contraste forte, escala, versus lado a lado, antes e
   depois, resultado surpreendente, número gigante)? Visual correto mas morno = false.
5. fala_forte: a 1ª frase da fala/legenda prende sozinha?
6. compensa: se a fala é fraca, o visual compensa com impacto? (fala forte = true; fala fraca e visual morno = false)
7. retencao: abre uma pergunta/promessa cedo, muda algo a cada 2–3 s, sobe de intensidade e paga no fim?
8. engajamento: termina com pergunta de verdade ou algo para a pessoa comentar/discordar?
Para cada público: "para" (true/false) = ele pararia nos primeiros 3 s?
Liste as imagens fracas: segundo, o que mostra, por que é fraca e o que mostrar no lugar (concreto, do assunto).
Nota 0–10: "esse vídeo para o feed e segura?" (5 = pulo, 7 = paro e fico um pouco, 9 = não consigo sair).

Responda SÓ com JSON numa linha:
{{"manchete_lida": "<texto da maior manchete dos 3 s, ou vazio>", "manchete_3s": true|false, "manchete_para": true|false,
"assunto_visivel": true|false, "impacto_visual": true|false, "fala_forte": true|false, "compensa": true|false,
"retencao": true|false, "engajamento": true|false,
"publicos": {{"canal": true|false, "jovem": true|false, "executivo": true|false, "dona_de_casa": true|false}},
"imagens_fracas": [{{"t": <s>, "mostra": "...", "por_que": "...", "trocar_por": "..."}}],
"nota": 0-10, "manchete_melhor": "<manchete em MAIÚSCULAS até 7 palavras>", "resumo": "<uma frase>"}}"""


def sh(*a, **k):
    return subprocess.run(a, capture_output=True, text=True, **k)


def quadro(video, t, w):
    f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
    sh("ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
       "-vf", f"scale={w}:-2", f)
    try:
        return Image.open(f).convert("RGB")
    finally:
        os.unlink(f)


def folha(imgs, rotulos, colunas, destino):
    w, h = imgs[0].size
    faixa = max(22, h // 16)
    fonte = ImageFont.truetype(FONTE, int(faixa * 0.8))
    linhas = (len(imgs) + colunas - 1) // colunas
    s = Image.new("RGB", (w * colunas, (h + faixa) * linhas), "black")
    d = ImageDraw.Draw(s)
    for i, (im, r) in enumerate(zip(imgs, rotulos)):
        x, y = (i % colunas) * w, (i // colunas) * (h + faixa)
        d.text((x + 6, y + 1), r, fill="yellow", font=fonte)
        s.paste(im, (x, y + faixa))
    s.save(destino, quality=88)


def legenda(video, opt):
    cands = [opt.get("--legenda"), video.with_suffix(".srt")]
    if opt.get("--pasta"):
        cands += sorted(Path(opt["--pasta"]).glob("**/*.srt"))[:1]
    for c in cands:
        if c and Path(c).is_file():
            txt = [ln.strip() for ln in Path(c).read_text(errors="ignore").splitlines()
                   if ln.strip() and not ln.strip().isdigit() and "-->" not in ln]
            return " ".join(txt)[:4000]
    return "(sem legenda)"


def juntar(votos):
    c = {k: sum(bool(v.get(k)) for v in votos) * 2 > len(votos) for k in PERGUNTAS}
    c["publicos"] = {p: sum(bool((v.get("publicos") or {}).get(p)) for v in votos) * 2 > len(votos) for p in PUBLICOS}
    c["nota"] = int(statistics.median(int(v["nota"]) for v in votos))
    duro = min(votos, key=lambda v: int(v["nota"]))
    for k in ("manchete_lida", "imagens_fracas", "manchete_melhor", "resumo"):
        c[k] = duro.get(k)
    c["votos"] = [{k: v.get(k) for k in PERGUNTAS + ("publicos", "nota", "resumo")} for v in votos]
    return c


def julgar(pedido, pasta):
    cmd = os.environ.get("QA_VIRAL_CMD")
    base = cmd.split() if cmd else ["claude", "-p", "--output-format", "json", "--max-turns", "6",
                                    "--allowedTools", "Read", "--add-dir", str(pasta), "--"]
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}   # só pela assinatura
    procs = [subprocess.Popen(base + [pedido], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                              stdin=subprocess.DEVNULL, env=env) for _ in range(VOTOS)]
    votos, erros = [], []
    for pr in procs:
        try:
            out, _ = pr.communicate(timeout=900)
            res = json.loads(out)["result"].strip() if out.lstrip().startswith("{\"") and "\"result\"" in out else out
            v = json.loads(res[res.index("{"): res.rindex("}") + 1])
            int(v["nota"])
            votos.append(v)
        except Exception as e:
            pr.kill()
            erros.append(str(e)[:160])
    if len(votos) * 2 <= VOTOS:
        raise RuntimeError("; ".join(erros) or "sem resposta")
    return juntar(votos)


def veredito(c):
    motivos = [k for k in BARRA if not c.get(k)]
    param = sum(bool(c["publicos"].get(p)) for p in PUBLICOS)
    if param < 2:
        motivos.append(f"só {param} de 4 públicos param")
    if int(c["nota"]) < 7:
        motivos.append(f"nota {c['nota']} (precisa ≥ 7)")
    return motivos


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opt = {a.split("=")[0]: a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--") and "=" in a}
    video = Path(args[0]).resolve()
    saida = Path(opt.get("--saida", video.parent))
    saida.mkdir(parents=True, exist_ok=True)
    tec_args = [a for a in sys.argv[1:] if not a.startswith(("--pasta=", "--legenda="))]
    tec = subprocess.run([sys.executable, str(V2 / "qa_tecnico.py"), *tec_args])
    print(f"qa técnico: {'APROVADO' if tec.returncode == 0 else 'REPROVADO'}")
    if os.environ.get("QA_VIRAL_APELO") == "0":
        sys.exit(tec.returncode)

    nome = video.stem
    dur = float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)).stdout)
    wh = sh("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
            str(video)).stdout.strip().split(",")
    vertical = int(wh[1]) > int(wh[0])
    w = 360 if vertical else 480
    ab = saida / f"abertura-{nome}.jpg"
    fo = saida / f"folha-{nome}.jpg"
    ts = [i * 0.5 for i in range(7)]
    folha([quadro(video, t, w) for t in ts], [f"{t:.1f}s" for t in ts], 7, ab)
    tf = [min(dur - 0.1, dur * (i + 0.5) / 16) for i in range(16)]
    folha([quadro(video, t, w // 2 if not vertical else w // 2) for t in tf], [f"{t:.0f}s" for t in tf],
          8 if vertical else 4, fo)

    ped = {}
    if opt.get("--pasta") and (Path(opt["--pasta"]) / "pedido.json").exists():
        ped = json.loads((Path(opt["--pasta"]) / "pedido.json").read_text())
    pedido = PEDIDO.format(abertura=ab, folha=fo, formato="vertical 9:16" if vertical else "horizontal 16:9", dur=dur,
                           canal=", ".join(ped.get("canais") or []) or "(não informado)", persona=persona_de(ped),
                           fala=legenda(video, opt))
    h = hashlib.sha1(pedido.encode() + ab.read_bytes() + fo.read_bytes()).hexdigest()
    arq = saida / f"viral-{nome}.json"
    c = json.loads(arq.read_text()) if arq.exists() else {}
    if c.get("hash") != h:
        try:
            c = julgar(pedido, saida)
        except Exception as e:
            print(f"erro: o juiz do apelo não respondeu: {str(e)[:240]}")
            if SEGUE:
                print("VIRAL_SEGUE=1: sigo sem o juiz (escape consciente)")
                sys.exit(tec.returncode)
            sys.exit(2)
        c["hash"] = h
        arq.write_text(json.dumps(c, ensure_ascii=False, indent=1))

    motivos = veredito(c)
    c["ok"] = not motivos
    c["motivos"] = motivos
    arq.write_text(json.dumps(c, ensure_ascii=False, indent=1))
    qa = video.parent / f"{video.name}.qa.json"
    q = json.loads(qa.read_text()) if qa.exists() else {"video": video.name}
    q["tecnico_ok"] = tec.returncode == 0
    q["viral"] = {k: c.get(k) for k in ("ok", "nota", "motivos", "manchete_lida", "manchete_melhor", "resumo")}
    q["ok"] = q["tecnico_ok"] and c["ok"]
    qa.write_text(json.dumps(q, ensure_ascii=False, indent=1))

    pub = ", ".join(p for p in PUBLICOS if c["publicos"].get(p)) or "nenhum"
    print(f"qa viral ({len(c.get('votos') or []) or 1} leituras): nota {c['nota']} · manchete lida: "
          f"\"{c.get('manchete_lida') or ''}\" · param: {pub} — {c.get('resumo', '')}")
    for f in (c.get("imagens_fracas") or [])[:8]:
        print(f"  imagem fraca {f.get('t')} s: {f.get('mostra')} — {f.get('por_que')} → {f.get('trocar_por')}")
    if motivos:
        print(f"manchete sugerida: {c.get('manchete_melhor') or ''}")
        print(f"REPROVADO no apelo: {'; '.join(motivos)} (folhas: {ab}, {fo})")
        if SEGUE:
            print("VIRAL_SEGUE=1: sigo com apelo fraco (escape consciente; registre no RESUMO.md)")
            sys.exit(tec.returncode)
        sys.exit(1)
    print("APROVADO no apelo" if tec.returncode == 0 else "apelo ok, mas o técnico reprovou")
    sys.exit(tec.returncode)


if __name__ == "__main__":
    main()
