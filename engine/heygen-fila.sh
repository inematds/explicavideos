#!/usr/bin/env bash
# Quem está com o perfil do HeyGen (estúdio) agora, quem está na fila e o uso recente.
# uso: engine/heygen-fila.sh [N linhas do histórico, padrão 15]
PERFIL="${HEYGEN_PERFIL:-$HOME/.cache/inemaccbot/perfil-heygen}"
LOG="$HOME/.cache/inemaccbot/heygen-uso.log"
dono=$(readlink "$PERFIL/SingletonLock" 2>/dev/null | sed 's/.*-//')
echo "== perfil: $PERFIL"
if [ -n "$dono" ] && kill -0 "$dono" 2>/dev/null; then
  pai=$(ps -o ppid= -p "$dono" | tr -d ' ')
  echo "EM USO pelo Chrome pid $dono, desde $(ps -o lstart= -p "$dono")"
  echo "  aberto por: $(ps -o args= -p "$pai" | cut -c1-200)"
  echo "  pasta: $(readlink /proc/"$pai"/cwd 2>/dev/null)"
else
  echo "LIVRE"
fi
echo "== processos do estúdio (o que não é o dono está na fila)"
pgrep -af 'heygen-studio.mjs|heygen-estudio-baixar.mjs' | grep -v pgrep | cut -c1-200 || echo "(nenhum)"
echo "== últimos usos ($LOG)"
tail -n "${1:-15}" "$LOG" 2>/dev/null || echo "(sem histórico ainda)"
