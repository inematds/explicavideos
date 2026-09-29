"""Explicavideos v2 — renderiza os blocos já construídos e grava os recibos que a montagem/publicação leem.

Uso: EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json python3 engine/v2/produce.py [N ...]
Retomável: blocos com status "rendered" e MP4 íntegro são pulados. Nenhuma chamada ao HeyGen.
Depois: python3 engine/assemble_languages.py e engine/publish_finished.py com o mesmo EXPLICAVIDEOS_CONFIG.
"""
from pathlib import Path
import json, os, subprocess, sys, fcntl

PROJECT = Path(__file__).resolve().parents[2]
CFG = json.loads(Path(os.environ.get('EXPLICAVIDEOS_CONFIG', PROJECT / 'examples/oswork-v2.json')).read_text())
ROOT = Path(CFG['output'])
HV = CFG.get('hyperframes', '0.8.77')
STATE = ROOT / 'verification/production.json'
# Reel (2.4): com "reel_profile" na config, render a 30 fps, loudness -14 LUFS e QA do makeshorts.
REEL = CFG.get('reel_profile')
FPS = '30' if REEL else '25'
QA = Path(os.path.expanduser(CFG.get('reel_qa', '~/projetos/makeshorts/.claude/skills/makeshorts/scripts/qa_short.py')))


def probe(path):
    out = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,r_frame_rate:format=duration', '-of', 'json', str(path)])
    return json.loads(out)


def update(key, value):
    """Atualiza um bloco no production.json sob lock (vários processos renderizam em paralelo)."""
    with open(str(STATE) + '.lock', 'w') as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        state = json.loads(STATE.read_text()) if STATE.exists() else {}
        state[key] = value
        STATE.write_text(json.dumps(state, indent=2))


def render(key):
    project, output = ROOT / 'final' / key, ROOT / 'final' / f'{key}.mp4'
    log = ROOT / 'logs' / f'render-{key}.log'
    with log.open('w') as f:
        subprocess.run(['npx', '--yes', f'hyperframes@{HV}', 'render', '.', '--fps', FPS, '--quality', 'delivery', '--crf', '20',
                        '--workers', '2', '--output', str(output)], cwd=project, stdout=f, stderr=subprocess.STDOUT, check=True)
    return output


def loudnorm(path, target=-14.0, tp=-1.5):
    """Normalização em duas passadas (mede, depois aplica linear) — acerta ±1 LU; vídeo copiado."""
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-af',
                        f'loudnorm=I={target}:TP={tp}:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True, check=True)
    m = json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}') + 1])
    af = (f"loudnorm=I={target}:TP={tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    tmp = path.with_suffix('.norm.mp4')
    subprocess.run(['ffmpeg', '-nostdin', '-y', '-loglevel', 'error', '-i', str(path), '-c:v', 'copy', '-af', af,
                    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', str(tmp)], check=True)
    tmp.replace(path)


def qa(key, out, single):
    """Portão do makeshorts. Duração só vale para o vídeo inteiro: com vários blocos, avisa e roda no montado."""
    rep = ROOT / 'verification' / f'qa-{key}.json'
    cmd = ['python3', str(QA), str(out), '--profile', REEL, '--srt', str(ROOT / 'final' / key / 'captions.srt'),
           '--sheet', str(ROOT / 'verification' / f'sheet-{key}.png'), '--report', str(rep)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout, flush=True)
    if r.returncode and single:
        update(key, {'status': 'qa_failed', 'file': str(out), 'qa_report': str(rep)})
        raise SystemExit(f'{key}: QA reprovou (ver {rep})')
    return r.returncode == 0


def main(parts):
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    downloads = json.loads((ROOT / 'verification/blocos-downloads.json').read_text())
    blocks = json.loads((ROOT / 'blocos/manifest.json').read_text())
    for b in blocks:
        if parts and b['part'] not in parts:
            continue
        key = f"{b['language']}-b{b['part']:02d}"
        report = json.loads((ROOT / f'verification/build-v2-{key}.json').read_text())
        assert not any('fallback' in w for w in report['warnings']), f'{key}: cenas sem roteiro visual'
        out = ROOT / 'final' / f'{key}.mp4'
        if state.get(key, {}).get('status') == 'rendered' and out.exists() and not '--force' in sys.argv:
            continue
        update(key, {'status': 'rendering'})
        render(key)
        p = probe(out)
        dur = float(p['format']['duration'])
        vids = [s for s in p['streams'] if s['codec_type'] == 'video']
        assert vids and vids[0]['r_frame_rate'] == f'{FPS}/1', f'{key}: fps {vids and vids[0]["r_frame_rate"]}'
        assert any(s['codec_type'] == 'audio' for s in p['streams']), f'{key}: sem áudio'
        assert abs(dur - float(downloads[key]['duration'])) < 1, f'{key}: duração {dur} != {downloads[key]["duration"]}'
        with (ROOT / 'verification' / f'decode-{key}.log').open('w') as f:
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(out), '-f', 'null', '-'], stderr=f, check=True)
        assert (ROOT / 'verification' / f'decode-{key}.log').read_text() == '', f'{key}: erro de decodificação'
        rec = {'status': 'rendered', 'file': str(out), 'duration': dur, 'engine': 'v2'}
        if REEL:
            loudnorm(out)
            single = sum(1 for x in blocks if x['language'] == b['language']) == 1
            rec['qa'] = 'ok' if qa(key, out, single) else ('reprovado' if single else 'rodar no montado')
            rec['reel_profile'] = REEL
        update(key, rec)
        print(key, 'rendered', dur, flush=True)


if __name__ == '__main__':
    main([int(a) for a in sys.argv[1:] if a.isdigit()])
