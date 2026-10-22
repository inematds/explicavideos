#!/usr/bin/env bash
# Fase `entrega` do /explicavideo no inemaccbot (22/10/2026): render v2 de cada formato pedido → som → QA → publica
# no(s) canal(is) do pedido (yt-pubx) → link no inemaytbot → arquivo no bot v3 → BOT-FIM.md.
# Mesma cadeia e publicação da Thwaites (cadeia.sh + publica.sh, 21/10/2026).
# Uso: bot/entrega.sh <pasta-do-bot>   · última linha "fim: <BOT-FIM.md>" ou "erro: …" e sai 1.
set -uo pipefail
export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH" DISPLAY="${DISPLAY:-:99}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
B=$(realpath "${1:?uso: entrega.sh <pasta-do-bot>}")
EV=${EXPLICAVIDEOS:-$HOME/projetos/explicavideos}
YT=${YTPUBX:-$HOME/projetos/yt-pubx/yt-pubx}
BOTV3=${BOTV3:-$HOME/projetos/refazvideo/ferramentas/enviar_bot_v3.mjs}
log(){ echo "$(date +%H:%M:%S) $*"; }
fim(){ echo "erro: $*"; exit 1; }
campo(){ python3 -c "import json,sys;v=json.load(open(sys.argv[1])).get(sys.argv[2],'');print(' '.join(v) if isinstance(v,list) else v)" "$B/pedido.json" "$1"; }
ytbot(){ [ -n "${SEM_ENVIO:-}" ] && { echo "[ensaio] inemaytbot: $1"; return 0; }; python3 - "$1" <<'EOF'
import json, sys, urllib.request, urllib.parse
from pathlib import Path
tok = next(l.split("=", 1)[1].strip().strip('"') for l in (Path.home() / "projetos/yt-pub-livesx-master/config/.env").read_text().splitlines() if l.startswith("TELEGRAM_NOTIFY_BOT_TOKEN="))
chat = (Path.home() / ".config/aventurasinemavideo/telegram_chat").read_text().strip()
d = urllib.parse.urlencode({"chat_id": chat, "text": sys.argv[1], "disable_web_page_preview": "true"}).encode()
r = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", d, timeout=60))
assert r.get("ok"), r
EOF
}

[ -s "$B/pedido.json" ] || fim "sem $B/pedido.json"
[ -f "$B/VISUAL-OK" ] || fim "a fase visual não liberou o render (sem $B/VISUAL-OK)"
ID=$(campo id); TIT=$(campo titulo); CTX=$(campo contexto_yt); CANAIS=$(campo canais); TRILHA=$(campo trilha); PERFIL=$(campo perfil)
[ -n "$CANAIS" ] || CANAIS=lives1
[ -n "$TRILHA" ] || TRILHA=noticia-urgente
OUT=$HOME/projetos/output/$ID; E=$OUT/entrega; mkdir -p "$E"
cp "$B"/pedido.json "$B"/roteiro-pt.json "$B"/RESUMO.md "$OUT/" 2>/dev/null
LINHAS=(); FALHAS=(); CARQ=(); [ -s "$B/yt.txt" ] && CARQ=(--contexto-arquivo "$B/yt.txt")

for cfg in "$B/v2.json" "$B/v2-916.json"; do
  [ -s "$cfg" ] || continue
  V=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['output'])" "$cfg")
  if [ "${cfg##*/}" = v2-916.json ]; then FMT=9x16; NOME=$ID-916; else FMT=16x9; NOME=$ID; fi
  F=$E/$NOME.mp4
  if [ ! -s "$F" ]; then
    log "render $FMT (≈ 20 min por 3 min de vídeo)"
    rm -f "$V/final/$ID-pt.mp4"
    systemd-run --user --scope --slice=explica.slice -p MemoryMax=16G -p MemorySwapMax=0 env EXPLICAVIDEOS_CONFIG="$cfg" \
      bash -c "cd '$EV' && engine/v2/run_lane.sh 1 && python3 engine/assemble_languages.py" > "$V/render.log" 2>&1 \
      || fim "render $FMT falhou: $(tail -3 "$V/render.log" | tr '\n' ' ' | cut -c1-300)"
    [ -s "$V/final/$ID-pt.mp4" ] || fim "render $FMT terminou sem $V/final/$ID-pt.mp4"
    if [ "$PERFIL" = aula ] && [ $FMT = 16x9 ]; then cp "$V/final/$ID-pt.mp4" "$F"; else
      (cd "$EV" && python3 engine/v2/som_viral.py "$V/final/pt-b01" "$V/final/$ID-pt.mp4" "$F" --trilha="$TRILHA" --sem-efeitos) > "$V/som.log" 2>&1 \
        || fim "som $FMT falhou: $(tail -2 "$V/som.log" | tr '\n' ' ')"
    fi
  fi
  QA=0; if [ "$PERFIL" != aula ] || [ $FMT = 9x16 ]; then
    (cd "$EV" && python3 engine/v2/qa_viral.py "$F" --saida="$V/verification") > "$V/qa.log" 2>&1; QA=$?; fi
  [ $QA = 0 ] || fim "QA reprovou o $FMT: $(tail -3 "$V/qa.log" | tr '\n' ' ' | cut -c1-300) — vídeo em $F, nada publicado"
  DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$F" | cut -d. -f1)
  log "$FMT pronto: ${DUR}s"

  # publicação: 16:9 leva a capa como thumb; 9:16 é Short, sem thumb (Nei 07/10/2026)
  for C in $CANAIS; do
    MARCA="$OUT/youtube-$C-$FMT.txt"
    if [ -s "$MARCA" ]; then YID=$(cat "$MARCA"); else
      THUMB=(--sem-thumb); [ $FMT = 16x9 ] && THUMB=(); [ $FMT = 16x9 ] && [ -s "$OUT/media/capa.png" ] && {
        ffmpeg -v error -y -i "$OUT/media/capa.png" -vf scale=1280:720 -q:v 3 "$E/thumb.jpg" && THUMB=(--thumb "$E/thumb.jpg"); }
      if [ -n "${SEM_ENVIO:-}" ]; then echo "[ensaio] yt-pubx publicar $F --canal $C"; YID=ENSAIO; else
        timeout 2400 "$YT" publicar "$F" --canal "$C" --title "$(echo "$TIT" | cut -c1-100)" --contexto "$CTX" "${CARQ[@]}" "${THUMB[@]}" > "$OUT/publicar-$C-$FMT.log" 2>&1
        YID=$(grep -o 'watch?v=[A-Za-z0-9_-]*\|shorts/[A-Za-z0-9_-]*' "$OUT/publicar-$C-$FMT.log" | tail -1 | sed 's#.*[=/]##')
      fi
      [ -n "$YID" ] && [ -z "${SEM_ENVIO:-}" ] && echo "$YID" > "$MARCA"
    fi
    if [ -n "$YID" ]; then
      U="https://www.youtube.com/watch?v=$YID"; [ $FMT = 9x16 ] && U="https://youtube.com/shorts/$YID"
      LINHAS+=("- $FMT · ${DUR}s · $C: $U")
      [ -s "$MARCA.avisado" ] || { ytbot "Publicado no $C — $TIT ($FMT, $(date +%d/%m/%Y)):
$U" && echo ok > "$MARCA.avisado"; }
    else
      MOT=$(grep -h -i 'erro\|error\|quota\|limit' "$OUT/publicar-$C-$FMT.log" 2>/dev/null | tail -1 | cut -c1-160)
      FALHAS+=("- $FMT · $C: NÃO publicado ($MOT)")
      ytbot "⚠ NÃO publicado no $C ($TIT, $FMT): $MOT" || true
    fi
  done

  # arquivo no bot v3 (sem links; Nei 12/10/2026)
  BX=$E/$NOME-720p.mp4
  if [ $FMT = 16x9 ]; then [ -s "$BX" ] || ffmpeg -v error -y -i "$F" -vf scale=1280:720 -c:v libx264 -b:v 850k -maxrate 1100k -bufsize 2200k -c:a aac -b:a 96k -movflags +faststart "$BX"
  else BX=$F; fi
  if [ -n "${SEM_ENVIO:-}" ]; then echo "[ensaio] bot v3: $BX"; elif [ ! -s "$BX.envio-v3.json" ]; then
    node "$BOTV3" "$BX" "$TIT · explicavideo $FMT · ${DUR}s · com avatar · $CANAIS" >> "$OUT/bot.log" 2>&1 || FALHAS+=("- $FMT: bot v3 falhou (ver $OUT/bot.log)")
  fi
  [ -s "$BX.envio-v3.json" ] && LINHAS+=("  bot v3 msg $(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['message_id'])" "$BX.envio-v3.json")")
done

[ ${#LINHAS[@]} -gt 0 ] || [ ${#FALHAS[@]} -gt 0 ] || fim "nenhum formato para entregar (sem v2.json nem v2-916.json em $B)"
{
  if [ ${#FALHAS[@]} -gt 0 ]; then echo "Falhou em parte: explicavideo $TIT"; else echo "Terminei: explicavideo $TIT"; fi
  echo; printf '%s\n' "${LINHAS[@]}" "${FALHAS[@]}"
  echo; echo "Arquivos: $E"
  echo "Links também no inemaytbot."
} > "$B/BOT-FIM.md"
cp "$B/BOT-FIM.md" "$OUT/"
echo "pasta: $B"
echo "fim: $B/BOT-FIM.md"
