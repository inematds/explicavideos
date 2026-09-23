// Gera o vídeo de avatar no estúdio do HeyGen por SCRIPT — sem agente.
//
//   node scripts/heygen-estudio.mjs --titulo A32-jovens-v1 \
//     --fala-arquivo /tmp/fala.txt --perfil <dir> [--template TEMPLATE-AVATAR] [--seco]
//
// Faz o mesmo caminho que o prompt `fase-navega-avatar.md` descreve ao agente:
// busca o template, `Editar como Novo`, renomeia ANTES de tudo, troca a fala,
// `Gerar` e confirma no modal. As quatro diferenças que só um script consegue:
//
//  1. **Igualdade exata no nome do template.** A busca traz `TEMPLATE-AVATAR9`
//     e `-16` junto; o prompt manda o agente PARAR nesse caso porque ele não
//     tem como decidir. Aqui a decisão é `===`.
//  2. **O modal.** "Gerar" só ABRE a confirmação (resolução/formato/fps); quem
//     dispara é o "Enviar". Sem ele o vídeo fica `draft` para sempre e a fase
//     `baixar` espera 1h30 por um vídeo que nunca vem. Medido em 2026-08-06.
//  3. **Acento.** `type()` passa pelo CDP e escreve certo no tiptap — some toda
//     a receita de xclip/xdotool/ctrl+2/visibilityState, que era a maior seção
//     do prompt e a causa nº 1 de falha silenciosa.
//  4. **A fala vem de ARQUIVO**, nunca de argumento: texto acentuado dentro de
//     aspas de shell é a mesma classe de bug que a receita antiga tentava
//     evitar.
//
// Sai 0 com `RESULT: <titulo>` na última linha; 3 com `ERRO: <motivo>`.
import { readFileSync } from 'node:fs';
import { chromium } from '/home/nmaldaner/projetos/inemaccbot/node_modules/playwright/index.mjs';

const arg = (n, d) => {
  const i = process.argv.indexOf(`--${n}`);
  return i > 0 && process.argv[i + 1] ? process.argv[i + 1] : d;
};
const TITULO = arg('titulo');
const PERFIL = arg('perfil');
const TEMPLATE = arg('template', 'TEMPLATE-AVATAR');
const SECO = process.argv.includes('--seco');   // para tudo antes do "Enviar"
const FALA = (() => {
  const f = arg('fala-arquivo');
  return f ? readFileSync(f, 'utf8').trim() : '';
})();

if (!TITULO || !PERFIL || !FALA) {
  console.error('ERRO: uso: --titulo <t> --perfil <dir> --fala-arquivo <arq> [--template <t>] [--seco]');
  process.exit(3);
}

const passo = (m) => console.log(`${new Date().toISOString().slice(11, 19)} ${m}`);
if(FALA.length>4500){console.error("ERRO: bloco excede teto local de4500 caracteres");process.exit(3);}
let ctx;
const morrer = async (m) => {
  await ctx?.close().catch(() => {});
  console.error(`ERRO: ${m}`);
  process.exit(3);
};

// COM JANELA sempre que houver uma tela — nem que a tela seja um Xvfb que
// ninguém olha.
//
// Custou o C#77: o HeyGen passou a barrar navegador headless. Ele não redireciona
// para o login — carrega a app INTEIRA, com avatar e nome da conta, e joga o
// modal "Continuar com o Google" por cima. Como a prova de sessão daqui é a
// barra de busca da tela de Projetos, o script lia isso como "não está logada
// neste perfil", e a fase morria acusando a credencial — que estava certa o
// tempo todo. Medido lado a lado no MESMO perfil: `headless: true` → modal de
// login; `headless: false` → logado, tanto na tela real quanto no Xvfb.
//
// Sem `DISPLAY` (VPS pelada, CI) cai no headless de antes: melhor tentar e
// falhar com a mensagem de sempre do que não rodar.
const COM_TELA = Boolean(process.env.DISPLAY);
passo(COM_TELA ? `com janela (DISPLAY=${process.env.DISPLAY})` : 'sem DISPLAY — headless');
ctx = await chromium.launchPersistentContext(PERFIL, {
  headless: !COM_TELA,
  // `--password-store=basic`: é assim que o Chromium do snap cifra os cookies.
  // Sem isto a sessão do HeyGen parece deslogada.
  args: ['--password-store=basic', '--no-first-run', '--no-default-browser-check'],
  viewport: { width: 1440, height: 900 },
});
const pg = ctx.pages()[0] ?? await ctx.newPage(); for(const extra of ctx.pages().slice(1))await extra.close();
pg.setDefaultTimeout(45_000);
const BUSCA = 'input[placeholder*="esquisar" i], input[placeholder*="earch" i]';

// A BUSCA agora nasce ESCONDIDA atrás de uma lupa.
//
// O HeyGen redesenhou a tela de Projetos (visto em 2026-08-26): a barra de
// busca virou um ícone, e o DOM passou a ter DOIS inputs com o mesmo
// placeholder — o `[0]` fica invisível para sempre e o `[1]` só aparece depois
// do clique. O script pegava `.first()`, ou seja, sempre o fantasma: o `fill`
// esperava 45s por um elemento que nunca ficaria visível e a fase morria com
// `locator.fill: Timeout`. Foi assim que as 36 fases do C#110 falharam de uma
// vez, com a sessão perfeitamente logada.
//
// Por isso `:visible` em vez de `.first()`: o que importa não é existir, é
// poder ser usado. E o clique na lupa é condicional — se um dia a barra voltar
// a nascer aberta, este código continua servindo.
const buscaVisivel = () => pg.locator(`${BUSCA}`).filter({ visible: true }).first();

async function abrirBusca() {
  if (await buscaVisivel().count()) return;
  const lupa = pg.getByRole('button', { name: /^(search|buscar|pesquisar)$/i }).first();
  if (!(await lupa.count())) await morrer('não achei a busca nem o botão de lupa na tela de Projetos');
  await lupa.click();
  await pg.waitForTimeout(1_500);
  if (!(await buscaVisivel().count())) await morrer('cliquei na lupa e a busca não apareceu');
}

async function buscar(termo) {
  await abrirBusca();
  const campo = buscaVisivel();
  await campo.fill('');
  await campo.fill(termo);
}
const CAMPO_TITULO = 'input[placeholder*="sem título" i], input[placeholder*="Untitled" i]';

try {
  passo('abrindo Projetos');
  await pg.goto('https://app.heygen.com/projects', { waitUntil: 'domcontentloaded', timeout: 90_000 });
  await pg.waitForTimeout(5_000);
  if (!(await pg.locator(BUSCA).count())) {
    await morrer('a sessão do HeyGen não está logada neste perfil');
  }

  // Retomada: um rascunho com ESTE título é uma tentativa anterior que renomeou
  // e não gerou. Continuar dele evita deixar um segundo rascunho homônimo.
  await buscar(TITULO);
  await pg.waitForTimeout(3_500);
  const rascunho = pg.getByText(TITULO, { exact: true }).first();
  if (await rascunho.count()) {
    passo(`rascunho "${TITULO}" existe — continuando dele`);
    await rascunho.locator('xpath=ancestor::*[.//img or .//video][1]').click();
    await pg.waitForURL(/create-v4|editor/, { timeout: 60_000 });
  } else {
    passo(`buscando "${TEMPLATE}"`);
    await buscar(TEMPLATE);
    await pg.waitForTimeout(4_000);
    const alvo = pg.getByText(TEMPLATE, { exact: true });
    const n = await alvo.count();
    if (n !== 1) await morrer(`${n} cards com o nome exato "${TEMPLATE}" (esperado 1)`);

    const card = alvo.first().locator('xpath=ancestor::*[.//img or .//video][1]');
    await card.hover();
    await card.locator('button').first().click();     // o ⋮ do CARD
    await pg.waitForTimeout(1_200);
    const item = pg.getByText(/Editar como Novo|Edit as New/i).first();
    if (!(await item.count())) await morrer('o menu do card não tem "Editar como Novo"');
    passo('Editar como Novo');
    await item.click();
    await pg.waitForURL(/create-v4|editor/, { timeout: 60_000 });
  }
  await pg.waitForTimeout(6_000);

  // TÍTULO PRIMEIRO: o clone nasce com o nome do template, e enquanto não
  // renomear existem dois `TEMPLATE-AVATAR` — a busca da rodada seguinte fica
  // ambígua e o passo do `!== 1` acima recusaria o fluxo inteiro.
  passo('renomeando');
  const campo = pg.locator(CAMPO_TITULO).first();
  if (!(await campo.count())) await morrer('campo de título não encontrado no estúdio');
  await campo.click();
  await campo.fill(TITULO);
  await campo.press('Tab');
  await pg.waitForTimeout(1_500);

  passo('trocando a fala');
  const editor = pg.locator('[contenteditable="true"]').first();
  if (!(await editor.count())) await morrer('editor de script não encontrado');
  await editor.locator('[data-node-view-content-react]').first().click();
  await editor.press('ControlOrMeta+a');
  await editor.press('Backspace');
  await pg.keyboard.insertText(FALA); await campo.click(); await campo.press('Tab'); await pg.waitForTimeout(10000);
  await pg.waitForTimeout(2_000);

  // Conferência pelo DOM, não por screenshot: `read_page` mostra o placeholder
  // do título, não o valor.
  const conferido = await pg.evaluate((sel) => ({
    titulo: document.querySelector(sel)?.value ?? null,
    texto: Array.from(document.querySelectorAll('[contenteditable="true"] [data-node-view-content-react]')).map(x=>x.textContent).join(' ').trim(),
  }), CAMPO_TITULO);
  if (conferido.titulo !== TITULO) await morrer(`título ficou "${conferido.titulo}"`);
  console.log(JSON.stringify({url:pg.url(),chars:conferido.texto.length,ui:(await pg.locator('body').innerText()).slice(-1800)}));
  if (conferido.texto.replace(/\s+/g,' ').trim() !== FALA.replace(/\s+/g,' ').trim()) await morrer('a fala não entrou no editor');

  if (SECO) { console.log(JSON.stringify({url:pg.url(),ui:(await pg.locator('body').innerText()).slice(-1200),chars:conferido.texto.length})); await pg.screenshot({path:'/tmp/astra-studio-draft.png'}); passo('--seco: parando antes de gerar'); await ctx.close(); process.exit(0); }

  if(!(await pg.locator('body').innerText()).includes('Avatar III'))await morrer('Avatar III não confirmado');
  passo('Gerar');
  const gerar = pg.getByRole('button', { name: /^(Gerar|Generate)/i }).first();
  if (!(await gerar.count())) await morrer('botão Gerar não encontrado');
  await gerar.click();
  await pg.waitForTimeout(4_000);

  // O passo que não estava no prompt do agente.
  const enviar = pg.getByRole('button', { name: /^(Enviar|Submit)$/i }).first();
  if (!(await enviar.count())) await morrer('modal de geração sem botão "Enviar"');
  console.log('MODAL', (await pg.locator('[role=dialog]').allTextContents()).join(' | ').slice(0,4000));
  passo('Enviar');
  await enviar.click();
  await pg.waitForTimeout(8_000);

  await ctx.close();
  console.log(`RESULT: ${TITULO}`);
} catch (e) {
  await morrer((e && e.message ? e.message : String(e)).split('\n')[0].slice(0, 200));
}
