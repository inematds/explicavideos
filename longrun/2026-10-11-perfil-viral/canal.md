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
