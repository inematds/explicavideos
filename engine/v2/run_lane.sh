#!/usr/bin/env bash
# Fila de produção v2: para cada bloco, hyperframes check (tem de passar) e depois render verificado.
# Uso: EXPLICAVIDEOS_CONFIG=examples/oswork-v2.json engine/v2/run_lane.sh 1 4 7 ...
set -uo pipefail
cd "$(dirname "$0")/../.."
OUT=$(python3 -c "import json,os;print(json.load(open(os.environ['EXPLICAVIDEOS_CONFIG']))['output'])")
for n in "$@"; do
  key=$(printf 'pt-b%02d' "$n")
  log="$OUT/logs/check-$key.log"
  (cd "$OUT/final/$key" && timeout 3600 npx --yes hyperframes@0.8.77 check --timeout 90000 >"$log" 2>&1)
  if ! grep -q "Check passed" "$log"; then echo "$key CHECK FALHOU (ver $log)"; continue; fi
  python3 engine/v2/produce.py "$n" || echo "$key RENDER FALHOU"
done
echo "fila $* concluída"
