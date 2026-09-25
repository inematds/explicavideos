/* Explicavideos v2 — biblioteca de cenas explicativas animadas (GSAP, seek-safe).
   Cada cena = cabeçalho + cartão lateral + sequência de "shots". Cada shot é um primitivo de V2.P
   que recebe tempos já resolvidos (segundos relativos à cena) a partir das palavras faladas. */
(function () {
  const V2 = (window.V2 = { P: {} });
  const NS = 'http://www.w3.org/2000/svg';
  const COLORS = ['#3ee6ff', '#ffb638', '#9a86ff', '#3ef0a0', '#ff5d7a', '#e58bff', '#7dd3fc', '#fde047'];

  // ---------- utilitários
  const h = (parent, tag, cls, css, html) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (css) e.style.cssText = css;
    if (html != null) e.innerHTML = html;
    if (parent) parent.appendChild(e);
    return e;
  };
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[m]);
  const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<span class="hl">$1</span>').replace(/\+\+(.+?)\+\+/g, '<span class="good">$1</span>').replace(/~~(.+?)~~/g, '<span class="bad">$1</span>');
  const plain = (s) => String(s == null ? '' : s).replace(/\*\*|\+\+|~~/g, '');
  const fs = (text, max, min, lo, hi) => { const n = plain(text).length; if (n <= lo) return max; if (n >= hi) return min; return Math.round(max - (max - min) * (n - lo) / (hi - lo)); };
  const rng = (seed) => { let s = (seed % 2147483646) + 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; };
  const lines = (text, px, width) => Math.max(1, Math.ceil(plain(text).length * px * 0.56 / width));
  const def = (v, d) => (v == null || Number.isNaN(v) ? d : v);
  V2.util = { h, esc, rich, fs, rng };

  const ICON = {
    doc: 'M6 2h9l5 5v15H6z M14 2v6h6 M9 13h7 M9 17h7', folder: 'M3 6h6l2 3h10v11H3z', chat: 'M4 4h16v11H9l-5 4z',
    terminal: 'M3 4h18v16H3z M7 9l3 3-3 3 M12 15h5', key: 'M14.5 9.5a4.5 4.5 0 1 1-2.2 3.9L4 21.7V18h3v-3h3l2.3-2.3 M16.5 7.5h.01',
    lock: 'M5 11h14v10H5z M8 11V7a4 4 0 0 1 8 0v4', cloud: 'M7 18h10a4 4 0 0 0 0-8 6 6 0 0 0-11.5 1.5A3.5 3.5 0 0 0 7 18z',
    server: 'M4 4h16v6H4z M4 14h16v6H4z M8 7h.01 M8 17h.01', ai: 'M12 2l2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z',
    user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M4 21a8 8 0 0 1 16 0', team: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M17 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 20a6 6 0 0 1 12 0 M13 20a6 6 0 0 1 8-5.6',
    check: 'M4 12l5 5L20 6', x: 'M6 6l12 12 M18 6L6 18', clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 7v5l3 3',
    money: 'M12 2v20 M17 6H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6', star: 'M12 2l3 7h7l-5.5 4.5 2 7.5-6.5-4.5L5.5 21l2-7.5L2 9h7z',
    search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M21 21l-5-5', gear: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M12 2v3 M12 19v3 M2 12h3 M19 12h3 M4.9 4.9L7 7 M17 17l2.1 2.1 M4.9 19.1L7 17 M17 7l2.1-2.1',
    git: 'M6 3v12 M6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M18 9a9 9 0 0 1-9 9', send: 'M22 2L11 13 M22 2l-7 20-4-9-9-4z',
    book: 'M4 4h6a3 3 0 0 1 3 3v14a2 2 0 0 0-2-2H4z M20 4h-5a3 3 0 0 0-3 3 M20 4v15h-7', bulb: 'M9 18h6 M10 22h4 M12 2a7 7 0 0 0-4 12.7V16h8v-1.3A7 7 0 0 0 12 2z',
    warn: 'M12 3l10 18H2z M12 10v5 M12 18h.01', target: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z M12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z',
    list: 'M8 6h13 M8 12h13 M8 18h13 M3 6h.01 M3 12h.01 M3 18h.01', image: 'M3 4h18v16H3z M8.5 10a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z M21 15l-5-5L5 20',
    video: 'M3 6h13v12H3z M16 10l5-3v10l-5-3', code: 'M16 18l6-6-6-6 M8 6l-6 6 6 6',
    link: 'M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1 M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1', shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
    eye: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z', pencil: 'M17 3l4 4L7 21H3v-4z',
    calendar: 'M3 5h18v16H3z M16 3v4 M8 3v4 M3 10h18', chart: 'M4 20V10 M10 20V4 M16 20v-8 M22 20H2',
    cpu: 'M6 6h12v12H6z M9 9h6v6H9z M9 2v4 M15 2v4 M9 18v4 M15 18v4 M2 9h4 M2 15h4 M18 9h4 M18 15h4', play: 'M6 4l14 8-14 8z',
    pause: 'M7 4h3v16H7z M14 4h3v16h-3z', refresh: 'M21 12a9 9 0 1 1-3-6.7L21 8 M21 3v5h-5', phone: 'M7 2h10v20H7z M11 18h2',
    globe: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M2 12h20 M12 2a15 15 0 0 1 0 20 M12 2a15 15 0 0 0 0 20',
    upload: 'M12 16V4 M7 9l5-5 5 5 M4 20h16', download: 'M12 4v12 M7 11l5 5 5-5 M4 20h16', dot: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
    bot: 'M5 8h14v11H5z M12 4v4 M9 13h.01 M15 13h.01 M9 17h6', memory: 'M4 6h16v12H4z M8 6v12 M12 6v12 M16 6v12',
    flag: 'M5 21V4 M5 4h12l-2 4 2 4H5', box: 'M3 7l9-4 9 4v10l-9 4-9-4z M3 7l9 4 9-4 M12 11v10',
  };
  const icon = (name, size, color, sw) => `<svg class="v2-ico" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color || 'currentColor'}" stroke-width="${sw || 2}" stroke-linecap="round" stroke-linejoin="round"><path d="${ICON[name] || ICON.dot}"/></svg>`;
  V2.ICON = ICON;
  V2.icon = icon;

  // ---------- cena
  V2.scene = function (id, S) {
    const root = document.querySelector(`[data-composition-id="${id}"]`);
    const stage = root.querySelector('.v2-stage');
    const tl = gsap.timeline({ paused: true });
    const renders = [];
    const E = CustomEase.create('v2snap' + S.n, 'M0,0 C0.12,0.9 0.3,1.06 0.5,1.02 0.7,1 0.85,1 1,1');
    const ctx = { tl, root, stage, S, E, rnd: rng(S.n * 97 + 13), render: (f) => renders.push(f), dur: S.dur };
    ctx.pop = (el, t, from) => tl.fromTo(el, Object.assign({ opacity: 0, scale: 0.6, y: 20 }, from || {}), { opacity: 1, scale: 1, y: 0, x: 0, duration: 0.45, ease: E }, t);
    ctx.rise = (el, t, d) => tl.fromTo(el, { opacity: 0, y: d == null ? 40 : d }, { opacity: 1, y: 0, duration: 0.45, ease: 'power3.out' }, t);
    ctx.fade = (el, t, d) => tl.fromTo(el, { opacity: 0 }, { opacity: 1, duration: d || 0.35 }, t);

    tl.fromTo(stage, { opacity: 0 }, { opacity: 1, duration: 0.3 }, 0);
    header(ctx);
    side(ctx);
    const shots = S.shots || [];
    shots.forEach((shot, i) => {
      let j = i + 1;
      while (j < shots.length && shots[j].keep) j++;
      const t0 = Math.max(0, shot.at), t1 = j < shots.length ? shots[j].at : S.dur;
      const box = h(stage, 'div', 'v2-shot');
      box.setAttribute('data-layout-allow-overflow', '');
      tl.fromTo(box, { opacity: 0 }, { opacity: 1, duration: 0.25 }, Math.max(0, t0 - 0.1));
      if (t1 < S.dur - 0.05) tl.to(box, { opacity: 0, scale: 1.035, filter: 'blur(8px)', duration: 0.32, ease: 'power2.in' }, Math.max(t0 + 0.4, t1 - 0.34));
      const fn = V2.P[shot.type];
      if (!fn) throw new Error('shot desconhecido: ' + shot.type);
      fn(box, shot, Object.assign({}, ctx, { T0: t0, T1: t1, box }));
    });
    if (S.dur > 1) tl.to(stage, { opacity: 0, scale: 1.08, filter: 'blur(10px)', duration: 0.3, ease: 'power2.in' }, S.dur - 0.3);
    tl.eventCallback('onUpdate', () => renders.forEach((f) => f()));
    renders.forEach((f) => f());
    window.__timelines[id] = tl;
    return tl;
  };

  function header(c) {
    const { S, tl, stage } = c;
    const tf = Math.min(44, Math.floor(1330 / (S.title.length * 0.62)));
    const hd = h(stage, 'div', 'v2-hdr', '', `<div class="kick">${esc(S.chapter)}</div><div class="ttl" style="font-size:${tf}px">${esc(S.title)}</div>`);
    const first = (S.shots && S.shots.length) ? S.shots[0].at : S.dur;
    if (first < 1.4) { tl.fromTo(hd, { opacity: 0, y: -10 }, { opacity: 1, y: 0, duration: 0.4 }, 0.05); return; }
    const sc = Math.min(1.9 * 44 / tf, 1260 / (S.title.length * 0.62 * tf));
    tl.fromTo(hd, { x: 60, y: 330, scale: sc, opacity: 0 }, { opacity: 1, duration: 0.45, ease: 'power2.out' }, 0.08);
    tl.to(hd, { x: 0, y: 0, scale: 1, duration: 0.8, ease: 'power3.inOut' }, Math.max(0.7, Math.min(2.4, first - 0.9)));
  }

  function side(c) {
    const { S, tl, stage } = c;
    const sd = h(stage, 'div', 'v2-side', '', `<div class="no">CENA ${String(S.n).padStart(3, '0')} / ${S.total}</div><div class="bar"><i style="width:${(100 * S.n / S.total).toFixed(1)}%"></i></div>`);
    c.fade(sd, 0.4);
    if (S.takeaway) {
      const tk = h(stage, 'div', 'v2-take', '', `<div class="k">PARA LEVAR</div><div class="t">${rich(S.takeaway)}</div>`);
      const t = Math.max(Math.min(S.dur * 0.5, 14), S.dur - 12);
      tl.fromTo(tk, { opacity: 0, x: 40 }, { opacity: 1, x: 0, duration: 0.5, ease: 'power3.out' }, t);
    }
  }

  // ---------- helpers de desenho
  const svgEl = (parent, tag, attrs) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; };
  const fullSvg = (box, z) => { const s = document.createElementNS(NS, 'svg'); s.setAttribute('width', '1920'); s.setAttribute('height', '1080'); s.setAttribute('viewBox', '0 0 1920 1080'); s.style.cssText = `position:absolute;left:0;top:0;${z != null ? 'z-index:' + z : ''}`; box.appendChild(s); return s; };
  const drawLine = (c, el, t, d) => { const L = el.getTotalLength ? el.getTotalLength() : 400; el.style.strokeDasharray = L; c.tl.fromTo(el, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: d || 0.5, ease: 'power2.out' }, t); };
  const times = (arr, c, gap) => arr.map((x, i) => def(x.at, c.T0 + 0.35 + i * (gap || 0.5)));

  // =====================================================================================
  // bullets — lista de ideias: cartões em linha (≤4 curtos) ou caminho vertical
  V2.P.bullets = function (box, s, c) {
    const items = s.items || [], n = items.length, T = times(items, c);
    const row = s.layout ? s.layout === 'row' : (n <= 4 && items.every((it) => plain(it.text).length <= 60));
    const top = s.title ? 260 : 220;
    if (s.title) { const t = h(box, 'div', 'v2-lbl', `left:90px;top:190px;width:1330px;color:var(--cyan);font-size:22px`, esc(s.title)); c.fade(t, c.T0 + 0.1); }
    if (row) {
      const w = (1330 - (n - 1) * 34) / n, H = Math.min(420, 150 + Math.max(...items.map((it) => lines(it.text, 38, w - 46) * 48 + (it.sub ? 70 : 0)))), rowTop = Math.max(top, 520 - H / 2);
      items.forEach((it, i) => {
        const x = 90 + i * (w + 34), col = COLORS[i % COLORS.length];
        const card = h(box, 'div', 'b-card', `left:${x}px;top:${rowTop}px;width:${w}px;height:${H}px`,
          `<div class="big">${String(i + 1).padStart(2, '0')}</div>${icon(it.icon || 'dot', 40, col)}<div class="tx" style="font-size:${fs(it.text, 40, 28, 16, 60)}px">${rich(it.text)}</div>${it.sub ? `<div class="sb">${esc(it.sub)}</div>` : ''}`);
        card.querySelector('svg').style.cssText = 'position:absolute;right:22px;top:20px';
        c.pop(card, T[i], { y: 70 });
        c.tl.to(card, { borderColor: 'rgba(255,182,56,.85)', boxShadow: '0 0 40px rgba(255,182,56,.22)', duration: 0.25 }, T[i] + 0.1);
        if (i > 0) {
          const prev = box.querySelectorAll('.b-card')[i - 1];
          c.tl.to(prev, { borderColor: 'rgba(62,230,255,.45)', boxShadow: '0 0 0 rgba(0,0,0,0)', duration: 0.3 }, T[i]);
          const ar = h(box, 'div', '', `position:absolute;left:${x - 30}px;top:${rowTop + H / 2 - 13}px;width:26px;height:26px;color:var(--amber)`, icon('play', 26, 'var(--amber)'));
          c.pop(ar, T[i] - 0.1);
        }
      });
    } else {
      const gap = Math.min(150, 640 / Math.max(1, n)), svg = fullSvg(box);
      items.forEach((it, i) => {
        const y = top + 10 + i * gap, f = fs(it.text, 38, 25, 30, 130), col = COLORS[i % COLORS.length];
        if (i > 0) { const ln = svgEl(svg, 'line', { x1: 142, y1: y - gap + 64, x2: 142, y2: y, stroke: 'rgba(255,182,56,.6)', 'stroke-width': 4 }); drawLine(c, ln, T[i] - 0.15, 0.3); }
        const nd = h(box, 'div', 'b-node', `left:110px;top:${y}px;border-color:${col}`, it.icon ? icon(it.icon, 32, col) : `<div class="num">${i + 1}</div>`);
        const tx = h(box, 'div', 'b-text', `left:206px;top:${y + (it.sub ? -4 : 32 - f * 0.62)}px;width:1200px;font-size:${f}px`, rich(it.text));
        c.pop(nd, T[i]);
        c.tl.fromTo(tx, { opacity: 0, x: 40 }, { opacity: 1, x: 0, duration: 0.45, ease: 'power3.out' }, T[i] + 0.05);
        if (it.sub) { const sb = h(box, 'div', 'b-sub', `left:206px;top:${y + f * 1.25}px;width:1200px`, esc(it.sub)); c.fade(sb, T[i] + 0.3); }
        c.tl.to(nd, { boxShadow: `0 0 34px ${col}`, scale: 1.12, duration: 0.25, yoyo: true, repeat: 1 }, T[i] + 0.1);
      });
    }
  };

  // hub — um núcleo e as peças ao redor, ligadas por linhas que se desenham
  V2.P.hub = function (box, s, c) {
    const cx = 745, cy = 530, nodes = s.nodes || [], n = nodes.length, T = times(nodes, c, 0.6);
    const svg = fullSvg(box);
    const ct = def(s.center && s.center.at, c.T0 + 0.1);
    const core = h(box, 'div', 'h-core', `left:${cx - 115}px;top:${cy - 115}px`, `${icon((s.center && s.center.icon) || 'ai', 64, '#ffb638')}<div class="lb" style="font-size:${fs(s.center && s.center.label, 28, 19, 10, 26)}px">${esc(s.center && s.center.label)}</div>`);
    c.pop(core, ct, { scale: 0.2 });
    c.tl.fromTo(core, { boxShadow: '0 0 20px rgba(255,182,56,.2)' }, { boxShadow: '0 0 110px rgba(255,182,56,.55)', duration: 1.2, yoyo: true, repeat: 3, ease: 'sine.inOut' }, ct + 0.5);
    nodes.forEach((nd, i) => {
      const a = -Math.PI / 2 + i * 2 * Math.PI / n, x = cx + 520 * Math.cos(a), y = cy + 285 * Math.sin(a), col = COLORS[i % COLORS.length];
      const ln = svgEl(svg, 'line', { x1: cx, y1: cy, x2: x, y2: y, stroke: col, 'stroke-width': 3, opacity: 0.75 });
      drawLine(c, ln, T[i], 0.45);
      const dot = svgEl(svg, 'circle', { r: 7, cx, cy, fill: '#fff', opacity: 0 });
      c.tl.set(dot, { opacity: 1 }, T[i] + 0.3);
      c.tl.fromTo(dot, { attr: { cx, cy } }, { attr: { cx: x, cy: y }, duration: 0.55, ease: 'power1.in' }, T[i] + 0.3);
      c.tl.to(dot, { opacity: 0, duration: 0.1 }, T[i] + 0.85);
      const el = h(box, 'div', 'h-node', `left:${x - 125}px;top:${y - 42}px;border-color:${col}`, `${icon(nd.icon || 'dot', 34, col)}<div class="lb" style="font-size:${fs(nd.label, 23, 17, 14, 34)}px">${esc(nd.label)}</div>${nd.sub ? `<div class="sb">${esc(nd.sub)}</div>` : ''}`);
      c.pop(el, T[i] + 0.35);
    });
    (s.focus || []).forEach((f) => {
      const el = box.querySelectorAll('.h-node')[f.node];
      if (!el || f.at == null) return;
      c.tl.to(el, { scale: 1.12, borderColor: '#ffb638', boxShadow: '0 0 40px rgba(255,182,56,.5)', duration: 0.3 }, f.at);
      c.tl.to(el, { scale: 1, boxShadow: '0 0 0 rgba(0,0,0,0)', duration: 0.4 }, f.at + 1.6);
    });
  };

  // pipeline — entrada → modelo (esfera de pontos 3D) → saída
  V2.P.pipeline = function (box, s, c) {
    const I = s.input || {}, C = s.core || {}, O = s.output || {};
    const ti = def(I.at, c.T0 + 0.2), tc = def(C.at, c.T0 + 0.1), to = def(O.at, ti + 1.2);
    const R = c.rnd, N = 170, pts = [];
    for (let i = 0; i < N; i++) { const y = 1 - 2 * (i + 0.5) / N, r = Math.sqrt(1 - y * y), th = i * 2.39996; pts.push({ x: Math.cos(th) * r, y, z: Math.sin(th) * r, sx: (R() - 0.5) * 1200, sy: (R() - 0.5) * 800, c: R() }); }
    const sv = h(box, 'div', '', 'position:absolute;left:560px;top:325px;width:480px;height:480px');
    sv.innerHTML = `<svg width="480" height="480" viewBox="-240 -240 480 480"><g>${pts.map(() => '<circle r="2"/>').join('')}</g></svg>`;
    const dots = [...sv.querySelectorAll('circle')], st = { k: 0, rot: 0 };
    c.render(() => {
      const ca = Math.cos(st.rot), sa = Math.sin(st.rot), ct = Math.cos(0.38), s2 = Math.sin(0.38), Rr = 132;
      pts.forEach((p, i) => {
        let x = p.x * ca + p.z * sa, z = -p.x * sa + p.z * ca; const y = p.y * ct - z * s2; z = p.y * s2 + z * ct;
        const d = (z + 1) / 2, e = dots[i];
        e.setAttribute('cx', (p.sx + (x * Rr - p.sx) * st.k).toFixed(1)); e.setAttribute('cy', (p.sy + (y * Rr - p.sy) * st.k).toFixed(1));
        e.setAttribute('r', (1.4 + 2.8 * d + (1 - st.k)).toFixed(2)); e.setAttribute('fill', p.c < 0.5 ? '#3ee6ff' : '#9a86ff'); e.setAttribute('opacity', (0.18 + 0.82 * d).toFixed(3));
      });
    });
    c.tl.fromTo(st, { k: 0 }, { k: 1, duration: 1.6, ease: 'power3.inOut' }, tc);
    c.tl.fromTo(st, { rot: 0 }, { rot: (c.T1 - c.T0) * 0.35, duration: Math.max(0.1, c.T1 - c.T0), ease: 'none' }, c.T0);
    c.fade(sv, tc - 0.1, 0.5);
    if (C.label) { const lb = h(box, 'div', 'p-core-lb', '', esc(C.label)); c.rise(lb, tc + 0.8, 16); }
    const svg = fullSvg(box);
    const fin = svgEl(svg, 'path', { d: 'M450 565 L650 565', stroke: '#3ee6ff', 'stroke-width': 5, 'stroke-dasharray': '14 12', fill: 'none' });
    const fout = svgEl(svg, 'path', { d: 'M950 565 L1108 565', stroke: '#3ef0a0', 'stroke-width': 5, 'stroke-dasharray': '14 12', fill: 'none' });
    c.fade(fin, ti + 0.3); c.fade(fout, to);
    c.tl.fromTo([fin, fout], { strokeDashoffset: 0 }, { strokeDashoffset: -26 * Math.ceil((c.T1 - c.T0) * 2), duration: Math.max(0.1, c.T1 - c.T0), ease: 'none' }, c.T0);
    const inC = h(box, 'div', 'p-card', 'left:130px', `<div class="cp" style="color:var(--cyan)">${esc(I.title || 'ENTRADA')}</div>`);
    (I.files || []).slice(0, 3).forEach((f, i) => h(inC, 'div', 'p-file', `top:${22 + i * 52}px`, esc(f)));
    const nf = Math.min(3, (I.files || []).length);
    [250, 210, 236, 150].slice(0, Math.max(1, 4 - nf)).forEach((w, i) => h(inC, 'div', 'p-line', `top:${40 + nf * 52 + i * 24}px;width:${w}px`));
    c.tl.fromTo(inC, { opacity: 0, x: -80 }, { opacity: 1, x: 0, duration: 0.5, ease: 'power3.out' }, ti);
    for (let i = 0; i < 5; i++) { const r = svgEl(svg, 'rect', { width: 16, height: 16, rx: 4, x: 442, y: 557, fill: '#3ee6ff', opacity: 0 }); c.tl.fromTo(r, { x: 0, opacity: 0 }, { x: 205, opacity: 1, duration: 0.55, ease: 'power1.in' }, ti + 0.5 + i * 0.2); c.tl.to(r, { opacity: 0, duration: 0.1 }, ti + 1.05 + i * 0.2); }
    const outC = h(box, 'div', 'p-card', 'left:1110px', `<div class="cp" style="color:var(--mint)">${esc(O.title || 'SAÍDA')}</div><div style="position:absolute;left:18px;top:20px;width:286px"></div>`);
    const body = outC.lastChild, toks = O.tokens || [];
    toks.forEach((t) => h(body, 'span', 'p-tk', '', esc(typeof t === 'string' ? t : t.text)));
    c.tl.fromTo(outC, { opacity: 0, x: 60 }, { opacity: 1, x: 0, duration: 0.5, ease: 'power3.out' }, to);
    [...body.children].forEach((sp, i) => { const tt = typeof toks[i] === 'object' && toks[i].at != null ? toks[i].at : to + 0.3 + i * 0.3; c.tl.fromTo(sp, { opacity: 0, scale: 0.7 }, { opacity: 1, scale: 1, duration: 0.25, ease: 'back.out(2)' }, tt); });
  };

  // orbs — opções diferentes (nomes, tamanhos, etiquetas), com destaque opcional
  V2.P.orbs = function (box, s, c) {
    const items = s.items || [], n = items.length;
    const SL = n <= 3 ? [[400, 540], [745, 540], [1090, 540]] : [[330, 420], [820, 370], [1250, 430], [330, 740], [620, 720], [1030, 690], [1250, 780]];
    const ta = def(s.at, c.T0 + 0.2), els = [];
    items.forEach((it, i) => {
      const [x, y] = SL[i % SL.length], col = it.color || COLORS[i % COLORS.length], sz = def(it.size, 1);
      const el = h(box, 'div', 'o-orb', `left:${x - 70}px;top:${y - 70}px;background:radial-gradient(circle at 34% 30%,#fff 0%,${col} 26%,${col}55 62%,${col}00 72%);box-shadow:0 0 50px ${col}66`,
        `<div class="nm">${esc(it.name)}</div>${it.tag ? `<div class="pr">${esc(it.tag)}</div>` : ''}`);
      els.push(el);
      const t = def(it.at, ta + i * 0.08);
      c.tl.fromTo(el, { x: 745 - x, y: 530 - y, scale: 0, opacity: 0 }, { x: 0, y: 0, scale: s.sizes_at != null ? 0.85 : sz, opacity: 1, duration: 0.7, ease: 'back.out(1.4)' }, t);
      if (s.names_at != null) c.tl.fromTo(el.querySelector('.nm'), { opacity: 0 }, { opacity: 1, duration: 0.3 }, s.names_at + i * 0.08);
      if (s.sizes_at != null) c.tl.to(el, { scale: sz, duration: 0.6, ease: 'back.out(2)' }, s.sizes_at + i * 0.05);
      if (it.tag) c.tl.fromTo(el.querySelector('.pr'), { opacity: 0, y: -30 }, { opacity: 1, y: 0, duration: 0.35, ease: 'bounce.out' }, def(s.tags_at, t + 0.4) + i * 0.08);
    });
    if (s.pick && s.pick.at != null) {
      const k = items.findIndex((it) => it.name === s.pick.name);
      els.forEach((el, i) => { if (i !== k) c.tl.to(el, { opacity: 0.25, duration: 0.4 }, s.pick.at); });
      if (k >= 0) {
        c.tl.to(els[k], { scale: def(items[k].size, 1) * 1.25, boxShadow: '0 0 90px #3ef0a0', duration: 0.5, ease: 'back.out(2)' }, s.pick.at);
        if (s.pick.note) { const nt = h(box, 'div', 'v2-chip', `left:${SL[k][0] - 160}px;top:${SL[k][1] + 110}px;width:320px;border-color:var(--mint);color:var(--mint)`, esc(s.pick.note)); c.pop(nt, s.pick.at + 0.3); }
      }
    }
  };

  // podium — "qual é o melhor?": opções brigam pelo topo e o pódio desmorona
  V2.P.podium = function (box, s, c) {
    const names = (s.names || ['A', 'B', 'C']).slice(0, 6), qa = def(s.question_at, c.T0 + 0.3), col = def(s.collapse_at, c.T1 - 1.5);
    const q = h(box, 'div', 's-line', `top:170px;font-size:${fs(s.question, 90, 60, 16, 50)}px`, plain(s.question).split(' ').map((w) => `<span>${esc(w)}</span>`).join(''));
    [...q.children].forEach((sp, i, a) => c.tl.fromTo(sp, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.3, ease: c.E }, s.wt ? s.wt[i] : qa + i * 0.12));
    const steps = [[520, 750, 130, '2'], [680, 690, 190, '1'], [840, 790, 90, '3']].map(([x, y, hh, l]) => {
      const e = h(box, 'div', '', `position:absolute;left:${x}px;top:${y}px;width:160px;height:${hh}px;border-radius:12px 12px 0 0;background:linear-gradient(180deg,#26365c,#121a2e);border:1.5px solid rgba(130,170,255,.3);font-family:MontBlack;font-size:44px;text-align:center;line-height:${hh}px;color:rgba(238,243,255,.5);box-sizing:border-box`, l);
      c.tl.fromTo(e, { scaleY: 0, transformOrigin: '50% 100%' }, { scaleY: 1, duration: 0.5, ease: 'power3.out' }, c.T0 + 0.1);
      return e;
    });
    const P = [[760, 632], [600, 692], [920, 732]], back = [[1120, 780], [1210, 780], [1300, 780]];
    const orbs = names.map((nm, i) => {
      const colr = COLORS[i % COLORS.length], [x, y] = i < 3 ? P[i] : back[i - 3];
      const e = h(box, 'div', 'o-orb', `left:${x - 50}px;top:${y - 50}px;width:100px;height:100px;border-radius:50px;background:radial-gradient(circle at 34% 30%,#fff 0%,${colr} 26%,${colr}55 62%,${colr}00 72%)`, `<div class="nm" style="left:-50px;top:36px;font-size:19px">${esc(nm)}</div>`);
      c.tl.fromTo(e, { opacity: 0, y: -80 }, { opacity: i < 3 ? 1 : 0.4, y: 0, duration: 0.5, ease: 'bounce.out' }, c.T0 + 0.35 + i * 0.1);
      return { e, x, y };
    });
    const pos = [0, 1, 2], swapT = s.swaps_at || [0, 1, 2].map((k) => qa + 0.9 + k * Math.max(0.35, (col - qa - 1.2) / 3));
    swapT.forEach((t, k) => {
      const a = k % 3, b = (k + 1) % 3; const ia = pos.indexOf(a), ib = pos.indexOf(b); pos[ia] = b; pos[ib] = a;
      [ia, ib].forEach((oi) => c.tl.to(orbs[oi].e, { x: P[pos[oi]][0] - orbs[oi].x, y: P[pos[oi]][1] - orbs[oi].y, duration: 0.35, ease: 'power3.inOut' }, t));
    });
    steps.forEach((e, i) => c.tl.to(e, { y: 260, rotation: [-22, 10, 26][i], opacity: 0, duration: 0.7, ease: 'power2.in' }, col + i * 0.07));
    orbs.forEach((o, i) => c.tl.to(o.e, { y: '+=240', opacity: 0, duration: 0.7, ease: 'power2.in' }, col + 0.05 + i * 0.05));
    c.tl.to(q, { color: '#ff5d7a', duration: 0.2 }, col + 0.2);
    const cr = h(box, 'div', '', 'position:absolute;left:330px;top:228px;width:830px;height:8px;border-radius:4px;background:var(--rose);box-shadow:0 0 20px var(--rose);transform-origin:0% 50%');
    c.tl.fromTo(cr, { scaleX: 0 }, { scaleX: 1, duration: 0.35, ease: 'power4.out' }, col + 0.45);
  };

  // statement — frase-chave palavra a palavra (no tempo da fala), com risco e troca
  const stFont = (text, size) => size || Math.round(Math.max(46, Math.min(fs(text, 84, 50, 18, 70), 1300 / (plain(text).length * 0.6))));
  V2.P.statement = function (box, s, c) {
    const mk = (text, wt, at, y, size) => {
      const words = String(text).split(/\s+/).filter(Boolean);
      const f = stFont(text, size);
      const one = plain(text).length * 0.6 * f <= 1330;
      const ln = h(box, 'div', 's-line', `top:${y}px;font-size:${f}px;line-height:1.15;${one ? 'white-space:nowrap' : ''}`);
      let mode = '';
      words.forEach((w, i) => {
        let t = w, cls = mode;
        for (const [m, k] of [['**', 'hl'], ['++', 'good'], ['~~', 'strike']]) {
          if (t.startsWith(m)) { mode = k; cls = k; t = t.slice(2); }
          if (t.replace(/[.,!?:;]+$/, '').endsWith(m)) { const p = t.replace(/[.,!?:;]+$/, ''); t = p.slice(0, -2) + t.slice(p.length); cls = cls || k; mode = ''; }
        }
        const sp = h(ln, 'span', cls === 'strike' ? '' : cls, cls === 'good' ? 'text-shadow:0 0 30px rgba(62,240,160,.55)' : '', esc(t));
        const tw = wt ? wt[i] : at + i * 0.13;
        if (cls === 'good') c.tl.fromTo(sp, { opacity: 0, rotationX: -100 }, { opacity: 1, rotationX: 0, duration: 0.5, ease: 'back.out(1.8)' }, tw);
        else c.tl.fromTo(sp, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.28, ease: c.E }, tw);
        if (cls === 'strike') { const k = h(sp, 'i', 'strk'); c.tl.fromTo(k, { scaleX: 0 }, { scaleX: 1, duration: 0.3, ease: 'power3.out' }, def(s.strike_at, tw + 0.45)); c.tl.to(sp, { opacity: 0.55, duration: 0.3 }, def(s.strike_at, tw + 0.45)); }
      });
      return ln;
    };
    const top = s.pos === 'top';
    const y1 = top ? 165 : (s.then ? 330 : 430);
    const l1 = mk(s.text, s.wt, def(s.at, c.T0 + 0.1), y1, s.size);
    if (s.then) {
      const ta = def(s.then.at, c.T1 - 2);
      if (s.then.replace !== false) c.tl.to(l1, { opacity: 0, y: -30, duration: 0.3 }, ta - 0.3);
      else c.tl.to(l1, { opacity: 0.45, scale: 0.8, y: -60, duration: 0.4 }, ta - 0.2);
      const f1 = stFont(s.text, s.size), n1 = plain(s.text).length * 0.6 * f1 <= 1330 ? 1 : 2;
      mk(s.then.text, s.then.wt, ta, s.then.replace !== false ? y1 : y1 + n1 * f1 * 1.15 * 0.8 + 10, s.then.size);
    }
  };

  // radar — critérios como eixos; requisito vira polígono; candidatos encaixam ou não
  V2.P.radar = function (box, s, c) {
    const axes = s.axes || [], k = axes.length, C = [745, 600], RAD = 210, T = times(axes, c, 0.9);
    const dir = axes.map((_, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / k; return [Math.cos(a), Math.sin(a)]; });
    const svg = fullSvg(box), grid = svgEl(svg, 'g', { fill: 'none', stroke: 'rgba(130,170,255,.25)', 'stroke-width': 2 });
    [1 / 3, 2 / 3, 1].forEach((f) => svgEl(grid, 'polygon', { points: dir.map((d) => [C[0] + d[0] * RAD * f, C[1] + d[1] * RAD * f].join(',')).join(' ') }));
    c.tl.fromTo(grid, { opacity: 0, scale: 0.6, transformOrigin: `${C[0]}px ${C[1]}px` }, { opacity: 1, scale: 1, duration: 0.6, ease: 'power3.out' }, c.T0 + 0.1);
    const cands = s.candidates || [];
    const pc = cands.map((cd, i) => svgEl(svg, 'polygon', { fill: cd.fit ? 'rgba(62,240,160,.25)' : 'rgba(154,134,255,.18)', stroke: cd.fit ? '#3ef0a0' : '#9a86ff', 'stroke-width': cd.fit ? 5 : 4, points: '' }));
    const req = svgEl(svg, 'polygon', { fill: 'rgba(255,182,56,.12)', stroke: '#ffb638', 'stroke-width': 4, 'stroke-dasharray': '12 8', points: '' });
    const st = { r: axes.map(() => 0), c: cands.map(() => 0) };
    const dots = axes.map(() => svgEl(svg, 'circle', { r: 10, fill: '#ffb638', cx: C[0], cy: C[1], opacity: 0 }));
    const poly = (vals) => vals.map((v, i) => [C[0] + dir[i][0] * RAD * v, C[1] + dir[i][1] * RAD * v].map((q) => q.toFixed(1)).join(',')).join(' ');
    c.render(() => {
      const rv = st.r.map((f, i) => f * def(axes[i].value, 0.7));
      req.setAttribute('points', poly(rv));
      rv.forEach((v, i) => { dots[i].setAttribute('cx', (C[0] + dir[i][0] * RAD * v).toFixed(1)); dots[i].setAttribute('cy', (C[1] + dir[i][1] * RAD * v).toFixed(1)); });
      cands.forEach((cd, j) => pc[j].setAttribute('points', poly((cd.values || []).map((v) => v * st.c[j]))));
    });
    axes.forEach((ax, i) => {
      const ln = svgEl(svg, 'line', { x1: C[0], y1: C[1], x2: C[0] + dir[i][0] * RAD, y2: C[1] + dir[i][1] * RAD, stroke: 'rgba(238,243,255,.55)', 'stroke-width': 3 });
      drawLine(c, ln, T[i] - 0.1, 0.35);
      const lx = C[0] + dir[i][0] * (RAD + 36), ly = C[1] + dir[i][1] * (RAD + 36) + 9;
      const tx = svgEl(svg, 'text', { x: lx, y: ly, 'text-anchor': Math.abs(dir[i][0]) < 0.3 ? 'middle' : dir[i][0] > 0 ? 'start' : 'end', fill: '#ffb638', class: 'r-ax' }); tx.textContent = String(ax.label).toUpperCase();
      c.fade(tx, T[i], 0.3);
      c.tl.fromTo(dots[i], { opacity: 0 }, { opacity: 1, duration: 0.1 }, T[i]);
      c.tl.to(st.r, { [i]: 1, duration: 0.5, ease: 'back.out(1.6)' }, T[i] + 0.05);
    });
    cands.forEach((cd, j) => {
      const t = def(cd.at, c.T1 - 2 + j * 0.8);
      const card = h(box, 'div', 'r-cand', `top:${520 + j * 80}px`, `<div class="d" style="background:${cd.fit ? '#3ef0a0' : '#9a86ff'}"></div><div class="n">${esc(cd.name)}</div><div class="v" style="color:${cd.fit ? 'var(--mint)' : 'var(--rose)'}">${cd.fit ? '✓' : '✕'} ${esc(cd.note || '')}</div>`);
      c.tl.fromTo(card, { opacity: 0, x: 40 }, { opacity: 1, x: 0, duration: 0.3 }, t);
      c.tl.to(st.c, { [j]: 1, duration: 0.45, ease: 'back.out(1.3)' }, t + 0.05);
      if (!cd.fit) { c.tl.to(pc[j], { attr: { stroke: '#ff5d7a' }, duration: 0.2 }, t + 0.5); c.tl.to(st.c, { [j]: 0, duration: 0.35, ease: 'power2.in' }, t + 0.8); }
      else c.tl.fromTo(svg, { filter: 'drop-shadow(0 0 0px #3ef0a0)' }, { filter: 'drop-shadow(0 0 22px #3ef0a0)', duration: 0.3 }, t + 0.4);
    });
  };

  // lanes — nomes/ideias separados por função em trilhas
  V2.P.lanes = function (box, s, c) {
    const L = s.lanes || [], m = L.length, gap = 24, w = (1330 - (m - 1) * gap) / m;
    const lx = L.map((_, i) => 90 + i * (w + gap));
    const laneEls = L.map((ln, i) => {
      const col = ln.color || COLORS[i % COLORS.length];
      const e = h(box, 'div', 'l-lane', `left:${lx[i]}px;width:${w}px`, `<div class="ic" style="background:${col}">${icon(ln.icon || 'dot', 28, '#0b1020', 2.4)}</div><div class="tt">${esc(ln.title)}</div>${ln.sub ? `<div class="vb">${esc(ln.sub)}</div>` : ''}`);
      c.tl.fromTo(e, { opacity: 0, y: 80 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }, def(s.lanes_at, c.T0 + 0.2) + i * 0.1);
      return e;
    });
    const focus = (i, t) => c.tl.to(laneEls, { opacity: (k) => (k === i ? 1 : 0.5), borderColor: (k) => (k === i ? 'rgba(255,182,56,.85)' : 'rgba(130,170,255,.22)'), duration: 0.35 }, t);
    // itens dentro das trilhas
    const yy = L.map(() => 350);
    (s.items || []).forEach((it) => {
      const i = it.lane, ww = w - 28, f = 21, hh = lines(it.text, f, ww - 56) * 26 + 26;
      const e = h(box, 'div', 'l-item', `left:${lx[i] + 14}px;top:${yy[i]}px;width:${ww}px`, rich(it.text));
      yy[i] += hh + 12;
      const t = def(it.at, c.T0 + 1);
      c.tl.fromTo(e, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.4, ease: 'power3.out' }, t);
      if (s.autofocus !== false) focus(i, t - 0.05);
    });
    // fichas: caos → faixa → trilha
    const chips = s.chips || [], cw = chips.map((ch) => Math.round(plain(ch.label).length * 11 + 40));
    const tot = cw.reduce((a, b) => a + b + 10, 0), sc = Math.min(1, 1330 / tot);
    let bx = 90;
    const trayX = L.map((_, i) => lx[i] + 14), trayY = L.map(() => 870 - 58);
    chips.forEach((ch, k) => {
      const e = h(box, 'div', 'v2-chip', `left:${bx}px;top:185px;width:${cw[k]}px;transform-origin:0 0`, esc(ch.label));
      e.setAttribute('data-layout-allow-overlap', '');
      const bxk = bx; bx += (cw[k] + 10) * sc;
      if (s.chaos_at != null) {
        const R = c.rnd, cx = 200 + R() * 1000 - bxk, cy = 330 + R() * 420 - 185, r = (R() - 0.5) * 40;
        c.tl.fromTo(e, { x: cx, y: cy, rotation: r, scale: 0.4, opacity: 0 }, { scale: 1.2, opacity: 1, duration: 0.4, ease: 'back.out(2)' }, s.chaos_at + k * 0.04);
        c.tl.to(e, { x: cx + (R() - 0.5) * 90, y: cy + (R() - 0.5) * 60, rotation: -r, duration: Math.max(0.5, def(s.sort_at, s.chaos_at + 2) - s.chaos_at - 0.4), ease: 'sine.inOut' }, s.chaos_at + 0.4);
        c.tl.to(e, { x: 0, y: 0, rotation: 0, scale: sc, duration: 0.7, ease: 'power3.inOut' }, def(s.sort_at, s.chaos_at + 2) + k * 0.03);
      } else c.tl.fromTo(e, { opacity: 0, scale: sc * 0.5 }, { opacity: 1, scale: sc, duration: 0.35, ease: 'back.out(2)' }, c.T0 + 0.3 + k * 0.05);
      if (ch.lane != null && ch.at != null) {
        const i = ch.lane, s2 = 0.82, wd = cw[k] * s2;
        if (trayX[i] + wd > lx[i] + w - 10) { trayX[i] = lx[i] + 14; trayY[i] -= 44; }
        c.tl.to(e, { x: trayX[i] - bxk, y: trayY[i] - 185, scale: s2, duration: 0.6, ease: 'power3.inOut' }, ch.at);
        c.tl.to(e, { borderColor: COLORS[i % COLORS.length], duration: 0.3 }, ch.at + 0.4);
        trayX[i] += wd + 8;
      }
    });
    (s.focus || []).forEach((f) => focus(f.lane, f.at));
  };

  // compare — antes/depois ou errado/certo, lado a lado
  V2.P.compare = function (box, s, c) {
    const Lx = [s.left || {}, s.right || {}];
    const f = Math.min(34, ...Lx.map((P) => fs((P.lines || []).map((l) => (typeof l === 'string' ? l : l.text)).join(' '), 34, 26, 40, 200)));
    const hOf = (P) => { let y = 104; (P.lines || []).forEach((l) => { y += lines(typeof l === 'string' ? l : l.text, f, 548) * f * 1.3 + 24; }); return Math.max(300, y + 26); };
    const H = Math.max(hOf(Lx[0]), hOf(Lx[1])), top = Math.max(190, 500 - H / 2 - (s.verdict ? 40 : 0));
    const panel = (P, x, tone, t) => {
      const col = tone === 'good' ? '#3ef0a0' : tone === 'bad' ? '#ff5d7a' : '#3ee6ff';
      const e = h(box, 'div', 'c-panel', `left:${x}px;top:${top}px;height:${H}px;border-color:${col}88`, `<div class="hd" style="color:${col};font-size:${fs(P.title, 34, 25, 16, 40)}px">${esc(P.title)}</div><div class="st" style="background:${col}">${icon(tone === 'good' ? 'check' : tone === 'bad' ? 'x' : 'dot', 28, '#0b1020', 3)}</div>`);
      c.tl.fromTo(e, { opacity: 0, x: x < 700 ? -60 : 60 }, { opacity: 1, x: 0, duration: 0.5, ease: 'power3.out' }, t);
      c.tl.fromTo(e.querySelector('.st'), { scale: 0 }, { scale: 1, duration: 0.4, ease: 'back.out(3)' }, t + 0.3);
      let y = 104;
      (P.lines || []).forEach((ln, i) => {
        const txt = typeof ln === 'string' ? ln : ln.text, hh = lines(txt, f, 548) * f * 1.3;
        const le = h(e, 'div', 'c-line', `top:${y}px;font-size:${f}px`, rich(txt));
        y += hh + 24;
        c.tl.fromTo(le, { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.35 }, def(ln.at, t + 0.4 + i * 0.4));
      });
      return e;
    };
    const tl0 = def(s.left && s.left.at, c.T0 + 0.2), tr0 = def(s.right && s.right.at, tl0 + 1.5);
    const le = panel(Lx[0], 90, Lx[0].tone || 'bad', tl0);
    panel(Lx[1], 790, Lx[1].tone || 'good', tr0);
    if ((Lx[0].tone || 'bad') === 'bad') c.tl.to(le, { opacity: 0.6, duration: 0.4 }, tr0 + 0.2);
    if (s.verdict) { const v = h(box, 'div', 'c-verdict', `top:${top + H + 40}px`, rich(s.verdict.text)); c.rise(v, def(s.verdict.at, c.T1 - 1.5), 20); }
  };

  // chat — conversa com bolhas (você / IA / nota), IA "digitando"
  V2.P.chat = function (box, s, c) {
    const win = h(box, 'div', 'ch-win', '', `<div class="ch-bar">${esc(s.title || 'Chat')}</div><div style="position:absolute;left:0;top:62px;width:1080px;height:658px;overflow:hidden"><div class="ch-in" style="position:absolute;left:0;top:0;width:1080px"></div></div>`);
    c.tl.fromTo(win, { opacity: 0, y: 40, scale: 0.97 }, { opacity: 1, y: 0, scale: 1, duration: 0.45, ease: 'power3.out' }, c.T0 + 0.05);
    const inner = win.querySelector('.ch-in'), M = s.messages || [], T = times(M, c, 1.2);
    let y = 26;
    M.forEach((m, i) => {
      const role = m.role || 'user', f = role === 'note' ? 21 : 25, hh = lines(m.text, f, 700) * f * 1.32 + 36;
      if (y + hh > 640) { c.tl.to(inner, { y: -(y + hh - 630), duration: 0.4, ease: 'power2.inOut' }, T[i] - 0.2); }
      if (role === 'ai') {
        const d = h(inner, 'div', 'ch-dots', `top:${y}px`, '<i style="left:22px"></i><i style="left:43px"></i><i style="left:64px"></i>');
        c.tl.fromTo(d, { opacity: 0 }, { opacity: 1, duration: 0.15 }, T[i] - 0.75);
        c.tl.fromTo(d.children, { y: 0 }, { y: -8, duration: 0.18, yoyo: true, repeat: 3, stagger: 0.08 }, T[i] - 0.7);
        c.tl.to(d, { opacity: 0, duration: 0.1 }, T[i] - 0.05);
      }
      const e = h(inner, 'div', 'ch-msg ' + ({ user: 'ch-u', ai: 'ch-a', note: 'ch-n' }[role]), `top:${y}px`, rich(m.text));
      if (role === 'note') gsap.set(e, { xPercent: -50 });
      c.tl.fromTo(e, { opacity: 0, y: 20, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.35, ease: c.E }, T[i]);
      y += hh + 18;
    });
  };

  // terminal — comandos digitados e respostas
  V2.P.terminal = function (box, s, c) {
    const win = h(box, 'div', 't-win', '', `<div class="t-bar"><i style="left:20px;background:#ff5f57"></i><i style="left:46px;background:#febc2e"></i><i style="left:72px;background:#28c840"></i><span>${esc(s.title || 'terminal')}</span></div><div style="position:absolute;left:0;top:52px;width:1210px;height:638px;overflow:hidden"><div class="t-in" style="position:absolute;left:0;top:0;width:1210px"></div></div>`);
    c.tl.fromTo(win, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.45, ease: 'power3.out' }, c.T0 + 0.05);
    const inner = win.querySelector('.t-in'), Ls = s.lines || [], T = times(Ls, c, 1.0);
    let y = 24;
    Ls.forEach((ln, i) => {
      const type = ln.type || 'cmd', txt = String(ln.text), hh = Math.ceil(Math.max(1, txt.length + 2) / 68) * 38;
      if (y + hh > 610) c.tl.to(inner, { y: -(y + hh - 600), duration: 0.3 }, T[i] - 0.1);
      const e = h(inner, 'div', 't-line', `top:${y}px;color:${type === 'cmd' ? '#eef3ff' : type === 'comment' ? '#7d8aa5' : type === 'err' ? '#ff5d7a' : '#9fb3d8'}`);
      y += hh + 8;
      if (type === 'cmd') {
        const pr = '<span style="color:#3ef0a0">$ </span>', st = { n: 0 }, body = h(e, 'span'); e.insertAdjacentHTML('afterbegin', pr);
        const cur = h(e, 'i', 't-cur');
        c.render(() => { body.textContent = txt.slice(0, Math.round(st.n)); });
        c.tl.fromTo(e, { opacity: 0 }, { opacity: 1, duration: 0.05 }, T[i] - 0.05);
        c.tl.fromTo(st, { n: 0 }, { n: txt.length, duration: Math.min(1.6, 0.25 + txt.length * 0.035), ease: 'none' }, T[i]);
        c.tl.fromTo(cur, { opacity: 1 }, { opacity: 0, duration: 0.1 }, def(Ls[i + 1] && Ls[i + 1].at, T[i] + 2) - 0.05);
      } else {
        e.textContent = txt;
        c.tl.fromTo(e, { opacity: 0, x: -10 }, { opacity: 1, x: 0, duration: 0.25 }, T[i]);
      }
    });
  };

  // filetree — pastas e arquivos aparecendo, com notas
  V2.P.filetree = function (box, s, c) {
    const win = h(box, 'div', 'f-win', '');
    c.tl.fromTo(win, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.45, ease: 'power3.out' }, c.T0 + 0.05);
    const rootRow = h(box, 'div', 'f-row', `left:160px;top:205px;color:var(--amber)`, `${icon('folder', 26, '#ffb638')}<span>${esc(s.root || 'projeto/')}</span>`);
    c.fade(rootRow, c.T0 + 0.25);
    const E = s.entries || [], T = times(E, c, 0.8), gap = Math.min(58, 600 / Math.max(1, E.length));
    let lastNote = null;
    E.forEach((en, i) => {
      const parts = String(en.path).replace(/\/$/, '').split('/'), depth = parts.length, dir = en.kind === 'dir' || /\/$/.test(en.path);
      const y = 205 + (i + 1) * gap;
      const row = h(box, 'div', 'f-row', `left:${160 + depth * 34}px;top:${y}px;color:${dir ? 'var(--amber)' : 'var(--ink)'}`, `${icon(dir ? 'folder' : 'doc', 26, dir ? '#ffb638' : '#3ee6ff')}<span>${esc(parts[parts.length - 1])}${dir ? '/' : ''}</span>`);
      c.tl.fromTo(row, { opacity: 0, x: -24 }, { opacity: 1, x: 0, duration: 0.35, ease: 'power3.out' }, T[i]);
      c.tl.fromTo(row, { color: '#ffffff' }, { color: dir ? '#ffb638' : '#eef3ff', duration: 0.8 }, T[i] + 0.1);
      if (en.note) {
        const nt = h(box, 'div', 'f-note', `top:${y - 6}px`, rich(en.note));
        c.tl.fromTo(nt, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.35 }, T[i] + 0.2);
        if (lastNote) c.tl.to(lastNote, { opacity: 0.35, duration: 0.3 }, T[i] + 0.2);
        lastNote = nt;
      }
    });
  };

  // counter — números grandes contando
  V2.P.counter = function (box, s, c) {
    const it = s.items || [], n = it.length, T = times(it, c, 0.8), fz = [220, 160, 124][Math.min(2, n - 1)];
    it.forEach((x, i) => {
      const w = 1330 / n, left = 90 + i * w, st = { v: 0 }, dec = def(x.decimals, 0);
      const num = h(box, 'div', 'k-num', `left:${left}px;top:${430 - fz * 0.6}px;width:${w}px;font-size:${fz}px;color:${COLORS[(i + 1) % COLORS.length]}`);
      const lb = h(box, 'div', 'k-lab', `left:${left + 20}px;top:${430 + fz * 0.5}px;width:${w - 40}px`, esc(x.label));
      c.render(() => { num.textContent = (x.prefix || '') + st.v.toFixed(dec).replace('.', ',') + (x.suffix || ''); });
      c.tl.fromTo(num, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(2)' }, T[i]);
      c.tl.fromTo(st, { v: 0 }, { v: Number(x.value) || 0, duration: 0.9, ease: 'power2.out' }, T[i]);
      c.rise(lb, T[i] + 0.3, 16);
    });
  };

  // steps — laboratório passo a passo com trilho de progresso
  V2.P.steps = function (box, s, c) {
    const S = s.steps || [], n = S.length, T = times(S, c, 1.5), w = (1330 - (n - 1) * 24) / n;
    if (s.goal) { const g = h(box, 'div', 'st-goal', '', rich(s.goal)); c.fade(g, c.T0 + 0.1); }
    h(box, 'div', 'st-rail'); const fill = h(box, 'div', 'st-fill');
    c.tl.fromTo(fill, { scaleX: 0 }, { scaleX: 0, duration: 0.01 }, c.T0);
    const cards = S.map((st, i) => {
      const x = 90 + i * (w + 24);
      const e = h(box, 'div', 'st-card', `left:${x}px;width:${w}px`, `<div class="n">${i + 1}</div><div class="ok">${icon('check', 40, '#3ef0a0', 3)}</div><div class="tx" style="font-size:${fs(st.title, 30, 21, 30, 150)}px">${rich(st.title)}</div>`);
      c.tl.fromTo(e, { opacity: 0, y: 60 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, T[i]);
      c.tl.fromTo(e.querySelector('.ok'), { opacity: 0, scale: 0 }, { opacity: 0, scale: 0, duration: 0.01 }, c.T0);
      c.tl.to(e, { borderColor: 'rgba(255,182,56,.9)', boxShadow: '0 0 50px rgba(255,182,56,.25)', duration: 0.3 }, T[i] + 0.1);
      c.tl.to(e.querySelector('.n'), { backgroundColor: '#ffb638', color: '#1a1000', duration: 0.3 }, T[i] + 0.1);
      c.tl.to(fill, { scaleX: (i + 1) / n, duration: 0.6, ease: 'power2.inOut' }, T[i]);
      return e;
    });
    cards.forEach((e, i) => {
      const done = i + 1 < n ? T[i + 1] : def(s.done_at, null);
      if (done == null) return;
      c.tl.to(e, { borderColor: 'rgba(62,240,160,.6)', boxShadow: '0 0 0 rgba(0,0,0,0)', duration: 0.3 }, done);
      c.tl.to(e.querySelector('.ok'), { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(3)' }, done);
    });
  };

  // quiz — pergunta, pausa para pensar, resposta
  V2.P.quiz = function (box, s, c) {
    const ta = def(s.at, c.T0 + 0.2), tb = def(s.answer_at, ta + 4);
    const qf = fs(s.question, 38, 28, 60, 200), qh = lines(s.question, qf, 930) * qf * 1.3 + 80;
    const q = h(box, 'div', 'q-card', `font-size:${qf}px`, `<div class="mk">?</div><div class="tx" style="font-size:${qf}px">${rich(s.question)}</div>`);
    c.tl.fromTo(q, { opacity: 0, y: 40 }, { opacity: 1, y: 0, duration: 0.5, ease: 'power3.out' }, ta);
    c.tl.fromTo(q.querySelector('.mk'), { rotation: -90, scale: 0 }, { rotation: 0, scale: 1, duration: 0.5, ease: 'back.out(2.5)' }, ta + 0.2);
    const th = h(box, 'div', 'q-think', `top:${200 + qh + 30}px`, '<i style="left:0"></i><i style="left:30px"></i><i style="left:60px"></i>');
    c.tl.fromTo(th, { opacity: 0 }, { opacity: 1, duration: 0.2 }, ta + 1);
    const nb = Math.max(1, Math.floor((tb - ta - 1.2) / 0.5));
    c.tl.fromTo(th.children, { y: 0 }, { y: -12, duration: 0.25, yoyo: true, repeat: Math.min(40, nb), stagger: 0.1, ease: 'sine.inOut' }, ta + 1);
    c.tl.to(th, { opacity: 0, duration: 0.15 }, tb - 0.1);
    const af = fs(s.answer, 32, 25, 60, 220);
    const a = h(box, 'div', 'q-ans', `top:${200 + qh + 30}px`, `<div class="mk">${icon('check', 40, '#062414', 3.2)}</div><div class="tx" style="font-size:${af}px">${rich(s.answer)}</div>`);
    c.tl.fromTo(a, { opacity: 0, rotationX: -80 }, { opacity: 1, rotationX: 0, duration: 0.6, ease: 'back.out(1.4)' }, tb);
    if (s.note) { const nt = h(box, 'div', 'kw-s', `top:${200 + qh + 30 + lines(s.answer, af, 930) * af * 1.32 + 110}px;font-size:24px`, rich(s.note)); c.fade(nt, def(s.note_at, tb + 1.5)); }
  };

  // timeline — eventos em sequência
  V2.P.timeline = function (box, s, c) {
    const E = s.events || [], n = E.length, T = times(E, c, 0.9);
    h(box, 'div', 'tm-line'); const fill = h(box, 'div', 'tm-fill');
    c.tl.fromTo(fill, { scaleX: 0 }, { scaleX: 0, duration: 0.01 }, c.T0);
    E.forEach((ev, i) => {
      const x = 130 + (n === 1 ? 625 : i * 1250 / (n - 1)), up = i % 2 === 0;
      const d = h(box, 'div', 'tm-dot', `left:${x - 24}px`), lxp = Math.max(90, Math.min(1420 - 250, x - 125));
      const lb = h(box, 'div', 'tm-lab', `left:${lxp}px;top:${up ? 380 : 580}px`, rich(ev.label));
      c.tl.to(fill, { scaleX: (x - 130) / 1250, duration: 0.5, ease: 'power2.inOut' }, T[i] - 0.3);
      c.pop(d, T[i], { scale: 0 });
      c.tl.fromTo(lb, { opacity: 0, y: up ? 20 : -20 }, { opacity: 1, y: 0, duration: 0.35 }, T[i] + 0.1);
      if (ev.sub) { const sb = h(box, 'div', 'tm-sub', `left:${lxp}px;top:${up ? 440 : 640}px`, esc(ev.sub)); c.fade(sb, T[i] + 0.35); }
    });
  };

  // flow — nós e setas (arquitetura, caminho de dados)
  V2.P.flow = function (box, s, c) {
    const N = s.nodes || [], pos = {}, T = times(N, c, 0.8);
    const svg = fullSvg(box);
    const defs = svgEl(svg, 'defs', {}); const mk = svgEl(defs, 'marker', { id: 'arr' + c.S.n + '_' + Math.round(c.T0 * 10), markerWidth: 10, markerHeight: 10, refX: 8, refY: 5, orient: 'auto' }); svgEl(mk, 'path', { d: 'M0,0 L10,5 L0,10 z', fill: '#ffb638' });
    N.forEach((nd, i) => {
      const x = 100 + def(nd.col, i) * 270, y = 230 + def(nd.row, 1) * 170, col = COLORS[i % COLORS.length];
      pos[nd.id] = { x: x + 125, y: y + 55, t: T[i] };
      const e = h(box, 'div', 'fl-node', `left:${x}px;top:${y}px;border-color:${col}`, `${icon(nd.icon || 'dot', 40, col)}<div class="lb" style="font-size:${fs(nd.label, 23, 17, 12, 34)}px">${esc(nd.label)}</div>`);
      c.pop(e, T[i]);
    });
    (s.edges || []).forEach((ed, k) => {
      const a = pos[ed.from], b = pos[ed.to]; if (!a || !b) return;
      const dx = b.x - a.x, dy = b.y - a.y, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
      const cut = (u, v) => Math.min(Math.abs(u) > 1e-6 ? 130 / Math.abs(u) : 1e9, Math.abs(v) > 1e-6 ? 60 / Math.abs(v) : 1e9);
      const ca = cut(ux, uy) + 6, x1 = a.x + ux * ca, y1 = a.y + uy * ca, x2 = b.x - ux * (ca + 8), y2 = b.y - uy * (ca + 8);
      const p = svgEl(svg, 'path', { d: `M${x1} ${y1} L${x2} ${y2}`, stroke: '#ffb638', 'stroke-width': 4, fill: 'none', 'marker-end': `url(#${mk.id})` });
      const t = Math.max(def(ed.at, c.T0 + 1 + k * 0.6), a.t + 0.2, b.t + 0.2);
      drawLine(c, p, t, 0.45);
      c.tl.fromTo(p, { opacity: 0 }, { opacity: 1, duration: 0.05 }, t);
      const dot = svgEl(svg, 'circle', { r: 8, cx: x1, cy: y1, fill: '#fff', opacity: 0 });
      c.tl.set(dot, { opacity: 1 }, t + 0.45);
      c.tl.fromTo(dot, { attr: { cx: x1, cy: y1 } }, { attr: { cx: x2, cy: y2 }, duration: 0.6, ease: 'power1.inOut' }, t + 0.45);
      c.tl.to(dot, { opacity: 0, duration: 0.1 }, t + 1.05);
      if (ed.label) { const tx = svgEl(svg, 'text', { x: (x1 + x2) / 2, y: (y1 + y2) / 2 - 14, 'text-anchor': 'middle', fill: '#eef3ff', class: 'fl-el' }); tx.textContent = ed.label; c.fade(tx, t + 0.3); }
    });
  };

  // fields — documento/ficha sendo preenchido
  V2.P.fields = function (box, s, c) {
    const F = s.fields || [], n = F.length, T = times(F, c, 1.0), sp = Math.min(118, 520 / Math.max(1, n));
    const H = Math.min(720, 120 + n * sp + (s.stamp ? 110 : 30)), top = Math.max(170, 530 - H / 2);
    const doc = h(box, 'div', 'fd-doc', `top:${top}px;height:${H}px`, `<div class="hd">${esc(s.title || 'Ficha')}</div>`);
    c.tl.fromTo(doc, { opacity: 0, y: 60, rotation: -1.5 }, { opacity: 1, y: 0, rotation: 0, duration: 0.55, ease: 'power3.out' }, c.T0 + 0.05);
    F.forEach((f, i) => {
      const y = 120 + i * sp, row = h(doc, 'div', 'fd-row', `top:${y}px;height:${sp - 14}px`, `<div class="lb">${esc(f.label)}</div><div class="vl" style="font-size:${fs(f.value, 26, 19, 30, 120)}px"></div>`);
      const vl = row.querySelector('.vl'), txt = plain(f.value), st = { n: 0 };
      c.render(() => { vl.textContent = txt.slice(0, Math.round(st.n)); });
      c.fade(row, T[i] - 0.1, 0.2);
      c.tl.fromTo(st, { n: 0 }, { n: txt.length, duration: Math.min(1.4, 0.2 + txt.length * 0.025), ease: 'none' }, T[i]);
    });
    if (s.stamp) { const sm = h(doc, 'div', 'fd-stamp', `top:${H - 86}px;left:auto;right:48px`, esc(s.stamp.text)); c.tl.fromTo(sm, { opacity: 0, scale: 2.4, rotation: 8 }, { opacity: 1, scale: 1, rotation: -8, duration: 0.4, ease: 'power4.in' }, def(s.stamp.at, c.T1 - 1.2)); }
  };

  // keyword — palavra/número de impacto
  V2.P.keyword = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.1), f = s.size || fs(s.text, 160, 70, 6, 36);
    const k = h(box, 'div', 'kw-t', `top:${430 - f * 0.6}px;font-size:${f}px`, rich(s.text));
    c.tl.fromTo(k, { opacity: 0, scale: 2.2, filter: 'blur(16px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'power4.out' }, t);
    const svg = fullSvg(box), ring = svgEl(svg, 'circle', { cx: 745, cy: 430, r: 60, fill: 'none', stroke: '#ffb638', 'stroke-width': 4 });
    c.tl.fromTo(ring, { attr: { r: 60 }, opacity: 0.9 }, { attr: { r: 520 }, opacity: 0, duration: 0.9, ease: 'power2.out' }, t + 0.1);
    if (s.sub) { const nl = lines(s.text, f, 1330); const sb = h(box, 'div', 'kw-s', `top:${430 - f * 0.6 + nl * f * 1.05 + 24}px`, rich(s.sub)); c.rise(sb, def(s.sub_at, t + 0.6), 20); }
  };

  // module_intro — abertura cinematográfica de módulo
  V2.P.module_intro = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05);
    const nb = h(box, 'div', 'mi-n', '', String(s.n).padStart(2, '0'));
    const kk = h(box, 'div', 'mi-k', '', 'MÓDULO');
    c.tl.fromTo(nb, { opacity: 0, x: -120, filter: 'blur(12px)' }, { opacity: 1, x: 0, filter: 'blur(0px)', duration: 0.7, ease: 'power4.out' }, t);
    c.tl.fromTo(nb, { color: 'rgba(255,182,56,0)' }, { color: 'rgba(255,182,56,.14)', duration: 1.2 }, t + 0.5);
    c.fade(kk, t + 0.2);
    const ti = h(box, 'div', 'mi-t', `font-size:${fs(s.title, 76, 50, 20, 50)}px`, esc(s.title));
    c.tl.fromTo(ti, { opacity: 0, y: 50 }, { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' }, t + 0.35);
    let y = 640;
    [['OBJETIVO', s.goal, s.goal_at, 'var(--cyan)'], ['EXERCÍCIO', s.exercise, s.exercise_at, 'var(--amber)']].forEach(([k, v, at, col]) => {
      if (!v) return;
      const r = h(box, 'div', 'mi-row', `top:${y}px`, `<div class="k" style="color:${col}">${k}</div><div class="v">${rich(v)}</div>`);
      y += lines(v, 26, 1060) * 34 + 50;
      c.tl.fromTo(r, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.45, ease: 'power3.out' }, def(at, t + 1));
    });
  };

  // svg — diagrama da fonte animado (fallback para cenas "diagram")
  V2.P.svg = function (box, s, c) {
    const w = h(box, 'div', 'sv-wrap', '', s.svg || '');
    const el = w.querySelector('svg'); if (!el) return;
    el.removeAttribute('class'); el.setAttribute('width', '1270'); el.setAttribute('height', '660');
    const parts = [...el.querySelectorAll('rect,circle,ellipse,path,line,polyline,polygon,text')];
    const t = def(s.at, c.T0 + 0.2), span = Math.max(1, Math.min(6, (c.T1 - t) * 0.5));
    parts.forEach((p, i) => {
      const at = t + (i / Math.max(1, parts.length)) * span;
      if (p.tagName === 'text') c.tl.fromTo(p, { opacity: 0 }, { opacity: 1, duration: 0.3 }, at);
      else if (p.getTotalLength && p.tagName !== 'rect') { drawLine(c, p, at, 0.5); }
      else c.tl.fromTo(p, { opacity: 0, scale: 0.8, transformOrigin: '50% 50%' }, { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2)' }, at);
    });
    (s.marks || []).forEach((m) => {
      const hit = parts.find((p) => p.tagName === 'text' && p.textContent.trim().toLowerCase().includes(String(m.text).toLowerCase()));
      if (hit && m.at != null) c.tl.to(hit, { fill: '#ffb638', duration: 0.25 }, m.at);
    });
  };
})();
