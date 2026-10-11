# Goal — perfil-viral

- **Início:** 2026-10-11 05:24 · **Agente:** Claude (sessão wifi d1019a25) · trabalho no worktree `~/projetos/explicavideos-viral` (branch `perfil-viral`)
- **Tetos:** tempo 6 h · render sempre em `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0` · sem HeyGen, sem API, sem vídeo (b-roll só imagem local)

## Resultado
O explicavideos v2 ganha o perfil `"profile_visual": "viral"` (layout moderno, tela cheia, muito motion, peças vindas do finviral/eventosextremospub/clima-sul/filmarca), um padrão escrito (`engine/v2/PADRAO-VIRAL.md`) e um QA que reprova vídeo parado/vazio; piloto = TeraFab refeito com a mesma gravação, enviado ao Nei para aprovação.

## Critérios de pronto (verificáveis)

**Função**
- [ ] `EXPLICAVIDEOS_CONFIG=examples/terafab-viral-v2.json python3 engine/v2/build_block.py 1 --strict` → exit 0, 0 warnings
- [ ] o mesmo para `terafab-viral-v2-916.json` → exit 0
- [ ] `python3 engine/v2/qa_viral.py <mp4>` nos dois MP4 do piloto → `APROVADO`, com as checagens: nenhum quadro (amostra a cada 0,5 s) com > 40% de área "vazia" (fundo liso); nenhum trecho > 2 s sem mudança visual (diferença entre quadros); contact sheet gravada em `verification/`
- [ ] `grep -o '"type": "[a-z_]*"' visual/terafab-viral.json | sort -u` inclui `bignum`, `escala`, `mapa`, `cinetica`, `capitulo` (≥ 5 peças novas usadas no piloto)
- [ ] piloto 16:9 e 9:16 com duração 61,7 ± 0,3 s (`ffprobe`)

**Regressão**
- [ ] `python3 -m pytest tests -q` no worktree → mesmo número de testes passando que em `main` (base: anotar no state.md) e nenhum falhando a mais
- [ ] build do `examples/terafab-v2.json` (perfil aula, sem `profile_visual`) no worktree gera HTML de cena idêntico ao do `main` (`diff -r` dos `final/pt-b01/*.html` → vazio)

**Limite**
- [ ] `git -C ~/projetos/explicavideos status --short engine/` → só as mudanças da outra sessão (nada meu no main antes do merge aprovado)
- [ ] nenhuma chamada HeyGen/API/Magnific; nenhuma troca no YouTube/portal sem aprovação do Nei

**Teste rápido por ciclo:** build `--strict` + snapshot de 4 quadros da cena mexida (HyperFrames snapshot ou render curto)
**Teste completo no final:** pytest + render dos 2 pilotos + qa_viral + folha de quadros vista por mim + envio ao bot v3

## Portão humano
O Nei aprova o piloto no bot antes de: merge no `main`, troca do vídeo no lives1/portal, `modo viral` no refazvideo.
