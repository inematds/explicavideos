// Porteiro do perfil do HeyGen (estúdio). TODO projeto que usa o estúdio passa por
// heygen-studio.mjs ou heygen-estudio-baixar.mjs, e os dois abrem o perfil por aqui.
//
// O perfil é um só e o Chrome só deixa um processo abrir (SingletonLock). Antes, quem
// chegava com o perfil aberto morria com "ProcessSingleton" (saudeviral, 10/10/2026).
// Agora: espera o dono do perfil sair (PID do SingletonLock vivo) e entra; se perder a
// corrida no lançamento, espera e tenta de novo. Cada entrada/saída vai para
// ~/.cache/inemaccbot/heygen-uso.log (ver quem está usando: engine/heygen-fila.sh).
//
// Trava do estúdio (19/10/2026): olhar o SingletonLock e depois abrir não é atômico. Dois
// envios no mesmo segundo viam "livre" e o segundo morria com "Opening in existing browser
// session" (r7ex, 01:32). Agora quem abre o estúdio pega antes a trava
// ~/.cache/inemaccbot/heygen-estudio.trava (mkdir é atômico; arquivo `dono` = pid + quem).
// Trava de pid morto é tomada. Ela é da FERRAMENTA, não de um projeto: as cópias deste
// arquivo (explicavideos/engine, r7ex/heygen) usam o mesmo caminho.
import { appendFileSync, mkdirSync, readlinkSync, lstatSync, readdirSync, existsSync, readFileSync, writeFileSync, rmSync, statSync } from 'node:fs';
import { homedir } from 'node:os';
import path from 'node:path';

const LOG = path.join(homedir(), '.cache/inemaccbot/heygen-uso.log');
const TRAVA = process.env.HEYGEN_TRAVA || path.join(homedir(), '.cache/inemaccbot/heygen-estudio.trava');   // HEYGEN_TRAVA só para teste
const espera = (ms) => new Promise((r) => setTimeout(r, ms));
const agora = () => { const d = new Date(); return new Date(d - d.getTimezoneOffset() * 60_000).toISOString().replace('T', ' ').slice(0, 19); };

export function registrar(msg) {
  try { mkdirSync(path.dirname(LOG), { recursive: true }); appendFileSync(LOG, `${agora()} pid=${process.pid} ${msg}\n`); } catch {}
}

// PID vivo que segura o perfil, ou null
export function donoDoPerfil(perfil) {
  const lock = path.join(perfil, 'SingletonLock');
  try { lstatSync(lock); } catch { return null; }
  let pid = null;
  try { pid = Number(readlinkSync(lock).split('-').pop()); } catch { return null; }
  if (!pid) return null;
  try { process.kill(pid, 0); return pid; } catch { return null; }
}

// pid vivo dono da trava do estúdio, ou null (trava velha é apagada)
export function donoDaTrava() {
  let st; try { st = statSync(TRAVA); } catch { return null; }
  let pid = 0; try { pid = Number(readFileSync(path.join(TRAVA, 'dono'), 'utf8').split(' ')[0]); } catch {}
  if (pid) { try { process.kill(pid, 0); return pid; } catch {} }
  else if (Date.now() - st.mtimeMs < 60_000) return -1;            // acabou de ser criada, dono ainda escrevendo
  try { rmSync(TRAVA, { recursive: true, force: true }); registrar(`TRAVA velha removida (pid ${pid || '?'})`); } catch {}
  return null;
}

let tenhoTrava = false;
function soltarTrava() {
  if (!tenhoTrava) return;
  tenhoTrava = false;
  try { if (Number(readFileSync(path.join(TRAVA, 'dono'), 'utf8').split(' ')[0]) === process.pid) rmSync(TRAVA, { recursive: true, force: true }); } catch {}
}
process.on('exit', soltarTrava);
for (const s of ['SIGTERM', 'SIGINT', 'SIGHUP']) process.on(s, () => { soltarTrava(); process.exit(128 + ({ SIGHUP: 1, SIGINT: 2, SIGTERM: 15 })[s]); });

async function pegarTrava(ateMs, quem) {
  let avisou = 0;
  mkdirSync(path.dirname(TRAVA), { recursive: true });
  for (;;) {
    try {
      mkdirSync(TRAVA);
      writeFileSync(path.join(TRAVA, 'dono'), `${process.pid} ${quem} ${agora()}\n`);
      tenhoTrava = true;
      return;
    } catch (e) { if (e.code !== 'EEXIST') throw e; }
    const dono = donoDaTrava();
    if (dono === null) continue;
    if (Date.now() > ateMs) throw new Error(`ERRO: estúdio do HeyGen ocupado (trava do pid ${dono}) além do tempo de espera`);
    if (Date.now() - avisou > 300_000) { console.log(`${agora().slice(11)} estúdio do HeyGen em uso pelo pid ${dono}; na fila (${quem})`); avisou = Date.now(); }
    await espera(10_000 + Math.random() * 5_000);
  }
}

export async function esperarLivre(perfil, ateMs, quem) {
  let avisou = 0;
  for (;;) {
    const dono = donoDoPerfil(perfil);
    if (!dono) return;
    if (Date.now() > ateMs) throw new Error(`ERRO: perfil do HeyGen ocupado (pid ${dono}) além do tempo de espera`);
    if (Date.now() - avisou > 300_000) { console.log(`${agora().slice(11)} perfil do HeyGen em uso pelo pid ${dono}; na fila (${quem})`); avisou = Date.now(); }
    await espera(15_000 + Math.random() * 10_000);
  }
}

// Abre o perfil com fila. `quem` = rótulo para o log (script + título/id).
// Espera até HEYGEN_ESPERA_MIN minutos (padrão 180).
// O perfil é compartilhado com o r7ex (Playwright mais novo). Depois que um Chrome novo abre
// o perfil, o Chrome antigo cai com SIGTRAP (18/10/2026). Por isso: sempre o Chrome mais novo
// instalado (ou HEYGEN_CHROME), nunca o que vem com o Playwright local.
function chromeMaisNovo() {
  if (process.env.HEYGEN_CHROME) return process.env.HEYGEN_CHROME;
  const base = path.join(homedir(), '.cache/ms-playwright');
  try {
    const vs = readdirSync(base).filter((d) => /^chromium-\d+$/.test(d)).sort((a, b) => Number(b.split('-')[1]) - Number(a.split('-')[1]));
    for (const v of vs) for (const sub of ['chrome-linux-arm64', 'chrome-linux']) {
      const exe = path.join(base, v, sub, 'chrome'); if (existsSync(exe)) return exe;
    }
  } catch {}
  return undefined;
}

export async function abrirPerfil(chromium, perfil, opcoes, quem) {
  const ate = Date.now() + Number(process.env.HEYGEN_ESPERA_MIN || 180) * 60_000;
  const exe = chromeMaisNovo(); if (exe && !opcoes.executablePath) opcoes = { ...opcoes, executablePath: exe };
  await pegarTrava(ate, quem);
  for (;;) {
    await esperarLivre(perfil, ate, quem);   // ainda vale: login à mão ou script antigo sem a trava
    try {
      const ctx = await chromium.launchPersistentContext(perfil, opcoes);
      registrar(`ENTRA ${quem} (cwd ${process.cwd()})`);
      const fechar = ctx.close.bind(ctx);
      ctx.close = async () => { await fechar().catch(() => {}); registrar(`SAI ${quem}`); await liberado(perfil); soltarTrava(); };
      return ctx;
    } catch (e) {
      const m = e?.message ?? String(e);
      if (!/ProcessSingleton|SingletonLock|profile directory|existing browser session|has been closed/i.test(m) || Date.now() > ate) { soltarTrava(); throw e; }
      console.log(`${agora().slice(11)} outro processo abriu o perfil antes; volto para a fila (${quem})`);
      await espera(20_000 + Math.random() * 10_000);
    }
  }
}

// depois de fechar, o Chrome leva uns segundos para soltar o SingletonLock
async function liberado(perfil) {
  for (let i = 0; i < 15 && donoDoPerfil(perfil); i++) await espera(1000);
}
