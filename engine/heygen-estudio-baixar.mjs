// Confere e baixa um vídeo de avatar enviado pelo estúdio do HeyGen — pela API de LEITURA.
//
//   node engine/heygen-estudio-baixar.mjs --id <id32> --saida <arq.mp4> \
//     [--perfil <dir>] [--minutos 120] [--intervalo 120]
//
// Desde 17/10/2026 a verificação e o download são pela API (GET /v3/videos/<id> + video_url),
// autorizado pelo Nei (leitura não gasta crédito). Gerar/enviar continua só pelo estúdio
// (heygen-studio.mjs). Não abre navegador nem ocupa o perfil do HeyGen; --perfil é aceito e
// ignorado para não quebrar quem já chama assim.
// Sai 0 com `RESULT: <arquivo>`; 3 com `ERRO: <motivo>`; 4 se estourou o tempo.
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';

const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d; };
const ID = arg('id'), SAIDA = arg('saida');
const MINUTOS = Number(arg('minutos', '120'));
const INTERVALO = Math.min(Number(arg('intervalo', '120')), 60);
if (!/^[a-f0-9]{32}$/.test(ID ?? '') || !SAIDA) { console.error('ERRO: uso: --id <id32> --saida <arq.mp4>'); process.exit(3); }
const passo = (m) => console.log(`${new Date().toISOString().slice(11, 19)} ${m}`);
const sair = (cod, m) => { console[cod ? 'error' : 'log'](m); process.exit(cod); };

let CHAVE = null;
for (const linha of readFileSync(`${homedir()}/projetos/openpcbotv2/.env`, 'utf8').split('\n')) {
  const m = linha.match(/^\s*HEYGEN_API_KEY\s*=\s*(.+?)\s*$/);
  if (m) CHAVE = m[1].replace(/^['"]|['"]$/g, '');
}
if (!CHAVE) sair(3, 'ERRO: HEYGEN_API_KEY ausente em ~/projetos/openpcbotv2/.env');

async function status() {
  const r = await fetch(`https://api.heygen.com/v3/videos/${ID}`, { headers: { 'X-Api-Key': CHAVE }, signal: AbortSignal.timeout(30_000) });
  if (r.status === 404) return { status: 'nao_existe' };
  if (!r.ok) return { status: 'indisponivel', http: r.status };
  const j = await r.json();
  return j.data ?? j;
}

async function baixar(url) {
  const r = await fetch(url, { signal: AbortSignal.timeout(900_000) });
  if (!r.ok) sair(3, `ERRO: download HTTP ${r.status}`);
  const corpo = Buffer.from(await r.arrayBuffer());
  if (corpo.length < 1_000_000) sair(3, `ERRO: arquivo pequeno demais (${corpo.length} bytes)`);
  const temp = SAIDA.replace(/\.mp4$/, '') + '.part.mp4';
  writeFileSync(temp, corpo); renameSync(temp, SAIDA);
  sair(0, `RESULT: ${SAIDA}`);
}

const fim = Date.now() + MINUTOS * 60_000;
let semId = 0;
while (Date.now() < fim) {
  let d;
  try { d = await status(); } catch (e) { d = { status: 'indisponivel', erro: String(e?.message ?? e).slice(0, 120) }; }
  const st = String(d.status ?? '').toLowerCase();
  if (st === 'completed' && d.video_url) { passo(`pronto (${d.title ?? ID}) — baixando pela API`); await baixar(d.video_url); }
  if (st === 'failed') sair(3, `ERRO: HeyGen falhou (${String(d.failure_message ?? d.error ?? '').slice(0, 160)})`);
  if (st === 'draft') sair(3, 'ERRO: vídeo está em Draft — o envio não pegou');
  // 404 logo após o envio pode ser atraso de indexação; 3 seguidos = ID errado ou rascunho nunca enviado
  if (st === 'nao_existe') { if (++semId >= 3) sair(3, 'ERRO: a API não acha este ID (404) — conferir o título em Projetos no estúdio (Draft?)'); }
  else semId = 0;
  passo(`status: ${st || '?'}${d.http ? ` (HTTP ${d.http})` : ''}`);
  await new Promise((r) => setTimeout(r, INTERVALO * 1000));
}
sair(4, 'ERRO: tempo esgotado esperando o HeyGen');
