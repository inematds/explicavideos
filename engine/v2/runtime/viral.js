/* Explicavideos v2 — perfil VIRAL (2.9): peças de tela cheia com muito movimento, para notícia/reel.
   Mesmo contrato do v2: fn(box, shot, ctx), tempos em segundos relativos à cena, tudo em c.tl (seek-safe).
   O palco tem o tamanho da área de cena do perfil: S.vw × S.vh (16:9 = 1920×1080; 9:16 = 1080×1150).
   Peças: capa, foto, capitulo, bignum, escala, barra, ranking, carimbo, cinetica, rosto, cta. Padrão: PADRAO-VIRAL.md */
(function () {
  const { h, esc, rich, fs } = V2.util;
  const def = (v, d) => (v == null || Number.isNaN(v) ? d : v);
  const fmt = (v, dec) => v.toLocaleString('pt-BR', { minimumFractionDigits: dec || 0, maximumFractionDigits: dec || 0 });
  const WH = (c) => [c.S.vw || 1920, c.S.vh || 1080];
  const TW = (c) => ((c.S.vw || 1920) >= 1500 ? 1320 : (c.S.vw || 1080));
  const P = V2.P;

  // imagem de fundo em tela cheia, sempre em movimento; `pontos` re-enquadra a mesma imagem nas deixas
  function bleed(box, s, c, t, opt) {
    const [W, H] = WH(c);
    const wrap = h(box, 'div', 'vr-bleed', `width:${W}px;height:${H}px`);
    const inteira = s.texto && W < 1500;
    if (inteira) h(wrap, 'div', 'vr-img vr-fill', `background-image:url("${s.src}")`);
    let im = h(wrap, 'div', 'vr-img' + (inteira ? ' vr-contain' : ''), `background-image:url("${s.src}")`);
    const ve = s.vid && c.root.querySelector('video[data-vid="' + s.vidid + '"]');
    if (ve) { wrap.insertBefore(ve, im); im.remove(); im = ve; ve.classList.add('vr-img'); }   // clipe .mp4 (voo 3D) no lugar da foto
    h(wrap, 'div', 'vr-grain', '');
    h(wrap, 'div', 'vr-shade' + (opt && opt.dark ? ' dark' : ''), '');
    const pts = [{ t, f: s.focus || [0.5, 0.5], z: (s.zoom || [1.05, 1.18])[0] }].concat((s.pontos || []).map((p) => ({ t: p.at, f: p.focus || [0.5, 0.5], z: p.zoom || 1.15 })));
    const endZ = (s.zoom || [1.05, 1.18])[1];
    const pos = (f, z) => ({ scale: z, xPercent: (0.5 - f[0]) * (z - 1) * 100, yPercent: (0.5 - f[1]) * (z - 1) * 100 });
    c.tl.set(im, pos(pts[0].f, pts[0].z), 0);
    pts.forEach((p, i) => {
      const nx = pts[i + 1];
      const t1 = nx ? nx.t : c.T1 + 0.6;
      if (i > 0) c.tl.to(im, Object.assign(pos(p.f, p.z), { duration: 0.55, ease: 'expo.out' }), p.t);
      const zEnd = nx ? p.z + 0.04 : Math.max(p.z + 0.04, endZ);
      c.tl.to(im, Object.assign(pos(p.f, zEnd), { duration: Math.max(0.4, t1 - p.t - (i > 0 ? 0.55 : 0)), ease: 'none' }), p.t + (i > 0 ? 0.55 : 0));
    });
    return wrap;
  }

  // flash de corte: faixa de luz que atravessa no início do shot (dá o "tranco" do viral)
  function corte(box, c, t) {
    const [W, H] = WH(c);
    const f = h(box, 'div', 'vr-flash', `width:${W}px;height:${H}px`);
    c.tl.fromTo(f, { opacity: 0.55 }, { opacity: 0, duration: 0.28, ease: 'power2.out', immediateRender: false }, t);
  }

  // texto de manchete: palavras entram uma a uma (com deixas próprias ou espaçadas)
  function manchete(box, txt, t, c, cls, css, gap) {
    const el = h(box, 'div', 'vr-head ' + (cls || ''), css || '');
    const parts = String(txt).split(/(\*\*.+?\*\*|\s+)/).filter((x) => x && !/^\s+$/.test(x));
    parts.forEach((w, i) => {
      const hl = /^\*\*/.test(w);
      const sp = h(el, 'span', hl ? 'hl' : '', '', esc(w.replace(/\*\*/g, '')));
      c.tl.fromTo(sp, { opacity: 0, y: 60, rotationX: -70 }, { opacity: 1, y: 0, rotationX: 0, duration: 0.42, ease: 'back.out(1.6)' }, t + i * (gap || 0.09));
    });
    return el;
  }

  // fundo das peças de número/palavra: a foto da cena (s.src ou S.fundo) desfocada e viva; preto só se não houver
  function fundo(box, s, c, t) {
    const src = s.src || c.S.fundo, [W] = WH(c);
    if (!src) { h(box, 'div', 'vr-black grad', ''); return; }
    const w = bleed(box, Object.assign({}, s, { src, zoom: s.zoom || [1.12, 1.28], focus: s.focus || [0.5, 0.5] }), c, t, { dark: true });
    [...w.querySelectorAll('.vr-img')].pop().style.filter = (W < 1500 ? 'blur(1.5px) saturate(1.35) brightness(1.05)' : 'blur(3px) saturate(1.3) brightness(.95)');
  }

  // capa — frame 0 pronto (thumbnail): imagem com o título já desenhado + selo opcional
  P.capa = function (box, s, c) {
    const w = bleed(box, s, c, 0, {});
    w.querySelector('.vr-shade').style.opacity = 0.25;
    c.tl.set(box, { opacity: 1 }, 0);
    if (s.selo) {
      const sl = h(box, 'div', 'vr-selo', '', esc(s.selo));
      c.tl.fromTo(sl, { opacity: 0, scale: 2.2, rotation: -8 }, { opacity: 1, scale: 1, rotation: -8, duration: 0.28, ease: 'power4.in' }, def(s.selo_at, 0.9));
    }
  };

  // foto — imagem em tela cheia com movimento, manchete opcional e destaques nas deixas
  P.foto = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05);
    bleed(box, s, c, t, { dark: !!s.titulo });
    corte(box, c, t);
    if (s.tag) { const tg = h(box, 'div', 'vr-tag', '', esc(s.tag)); c.tl.fromTo(tg, { opacity: 0, x: -40 }, { opacity: 1, x: 0, duration: 0.35, ease: 'power3.out' }, t + 0.1); }
    if (s.titulo) manchete(box, s.titulo, def(s.titulo_at, t + 0.2), c, 'low', `font-size:${s.size || fs(s.titulo, 118, 70, 10, 40)}px`);
    (s.marcas || []).forEach((m) => {
      const b = h(box, 'div', 'vr-marca', `left:${m.x * 100}%;top:${m.y * 100}%;width:${m.w * 100}%;height:${m.h * 100}%`, m.txt ? `<b>${esc(m.txt)}</b>` : '');
      c.tl.fromTo(b, { opacity: 0, scale: 1.25 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2)' }, m.at);
    });
  };

  // capitulo — tela limpa + assunto grande (molde clima-sul): foto empurrando, tag, palavra gigante, barra
  P.capitulo = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.02);
    if (s.src) bleed(box, Object.assign({ zoom: [1.16, 1.04] }, s), c, t, { dark: true });
    else h(box, 'div', 'vr-black', '');
    corte(box, c, t);
    const k = h(box, 'div', 'vr-kick', '', esc(s.k || ''));
    c.tl.fromTo(k, { opacity: 0, letterSpacing: '0.6em' }, { opacity: 1, letterSpacing: '0.28em', duration: 0.5, ease: 'power3.out' }, t + 0.05);
    const wd = h(box, 'div', 'vr-cap', `font-size:${s.size || fs(s.text, 190, 110, 6, 22)}px`, rich(s.text));
    c.tl.fromTo(wd, { opacity: 0, scale: 1.35, filter: 'blur(14px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.5, ease: 'expo.out' }, t + 0.12);
    const bar = h(box, 'div', 'vr-bar', '');
    c.tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.7, ease: 'expo.out' }, t + 0.25);
    if (s.sub) { const sb = h(box, 'div', 'vr-csub', '', rich(s.sub)); c.tl.fromTo(sb, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4 }, def(s.sub_at, t + 0.45)); }
  };

  // bignum — número gigante (contagem ≤ 0,8 s que termina na deixa), anel de impacto, pulso e legenda
  P.bignum = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), hit = def(s.hit_at, t + 0.8), cnt = Math.min(0.8, Math.max(0.3, hit - t));
    const [W, H] = WH(c);
    fundo(box, s, c, t);
    corte(box, c, t);
    const st = { v: Number(s.de) || 0 };
    if (s.k) { const k = h(box, 'div', 'vr-nk', '', esc(s.k)); c.tl.fromTo(k, { opacity: 0, y: -20 }, { opacity: 1, y: 0, duration: 0.3 }, t); }
    const nn = h(box, 'div', 'vr-num', `font-size:${s.size || (W < 1500 ? 220 : 250)}px;color:${s.cor || 'var(--amber)'}`);
    c.render(() => { nn.innerHTML = `${s.pre ? `<i>${esc(s.pre)}</i>` : ''}${fmt(st.v, s.dec)}${s.unid ? `<small>${esc(s.unid)}</small>` : ''}`; });
    c.tl.fromTo(nn, { opacity: 0, scale: 0.55 }, { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(1.8)' }, t);
    c.tl.fromTo(st, { v: Number(s.de) || 0 }, { v: Number(s.ate) || 0, duration: cnt, ease: 'power2.out' }, Math.max(t, hit - cnt));
    c.tl.to(nn, { scale: 1.09, duration: 0.14, yoyo: true, repeat: 1, ease: 'power2.out' }, hit);
    const ring = h(box, 'div', 'vr-ring', `left:${TW(c) / 2 - 160}px;top:${H * 0.46 - 160}px`);
    c.tl.fromTo(ring, { scale: 0.3, opacity: 0.9 }, { scale: 3.2, opacity: 0, duration: 0.7, ease: 'power2.out', immediateRender: false }, hit);
    if (s.l) { const l = h(box, 'div', 'vr-nl', '', rich(s.l)); c.tl.fromTo(l, { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.4 }, def(s.l_at, hit + 0.1)); }
  };

  // escala — comparação por cópias: a unidade (A) aparece e as cópias de B entram uma a uma até N (aceita fração)
  P.escala = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), N = Number(s.n) || 3;
    fundo(box, s, c, t);
    corte(box, c, t);
    if (s.titulo) manchete(box, s.titulo, t + 0.05, c, 'top', `font-size:${W < 1500 ? 64 : 76}px`);
    const k = Math.ceil(N), tw = Math.min((TW(c) * 0.86) / k - 24, H * 0.36), th = Math.min(tw * (s.prop || 0.62), H * 0.3);
    const x0 = (TW(c) - (k * tw + (k - 1) * 24)) / 2, y0 = H * 0.42 - th / 2;
    const steps = (s.passos || []).map((p) => p.at);
    for (let i = 0; i < k; i++) {
      const frac = Math.min(1, N - i);
      const tile = h(box, 'div', 'vr-tile' + (i === 0 && s.a ? ' a' : ''), `left:${x0 + i * (tw + 24)}px;top:${y0}px;width:${tw * frac}px;height:${th}px`,
        `<b>${esc(i === 0 && s.a ? s.a : (s.b || ''))}</b>`);
      const ti = def(steps[i], t + 0.2 + i * 0.28);
      c.tl.fromTo(tile, { opacity: 0, scale: 0.4, y: 40 }, { opacity: 1, scale: 1, y: 0, duration: 0.4, ease: 'back.out(2)' }, ti);
    }
    const ct = h(box, 'div', 'vr-ecount', `top:${y0 + th + 40}px`);
    const st = { v: 1 };
    c.render(() => { ct.innerHTML = `${fmt(st.v, s.dec == null ? 1 : s.dec)}<small>×</small> <span>${esc(s.l || '')}</span>`; });
    const tEnd = def(steps[k - 1], t + 0.2 + (k - 1) * 0.28);
    c.tl.fromTo(ct, { opacity: 0 }, { opacity: 1, duration: 0.25 }, t + 0.2);
    c.tl.fromTo(st, { v: 1 }, { v: N, duration: Math.max(0.3, tEnd - t - 0.1), ease: 'none' }, t + 0.25);
  };

  // barra — o todo vs. a parte: tanque cheio de "necessidade" e o pedacinho que existe (ex.: 2%)
  P.barra = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), pct = Number(s.pct) || 2, hit = def(s.hit_at, t + 1);
    fundo(box, s, c, t);
    corte(box, c, t);
    const bw = TW(c) * 0.86, bh = Math.min(170, H * 0.16), x = (TW(c) - bw) / 2, y = H * 0.4;
    const lt = h(box, 'div', 'vr-blab top', `left:${x}px;top:${y - 70}px;width:${bw}px`, rich(s.total || ''));
    const frame = h(box, 'div', 'vr-bframe', `left:${x}px;top:${y}px;width:${bw}px;height:${bh}px`);
    const fill = h(frame, 'div', 'vr-bfill', '');
    const ghost = h(frame, 'div', 'vr-bghost', '');
    c.tl.fromTo(lt, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.35 }, t);
    c.tl.fromTo(frame, { opacity: 0, scaleX: 0.2 }, { opacity: 1, scaleX: 1, duration: 0.5, ease: 'expo.out' }, t + 0.1);
    c.tl.fromTo(ghost, { width: '0%' }, { width: '100%', duration: 0.9, ease: 'power2.inOut' }, t + 0.3);
    c.tl.to(ghost, { opacity: 0.12, duration: 0.4 }, Math.max(t + 1.2, hit - 0.5));
    c.tl.fromTo(fill, { width: '0%' }, { width: Math.max(0.6, pct) + '%', duration: 0.5, ease: 'power2.out' }, hit - 0.4);
    const st = { v: 0 };
    const big = h(box, 'div', 'vr-bpct', `left:${x}px;top:${y + bh + 30}px`);
    c.render(() => { big.innerHTML = `${fmt(st.v, 0)}<small>%</small>`; });
    c.tl.fromTo(big, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.3, ease: 'back.out(2)' }, hit - 0.4);
    c.tl.fromTo(st, { v: 0 }, { v: pct, duration: 0.4, ease: 'power2.out' }, hit - 0.4);
    if (s.parte) { const lp = h(box, 'div', 'vr-blab', `left:${x + 260}px;top:${y + bh + 60}px;width:${bw - 260}px`, rich(s.parte)); c.tl.fromTo(lp, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.35 }, hit); }
  };

  // ranking — gráfico comparativo: barras horizontais que crescem uma a uma (cada item pode ter a sua deixa),
  // valor contando no fim da barra; "hl": true pinta a barra de âmbar (o destaque). "max" fixa a escala (padrão: maior valor).
  P.ranking = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), it = s.itens || [], n = Math.max(1, it.length);
    const v916 = W < 1500;
    fundo(box, s, c, t);
    corte(box, c, t);
    const tw = TW(c), x = v916 ? 50 : 70, pw = tw - x * 2;
    const top = H * (v916 ? 0.25 : 0.255), bot = H * (v916 ? 0.78 : 0.755);
    const rh = Math.min(v916 ? 190 : 130, (bot - top) / n), bh = rh * (v916 ? 0.36 : 0.42);
    // 9:16 (15/10/2026): o painel acompanha as linhas; com 0,66 da altura fixo, 3 itens deixavam ~60% do painel vazio
    const ptop = H * (v916 ? 0.17 : 0.13), fy = v916 ? top + n * rh + 20 : H * 0.765;
    const ph = v916 ? fy - ptop + (s.fonte ? 70 : 20) : H * 0.68;
    const pnl = h(box, 'div', 'vr-rpanel', `left:${x - 30}px;top:${ptop}px;width:${pw + 60}px;height:${ph}px`);
    c.tl.fromTo(pnl, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t);
    if (s.titulo) manchete(box, s.titulo, t + 0.05, c, 'top', `font-size:${v916 ? 56 : 68}px`);
    const lw = v916 ? pw : (s.lw || 380), bx = v916 ? x : x + lw + 20, bw = (v916 ? pw : pw - lw - 20) - (v916 ? 190 : 200);
    const mx = Number(s.max) || Math.max(...it.map((r) => Number(r.v) || 0)) || 1;
    it.forEach((r, i) => {
      const ti = def(r.at, t + 0.35 + i * 0.32), y = top + i * rh;
      const lab = h(box, 'div', 'vr-rlab' + (r.hl ? ' hl' : ''), `left:${x}px;top:${v916 ? y - 4 : y + rh * 0.5 - 26}px;width:${lw}px`, esc(r.n || ''));
      const by = v916 ? y + 44 : y + rh * 0.5 - bh / 2;
      const bar = h(box, 'div', 'vr-rbar' + (r.hl ? ' hl' : ''), `left:${bx}px;top:${by}px;height:${bh}px;width:${Math.max(6, bw * (Number(r.v) || 0) / mx)}px`);
      const val = h(box, 'div', 'vr-rval' + (r.hl ? ' hl' : ''), `left:${bx + Math.max(6, bw * (Number(r.v) || 0) / mx) + 18}px;top:${by + bh / 2 - (v916 ? 30 : 34)}px`);
      const st = { v: 0 };
      c.render(() => { val.innerHTML = `${s.pre ? esc(s.pre) : ''}${fmt(st.v, s.dec)}${s.unid ? `<small>${esc(s.unid)}</small>` : ''}`; });
      c.tl.fromTo(lab, { opacity: 0, x: -30 }, { opacity: 1, x: 0, duration: 0.3, ease: 'power3.out' }, ti);
      const tb = def(r.v_at, ti);   // "v_at": a barra cresce numa 2ª deixa (pergunta no "at", resposta no "v_at")
      c.tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.6, ease: 'expo.out' }, tb + 0.05);
      c.tl.fromTo(val, { opacity: 0 }, { opacity: 1, duration: 0.2 }, tb + 0.1);
      c.tl.fromTo(st, { v: 0 }, { v: Number(r.v) || 0, duration: 0.6, ease: 'power2.out' }, tb + 0.05);
      if (r.hl) c.tl.to(bar, { boxShadow: '0 0 70px rgba(255,182,56,.95)', duration: 0.18, yoyo: true, repeat: 1 }, tb + 0.65);
    });
    if (s.fonte) { const f = h(box, 'div', 'vr-rfonte', `left:${x}px;top:${fy}px`, esc(s.fonte)); c.tl.fromTo(f, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t + 0.4); }
  };

  // colunas — série no tempo (até ~30 barras verticais): sobem da esquerda para a direita; o "at" do item é a deixa em que
  // ele acende ("hl" âmbar, "alerta" vermelho) e mostra o valor (também com "mostra"); "rot"/"todos_rotulos" = ano embaixo (15/10/2026)
  P.colunas = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), it = s.itens || [], n = Math.max(1, it.length);
    const v916 = W < 1500;
    fundo(box, s, c, t);
    corte(box, c, t);
    const tw = TW(c), x = v916 ? 40 : 70, pw = tw - x * 2;
    const pnl = h(box, 'div', 'vr-rpanel', `left:${x - 30}px;top:${H * (v916 ? 0.17 : 0.13)}px;width:${pw + 60}px;height:${H * (v916 ? 0.66 : 0.7)}px`);
    c.tl.fromTo(pnl, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t);
    if (s.titulo) manchete(box, s.titulo, t + 0.05, c, 'top', `font-size:${v916 ? 56 : 68}px`);
    const top = H * (v916 ? 0.3 : 0.31), base = H * (v916 ? 0.74 : 0.74);
    const gap = n > 16 ? 8 : 18, cw = (pw - gap * (n - 1)) / n;
    const mx = Number(s.max) || Math.max(...it.map((r) => Number(r.v) || 0)) || 1;
    const passo = Math.min(0.09, 1.4 / n);
    it.forEach((r, i) => {
      const v = Number(r.v) || 0, bh = Math.max(4, (base - top) * v / mx), bx = x + i * (cw + gap);
      const cls = r.alerta ? ' alerta' : (r.hl ? ' hl' : '');
      const tg = t + 0.3 + i * passo, ti = Math.max(tg + 0.3, def(r.at, tg + 0.3));   // barra sobe em sequência; "at" = destaque
      const bar = h(box, 'div', 'vr-cbar', `left:${bx}px;top:${base - bh}px;width:${cw}px;height:${bh}px`);
      c.tl.fromTo(bar, { scaleY: 0 }, { scaleY: 1, duration: 0.5, ease: 'expo.out' }, tg);
      if (cls) { const on = h(bar, 'div', 'vr-cbar-on' + cls, ''); c.tl.fromTo(on, { opacity: 0 }, { opacity: 1, duration: 0.2 }, ti); }
      if (r.n != null && (s.todos_rotulos || r.hl || r.alerta || r.rot)) {
        const lab = h(box, 'div', 'vr-clab' + cls, `left:${bx + cw / 2}px;top:${base + 14}px`, esc(r.n));
        c.tl.fromTo(lab, { opacity: 0 }, { opacity: 1, duration: 0.25 }, ti);
      }
      if (r.hl || r.alerta || r.mostra) {
        const val = h(box, 'div', 'vr-cval' + cls, `left:${bx + cw / 2}px;top:${base - bh - (v916 ? 64 : 74)}px`);
        const st = { v: 0 };
        c.render(() => { val.innerHTML = `${fmt(st.v, s.dec)}${s.unid ? `<small>${esc(s.unid)}</small>` : ''}`; });
        c.tl.fromTo(val, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.25 }, ti + 0.15);
        c.tl.fromTo(st, { v: 0 }, { v, duration: 0.5, ease: 'power2.out' }, ti + 0.05);
        if (r.hl || r.alerta) c.tl.to(bar.firstChild || bar, { boxShadow: r.alerta ? '0 0 70px rgba(255,70,70,.95)' : '0 0 70px rgba(255,182,56,.95)', duration: 0.18, yoyo: true, repeat: 1 }, ti + 0.55);
      }
    });
    if (s.fonte) { const f = h(box, 'div', 'vr-rfonte', `left:${x}px;top:${H * (v916 ? 0.8 : 0.79)}px`, esc(s.fonte)); c.tl.fromTo(f, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t + 0.4); }
  };
  // linha (2.17) — gráfico de linha REAL que se desenha no tempo da fala. Cada série tem pontos [[x, v], ...] e vai de
  // "de" (já desenhado quando o shot entra: continuidade entre shots) até "ate", chegando lá na deixa "ate_at".
  // "marcos" = linha vertical com rótulo numa deixa (ex.: 1993). Valor acima de y[1] encosta no teto e mostra "teto_txt".
  P.linha = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), v916 = W < 1500, NS = 'http://www.w3.org/2000/svg';
    fundo(box, s, c, t);
    corte(box, c, t);
    const tw = TW(c), x = v916 ? 40 : 70, pw = tw - x * 2;
    const pnl = h(box, 'div', 'vr-rpanel', `left:${x - 30}px;top:${H * (v916 ? 0.17 : 0.13)}px;width:${pw + 60}px;height:${H * (v916 ? 0.66 : 0.7)}px`);
    c.tl.fromTo(pnl, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t);
    if (s.titulo) manchete(box, s.titulo, t + 0.05, c, 'top', `font-size:${v916 ? 50 : 62}px`);
    const L = x + (v916 ? 70 : 90), R = x + pw - (v916 ? 210 : 200), T = H * (v916 ? 0.25 : 0.31), B = H * (v916 ? 0.6 : 0.72);   // 9:16: acima do avatar (pip)
    const [x0, x1] = s.x || [0, 1], [y0, y1] = s.y || [0, 1];
    const px = (v) => L + (R - L) * (v - x0) / (x1 - x0), py = (v) => B - (B - T) * (Math.min(v, y1) - y0) / (y1 - y0);
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'vr-lsvg'); svg.setAttribute('width', W); svg.setAttribute('height', H);
    box.appendChild(svg);
    const el = (tag, at, par) => { const e = document.createElementNS(NS, tag); Object.entries(at).forEach(([k, v]) => e.setAttribute(k, v)); (par || svg).appendChild(e); return e; };
    const eixo = el('g', {});
    (s.yticks || [y0, y1]).forEach((v) => {
      el('line', { x1: L, x2: R, y1: py(v), y2: py(v), class: 'vr-lgrid' }, eixo);
      const tx = el('text', { x: L - 14, y: py(v) + 9, class: 'vr-ltick', 'text-anchor': 'end' }, eixo); tx.textContent = fmt(v, 0);
    });
    (s.xticks || [x0, x1]).forEach((v) => { const tx = el('text', { x: px(v), y: B + 40, class: 'vr-ltick', 'text-anchor': 'middle' }, eixo); tx.textContent = String(v); });
    c.tl.fromTo(eixo, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t + 0.1);
    (s.marcos || []).forEach((m) => {
      const g = el('g', {}), tm = def(m.at, t + 0.5);
      el('line', { x1: px(m.x), x2: px(m.x), y1: T - 10, y2: B, class: 'vr-lmarco' }, g);
      const esq = px(m.x) > R - 260;   // marco perto da borda direita: rótulo à esquerda da linha (a ponta da série fica à direita)
      const tx = el('text', { x: px(m.x) + (esq ? -14 : 12), y: T + 26, class: 'vr-lmtxt', 'text-anchor': esq ? 'end' : 'start' }, g); tx.textContent = m.txt || String(m.x);
      c.tl.fromTo(g, { opacity: 0 }, { opacity: 1, duration: 0.3 }, tm);
    });
    const tips = [];
    (s.series || []).forEach((se, i) => {
      const pts = (se.pts || []).slice().sort((a, b) => a[0] - b[0]);
      if (!pts.length) return;
      const de = def(se.de, pts[0][0]), ate = def(se.ate, pts[pts.length - 1][0]);
      const ta = def(se.at, t + 0.35), tb = Math.max(ta + 0.4, def(se.ate_at, ta + 2.5));
      const cls = se.cor === 'alerta' ? ' alerta' : (se.cor === 'hl' ? ' hl' : '');
      const path = el('path', { class: 'vr-lpath' + cls, d: '' });
      const dot = el('circle', { r: v916 ? 9 : 11, class: 'vr-ldot' + cls });
      const val = h(box, 'div', 'vr-lval' + cls, '');
      const st = { p: de };
      const ival = (p) => {   // valor interpolado na posição p
        for (let k = 1; k < pts.length; k++) if (p <= pts[k][0]) { const [a, va] = pts[k - 1], [b, vb] = pts[k]; return va + (vb - va) * (p - a) / (b - a || 1); }
        return pts[pts.length - 1][1];
      };
      const tip = { y: 0, val, se };
      tips.push(tip);
      c.render(() => {
        const p = st.p, d = [];
        pts.forEach(([a, v]) => { if (a <= p) d.push(`${px(a).toFixed(1)},${py(v).toFixed(1)}`); });
        const v = ival(p), X = px(p), Y = py(v);
        d.push(`${X.toFixed(1)},${Y.toFixed(1)}`);
        path.setAttribute('d', 'M' + d.join(' L'));
        dot.setAttribute('cx', X); dot.setAttribute('cy', Y);
        const txt = v > y1 && se.teto_txt ? esc(se.teto_txt) : `${fmt(v, s.dec)}${s.unid ? `<small>${esc(s.unid)}</small>` : ''}`;
        val.innerHTML = `${txt}${se.n ? `<i>${esc(se.n)}</i>` : ''}`;
        tip.x = X + 22; tip.y = Y;
        // rótulos das pontas não se encostam: empurra para baixo o que estiver a < 70 px de outro
        // e nunca descem até os anos do eixo: a pilha sobe inteira se passar do limite
        const ord = tips.filter((q) => q.x != null).sort((a, b) => a.y - b.y), lim = B - 100;
        ord.forEach((q, k) => { q.yy = k > 0 && q.y - ord[k - 1].yy < 76 ? ord[k - 1].yy + 76 : q.y; });
        const sobe = ord.length ? Math.max(0, ord[ord.length - 1].yy - lim) : 0;
        ord.forEach((q) => { q.val.style.left = q.x + 'px'; q.val.style.top = (q.yy - sobe - 34) + 'px'; });
      });
      c.tl.fromTo([path, dot, val], { opacity: 0 }, { opacity: 1, duration: 0.3 }, t + 0.2 + i * 0.1);
      c.tl.set(st, { p: de }, 0);
      if (Array.isArray(se.passos) && se.passos.length) {
        // "passos": [{x, at}] = a linha chega em x exatamente na deixa (anda no ritmo da fala, trecho a trecho)
        let t0 = ta;
        se.passos.forEach((pp) => {
          const t1 = Math.max(t0 + 0.3, def(pp.at, t0 + 1.5));
          c.tl.to(st, { p: pp.x, duration: t1 - t0, ease: 'none' }, t0);
          t0 = t1;
        });
      } else c.tl.to(st, { p: ate, duration: tb - ta, ease: se.ease || 'none' }, ta);
    });
    if (s.fonte) { const f = h(box, 'div', 'vr-rfonte', `left:${x}px;top:${H * (v916 ? 0.8 : 0.79)}px`, esc(s.fonte)); c.tl.fromTo(f, { opacity: 0 }, { opacity: 1, duration: 0.3 }, t + 0.4); }
  };

  // carimbo — bate por cima do shot anterior (use "keep": true)
  P.carimbo = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), cor = s.cor || 'var(--rose)';
    const k = h(box, 'div', 'vr-carimbo', `color:${cor};border-color:${cor};left:${s.x != null ? W * s.x : TW(c) / 2}px;top:${H * (s.y || 0.62)}px`, esc(s.txt || 'ALERTA'));   // "x" (0–1): 0,82 = acima do avatar, livre nos gráficos
    c.tl.fromTo(k, { opacity: 0, scale: 2.4, rotation: -8, xPercent: -50, yPercent: -50 }, { opacity: 1, scale: 1, rotation: -8, duration: 0.26, ease: 'power4.in' }, t);
    c.tl.fromTo(k, { x: 0 }, { x: 7, duration: 0.05, yoyo: true, repeat: 3, immediateRender: false }, t + 0.26);
  };

  // cinetica — frase em tipografia cinética; cada palavra pode ter a sua deixa ("palavras":[{t,at}])
  P.cinetica = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W] = WH(c);
    fundo(box, s, c, t);
    corte(box, c, t);
    const el = h(box, 'div', 'vr-kin', `font-size:${s.size || (W < 1500 ? 120 : 150)}px`);
    (s.palavras || []).forEach((p, i) => {
      const sp = h(el, 'span', p.hl ? 'hl' : (p.bad ? 'bad' : ''), '', esc(p.t));
      const ti = def(p.at, t + i * 0.18);
      c.tl.fromTo(sp, { opacity: 0, scale: 2.2, filter: 'blur(10px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.28, ease: 'power4.out' }, ti);
      if (p.risca_at != null) c.tl.fromTo(sp, { '--risco': '0%' }, { '--risco': '100%', duration: 0.25, ease: 'power2.out', immediateRender: true }, p.risca_at);
    });
  };

  // rosto — o avatar toma a tela (o index cresce o avatar nesses trechos); a cena só escurece o palco
  P.rosto = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05);
    const [W, H] = WH(c);
    fundo(box, s, c, t);
  };

  // mapa — contornos reais (mapa_geo.py no build), câmera que voa/aproxima nas deixas, regiões que acendem e
  // pinos com haste e rótulo (molde eventosextremospub). Fundo = foto da cena desfocada (nunca oceano liso).
  P.mapa = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c), G = s.geo || { feats: [], cam: [], pinos: [] };
    fundo(box, Object.assign({}, s, { src: null }), c, t);
    const tint = h(box, 'div', 'vr-mapa-tint', `width:${W}px;height:${H}px`);
    const NS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', W); svg.setAttribute('height', H); svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.setAttribute('class', 'vr-mapa');
    box.appendChild(svg);
    const g = document.createElementNS(NS, 'g'); svg.appendChild(g);
    const hl = {};
    G.feats.forEach((f) => {
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', f.d); p.setAttribute('class', 'vr-terra' + (f.hl ? ' hl' : ''));
      g.appendChild(p);
      if (f.hl) hl[f.n] = p;
    });
    if (G.cond) {
      const cp = document.createElementNS(NS, 'path');
      cp.setAttribute('d', G.cond); cp.setAttribute('class', 'vr-cond'); g.appendChild(cp);
      c.tl.fromTo(cp, { opacity: 0 }, { opacity: 1, duration: 0.6 }, def((s.destaques || [])[0] && s.destaques[0].at, t + 0.3) + 0.4);
    }
    const cams = G.cam.length ? G.cam : [{ at: t, xy: [W / 2, H / 2], z: 1 }];
    const cam = { x: cams[0].xy[0], y: cams[0].xy[1], z: cams[0].z };
    c.tl.fromTo(svg, { opacity: 0, scale: 1.08 }, { opacity: 1, scale: 1, duration: 0.5, ease: 'expo.out' }, t);
    cams.forEach((k, i) => {
      if (i === 0) return;
      c.tl.to(cam, { x: k.xy[0], y: k.xy[1], z: k.z, duration: 1.1, ease: 'expo.inOut' }, k.at);
    });
    const last = cams[cams.length - 1];
    c.tl.to(cam, { z: last.z * 1.06, duration: Math.max(0.5, c.T1 - last.at - 1.1), ease: 'none' }, Math.max(t, last.at) + 1.1);
    (s.destaques || []).forEach((d) => {
      const p = hl[d.nome]; if (!p) return;
      c.tl.fromTo(p, { fillOpacity: 0.15 }, { fillOpacity: 0.62, duration: 0.45, ease: 'power2.out' }, def(d.at, t + 0.3));
    });
    const pins = G.pinos.map((p) => {
      const el = h(box, 'div', 'vr-pino', '', `<i class="ring"></i><i class="dot"></i><b class="stem"></b><div class="lab">${esc(p.txt || '')}${p.sub ? `<small>${rich(p.sub)}</small>` : ''}</div>`);
      const ta = def(p.at, t + 0.6);
      c.tl.fromTo(el.querySelector('.dot'), { scale: 0 }, { scale: 1, duration: 0.3, ease: 'back.out(3)' }, ta);
      c.tl.fromTo(el.querySelector('.ring'), { scale: 0.2, opacity: 1 }, { scale: 3.5, opacity: 0, duration: 1.1, ease: 'power2.out', repeat: Math.max(0, Math.floor((c.T1 - ta) / 1.2)), immediateRender: false }, ta);
      c.tl.fromTo(el.querySelector('.stem'), { scaleY: 0 }, { scaleY: 1, duration: 0.35, ease: 'expo.out' }, ta + 0.1);
      c.tl.fromTo(el.querySelector('.lab'), { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.35, ease: 'back.out(2)' }, ta + 0.3);
      if (p.sub) c.tl.fromTo(el.querySelector('small'), { opacity: 0 }, { opacity: 1, duration: 0.3 }, def(p.sub_at, ta + 0.8));
      c.tl.set(el, { opacity: 1 }, ta);
      return { el, xy: p.xy };
    });
    c.render(() => {
      g.setAttribute('transform', `translate(${W / 2} ${H / 2}) scale(${cam.z}) translate(${-cam.x} ${-cam.y})`);
      g.style.setProperty('--sw', (1.2 / cam.z).toFixed(3));
      pins.forEach((p) => { p.el.style.left = ((p.xy[0] - cam.x) * cam.z + W / 2) + 'px'; p.el.style.top = ((p.xy[1] - cam.y) * cam.z + H / 2) + 'px'; });
    });
    void tint;
  };

  // cta — cartão final: print do site inclinado + url pulsando
  P.cta = function (box, s, c) {
    const t = def(s.at, c.T0 + 0.05), [W, H] = WH(c);
    fundo(box, Object.assign({}, s, { src: null }), c, t);
    corte(box, c, t);
    const wide = W >= 1500, pw = wide ? 1000 : W * 0.84, sx = wide ? 70 : (W - pw) / 2, sy = wide ? 170 : 160;
    const sh = h(box, 'div', 'vr-shot', `left:${sx}px;top:${sy}px;width:${pw}px;height:${pw * 0.5625}px;background-image:url("${s.src}")`);
    c.tl.fromTo(sh, { opacity: 0, rotationY: -28, rotationX: 12, y: 80 }, { opacity: 1, rotationY: -10, rotationX: 6, y: 0, duration: 0.7, ease: 'expo.out' }, t);
    c.tl.to(sh, { rotationY: 6, rotationX: 2, duration: Math.max(1, c.T1 - t - 0.7), ease: 'none' }, t + 0.7);
    const url = wide ? h(box, 'div', 'vr-url side', `left:1120px;top:230px`, rich(s.url || '**inema.club**'))
      : h(box, 'div', 'vr-url', `top:${sy + pw * 0.5625 + 50}px`, rich(s.url || '**inema.club**'));
    c.tl.fromTo(url, { opacity: 0, scale: 0.6 }, { opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(2)' }, def(s.url_at, t + 0.4));
    c.tl.to(url, { scale: 1.06, duration: 0.5, yoyo: true, repeat: 5, ease: 'sine.inOut' }, def(s.url_at, t + 0.4) + 0.5);
    if (s.sub) { const sb = wide ? h(box, 'div', 'vr-usub side', `left:1120px;top:370px`, rich(s.sub)) : h(box, 'div', 'vr-usub', `top:${sy + pw * 0.5625 + 170}px`, rich(s.sub)); c.tl.fromTo(sb, { opacity: 0 }, { opacity: 1, duration: 0.4 }, def(s.sub_at, t + 0.7)); }
  };
})();
