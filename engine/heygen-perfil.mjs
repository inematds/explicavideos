// Porteiro do perfil do HeyGen (estúdio). TODO projeto que usa o estúdio passa por
// heygen-studio.mjs ou heygen-estudio-baixar.mjs, e os dois abrem o perfil por aqui.
//
// O perfil é um só e o Chrome só deixa um processo abrir (SingletonLock). Antes, quem
// chegava com o perfil aberto morria com "ProcessSingleton" (saudeviral, 10/10/2026).
// Agora: espera o dono do perfil sair (PID do SingletonLock vivo) e entra; se perder a
// corrida no lançamento, espera e tenta de novo. Cada entrada/saída vai para
// ~/.cache/inemaccbot/heygen-uso.log (ver quem está usando: engine/heygen-fila.sh).
import { appendFileSync, mkdirSync, readlinkSync, lstatSync } from 'node:fs';
import { homedir } from 'node:os';
import path from 'node:path';

const LOG = path.join(homedir(), '.cache/inemaccbot/heygen-uso.log');
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
export async function abrirPerfil(chromium, perfil, opcoes, quem) {
  const ate = Date.now() + Number(process.env.HEYGEN_ESPERA_MIN || 180) * 60_000;
  for (;;) {
    await esperarLivre(perfil, ate, quem);
    try {
      const ctx = await chromium.launchPersistentContext(perfil, opcoes);
      registrar(`ENTRA ${quem} (cwd ${process.cwd()})`);
      const fechar = ctx.close.bind(ctx);
      ctx.close = async () => { await fechar().catch(() => {}); registrar(`SAI ${quem}`); await liberado(perfil); };
      return ctx;
    } catch (e) {
      const m = e?.message ?? String(e);
      if (!/ProcessSingleton|SingletonLock|profile directory/i.test(m) || Date.now() > ate) throw e;
      console.log(`${agora().slice(11)} outro processo abriu o perfil antes; volto para a fila (${quem})`);
      await espera(20_000 + Math.random() * 10_000);
    }
  }
}

// depois de fechar, o Chrome leva uns segundos para soltar o SingletonLock
async function liberado(perfil) {
  for (let i = 0; i < 15 && donoDoPerfil(perfil); i++) await espera(1000);
}
