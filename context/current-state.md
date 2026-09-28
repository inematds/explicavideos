# Concluído — v2.0.0 (2026-09-25)
Motor v2 (animação explicativa por deixas faladas) em `engine/v2/`; v1 intacto e em uso pela produção OSWork v6.2 (outra sessão).
OSWork completo refeito em v2 e publicado (release video-v2.0.0, 1h05m55s, 122 cenas, 14 blocos): https://inematds.github.io/oswork/videos/ — v1 preservado no release video-v1.0.0.
Recibos: docs/video-publication.json (v2) e docs/video-publication-v1.json. Roteiros visuais: examples/oswork-v2-visual/.
Portal: docs/portal-publication.json.

# LOOP-R em vídeo (2026-09-28)
- 15 vídeos (5 trilhas × PT/EN/ES), configs `examples/loop-r-*.json` (v1) e `*-v2.json`; saída em `~/projetos/output/loop-r-videos/`.
- Orquestração lá: `orquestra.py` (original), `orquestra_pt.py`, `orquestra_multi.py` (envio em série, 2 renders, tudo em `explica.slice`), avisos pelo bot v3 (`notify_v3.mjs`).
- Publicação: NÃO usar `publish_finished.py` (1 vídeo por repo, sobrescreve `videos/index.html`). Usar `publica_loop_r.py` (idempotente): release `video-v2.0.0` em inematds/loop-r + https://inematds.github.io/loop-r/videos/ (index/en/es).
- PT T2–T5 publicados em 28/09; T1 PT e EN/ES em produção pelo `loop-r-multi-orquestra`.
