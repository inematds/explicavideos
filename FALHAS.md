| data | o que quebrou | menor correção | prompt ou infra |
| 2026-09-24 | Imagem do Nei esticada na hero (atributo height=720 fixo com width:100%) | CSS height:auto + aspect-ratio + object-fit:cover no img | prompt |
| 2026-09-23 | Timeout de consulta HeyGen interrompeu fila após bloco 12 | Retry somente do GET, reconciliar ID baixado e retomar blocos 13–14 | infra |
| 2026-09-23 | Guia excedeu 390px por comandos e navegação | Permitir quebra de comandos e wrap da navegação | prompt |
| 2026-09-23 | Placeholder composto permaneceu na hero | Preencher o título e validar ausência de chaves duplas | prompt |
| 2026-09-23 | Fonte forçada alargou texto do SVG | Preservar fonte original dos diagramas | prompt |
| 2026-09-23 | Browser sem XServer antes de abrir página | Xvfb supervisionado e preflight xdpyinfo | infra |
| 2026-09-23 | Criação de guia/assets antes da pasta pai | Usar mkdir com parents=True | infra |
