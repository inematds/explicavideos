# Explicavideos

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

> 2.1.1: v2 em PT/EN/ES (rótulos fixos e `lang` por idioma; `setup_output` aceita v1 de qualquer idioma) e regra de autoria "nenhuma moldura vazia por mais de 3 s".
>
> 2.0.1: o shot anterior fica na tela até o próximo mostrar conteúdo (rótulos não contam) e o título grande da cena espera o primeiro conteúdo — palco vazio medido caiu de 26% para 17% no OSWork v6.2 M1; o que resta são molduras com pouco conteúdo, a resolver no roteiro visual.

No v2, o visual explica o que está sendo falado, no instante da fala. Cada cena recebe um roteiro visual (`<output>/visual-v2/pt-bNN.json`), com shots de 21 primitivos animados em `engine/v2/runtime/v2.js`. Todo tempo é uma **deixa falada**, resolvida pela transcrição real. A legenda usa a grafia do roteiro, e o avatar e o áudio da produção v1 são reaproveitados, sem nova geração no HeyGen. Regras e catálogo: [engine/v2/AUTHORING.md](engine/v2/AUTHORING.md). Exemplo aprovado: `visual-v2/pt-b01.json` do OSWork.

```bash
export EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json
python3 engine/v2/setup_output.py            # novo diretório de saída; o v1 não é tocado
python3 engine/v2/build_block.py 1 --strict   # deixas → tempos, 0 avisos, lacunas > 10 s acusadas
engine/v2/run_lane.sh 1 2 3                   # hyperframes check + render 25 fps verificado por bloco
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

## Referências e licenças

Pipeline adaptado de astrabasico e oswork-quick. Fontes locais de layout: Montserrat e DejaVu; animação GSAP. Conteúdo educacional e diagramas pertencem ao curso fonte. Preserve as licenças dos recursos ao redistribuir.

## Verificação

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q engine
```


## Entrega OSWork

[Assistir ao vídeo completo](https://inematds.github.io/oswork/videos/). Recibo de publicação em docs/video-publication.json.
