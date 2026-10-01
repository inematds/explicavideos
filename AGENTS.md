# Explicavideos
Leia README.md e context/current-state.md. Autor: inematds <inematds@gmail.com>. Credenciais apenas em runtime. Não repita submissão ambígua ao HeyGen. Não altere o manifesto depois de IDs gerados. Artefatos em output; nunca commitar MP4s ou segredos.

## Ao pedir autorização do HeyGen, explique as opções

Todo pedido de ok ao Nei para gerar ou reenviar avatar (novo `APROVADO_HEYGEN`) diz, em texto, sem menu:
- **o que será gerado:** produção, blocos, idiomas e minutos estimados (~800 caracteres ≈ 1 min);
- **como, no modelo atual (padrão):** gerar pelo estúdio com script, na assinatura; conferir e baixar pela API, só leitura, com a chave do `openpcbotv2/.env`;
- **a alternativa:** estúdio de ponta a ponta, sem chave de API (usada pela 1ª vez em 01/10/2026 no Codex + Claude EN/ES: envio com `engine/heygen-studio.mjs` e conferência/download com `engine/heygen-estudio-baixar.mjs`, rodados à mão, sem `submit.py`/`monitor.py`, que chamam a API; ganhos e riscos no README, seção "HeyGen: como o motor gera, confere e baixa");
- **o que acontece depois:** render, montagem, publicação e portal, tudo local e sem custo.

Bloco `pending` por horas: antes de propor reenvio, olhe Projetos no estúdio, só leitura (modelo: `~/projetos/output/oswork-v62/verification-estudio-2026-09-29/olhar-travados.mjs`). A API chama rascunho de `pending`. Se estiver em Draft, nada foi cobrado; se estiver fora de Draft, o envio anterior valeu e não se reenvia.
