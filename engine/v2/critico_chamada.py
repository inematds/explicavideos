#!/usr/bin/env python3
"""Crítico da CHAMADA (D20, Nei 12/11/2026; D23, 17/11/2026): julga ATENÇÃO, não só forma. Complementa checar_chamada.py.

"Não adianta estar claro e correto se não chama atenção, não mexe na dor ou desejo." O checar_chamada.py confere o
que é objetivo (abertura proibida, 'você', nome do método, título, CTA). Este pergunta como quem rola o feed: nos
primeiros 15 s eu sei o problema, que é comigo, por que importa e o nome da solução? A fala é de gente ou de máquina?

Uso: critico_chamada.py <pasta> [--roteiro arquivo]   (lê roteiro-pt.json, yt.txt, chamada.json, pedido.json)
Grava <pasta>/chamada-critica.json (com hash da entrada: mudou o roteiro, critica de novo). Chama `claude -p` pela
assinatura (como o r7ex.py plano). Sai 0 se passou (nota ≥ 7 e todas as perguntas sim), 1 se não passou, 2 se o crítico
não respondeu.

BARRA (2.27.11, Nei 13/11/2026 "aplica", PADRAO-VIRAL Retenção item 4): até a 2.26 a ficha reescrevia 2 vezes e seguia
com nota < 7; os /swarm passaram assim com nota 5 e foram reprovados no ar. Agora quem chama para no código ≠ 0
(`bot/avatar.sh` roda este portão antes do envio ao estúdio; a fase ficha para com ERRO depois de 2 rodadas).
Escape consciente: CRITICO_SEGUE=1 imprime o aviso e sai 0 (só quando o Nei mandou seguir com a nota que está).

2.29.11 (D23, Nei 17/11/2026: "a questão do crítico temos que rever porque pode ser ele o problema"; "isca faz parte
do jogo… faz a pessoa parar para ver e aí continuamos provocando a escada"). O que mudou e por quê:
- a abertura ia cortada em 45 palavras, no meio da frase (fim-universidade-v2: a promessa ficou de fora e ele reprovou
  "importa"). Agora vai até o fim da frase depois de ~40 palavras (teto 75);
- 1 leitura só, com 5 "sim" obrigatórios = sorteio perto do corte (24 de 40 críticas deram exatamente 7; a mesma fala
  virou "importa" de sim para não). Agora CRITICO_VOTOS leituras (padrão 3) em paralelo: maioria por pergunta, nota
  mediana;
- persona fixa de escritório para todo canal: agora `publico` do pedido.json (versionado na pasta), padrão o de sempre;
- não punia sumário (o lives11 passou com 9) e punia a isca: agora pergunta `escada` (uma linha que sobe, não sumário)
  e `paga` (o fecho responde a provocação), e a provocação forte NÃO baixa a nota se é verdade e o fecho paga.
2.30.11 (Nei 17/11/2026, sobre o fim-universidade-v2 já no ar: "o que falou no vídeo é o óbvio, mas não tem a ver com a
tecnologia e sim voltando atrás, como era feito antes, prova oral"): `paga` só conferia se o fecho responde ao
título; o v2 respondeu "não acabou" e passou com resposta velha. Nova pergunta `entrega`: o corpo cumpre a promessa
da isca com algo novo, não com o óbvio nem com volta ao método antigo.
2.31.12 (D29, Nei 18/11/2026, aprovou o público por canal): canal técnico era julgado por quem só usa ChatGPT e reprovava
só em `comigo` (Zelador no lives7). Agora vale `publico` do pedido.json; sem ele, PUBLICO_CANAL pelo 1º canal do pedido que
estiver na tabela; sem canal na tabela, a persona padrão.
A persona e o pedido só mudam neste arquivo ou no pedido.json, nunca num script da sessão (chamada.md §3.7).
"""
import argparse
import hashlib
import json, time
import os
import statistics
import subprocess
import sys
from pathlib import Path

PERGUNTAS = ("problema", "comigo", "importa", "nome", "manchete", "escada", "paga", "entrega", "virada")
# Nei, 21/11/2026: por uns dias o crítico só AVALIA e registra; não reprova (sai 0). Passou a data, volta a barrar.
OBSERVAR_ATE = os.environ.get("CRITICO_OBSERVAR_ATE", "2026-11-28")
OBSERVAR = time.strftime("%Y-%m-%d") <= OBSERVAR_ATE and os.environ.get("CRITICO_OBSERVAR") != "0"
REGISTRO = Path(__file__).resolve().parents[2] / "registro-critico-chamada.jsonl"
SEGUE = os.environ.get("CRITICO_SEGUE") == "1"   # escape consciente (docstring)
VOTOS = max(1, int(os.environ.get("CRITICO_VOTOS", "3")))
PERSONA = ("uma pessoa de 35 a 50 anos rolando o feed do YouTube/Instagram. Usa ChatGPT ou outra IA no trabalho, "
           "não é programador")
PUBLICO_CANAL = {   # D29: canais de público único no mapa aprovado pelo Nei (promoavatar/docs/publicos.md, 18/11/2026);
    # canal com mais de um público usa a persona padrão. Mudar aqui exige commit com o motivo.
    # Nei, 20/11/2026: lives1/2/3/11/12 com público próprio (promoavatar/docs/publicos.md, "Público de cada canal").
    "lives1": "uma pessoa da comunidade INEMA que já acompanha o canal, quer novidade e se sentir parte",
    "lives2": "um gestor que quer saber de novidades de jurídico, contabilidade e financeiro",
    "lives3": "uma pessoa que quer aprender IA e está começando, não é programadora",
    "lives12": "um profissional liberal de qualquer área (advogado, médico, contador, arquiteto, dentista) que não é de tecnologia",
    "lives24": ("dono de negócio, autônomo ou prestador de serviço que quer gastar menos, vender mais e sair da operação"),
    "lives11": "uma pessoa que gosta de visão de futuro e quer saber para onde o trabalho e a IA estão indo",
    "lives4": "uma pessoa que já mexe com tecnologia e quer construir sistemas, não só testar ferramentas",
    "lives7": "uma pessoa que já deixa agentes, robôs ou rotinas de IA fazendo tarefas sozinhos; não precisa ser programadora",
    "lives8": "uma pessoa que quer criar site, app ou ferramenta com IA, sem saber programar",
}

PEDIDO = """Você é {persona}. Tem pouco tempo e pula vídeo que não fala da sua vida nos primeiros segundos.
Você não sabe como este vídeo foi feito. Julgue só o que está abaixo.

TÍTULO: {titulo}

MANCHETE DA CAPA (texto grande do 1º quadro): {manchete}

PRIMEIROS ~15 SEGUNDOS DA FALA: {abertura}

FECHO (última cena da fala): {fecho}

FALA COMPLETA: {fala}

O QUE O AUTOR QUERIA (núcleo da chamada): {nucleo} · método: {metodo}

A ISCA FAZ PARTE DO JOGO. Título, capa ou 1ª frase provocativa ("O fim da universidade chegou?") é o que faz a pessoa
parar; isso é desejado e NÃO baixa a nota. Só baixa se a provocação for afirmação falsa/exagerada, se a abertura não
sustenta a provocação com fato logo depois, ou se o fecho não responde à provocação.

Responda às perguntas pensando no título e nos primeiros 15 s (o fecho é para a pergunta 7; a fala completa é para
julgar jargão e lista):
1. problema: eu já sei qual é o problema ou a novidade?
2. comigo: eu sinto que é COMIGO (minha dor ou meu desejo), não um assunto técnico dos outros?
3. importa: eu sei por que isso importa para mim (o que eu perco ou ganho), ou me prometeram mostrar isso?
4. nome: se há método, eu já ouvi o NOME da solução? (sem método: responda true)
5. manchete: lendo SÓ a manchete da capa, sem som, eu entendo a informação (quem + o que acontece)? Enigmática
   ("IA COM PROVA") ou sem sujeito = false; clara e completa ("SUA IA DIZ 'PRONTO' SEM TER FEITO") = true. Pergunta
   provocativa seguida de manchete com a informação = true.
6. escada: os primeiros 15 s seguem UMA linha que sobe (cada frase aumenta o peso da anterior: provocação → quem diz →
   quem já fez, com número → promessa para mim)? Faça o teste: para cada frase, ela PROVA ou AGRAVA a frase anterior
   (escada) ou abre outro assunto (sumário)? Duas perguntas seguidas sobre coisas diferentes, uma frase-tese abstrata
   no meio ("o diploma precisa provar…"), número arredondado ("milhares") no lugar do exato, ou mais de 4 frases curtas
   cada uma com um assunto = sumário = false. Liste em "frases" o papel de cada frase dos 15 s.
7. paga: se o título ou a 1ª frase provocam (pergunta ou tese forte), o FECHO responde com todas as letras? Sem
   provocação: true.
8. entrega: o CORPO e o fecho entregam o que a abertura prometeu, com algo que eu não saberia dizer sozinho? Leia a
   fala completa. Se a isca fala de mudança, tecnologia ou futuro e a resposta é voltar a método antigo (prova oral,
   proibir, vigiar, "explique sua decisão", portfólio) ou um conselho óbvio que já existia antes da novidade = false.
   Teste: cada passo da resposta seria possível sem a novidade da isca? Se quase todos sim = false.
9. virada: {virada}
A 1ª fala é frase completa, como se fala com alguém (quem faz o quê, em que condição), ou slogan comprimido que eu
tenho que decifrar? Slogan ('nunca mais diz pronto sem prova') = nota ≤ 6; frase de gente ('o seu agente nunca mais vai
dizer pronto se não tiver provado. É isso que este método faz. Vou explicar como.') é o certo.
Depois: liste palavras/expressões de máquina na fala (rótulo técnico sem explicação comum, sigla, nome de função) e
diga se a fala vira catálogo (lista de mais de 3 itens). Nota 0–10: "eu continuo assistindo?" (use a escala inteira:
5 = eu pulo, 7 = fico por educação, 9 = não consigo sair).

Responda SÓ com JSON numa linha:
{{"problema": true|false, "comigo": true|false, "importa": true|false, "nome": true|false, "manchete": true|false,
"frases": ["<frase curta> → prova|agrava|promessa|outro assunto"], "escada": true|false, "paga": true|false, "entrega": true|false, "virada": true|false, "nota": 0-10,
"jargao": ["..."], "catalogo": true|false, "melhorar": "<abertura reescrita em 1-2 frases, na voz do Nei, ou vazio se nota >= 9>", "manchete_melhor": "<manchete clara, até 9 palavras, ou vazio>",
"resumo": "<uma frase>"}}"""


def abertura(palavras, minimo=40, teto=75):
    """~15 s da fala, até o fim da frase (nunca cortada no meio)."""
    for i in range(minimo - 1, min(len(palavras), teto)):
        if palavras[i].endswith((".", "?", "!")):
            return " ".join(palavras[:i + 1])
    return " ".join(palavras[:teto])


# D32 (D20 revista, Nei 27/11/2026): "como as pessoas já sabem do assunto, não é a dor que move, e sim o desejo, a
# provocação, a perda… 'para de perder tokens'… é a dor pelo outro lado". Padrão por canal = inema-design chamada.md §2f.
SABE_CANAL = {"lives1": True, "lives4": True, "lives7": True,
              "lives2": False, "lives8": False, "lives12": False, "lives24": False}   # lives3/lives11: pelo assunto
VIRADA_SABE = ("EU JÁ VIVO ESSE ASSUNTO (uso, gasto, sofro com ele). A abertura e o título pegam a dor pelo OUTRO LADO "
               "— o que eu paro de perder/pagar/esperar (\"pare de perder tokens\", \"nunca mais vai sentir falta dos "
               "seus tokens\"), o jeito antigo que eu ainda uso (\"você ainda usa do jeito antigo\") ou quem de peso já "
               "resolveu (\"os engenheiros da Anthropic mostraram como…\")? true. Se gasta mais de 2 frases me "
               "descrevendo a dor que eu já conheço, ou abre com dúvida morna/rótulo neutro que não promete eu parar de "
               "perder nada = false. Em \"melhorar\" e \"manchete_melhor\", a 1ª frase é do tipo parar de perder, jeito "
               "antigo ou autoridade; NUNCA comece descrevendo o problema que eu já sofro (\"seu agente diz que está "
               "pronto e tem defeito\" = errado; \"nunca mais deixe defeito ir para o ar\" = certo).")
VIRADA_LEIGO = "eu ainda não vivo esse assunto (sou leigo nele): responda true."
VIRADA_TALVEZ = "se eu já vivo esse assunto: " + VIRADA_SABE + " Se o assunto é novo para mim: true."


def sabe_de(ch, ped):
    """chamada.json > padrão do canal (D32). None = não dá para saber (lives3/lives11 sem o campo)."""
    v = str(ch.get("publico_ja_sabe") or "").strip().lower().replace("ã", "a")
    if v in ("sim", "nao"):
        return v == "sim"
    return next((SABE_CANAL[c] for c in ped.get("canais") or [] if c in SABE_CANAL), None)


def persona_de(ped):
    """pedido.json > tabela do canal > padrão (D29)."""
    canal = next((c for c in ped.get("canais") or [] if c in PUBLICO_CANAL), None)
    return ped.get("publico") or PUBLICO_CANAL.get(canal) or PERSONA


def montar(pasta, cenas):
    p = Path(pasta)
    fala = " ".join(str(c.get("speech") or "") for c in cenas)
    yt = p / "yt.txt"
    titulo = yt.read_text().splitlines()[0] if yt.exists() and yt.read_text().strip() else "(sem título ainda)"
    ch = json.loads((p / "chamada.json").read_text()) if (p / "chamada.json").exists() else {}
    ped = json.loads((p / "pedido.json").read_text()) if (p / "pedido.json").exists() else {}
    manchete = " · ".join(str(x) for x in (cenas[0].get("labels") or [])) if cenas else ""
    txt = PEDIDO.format(persona=persona_de(ped), titulo=titulo, manchete=manchete or "(sem)",
                        abertura=abertura(fala.split()), fecho=str(cenas[-1].get("speech") or "") if cenas else "",
                        fala=fala, nucleo=ch.get("nucleo") or "(sem chamada.json)", metodo=ch.get("metodo") or "nenhum",
                        virada={True: VIRADA_SABE, False: VIRADA_LEIGO, None: VIRADA_TALVEZ}[sabe_de(ch, ped)])
    return txt + (PRODUTO if ch.get("formato") == "produto" else "")


# D30 (Nei, 24/11/2026): vídeo de ferramenta abre pelo produto, curto e direto, sem história. "as pessoas querem um
# produto, e aí a solução"; "quando fala openbot, mesmo não sabendo, chama atenção"; "é informação e não venda".
PRODUTO = """

ESTE VÍDEO É DE PRODUTO (formato produto, D30). Ajuste a leitura:
- "comigo" = eu QUERO esse produto depois da 1ª frase? (o nome do produto + o ganho já bastam; não exija cena da minha vida).
- O nome do produto e os termos dele (ferramenta, servidor, WhatsApp, agente) NÃO contam como jargão.
- Lista de benefícios curta e direta é o formato certo: "catalogo" só se passar de 5 itens soltos sem prova.
- "escada" = cada frase acrescenta um benefício ou a prova dele. Sem provocação: "paga" = true.
- Abrir com cena/historinha antes do produto baixa a nota (nota ≤ 6): o produto vem nos 2 primeiros segundos.
- Não peça ressalva de licença, custo ou "não testado": é informação, não venda."""


def juntar(votos):
    """maioria por pergunta, nota mediana; conselho do voto mais duro."""
    c = {k: sum(bool(v.get(k)) for v in votos) * 2 > len(votos) for k in PERGUNTAS}
    c["nota"] = int(statistics.median(int(v["nota"]) for v in votos))
    duro = min(votos, key=lambda v: int(v["nota"]))
    for k in ("jargao", "catalogo", "melhorar", "manchete_melhor", "resumo"):
        c[k] = duro.get(k)
    c["votos"] = [{k: v.get(k) for k in PERGUNTAS + ("nota", "resumo")} for v in votos]
    return c


def criticar(pedido):
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}   # só pela assinatura
    procs = [subprocess.Popen(["claude", "-p", "--output-format", "json", "--max-turns", "2", "--", pedido],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, stdin=subprocess.DEVNULL, env=env)
             for _ in range(VOTOS)]
    votos, erros = [], []
    for pr in procs:
        try:
            out, err = pr.communicate(timeout=600)
            res = json.loads(out)["result"].strip()
            v = json.loads(res[res.index("{"): res.rindex("}") + 1])
            int(v["nota"])
            votos.append(v)
        except Exception as e:
            pr.kill()
            erros.append(str(e)[:160])
    if len(votos) * 2 <= VOTOS:   # menos da metade respondeu
        raise RuntimeError("; ".join(erros))
    return juntar(votos)


def registrar(pasta, c, h):
    """Uma linha por avaliação (dedupe por hash do pedido) em explicavideos/registro-critico-chamada.jsonl."""
    try:
        if REGISTRO.exists() and h in REGISTRO.read_text():
            return
        lin = {"data": time.strftime("%Y-%m-%d %H:%M:%S"), "pasta": str(pasta), "hash": h, "nota": c.get("nota"),
               **{k: bool(c.get(k)) for k in PERGUNTAS}, "jargao": c.get("jargao"), "catalogo": c.get("catalogo"),
               "resumo": c.get("resumo"), "melhorar": c.get("melhorar"), "modo": "observar" if OBSERVAR else "barra"}
        with open(REGISTRO, "a") as f:
            f.write(json.dumps(lin, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--roteiro")
    a = ap.parse_args()
    p = Path(a.pasta)
    rot = Path(a.roteiro) if a.roteiro else p / "roteiro-pt.json"
    pedido = montar(p, json.loads(rot.read_text()))
    h = hashlib.sha1(pedido.encode()).hexdigest()
    arq = p / "chamada-critica.json"
    c = json.loads(arq.read_text()) if arq.exists() else {}
    if c.get("hash") != h:
        try:
            c = criticar(pedido)
        except Exception as e:
            print(f"erro: crítico da chamada não respondeu direito: {str(e)[:240]}")
            if SEGUE:
                print("CRITICO_SEGUE=1: sigo sem a nota do crítico (escape consciente)")
                sys.exit(0)
            sys.exit(2)
        c["hash"] = h
        arq.write_text(json.dumps(c, ensure_ascii=False, indent=1))
    sim = [k for k in PERGUNTAS if c.get(k)]
    registrar(p, c, h)
    ok = int(c["nota"]) >= 7 and len(sim) == len(PERGUNTAS)
    nv = len(c.get("votos") or []) or 1
    print(f"crítico da chamada ({nv} leitura{'s' if nv > 1 else ''}): nota {c['nota']} · sim: {', '.join(sim) or 'nenhuma'}"
          + (f" · jargão: {', '.join(c.get('jargao') or [])}" if c.get("jargao") else "")
          + (" · CATÁLOGO" if c.get("catalogo") else "") + f" — {c.get('resumo', '')}")
    if not ok and OBSERVAR:
        print(f"OBSERVAÇÃO (modo observar até {OBSERVAR_ATE}): nota {c['nota']}, 'não' em "
              f"{', '.join(k for k in PERGUNTAS if not c.get(k)) or 'nenhuma'}; registrado, NÃO barra. melhorar: {c.get('melhorar', '')}")
        sys.exit(0)
    if not ok:
        print(f"melhorar: {c.get('melhorar', '')}")
        if c.get("manchete_melhor"):
            print(f"manchete: {c['manchete_melhor']}")
        print("chamada fraca: reescreva com outro gatilho (ver PADRAO-VIRAL Retenção)"
              f" — nota {c['nota']} (precisa ≥ 7) e 'não' em: {', '.join(k for k in PERGUNTAS if not c.get(k)) or 'nenhuma'}")
        if SEGUE:
            print("CRITICO_SEGUE=1: sigo com a chamada fraca (escape consciente; registre a nota no RESUMO.md)")
            sys.exit(0)
        sys.exit(1)
    print("chamada forte")


if __name__ == "__main__":
    main()
