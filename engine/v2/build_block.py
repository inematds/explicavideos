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

# Proporção do quadro (2.3): "16:9" (padrão, 1920×1080) ou "9:16" (1080×1920, Reels/Shorts).
# No 9:16 as cenas continuam desenhadas em 1920×1080 (todos os primitivos intactos); a área útil
# x 90–1420 é escalada para a largura de 1080 no topo, o avatar ocupa a faixa de baixo e a legenda
# fica entre os dois (zona segura das redes). Coluna direita (CENA n/N, PARA LEVAR) não aparece.
ASPECTS = {'16:9': (1920, 1080), '9:16': (1080, 1920)}

# Perfil de reel (2.4): contrato único do makeshorts (reel-profiles.json). Proporção NÃO define reel:
# só vale quando a config traz "reel_profile" (divulgacao | tutorial | mini-aula). A chave "profile"
# já é o perfil do navegador do HeyGen — por isso o nome é outro.
REEL_PROFILES = '~/projetos/makeshorts/.claude/skills/makeshorts/references/reel-profiles.json'


def reel_of(cfg):
    name = cfg.get('reel_profile')
    if not name:
        return None
    data = json.loads(Path(os.path.expanduser(cfg.get('reel_profiles', REEL_PROFILES))).read_text())
    if name not in data['profiles']:
        raise BuildError(f'reel_profile inválido {name!r}; use ' + ', '.join(data['profiles']))
    return dict(data['common'], name=name, version=data['version'], duration=data['profiles'][name]['duration'])


def aspect_of(cfg):
    a = str(cfg.get('aspect', '16:9')).strip()
    if a not in ASPECTS:
        raise BuildError(f'aspect inválido {a!r}; use ' + ' ou '.join(ASPECTS))
    return a


def frame(cfg):
    """(largura, altura, classe CSS do modo) do quadro final."""
    a = aspect_of(cfg)
    w, h = ASPECTS[a]
    return w, h, ('v916' if a == '9:16' else '')

SHOT_TYPES = {'bullets', 'hub', 'pipeline', 'orbs', 'podium', 'statement', 'radar', 'lanes', 'compare', 'chat', 'terminal',
              'filetree', 'counter', 'steps', 'quiz', 'timeline', 'flow', 'fields', 'keyword', 'module_intro', 'svg',
              'hook', 'media'}
# perfil viral (2.9, PADRAO-VIRAL.md): peças de tela cheia do runtime/viral.js
VIRAL_TYPES = {'capa', 'foto', 'capitulo', 'bignum', 'escala', 'barra', 'carimbo', 'cinetica', 'rosto', 'cta', 'mapa', 'ranking', 'colunas'}
SHOT_TYPES |= VIRAL_TYPES
OPENERS = ('hook', 'capa')   # nascem visíveis no frame 0 ("@start")
MEDIA_EXT = {'.png', '.jpg', '.jpeg', '.webp'}


def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode())


def stamp(t):
    ms = round(t * 1000)
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


class BuildError(Exception):
    pass


# O ASR escreve de outro jeito o que o roteiro escreve por extenso: a sigla "IA" vira "inteligência artificial",
# "pro" vira "para o", "inema ponto club" vira "inema.club". Antes de casar, o lado falado é reescrito na forma
# do roteiro (dividindo o tempo da palavra entre as partes) — assim essas palavras não ficam "interpoladas".
ALIASES = [(('inteligencia', 'artificial'), ('IA',)), (('para', 'o'), ('pro',)), (('para', 'a'), ('pra',)),
           (('inemaclub',), ('inema', 'ponto', 'club')), (('inema', 'club'), ('inema', 'ponto', 'club'))]


def expand_aliases(words):
    out, i = [], 0
    toks = [norm(w['word']) for w in words]
    while i < len(words):
        for src, dst in ALIASES:
            n = len(src)
            if tuple(toks[i:i + n]) == src:
                s0, e0 = words[i]['start'], words[i + n - 1]['end']
                step = (e0 - s0) / len(dst)
                out.extend({'word': d, 'start': round(s0 + j * step, 3), 'end': round(s0 + (j + 1) * step, 3)} for j, d in enumerate(dst))
                i += n
                break
        else:
            out.append(words[i]); i += 1
    return out


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
        words = expand_aliases(words)
        spoken = [norm(w['word']) for w in words]
        m = difflib.SequenceMatcher(None, [t[1] for t in self.tokens], spoken, autojunk=False)
        # Whisper escreve números em dígitos ("83%") e o roteiro por extenso: trecho trocado com dígito
        # no lado falado conta como acerto, com o tamanho do lado do roteiro (igual ao v1).
        nums = [(a2 - a1, b2 - b1) for op, a1, a2, b1, b2 in m.get_opcodes()
                if op == 'replace' and any(re.search(r'\d', words[i]['word']) for i in range(b1, b2))]
        hit = sum(b.size for b in m.get_matching_blocks()) + sum(a for a, _ in nums)
        self.ratio = 2 * hit / (len(self.tokens) + len(spoken) - sum(b for _, b in nums) + sum(a for a, _ in nums))
        mp = {}
        for b in m.get_matching_blocks():
            for i in range(b.size):
                mp[b.a + i] = b.b + i
        keys = sorted(mp)
        # palavras do roteiro que o ASR não casou: o tempo delas é interpolado — fica no relatório, não some
        self.unmatched = [(self.tokens[i][2], self.tokens[i][0]) for i in range(len(self.tokens)) if i not in mp]
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
        if sh['type'] in OPENERS and raw in ('@start', 'start'):
            # abertura do reel: t = 0 da cena. Só o hook aceita o marcador — "start" continua deixa normal nos outros
            sh['at'], gi = 0.0, cursor
        else:
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


EFFECT_KEYS = {'punch_at', 'strike_at'}   # pulso/risco: efeito, não informação nova (não conta no ritmo do reel)


def all_times(shots, words=True, effects=True):
    ts = []

    def walk(o):
        if isinstance(o, dict):
            for kk, vv in o.items():
                if (kk == 'at' or kk.endswith('_at')) and isinstance(vv, (int, float)):
                    if effects or kk not in EFFECT_KEYS:
                        ts.append(float(vv))
                elif kk == 'wt' and isinstance(vv, list):
                    if words:
                        ts.extend(vv)
                else:
                    walk(vv)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(shots)
    return sorted(ts)


def srt(caps, min_cue):
    """SRT sem sobreposição: o cue dura ao menos min_cue, mas nunca passa do início do próximo."""
    cues = []   # [início, fim, texto] — grupos com início coincidente viram um cue só (nunca fim ≤ início)
    for g in caps:
        s0, text = g['s'], ' '.join(w['w'] for w in g['w'])
        if cues and s0 < cues[-1][0] + 0.05:
            cues[-1][2] += ' ' + text
            cues[-1][1] = max(cues[-1][1], g['e'])
            continue
        if cues:
            cues[-1][1] = min(cues[-1][1], s0)
        cues.append([s0, max(g['e'], s0 + min_cue), text])
    return '\n'.join(f'{i + 1}\n{stamp(a)} --> {stamp(max(b, a + 0.05))}\n{t}\n' for i, (a, b, t) in enumerate(cues))


def copy_media(src, dest, n, i):
    """Mídia local (print/foto do produto) congelada dentro do bloco: assets/media/. Sem rede no render."""
    if not src:
        raise BuildError(f'cena {n}: shot {i} sem "src"')
    p = Path(os.path.expanduser(str(src)))
    if not p.is_absolute():
        p = ROOT / 'media' / p
    if not p.exists():
        raise BuildError(f'cena {n}: mídia não encontrada {p}')
    if p.suffix.lower() not in MEDIA_EXT:
        raise BuildError(f'cena {n}: mídia {p.name} — use imagem ({", ".join(sorted(MEDIA_EXT))}); vídeo ainda não é suportado')
    (dest / 'assets/media').mkdir(parents=True, exist_ok=True)
    import hashlib
    name = hashlib.sha256(p.read_bytes()).hexdigest()[:10] + '-' + p.name   # /a/print.png ≠ /b/print.png
    shutil.copy2(p, dest / 'assets/media' / name)
    return f'assets/media/{name}'


def image_size(p):
    import subprocess
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(p)],
                         capture_output=True, text=True).stdout.strip().split(',')
    try:
        return int(out[0]), int(out[1])
    except (ValueError, IndexError):
        raise BuildError(f'mídia ilegível: {p.name}')


def fallback_shots(scene):
    """Cena sem roteiro visual: lista dos rótulos (garante que o bloco monta; o relatório acusa)."""
    labels = [l.split('\n')[0] for l in scene.get('labels', [])][:5] or [scene['title']]
    return [{'type': 'bullets', 'at': 1.2, 'items': [{'text': l, 'at': 2 + i * 3} for i, l in enumerate(labels)]}]


def captions(timing, starts, scene_ids, dur, max_words=7, max_chars=None):
    groups, cur = [], []
    toks = timing.tokens
    for i, (w, nw, k) in enumerate(toks):
        cur.append(i)
        nxt = i + 1 if i + 1 < len(toks) else None
        end = w[-1] in '.?!'
        gap = nxt is not None and timing.t[nxt] - timing.t[i] > 0.9
        chars = sum(len(toks[j][0]) + 1 for j in cur) + (len(toks[nxt][0]) if nxt is not None else 0)
        full = len(cur) >= max_words or (max_chars and chars > max_chars)
        if nxt is None or full or end or (w[-1] in ',:;' and len(cur) >= min(3, max_words)) or gap or toks[nxt][2] != k:
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
<div id="root" class="__MODE__" data-composition-id="main" data-width="__W__" data-height="__H__" data-duration="__DUR__">
 <div id="bg" class="full"><div class="bg-grad"></div><div id="bg-grid-wrap" data-layout-allow-overflow><div id="bg-grid" style="transform:rotateX(62deg)"></div></div><svg id="stars" width="__W__" height="__H__" viewBox="0 0 __W__ __H__"></svg><div class="vignette"></div></div>
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
 let s='';for(let i=0;i<140;i++){const r=rnd()*1.6+.3;s+=`<circle cx="${(rnd()*__W__).toFixed(1)}" cy="${(rnd()*620).toFixed(1)}" r="${r.toFixed(2)}" fill="#bcd4ff" opacity="${(rnd()*.5+.1).toFixed(2)}"/>`;}
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
<div id="{id}-root" class="v2-scene {mode}" data-composition-id="{id}" data-width="{W}" data-height="{H}" data-duration="{dur}">
<div class="v2-fit" data-layout-allow-overflow><div class="v2-stage" data-layout-allow-overflow></div></div>
<script>V2.scene("{id}", {spec});</script>
</div>
</template></body></html>
'''


def viral_index(idx, rostos, fontes, marca, selo, capa=None, pip_t=None):
    """Perfil viral: runtime viral.css/js, faixa de marca no topo, fonte do dado e avatar em MEIA tela nos "rosto"
    (nunca tela cheia, Nei 15/10/2026). pip_t (9:16 com "avatar_916": "pip"): a partir dele o avatar vira PiP no canto
    e a cena ocupa o quadro inteiro."""
    head = '<script src="assets/v2.js"></script>'
    idx = idx.replace(head, head + '<link rel="stylesheet" href="assets/viral.css"><script src="assets/viral.js"></script>')
    fts = ''.join(f'<div class="fonte" id="ft{i}">{html.escape("Fonte: " + f[2])}</div>' for i, f in enumerate(fontes))
    topo = f'<div id="topo"><span>{html.escape(marca)}</span>' + (f'<span class="ao">{html.escape(selo)}</span>' if selo else '') + fts + '</div>'
    rich = lambda t: re.sub(r'\*\*(.+?)\*\*', r'<span class="hl">\1</span>', html.escape(t))
    rtx = ''.join(f'<div class="rtx" id="rt{i}">{rich(r[2])}</div>' for i, r in enumerate(rostos) if r[2])
    cc = f'<div id="capa-cheia" style="background-image:url(\'{capa[0]}\')"></div>' if capa else ''
    idx = idx.replace(' <div id="caps"></div>', cc + ' <div id="caps"></div>\n ' + topo + rtx)
    js = ('<script>(function(){const tl=window.__timelines["main"],R=%s,F=%s,v9=document.getElementById("root").classList.contains("v916");'
          'const W=+document.getElementById("root").dataset.width,H=+document.getElementById("root").dataset.height;'
          'const pc=getComputedStyle(document.getElementById("pip")),sm={left:parseFloat(pc.left),top:parseFloat(pc.top),width:parseFloat(pc.width),height:parseFloat(pc.height),borderRadius:parseFloat(pc.borderTopLeftRadius)};'
          'const big=v9?{left:0,top:H/2,width:W,height:H/2,borderRadius:0}:{left:W/2,top:0,width:W/2,height:H,borderRadius:0};'
          'const P=%s,pg={left:W-380,top:H-520,width:340,height:440,borderRadius:24};'
          'if(P!==null){tl.fromTo("#pip",Object.assign({},sm),Object.assign({duration:.6,ease:"expo.inOut",immediateRender:false},pg),P);'
          'tl.fromTo("#caps",{left:40,top:1020,width:1000},{left:40,top:H-330,width:W-440,duration:.4,immediateRender:false},P);'
          'tl.fromTo("#caps .cap",{width:1000,fontSize:84},{width:W-440,fontSize:64,duration:.4,immediateRender:false},P);}'
          'R.forEach(([a,b])=>{const s0=(P!==null&&a>=P)?pg:sm;tl.fromTo("#pip",Object.assign({},s0),Object.assign({duration:.35,ease:"expo.out",immediateRender:false},big),a);'
          'tl.fromTo("#pip",Object.assign({},big),Object.assign({duration:.3,ease:"expo.inOut",immediateRender:false},s0),Math.max(a+.4,b-.3));});'
          'R.forEach(([a,b,t,ta],i)=>{if(!t)return;tl.fromTo("#rt"+i,{opacity:0,scale:1.4},{opacity:1,scale:1,duration:.3,ease:"back.out(2)",immediateRender:false},ta);tl.to("#rt"+i,{opacity:0,duration:.2},Math.max(ta+.3,b-.25));});'
          + ('tl.fromTo("#capa-cheia",{opacity:1,scale:1},{scale:1.06,duration:%.3f,ease:"none",immediateRender:true},0);tl.to("#capa-cheia",{opacity:0,duration:.25},%.3f);' % (max(.3, capa[1] - .25), max(0, capa[1] - .25)) if capa else '') +
          'F.forEach(([a,b],i)=>{tl.fromTo("#ft"+i,{opacity:0,y:-8},{opacity:1,y:0,duration:.25},a);tl.to("#ft"+i,{opacity:0,duration:.2},Math.max(a+.3,b-.2));});'
          '})();</script>') % (json.dumps(rostos), json.dumps([[a, b] for a, b, _ in fontes]), json.dumps(pip_t))
    return idx.replace('</body></html>', js + '\n</body></html>')


def build(part, strict=False, spec_path=None, out=None):
    lang = CFG['languages'][0]
    W, H, mode = frame(CFG)
    reel = reel_of(CFG)
    if reel:
        if aspect_of(CFG) != '9:16':
            raise BuildError(f'reel_profile {reel["name"]!r} exige "aspect": "9:16" na config (está {aspect_of(CFG)})')
        mode = (mode + ' reel').strip()
    viral = CFG.get('profile_visual') == 'viral'
    if viral:
        mode = (mode + ' viral').strip()
    VW, VH = (1080, 1150) if (viral and aspect_of(CFG) == '9:16') else (1920, 1080)
    rostos, fontes, capa_cheia, mapas = [], [], None, []
    # 9:16 "avatar_916": "pip" (Nei 15/10/2026): até a cena "pip_cena" o avatar fica em meio tamanho (palco 1080×1150);
    # dela em diante vira PiP no canto e o palco ocupa o quadro inteiro (1080×1920).
    pip916 = viral and aspect_of(CFG) == '9:16' and CFG.get('avatar_916') == 'pip'
    pip_cena, pip_t = int(CFG.get('pip_cena', 2)), None
    key = f'{lang}-b{part:02d}'
    # Relatório velho não pode sobreviver a um build que falhou no meio: o produtor o leria como aprovado.
    (ROOT / 'verification' / f'build-v2-{key}.json').unlink(missing_ok=True)
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
    # As composições antigas só são trocadas depois de TODAS as cenas validarem (build que falha no meio
    # não deixa o bloco pela metade): as novas ficam em `pending` até o fim.
    pending = []
    (dest / 'compositions').mkdir(parents=True, exist_ok=True)
    (dest / 'assets').mkdir(exist_ok=True)
    for f in RUNTIME.iterdir():
        shutil.copy2(f, dest / 'assets' / f.name)
    av = dest / 'assets/avatar.mp4'
    src_av = (ROOT / 'assets' / f'nei-{key}.mp4').resolve()
    if reel:
        # pacote autossuficiente: cópia real do avatar (symlink quebra se a pasta v1 sumir)
        if av.is_symlink() or not av.exists() or av.stat().st_size != src_av.stat().st_size:
            if av.is_symlink() or av.exists():
                av.unlink()
            shutil.copy2(src_av, av)
    else:
        if av.is_symlink() or av.exists():
            av.unlink()
        av.symlink_to(src_av)
    CRIT = {'ia', 'nei', 'nao', 'sem', 'so', 'zero', 'gratis', 'club', 'inema'}
    warnings, report, hosts = [], {'key': key, 'ratio': round(timing.ratio, 4), 'scenes': [],
                                   'interpolated': [{'scene': k + 1, 'word': w} for k, w in timing.unmatched]}, []
    if reel:
        crit = [w for k, w in timing.unmatched if norm(w) in CRIT]
        if crit:
            warnings.append(f'palavras críticas não ouvidas na transcrição (tempo interpolado): {", ".join(crit[:8])}')
        if len(timing.unmatched) > 0.10 * max(1, len(timing.tokens)):
            warnings.append(f'{len(timing.unmatched)} de {len(timing.tokens)} palavras com tempo interpolado (> 10%)')
    total = len(lesson)
    for k, (n, sc) in enumerate(zip(block['scenes'], scenes)):
        s0 = starts[k]
        s1 = starts[k + 1] if k + 1 < len(starts) else dur
        sdur = round(s1 - s0, 3)
        sVH, smode = VH, mode
        if pip916 and n >= pip_cena:
            sVH, smode = 1920, mode + ' pipfull'
            pip_t = round(s0, 3) if pip_t is None else pip_t
        entry = spec.get('scenes', {}).get(str(n))
        fb = entry is None or not entry.get('shots')
        if fb:
            if strict and reel:
                raise BuildError(f'cena {n}: sem roteiro visual (--strict não aceita fallback no reel)')
            warnings.append(f'cena {n}: sem roteiro visual (fallback)')
            shots = fallback_shots(sc)
        else:
            shots = resolve_scene(timing, k, s0, json.loads(json.dumps(entry)), warnings, n, strict)
            if sc.get('svg'):
                for sh in shots:
                    if sh['type'] == 'svg' and not sh.get('svg'):
                        sh['svg'] = sc['svg']
        for i, sh in enumerate(shots):
            if sh['type'] == 'media':
                sh['src'] = copy_media(sh.get('src'), dest, n, i)
                sh['iw'], sh['ih'] = image_size(dest / sh['src'])
            if sh['type'] == 'hook' and sh.get('src'):
                sh['src'] = copy_media(sh['src'], dest, n, i)
            if sh['type'] in VIRAL_TYPES and sh.get('src'):
                if viral and aspect_of(CFG) == '9:16' and sh.get('src_916'):
                    sh['src'] = sh['src_916']
                sh.pop('src_916', None)
                sh['src'] = copy_media(sh['src'], dest, n, i)
            if sh['type'] == 'mapa':
                import mapa_geo   # contornos locais → SVG (perfil viral)
                sh['geo'] = mapa_geo.geo(sh, VW, sVH)
        if viral:
            # trechos absolutos: avatar em tela cheia ("rosto") e fonte do dado na faixa do topo
            for i, sh in enumerate(shots):
                j = i + 1
                while j < len(shots) and shots[j].get('keep'):
                    j += 1
                a, b = s0 + sh['at'], s0 + (shots[j]['at'] if j < len(shots) else sdur)
                if sh['type'] == 'capa' and k == 0 and aspect_of(CFG) == '9:16':
                    capa_cheia = [sh['src'], round(b, 3)]   # 9:16: a capa cobre o quadro inteiro (sobre o avatar) até o 1º corte
                if sh['type'] == 'mapa':
                    mapas.append([round(a, 3), round(b, 3)])
                if sh['type'] == 'rosto':
                    rostos.append([round(a, 3), round(b, 3), sh.get('txt', ''), round(s0 + sh.get('txt_at', sh['at'] + 0.3), 3)])
                if sh.get('fonte'):
                    fontes.append([round(a, 3), round(b, 3), sh['fonte']])
        if reel and k > 0 and shots and shots[0]['at'] > 0.5:
            warnings.append(f'cena {n}: topo vazio por {shots[0]["at"]}s até o 1º shot (use uma deixa do começo da fala)')
        if reel and k == 0 and not (shots and shots[0]['type'] in OPENERS and shots[0]['at'] <= 0.05):
            msg = f'cena {n}: reel precisa abrir com shot "hook" em "start" (frame 0 completo)'
            if strict:
                raise BuildError(msg)
            warnings.append(msg)
        if (not reel and part == 1 and k == 0 and not CFG.get('cold_open') and not CFG.get('allow_cold_start')
                and not (shots and shots[0]['type'] in OPENERS and shots[0]['at'] <= 0.05)):
            # 2.6.6: no 16:9 o frame 0 também não pode nascer vazio — shot com "at" 0 ainda entra animado e o 1º frame
            # sai só com o fundo (trilogia gestão de agentes, 08/10/2026). Só o "hook" nasce visível em t = 0.
            msg = (f'cena {n}: o vídeo abre sem gancho — 1º shot "hook" em "@start", ou "cold_open" na config (abertura com '
                   'thumb + frase de impacto montada depois); "allow_cold_start": true só se for de propósito')
            if strict:
                raise BuildError(msg)
            warnings.append(msg)
        if viral:
            limit = 2.0   # PADRAO-VIRAL: nunca > 2 s sem troca de conteúdo
            ts = [0.0] + all_times(shots, words=False, effects=False) + [sdur]
        elif reel:
            # no reel conta só troca de conteúdo (at/*_at), não palavra aparecendo (wt); e a cauda inteira
            limit = reel['rhythm']['static_review_s']
            ts = [0.0] + all_times(shots, words=False, effects=False) + [sdur]
        else:
            limit = 10
            ts = [0.0] + all_times(shots) + [sdur - 2]
        gaps = [(round(a, 1), round(b - a, 1)) for a, b in zip(ts, ts[1:]) if b - a > limit]
        if viral and k == 0 and CFG.get('capa_segura') and len(shots) > 1 and shots[0]['type'] == 'capa':
            # "capa_segura" (Nei 15/10/2026: "o texto inicial tem que ficar mais segundos aberto"): a capa parada
            # de propósito não conta como trecho sem troca
            gaps = [(a, g) for a, g in gaps if a >= shots[1]['at'] - 0.05]
        for a, g in gaps:
            warnings.append(f'cena {n}: {g}s sem mudança visual a partir de {a}s (limite {limit}s)')
        sid = f'scene-{n:03d}'
        S = {'lang': lang, 'n': n, 'total': total, 'chapter': sc['chapter'], 'title': sc['title'], 'takeaway': sc.get('takeaway') if entry is None or entry.get('takeaway', True) is not False else None,
             'dur': sdur, 'shots': shots, 'reel': bool(reel), 'header': bool(entry and entry.get('header'))}
        if viral:
            S.update(viral=True, vw=VW, vh=sVH)
        if viral and entry and entry.get('fundo'):
            S['fundo'] = copy_media(entry['fundo'], dest, n, 'fundo')
        if entry and isinstance(entry.get('takeaway'), str):
            S['takeaway'] = entry['takeaway']
        pending.append((dest / 'compositions' / f'{sid}.html', SCENE.format(id=sid, dur=sdur, LANG=lang, W=W, H=H, mode=smode, spec=json.dumps(S, ensure_ascii=False).replace('</', '<\\/'))))
        hosts.append(f' <div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{s0}" data-duration="{sdur}" data-track-index="1"></div>')
        report['scenes'].append({'scene': n, 'start': s0, 'dur': sdur, 'shots': [sh['type'] for sh in shots], 'fallback': fb, 'max_gap': max([b - a for a, b in zip(ts, ts[1:])] or [0])})
    for old in (dest / 'compositions').glob('*.html'):
        old.unlink()
    for path, content in pending:
        path.write_text(content)
    caps = captions(timing, starts, block['scenes'], dur,
                    max_words=3 if viral else (reel['captions']['max_words'] if reel else 7),
                    max_chars=(18 if aspect_of(CFG) == '9:16' else 24) if viral else (reel['captions']['max_chars'] if reel else None))
    idx = INDEX.replace('__CAPS__', json.dumps(caps, ensure_ascii=False)).replace('__DUR__', str(dur)).replace('__HOSTS__', '\n'.join(hosts)).replace('__SEED__', str(7 + part)).replace('{LANG}', lang)
    idx = idx.replace('__W__', str(W)).replace('__H__', str(H)).replace('__MODE__', mode)
    if viral:
        idx = viral_index(idx, rostos, fontes, CFG.get('marca', 'INEMA'), CFG.get('selo_topo', ''), capa_cheia, pip_t)
    report['aspect'] = aspect_of(CFG)
    report['rostos'] = [r[:2] for r in rostos]
    report['mapas'] = mapas   # o qa_viral não mede 'área lisa' em mapa (oceano/terra sólidos são informação)
    report['reel_profile'] = reel and {'name': reel['name'], 'contract_version': reel['version']}
    (dest / 'index.html').write_text(idx)
    (dest / 'captions.srt').write_text(srt(caps, reel['captions']['min_cue_s'] if reel else 0.5))
    (dest / 'alignment.json').write_text(json.dumps(align, indent=2))
    (dest / 'hyperframes.json').write_text(json.dumps({'$schema': 'https://hyperframes.heygen.com/schema/hyperframes.json', 'paths': {'blocks': 'compositions', 'assets': 'assets'}, 'media': {'autoProxy': True}, 'authoringSkill': 'general-video'}, indent=2))
    hv = CFG.get('hyperframes', '0.8.77')
    (dest / 'package.json').write_text(json.dumps({'name': f'explica-v2-{key}', 'private': True, 'type': 'module', 'scripts': {'check': f'npx --yes hyperframes@{hv} check', 'render': f'npx --yes hyperframes@{hv} render'}}, indent=2))
    report['warnings'] = warnings
    # O produtor exige isto no reel (render_guard.build_problem): strict rodado e nenhum aviso.
    report['validation'] = {'strict': bool(strict), 'ok': bool(strict) and not warnings}
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
    # --strict no reel reprova de verdade: qualquer aviso bloqueia. Fora do reel mantém o comportamento
    # antigo (avisos não mudam o código de saída) para não quebrar as filas em produção.
    if strict and r['warnings'] and (r.get('reel_profile') or CFG.get('profile_visual') == 'viral'):
        print('REPROVADO (--strict): corrija os avisos acima')
        sys.exit(3)
