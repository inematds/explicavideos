# Estado — 2026-09-23
Motor criado, OSWork PT preparado: 48 tópicos, 122 cenas, 14 blocos. Geração assíncrona via HeyGen; não declarar vídeo entregue antes de verification/publication.json e telegram-final.json. Configuração em examples/oswork.json. Portal autorizado. CLI HyperFrames atualizado de 0.8.60 para 0.8.66; motor anterior usava 0.8.58.

Portal 51c496e, busca 5204649, PRO df4dc47: pushes concluídos; guia HTTP 200. 6 testes do motor, 11 do portal e 41 da base aprovados. 18.380 IDs anteriores preservados, novo total 18.381. Produção do vídeo assíncrona; comandos `python3 explica.py status` e `journalctl --user -u explica-oswork-completo-submit`. Todos os cinco serviços lançados.

Retomada 23/09 às 23:46: 12/14 blocos renderizados (59min27s); fila de envio havia parado por timeout de consulta após bloco 12. ID reconciliado com download, sem duplicar; serviços retomados para blocos 13–14. Fix 9547b82: retry de leitura e alerta se serviço de envio parar com blocos pendentes. Oito testes aprovados. Ainda sem publicação do vídeo completo.
