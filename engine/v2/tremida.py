#!/usr/bin/env python3
"""Detecta TREMIDA de câmera: a escala da tela sobe e desce rápido (aproxima/afasta) sem trocar de imagem.

Uso: tremida.py <video.mp4> [--janela=0.5] [--salto=0.012] [--max=0]
- 25 quadros/s reduzidos a 320 px; compara cada quadro com o de 2 quadros antes e estima a escala global
  (0,96–1,04) que melhor encaixa, só na área central (fora avatar no canto/terço de baixo e fora a legenda).
- tremida = dentro de --janela s a escala sobe ≥ --salto E desce ≥ --salto (ex.: 1,028 e 0,96), cada sentido em 2 quadros seguidos.
- Reprova (código 1) se houver mais de --max ocorrências (o qa_viral usa 2). Sem OpenCV: avisa e sai 0.
Calibragem (17/11/2026, fade > 9 de brilho ignorado): fim-software 2.27 (pontos 1,18 vai e volta) = 3; o mesmo vídeo no
2.28.11 (câmera parada) = 0; rtex = 0; r7ex = 0. Poucos vídeos: recalibrar se aparecer falso positivo/negativo.
Serve para qualquer motor (explicavideos, r7ex, rtex, rtexjp, r7exp). Saída: JSON numa linha + veredito."""
import json, subprocess, sys

import numpy as np

try:
    import cv2
except ImportError:
    print('AVISO: sem OpenCV (cv2); tremida não medida'); sys.exit(0)

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: a.split('=')[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
video = args[0]
JAN, SALTO, MAX = float(opt.get('--janela', 0.5)), float(opt.get('--salto', 0.012)), int(opt.get('--max', 0))
FPS, K = 25, 2

pw, ph = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                         '-of', 'csv=p=0', video], capture_output=True, text=True).stdout.strip().split(',')[:2]
vertical = int(ph) > int(pw)
W = 180 if vertical else 320
H = int(round(W * int(ph) / int(pw) / 2) * 2)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', video, '-vf', f'fps={FPS},scale={W}:{H},format=gray',
                      '-f', 'rawvideo', '-'], capture_output=True).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)

m = np.zeros((H, W), bool)
if vertical:   # 9:16: avatar/legenda no terço de baixo
    m[int(H * .12):int(H * .62), int(W * .08):int(W * .92)] = True
else:          # 16:9: avatar mini no canto direito, legenda embaixo
    m[int(H * .14):int(H * .72), int(W * .06):int(W * .72)] = True

S = np.arange(0.96, 1.0401, 0.004)
Ms = [cv2.getRotationMatrix2D((W / 2, H / 2), 0, s) for s in S]


def escala(a, b):
    e0 = np.abs(a - b)[m].mean()
    if e0 < 0.3 or e0 > 25 or abs(a[m].mean() - b[m].mean()) > 9.0:   # sem mudança, corte/ruído (tudo muda) ou fade (brilho muda) = não é câmera
        return 1.0
    es = [np.abs(cv2.warpAffine(a, M, (W, H)) - b)[m].mean() for M in Ms]
    i = int(np.argmin(es))
    return float(S[i]) if es[i] < e0 else 1.0


s = np.array([escala(f[i - K], f[i]) for i in range(K, len(f))])
t = np.arange(K, len(f)) / FPS
n = max(2, int(JAN * FPS))
ev = []
up = (s >= 1 + SALTO).astype(int); dn = (s <= 1 - SALTO).astype(int)
up2 = np.r_[up[1:] & up[:-1], 0]; dn2 = np.r_[dn[1:] & dn[:-1], 0]   # 2 quadros seguidos no mesmo sentido (zoom real, não ruído)
for i in range(len(s) - n):
    if up2[i:i + n].any() and dn2[i:i + n].any() and (not ev or t[i] - ev[-1] > 1):
        ev.append(round(float(t[i]), 2))
ok = len(ev) <= MAX
print(json.dumps({'video': video, 'tremidas': len(ev), 'em_s': ev[:30]}, ensure_ascii=False))
print('APROVADO' if ok else f'REPROVADO: tremida de câmera (aproxima/afasta rápido) em {len(ev)} pontos: '
      + ', '.join(f'{x:g} s' for x in ev[:12]))
sys.exit(0 if ok else 1)
