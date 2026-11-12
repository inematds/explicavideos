#!/usr/bin/env python3
"""Portão da CHAMADA do explicavideo (D20, Nei 12/11/2026): clareza + atenção antes do avatar.

Regra: ~/projetos/inema-design/regras/chamada.md. "Não adianta estar claro e correto se não chama atenção, não mexe na
dor ou desejo." Caso: escrita-e-engenharia (lives3, 12/11) abriu com "Imagina…", não disse o nome do método, título de
inventário ("8 frases") e CTA "Comenta PROVA".

Uso: checar_chamada.py <pasta>   (lê <pasta>/roteiro-pt.json, <pasta>/yt.txt e <pasta>/chamada.json)
     refazvideo: checar_chamada.py $OUT --roteiro $OUT/roteiro/pt.json --sem-titulo
Saída: linhas "erro: …" / "aviso: …" e "chamada ok" na última linha; sai 1 se houver erro.
"""
import json
import re
import sys
from pathlib import Path

VALE_DESDE = 1794499200 # 2026-11-12 13:00 BRT: ficha anterior a isto (em andamento) sem chamada.json só recebe aviso
PAL_15S = 45         # ~15 s de fala a ~180 palavras/min
PAL_25S = 75          # ~25 s: a dor/desejo em "você" tem de aparecer até aqui (erro); até 15 s é o ideal (aviso)
PAL_METODO = 60       # ~20 s: o nome do método (quando houver) é dito até aqui
FORMATOS = {"acusacao", "promessa", "perda", "contrario", "numero", "estatistica", "pergunta", "nome", "noticia",
            "terceiro", "provocacao"}
VOCE = re.compile(r"\b(voc[eê]s?|seus?|suas?|te|teu|tua|contigo)\b", re.I)
ABERTURA_PROIBIDA = re.compile(r"^\W*(imagin[ae]|pense|neste v[ií]deo|nesse v[ií]deo|hoje (vamos|eu vou)|voc[eê] sabia|"
                               r"sabia que|eu fiz|eu criei|eu testei|ent[aã]o\b|neste momento)", re.I)
NESTE_VIDEO = re.compile(r"\bne(st|ss)e v[ií]deo\b", re.I)
NUM = (r"\d+|um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez|onze|doze|quinze|vinte|trinta|cinquenta|cem")
INVENTARIO = re.compile(rf"\b({NUM})\s+(frases|t[eé]cnicas|dicas|solu[cç][oõ]es|passos|coisas|ferramentas|prompts|truques|"
                        r"segredos|erros|formas|jeitos|motivos|regras|li[cç][oõ]es|recursos|comandos|habilidades|skills|"
                        r"m[eé]todos|maneiras|h[aá]bitos|ideias|apps|sites)\b", re.I)
CTA_PALAVRA = re.compile(r"\b[Cc]oment[ae]\s+(a\s+palavra\s+)?[\"'“]?[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{3,}\b")   # "Comenta PROVA"
CTA_PROIBIDO = re.compile(r"\bcoment[ae]\s+a\s+palavra\b|\bme\s+pe[cd]e\s+o\s+link\b|\bpe[cd]e\s+o\s+link\b|"
                          r"\blink\s+na\s+bio\b|\b(te|lhe)\s+(mando|envio|passo)\b|\bno\s+(direct|privado)\b|\bna\s+dm\b|"
                          r"\bfixad[oa]\b|\bcoment[ae]\s+\S+\s+que\s+(eu\s+)?(te\s+)?(mando|envio|passo)\b", re.I)
INEMA = re.compile(r"inema\s*(\.|ponto)\s*club", re.I)


def norm(s):
    return re.sub(r"\s+", " ", s.lower()).strip()


def checar(pasta, roteiro=None, sem_titulo=False):
    p = Path(pasta)
    erros, avisos = [], []
    rot = Path(roteiro) if roteiro else p / "roteiro-pt.json"
    if not rot.exists():
        return [f"sem {rot}"], []
    cenas = json.loads(rot.read_text())
    falas = [str(c.get("speech") or "") for c in cenas]
    tudo = " ".join(falas)
    pal = tudo.split()

    # 1. bloco CHAMADA
    cj = p / "chamada.json"
    ch = {}
    rec = p / "ficha.recibo"
    if not cj.exists() and rec.exists() and rec.stat().st_mtime < VALE_DESDE:
        avisos.append("ficha feita antes da regra da chamada (12/11/2026 13h): sem chamada.json, só avisa")
        return [], avisos
    if not cj.exists():
        erros.append("falta chamada.json (dor_ou_desejo, quem, nucleo, por_que_importa, metodo, formato) — "
                     "regra inema-design/regras/chamada.md §1; escreva antes do roteiro")
    else:
        ch = json.loads(cj.read_text())
        for k in ("dor_ou_desejo", "quem", "nucleo", "por_que_importa", "formato"):
            if not str(ch.get(k) or "").strip():
                erros.append(f"chamada.json sem '{k}'")
        if ch.get("dor_ou_desejo") and ch["dor_ou_desejo"] not in ("dor", "desejo"):
            erros.append("chamada.dor_ou_desejo: 'dor' ou 'desejo'")
        if ch.get("formato") and ch["formato"] not in FORMATOS:
            erros.append(f"chamada.formato '{ch['formato']}': um de {sorted(FORMATOS)}")
        if ch.get("nucleo") and INVENTARIO.search(ch["nucleo"]):
            erros.append(f"chamada.nucleo é inventário ('{INVENTARIO.search(ch['nucleo']).group(0)}'): diga o que a "
                         "pessoa ganha ou deixa de perder, não quantas peças tem")

    # 2. abertura: sem fórmula proibida, dor/desejo em "você" cedo
    frase1 = re.split(r"(?<=[.!?])\s", (falas[0] if falas else "").strip())[0]
    if ABERTURA_PROIBIDA.search(frase1):
        erros.append(f"abertura proibida na 1ª frase ('{frase1[:70]}'): comece pela dor/desejo ou pelo fato mais forte "
                     "(texto.md: nada de 'Imagine…', 'Neste vídeo…', 'Você sabia…')")
    ab15, ab25 = " ".join(pal[:PAL_15S]), " ".join(pal[:PAL_25S])
    if not VOCE.search(ab25):
        erros.append("até ~25 s a fala não fala com a pessoa ('você/seu/sua'): a dor ou o desejo dela tem de aparecer já")
    elif not VOCE.search(ab15):
        avisos.append("o 'você' só aparece depois de ~15 s: o ideal é a dor/desejo da pessoa nos primeiros 15 s")
    if NESTE_VIDEO.search(ab15):
        avisos.append("'neste vídeo' nos primeiros 15 s: troque pela promessa direta ('no fim você sai com…')")

    # 3. método nomeado
    met = str(ch.get("metodo") or "").strip()
    if met:
        n = norm(tudo).count(norm(met))
        if norm(met) not in norm(" ".join(pal[:PAL_METODO])):
            erros.append(f"o nome do método '{met}' não é dito até ~20 s (a pessoa tem de saber o nome da solução cedo)")
        if n < 2:
            erros.append(f"o nome do método '{met}' aparece {n}× na fala: diga pelo menos 2× (abertura e fecho)")

    # 4. título (yt.txt, 1ª linha)
    yt = p / "yt.txt"
    tit = yt.read_text().splitlines()[0].strip() if yt.exists() and yt.read_text().strip() else ""
    if sem_titulo and not tit:
        avisos.append("sem título ainda (--sem-titulo): confira na publicação que ele sai do núcleo, sem inventário")
    elif not tit:
        erros.append("sem título (yt.txt, 1ª linha)")
    else:
        if INVENTARIO.search(tit):
            erros.append(f"título com contagem de inventário ('{INVENTARIO.search(tit).group(0)}'): o título leva a "
                         "dor/desejo e o nome do método; número só de FATO (nota, resultado medido)")
        if met and norm(met) not in norm(tit) and not VOCE.search(tit):
            avisos.append(f"título sem o nome do método ('{met}') e sem 'você/sua/seu': confira se a chamada está nele")

    # 5. CTA (última cena): engajamento natural, sem pedir palavra nem link
    cta = falas[-1] if falas else ""
    m = CTA_PALAVRA.search(cta) or CTA_PROIBIDO.search(cta)
    if m:
        erros.append(f"CTA pede palavra/link/recompensa ('{m.group(0)}'): faça uma pergunta de verdade e diga que está "
                     "no inema.club, direto na internet (chamada.md §4)")
    if "?" not in cta:
        erros.append("CTA sem pergunta: o fecho pergunta algo da vida/opinião da pessoa, ligado à dor/desejo")
    if not INEMA.search(cta):
        erros.append("CTA sem 'inema ponto club' (onde está o kit/conteúdo, grátis se for verdade)")
    return erros, avisos


def main():
    import argparse
    ap = argparse.ArgumentParser(description="portão da chamada (D20)")
    ap.add_argument("pasta")
    ap.add_argument("--roteiro", help="roteiro fora da pasta (refazvideo: $OUT/roteiro/pt.json)")
    ap.add_argument("--sem-titulo", action="store_true", help="título ainda não existe (só avisa)")
    a = ap.parse_args()
    erros, avisos = checar(a.pasta, a.roteiro, a.sem_titulo)
    for a in avisos:
        print(f"aviso: {a}")
    for e in erros:
        print(f"erro: {e}")
    if erros:
        print(f"chamada reprovada: {len(erros)} erro(s) — regra ~/projetos/inema-design/regras/chamada.md")
        sys.exit(1)
    print("chamada ok")


if __name__ == "__main__":
    main()
