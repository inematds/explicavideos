# Padrão viral (perfil `"profile_visual": "viral"`)

Para notícia, reel e vídeo com números (refazvideo `modo viral`, cortes de notícia). Aula continua no perfil
padrão. Nasceu do TeraFab (11/10/2026), que saiu com cara de slide e o Nei reprovou: "apresentação muito ruim".

## Roteiro (antes do HeyGen)
- **Uma ideia só**, 45–75 s. A 1ª frase diz o fato mais forte com o sujeito ("O maior prédio da história…").
- **Quadro 0 = capa**: imagem forte + o número/promessa mais forte, sem fade (vira thumbnail).
- Promessa do que vem ("no fim, o que isso muda pra você") nos primeiros 8 s.
- Todo número com fonte; número sem fonte sai do roteiro. Fecho: cursos grátis no inema.club.
- Números por extenso na fala (o Whisper escreve algarismo; ver FALHAS 11/10).

## Visual
- **Tela cheia**: a cena ocupa o quadro todo; nada de "área útil à esquerda" nem cartão lateral.
- **Troca a cada 1,5–3 s** (corte, número, carimbo, pan para outro ponto da imagem). Nunca > 2 s parado **em imagem**. Gráfico animado (`linha`, `colunas`, `ranking`, `barra`, `escala`, `mapa`) pode ficar até 9 s: tem de dar tempo de ler (Nei 21/10/2026).
- **Número = peça própria** (`bignum`): gigante, contagem curta (≤ 0,8 s) que termina na deixa, fonte embaixo.
- **Comparação de escala** (`escala`), **mapa** (`mapa`), **tipografia cinética** (`cinetica`),
  **carimbo** (`carimbo`), **barra/percentual** (`barra`), **capítulo** (`capitulo`: tela limpa + assunto grande), **linha** (`linha`, 2.17: gráfico de linha real que se desenha no tempo da fala; `series[{n, pts:[[x,v]], de, ate, at, ate_at, passos:[{x, at}], cor, teto_txt}]` (`passos` = a linha chega em x na deixa, trecho a trecho), `x`, `y`, `xticks`, `yticks`, `marcos[{x, txt, at}]`, `unid`, `dec`; repetir o mesmo gráfico em shots seguidos com `de` = onde parou dá a continuidade).
- **Gráfico comparativo** (`ranking`, 14/10/2026): barras horizontais que crescem uma a uma, valor contando no fim;
  `itens` [{n, v, hl, at}] (até 5–6; `hl` = destaque âmbar), `titulo`, `unid`, `dec`, `max`, `fonte`. Cada item com a
  sua deixa na fala, senão o shot fica parado. `v_at` (opcional, 14/10/2026): a barra cresce numa 2ª deixa — pergunta no
  `at`, resposta no `v_at` ("Acha pela palavra exata?" → "Nível um"), duas trocas por item. Painel translúcido sobre a foto desfocada (passa no QA de área lisa).
- **Ranking grande** (`"grande": true`, 2.19, 21/10/2026): no 16:9 com 2–4 itens, linhas altas (175 px), barras grossas, rótulo 46 px e valor 74 px, bloco centrado no painel; com `log` deixa espaço para a régua. Use com `lw` ~430 e rótulos curtos (≤ 14 caracteres); valor longo com `txt` cai dentro da barra se ela encostar no fim, então aumente `max` para o valor ficar fora. Fonte curta (≤ 50 caracteres), senão passa por baixo do avatar. Primeiro uso: musk-humanoides v2.
- **Escala de potências de dez** (`ranking` com `"log": true`, 2.18, 21/10/2026): para comparar +30% com 1 milhão de vezes; barras em log10, régua `1× 10× 100× 10³…` embaixo; `txt` no item escreve o valor ("até 10^6×" vira expoente) e, se a barra encosta no fim, o valor vai dentro dela. Diga na fala ou na fonte que é escala log. Primeiro uso: musk-isaacson.
- **Série no tempo** (`colunas`, 15/10/2026): até ~30 barras verticais que sobem em sequência (ex.: focos 2003–2026); `itens` [{n, v, hl|alerta|mostra, rot, at}] — o `at` do item é a deixa em que ele acende (âmbar `hl`, vermelho `alerta`) e mostra o valor; `todos_rotulos` põe o ano em todas; `titulo`, `unid`, `dec`, `max`, `fonte`. Molde: `~/projetos/output/explica-queimadas-viral/visual/gerar_visual.py`.
- **Carimbo ao lado** (`carimbo` com `x`, 15/10/2026): em cena de gráfico/número o carimbo central cobre título, rótulo e barras (o `hyperframes check` reprova `content_overlap`). Use `x: 0.82` (área livre acima da caixa do avatar, y 0,22–0,50) e texto ≤ ~10 caracteres; carimbos com `keep` empilham — varie o `y`.
- **Mapa** (`mapa`): contornos reais locais (`mapa_geo.py`, us-atlas/world-atlas em `~/projetos/biblioteca-mapas`),
  `base` eua|mundo|brasil|brasil-uf (27 estados com nome completo, para acender Pará, Amazonas…; contornos em `biblioteca-mapas/brasil-uf/`), `camera` [{at, centro:[lon,lat], zoom}], `destaques` [{nome, at}] (estado dos EUA ganha os
  condados), `pinos` [{lon, lat, txt, at, sub, sub_at}]. O qa_viral não mede área lisa nos trechos de mapa.
- **Cor da imagem**: luz neutra, branco que parece branco, uma cor forte de destaque; nada de "paleta âmbar", "luz dourada" ou objeto dourado em toda cena (o gerador do Codex já puxa para o amarelo). O âmbar da marca fica só no texto e nas peças desenhadas. Depois de gerar: `refazvideo/ferramentas/cor_neutra.py corrigir media/*.png` (corrige amarelo > 18, guarda `-amarela`).
- **Recorte de leitura** (`foto` com `"leitura": true`, 2.22.11, 23/10/2026): print de tela do original (em inglês) + tradução PT grande desenhada na imagem (`src` 16:9 e `src_916`); vale o teto do gráfico (até 9 s), não os 2 s. Molde: `~/projetos/output/explica-vZD4PmureWM/media/recortar.py`.
- **Imagem** (`foto`): sempre em movimento (pan + zoom ≤ 1,25 + leve parallax de camadas), com vinheta e grão.
- **Avatar** (D8 do inema-design, 15/10/2026): **nunca em tela cheia** — no máximo meia tela. 16:9 = caixa no canto
  inferior direito; `rosto` cresce até a metade direita. 9:16 = metade de baixo; `rosto` = metade de baixo. Com
  `"avatar_916": "pip"` + `"pip_cena": N` na config: capa sem avatar → meio tamanho até a cena N → PiP pequeno no canto
  e a cena no quadro inteiro (1080×1920, classe `pipfull`). Versão **sem avatar** (2.23.11): `"sem_avatar": true` + `"pip_cena": 1`, sem shot `rosto`. `"capa_segura": true` deixa a capa parada uns segundos
  (texto inicial mais tempo aberto) sem o build acusar "sem mudança".
- **Imagens**: uma por momento, sem repetir; dado de lugar vira mapa real (satélite NASA HLS via GIBS, anotado).
- **Marca**: faixa fina no topo (INEMA · assunto · fonte do dado da vez). Legenda grande, 1–3 palavras, palavra
  falada em âmbar.
- Sem vídeo de terceiros nem b-roll pago por padrão (imagens locais/Codex).

## Som
- **Sem efeitos no meio** (D7, 15/10/2026): `som_viral.py --sem-efeitos` = só voz + trilha baixa.
- Sem som de movimento de tela (13/10/2026, pedido do Nei): nada de whoosh nas trocas, pop nas palavras nem riser.
  Efeito só onde marca algo: carimbo, selo da capa, impacto do bignum/barra, capítulo (braam), cta (ding).
  Voz na frente: comprimida e levada a -13 LUFS, trilha abaixa sob a fala (sidechain), limitador no fim.
- Trilha baixa sob a voz e efeitos nos números: `som_viral.py --trilha=<nome>` usa a biblioteca local
  `~/projetos/biblioteca-sons` (6 trilhas MusicGen: noticia-urgente, tech-epico, tech-otimista, sombrio-pulso,
  inspirador, beat-viral; 30 efeitos sintetizados que giram). O buscador do inemavox (Pixabay/Freesound) não funciona
  sem FREESOUND_API_KEY.

## QA (`engine/v2/qa_viral.py`, reprova)
- Quadro com > 40% de área lisa (fundo vazio), amostra a cada 0,5 s.
- Avatar que se move (16:9, 2.24.11): `"av"` no shot troca posição/tamanho do avatar até o próximo `"av"`. Em shot com texto, número ou gráfico, só `dir`, `mini` ou `alto-dir` (as poses `-esq`, `grande` e `meia` cobriram título, cinética e número no quadro de 27/10/2026); alternar entre elas dá o movimento, e o tamanho grande fica com o `rosto`.
- Trecho > 2 s sem mudança visual (fora de gráfico; gráfico até 9 s).
- Folha de quadros (`verification/sheet-viral-*.jpg`) sempre gerada e olhada antes de entregar.
