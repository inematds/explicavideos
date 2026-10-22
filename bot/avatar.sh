#!/usr/bin/env bash
# Fase `avatar` do /explicavideo no inemaccbot (22/10/2026): envia o bloco ao estúdio HeyGen (assinatura),
# baixa pela API de leitura e roda o v1 (render + montagem) no explica.slice. Mesma cadeia da Thwaites (21/10/2026).
# Uso: bot/avatar.sh <pasta-do-bot>   · última linha "pasta: <pasta>" (a fase seguinte lê) ou "erro: …" e sai 1.
# Nunca reenvia: envio sem id no log = ambíguo = para e avisa (AGENTS.md).
set -uo pipefail
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH" DISPLAY="${DISPLAY:-:99}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
B=$(realpath "${1:?uso: avatar.sh <pasta-do-bot>}")
EV=${EXPLICAVIDEOS:-$HOME/projetos/explicavideos}
log(){ echo "$(date +%H:%M:%S) $*"; }
fim(){ echo "erro: $*"; exit 1; }
campo(){ python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get(sys.argv[2],''))" "$B/pedido.json" "$1"; }

[ -s "$B/pedido.json" ] && [ -s "$B/v1.json" ] || fim "faltam pedido.json/v1.json em $B (a fase ficha não terminou)"
ID=$(campo id); REF=$(campo ref); PEDIDO=$(campo pedido)
O=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['output'])" "$B/v1.json")
M="$O/blocos/manifest.json"
[ -s "$M" ] || fim "sem $M (o prepare não rodou)"
N=$(python3 -c "import json,sys;print(len(json.load(open(sys.argv[1]))))" "$M")
[ "$N" = 1 ] || fim "o roteiro deu $N blocos; pelo bot vai só 1 bloco (≤ 4.400 caracteres)"
CH=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[0]['chars'])" "$M")
MIN=$(( (CH + 799) / 800 ))

# O comando do Nei no bot é o OK do avatar desta produção (Nei, 22/10/2026).
[ -s "$O/APROVADO_HEYGEN" ] || printf '%s Nei pelo /explicavideo no inemaccbot (%s): "%s"; o comando vale como OK do avatar desta produção. 1 bloco PT, %s caracteres, ~%s min. Estúdio gera (assinatura, TEMPLATE-AVATAR16); API HeyGen só status/download.\n' \
  "$(date +%F)" "$REF" "$PEDIDO" "$CH" "$MIN" > "$O/APROVADO_HEYGEN"

# 1. envio (pula se o manifest já tem id: retomada)
mkdir -p "$O/verification"
SUB="$O/verification/submit-pt-01.log"
if [ -z "$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[0].get('id',''))" "$M")" ]; then
  [ -s "$SUB" ] && fim "já houve um envio sem id ($SUB): olhe Projetos no estúdio antes de qualquer reenvio"
  TIT=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))[0]['title'])" "$M")
  log "enviando $TIT ao estúdio (espera o perfil do HeyGen ficar livre)"
  (cd "$EV" && timeout 12000 node engine/heygen-studio.mjs --titulo "$TIT" --fala-arquivo "$O/blocos/pt-b01.txt" \
     --perfil "$HOME/.cache/inemaccbot/perfil-heygen" --template TEMPLATE-AVATAR16) > "$SUB" 2>&1
  rc=$?
  HID=$(grep -o 'create-v4/[a-f0-9]\{32\}' "$SUB" | head -1 | cut -d/ -f2)
  [ -n "$HID" ] || fim "envio sem id (rc=$rc, ver $SUB): NÃO reenvio; olhe Projetos no estúdio"
  grep -iq draft "$SUB" && fim "o log do envio fala em Draft ($SUB): confira no estúdio antes de seguir"
  python3 - "$M" "$HID" <<'PY'
import json,sys
p=sys.argv[1];d=json.load(open(p));d[0].update(status='submitted',id=sys.argv[2],via='estudio')
open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2))
PY
  log "enviado: id $HID"
fi

# 2. download pela API de leitura (baixa_blocos espera até 2 h por bloco)
for t in 1 2 3 4; do
  [ -s "$O/assets/nei-pt-b01.mp4" ] && break
  "$HOME/projetos/refazvideo/ferramentas/baixa_blocos.sh" "$(dirname "$O")" > "$O/baixa.log" 2>&1 && break
  log "download falhou ($(tail -1 "$O/baixa.log")); tento de novo em 5 min"; sleep 300
done
[ -s "$O/assets/nei-pt-b01.mp4" ] || fim "avatar não baixou (ver $O/baixa.log)"
log "avatar ok $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$O/assets/nei-pt-b01.mp4")s"

# 3. v1: render + montagem (transcrição real) no explica.slice, fora do processo do bot
if [ ! -f "$O/verification/assembled-pt.json" ]; then
  for s in render:produce_blocks.py assemble:wait_assembly.py; do
    systemd-run --user --collect --unit="explica-$ID-${s%%:*}-$(date +%s)" --slice=explica.slice -p MemoryMax=16G -p MemorySwapMax=0 \
      --property=WorkingDirectory="$EV" --setenv=EXPLICAVIDEOS_CONFIG="$B/v1.json" /usr/bin/python3 "$EV/engine/${s#*:}" \
      || fim "systemd-run do v1 ${s%%:*} falhou"
  done
  for i in $(seq 1 270); do
    [ -f "$O/verification/assembled-pt.json" ] && break
    grep -q '"failed"' "$O/verification/production.json" 2>/dev/null && fim "v1 falhou: $(tr -d '\n' < "$O/verification/production.json" | cut -c1-300)"
    [ $((i % 15)) = 0 ] && log "v1 rodando ($((i / 3)) min)"
    sleep 20
  done
  [ -f "$O/verification/assembled-pt.json" ] || fim "v1 sem montagem em 1,5 h (ver journalctl --user -u 'explica-$ID-*')"
fi
log "v1 ok (avatar transcrito e montado)"
echo "avatar: $O/assets/nei-pt-b01.mp4"
echo "pasta: $B"
