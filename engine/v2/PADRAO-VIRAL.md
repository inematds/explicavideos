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
- **Troca a cada 1,5–3 s** (corte, número, carimbo, pan para outro ponto da imagem). Nunca > 2 s parado.
- **Número = peça própria** (`bignum`): gigante, contagem curta (≤ 0,8 s) que termina na deixa, fonte embaixo.
- **Comparação de escala** (`escala`), **mapa** (`mapa`), **tipografia cinética** (`cinetica`),
  **carimbo** (`carimbo`), **barra/percentual** (`barra`), **capítulo** (`capitulo`: tela limpa + assunto grande).
- **Mapa** (`mapa`): contornos reais locais (`mapa_geo.py`, us-atlas/world-atlas em `~/projetos/biblioteca-mapas`),
  `base` eua|mundo|brasil, `camera` [{at, centro:[lon,lat], zoom}], `destaques` [{nome, at}] (estado dos EUA ganha os
  condados), `pinos` [{lon, lat, txt, at, sub, sub_at}]. O qa_viral não mede área lisa nos trechos de mapa.
- **Cor da imagem**: luz neutra, branco que parece branco, uma cor forte de destaque; nada de "paleta âmbar", "luz dourada" ou objeto dourado em toda cena (o gerador do Codex já puxa para o amarelo). O âmbar da marca fica só no texto e nas peças desenhadas. Depois de gerar: `refazvideo/ferramentas/cor_neutra.py corrigir media/*.png` (corrige amarelo > 18, guarda `-amarela`).
- **Imagem** (`foto`): sempre em movimento (pan + zoom ≤ 1,25 + leve parallax de camadas), com vinheta e grão.
- **Avatar**: grande. 16:9 = janela redonda grande no canto inferior direito, que cresce para tela cheia nos
  shots `rosto`; 9:16 = metade de baixo, e `rosto` toma a tela.
- **Marca**: faixa fina no topo (INEMA · assunto · fonte do dado da vez). Legenda grande, 1–3 palavras, palavra
  falada em âmbar.
- Sem vídeo de terceiros nem b-roll pago por padrão (imagens locais/Codex).

## Som
- Trilha baixa sob a voz e efeitos nos cortes e números: `som_viral.py --trilha=<nome>` usa a biblioteca local
  `~/projetos/biblioteca-sons` (6 trilhas MusicGen: noticia-urgente, tech-epico, tech-otimista, sombrio-pulso,
  inspirador, beat-viral; 30 efeitos sintetizados que giram). O buscador do inemavox (Pixabay/Freesound) não funciona
  sem FREESOUND_API_KEY.

## QA (`engine/v2/qa_viral.py`, reprova)
- Quadro com > 40% de área lisa (fundo vazio), amostra a cada 0,5 s.
- Trecho > 2 s sem mudança visual.
- Folha de quadros (`verification/sheet-viral-*.jpg`) sempre gerada e olhada antes de entregar.
