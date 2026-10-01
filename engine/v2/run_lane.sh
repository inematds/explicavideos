#!/usr/bin/env bash
# Fila de produção v2: para cada bloco, hyperframes check (tem de passar) e depois render verificado.
# Uso: EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json engine/v2/run_lane.sh 1 4 7 ...
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=$(python3 -c "import json,os;print(json.load(open(os.environ['EXPLICAVIDEOS_CONFIG']))['output'])")
LANG1=$(python3 -c "import json,os;print(json.load(open(os.environ['EXPLICAVIDEOS_CONFIG']))['languages'][0])")
falhas=()
for n in "$@"; do
  key=$(printf '%s-b%02d' "$LANG1" "$n")
  log="$OUT/logs/check-$key.log"
  (cd "$OUT/final/$key" && timeout 3600 npx --yes hyperframes@0.8.77 check --timeout 90000 >"$log" 2>&1)
  if ! grep -q "Check passed" "$log"; then echo "$key CHECK FALHOU (ver $log)"; falhas+=("$key"); continue; fi
  python3 engine/v2/produce.py "$n" || { echo "$key RENDER FALHOU"; falhas+=("$key"); }
done
# 2.4.5: falha na fila sai com código != 0 (antes terminava "concluída" e com sucesso)
if [ ${#falhas[@]} -gt 0 ]; then echo "fila $* com falha: ${falhas[*]}"; exit 1; fi
echo "fila $* concluída"
