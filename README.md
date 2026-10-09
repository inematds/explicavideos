# Explicavideos

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

Processo reproduzível para vídeos explicativos com avatar e voz do Nei, ilustrações, capítulos e legendas. Derivado das produções concluídas do Astra Básico e OSWork Quick.

[Guia de uso](https://inematds.github.io/explicavideos/guia/) · [Fonte OSWork](https://inematds.github.io/oswork/)

## Fluxo real

Fonte → cenas com cobertura → blocos de até 4.400 caracteres → HeyGen Studio pela assinatura → download → transcrição Groq com tempos por palavra → composição HyperFrames → validação → renderização → concatenação → GitHub Release e player → bot v3.

O adaptador OSWork cobre os 48 tópicos, todos os campos explicativos, oito laboratórios e revisões em 122 cenas. Primeira produção: português. O motor aceita PT/ES/EN; outros idiomas precisam de arquivos de cenas revisados, não são traduzidos automaticamente.

## Operação

Requer Python 3 com requests e beautifulsoup4, Node, FFmpeg, gh autenticado, systemd de usuário, Xvfb e o perfil HeyGen autenticado. O adaptador de browser usa o Playwright instalado no inemaccbot. Esta versão é executável no ambiente INEMA; ajuste caminhos para outra máquina. Não é um serviço público.

```bash
python3 explica.py --config examples/oswork.json prepare
python3 explica.py --config examples/oswork.json preview
python3 engine/check_layouts.py
python3 explica.py --config examples/oswork.json start
python3 explica.py --config examples/oswork.json status
journalctl --user -u explica-oswork-completo-submit -n 20 --no-pager
```

`prepare` não sobrescreve produções já iniciadas. `start` lança cinco serviços persistentes; não interrompe os já ativos. Não reinicie uma submissão `needs_review`: confira primeiro se existe um ID no HeyGen. A produção em andamento já está preparada; use `status`, não `prepare`.

## Formato v2: animação explicativa (2.0.0)

> 2.7.7: shot `media` com `calm: true` (troca por dissolve, ilustração inteira na moldura, aproximação lenta) e `cont`+`from` (a câmera desliza na mesma imagem em vez de cortar). Opcional; vídeos antigos não mudam.

> 2.6.7: `submit.py` espera o perfil do HeyGen ficar livre (SingletonLock de outra produção) antes de abrir o navegador, em vez de deixar o bloco em `needs_review`.

> 2.6.6: 16:9 também precisa de gancho — `build_block --strict` reprova o bloco 1 que não abre com shot `hook` em `"@start"` (o 1º shot em 0 s ainda entra animado e o frame 0 sai vazio); `"cold_open": true` na config quando a abertura com thumb + imagem + frase de impacto é montada depois (receita em `engine/v2/AUTHORING.md`), `"allow_cold_start": true` só de propósito.

> 2.5.6: reel — topo nunca vazio (1º shot ≤ 0,5 s da 2ª cena em diante), palavras interpoladas rastreáveis no relatório (`interpolated`) com equivalências do ASR (IA ↔ inteligência artificial, inema.club ↔ inema ponto club…), avatar copiado no pacote, bullets em coluna ~1,6× maiores e margem de 6%, e `publish_finished.py` exigindo `APROVADO_REEL` com o sha do MP4 montado.
>
> 2.4.6: correções da auditoria Astra (01/10): marcador `@start` só no `hook` ("start" volta a ser deixa comum nos outros shots); composições só trocadas depois de todas as cenas validarem; SRT sem cue de duração zero quando dois grupos começam juntos; mídia gravada como `<hash>-nome` (sem colisão) e zoom que nunca deixa faixa vazia; `punch_at`/`strike_at` não contam como mudança de conteúdo; `reel_profile` exige `aspect 9:16`; `header: true` chega ao runtime; pisos do v1 inclusivos; fps e perfis lidos do mesmo contrato que o QA. Fora do reel, `--strict` com fallback volta a só avisar.
>
> 2.4.3: **reel** — `"reel_profile"` (divulgacao | tutorial | mini-aula, contrato do makeshorts) liga: shot `hook` visível no frame 0, shot `media` (print real com zoom e destaques), legenda de até 3 palavras em 70 px, sem cabeçalho no topo, aviso de trecho parado > 4 s (e `--strict` reprovando no reel), render 30 fps, −14 LUFS e QA do makeshorts com folha de quadros. Fora do reel, nada muda. Detalhes em `engine/v2/AUTHORING.md`.
>
> 2.3.3: modo vertical 9:16 no v2 — `"aspect": "9:16"` na config v2 gera 1080×1920 (Reels/Shorts): as cenas continuam desenhadas em 1920×1080 com todos os primitivos, a área útil é escalada para o topo, a legenda (46 px, 2 linhas) fica na zona segura e o avatar 16:9 recortado ocupa a faixa de baixo; coluna direita (CENA n/N, PARA LEVAR) não aparece. Sem `aspect`, tudo igual (16:9). Para blocos curtos, a config v1 aceita `min_block_seconds` (padrão 60) e `min_words` (padrão 100), os pisos do download e da transcrição. Primeiro uso: 9 shorts das áreas do eventos.inema.pro (`examples/eventos-shorts-*.json` e `*-v2.json`).
>
> 2.2.3: Whisper local — trechos pulados (buracos > 3 s entre palavras) são retranscritos sozinhos, com até 3 inícios; a checagem de alinhamento (v1 e v2) conta como acerto número falado em dígitos ("83%") contra o roteiro por extenso. LOOP-R PT: 10 blocos reprovados entre 0,79 e 0,88 passaram para 0,97–0,99.
>
> 2.2.2: os serviços (`start`) sobem dentro de `explica.slice` (`~/.config/systemd/user/explica.slice`: MemoryMax=40G, sem swap). Se o lote de renders estourar, o kernel mata um render, não os terminais da sessão (incidente de 2026-09-27 04:01).
>
> 2.2.1: `"transcriber": "whisper-local"` na config troca a Groq pelo Whisper large-v3 local (um processo por vez, lock em /tmp; `whisper_prompt` para nomes próprios) e `"balanced_blocks": true` equilibra os blocos para não sobrar um último bloco curto (< 60 s). Sem as chaves, o comportamento é o anterior. Primeiro uso: LOOP-R (`examples/loop-r-*.json`).
>
> 2.1.1: v2 em PT/EN/ES (rótulos fixos e `lang` por idioma; `setup_output` aceita v1 de qualquer idioma) e regra de autoria "nenhuma moldura vazia por mais de 3 s".
>
> 2.0.1: o shot anterior fica na tela até o próximo mostrar conteúdo (rótulos não contam) e o título grande da cena espera o primeiro conteúdo — palco vazio medido caiu de 26% para 17% no OSWork v6.2 M1; o que resta são molduras com pouco conteúdo, a resolver no roteiro visual.

No v2, o visual explica o que está sendo falado, no instante da fala. Cada cena recebe um roteiro visual (`<output>/visual-v2/pt-bNN.json`), com shots de 21 primitivos animados em `engine/v2/runtime/v2.js`. Todo tempo é uma **deixa falada**, resolvida pela transcrição real. A legenda usa a grafia do roteiro, e o avatar e o áudio da produção v1 são reaproveitados, sem nova geração no HeyGen. Regras e catálogo: [engine/v2/AUTHORING.md](engine/v2/AUTHORING.md). Exemplo aprovado: `visual-v2/pt-b01.json` do OSWork.

```bash
export EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json
python3 engine/v2/setup_output.py            # novo diretório de saída; o v1 não é tocado
python3 engine/v2/build_block.py 1 --strict   # deixas → tempos, 0 avisos, lacunas > 10 s acusadas
engine/v2/run_lane.sh 1 2 3                   # hyperframes check + render verificado por bloco; sai ≠0 se algum bloco falhar (2.4.5)
python3 engine/assemble_languages.py && python3 engine/publish_finished.py
```

O motor v1 (`explica.py`, `engine/*.py`) continua igual e disponível. A versão anterior do vídeo OSWork fica no release `video-v1.0.0`.

## Configuração para outros vídeos

Copie examples/oswork.json e altere id, title, source_repo, output, github_repo e release_tag. Para conteúdo que não é OSWork, forneça `scene_files` com caminhos por idioma, por exemplo `{"pt":"/caminho/lesson-pt.json"}`. Cada cena contém title, chapter, speech, labels, source, kind e takeaway; svg é opcional. O roteiro precisa ser revisado antes de `start`.

As mídias e os estados ficam em `~/projetos/output/<id>/`. O repositório contém o motor, configurações, documentação e recursos visuais; não contém credenciais nem MP4s.

## Qualidade e recuperação

- Fonte congelada em JSON, cobertura por tópico e SHA-256 de cada bloco.
- Nunca repetir automaticamente submissão com resultado ambíguo.
- Avatar: template TEMPLATE-AVATAR16, Nei, voz INEMATIME, Avatar III.
- Transcrição real; correspondência de palavras acima de 90% para render/publicação.
- Composição 1920×1080, 25 fps; legendas sem sobreposição.
- Conferência HyperFrames, duração real, presença de áudio e decodificação FFmpeg.
- MP4 e SRT em Release; player com capítulos e VTT no próprio curso.
- Aviso final no bot v3 somente depois de publicação e recibo do portal.

`verification/production.json` registra falhas por bloco. Corrija a causa e remova apenas o estado daquele bloco para retomá-lo, preservando seu ID HeyGen. Serviços têm janela de 12 horas; acompanhe com status e journalctl. Não há retentativa cega de geração.

## Custos

Geração do avatar usa a sessão da assinatura HeyGen no navegador. A API HeyGen é usada só para consulta; Groq cobra transcrição conforme a conta. HyperFrames renderiza localmente. O motor não chama um LLM para coordenar cada etapa. Assinatura não significa uso ilimitado; este projeto registra duração e IDs, mas não calcula a fatura dos provedores.

## HeyGen: como o motor gera, confere e baixa (opções)

**Modelo atual — o padrão, e o que está em produção.** Não mudou.

| etapa | como é feito hoje | custo |
|---|---|---|
| gerar o avatar | script Playwright no **estúdio** do HeyGen (`engine/heygen-studio.mjs`): clona o `TEMPLATE-AVATAR16`, troca título e fala, "Gerar" → modal → "Enviar" | assinatura (sessão do navegador, perfil `~/.cache/inemaccbot/perfil-heygen`, tela `:99`) |
| conferir se entrou na fila | `submit.py` lê `GET /v3/videos/<id>` na **API** | só leitura; não gera cobrança |
| acompanhar até ficar pronto | `monitor.py` lê a mesma rota da **API** a cada 60 s | só leitura |
| baixar o MP4 | `monitor.py` baixa o `video_url` que a **API** devolve | só leitura |

A chave usada na leitura é a `HEYGEN_API_KEY` de `~/projetos/openpcbotv2/.env`. Cada produção registra essa permissão no `APROVADO_HEYGEN` ("API HeyGen só status/download").

**Opção em estudo — estúdio de ponta a ponta (ainda NÃO implementada).** Mesma rota `| estudio` do [promoavatar3](https://github.com/inematds/promoavatar3), levada até o fim: conferir o status e baixar também pelo estúdio, pelo título exato, sem nenhuma chamada de API.

| | modelo atual (API para ler) | estúdio de ponta a ponta |
|---|---|---|
| chave de API | usada para ler | nenhuma |
| status que enxerga | o da API — **rascunho aparece como `pending`** | o da tela: Draft, na fila, processando, pronto, falhou |
| velocidade da checagem | milissegundos, a cada 60 s | segundos (abre o navegador), a cada 5–10 min |
| o que pode quebrar | a chave (vencida, sem permissão) | a sessão do perfil expira; o layout do HeyGen muda |
| navegador `:99` | só no envio | envio e checagem disputam a mesma tela: um de cada vez |

**Por que a opção existe — o caso de 29/09/2026.** Três blocos do OSWork v6.2 (M3 PT b02, M6 PT b01, M6 EN b03) ficaram 4 dias como `pending` na API. No estúdio, os três estavam como **Draft**: o "Enviar" do modal não pegou (o modal veio em inglês, "Submit"), o script registrou o ID mesmo assim, e a API responde `pending` para rascunho. Nada foi gerado nem cobrado. O monitor não tinha como perceber; o estúdio mostra na hora. Conferência só de leitura em `~/projetos/output/oswork-v62/verification-estudio-2026-09-29/`.

**Proteção mínima que vale nos dois modelos (pendente):** depois do "Enviar", o `heygen-studio.mjs` confirma em Projetos que o título saiu de **Draft**; se não saiu, marca `needs_review` em vez de gravar o ID como enviado.

Destravar um rascunho é **gerar vídeo**: só com autorização explícita do Nei (novo `APROVADO_HEYGEN` com blocos e minutos). Nunca reenviar sem antes olhar o estúdio: se o título já está fora de Draft, o envio anterior valeu e já foi cobrado.

## Referências e licenças

Pipeline adaptado de astrabasico e oswork-quick. Fontes locais de layout: Montserrat e DejaVu; animação GSAP. Conteúdo educacional e diagramas pertencem ao curso fonte. Preserve as licenças dos recursos ao redistribuir.

## Verificação

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q engine
```


## Entrega OSWork

[Assistir ao vídeo completo](https://inematds.github.io/oswork/videos/). Recibo de publicação em docs/video-publication.json.
