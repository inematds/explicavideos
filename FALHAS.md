| data | o que quebrou | menor correção | prompt ou infra |
| 2026-09-26 | Whisper inseriu palavra duplicada fora de ordem (m7-es b04, "LUCIA" 120s→110s) → legenda longa sobreposta, check falhou | Descartar palavras que voltam >1 s no tempo antes de montar legendas; re-render do bloco | infra |
| 2026-09-26 | Correção do palco vazio no v2 (`box.contains` em alvo de tween) quebrou cenas com contador: alvo era objeto JS → exceção → cena em branco (72% vazio) | Filtrar `el instanceof Node`; validar com `hyperframes snapshot` antes de render completo | prompt |
| 2026-09-25 | Whisper (Groq) pulou 27 s de fala no bloco m7 pt-b02 → alinhamento 0,894 < 0,90, render parou | Transcrever só o trecho sem palavras e encaixar com offset; re-render do bloco (sem novo HeyGen) | infra |
| 2026-09-25 | Título do comparativo (ffmpeg drawtext) truncado/tofu com acentos e "·" | Texto de sobreposição do ffmpeg só em ASCII (acentos ficam no HTML/HyperFrames) | infra |
| 2026-09-25 | oswork-v62: painel estático (título+3 rótulos animam em 1,3s, cena de ~60s parada) e legenda do Whisper com nomes errados ("Neymar Dunner", "ia"→"inteligência artificial") | Roteiro visual com deixas faladas (`visual_files`, `build_visual_block.py`) cronometradas pelas palavras do Whisper; legenda com o texto do roteiro | prompt |
| 2026-09-25 | Vídeos oswork-quick/completo soaram como leitura de página (título repetido, frases telegráficas) | Roteiro falado escrito por módulo em scene_files; nunca narrar texto raspado da página | prompt |
| 2026-09-24 | Imagem do Nei esticada na hero (atributo height=720 fixo com width:100%) | CSS height:auto + aspect-ratio + object-fit:cover no img | prompt |
| 2026-09-23 | Timeout de consulta HeyGen interrompeu fila após bloco 12 | Retry somente do GET, reconciliar ID baixado e retomar blocos 13–14 | infra |
| 2026-09-23 | Guia excedeu 390px por comandos e navegação | Permitir quebra de comandos e wrap da navegação | prompt |
| 2026-09-23 | Placeholder composto permaneceu na hero | Preencher o título e validar ausência de chaves duplas | prompt |
| 2026-09-23 | Fonte forçada alargou texto do SVG | Preservar fonte original dos diagramas | prompt |
| 2026-09-23 | Browser sem XServer antes de abrir página | Xvfb supervisionado e preflight xdpyinfo | infra |
| 2026-09-23 | Criação de guia/assets antes da pasta pai | Usar mkdir com parents=True | infra |
