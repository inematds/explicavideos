# Canal — perfil-viral (só acrescentar; nunca reescrever)

Conhecimento do projeto que a compactação perde: fatos descobertos, aprendizados, glossário, armadilhas, onde estão as coisas.
Não é estado da tarefa (isso vai em state/plan/progress). Preencha cedo — o hook avisa na faixa 1 (~50% do contexto).

Formato: `- AAAA-MM-DD HH:MM · fato|aprendizado|glossário|armadilha · texto`

- 11/10 05:30: pedido do Nei: perfil viral no explicavideos (sem vídeo/b-roll; layout moderno com muito motion; peças do finviral e eventosextremospub). Proposta aceita: perfil novo no v2 (não motor separado), peças bignum/escala/mapa/cinetica, tela cheia + parallax, som (inemavox), QA medido (≤40% vazio, ≤2 s parado, contact sheet). Piloto TeraFab com a mesma gravação; só troca o publicado com aprovação.
- Armadilha: o main tem trabalho não commitado de outra sessão nos mesmos arquivos → trabalhar no worktree, peças em arquivos novos (viral.js/viral.css).
- 11/10 ~06:20: runtime/viral.js + viral.css + build_block (profile_visual viral, VIRAL_TYPES, rostos/fontes no index, gap 2 s) + qa_viral.py + som_viral.py no worktree. Piloto 16:9 render 1 → QA reprovou (fundo preto liso, texto sob o avatar). Correções: texto 16:9 só em x<1320; fundo = foto desfocada (S.fundo por cena); sombra mais leve.
- Armadilhas: texto de "rosto" dentro da cena fica ATRÁS do avatar (pip z30) → vai no index (.rtx). "Dois por cento#2" conta a partir do cursor (usar a 1ª ocorrência depois do shot anterior). sfx_v1.py do inemavox = API Pixabay (precisa autorização) → SFX locais em ~/projetos/mkivideos/motion-sfx, trilha ~/projetos/cardshorts/musicas/tensa.mp3 (MusicGen local).
- 11/10 ~07:00: piloto APROVADO no qa_viral (16:9 e 9:16), enviado ao bot. 9:16: capa cobre o quadro inteiro até o 1º corte (#capa-cheia no index); imagem com texto usa "texto": true (inteira sobre a própria imagem desfocada); QA ignora trechos de rosto (--relatorio) e mergulho de 0,5 s.
- 11/10 tarde: Nei aprovou ('sim'). Merge no main 0df3e41 (stash/pop do trabalho da outra sessão: 38/38 linhas preservadas, continua não commitado), worktree removido. Publicado: lives1 NtuTfKogeIc + q691yAilGsY, portal 9d02ee9, refazvideo modo viral 045ca17. Aberto: peça mapa (deck.gl pré-render), sfx via inemavox (API Pixabay, precisa autorização).
- 12/10: peça mapa (3fc0be5) + biblioteca-sons local (Pixabay/Freesound do inemavox não funcionam: stub + key vazia). Piloto TeraFab v2 com mapa enviado ao bot; NÃO republicado no YouTube/portal (aguarda o Nei).
- 05/11 (visual vídeo de referência 16:9): `fundo` só desfoca 3 px no CSS e o zoom 1,12–1,28 amplia — imagem do Codex com texto (tela de app, etiquetas, capa) vaza atrás de cinética/bignum. Usar cópia local desfocada (`ffmpeg scale=720,gblur=2.5`; letra grande/tela de app 260–360 px) e nunca a capa como fundo. Medir área lisa nos snapshots com o critério do qa_viral (192 px, blocos 8×8, std<6): reprova só >0,90, aviso >0,40; desfoque forte (480/4) levou a 0,58. Deixas casam no texto do roteiro (`meio-termo` → norm "meiotermo", então a deixa é "o meio-termo").

## 08/11/2026 — visual medidor-limite-20261108 (fase visual do bot)
- `foto.marcas` usa coordenadas da TELA (box), não da imagem: com recortes diferentes em 16:9 e 9:16 (src_916) a marca cai em lugar errado num dos formatos. Só use marca quando o recorte coincide nos dois; senão, use `pontos` (zoom).
- Capa com título no topo some sob a faixa de marca: reduzir a arte (~0,88) e descer a imagem sobre o fundo desfocado (media/capa-pad.png).
- Carimbo/2º texto sobre `rosto` = content_overlap ✗ no check; troque o texto com um 2º `rosto` (txt novo).
- `barra` formata com 0 casas (81,9 vira 82): use `bignum`/`ranking` com dec para decimais.
- Deixa com número por extenso cai em tempo interpolado (o ASR escreve dígitos): ancore o hit/marca numa palavra casada vizinha.

## 10/11/2026 — visual podcast-em-shorts (fase visual do /explicavideo)
- 16:9 viral: avatar no canto inferior direito cobre o texto da capa se o texto ocupar a largura toda → pedir ao Codex o texto na metade ESQUERDA e o canto inferior direito livre (capa2). Topo: deixar margem (~80 px) para a faixa INEMA · VÍDEOS (mock "-safe" com fundo desfocado).
- `capa_segura` só existia no 9:16; no 16:9 a capa parada > 2 s reprova o strict → pôr `"capa_segura": true` também no v2.json.
- Diagrama no 9:16 (pipfull) fica pequeno no topo e vazio → no visual compartilhado pelos dois formatos, preferir cinética.
- `foto` aceita `.mp4` (vfull, mudo) via `src_916`: os shorts reais 9:16 tocam no vertical; no 16:9 use mockup de celular.
- Print de webcam em quarto escuro + `vr-shade dark` (foto com titulo) = tela quase preta: clarear com gamma 0,7 antes de compor, fundo = foto clara desfocada, e tirar o titulo de foto escura. Medir área lisa com a conta do qa_viral (8×8, std<6, 192 px) nos snapshots.

- 12/11/2026 (fase visual escrita-prova-lives3): deixas casam com o TEXTO do roteiro (find_cue em `speech`), não com o Whisper. Mockup de print: `~/projetos/output/escrita-prova-lives3-20261112/media/mockups.py` (janela sobre fundo claro texturizado, `-v` próprio p/ 9:16 com recorte legível). `foto` com `texto: true` mostra a imagem inteira no 9:16 (placas). `fundo` da cena deve ser foto SEM texto (blur de 1,5–3 px deixa texto legível e cortado). No 9:16, cinetica com palavra única > ~11 letras a 120 px estoura a largura; capítulo com 10 letras precisa `size` ~120. Ranking aceita `cor` por item (não `alerta`).

## 13/11/2026 — fase visual nivel-ia-lives3-b (aprendizados)
- Capa com título desenhado NÃO serve de `fundo` de cena nem de `src` de capitulo: o título vira fantasma desfocado atrás de gráfico/CTA. Fundo = imagem sem texto.
- `sub` do `capitulo` no 9:16 (pipfull) cai atrás do PiP e por cima da legenda: troque por `cinetica` com as mesmas deixas.
- `selo` da capa no 9:16 bate na legenda (hyperframes check ⚠ content_overlap): sem selo quando há 9:16.
- Título de `foto` com pontuação colada no destaque ("**AL5**: x") separa o ":" no 9:16; evite.
- Escada AL1–AL5 com nomes curtos: `ranking` lw 200, max 8, n="AL1", txt=nome (cabe nos dois formatos).
- Recorte 9:16 local das fotos 16:9 (ffmpeg crop ih*9/16 no centro do assunto) → `src_916`.

## 13/11/2026 — visual nivel-ia-lives1-a (quiz)
- Capa 16:9 do Codex com texto até ~59% da altura encosta na caixa do avatar (topo ~60%): conferir o quadro 0 em tamanho cheio; contorno sem regerar = recortar 94% (y a partir de 6%) e ampliar.
- `diagrama` no 9:16: nós com x 0.62 saem pela borda direita; x ≤ 0.5 cabe nos dois formatos. Nota sem `lado` em nó baixo vai para cima e cobre o nó do meio.
- `barra` com `parte` no 16:9: o "%" grande encosta no texto lateral (content_overlap no check); usar só `total`.
- Whisper escreve "Pergunta dois/três" como "2."/"5." e todo "nível N" como dígito: nunca usar como deixa; conferir `interpolated` no build-v2-pt-b01.json.

## 14/11/2026 — fase visual "biblioteca sem internet" (lives3)
- No 9:16 a `.vr-img` é `background-position:50% 50%`: o `focus` mal move a imagem (só o zoom). Sujeito fora do centro de uma imagem 16:9 some; contorno = recorte vertical derivado (PIL, 9:16 da altura toda) em `src_916` por shot.
- Capa com manchete colada no topo: a faixa da marca cobre a 1ª linha; contorno = descer a arte 5% (16:9) / 6,5% (9:16) num derivado.
- Título de foto com `**frase longa**` destacada não quebra dentro do destaque: vai inteiro para a 2ª linha e bate na legenda (check `content_overlap`).

## 14/11/2026 — fase visual agentes-do-zero-lives3-20261114 (bot)
- Deixas casam com o texto do ROTEIRO (docs/lesson-pt.json), não com a transcrição: "a IA", números por extenso, "mal-intencionada" com hífen; o tempo vem do Whisper via difflib (número em dígito = interpolado).
- Perfil viral: limite 2 s entre trocas inclui 0 e o fim da cena; gráfico (ranking/colunas/linha/barra/escala/mapa) e foto "leitura" até 9 s, mas só se o gráfico for o ÚLTIMO shot ativo (carimbo keep por cima volta para 2 s).
- "av" no shot quebra o 9:16 (BuildError) — com o mesmo visual nos dois formatos, não usar.
- 9:16 pipfull (cena ≥ pip_cena): palco 1080×1920, PiP em (700,1400) 340×440 e legenda em y 1590 → área útil y 110–1380. Foto 16:9 em "cover" mostra só ~31% da largura: fazer src_916 recortado (media/mock/vcrops.py) ou "texto": true.
- Prints de terminal: recortar as linhas reais e reempilhar (media/mock/mockups.py) — 16:9 com janela à esquerda (avatar em x ≥ 1300, y ≥ 600), 9:16 em janela vertical. Cuidado com nomes: vcrops sobrescreveu mocks com o mesmo nome (trava-v19).

## 14/11/2026 — visual agente-por-pecas (lives3, só 16:9)
- Prints do kit (1280 px, fonte mono 10,24 px por caractere, linha i no centro y = 96 + 26,35·i) viram mockups 16:9 legíveis recortando linha a linha e ampliando 1,5–2,7×: `output/agente-por-pecas-lives3-20261114/media/mock/mockups.py` (grava `pos.json` com a posição de cada linha, que vira o `focus` dos `pontos`).
- Armadilhas: `carimbo` com mais de 10 letras é cortado na borda e o check não acusa (SEM CÉREBRO, TARDE DEMAIS); carimbo em x 0,82 / y 0,22 cobre o fim da 1ª linha longa do print, então quebre a linha; `foco` de diagrama num nó do topo desce o mundo e põe o núcleo sob a legenda (content_overlap).
- Área lisa medida sem render: snapshots a cada 2,5 s, blocos 8×8 com desvio < 6 a 192 px, a mesma conta do qa_viral. Deu ~12%.

- 14/11/2026 (visual explica-reel-asmr-cortes): `foto` com .mp4 toca do início do arquivo → cortar o trecho antes com ffmpeg (media/preparar.py). Vertical 1080×1920 no 16:9: compor o vertical nítido sobre ele mesmo desfocado (overlay x≈400–560, avatar não cobre). Clipe com texto embutido no pé (ex.: "Qual pote…") briga com legenda/PiP: cortar o pé. Print de terminal no 16:9: janela curta só com as linhas-chave no alto (o título `low` cobre o terço de baixo). Selo da capa e carimbo no fecho do `cta` dão content_overlap no check (16:9).

## 15/11/2026 — fase visual explica-robo-que-conversa (claude -p)
- Deixas casam com `docs/lesson-pt.json` (= roteiro-pt.json), não com o Whisper; tempos vêm do alinhamento. `*_at` internos buscam a partir do `at` do shot.
- Viral: limite 2,0 s entre tempos (at/*_at/pontos/marcas) da cena inteira, inclusive até o fim; só GRAFICOS e foto `leitura` têm 9 s. `av` quebra o 9:16 (mesmo arquivo serve os dois).
- 9:16 pip: cena 1 palco 1080×1150, cena ≥2 1080×1920 (PiP 340×440 em baixo, legenda y≈1590). 16:9: texto em x<1320, titulo low em y≈626, legenda y 880.
- qa_viral: bloco 8×8 em 192 px com desvio < 6 = liso; fundo claro chapado de mockup conta como liso.
- 15/11 deepseek-harness-lives4 (visual): deixas casam com a FALA do roteiro (lesson-pt.json), não com a grafia do Whisper ("Claude ponto M D", "seiscentas…", "contêiner"); prefira palavras que o ASR casou. `marcas` do `foto` são caixas fixas em % do palco (não seguem o zoom, cada uma escurece 35%): 1 marca por shot, zoom [1.6,1.6], tela = f + (p−f)·z. Capa 9:16 vai em #capa-cheia sob o #topo (110 px): descer a arte (capa-v.png) para o título não ficar sob a faixa.
- 15/11 lives4 (cont.): capitulo/bignum/cinetica com `src` de mockup (ou `fundo` de cena = mockup) ficam com texto sobre texto (blur só 1,5 px no 9:16); use foto do Codex sem texto nesses `src`/`fundo` e deixe os mockups só para `foto` com marca. Cinética com palavra de 11+ letras em size 110 vaza nas bordas do 9:16 (use ~90).

## 2026-11-18 · fase visual do Zelador (zelador-20261117, perfil aula)
- Perfil `aula` não carrega `viral.js`: `capa`, `foto`, `bignum`, `cta`, `rosto` e `av` passam no build e quebram no render. Usar `hook`, `media`, `keyword`, `counter`, `statement`, `diagrama`.
- `find_cue` casa as deixas com o roteiro (`docs/lesson-pt.json`), não com a grafia do Whisper. Validador descartável: `/tmp/zel/cues.py`; ritmo: `/tmp/zel/gaps.py`.
- `--strict` só reprova aviso em reel/viral; no aula, ler `warnings` em `verification/build-v2-pt-b01.json`.
- Frase solta em fundo escuro foi reprovada: virou legenda de `media`, com `cont` para trocar a legenda na mesma imagem. Fonte: `output/zelador-20261117/visual/gerar_visual.py`.
- `painel.jpg` (760×1910): evitar a faixa 0,60–0,77, que diz "o erro deixa de existir"; botões em fy 0,885.

## 18/11/2026: fase visual do explicavideo do-chat-ao-agente-3d-lives4
- Perfil `aula` não carrega viral.js: usar hook/media/counter/keyword/statement/diagrama, nunca capa/foto/bignum. O `--strict` fora do viral sai 0 mesmo com aviso: conferir `warnings` em `verification/build-v2-pt-b01.json`.
- Deixas casam com o `speech` do roteiro (`docs/lesson-pt.json`), não com a grafia do Whisper.
- Gerador e medidor: `~/projetos/output/do-chat-ao-agente-3d-lives4-20261118/visual/` (`gerar_visual.py`, `medir.py`); recortes em `media/recortar.py` (processo.png cortado acima da tabela de tempos).
- `statement` com `src` ou `then` revela palavra a palavra e pode sumir antes de ser lida: ressalva obrigatória vai em `label` de `media` ou no rótulo do `counter`. O `then` em `pos:"top"` com `keep` não mostrou a 1ª linha sobre o `counter` (lives4, cena 6).

## 2026-11-18 · fase visual gpt62-lives3 (anotado pelo aviso de contexto)
- Deixas casam com a fala do ROTEIRO (`docs/lesson-pt.json`), não com a escrita do Whisper; número por extenso e nome próprio ficam com tempo interpolado (`Timing.unmatched`).
- `capa_segura: true` no `v2.json` isenta só a capa do limite de 2 s; a entrega lê o mesmo `v2.json` da pasta do pedido.
- `barra` com `total` longo quebra linha para dentro da barra (≤ ~31 caracteres). Título com `**x**, y` deixa a vírgula solta: escrever sem vírgula depois do destaque.
- Carimbo com `x: 0.82` e 9+ letras encosta na borda: usar `x` ≤ 0,78.
- `pontos` na foto ainda contam como troca no build, mas a câmera não anda mais (2.28.11): usar troca real.

## 2026-11-19 · fase visual do Modelo do Seu Jeito (lives7, perfil aula)
- Saída: `~/projetos/output/modelo-do-seu-jeito-20261118`; gerador do visual em `visual/gerar_visual.py` (grava `v2/visual-v2/pt-b01.json`); pasta do bot: `textos/modelo-do-seu-jeito-lives7`.
- Perfil aula 16:9 não carrega `viral.js`: abertura é `hook` com `scrim:false`, não `capa`; imagem entra como `media` com `calm`. A `entrega` não roda `qa_viral` nesse perfil, então a olhada nos quadros é o único portão visual.
- Armadilha: `statement` aparece palavra por palavra e, se o shot seguinte entra logo após a última palavra, a frase nunca fica inteira na tela. Para frase que precisa ser lida, usar `media` com `label` e `label_at`.
- Deixa casa com o texto do roteiro (`docs/lesson-pt.json`), com o tempo vindo da transcrição.
