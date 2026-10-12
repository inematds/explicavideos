#!/usr/bin/env python3
"""QA do perfil viral (PADRAO-VIRAL.md): reprova vídeo com tela vazia ou parada.

Uso: qa_viral.py <video.mp4> [--saida <pasta>] [--vazio 0.40] [--parado 2.0]
- vazio: em cada quadro (amostra a cada 0,5 s, reduzido a 192 px de largura), fração de blocos 8×8 lisos
  (desvio-padrão < 6 em cinza). Mais de 40% liso = tela vazia.
- parado: diferença média entre amostras vizinhas < 1,2 (0–255) por mais de 2 s seguidos = tela parada.
- grava a folha de quadros (sheet-viral-<nome>.jpg) e o relatório JSON ao lado.
Saída: APROVADO / REPROVADO (código 0 / 1)."""
import json, subprocess, sys
from pathlib import Path

import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
video = Path(args[0])
out = Path(opt.get('--saida', video.parent))
LIM_VAZIO, LIM_PARADO, PASSO = float(opt.get('--vazio', 0.40)), float(opt.get('--parado', 2.0)), 0.5

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
ruim = [v > LIM_VAZIO and not em_rosto(i * PASSO) for i, v in enumerate(vazios)]
# um quadro isolado (o mergulho de 0,3 s entre cenas) não reprova: só 2 amostras seguidas (≥ 1 s)
ruins_vazio = [(round(i * PASSO, 1), round(vazios[i], 2)) for i in range(len(ruim)) if ruim[i] and ((i and ruim[i - 1]) or (i + 1 < len(ruim) and ruim[i + 1]))]
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

ok = not ruins_vazio and not parados
rel = {'video': str(video), 'dur': round(dur, 2), 'ok': ok, 'vazio_max': round(max(vazios), 2), 'vazio_medio': round(float(np.mean(vazios)), 2),
       'quadros_vazios': ruins_vazio, 'trechos_parados': parados, 'sheet': str(sheet)}
(out / f'qa-viral-{video.stem}.json').write_text(json.dumps(rel, indent=1, ensure_ascii=False))
print(json.dumps({k: rel[k] for k in ('vazio_max', 'vazio_medio', 'quadros_vazios', 'trechos_parados', 'sheet')}, ensure_ascii=False))
print('APROVADO' if ok else 'REPROVADO')
sys.exit(0 if ok else 1)
