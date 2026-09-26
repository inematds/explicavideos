"""Prepara o diretório de saída v2 a partir de uma produção v1 concluída (sem nova geração no HeyGen).

Copia manifesto, roteiro, transcrições e tempos de cena; liga (symlink) os vídeos do avatar.
Nunca sobrescreve o que já existe no destino. Não toca no diretório v1.
"""
from pathlib import Path
import json, os, shutil, sys

PROJECT = Path(__file__).resolve().parents[2]
CFG = json.loads(Path(os.environ.get('EXPLICAVIDEOS_CONFIG', PROJECT / 'examples/oswork-v2.json')).read_text())
ROOT, V1 = Path(CFG['output']), Path(CFG['v1_output'])


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def main():
    for lang in CFG['languages']:
        assert (V1 / f'verification/assembled-{lang}.json').exists(), f'produção v1 ({lang}) não está montada'
    for d in ['assets', 'blocos', 'docs', 'verification', 'final', 'align', 'visual-v2', 'logs']:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    copy(V1 / 'blocos/manifest.json', ROOT / 'blocos/manifest.json')
    for lang in CFG['languages']:
        copy(V1 / f'docs/lesson-{lang}.json', ROOT / f'docs/lesson-{lang}.json')
    copy(V1 / 'verification/blocos-downloads.json', ROOT / 'verification/blocos-downloads.json')
    for b in json.loads((ROOT / 'blocos/manifest.json').read_text()):
        key = f"{b['language']}-b{b['part']:02d}"
        copy(V1 / f'verification/transcript-{key}.json', ROOT / f'verification/transcript-{key}.json')
        copy(V1 / f'final/{key}/alignment.json', ROOT / f'align/{key}.json')
        for ext in ['mp4', 'mp3']:
            link = ROOT / f'assets/nei-{key}.{ext}'
            if not link.exists():
                link.symlink_to((V1 / f'assets/nei-{key}.{ext}').resolve())
    print('ok', ROOT)


if __name__ == '__main__':
    main()
