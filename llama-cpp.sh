#!/usr/bin/env bash
# Run every benchmark prompt through a local llama.cpp model and turn the
# transcripts into a gradeable submission directory.
#
# Usage:
#   ./llama-cpp.sh [options] <model.gguf>
#
# Produces, for each problem:
#   results/<host>/oneshot/<model>/transcripts/<problem>.txt   raw model output
#   results/<host>/oneshot/<model>/<problem>/<deliverables>    files for the grader
#
# Then grade it:
#   ./benchmark/run_all.sh results/<host>/oneshot/<model> "<model>"   (or --grade)
#
# llama-cli is a completion front end, not an agent: it streams an answer rather
# than writing files, so benchmark/extract_submission.py lifts the code blocks
# out of each transcript into the filenames the graders import. A model that
# answers in prose with no code block produces no file, and the grader reports
# it as a missing deliverable — that is a real result, not an error here.

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
MODELDIR="${MODELDIR:-$HOME/models}"
BENCHMARKS="01-python-parse-duration 02-js-lru-ttl-cache 03-sql-analytics 04-go-worker-pool 05-python-scheduler"

# One attempt, greedy decoding, prompt not echoed back into the transcript.
# Override wholesale with LLAMA_ARGS='...' if your build wants different flags.
LLAMA_ARGS="${LLAMA_ARGS:--st --temp 0 --no-display-prompt}"
CTX="${CTX:-8192}"
N_PREDICT="${N_PREDICT:-4096}"

MODEL=""
ONLY=""
GRADE=0
KEEP=0

usage() {
  awk 'NR > 1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"
  cat <<'EOF'

Options:
  -o, --only LIST   run only these problems (e.g. -o 1  or  -o 1,3,5)
  -g, --grade       run benchmark/run_all.sh on the result when finished
  -k, --keep        keep an existing output directory instead of clearing it
      --model-dir D directory holding the .gguf (default $MODELDIR or ~/models)
  -h, --help        this message

Environment:
  MODELDIR    where the .gguf lives            (default ~/models)
  LLAMA_ARGS  sampling flags passed to llama-cli
  CTX         context size, -c                 (default 8192)
  N_PREDICT   max tokens generated, -n         (default 4096)
EOF
}

die() { echo "llama-cpp.sh: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--only)   [ $# -ge 2 ] || die "--only needs an argument"; ONLY="$2"; shift 2 ;;
    -g|--grade)  GRADE=1; shift ;;
    -k|--keep)   KEEP=1; shift ;;
    --model-dir) [ $# -ge 2 ] || die "--model-dir needs an argument"; MODELDIR="$2"; shift 2 ;;
    -h|--help)   usage; exit 0 ;;
    -*)          die "unknown option '$1' (try --help)" ;;
    *)           [ -z "$MODEL" ] || die "unexpected argument '$1'"; MODEL="$1"; shift ;;
  esac
done

[ -n "$MODEL" ] || { usage; exit 2; }

# accept either a bare name or a full path to the .gguf
if [ -f "$MODEL" ]; then
  MODELPATH="$MODEL"; MODEL="$(basename "$MODEL")"
else
  MODELPATH="$MODELDIR/$MODEL"
fi
[ -f "$MODELPATH" ] || die "model not found: $MODELPATH
       (set MODELDIR or pass --model-dir; --help for details)"

command -v llama-cli >/dev/null 2>&1 || die "llama-cli not on PATH"

PY=""
for c in python3 python; do
  command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }
done
[ -n "$PY" ] || die "python3 not on PATH (needed to extract deliverables)"

selected() { # problem name
  [ -z "$ONLY" ] && return 0
  local num="${1%%-*}"
  echo "$ONLY" | tr ',' '\n' | while read -r item; do
    item="$(echo "$item" | tr -d ' ')"
    [ -z "$item" ] && continue
    case "$item" in
      "$1") echo match ;;
      *) [ "$(printf '%02d' "$item" 2>/dev/null)" = "$num" ] && echo match ;;
    esac
  done | grep -q match
}

OUT="$ROOT/results/$(hostname -s)/oneshot/$MODEL"
if [ "$KEEP" = "0" ] && [ -d "$OUT" ] && [ -z "$ONLY" ]; then
  echo "clearing previous $OUT (use --keep to preserve it)"
  rm -rf "$OUT"
fi
mkdir -p "$OUT/transcripts" || die "cannot create $OUT"

echo "======================================================"
echo " Model:   $MODELPATH"
echo " Output:  $OUT"
echo " Flags:   $LLAMA_ARGS -c $CTX -n $N_PREDICT"
echo "======================================================"

failed=0
for B in $BENCHMARKS; do
  selected "$B" || continue
  prompt="$ROOT/benchmark/problems/$B/PROMPT.md"
  [ -f "$prompt" ] || die "prompt missing: $prompt"
  transcript="$OUT/transcripts/$B.txt"

  echo
  echo "== $B =="
  # shellcheck disable=SC2086  # LLAMA_ARGS is deliberately word-split
  if ! llama-cli -m "$MODELPATH" -f "$prompt" \
        -c "$CTX" -n "$N_PREDICT" $LLAMA_ARGS > "$transcript" 2>"$transcript.err"; then
    echo "  llama-cli failed — see $transcript.err"
    tail -3 "$transcript.err" 2>/dev/null | sed 's/^/    | /'
    failed=1
    continue
  fi
  rm -f "$transcript.err"
  echo "  transcript: $transcript ($(wc -l < "$transcript" | tr -d ' ') lines)"
  "$PY" "$ROOT/benchmark/extract_submission.py" "$B" "$transcript" "$OUT/$B" || failed=1
done

echo
if [ "$failed" = "1" ]; then
  echo "One or more problems produced no usable deliverable (see above)."
  echo "The raw transcripts are under $OUT/transcripts/ if you want to check."
fi

if [ "$GRADE" = "1" ]; then
  echo
  exec "$ROOT/benchmark/run_all.sh" "$OUT" "$MODEL"
fi

echo "Next: ./benchmark/run_all.sh $OUT \"$MODEL\""
