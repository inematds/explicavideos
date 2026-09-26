# Explicavideos v2: como escrever o roteiro visual

O vídeo v2 mostra **o mecanismo do que está sendo falado, no momento em que é falado**. A fala e o avatar já existem.
Você escreve apenas o roteiro visual de cada cena, em `<output>/visual-v2/<bloco>.json`.

## Regra de ouro

Uma cena não é um slide. Cada frase importante da fala precisa de uma **imagem que explique**:

- processo vira fluxo;
- escolha vira radar ou órbitas;
- mito vira frase riscada e corrigida;
- passos viram trilho;
- comando vira terminal digitando;
- estrutura vira árvore de pastas;
- antes/depois vira comparação.

Nunca deixe mais de **10 s sem algo novo acontecer**. O build acusa essas lacunas.

**Nenhuma moldura vazia por mais de 3 s** (2.0.1). Um shot com cartões, raias, chat ou terminal não pode ficar
só com as molduras/títulos enquanto a fala segue: ponha o 1º item na mesma deixa do `at` do shot (ou até ~3 s
depois) e distribua os demais pelas frases seguintes. Se a fala demora a chegar no conteúdo, use antes um
`statement`/`keyword` curto. O runtime já segura o shot anterior até o próximo ter conteúdo; o que ele não
resolve é um shot que entra e fica com as caixas vazias. Confira nos snapshots.

**Outros idiomas.** Para EN/ES, parta do roteiro visual PT do mesmo módulo: mesma sequência de shots e tipos,
textos traduzidos (mesma terminologia do curso no idioma) e **todas as deixas refeitas** com trechos literais da
fala no idioma (`docs/lesson-<lang>.json`). Os rótulos fixos (PARA LEVAR, CENA…) já saem no idioma pelo `lang`.

## Formato

```json
{"block":"pt-b03","scenes":{
  "15":{"takeaway":"frase curta com **destaque** (opcional; substitui a da fonte)",
        "shots":[ {"type":"steps","at":"Vamos ao laboratório", ...}, {"type":"...","at":"...", ...} ]}}}
```

As regras de tempo:

- **Todo tempo é uma deixa falada.** `at` e qualquer campo `*_at` recebem um trecho literal da fala da **própria cena** (de 1 a 5 palavras). Nunca use segundos: o modo `--strict` recusa.
- **A comparação ignora maiúsculas, acentos e pontuação.** Se a mesma deixa aparece mais de uma vez na cena, use `"trecho#2"` para pegar a 2ª ocorrência.
- **Os shots ficam em ordem de fala.** Um shot substitui o anterior no seu `at`. Com `"keep": true`, o anterior continua na tela (por exemplo, uma frase no topo com `pos:"top"` e um radar embaixo).
- **Os itens internos são buscados a partir do `at` do próprio shot.** O build avisa se uma deixa estiver antes da anterior.
- **Markup nos textos:** `**x**` fica âmbar, `++x++` fica verde (certo) e `~~x~~` fica vermelho ou riscado (errado, no statement).
- **A área útil é a esquerda (x 90–1420).** O avatar fica no canto superior direito, e o cartão "PARA LEVAR" aparece sozinho sob o avatar. Seja conciso: textos curtos e grandes explicam melhor que parágrafos.

## Primitivos (`type`)

| type | quando usar | campos |
|---|---|---|
| `bullets` | ideias ou itens (≤4 curtos em linha; senão em coluna) | `items:[{text, at, icon?, sub?}]`, `layout?:"row"\|"column"`, `title?` |
| `hub` | um sistema e suas peças | `center:{label, icon?, at}`, `nodes:[{label, icon?, sub?, at}]` (≤8), `focus?:[{node, at}]` |
| `pipeline` | entrada → modelo → saída | `input:{title, files[], at}`, `core:{label, at}`, `output:{title, tokens[], at}` |
| `flow` | caminho e arquitetura | `nodes:[{id, label, icon?, col 0-4, row 0-3, at}]`, `edges:[{from, to, at, label?}]` |
| `orbs` | opções diferentes (nomes, tamanhos, custos) | `items:[{name, size 0.6-1.8, tag?}]` (≤7), `names_at?`, `sizes_at?`, `tags_at?`, `pick?:{name, at, note}` |
| `podium` | "qual é o melhor?" desmontado | `question`, `question_at`, `names[]` (3-6), `collapse_at` |
| `statement` | frase-chave, mito → verdade | `text`, `pos?:"top"`, `strike_at?`, `then?:{text, at, replace?:false}` |
| `radar` | critérios de escolha e encaixe | `axes:[{label, at, value 0-1}]` (3-6), `candidates:[{name, values[], fit, note, at}]` |
| `lanes` | separar por função ou categoria | `lanes:[{title, sub?, icon?}]` (2-4), `items:[{lane, text, at}]`, `chips?:[{label, lane, at}]`, `chaos_at?`, `sort_at?`, `lanes_at?` |
| `compare` | antes/depois, errado/certo | `left:{title, at, tone?, lines:[{text, at}]}`, `right:{...}`, `verdict?:{text, at}` (`tone` pode ser bad, good ou neutral) |
| `chat` | conversa com a IA | `title?`, `messages:[{role:"user"\|"ai"\|"note", text, at}]` (≤6) |
| `terminal` | comandos e saídas | `title?`, `lines:[{type:"cmd"\|"out"\|"comment"\|"err", text, at}]` (≤9) |
| `filetree` | pastas e arquivos | `root`, `entries:[{path, at, note?, kind?:"dir"}]` (≤9) |
| `fields` | ficha, contrato ou pedido preenchido | `title`, `fields:[{label, value, at}]` (≤6), `stamp?:{text, at}` |
| `steps` | laboratório passo a passo | `goal?`, `steps:[{title, at}]` (2-5), `done_at?` |
| `quiz` | "Confira o que aprendeu" | `question`, `at`, `answer`, `answer_at`, `note?`, `note_at?` |
| `timeline` | sequência no tempo | `events:[{label, sub?, at}]` (2-6) |
| `counter` | números | `items:[{value, label, prefix?, suffix?, decimals?, at}]` (1-3) |
| `keyword` | palavra ou número de impacto | `text`, `sub?`, `sub_at?` |
| `module_intro` | abertura "Módulo N" | `n`, `title`, `goal`, `goal_at`, `exercise`, `exercise_at` |
| `svg` | diagrama original da fonte (último recurso) | `marks?:[{text, at}]` |

Os ícones (`icon`) disponíveis são: doc, folder, chat, terminal, key, lock, cloud, server, ai, user, team, check, x, clock,
money, star, search, gear, git, send, book, bulb, warn, target, list, image, video, code, link, shield, eye, pencil,
calendar, chart, cpu, play, pause, refresh, phone, globe, upload, download, bot, memory, flag e box.

## Padrões para as cenas recorrentes

- **"Módulo N. …":** use `module_intro`.
- **Conceito (cenas longas, de 40 a 90 s):** 4 a 8 shots, variando os tipos. Termine em "Pontos para lembrar" com `bullets`.
- **"Na prática":** a parte "Vamos a um exemplo" vira `compare`, `chat`, `terminal`, `lanes` ou `fields`, conforme o exemplo. A parte "Agora é sua vez" vira `bullets` (row, `title:"SUA AÇÃO"`), `fields` ou `terminal`.
- **"Vamos ao laboratório":** use `steps`, com um card por "Passo N" e deixas "Passo 1", "Passo 2"… Depois, `bullets` ou `fields` para o registro.
- **"Antes de avançar… pergunta":** use `quiz` (a deixa `answer_at` é "A resposta é").

## Aceite (por bloco)

```bash
cd ~/projetos/explicavideos && export EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json
python3 engine/v2/build_block.py <N> --strict      # 0 erros; acerte até warnings = []
cd ~/projetos/output/oswork-completo-v2/final/pt-bNN && npx --yes hyperframes@0.8.77 check   # "Check passed"
npx --yes hyperframes@0.8.77 snapshot --at <t1,t2,...> --no-end --describe false          # olhe os quadros
```

O exemplo completo e aprovado está em `visual-v2/pt-b01.json`.
