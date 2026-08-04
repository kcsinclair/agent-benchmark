#!/usr/bin/env bash
# Self-test for run_all.sh — checks that the harness reports correct scores and
# degrades sanely when things are broken. Builds its own throwaway fixtures.
#
#   ./test_run_all.sh          # run every case
#
# Cases that need a toolchain skip themselves if it is absent, so this is safe
# to run anywhere. Exits non-zero if any case fails.

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
RUN="$ROOT/run_all.sh"

# Reference solutions live in the private harness submodule alongside the
# graders. Without it there is nothing to test, so say so plainly rather than
# reporting a wall of failures.
HARNESS="${BENCH_HARNESS:-$REPO/harness}"
SOLUTIONS="$HARNESS/solutions"
[ -d "$SOLUTIONS" ] || {
  echo "test_run_all.sh: no harness at $HARNESS" >&2
  echo "  git submodule update --init   (private repo; see README 'Contributing')" >&2
  exit 1
}

TMP="$(mktemp -d "${TMPDIR:-/tmp}/run_all_test.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

PASS=0; FAIL=0

t() { # label expected_rc pattern cmd...
  local label="$1" xrc="$2" pat="$3"; shift 3
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" = "$xrc" ] && echo "$out" | grep -q "$pat"; then
    echo "  ok   $label"; PASS=$((PASS + 1))
  else
    echo "  FAIL $label  (exit $rc, wanted $xrc; missing /$pat/)"
    echo "$out" | tail -8 | sed 's/^/       | /'
    FAIL=$((FAIL + 1))
  fi
}

# ---- fixtures ---------------------------------------------------------------
B="$TMP/broken"
mkdir -p "$B/01-python-parse-duration" "$B/02-js-lru-ttl-cache" \
         "$B/03-sql-analytics" "$B/04-go-worker-pool" "$B/05-python-scheduler"
printf 'while True:\n    pass\n'      > "$B/01-python-parse-duration/parse_duration.py"  # hangs
: >                                    "$B/02-js-lru-ttl-cache/notes.txt"                # no deliverable
for q in q1 q2 q3 q4; do echo "SELECT 1;" > "$B/03-sql-analytics/$q.sql"; done           # wrong answers
printf 'package main\nfunc Run(  {}\n' > "$B/04-go-worker-pool/pool.go"                  # will not compile
printf 'raise RuntimeError("boom")\n' > "$B/05-python-scheduler/scheduler.py"            # explodes on import

mkdir -p "$TMP/misplaced" && : > "$TMP/misplaced/cache.mjs"   # files at the wrong level

# a GNU-timeout stand-in, to exercise the external-timeout branch
mkdir -p "$TMP/bin"
cat > "$TMP/bin/timeout" <<'SH'
#!/bin/sh
secs=$1; shift
"$@" & pid=$!
( sleep "$secs"; kill -9 "$pid" 2>/dev/null ) & wpid=$!
wait "$pid"; rc=$?
kill "$wpid" 2>/dev/null
[ "$rc" -ge 128 ] && rc=124
exit $rc
SH
chmod +x "$TMP/bin/timeout"

# ---- cases ------------------------------------------------------------------
echo "run_all.sh self-test"

t "reference solutions score 68/68"  0 'TOTAL *68 / 68'       "$RUN" -q "$SOLUTIONS"
t "verbose output streams checks"    0 'PASS  '               "$RUN" --only 1 "$SOLUTIONS"
t "broken submission scores 0/68"    1 'TOTAL *0 / 68'        "$RUN" -q -t 6 "$B"
t "runaway submission times out"     1 '\[timeout\]'          "$RUN" -q -t 6 --only 1 "$B"
t "uncompilable Go is [crashed]"     0 '\[crashed\]'          "$RUN" -q --only 4 "$B"
t "missing deliverable is named"     0 'MISSING deliverable'  "$RUN" -q --only 2 "$B"
t "wrong layout is diagnosed"        0 'no problem directories' "$RUN" -q "$TMP/misplaced"
t "missing dir exits 2"              2 'not found'            "$RUN" "$TMP/nope"
t "unknown flag exits 2"             2 'unknown option'       "$RUN" --bogus
t "--only matching nothing exits 2"  2 'matched no problems'  "$RUN" --only 9 "$SOLUTIONS"
t "--only takes a list"              0 'TOTAL *28 / 28'       "$RUN" -q --only 1,3 "$SOLUTIONS"
t "--only takes a full name"         0 'TOTAL *8 / 8'         "$RUN" -q --only 03-sql-analytics "$SOLUTIONS"
t "--no-race is flagged on the row"  0 '\[no -race\]'         "$RUN" -q --no-race --only 4 "$SOLUTIONS"
t "--list"                           0 '05-python-scheduler'  "$RUN" --list
t "--help"                           0 'Exit status'          "$RUN" --help
t "works with a timeout binary"      0 'TOTAL *20 / 20'       env PATH="$TMP/bin:$PATH" "$RUN" -q --only 1 "$SOLUTIONS"

# missing-toolchain handling: only meaningful if node really is absent from a
# minimal PATH (it usually is — node is rarely in /usr/bin)
if ! env -i PATH=/usr/bin:/bin sh -c 'command -v node' >/dev/null 2>&1; then
  t "absent toolchain is [no node]"  1 '\[no node\]' \
    env -i PATH=/usr/bin:/bin HOME="$HOME" bash "$RUN" -q --only 2 "$SOLUTIONS"
else
  echo "  skip node-absent case (node is on the minimal PATH here)"
fi

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
