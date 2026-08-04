#!/usr/bin/env bash
# Run all five graders against a submissions directory and print a scorecard.
#
# Usage:
#   ./run_all.sh [options] [submissions_dir] [label]
#
# submissions_dir defaults to ./submissions and must contain one folder per
# problem (same names as problems/), each holding that problem's deliverable
# file(s):
#
#   submissions/
#     01-python-parse-duration/parse_duration.py
#     02-js-lru-ttl-cache/cache.mjs
#     03-sql-analytics/q1.sql q2.sql q3.sql q4.sql
#     04-go-worker-pool/pool.go
#     05-python-scheduler/scheduler.py
#
# Tip: keep one submissions dir per model, e.g. ./run_all.sh results/<server>/oneshot/<model>
#
# Portability: works with bash 3.2 (stock macOS) and bash 4/5 (Linux), with or
# without GNU coreutils. `timeout` is used when present (timeout or gtimeout);
# otherwise a built-in watchdog provides the same limits.
#
# Exit status: 0 = every problem was graded (a score of 0 is a valid result)
#              1 = one or more problems could not be graded (missing toolchain
#                  or timeout) — the total is incomplete, do not report it
#              2 = usage error (bad flag, missing submissions dir)

set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# The graders and reference solutions live in a separate PRIVATE repo, checked
# out here as the `harness` submodule. They are split out because this repo is
# public and the graders carry the hidden edge cases: a contestant who can read
# them can code to them. Without the submodule there is nothing to grade with,
# which is a hard error rather than a score of zero — a silent 0/68 would look
# like a terrible submission instead of a missing checkout.
HARNESS="${BENCH_HARNESS:-$REPO/harness}"

# problem | max checks | runtime | timeout secs | required deliverables
PROBLEMS="
01-python-parse-duration|20|py|120|parse_duration.py
02-js-lru-ttl-cache|17|node|120|cache.mjs
03-sql-analytics|8|py|120|q1.sql q2.sql q3.sql q4.sql
04-go-worker-pool|11|go|300|pool.go
05-python-scheduler|12|py|300|scheduler.py
"

SUB=""
LABEL=""
ONLY=""
QUIET=0
USE_RACE=1
TIMEOUT_OVERRIDE=""

usage() {
  # reuse the comment header above as the usage text
  awk 'NR > 1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"
  cat <<'EOF'

Options:
  -o, --only LIST   grade only these problems (e.g. -o 4  or  -o 1,3,5)
  -q, --quiet       suppress per-check output; print the scorecard only
  -t, --timeout N   override every per-problem time limit with N seconds
                    (defaults: 120s for problems 1-3, 300s for 4-5)
      --no-race     run problem 4 without the Go race detector (faster, and a
                    fallback when no C compiler is available — but data races
                    then go undetected, so the score is not comparable)
  -l, --list        list the problems and their check counts, then exit
  -h, --help        this message
EOF
}

die() { echo "run_all.sh: $*" >&2; exit 2; }

while [ $# -gt 0 ]; do
  case "$1" in
    -o|--only)  [ $# -ge 2 ] || die "--only needs an argument"; ONLY="$2"; shift 2 ;;
    --only=*)   ONLY="${1#--only=}"; shift ;;
    -q|--quiet) QUIET=1; shift ;;
    -t|--timeout)
      [ $# -ge 2 ] || die "--timeout needs an argument"
      case "$2" in ''|*[!0-9]*) die "--timeout wants whole seconds, got '$2'" ;; esac
      TIMEOUT_OVERRIDE="$2"; shift 2 ;;
    --no-race)  USE_RACE=0; shift ;;
    -l|--list)
      echo "$PROBLEMS" | while IFS='|' read -r name max kind secs files; do
        [ -n "${name:-}" ] || continue
        printf ' %-28s %2s checks  %-5s  %s\n' "$name" "$max" "$kind" "$files"
      done
      exit 0 ;;
    -h|--help)  usage; exit 0 ;;
    --)         shift; break ;;
    -*)         die "unknown option '$1' (try --help)" ;;
    *)
      if [ -z "$SUB" ]; then SUB="$1"
      elif [ -z "$LABEL" ]; then LABEL="$1"
      else die "unexpected argument '$1'"
      fi
      shift ;;
  esac
done
[ $# -gt 0 ] && { [ -z "$SUB" ] && SUB="$1" || LABEL="$1"; }

[ -n "$SUB" ] || SUB="$ROOT/submissions"
SUB="${SUB%/}"
[ -n "$LABEL" ] || LABEL="$(basename "$SUB")"

[ -d "$SUB" ] || die "submissions directory not found: $SUB"

[ -d "$HARNESS/problems" ] || die "graders not found at $HARNESS
The graders live in a separate private repo, checked out as a submodule:
    git submodule update --init
If you do not have access to it you cannot grade locally — see README.md,
'Contributing'. Set BENCH_HARNESS to grade against a checkout elsewhere."

# make it absolute so the Go stage can cd elsewhere safely
SUB="$(cd "$SUB" && pwd)"

# ---------------------------------------------------------------- toolchain --

# Prefer the newest Python >= 3.10 (the documented minimum). Stock macOS puts
# Python 3.9 at /usr/bin/python3 ahead of a newer Homebrew one on PATH, so
# check versioned names too rather than trusting whichever python3 wins.
find_python() { # echoes a command name; rc 0 = >=3.10, 3 = older 3.x, 1 = none
  local c
  for c in python3.14 python3.13 python3.12 python3.11 python3.10 python3 python; do
    command -v "$c" >/dev/null 2>&1 || continue
    "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null \
      && { echo "$c"; return 0; }
  done
  for c in python3 python; do
    command -v "$c" >/dev/null 2>&1 || continue
    "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,0) else 1)' 2>/dev/null \
      && { echo "$c"; return 3; }
  done
  return 1
}

PYTHON="$(find_python)"; PY_RC=$?
NODE="$(command -v node 2>/dev/null || true)"
GO="$(command -v go 2>/dev/null || true)"

# short version strings for the run header (reproducibility)
PY_V="none"; NODE_V="none"; GO_V="none"
[ -n "$PYTHON" ] && PY_V="$("$PYTHON" -c 'import platform; print(platform.python_version())' 2>/dev/null)"
[ -n "$NODE" ]   && NODE_V="$("$NODE" -v 2>/dev/null)"
[ -n "$GO" ]     && GO_V="$("$GO" env GOVERSION 2>/dev/null)"

TIMEOUT_BIN=""
for t in timeout gtimeout; do
  if command -v "$t" >/dev/null 2>&1; then TIMEOUT_BIN="$t"; break; fi
done

# The Go race detector needs cgo and a working C compiler.
RACE_OK=1
if [ -n "$GO" ]; then
  [ "$("$GO" env CGO_ENABLED 2>/dev/null)" = "1" ] || RACE_OK=0
  command -v "$("$GO" env CC 2>/dev/null || echo cc)" >/dev/null 2>&1 ||
    command -v cc >/dev/null 2>&1 || RACE_OK=0
fi

WARNINGS=""
warn() { WARNINGS="${WARNINGS}  ! $*
"; echo "run_all.sh: warning: $*" >&2; }

if [ "$PY_RC" = "3" ]; then
  warn "python $PY_V is below the documented 3.10 minimum; submissions using
      3.10+ syntax will fail to load and score 0 unfairly (macOS: /usr/bin/python3
      is 3.9 — install a newer one, e.g. 'brew install python@3.13')"
fi

if [ "$USE_RACE" = "1" ] && [ -n "$GO" ] && [ "$RACE_OK" = "0" ]; then
  warn "no cgo/C compiler: problem 4 will run WITHOUT -race, so data races go undetected"
  USE_RACE=0
fi

# ------------------------------------------------------------------ timeout --

_watchdog() { # secs pid
  local secs="$1" pid="$2" i=0
  while [ "$i" -lt "$secs" ]; do
    kill -0 "$pid" 2>/dev/null || return 0
    sleep 1
    i=$((i + 1))
  done
  kill -TERM "$pid" 2>/dev/null
  sleep 2
  kill -KILL "$pid" 2>/dev/null
  return 0
}

# Run a command under a wall-clock limit. Returns 124 on timeout, like GNU
# timeout, whether or not a timeout binary exists on this machine.
run_limited() { # secs cmd...
  local secs="$1"; shift
  if [ -n "$TIMEOUT_BIN" ]; then
    "$TIMEOUT_BIN" "$secs" "$@"
    return $?
  fi
  local cpid wpid rc=0
  "$@" &
  cpid=$!
  _watchdog "$secs" "$cpid" &
  wpid=$!
  wait "$cpid" 2>/dev/null || rc=$?
  kill "$wpid" 2>/dev/null
  wait "$wpid" 2>/dev/null || true
  case "$rc" in 137|143) rc=124 ;; esac
  return $rc
}

TMPROOT=""
cleanup() { [ -n "$TMPROOT" ] && rm -rf "$TMPROOT"; }
trap cleanup EXIT HUP INT TERM

# ------------------------------------------------------------------ grading --

NAMES=""; SCORES=""; MAXES=""; STATUSES=""   # newline-joined, bash 3.2 safe
HARNESS_FAILED=0

selected() { # problem name -> 0 if it should run
  [ -z "$ONLY" ] && return 0
  local num="${1%%-*}" item
  echo "$ONLY" | tr ',' '\n' | while read -r item; do
    item="$(echo "$item" | tr -d ' ')"
    [ -z "$item" ] && continue
    case "$item" in
      "$1") echo match ;;
      *) [ "$(printf '%02d' "$item" 2>/dev/null)" = "$num" ] && echo match ;;
    esac
  done | grep -q match
}

missing_files() { # dir, file list -> prints missing names
  local dir="$1"; shift
  local f out=""
  for f in $1; do
    [ -f "$dir/$f" ] || out="$out $f"
  done
  echo "${out# }"
}

go_grade() { # submission dir, timeout secs
  local subdir="$1" secs="$2" tmp rc
  local H="$HARNESS/problems/04-go-worker-pool"
  tmp="$TMPROOT/pool"
  rm -rf "$tmp"; mkdir -p "$tmp" || return 125
  cp "$H/go.mod" "$H/grader.go" "$subdir/pool.go" "$tmp/" || return 125
  local flags=""
  [ "$USE_RACE" = "1" ] && flags="-race"
  ( cd "$tmp" && run_limited "$secs" "$GO" run $flags . )
  rc=$?
  rm -rf "$tmp"
  return $rc
}

exec_grader() { # kind name dir secs tool
  local kind="$1" name="$2" dir="$3" secs="$4" tool="$5"
  case "$kind" in
    py)   run_limited "$secs" "$tool" "$HARNESS/problems/$name/grade.py"  "$dir" ;;
    node) run_limited "$secs" "$tool" "$HARNESS/problems/$name/grade.mjs" "$dir" ;;
    go)   go_grade "$dir" "$secs" ;;
  esac
}

record() { # name score max status
  NAMES="$NAMES$1
"; SCORES="$SCORES$2
"; MAXES="$MAXES$3
"; STATUSES="$STATUSES$4
"
}

TMPROOT="$(mktemp -d "${TMPDIR:-/tmp}/benchgrade.XXXXXX")" || die "cannot create temp dir"
OUT="$TMPROOT/out.txt"

# A submissions dir with none of the expected problem folders is nearly always
# a layout mistake (files dropped at the top level), not five zero scores.
found_dirs=0
for d in 01-python-parse-duration 02-js-lru-ttl-cache 03-sql-analytics \
         04-go-worker-pool 05-python-scheduler; do
  [ -d "$SUB/$d" ] && found_dirs=$((found_dirs + 1))
done
if [ "$found_dirs" -eq 0 ]; then
  warn "no problem directories found in $SUB — expected layout:
        <dir>/01-python-parse-duration/parse_duration.py
        <dir>/02-js-lru-ttl-cache/cache.mjs
        <dir>/03-sql-analytics/q1.sql q2.sql q3.sql q4.sql
        <dir>/04-go-worker-pool/pool.go
        <dir>/05-python-scheduler/scheduler.py
        (../make-runs.sh <model> creates these folders for you)"
fi

echo "======================================================"
echo " Grading: $SUB"
echo " Label:   $LABEL"
printf " Tools:   python %s | node %s | %s | timeout: %s\n" \
  "$PY_V" "$NODE_V" "$GO_V" "${TIMEOUT_BIN:-built-in watchdog}"
[ "$USE_RACE" = "1" ] || echo " Note:    problem 4 running WITHOUT -race"
echo "======================================================"
echo

while IFS='|' read -r name max kind secs files; do
  [ -n "${name:-}" ] || continue
  selected "$name" || continue
  [ -n "$TIMEOUT_OVERRIDE" ] && secs="$TIMEOUT_OVERRIDE"

  if [ "$QUIET" = "1" ]; then
    printf '  grading %s ...\n' "$name" >&2
  else
    echo "== $name =="
  fi
  dir="$SUB/$name"
  status="ok"; rc=0
  : > "$OUT"

  # 1. toolchain present?
  tool=""
  case "$kind" in
    py)   tool="$PYTHON" ;;
    node) tool="$NODE" ;;
    go)   tool="$GO" ;;
  esac
  if [ -z "$tool" ]; then
    echo "  SKIPPED — no $kind runtime found on PATH"
    record "$name" 0 "$max" "no $kind"
    HARNESS_FAILED=1
    [ "$QUIET" = "1" ] || echo
    continue
  fi

  # 2. submission present?
  if [ ! -d "$dir" ]; then
    echo "  MISSING — no directory $dir"
    record "$name" 0 "$max" "not submitted"
    [ "$QUIET" = "1" ] || echo
    continue
  fi
  miss="$(missing_files "$dir" "$files")"
  if [ -n "$miss" ]; then
    echo "  MISSING deliverable(s):$( for f in $miss; do printf ' %s' "$f"; done )"
    echo "  (found:$( ls "$dir" 2>/dev/null | grep -v '^\.' | while read -r f; do printf ' %s' "$f"; done ))"
    # problems 1-3 and 5 still grade partial submissions; only 4 cannot build
    if [ "$kind" = "go" ]; then
      record "$name" 0 "$max" "missing files"
      [ "$QUIET" = "1" ] || echo
    continue
    fi
  fi

  # 3. run the grader (streaming output live unless --quiet), capturing it
  if [ "$QUIET" = "1" ]; then
    exec_grader "$kind" "$name" "$dir" "$secs" "$tool" > "$OUT" 2>&1
    rc=$?
  else
    exec_grader "$kind" "$name" "$dir" "$secs" "$tool" 2>&1 | tee "$OUT"
    rc=${PIPESTATUS[0]}
  fi

  # 4. score = the last SCORE: line the grader printed
  line="$(grep -Eo 'SCORE: [0-9]+/[0-9]+' "$OUT" | tail -1)"
  if [ -n "$line" ]; then
    s="${line#SCORE: }"; m="${s#*/}"; s="${s%/*}"
    if [ "$m" != "$max" ]; then
      warn "$name: grader reports $m checks, script expects $max — update PROBLEMS"
      max="$m"
    fi
  else
    s=0
    if [ "$rc" -eq 124 ]; then
      echo "  TIMEOUT after ${secs}s — treating as 0/$max"
      status="timeout"; HARNESS_FAILED=1
    else
      echo "  (no SCORE line — grader or submission failed; treating as 0/$max)"
      status="crashed"
      # in --quiet mode the failure output was swallowed; show enough to debug
      if [ "$QUIET" = "1" ] && [ -s "$OUT" ]; then
        tail -5 "$OUT" | sed 's/^/    | /'
      fi
    fi
  fi
  # keep the -race caveat attached to the number, not just the run header
  [ "$kind" = "go" ] && [ "$USE_RACE" = "0" ] && [ "$status" = "ok" ] && status="no -race"
  record "$name" "$s" "$max" "$status"
  [ "$QUIET" = "1" ] || echo
done <<EOF
$PROBLEMS
EOF

# ---------------------------------------------------------------- scorecard --

if [ -z "$NAMES" ]; then
  die "nothing selected to grade${ONLY:+ (--only '$ONLY' matched no problems)}"
fi

echo "======================================================"
echo " SCORECARD — $LABEL"
echo "======================================================"
total=0; max=0; timed=""
rows="$(echo "$NAMES" | grep -c .)"
i=1
while [ "$i" -le "$rows" ]; do
  n="$(echo "$NAMES"    | sed -n "${i}p")"
  s="$(echo "$SCORES"   | sed -n "${i}p")"
  m="$(echo "$MAXES"    | sed -n "${i}p")"
  st="$(echo "$STATUSES"| sed -n "${i}p")"
  if [ "$st" = "ok" ]; then
    printf " %-28s %3s / %-3s\n" "$n" "$s" "$m"
  else
    printf " %-28s %3s / %-3s  [%s]\n" "$n" "$s" "$m" "$st"
  fi
  if [ "$st" = "ok" ] && [ "$s" -gt 0 ] && [ "$s" -lt "$m" ]; then
    case "$n" in 04-*|05-*) timed="yes" ;; esac
  fi
  total=$((total + s)); max=$((max + m))
  i=$((i + 1))
done
echo "------------------------------------------------------"
pct=0
[ "$max" -gt 0 ] && pct=$(( 100 * total / max ))
printf " %-28s %3s / %-3s  (%s%%)\n" "TOTAL" "$total" "$max" "$pct"

if [ -n "$WARNINGS" ]; then
  echo
  echo " Warnings:"
  printf '%s' "$WARNINGS"
fi
if [ -n "$timed" ]; then
  echo
  echo " Note: problems 4 and 5 include timing checks. Re-run on an idle"
  echo "       machine before treating a near-miss there as real."
fi
if [ "$HARNESS_FAILED" = "1" ]; then
  echo
  echo " INCOMPLETE: some problems could not be graded (see [status] above)."
  exit 1
fi
exit 0
