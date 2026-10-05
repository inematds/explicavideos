# Concluído — v2.0.0 (2026-09-25)
Motor v2 (animação explicativa por deixas faladas) em `engine/v2/`; v1 intacto e em uso pela produção OSWork v6.2 (outra sessão).
OSWork completo refeito em v2 e publicado (release video-v2.0.0, 1h05m55s, 122 cenas, 14 blocos): https://inematds.github.io/oswork/videos/ — v1 preservado no release video-v1.0.0.
Recibos: docs/video-publication.json (v2) e docs/video-publication-v1.json. Roteiros visuais: examples/oswork-v2-visual/.
Portal: docs/portal-publication.json.

# LOOP-R em vídeo (2026-09-28)
- 15 vídeos (5 trilhas × PT/EN/ES), configs `examples/loop-r-*.json` (v1) e `*-v2.json`; saída em `~/projetos/output/loop-r-videos/`.
- Orquestração lá: `orquestra.py` (original), `orquestra_pt.py`, `orquestra_multi.py` (envio em série, 2 renders, tudo em `explica.slice`), avisos pelo bot v3 (`notify_v3.mjs`).
- Publicação: NÃO usar `publish_finished.py` (1 vídeo por repo, sobrescreve `videos/index.html`). Usar `publica_loop_r.py` (idempotente): release `video-v2.0.0` em inematds/loop-r + https://inematds.github.io/loop-r/videos/ (index/en/es).
- Concluído em 29/09/2026 04:30: 15 de 15 publicados (≈4h13). Lições em FALHAS.md (nome do asset `mp4.stem`, 1 render por vez por causa do Whisper na GPU).

# IA Cultivada em vídeo (2026-09-28)
- 1 vídeo PT, v2 (10min07s, 14 cenas, 2 blocos HeyGen). Configs `examples/iacultivada.json` (v1, só intermediário) e `iacultivada-v2.json`; roteiro e visual-v2 em `~/projetos/output/iacultivada-video/`.
- Publicado: release `video-v2.0.0` em inematds/iacultivada + https://inematds.github.io/iacultivada/videos/ ; feed de projetos do portal (41f774b) e catalog PRO (5a85e06).
- Regra: entrega de explicavideo é sempre v2; no v1 subir só submit/monitor/render/assemble (a etapa publish usa o recibo de portal antigo).

# Codex + Claude em vídeo (2026-09-29)
- Configs `examples/codex-claude.json` (v1) e `codex-claude-v2.json`; saída em `~/projetos/output/codex-claude-video/` (2 blocos HeyGen, alinhamento 0,98/0,94).
- Três versões a partir do v2: completo 16:9 (6min22s), essencial 16:9 (cenas 1-4 + 10-11, 3min25s) e reel 9:16 (cenas 1, 2, 11, 1min31s) — `extras.py` corta nas divisas de cena, sem nova geração.
- Publicação própria (`publica.py`): repo inematds/codex-claude-video, release video-v2.0.0, https://inematds.github.io/codex-claude-video/videos/ + card de projeto no portal.
