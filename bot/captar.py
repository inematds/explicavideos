#!/usr/bin/env python3
"""Captação do MATERIAL do pedido (2.34.12, Nei 20/11/2026, EV#187–191: "quando lhe mando um vídeo não está tendo
capacidade de planejar"). Roda na ficha ANTES do roteiro; o plano e o visual partem do que ela juntou.

Uso: echo "<texto do pedido>" | python3 bot/captar.py <pasta-do-bot> <pasta-de-material>
     (a pasta de material é ~/projetos/output/<id>/media/real — o build copia de lá)

Junta, para cada link e arquivo do pedido (e dos .md/.json locais que ele cita, um nível):
  - vídeo de rede social/YouTube pelo inemavox (`baixar_v1.py`, cookies do Firefox), até 3 min;
  - se não baixar, ou se for notícia: a foto principal da página (og:image) e o og:video, com crédito do site;
  - arquivos locais citados: foto/vídeo anexado pelo Nei (`facebook-*`, anexo do bot) entram como real.
Grava `<pasta-do-bot>/material.json`:
  {"pedido_tem_material": bool, "itens": [{"arquivo", "tipo": "foto|video", "real": true, "origem", "credito",
   "largura", "altura", "duracao_s", "mostra": ""}], "falhas": [{"origem", "motivo"}]}
O agente da ficha OLHA cada item, preenche "mostra" e marca "real": false no que não é do fato (ilustração antiga).
Miniatura pequena (< 500 px) não conta como material. Nada de API: só páginas públicas e o inemavox.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

INEMAVOX = Path.home() / 'projetos/inemavox'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
SOCIAL = ('youtube.com', 'youtu.be', 'tiktok.com', 'instagram.com', 'facebook.com', 'fb.watch', 'x.com',
          'twitter.com', 'kwai.com', 'threads.net')
PULA = ('.pdf', '.zip', '.xml', '.rss')
IMG = {'.jpg', '.jpeg', '.png', '.webp'}
VID = {'.mp4', '.mov', '.webm', '.mkv'}
MAX_LINKS = 12
MIN_LADO = 500


def run(cmd, timeout):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None


def medir(p):
    r = run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height:format=duration',
             '-of', 'json', str(p)], 30)
    try:
        d = json.loads(r.stdout)
        s = (d.get('streams') or [{}])[0]
        dur = float((d.get('format') or {}).get('duration') or 0)
        return int(s.get('width') or 0), int(s.get('height') or 0), round(dur, 1)
    except (AttributeError, ValueError, TypeError):
        return 0, 0, 0.0


def baixar_http(url, destino, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r, open(destino, 'wb') as f:
        shutil.copyfileobj(r, f)
    return destino


def pagina(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'pt-BR,pt;q=0.9'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.geturl(), r.read(3_000_000).decode('utf-8', 'ignore')


def meta(h, prop):
    for m in re.finditer(r'<meta\b[^>]*>', h, re.I):
        tag = m.group(0)
        if re.search(rf'(?:property|name)=["\']{re.escape(prop)}["\']', tag, re.I):
            c = re.search(r'content=["\']([^"\']+)["\']', tag, re.I)
            if c:
                return html.unescape(c.group(1)).strip()
    return ''


def slug(s, n=28):
    s = re.sub(r'[^a-z0-9]+', '-', urllib.parse.urlparse(s).netloc.lower().replace('www.', '') + '-' +
               urllib.parse.urlparse(s).path.lower())
    return s.strip('-')[:n].strip('-') or 'fonte'


def extrair(texto):
    urls, arquivos = [], []
    for u in re.findall(r'https?://[^\s<>"\'`)\]]+', texto):
        u = u.rstrip('.,;:')
        if u not in urls and not u.lower().split('?')[0].endswith(PULA):
            urls.append(u)
    for p in re.findall(r'(?:~|/home/)[^\s<>"\'`,;)]+', texto):
        p = Path(p.rstrip('.:').replace('~', str(Path.home()), 1))
        if p.exists() and p not in arquivos:
            arquivos.append(p)
    return urls, arquivos


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    pasta, mat = Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser()
    mat.mkdir(parents=True, exist_ok=True)
    texto = sys.stdin.read()
    urls, arquivos = extrair(texto)
    # um nível: .md/.json citados trazem links e as fotos que a apuração já juntou
    for p in list(arquivos):
        alvos = sorted(p.glob('*.md')) + sorted(p.glob('*.json')) if p.is_dir() else [p]
        for a in alvos:
            if a.suffix.lower() in ('.md', '.json') and a.stat().st_size < 400_000:
                u2, f2 = extrair(a.read_text(errors='ignore'))
                urls += [u for u in u2 if u not in urls]
                arquivos += [f for f in f2 if f not in arquivos]
        if p.is_dir():
            for f in sorted(p.iterdir()):
                if f.suffix.lower() in IMG | VID and re.match(r'(facebook|real|anexo|foto|video)[-_]', f.name, re.I):
                    if f not in arquivos:
                        arquivos.append(f)
    itens, falhas, n = [], [], 0

    def novo(src, tipo, origem, credito):
        nonlocal n
        w, h, dur = medir(src)
        if max(w, h) < MIN_LADO:
            falhas.append({'origem': origem, 'motivo': f'só miniatura {w}×{h} (não conta)'})
            src.unlink(missing_ok=True)
            return
        n += 1
        itens.append({'arquivo': str(src), 'tipo': tipo, 'real': True, 'origem': origem, 'credito': credito,
                      'largura': w, 'altura': h, 'duracao_s': dur if tipo == 'video' else 0, 'mostra': ''})

    for f in arquivos:
        if f.is_file() and f.suffix.lower() in IMG | VID:
            d = mat / f'real-{len(itens) + 1:02d}-{re.sub(r"[^a-z0-9]+", "-", f.stem.lower())[:30]}{f.suffix.lower()}'
            shutil.copy2(f, d)
            novo(d, 'video' if f.suffix.lower() in VID else 'foto', str(f), 'anexo do pedido')

    vistos, unicos = set(), []
    for u in urls:   # o mesmo post aparece como /share/… e como link canônico: 1 vez só
        chave = (re.findall(r'\d{10,}', u) or [u.split('?')[0].rstrip('/')])[-1]
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(u)
    for u in unicos[:MAX_LINKS]:
        host = urllib.parse.urlparse(u).netloc.lower()
        nome = f'real-{len(itens) + 1:02d}-{slug(u)}'
        if any(s in host for s in SOCIAL):
            tmp = mat / f'.baixa-{nome}'
            r = run(['python3', str(INEMAVOX / 'baixar_v1.py'), '--url', u, '--outdir', str(tmp), '--quality', '720p'], 240)
            vids = sorted((p for p in tmp.rglob('*') if p.suffix.lower() in VID), key=lambda p: p.stat().st_size) if tmp.exists() else []
            if vids:
                d = mat / f'{nome}{vids[-1].suffix.lower()}'
                shutil.move(str(vids[-1]), d)
                shutil.rmtree(tmp, ignore_errors=True)
                novo(d, 'video', u, host.replace('www.', ''))
                continue
            shutil.rmtree(tmp, ignore_errors=True)
            erro = ((r.stdout + r.stderr) if r else 'tempo esgotado').strip().splitlines()
            falhas.append({'origem': u, 'motivo': 'vídeo não baixou: ' + next((e for e in reversed(erro) if 'ERRO' in e or 'ERROR' in e), erro[-1] if erro else '?')[:200]})
        try:
            final, h = pagina(u)
        except Exception as e:  # noqa: BLE001 — página fora/bloqueada vira falha registrada, não para a ficha
            falhas.append({'origem': u, 'motivo': f'página não abriu: {e}'[:200]})
            continue
        site = meta(h, 'og:site_name') or urllib.parse.urlparse(final).netloc.replace('www.', '')
        titulo = meta(h, 'og:title')
        for prop, tipo in (('og:video', 'video'), ('og:video:url', 'video'), ('og:image', 'foto')):
            src = meta(h, prop)
            if not src or (tipo == 'video' and not src.lower().split('?')[0].endswith(tuple(VID))):
                continue
            src = urllib.parse.urljoin(final, src)
            ext = Path(urllib.parse.urlparse(src).path).suffix.lower()
            ext = ext if ext in IMG | VID else ('.mp4' if tipo == 'video' else '.jpg')
            d = mat / f'{nome}{ext}'
            try:
                baixar_http(src, d)
                novo(d, tipo, u, f'{site}' + (f' · {titulo[:80]}' if titulo else ''))
                break
            except Exception as e:  # noqa: BLE001
                falhas.append({'origem': u, 'motivo': f'{prop} não baixou: {e}'[:200]})
    shutil.rmtree(mat / 'dub_work', ignore_errors=True)   # sobra do inemavox
    out = {'pedido_tem_material': bool(urls or arquivos), 'itens': itens, 'falhas': falhas}
    (pasta / 'material.json').write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    fotos = sum(i['tipo'] == 'foto' for i in itens)
    print(f'material: {len(itens)} itens reais ({fotos} fotos, {len(itens) - fotos} vídeos), {len(falhas)} falhas '
          f'→ {pasta / "material.json"}')
    for fl in falhas:
        print(f"  falhou: {fl['origem'][:90]} — {fl['motivo']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
