// Confere e baixa um vídeo de avatar SÓ pelo estúdio do HeyGen — sem chave de API.
//
//   DISPLAY=:99 node engine/heygen-estudio-baixar.mjs --id <id32> --saida <arq.mp4> \
//     --perfil <dir> [--minutos 120] [--intervalo 120]
//
// Só leitura no estúdio: abre /videos/<id>, recarrega até o player aparecer e baixa
// o MP4 que o próprio player usa (URL assinada do CDN), pelo contexto logado.
// Não clica em Gerar/Enviar/Editar. Se a página mostrar Draft, para (nada foi
// enviado — não é caso de esperar).
// Sai 0 com `RESULT: <arquivo>`; 3 com `ERRO: <motivo>`; 4 se estourou o tempo.
import { renameSync, writeFileSync } from 'node:fs';
import { chromium } from '/home/nmaldaner/projetos/inemaccbot/node_modules/playwright/index.mjs';

const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d; };
const ID = arg('id'), SAIDA = arg('saida'), PERFIL = arg('perfil');
const MINUTOS = Number(arg('minutos', '120')), INTERVALO = Number(arg('intervalo', '120'));
if (!/^[a-f0-9]{32}$/.test(ID ?? '') || !SAIDA || !PERFIL) { console.error('ERRO: uso: --id <id32> --saida <arq.mp4> --perfil <dir>'); process.exit(3); }
const passo = (m) => console.log(`${new Date().toISOString().slice(11, 19)} ${m}`);

const ctx = await chromium.launchPersistentContext(PERFIL, {
  headless: !process.env.DISPLAY,
  args: ['--password-store=basic', '--no-first-run', '--no-default-browser-check'],
  viewport: { width: 1440, height: 900 },
});
const sair = async (cod, m) => { await ctx.close().catch(() => {}); console[cod ? 'error' : 'log'](m); process.exit(cod); };
const pg = ctx.pages()[0] ?? await ctx.newPage();
for (const extra of ctx.pages().slice(1)) await extra.close();

const fim = Date.now() + MINUTOS * 60_000;
try {
  while (Date.now() < fim) {
    await pg.goto(`https://app.heygen.com/videos/${ID}`, { waitUntil: 'domcontentloaded', timeout: 90_000 });
    await pg.waitForTimeout(12_000);
    // A página se recarrega sozinha quando o vídeo fica pronto: se a leitura cair no meio, lê de novo.
    let v = null;
    for (let i = 0; i < 3 && !v; i++) {
      v = await pg.evaluate(() => ({
        texto: document.body.innerText.replace(/\s+/g, ' ').slice(0, 600),
        src: [...document.querySelectorAll('video, video source')].map((e) => e.currentSrc || e.src).find((s) => /^https:.*\.mp4/i.test(s ?? '')) ?? null,
      })).catch(async () => { await pg.waitForTimeout(8_000); return null; });
    }
    if (!v) { passo('página recarregando — tento no próximo ciclo'); await pg.waitForTimeout(30_000); continue; }
    if (/doesn't exist or has been moved|não existe/i.test(v.texto) && !v.src) await sair(3, 'ERRO: o estúdio diz que este ID de vídeo não existe — conferir o título em Projetos');
    if (/\bdraft\b|rascunho/i.test(v.texto) && !v.src) await sair(3, `ERRO: vídeo está em Draft — o envio não pegou (${v.texto.slice(0, 160)})`);
    if (/failed|falhou|error generating/i.test(v.texto) && !v.src) await sair(3, `ERRO: estúdio mostra falha (${v.texto.slice(0, 160)})`);
    if (v.src) {
      passo('pronto no estúdio — baixando');
      const r = await ctx.request.get(v.src, { timeout: 600_000 });
      if (!r.ok()) await sair(3, `ERRO: download HTTP ${r.status()}`);
      const corpo = await r.body();
      if (corpo.length < 1_000_000) await sair(3, `ERRO: arquivo pequeno demais (${corpo.length} bytes)`);
      const temp = SAIDA.replace(/\.mp4$/, '.part.mp4');
      writeFileSync(temp, corpo); renameSync(temp, SAIDA);
      await sair(0, `RESULT: ${SAIDA}`);
    }
    passo(`ainda gerando: ${(v.texto.match(/\d{1,3}%/) ?? ['?'])[0]}`);
    await pg.waitForTimeout(INTERVALO * 1000);
  }
  await sair(4, 'ERRO: tempo esgotado esperando o estúdio');
} catch (e) {
  await sair(3, `ERRO: ${(e?.message ?? String(e)).split('\n')[0].slice(0, 200)}`);
}
