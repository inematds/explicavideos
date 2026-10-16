#!/usr/bin/env python3
"""QA do perfil viral (PADRAO-VIRAL.md): reprova vídeo com tela vazia ou parada.

Uso: qa_viral.py <video.mp4> [--saida <pasta>] [--vazio 0.90] [--liso 0.40] [--parado 2.0]
- em cada quadro (amostra a cada 0,5 s, reduzido a 192 px de largura), fração de blocos 8×8 lisos (desvio-padrão < 6 em cinza).
- vazio (REPROVA): mais de 90% liso = tela de uma cor só (ex.: carimbo sem keep vira tela preta).
- liso (AVISO, 15/10/2026): mais de 40% liso. Antes reprovava, mas foto escura boa (rio, céu, fumaça) mede 0,5–0,63 e painel
  meio vazio mede 0,48–0,52: o pixel não separa os dois. Vira aviso, com a folha dos momentos marcados para olhar.
- parado (REPROVA): diferença média entre amostras vizinhas < 1,2 (0–255) por mais de 2 s seguidos = tela parada.
- grava a folha de quadros (sheet-viral-<nome>.jpg), a dos momentos marcados (sheet-marcados-<nome>.jpg, com o segundo
  escrito) e o relatório JSON ao lado; cópia em <video>.qa.json, que o enviar_bot_v3.mjs lê para pôr o veredito na mensagem.
Saída: APROVADO / APROVADO COM AVISO (código 0) · REPROVADO (código 1)."""
import json, subprocess, sys
from pathlib import Path

import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
video = Path(args[0])
out = Path(opt.get('--saida', video.parent))
LIM_VAZIO, LIM_LISO, LIM_PARADO, PASSO = float(opt.get('--vazio', 0.90)), float(opt.get('--liso', 0.40)), float(opt.get('--parado', 2.0)), 0.5

dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video)],
                           capture_output=True, text=True).stdout)
w = 192
probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(video)],
                       capture_output=True, text=True).stdout.strip().split(',')
hh = int(round(w * int(probe[1]) / int(probe[0]) / 2) * 2)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', str(video), '-vf', f'fps={1 / PASSO},scale={w}:{hh},format=gray', '-f', 'rawvideo', '-'],
                     capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, hh, w).astype(np.float32)

vazios, dif = [], []
for i, f in enumerate(fr):
    b = f[:hh // 8 * 8, :w // 8 * 8].reshape(hh // 8, 8, w // 8, 8).std(axis=(1, 3))
    vazios.append(float((b < 6).mean()))
    if i:
        dif.append(float(np.abs(f - fr[i - 1]).mean()))

# trechos com o avatar em tela cheia ("rosto") não contam como tela vazia (relatório do build)
_rel = json.loads(Path(opt['--relatorio']).read_text()) if '--relatorio' in opt else {}
# avatar em tela cheia e mapa: grandes áreas sólidas que são conteúdo, não tela vazia
rostos = _rel.get('rostos', []) + _rel.get('mapas', [])
em_rosto = lambda t: any(a - 0.3 <= t <= b + 0.3 for a, b in rostos)
def marcados(lim):
    ruim = [v > lim and not em_rosto(i * PASSO) for i, v in enumerate(vazios)]
    # um quadro isolado (o mergulho de 0,3 s entre cenas) não conta: só 2 amostras seguidas (≥ 1 s)
    return [(round(i * PASSO, 1), round(vazios[i], 2)) for i in range(len(ruim)) if ruim[i] and ((i and ruim[i - 1]) or (i + 1 < len(ruim) and ruim[i + 1]))]


def trechos(qs):   # [(t, v)…] → [[início, fim]…] (amostras a ≤ 1 s viram um trecho)
    out = []
    for t, _ in qs:
        if out and t - out[-1][1] <= 1.0:
            out[-1][1] = t
        else:
            out.append([t, t])
    return out


ruins_vazio = marcados(LIM_VAZIO)
lisos = [q for q in marcados(LIM_LISO) if q not in ruins_vazio]
parados, run = [], 0
for i, d in enumerate(dif):
    run = run + 1 if d < 1.2 else 0
    if run * PASSO > LIM_PARADO and (not parados or parados[-1][1] != 'aberto'):
        parados.append([round((i + 1 - run) * PASSO, 1), 'aberto'])
    if run == 0 and parados and parados[-1][1] == 'aberto':
        parados[-1][1] = round(i * PASSO, 1)
if parados and parados[-1][1] == 'aberto':
    parados[-1][1] = round(len(dif) * PASSO, 1)

# folha de quadros: 12 quadros espalhados
sheet = out / f'sheet-viral-{video.stem}.jpg'
n = 12
tiles = []
for k in range(n):
    t = dur * (k + 0.5) / n
    png = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', f'{t:.2f}', '-i', str(video), '-frames:v', '1', '-vf', 'scale=480:-2', '-f', 'image2pipe', '-vcodec', 'png', '-'],
                         capture_output=True).stdout
    tiles.append(Image.open(__import__('io').BytesIO(png)).convert('RGB'))
tw, th = tiles[0].size
cols = 6 if th < tw else 6
rows = (n + cols - 1) // cols
img = Image.new('RGB', (cols * tw, rows * th))
for k, t in enumerate(tiles):
    img.paste(t, ((k % cols) * tw, (k // cols) * th))
img.save(sheet, quality=85)

# folha dos momentos marcados: 1 quadro por trecho (até 12), faixa com o tipo e o segundo (vermelho reprova, amarelo avisa)
marc = ([('VAZIO', a, b) for a, b in trechos(ruins_vazio)] + [('PARADO', a, b) for a, b in parados]
        + [('liso', a, b) for a, b in trechos(lisos)])[:12]
sheet_m = None
if marc:
    from PIL import ImageDraw
    tiles = []
    for tipo, a, b in marc:
        png = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-ss', f'{(a + b) / 2:.2f}', '-i', str(video), '-frames:v', '1', '-vf', 'scale=360:-2',
                              '-f', 'image2pipe', '-vcodec', 'png', '-'], capture_output=True).stdout
        im = Image.open(__import__('io').BytesIO(png)).convert('RGB')
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, im.width, 34], fill=(150, 110, 0) if tipo == 'liso' else (200, 30, 30))
        d.text((8, 10), f'{tipo}  {a:g}-{b:g} s', fill=(255, 255, 255))
        tiles.append(im)
    tw, th = tiles[0].size
    cols = min(6, len(tiles))
    img = Image.new('RGB', (cols * tw, -(-len(tiles) // cols) * th))
    for k, t in enumerate(tiles):
        img.paste(t, ((k % cols) * tw, (k // cols) * th))
    sheet_m = out / f'sheet-marcados-{video.stem}.jpg'
    img.save(sheet_m, quality=85)

seg = lambda tr: ', '.join(f'{a:g}–{b:g} s' for a, b in tr)
ok = not ruins_vazio and not parados
motivo = '; '.join(([f'tela vazia (uma cor só) em {seg(trechos(ruins_vazio))}'] if ruins_vazio else [])
                   + ([f'tela parada em {seg(parados)}'] if parados else []))
aviso = f'área lisa (foto escura ou painel vazio?) em {seg(trechos(lisos))}' if lisos else ''
rel = {'video': str(video), 'dur': round(dur, 2), 'ok': ok, 'vazio_max': round(max(vazios), 2), 'vazio_medio': round(float(np.mean(vazios)), 2),
       'quadros_vazios': ruins_vazio, 'trechos_parados': parados, 'quadros_lisos': lisos, 'motivo': motivo, 'aviso': aviso,
       'sheet': str(sheet), 'sheet_marcados': str(sheet_m) if sheet_m else None}
(out / f'qa-viral-{video.stem}.json').write_text(json.dumps(rel, indent=1, ensure_ascii=False))
# cópia ao lado do vídeo: o enviar_bot_v3.mjs acha sozinha (<video>.qa.json) e põe o veredito na mensagem do bot
Path(str(video) + '.qa.json').write_text(json.dumps(rel, indent=1, ensure_ascii=False))
print(json.dumps({k: rel[k] for k in ('vazio_max', 'vazio_medio', 'motivo', 'aviso', 'sheet_marcados')}, ensure_ascii=False))
print('REPROVADO' if not ok else 'APROVADO COM AVISO' if lisos else 'APROVADO')
sys.exit(0 if ok else 1)
