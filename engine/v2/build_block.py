"""Explicavideos v2 — monta um bloco HyperFrames a partir do roteiro visual (visual-v2/<key>.json).

Uso:
  EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json python3 engine/v2/build_block.py 1 [--strict]

Cada cena do roteiro visual é uma lista de shots; todo tempo é uma DEIXA FALADA (trecho da fala da cena)
que é resolvida para segundos pela transcrição real (Whisper/Groq), nunca um número digitado.
Legenda = texto do roteiro (grafia correta) com os tempos da transcrição.
"""
from pathlib import Path
import json, re, sys, shutil, difflib, unicodedata, html, os, bisect

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
CONFIG = Path(os.environ.get('EXPLICAVIDEOS_CONFIG', PROJECT / 'examples/oswork-v2.json')).resolve()
CFG = json.loads(CONFIG.read_text())
ROOT = Path(CFG['output'])
RUNTIME = HERE / 'runtime'
E = html.escape

SHOT_TYPES = {'bullets', 'hub', 'pipeline', 'orbs', 'podium', 'statement', 'radar', 'lanes', 'compare', 'chat', 'terminal',
              'filetree', 'counter', 'steps', 'quiz', 'timeline', 'flow', 'fields', 'keyword', 'module_intro', 'svg'}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode())


def stamp(t):
    ms = round(t * 1000)
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


class BuildError(Exception):
    pass


class Timing:
    """Mapeia cada palavra do roteiro (texto correto) para o tempo medido na transcrição."""

    def __init__(self, scenes, words):
        self.tokens = []          # (texto original, norm, índice da cena)
        self.bounds = []
        for k, s in enumerate(scenes):
            self.bounds.append(len(self.tokens))
            for w in s['speech'].split():
                self.tokens.append((w, norm(w), k))
        self.bounds.append(len(self.tokens))
        spoken = [norm(w['word']) for w in words]
        m = difflib.SequenceMatcher(None, [t[1] for t in self.tokens], spoken, autojunk=False)
        self.ratio = m.ratio()
        mp = {}
        for b in m.get_matching_blocks():
            for i in range(b.size):
                mp[b.a + i] = b.b + i
        keys = sorted(mp)
        self.t = []
        for i in range(len(self.tokens)):
            if i in mp:
                self.t.append(words[mp[i]]['start'])
                continue
            k = bisect.bisect_left(keys, i)
            lo = keys[k - 1] if k > 0 else None
            hi = keys[k] if k < len(keys) else None
            if lo is None and hi is None:
                self.t.append(0.0)
            elif lo is None:
                self.t.append(words[mp[hi]]['start'] - 0.3 * (hi - i))
            elif hi is None:
                self.t.append(words[mp[lo]]['end'] + 0.3 * (i - lo - 1))
            else:
                a, b = words[mp[lo]]['end'], words[mp[hi]]['start']
                self.t.append(a + (b - a) * (i - lo) / (hi - lo))
        for i in range(1, len(self.t)):
            self.t[i] = max(self.t[i], self.t[i - 1])


def find_cue(timing, k, cue, cursor):
    """Retorna o índice global da primeira ocorrência da deixa na cena k, a partir de cursor (global)."""
    lo, hi = timing.bounds[k], timing.bounds[k + 1]
    occ = 1
    m = re.match(r'^(.*)#(\d+)$', cue)
    if m:
        cue, occ = m.group(1), int(m.group(2))
    cw = [norm(w) for w in cue.split() if norm(w)]
    if not cw:
        raise BuildError(f'deixa vazia: {cue!r}')
    seq = [t[1] for t in timing.tokens]
    for start in ([max(cursor, lo)] + ([lo] if cursor > lo else [])):
        found = 0
        for j in range(start, hi - len(cw) + 1):
            if seq[j:j + len(cw)] == cw:
                found += 1
                if found == occ:
                    return j, start != max(cursor, lo)
    raise BuildError(f'deixa não encontrada na cena: {cue!r}')


def words_of(text):
    return [w for w in re.sub(r'\*\*|\+\+|~~', '', str(text)).split() if w]


def resolve_scene(timing, k, scene_start, spec, warnings, n, strict):
    """Troca todas as deixas (campos 'at' e '*_at') por segundos relativos à cena."""
    lo = timing.bounds[k]
    rel = lambda gi: round(max(0.0, timing.t[gi] - scene_start), 3)

    def cue_time(v, cursor, where):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if strict:
                raise BuildError(f'cena {n}: {where} usa segundos ({v}); use uma deixa falada')
            return float(v), cursor
        gi, back = find_cue(timing, k, str(v), cursor)
        if back:
            warnings.append(f'cena {n}: deixa {v!r} ({where}) está antes da deixa anterior')
        return rel(gi), gi

    def walk(obj, cursor, where):
        if isinstance(obj, dict):
            for key in list(obj.keys()):
                val = obj[key]
                if (key == 'at' or key.endswith('_at')) and isinstance(val, (str, int, float)) and not isinstance(val, bool):
                    obj[key], _ = cue_time(val, cursor, f'{where}.{key}')
                elif key == 'swaps_at' and isinstance(val, list):
                    obj[key] = [cue_time(v, cursor, where)[0] for v in val]
                else:
                    walk(val, cursor, f'{where}.{key}')
        elif isinstance(obj, list):
            for i, it in enumerate(obj):
                walk(it, cursor, f'{where}[{i}]')

    shots = spec.get('shots', [])
    cursor = lo
    for i, sh in enumerate(shots):
        if sh.get('type') not in SHOT_TYPES:
            raise BuildError(f'cena {n}: shot {i} tipo inválido {sh.get("type")!r}')
        if 'at' not in sh:
            raise BuildError(f'cena {n}: shot {i} sem deixa "at"')
        raw = sh['at']
        sh['at'], gi = cue_time(raw, cursor, f'shot{i}.at')
        cursor = gi if not isinstance(raw, (int, float)) else cursor
        # palavras da frase no tempo da fala (statement/podium)
        for field, holder in (('text', sh), ('question', sh)):
            if sh['type'] in ('statement', 'podium') and field in holder and isinstance(holder[field], str):
                holder['wt'] = word_times(timing, k, holder[field], gi, scene_start)
        if sh['type'] == 'statement' and isinstance(sh.get('then'), dict):
            th = sh['then']
            tat = th.get('at')
            walk_then_cursor = gi
            if isinstance(tat, str):
                tgi, _ = find_cue(timing, k, tat, gi)
                walk_then_cursor = tgi
            th['wt'] = word_times(timing, k, th.get('text', ''), walk_then_cursor, scene_start)
        rest = {kk: vv for kk, vv in sh.items() if kk != 'at'}
        walk(rest, gi, f'shot{i}')
        sh.update(rest)
    ats = [sh['at'] for sh in shots]
    if any(b < a for a, b in zip(ats, ats[1:])):
        raise BuildError(f'cena {n}: shots fora de ordem temporal {ats}')
    return shots


def word_times(timing, k, text, gi, scene_start):
    """Para cada palavra da frase, o tempo em que ela é falada (se estiver na fala logo adiante)."""
    hi = timing.bounds[k + 1]
    out, j, last = [], gi, timing.t[gi] - scene_start
    for w in words_of(text):
        nw = norm(w)
        hit = None
        for x in range(j, min(hi, j + 14)):
            if timing.tokens[x][1] == nw and nw:
                hit = x
                break
        if hit is not None:
            last = timing.t[hit] - scene_start
            j = hit + 1
        else:
            last = last + 0.14
        out.append(round(max(0.0, last), 3))
    return out


def all_times(shots):
    ts = []

    def walk(o):
        if isinstance(o, dict):
            for kk, vv in o.items():
                if (kk == 'at' or kk.endswith('_at')) and isinstance(vv, (int, float)):
                    ts.append(float(vv))
                elif kk == 'wt' and isinstance(vv, list):
                    ts.extend(vv)
                else:
                    walk(vv)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(shots)
    return sorted(ts)


def fallback_shots(scene):
    """Cena sem roteiro visual: lista dos rótulos (garante que o bloco monta; o relatório acusa)."""
    labels = [l.split('\n')[0] for l in scene.get('labels', [])][:5] or [scene['title']]
    return [{'type': 'bullets', 'at': 1.2, 'items': [{'text': l, 'at': 2 + i * 3} for i, l in enumerate(labels)]}]


def captions(timing, starts, scene_ids, dur):
    groups, cur = [], []
    toks = timing.tokens
    for i, (w, nw, k) in enumerate(toks):
        cur.append(i)
        nxt = i + 1 if i + 1 < len(toks) else None
        end = w[-1] in '.?!'
        gap = nxt is not None and timing.t[nxt] - timing.t[i] > 0.9
        if nxt is None or len(cur) >= 7 or end or (w[-1] in ',:;' and len(cur) >= 3) or gap or toks[nxt][2] != k:
            groups.append(cur)
            cur = []
    out = []
    for g in groups:
        ws = []
        for i in g:
            s = timing.t[i]
            e = timing.t[i + 1] if i + 1 < len(toks) else min(dur, s + 0.6)
            ws.append({'w': toks[i][0], 's': round(s, 3), 'e': round(min(e, s + 1.2), 3)})
        out.append({'s': ws[0]['s'], 'e': ws[-1]['e'], 'w': ws})
    return out


INDEX = '''<!doctype html>
<html lang="{LANG}"><head><meta charset="utf-8">
<link rel="stylesheet" href="assets/v2.css">
<script src="assets/gsap.min.js"></script><script src="assets/CustomEase.min.js"></script><script src="assets/v2.js"></script>
<script>window.CAPS=__CAPS__;</script>
</head><body>
<div id="root" data-composition-id="main" data-width="1920" data-height="1080" data-duration="__DUR__">
 <div id="bg" class="full"><div class="bg-grad"></div><div id="bg-grid-wrap"><div id="bg-grid" style="transform:rotateX(62deg)"></div></div><svg id="stars" width="1920" height="1080" viewBox="0 0 1920 1080"></svg><div class="vignette"></div></div>
__HOSTS__
 <div class="pip" id="pip"><video id="nei-v" class="clip" src="assets/avatar.mp4" muted playsinline data-start="0" data-duration="__DUR__" data-track-index="2"></video></div>
 <div class="pip-tag"><b>NEI MALDANER</b> · INEMA</div>
 <audio id="vo" src="assets/avatar.mp4" data-start="0" data-duration="__DUR__" data-track-index="3"></audio>
 <div id="caps"></div>
</div>
<script>
(function(){
 const tl=gsap.timeline({paused:true}),D=__DUR__;
 let seed=__SEED__;const rnd=()=>(seed=(seed*16807)%2147483647)/2147483647;
 let s='';for(let i=0;i<140;i++){const r=rnd()*1.6+.3;s+=`<circle cx="${(rnd()*1920).toFixed(1)}" cy="${(rnd()*620).toFixed(1)}" r="${r.toFixed(2)}" fill="#bcd4ff" opacity="${(rnd()*.5+.1).toFixed(2)}"/>`;}
 document.getElementById('stars').innerHTML=s;
 tl.fromTo('#stars',{x:0},{x:-Math.min(400,D*.6),duration:D,ease:'none'},0);
 tl.fromTo('#bg-grid',{backgroundPosition:'0px 0px'},{backgroundPosition:'0px '+Math.round(D*16)+'px',duration:D,ease:'none'},0);
 const box=document.getElementById('caps');
 CAPS.forEach((g,i)=>{
  const d=document.createElement('div');d.className='cap';
  g.w.forEach(w=>{const sp=document.createElement('span');sp.textContent=w.w;d.appendChild(sp);});box.appendChild(d);
  const next=CAPS[i+1]?CAPS[i+1].s:g.e+.6,out=Math.min(next,g.e+.9);
  tl.fromTo(d,{opacity:0,y:14},{opacity:1,y:0,duration:.16,ease:'power2.out'},g.s);
  tl.to(d,{opacity:0,duration:.1},Math.max(g.s+.18,out-.1));
  [...d.children].forEach((sp,k)=>{const w=g.w[k];tl.to(sp,{color:'#ffb638',duration:.06},w.s);tl.to(sp,{color:'#eef3ff',duration:.18},Math.max(w.s+.07,w.e));});
 });
 window.__timelines["main"]=tl;
})();
</script>
</body></html>
'''

SCENE = '''<!doctype html>
<html lang="{LANG}"><body><template>
<div id="{id}-root" class="v2-scene" data-composition-id="{id}" data-width="1920" data-height="1080" data-duration="{dur}">
<div class="v2-stage" data-layout-allow-overflow></div>
<script>V2.scene("{id}", {spec});</script>
</div>
</template></body></html>
'''


def build(part, strict=False, spec_path=None, out=None):
    lang = CFG['languages'][0]
    key = f'{lang}-b{part:02d}'
    manifest = json.loads((ROOT / 'blocos/manifest.json').read_text())
    block = next(b for b in manifest if b['language'] == lang and b['part'] == part)
    lesson = json.loads((ROOT / f'docs/lesson-{lang}.json').read_text())
    scenes = [lesson[i - 1] for i in block['scenes']]
    words = json.loads((ROOT / f'verification/transcript-{key}.json').read_text())['words']
    dur = float(json.loads((ROOT / 'verification/blocos-downloads.json').read_text())[key]['duration'])
    align = json.loads((ROOT / f'align/{key}.json').read_text())   # starts oficiais (mesmos do v1)
    starts = list(align['starts'][:len(scenes)])
    timing = Timing(scenes, words)
    if timing.ratio <= 0.90:
        raise BuildError(f'{key}: alinhamento baixo {timing.ratio:.3f}')
    spec_file = Path(spec_path) if spec_path else ROOT / 'visual-v2' / f'{key}.json'
    spec = json.loads(spec_file.read_text()) if spec_file.exists() else {'scenes': {}}
    dest = Path(out) if out else ROOT / 'final' / key
    if dest.exists():
        for p in (dest / 'compositions').glob('*.html'):
            p.unlink()
    (dest / 'compositions').mkdir(parents=True, exist_ok=True)
    (dest / 'assets').mkdir(exist_ok=True)
    for f in RUNTIME.iterdir():
        shutil.copy2(f, dest / 'assets' / f.name)
    av = dest / 'assets/avatar.mp4'
    if av.is_symlink() or av.exists():
        av.unlink()
    av.symlink_to(ROOT / 'assets' / f'nei-{key}.mp4')
    warnings, report, hosts = [], {'key': key, 'ratio': round(timing.ratio, 4), 'scenes': []}, []
    total = len(lesson)
    for k, (n, sc) in enumerate(zip(block['scenes'], scenes)):
        s0 = starts[k]
        s1 = starts[k + 1] if k + 1 < len(starts) else dur
        sdur = round(s1 - s0, 3)
        entry = spec.get('scenes', {}).get(str(n))
        fb = entry is None or not entry.get('shots')
        if fb:
            warnings.append(f'cena {n}: sem roteiro visual (fallback)')
            shots = fallback_shots(sc)
        else:
            shots = resolve_scene(timing, k, s0, json.loads(json.dumps(entry)), warnings, n, strict)
            if sc.get('svg'):
                for sh in shots:
                    if sh['type'] == 'svg' and not sh.get('svg'):
                        sh['svg'] = sc['svg']
        ts = [0.0] + all_times(shots) + [sdur - 2]
        gaps = [(round(a, 1), round(b - a, 1)) for a, b in zip(ts, ts[1:]) if b - a > 10]
        for a, g in gaps:
            warnings.append(f'cena {n}: {g}s sem animação a partir de {a}s')
        sid = f'scene-{n:03d}'
        S = {'lang': lang, 'n': n, 'total': total, 'chapter': sc['chapter'], 'title': sc['title'], 'takeaway': sc.get('takeaway') if entry is None or entry.get('takeaway', True) is not False else None,
             'dur': sdur, 'shots': shots}
        if entry and isinstance(entry.get('takeaway'), str):
            S['takeaway'] = entry['takeaway']
        (dest / 'compositions' / f'{sid}.html').write_text(SCENE.format(id=sid, dur=sdur, LANG=lang, spec=json.dumps(S, ensure_ascii=False).replace('</', '<\\/')))
        hosts.append(f' <div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{s0}" data-duration="{sdur}" data-track-index="1"></div>')
        report['scenes'].append({'scene': n, 'start': s0, 'dur': sdur, 'shots': [sh['type'] for sh in shots], 'fallback': fb, 'max_gap': max([b - a for a, b in zip(ts, ts[1:])] or [0])})
    caps = captions(timing, starts, block['scenes'], dur)
    idx = INDEX.replace('__CAPS__', json.dumps(caps, ensure_ascii=False)).replace('__DUR__', str(dur)).replace('__HOSTS__', '\n'.join(hosts)).replace('__SEED__', str(7 + part)).replace('{LANG}', lang)
    (dest / 'index.html').write_text(idx)
    (dest / 'captions.srt').write_text('\n'.join(f'{i + 1}\n{stamp(g["s"])} --> {stamp(max(g["e"], g["s"] + .5))}\n{" ".join(w["w"] for w in g["w"])}\n' for i, g in enumerate(caps)))
    (dest / 'alignment.json').write_text(json.dumps(align, indent=2))
    (dest / 'hyperframes.json').write_text(json.dumps({'$schema': 'https://hyperframes.heygen.com/schema/hyperframes.json', 'paths': {'blocks': 'compositions', 'assets': 'assets'}, 'media': {'autoProxy': True}, 'authoringSkill': 'general-video'}, indent=2))
    hv = CFG.get('hyperframes', '0.8.77')
    (dest / 'package.json').write_text(json.dumps({'name': f'explica-v2-{key}', 'private': True, 'type': 'module', 'scripts': {'check': f'npx --yes hyperframes@{hv} check', 'render': f'npx --yes hyperframes@{hv} render'}}, indent=2))
    report['warnings'] = warnings
    (ROOT / 'verification').mkdir(exist_ok=True)
    (ROOT / 'verification' / f'build-v2-{key}.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    strict = '--strict' in sys.argv
    opt = dict(a.split('=', 1) for a in sys.argv[1:] if a.startswith('--') and '=' in a)
    try:
        r = build(int(args[0]), strict=strict, spec_path=opt.get('--spec'), out=opt.get('--out'))
    except BuildError as e:
        print('ERRO:', e)
        sys.exit(2)
    print(json.dumps({'key': r['key'], 'ratio': r['ratio'], 'scenes': len(r['scenes']), 'warnings': r['warnings']}, indent=1, ensure_ascii=False))
