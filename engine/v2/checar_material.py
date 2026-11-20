#!/usr/bin/env python3
"""Portão do MATERIAL e do PLANO (2.34.12, Nei 20/11/2026, EV#187–191).

Causa raiz dos tornados (output/tornado-refazer-20261120/CAUSA-RAIZ.md): nenhuma fase planejava a tela a partir do
material que o Nei mandou; o vídeo virava "guia de dicas" de ~160 s com ícone e peça de código, e a foto real sumia
depois dos 30 s. O QA de apelo só via isso no MP4 pronto, depois do avatar pago e de 20 min de render.

Dois modos, mesma régua:

  checar_material.py plano  <pasta-do-bot>      antes do avatar (ficha passo 4b e bot/avatar.sh)
      lê plano.json + material.json + roteiro-pt.json: duração estimada pela fala (≈ 1.080 caracteres/min, medido),
      teto de duração, trechos com material real espalhados pelo vídeo, peça de código só para número/comparação.

  checar_material.py visual <saída-do-formato>  fim da fase visual, antes do VISUAL-OK (ex.: ~/projetos/output/<id>/v2)
      mede no visual montado (final/pt-b01/compositions + verification/build-v2-pt-b01.json): segundos de material
      real, último segundo em que ele aparece, maior buraco sem ele e fatia de peça de código.

Material real = arquivo listado no material.json da produção (captado por bot/captar.py) ou, sem ele, nomes
`real-*` / `facebook-*` (fotos do Nei). Sai 0 = ok, 1 = reprovado (motivos na saída), 2 = faltou arquivo.
Escape consciente, só com ordem do Nei: MATERIAL_SEGUE=1.
"""
import json
import os
import re
import sys
from pathlib import Path

CHARS_POR_MIN = 1080          # medido nos avatares do EV#187–191 (1.076–1.132), não os 800 antigos
TETO_VIRAL_S = 100            # PADRAO-VIRAL: 45–75 s; folga para notícia com contexto. Mais só se o Nei pedir.
TETO_AULA_S = 270             # 1 bloco do HeyGen
REAL_MIN = 0.35               # fatia mínima de tela com material real quando ele existe
REAL_ULTIMO = 0.75            # o real tem de aparecer no último quarto
BURACO_MAX_S = 30             # maior trecho seguido sem material real
CODIGO_MAX = 0.30             # peça desenhada por código (bignum, ranking, diagrama…) no máximo 30% da tela
SEM_TELA = {'rosto', 'cta', 'legenda'}   # sobreposições / fecho: não contam como "o que está na tela"
CODIGO = {'bignum', 'ranking', 'colunas', 'linha', 'escala', 'cinetica', 'carimbo', 'diagrama', 'capitulo',
          'statement', 'svg', 'hook', 'iface', 'terminal', 'chat', 'tabela', 'lista', 'comparativo', 'versus'}
MAPA = {'mapa'}


def nome_base(src):
    """Raiz do nome, sem o caminho e sem o que o build e os inserts acrescentam:
    assets/media/85badcaecd-facebook-1.jpg → facebook-1 · 02-facebook-1.poster.jpg (foto virou clipe) → facebook-1."""
    b = os.path.basename(str(src or ''))
    b = re.sub(r'^[0-9a-f]{10}-', '', b)
    b = re.sub(r'^\d{2}-', '', b)
    b = re.sub(r'(\.poster)?\.[A-Za-z0-9]+$', '', b)
    return b


def nomes_reais(material):
    if material:
        return {nome_base(m.get('arquivo')) for m in material.get('itens', []) if m.get('real', True)}
    return None


def eh_real(src, reais):
    b = nome_base(src)
    if not b:
        return False
    if reais is not None and b in reais:
        return True
    return b.startswith(('real-', 'facebook-', 'clipe-'))   # clipe-N.mp4 = trecho cortado do vídeo real


def ler_json(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------- visual montado
def medir_visual(saida, reais=None):
    saida = Path(saida).expanduser()
    rel = ler_json(saida / 'verification' / 'build-v2-pt-b01.json')
    comp = saida / 'final' / 'pt-b01' / 'compositions'
    if not rel or not comp.is_dir():
        raise FileNotFoundError(f'sem build/compositions em {saida} (rode build_block --strict antes)')
    faixas = []   # (t0, t1, classe, src)
    for sc in rel.get('scenes', []):
        f = comp / f"scene-{int(sc['scene']):03d}.html"
        h = f.read_text() if f.exists() else ''
        m = re.search(r'V2\.scene\("[^"]+",\s*(\{.*\})\);?\s*</script>', h, re.S)
        if not m:
            continue
        d = json.loads(m.group(1))
        s0, dur = float(sc['start']), float(d.get('dur') or sc['dur'])
        shots = sorted((s for s in d.get('shots', []) if s.get('type') not in SEM_TELA and not s.get('keep')),
                       key=lambda s: float(s.get('at') or 0))
        for i, s in enumerate(shots):
            a = float(s.get('at') or 0)
            b = float(shots[i + 1].get('at')) if i + 1 < len(shots) else dur
            if b <= a:
                continue
            t = s.get('type')
            src = s.get('src') or ''
            if src and eh_real(src, reais):
                c = 'real'
            elif t in MAPA:
                c = 'mapa'
            elif src:
                c = 'gerada'
            elif t in CODIGO or not src:
                c = 'codigo'
            faixas.append((s0 + a, s0 + b, c, nome_base(src)))
    total = max((b for _, b, _, _ in faixas), default=0.0)
    soma = {}
    for a, b, c, _ in faixas:
        soma[c] = soma.get(c, 0.0) + (b - a)
    reais_t = sorted((a, b) for a, b, c, _ in faixas if c == 'real')
    ultimo = max((b for _, b in reais_t), default=0.0)
    buraco, cur = 0.0, 0.0
    for a, b in reais_t + [(total, total)]:
        buraco = max(buraco, a - cur)
        cur = max(cur, b)
    return {
        'duracao': round(total, 1),
        'real_s': round(soma.get('real', 0.0), 1),
        'real_pct': round(soma.get('real', 0.0) / total, 3) if total else 0.0,
        'ultimo_real_s': round(ultimo, 1),
        'buraco_sem_real_s': round(buraco, 1),
        'codigo_pct': round(soma.get('codigo', 0.0) / total, 3) if total else 0.0,
        'gerada_pct': round(soma.get('gerada', 0.0) / total, 3) if total else 0.0,
        'mapa_pct': round(soma.get('mapa', 0.0) / total, 3) if total else 0.0,
        'imagens_distintas': len({s for _, _, c, s in faixas if c in ('real', 'gerada') and s}),
    }


def veredito_visual(m, tem_real):
    mot = []
    if tem_real:
        if m['real_pct'] < REAL_MIN:
            mot.append(f"material real em {m['real_pct']:.0%} da tela (precisa ≥ {REAL_MIN:.0%})")
        if m['duracao'] and m['ultimo_real_s'] < REAL_ULTIMO * m['duracao']:
            mot.append(f"o real some aos {m['ultimo_real_s']:.0f} s de {m['duracao']:.0f} s (tem de aparecer no último quarto)")
        if m['buraco_sem_real_s'] > BURACO_MAX_S:
            mot.append(f"{m['buraco_sem_real_s']:.0f} s seguidos sem material real (máx. {BURACO_MAX_S} s)")
    if m['codigo_pct'] > CODIGO_MAX:
        mot.append(f"peça de código/ícone em {m['codigo_pct']:.0%} da tela (máx. {CODIGO_MAX:.0%}; só número e comparação)")
    minimo = int(m['duracao'] // 8)
    if m['imagens_distintas'] < minimo:
        mot.append(f"{m['imagens_distintas']} imagens distintas para {m['duracao']:.0f} s (precisa ≥ {minimo}, uma a cada ~8 s)")
    return mot


# ---------------------------------------------------------------- plano (antes do avatar)
def checar_plano(pasta):
    pasta = Path(pasta).expanduser()
    plano = ler_json(pasta / 'plano.json')
    if not plano:
        return None, [f'sem {pasta}/plano.json (passo 2c da ficha)']
    material = ler_json(pasta / 'material.json') or {'itens': []}
    roteiro = ler_json(pasta / 'roteiro-pt.json') or []
    pedido = ler_json(pasta / 'pedido.json') or {}
    mot = []
    chars = sum(len(c.get('speech') or '') for c in roteiro) if isinstance(roteiro, list) else 0
    est = round(chars / CHARS_POR_MIN * 60)
    perfil = pedido.get('perfil') or plano.get('perfil') or 'viral'
    pedida = plano.get('duracao_pedida_s')
    teto = int(pedida) if pedida else (TETO_AULA_S if perfil == 'aula' else TETO_VIRAL_S)
    if pedida and not str(plano.get('duracao_pedida_fonte') or '').strip():
        mot.append('duracao_pedida_s sem duracao_pedida_fonte (cite a frase do NEI; briefing do lead não vale)')
    if est > teto:
        mot.append(f'fala de {chars} caracteres ≈ {est} s (teto {teto} s): corte para caber')
    alvo = plano.get('duracao_alvo_s')
    if alvo and abs(est - int(alvo)) > max(15, 0.25 * int(alvo)):
        mot.append(f'fala ≈ {est} s, plano diz {alvo} s: ajuste a fala aos trechos')
    reais = [m for m in material.get('itens', []) if m.get('real', True)]
    trechos = plano.get('trechos') or []
    if len(trechos) < 4:
        mot.append(f'{len(trechos)} trechos no plano (mínimo 4: o que está NA TELA em cada parte da fala)')
    n = len(trechos) or 1
    com_real = [i for i, t in enumerate(trechos) if t.get('origem') == 'real']
    codigo = [t for t in trechos if t.get('origem') == 'codigo']
    if reais:
        if len(com_real) / n < REAL_MIN:
            mot.append(f'{len(com_real)} de {n} trechos com material real (precisa ≥ {REAL_MIN:.0%})')
        if not com_real or com_real[-1] < (n - 1) * REAL_ULTIMO:
            mot.append('o material real não aparece no último quarto do plano')
        nomes = {nome_base(m.get('arquivo')) for m in reais}
        usados = {nome_base(a) for t in trechos for a in (t.get('arquivos') or [])}
        fora = [x for x in nomes - usados if x]
        if len(fora) > max(1, len(nomes) // 2):
            mot.append(f'material real não usado no plano: {", ".join(sorted(fora)[:6])}')
    elif material.get('pedido_tem_material'):
        mot.append('o pedido trouxe links/arquivos e a captação não conseguiu nenhum material real '
                   '(peça o arquivo ao Nei no v3 em vez de seguir com ilustração)')
    if len(codigo) / n > CODIGO_MAX:
        mot.append(f'{len(codigo)} de {n} trechos são peça de código (máx. {CODIGO_MAX:.0%})')
    for i, t in enumerate(trechos):
        if not (t.get('tela') and t.get('deixa')):
            mot.append(f'trecho {i + 1} sem "deixa" (frase da fala) ou sem "tela"')
            break
    info = {'caracteres': chars, 'estimado_s': est, 'teto_s': teto, 'trechos': n, 'com_real': len(com_real),
            'material_real': len(reais)}
    return info, mot


def main(argv):
    if len(argv) < 3 or argv[1] not in ('plano', 'visual'):
        print(__doc__)
        return 2
    modo, alvo = argv[1], argv[2]
    if modo == 'plano':
        info, mot = checar_plano(alvo)
        if info is None:
            print('plano: ' + mot[0])
            return 2
        print('plano: ' + json.dumps(info, ensure_ascii=False))
    else:
        saida = Path(alvo).expanduser()
        material = ler_json(argv[3]) if len(argv) > 3 else None
        if material is None:
            pedido_dir = saida.parent / 'media' / 'material.json'
            material = ler_json(pedido_dir)
        reais = nomes_reais(material)
        try:
            m = medir_visual(saida, reais)
        except FileNotFoundError as e:
            print(f'visual: {e}')
            return 2
        tem_real = bool(reais) if reais is not None else m['real_s'] > 0
        print('visual: ' + json.dumps(m, ensure_ascii=False))
        mot = veredito_visual(m, tem_real)
    if mot:
        print(f'{modo} REPROVADO: ' + '; '.join(mot))
        if os.environ.get('MATERIAL_SEGUE') == '1':
            print('MATERIAL_SEGUE=1: seguindo por ordem do Nei')
            return 0
        return 1
    print(f'{modo} ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
