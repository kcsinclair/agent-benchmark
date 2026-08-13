#!/usr/bin/env bash
# Measure raw inference speed for every model with llama-bench, over ssh.
#
# Usage:
#   ./run_llama_bench.sh [options]
#
# Writes one llama-bench JSON per model into results/<host>/speed/, plus a run log
# with the accelerator temperature before and after each model. Feed the
# directory to collate_bench.py to join speed against the accuracy scores.
#
# The router is stopped for the duration (it keeps up to 3 models resident on a
# unified-memory box, which is RAM llama-bench needs, and models_autoload means
# a single stray request would reload one mid-measurement). It is restarted on
# exit, including on Ctrl-C.
#
# Thermal drift is measured rather than assumed: a control model is re-run at
# the start, middle and end. If its numbers hold, back-to-back running is fine
# and nobody had to wait; if they drift, --cooldown adds gaps and the affected
# models can be re-run.
#
# Options:
#   -H, --host HOST       ssh target (default leia)
#       --model-dir DIR   where the .gguf files live (default /opt/local-ai/models,
#                         or $MODELDIR)
#       --bin-dir DIR     where llama-bench lives, prepended to PATH (default
#                         /opt/local-ai/bin, or $BENCH_BINDIR)
#   -o, --out DIR         results directory (default results/<host>/speed)
#   -d, --depths LIST     context depths (default 0,4096,16384)
#   -r, --reps N          repetitions per test (default 3)
#   -c, --cooldown SECS   idle gap between models (default 0)
#       --keep-server     do not stop llama-server.service
#       --models LIST     comma-separated labels to run (default all)
#       --list            show the model table and exit
#   -n, --dry-run         print the commands without running them
#   -h, --help            this message

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

HOST="leia"
MODELDIR="${MODELDIR:-/opt/local-ai/models}"
# llama-bench lives beside llama-server and is NOT on the ssh login PATH, so it
# is prepended rather than assumed. Using the server's own bin dir also keeps
# the measured build identical to the one that produced the accuracy scores.
BINDIR="${BENCH_BINDIR:-/opt/local-ai/bin}"
OUT=""   # default: results/<host>/speed
DEPTHS="0,4096,16384"
REPS=3
COOLDOWN=0
STOP_SERVER=1
ONLY=""
DRY=0
UNIT="llama-server.service"

# label | llama-bench model argument
# local .gguf files by path; the two cached HF repos by -hf, as the router uses
MODELS="
Muse-Glimmer-30B|-m $MODELDIR/Muse-Glimmer-30B-UD-Q8_K_XL.gguf
gemma-4-31B|-hf unsloth/gemma-4-31B-it-qat-GGUF:Q4_K_XL
gemma-4-26B|-m $MODELDIR/gemma-4-26B-A4B-it-qat-UD-Q4_K_XL.gguf
gemma-4-26B-Q8|-m $MODELDIR/gemma-4-26B-A4B-it-UD-Q8_K_XL.gguf
gemma-4-26B-heretic|-m $MODELDIR/gemma-4-26B-A4B-it-ultra-uncensored-heretic-Q4_K_M.gguf
gemma-4-E4B|-m $MODELDIR/gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf
gemma-4-E2B|-m $MODELDIR/gemma-4-E2B-it-UD-Q4_K_XL.gguf
gpt-oss-120b|-m $MODELDIR/gpt-oss-120b-MXFP4.gguf
Qwen3-Coder-30B|-m $MODELDIR/Qwen3-Coder-30B-A3B-Instruct-UD-Q4_K_XL.gguf
Qwen3.6-27B|-m $MODELDIR/Qwen3.6-27B-Q4_K_M.gguf
Qwen3.6-35B|-m $MODELDIR/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf
gpt-oss-20b-Q8|-m $MODELDIR/gpt-oss-20b-Q8_0.gguf
gpt-oss-20b-Q4|-m $MODELDIR/gpt-oss-20b-Q4_K_M.gguf
Hermes-4-14B|-m $MODELDIR/NousResearch_Hermes-4-14B-Q4_K_M.gguf
Llama-3-14B|-m $MODELDIR/Llama-3-14B-Instruct-v1.Q4_K_M.gguf
Qwen3VL-8B|-m $MODELDIR/Qwen3VL-8B-Uncensored-HauhauCS-Aggressive-Q4_K_M.gguf
Llama-3.1-8B|-m $MODELDIR/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
"
CONTROL_LABEL="gemma-4-26B"

usage() { awk 'NR > 1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"; }
die() { echo "run_llama_bench: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    -H|--host)     HOST="$2"; shift 2 ;;
    --model-dir)   MODELDIR="$2"; shift 2 ;;
    --bin-dir)     BINDIR="$2"; shift 2 ;;
    -o|--out)      OUT="$2"; shift 2 ;;
    -d|--depths)   DEPTHS="$2"; shift 2 ;;
    -r|--reps)     REPS="$2"; shift 2 ;;
    -c|--cooldown) COOLDOWN="$2"; shift 2 ;;
    --keep-server) STOP_SERVER=0; shift ;;
    --models)      ONLY="$2"; shift 2 ;;
    --list)        echo "$MODELS" | grep . | sed 's/|/  ->  /'; exit 0 ;;
    -n|--dry-run)  DRY=1; shift ;;
    -h|--help)     usage; exit 0 ;;
    *)             die "unknown option '$1' (try --help)" ;;
  esac
done

[ -n "$OUT" ] || OUT="$REPO/results/${HOST%%.*}/speed"

rsh() { ssh -o ConnectTimeout=20 -o BatchMode=yes "$HOST" "bash -lc 'export PATH=$BINDIR:\$PATH; $1'"; }

# --- preflight ---------------------------------------------------------------
rsh 'which llama-bench >/dev/null' || die "llama-bench not found on $HOST"
mkdir -p "$OUT" || die "cannot create $OUT"
LOG="$OUT/runlog.jsonl"

temp() { rsh 'sensors 2>/dev/null | awk "/Tctl/ {gsub(/[+°C]/,\"\",\$2); print \$2; exit}"' 2>/dev/null; }

restore() {
  if [ "$STOP_SERVER" = "1" ] && [ "$DRY" = "0" ]; then
    echo
    echo "restarting $UNIT on $HOST"
    ssh -o ConnectTimeout=20 "$HOST" "systemctl --user start $UNIT" \
      && echo "  restarted" || echo "  FAILED — start it by hand: systemctl --user start $UNIT"
  fi
}
trap restore EXIT HUP INT TERM

if [ "$STOP_SERVER" = "1" ] && [ "$DRY" = "0" ]; then
  echo "stopping $UNIT on $HOST (Lexi will be unavailable until this finishes)"
  ssh -o ConnectTimeout=20 "$HOST" "systemctl --user stop $UNIT" || die "could not stop $UNIT"
fi

# --- one model ---------------------------------------------------------------
run_one() { # label, model-arg, extra-args, outfile
  local label="$1" marg="$2" extra="$3" out="$4"
  local t0 t1 start end
  t0="$(temp)"
  start=$(date +%s)
  echo "== $label ==  (Tctl ${t0:-?}C)"
  local cmd="llama-bench $marg -fa on -ctk q8_0 -ctv q8_0 -ngl 999 -r $REPS $extra -o json --offline 2>/dev/null"
  if [ "$DRY" = "1" ]; then
    echo "  would run: $cmd"
    return 0
  fi
  if ! rsh "$cmd" > "$out"; then
    echo "  FAILED — see $out"
    echo "{\"label\":\"$label\",\"error\":true}" >> "$LOG"
    return 1
  fi
  end=$(date +%s); t1="$(temp)"
  echo "  done in $((end - start))s  (Tctl ${t0:-?}C -> ${t1:-?}C)  -> $(basename "$out")"
  printf '{"label":"%s","seconds":%d,"temp_before":"%s","temp_after":"%s","file":"%s"}\n' \
    "$label" "$((end - start))" "${t0:-}" "${t1:-}" "$(basename "$out")" >> "$LOG"
}

control_arg() {
  echo "$MODELS" | grep "^$CONTROL_LABEL|" | head -1 | cut -d'|' -f2
}

# short control: generation only, no depth sweep — this is a drift probe, not a
# measurement, so it must be cheap enough to run three times
control() { # tag
  run_one "control-$1" "$(control_arg)" "-p 0 -n 128 -d 0" "$OUT/control-$1.json"
}

# --- run ---------------------------------------------------------------------
echo "results -> $OUT"
echo "depths $DEPTHS, $REPS repetition(s), cooldown ${COOLDOWN}s"
echo

selected=""
while IFS='|' read -r label marg; do
  [ -n "${label:-}" ] || continue
  if [ -n "$ONLY" ]; then
    echo ",$ONLY," | grep -q ",$label," || continue
  fi
  selected="$selected $label"
done <<EOF
$(echo "$MODELS" | grep .)
EOF

count="$(echo $selected | wc -w | tr -d ' ')"
[ "$count" -gt 0 ] || die "no models selected"
middle=$(( (count + 1) / 2 ))

control start
i=0
for label in $selected; do
  i=$((i + 1))
  marg="$(echo "$MODELS" | grep "^$label|" | head -1 | cut -d'|' -f2)"
  run_one "$label" "$marg" "-p 512 -n 128 -d $DEPTHS" "$OUT/$label.json"
  [ "$i" = "$middle" ] && control middle
  if [ "$COOLDOWN" -gt 0 ] && [ "$i" -lt "$count" ]; then
    echo "  cooling down ${COOLDOWN}s"
    sleep "$COOLDOWN"
  fi
done
control end

echo
echo "collate with:  ./benchmark/collate_bench.py $OUT"
