/* Explicavideos v2 — perfil "interface" (2.15): motion design de interface, o estilo dos explicativos de
   diagramas animados (fundo escuro chapado, um acento só, peças que se montam no tempo da fala).
   Peças novas (também valem fora do perfil; o build carrega este arquivo quando alguma é usada):
     tokens — texto que se parte em pedaços coloridos (como o modelo lê)
     probs  — barras de probabilidade do próximo pedaço; o escolhido entra no texto
     arcos  — atenção: arcos de uma palavra para as outras, com peso
     etapas — lista-mapa do vídeo com a etapa atual acesa (volta a cada "Etapa N")
   Todo tempo chega resolvido do build (segundos relativos à cena). Texto em fonte mono: 0,602 em por caractere. */
(function () {
  const V2 = window.V2, { h, esc, rich } = V2.util;
  const def = (v, d) => (v == null || Number.isNaN(v) ? d : v);
  const plain = (s) => String(s == null ? '' : s).replace(/\*\*|\+\+|~~/g, '');
  const MW = 0.602;                       // largura do caractere da fonte Mono (DejaVu Sans Mono)
  const X0 = 90, AW = 1330, Y0 = 175, AH = 740;   // área útil (o avatar fica à direita)
  const TONES = ['#FACC15', '#7dd3fc', '#f0abfc', '#86efac', '#fdba74', '#c4b5fd', '#fca5a5', '#e5e7eb'];
  const norm = (s) => plain(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^\w]/g, '');

  // -------------------------------------------------------------------------------------------------
  // tokens — linhas[{texto?, pedacos[], ids?[], rotulo?, at, corta_at?, ids_at?}] (1–3) ou os mesmos campos soltos
  //          nota?{texto, at}. O texto entra inteiro (digitado), no corta_at se separa em pedaços coloridos,
  //          no ids_at cada pedaço ganha o número que o modelo realmente recebe e a contagem "N tokens".
  V2.P.tokens = function (box, s, c) {
    const L = s.linhas || [{ texto: s.texto, pedacos: s.pedacos, ids: s.ids, rotulo: s.rotulo, at: s.at, corta_at: s.corta_at, ids_at: s.ids_at }];
    const n = L.length, rowH = AH / n, FS0 = [92, 72, 58][n - 1] || 58;
    L.forEach((ln, r) => {
      const P = (ln.pedacos && ln.pedacos.length ? ln.pedacos : [ln.texto || '']).map(String);
      const t0 = def(ln.at, c.T0 + 0.2 + r * 0.8), tc = def(ln.corta_at, t0 + 1.4), ti = ln.ids_at;
      const chars = P.reduce((a, p) => a + p.length, 0), pad = 0.32, gap = 0.36;   // em "em"
      // tamanho da letra para caber separado (pedaços + folgas) na largura útil
      const need = chars * MW + P.length * 2 * pad + (P.length - 1) * gap;
      const FS = Math.min(FS0, Math.floor((AW - 40) / need));
      const cy = Y0 + rowH * (r + 0.5) - (ti != null ? 22 : 0), chipH = Math.round(FS * 1.5);
      const wJoin = chars * MW * FS, wSplit = need * FS;
      let xj = X0 + (AW - wJoin) / 2, xs = X0 + (AW - wSplit) / 2;
      if (ln.rotulo) {
        const lb = h(box, 'div', 'tk-rot', `left:${xs}px;top:${cy - chipH / 2 - 52}px`, rich(ln.rotulo));
        c.rise(lb, t0, 10);
      }
      P.forEach((p, k) => {
        const w = p.length * MW * FS, col = TONES[k % TONES.length];
        const el = h(box, 'div', 'tk-chip', `left:${xs}px;top:${cy - chipH / 2}px;height:${chipH}px;line-height:${chipH}px;font-size:${FS}px;padding:0 ${pad * FS}px;--c:${col}`, esc(p));
        // posição colada (texto inteiro) → posição separada (pedaços); o x é relativo à posição separada
        const dx = (xj - pad * FS) - xs;
        c.tl.fromTo(el, { opacity: 0, x: dx }, { opacity: 1, x: dx, duration: 0.12 }, t0 + (k / P.length) * 0.5);
        c.tl.to(el, { x: 0, duration: 0.55, ease: 'back.out(1.6)' }, tc + k * 0.04);
        c.tl.to(el, { backgroundColor: col + '33', borderColor: col, color: '#ffffff', duration: 0.35 }, tc + k * 0.04);
        if (ti != null) {
          const id = ln.ids && ln.ids[k] != null ? String(ln.ids[k]) : String(k + 1);
          const ie = h(box, 'div', 'tk-id', `left:${xs}px;top:${cy + chipH / 2 + 12}px;width:${w + 2 * pad * FS}px;color:${col}`, esc(id));
          c.tl.fromTo(ie, { opacity: 0, y: -10 }, { opacity: 1, y: 0, duration: 0.3 }, ti + k * 0.08);
        }
        xj += w; xs += w + 2 * pad * FS + gap * FS;
      });
      const cnt = h(box, 'div', 'tk-cnt', `left:${X0}px;width:${AW}px;top:${cy + chipH / 2 + (ti != null ? 62 : 18)}px`,
        `<b>${P.length}</b> ${P.length === 1 ? 'token' : 'tokens'}`);
      c.tl.fromTo(cnt, { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.35 }, (ti != null ? ti : tc) + 0.5);
    });
    if (s.nota) { const nt = h(box, 'div', 'if-nota', `left:${X0}px;width:${AW}px;top:${Y0 + AH - 40}px`, rich(s.nota.texto)); c.rise(nt, def(s.nota.at, c.T1 - 2), 16); }
  };

  // -------------------------------------------------------------------------------------------------
  // probs — contexto, opcoes[{texto, p (0–1), tom?:"certo"|"erro"}] (2–5), at, barras_at?, escolhe_at?, escolhe?(índice),
  //         nota?{texto, at}. As barras crescem com o número contando; no escolhe_at o pedaço escolhido sobe e
  //         entra no fim do texto (o modelo escreve um pedaço por vez).
  V2.P.probs = function (box, s, c) {
    const O = s.opcoes || [], t0 = def(s.at, c.T0 + 0.2), tb = def(s.barras_at, t0 + 1), te = s.escolhe_at;
    const win = def(s.escolhe, O.reduce((b, o, i) => ((o.p || 0) > (O[b].p || 0) ? i : b), 0));
    const CF = 50, ctx = plain(s.contexto);
    const cx0 = X0 + 40, cyc = Y0 + 26;
    const cb = h(box, 'div', 'pb-ctx', `left:${X0}px;top:${Y0}px;width:${AW}px;height:120px`);
    const tx = h(cb, 'div', 'pb-tx', `font-size:${CF}px`, esc(ctx));
    const cur = h(cb, 'div', 'pb-cur', `left:${40 + ctx.length * MW * CF + 8}px`);
    c.rise(cb, t0, 20);
    c.tl.fromTo(cur, { opacity: 1 }, { opacity: 0, duration: 0.45, repeat: Math.max(0, Math.floor((c.T1 - t0) / 0.9) * 2 - 1), yoyo: true, ease: 'steps(1)' }, t0);
    const rows = O.length, rh = Math.min(150, (AH - 260) / Math.max(1, rows)), top = Y0 + 200 + Math.max(0, (AH - 260 - rows * rh) / 2);
    const LW = Math.max(...O.map((o) => plain(o.texto).length), 4) * MW * 56 + 30, bx = X0 + 40 + LW, bw = AW - 40 - LW - 170;
    const row = [];
    O.forEach((o, i) => {
      const y = top + i * rh, p = Math.max(0, Math.min(1, Number(o.p) || 0)), st = { v: 0 };
      const lb = h(box, 'div', 'pb-lb', `left:${X0 + 40}px;top:${y}px;height:${rh - 22}px;line-height:${rh - 22}px`, esc(o.texto));
      const tr = h(box, 'div', 'pb-tr', `left:${bx}px;top:${y + (rh - 22) / 2 - 22}px;width:${bw}px`);
      const fl = h(tr, 'i', '', i === win ? 'background:var(--amber)' : '');
      const pc = h(box, 'div', 'pb-pc', `left:${bx + bw + 24}px;top:${y}px;height:${rh - 22}px;line-height:${rh - 22}px`);
      c.render(() => { pc.textContent = Math.round(st.v * 100) + '%'; });
      c.rise(lb, tb + i * 0.15, 14);
      c.tl.fromTo(tr, { opacity: 0 }, { opacity: 1, duration: 0.2 }, tb + i * 0.15);
      c.tl.fromTo(fl, { width: '0%' }, { width: (p * 100).toFixed(1) + '%', duration: 0.9, ease: 'power2.out' }, tb + i * 0.15 + 0.1);
      c.tl.fromTo(st, { v: 0 }, { v: p, duration: 0.9, ease: 'power2.out' }, tb + i * 0.15 + 0.1);
      c.tl.fromTo(pc, { opacity: 0 }, { opacity: 1, duration: 0.2 }, tb + i * 0.15 + 0.1);
      row.push({ lb, tr, pc, y, o });
    });
    if (te != null && row[win]) {
      const w = row[win];
      row.forEach((r, i) => { if (i !== win) c.tl.to([r.lb, r.tr, r.pc], { opacity: 0.3, duration: 0.3 }, te); });
      c.tl.to(w.lb, { color: '#FACC15', duration: 0.25 }, te);
      // o pedaço escolhido viaja da barra até o fim do texto
      const word = ' ' + plain(w.o.texto), ex = cx0 + ctx.length * MW * CF, ey = cyc + 4;
      const fly = h(box, 'div', 'pb-fly', `left:${ex}px;top:${ey}px;font-size:${CF}px`, esc(word));
      c.tl.fromTo(fly, { opacity: 0, x: X0 + 40 - ex, y: w.y + 10 - ey, scale: 0.92 }, { opacity: 1, duration: 0.2 }, te + 0.15);
      c.tl.to(fly, { x: 0, y: 0, scale: 1, duration: 0.7, ease: 'power3.inOut' }, te + 0.3);
      c.tl.to(cur, { left: 40 + (ctx.length + word.length) * MW * CF + 8, duration: 0.01 }, te + 1);
      const tom = w.o.tom;
      if (tom) c.tl.to(fly, { color: tom === 'erro' ? '#ff5d7a' : '#3ef0a0', duration: 0.3 }, te + 1.1);
    }
    O.forEach((o, i) => {
      if (!o.tom || i === win) return;
      const tag = h(box, 'div', 'pb-tag ' + o.tom, `left:${X0 + 40}px;top:${row[i].y + rh - 30}px`, o.tom === 'erro' ? 'errado' : 'certo');
      c.rise(tag, def(s.tons_at, (te != null ? te : tb) + 1.2), 8);
    });
    if (s.nota) { const nt = h(box, 'div', 'if-nota', `left:${X0}px;width:${AW}px;top:${Y0 + AH - 40}px`, rich(s.nota.texto)); c.rise(nt, def(s.nota.at, c.T1 - 2), 16); }
  };

  // -------------------------------------------------------------------------------------------------
  // arcos — atenção. frase (palavras separadas por espaço), passos[{at, foco (palavra ou índice), arcos[{para, peso 0–1}],
  //         frase? (troca a frase), nota?}]. A palavra em foco acende; de cada arco sai uma curva até a outra palavra,
  //         grossa e clara conforme o peso; a nota diz o sentido que a palavra ganhou.
  V2.P.arcos = function (box, s, c) {
    const NS = 'http://www.w3.org/2000/svg', FS = 54, base = Y0 + 470;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', 1920); svg.setAttribute('height', 1080); svg.style.cssText = 'position:absolute;left:0;top:0';
    box.appendChild(svg);
    const t0 = def(s.at, c.T0 + 0.2);
    let words = null, nota = null, curArcs = [];
    const lay = (frase, t) => {
      const W = String(frase).trim().split(/\s+/), gap = 0.9;
      const fs = Math.min(FS, Math.floor((AW - 60) / ((W.join('').length + (W.length - 1) * gap) * MW)));
      let x = X0 + (AW - (W.join('').length + (W.length - 1) * gap) * MW * fs) / 2;
      const out = W.map((w) => {
        const ww = w.length * MW * fs;
        const el = h(box, 'div', 'ar-w', `left:${x}px;top:${base}px;font-size:${fs}px`, esc(w));
        const o = { el, w, cx: x + ww / 2, top: base - 6 };
        x += ww + gap * MW * fs;
        return o;
      });
      out.forEach((o, i) => c.tl.fromTo(o.el, { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power3.out' }, t + i * 0.05));
      return out;
    };
    const find = (ref) => typeof ref === 'number' ? words[ref] : words.find((o) => norm(o.w) === norm(ref)) || words.find((o) => norm(o.w).startsWith(norm(ref)));
    words = lay(s.frase || '', t0);
    let lastFocus = null;
    (s.passos || []).forEach((ps, k) => {
      const t = def(ps.at, t0 + 1.5 + k * 2);
      curArcs.forEach((a) => c.tl.to(a, { opacity: 0, duration: 0.25 }, t));
      curArcs = [];
      if (ps.frase) {
        words.forEach((o) => c.tl.to(o.el, { opacity: 0, y: -14, duration: 0.25 }, t));
        words = lay(ps.frase, t + 0.25); lastFocus = null;
      }
      const ta = t + (ps.frase ? 0.6 : 0);
      const f = ps.foco != null ? find(ps.foco) : null;
      if (lastFocus && lastFocus !== f) c.tl.to(lastFocus.el, { color: '#e5e7eb', backgroundColor: 'rgba(250,204,21,0)', duration: 0.25 }, ta);
      if (f) {
        c.tl.to(f.el, { color: '#0c0c10', backgroundColor: 'rgba(250,204,21,1)', duration: 0.3 }, ta);
        lastFocus = f;
        (ps.arcos || []).forEach((a, j) => {
          const g = find(a.para); if (!g || g === f) return;
          const p = Math.max(0.05, Math.min(1, Number(a.peso) || 0.5));
          const d = Math.abs(g.cx - f.cx), hgt = Math.min(330, 70 + d * 0.42);
          const path = document.createElementNS(NS, 'path');
          path.setAttribute('d', `M${f.cx} ${f.top} C${f.cx} ${f.top - hgt} ${g.cx} ${g.top - hgt} ${g.cx} ${g.top}`);
          path.setAttribute('fill', 'none'); path.setAttribute('stroke', '#FACC15'); path.setAttribute('stroke-linecap', 'round');
          path.setAttribute('stroke-width', (2 + 12 * p).toFixed(1)); path.setAttribute('opacity', (0.25 + 0.75 * p).toFixed(2));
          svg.appendChild(path);
          const L = path.getTotalLength ? path.getTotalLength() : 600;
          path.style.strokeDasharray = L;
          c.tl.fromTo(path, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: 0.6, ease: 'power2.out' }, ta + 0.25 + j * 0.12);
          curArcs.push(path);
          // a palavra olhada acende na medida do peso
          c.tl.to(g.el, { color: p > 0.6 ? '#FACC15' : '#e5e7eb', duration: 0.3 }, ta + 0.5 + j * 0.12);
          c.tl.to(g.el, { color: '#e5e7eb', duration: 0.25 }, def((s.passos[k + 1] || {}).at, c.T1 + 1));
        });
      }
      if (nota) { c.tl.to(nota, { opacity: 0, duration: 0.25 }, ta); nota = null; }
      if (ps.nota) {
        nota = h(box, 'div', 'if-nota', `left:${X0}px;width:${AW}px;top:${base + 120}px`, rich(ps.nota));
        c.rise(nota, ta + 0.8, 14);
      }
    });
  };

  // -------------------------------------------------------------------------------------------------
  // etapas — itens[] (≤7, o mapa do vídeo), atual (1..n), at, titulo?, sub? (o que é esta etapa), sub_at?
  //          A lista monta rápido; as anteriores ficam com ✓, a marca desliza da anterior para a atual.
  V2.P.etapas = function (box, s, c) {
    const I = s.itens || [], n = I.length, cur = Math.max(1, Math.min(n, s.atual || 1)) - 1, t0 = def(s.at, c.T0 + 0.1);
    const top = Y0 + (s.titulo ? 70 : 20), rh = Math.min(92, (AH - (s.titulo ? 90 : 40)) / Math.max(1, n)), LW = 700;
    if (s.titulo) { const tt = h(box, 'div', 'et-tt', `left:${X0 + 40}px;top:${Y0}px`, rich(s.titulo)); c.rise(tt, t0, 10); }
    const mk = h(box, 'div', 'et-mk', `left:${X0 + 20}px;top:${top + Math.max(0, cur - 1) * rh}px;width:${LW}px;height:${rh - 12}px`);
    I.forEach((it, i) => {
      const y = top + i * rh, done = i < cur, now = i === cur;
      const row = h(box, 'div', 'et-row' + (done ? ' done' : '') + (now ? ' now' : ''), `left:${X0 + 40}px;top:${y}px;width:${LW - 40}px;height:${rh - 12}px;line-height:${rh - 12}px`,
        `<span class="nb">${done ? '✓' : i + 1}</span><span class="tx">${esc(it)}</span>`);
      c.tl.fromTo(row, { opacity: 0, x: -24 }, { opacity: done ? 0.55 : now ? 1 : 0.32, x: 0, duration: 0.3, ease: 'power3.out' }, t0 + i * 0.06);
    });
    const tm = t0 + n * 0.06 + 0.25;
    c.tl.fromTo(mk, { opacity: 0 }, { opacity: 1, duration: 0.2 }, tm);
    c.tl.to(mk, { top: top + cur * rh, duration: 0.6, ease: 'power3.inOut' }, tm + 0.1);
    const big = h(box, 'div', 'et-big', `left:${X0 + LW + 60}px;top:${top + Math.max(0, cur * rh - 40)}px;width:${AW - LW - 80}px`,
      `<div class="k">ETAPA ${cur + 1} DE ${n}</div><div class="t">${esc(I[cur] || '')}</div>` + (s.sub ? `<div class="s">${rich(s.sub)}</div>` : ''));
    c.tl.fromTo(big, { opacity: 0, x: 30 }, { opacity: 1, x: 0, duration: 0.45, ease: 'power3.out' }, tm + 0.5);
    if (s.sub) { const sb = big.querySelector('.s'); c.tl.fromTo(sb, { opacity: 0, y: 10 }, { opacity: 1, y: 0, duration: 0.35 }, def(s.sub_at, tm + 1)); }
  };
})();
