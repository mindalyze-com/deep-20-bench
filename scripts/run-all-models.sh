#!/usr/bin/env bash

set -euo pipefail

MODE="${1:-}"

if [[ "$MODE" != "official" && "$MODE" != "experimental" ]]; then
  echo "usage: $0 <official|experimental> [three-digit sequence] [iterations]" >&2
  exit 2
fi

cd "$(dirname "$0")/.."

SEQUENCE="${2:-001}"
ITERATIONS="${3:-3}"
RUN_DATE="${RUN_DATE:-$(date +%Y%m%d)}"
LOG_DIR="benchmark-logs/BX-${RUN_DATE}-${MODE}-ALL-${SEQUENCE}"
# Stagger job launches to decorrelate provider rate-limit bursts across models.
STAGGER_SECONDS="${DEEP20BENCH_STAGGER_SECONDS:-45}"

log() {
  printf '%s.000 %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

mkdir -p "$LOG_DIR"
log "benchmark.batch_context models=all subjects=all logs=$PWD/$LOG_DIR"
pids=()
launched=0

MODEL_IDS="$(
  uv run python -c \
    'import yaml; print(*yaml.safe_load(open("config/models.yaml"))["models"], sep="\n")'
)"

while IFS= read -r model; do
  compact_model="${model//-/}"
  run_id="BX-${RUN_DATE}-${MODE}-${compact_model}-${SEQUENCE}"
  log_file="$LOG_DIR/${model}.log"

  if (( launched > 0 && STAGGER_SECONDS > 0 )); then
    sleep "$STAGGER_SECONDS"
  fi
  log "benchmark.batch.job model=$model status=started execution=$run_id log=$PWD/$log_file"
  (
    if uv run deep20 benchmark run B-0001 \
      --model "$model" \
      --benchmark-mode "$MODE" \
      --run-id "$run_id" \
      --iterations "$ITERATIONS" \
      > "$log_file" 2>&1
    then
      log "benchmark.batch.job model=$model status=completed execution=$run_id log=$PWD/$log_file"
    else
      exit_code=$?
      log "benchmark.batch.job model=$model status=failed exit_code=$exit_code execution=$run_id log=$PWD/$log_file" >&2
      exit "$exit_code"
    fi
  ) &

  pids+=("$!")
  launched=$((launched + 1))
done <<< "$MODEL_IDS"

status=0
for pid in "${pids[@]}"; do
  wait "$pid" || status=1
done

exit "$status"
