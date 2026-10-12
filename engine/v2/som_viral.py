#!/usr/bin/env python3
"""Som do perfil viral (PADRAO-VIRAL.md): trilha baixa sob a voz + efeitos nos cortes e números.

Uso: som_viral.py <pasta-do-bloco final/pt-bNN> <video.mp4> <saida.mp4> [--trilha=<mp3>] [--sfx=<pasta>]
Lê os tempos dos shots das composições (scene-*.html) e dos hosts (index.html). Tudo local, sem API.
- whoosh no início de cada shot que troca a tela; boom no impacto do bignum e no carimbo; pop nas palavras
  da cinetica; riser antes do capitulo. Trilha a -24 dB sob a voz, com fade no fim."""
import json, re, subprocess, sys
from pathlib import Path

args = [a for a in sys.argv[1:] if not a.startswith('--')]
opt = {a.split('=')[0]: a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith('--') and '=' in a}
blk, video, saida = Path(args[0]), args[1], args[2]
# biblioteca local (~/projetos/biblioteca-sons: trilhas MusicGen + efeitos sintetizados, sem API); --trilha aceita nome ou caminho
BIB = Path(opt.get('--biblioteca', str(Path.home() / 'projetos/biblioteca-sons')))
TRILHA = opt.get('--trilha', 'noticia-urgente')
if not Path(TRILHA).exists():
    TRILHA = str(BIB / 'trilhas' / f'{TRILHA}.wav')
if not Path(TRILHA).exists():
    TRILHA = str(Path.home() / 'projetos/cardshorts/musicas/tensa.mp3')
SFX = Path(opt.get('--sfx', str(BIB / 'sfx')))
# evento → famílias da biblioteca (gira entre as variações para não repetir o mesmo som)
FAM = {'whoosh': ['whoosh', 'swoosh'], 'boom': ['impacto', 'boom'], 'riser': ['riser'], 'pop': ['pop', 'clique'],
       'buzz': ['glitch'], 'braam': ['braam'], 'ding': ['ding']}
_giro = {}


def arquivo(e):
    vs = sorted(p for f in FAM.get(e, [e]) for p in SFX.glob(f'{f}-*.wav')) or sorted(SFX.glob(f'{e}*.wav'))
    if not vs:
        raise SystemExit(f'sem efeito {e!r} em {SFX}')
    i = _giro.get(e, 0)
    _giro[e] = i + 1
    return vs[i % len(vs)]

idx = (blk / 'index.html').read_text()
starts = {m[0]: float(m[1]) for m in re.findall(r'id="(scene-\d+)" class="clip"[^>]*data-start="([\d.]+)"', idx)}
ev = []   # (tempo, efeito, volume)
for f in sorted((blk / 'compositions').glob('scene-*.html')):
    sid = f.stem
    S = json.loads(re.search(r'V2\.scene\("[^"]+", (\{.*\})\);</script>', f.read_text(), re.S).group(1).replace('<\\/', '</'))
    s0 = starts[sid]
    for sh in S['shots']:
        t = s0 + sh['at']
        tp = sh['type']
        if tp in ('capa',):
            if sh.get('selo_at') is not None:
                ev.append((s0 + sh['selo_at'], 'boom', 0.5))
            continue
        if tp == 'carimbo':
            ev.append((t + 0.24, 'boom', 0.7))
            continue
        if tp == 'capitulo':
            ev.append((max(0, t - 0.6), 'riser', 0.45))
            ev.append((t + 0.1, 'braam', 0.5))
        if tp == 'cta':
            ev.append((t + 0.4, 'ding', 0.45))
        if not sh.get('keep'):
            ev.append((t, 'whoosh', 0.45))
        if tp == 'bignum':
            ev.append((s0 + sh.get('hit_at', sh['at'] + 0.8), 'boom', 0.6))
        if tp == 'barra' and sh.get('hit_at') is not None:
            ev.append((s0 + sh['hit_at'], 'boom', 0.55))
        if tp == 'cinetica':
            for p in sh.get('palavras', []):
                if p.get('at') is not None:
                    ev.append((s0 + p['at'], 'pop', 0.5))
                if p.get('risca_at') is not None:
                    ev.append((s0 + p['risca_at'], 'buzz', 0.3))
        for p in sh.get('pontos', []):
            ev.append((s0 + p['at'], 'whoosh', 0.3))
ev.sort()
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video], capture_output=True, text=True).stdout)
# trilha repetida com emenda em crossfade (2 s) até cobrir o vídeo — sem corte seco no loop
tdur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', TRILHA], capture_output=True, text=True).stdout)
nrep = max(1, int((dur + 4) // max(1.0, tdur - 2)) + 1)
ins, fil = ['-i', video] + sum([['-i', TRILHA] for _ in range(nrep)], []), []
cad = '[1:a]'
for r in range(2, nrep + 1):
    fil.append(f'{cad}[{r}:a]acrossfade=d=2:c1=tri:c2=tri[x{r}]')
    cad = f'[x{r}]'
fil.append(f'{cad}atrim=0:{dur:.2f},volume=0.075,afade=t=in:d=0.6,afade=t=out:st={max(0, dur - 2):.2f}:d=2[mus]')
labs = ['[0:a]', '[mus]']
for i, (t, e, v) in enumerate(ev):
    ins += ['-i', str(arquivo(e))]
    ms = int(max(0, t) * 1000)
    fil.append(f'[{i + 1 + nrep}:a]volume={v},adelay={ms}|{ms}[s{i}]')
    labs.append(f'[s{i}]')
fil.append(f'{"".join(labs)}amix=inputs={len(labs)}:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]')
cmd = ['ffmpeg', '-v', 'error', '-nostdin', '-y'] + ins + ['-filter_complex', ';'.join(fil), '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', saida]
subprocess.run(cmd, check=True)
print(f'{len(ev)} efeitos + trilha → {saida}')
