#!/usr/bin/env bash
# Self-test for bench.sh — checks that a profile resolves into the right runner
# command line, and that a key never reaches the output.
#
#   ./test_bench.sh            # run every case
#
# Everything here runs under --dry-run against a throwaway .env, so no model is
# called, no network is touched and nothing is graded. Exits non-zero if any
# case fails.

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
BENCH="$REPO/bench.sh"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/bench_test.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

# ---- fixture ----------------------------------------------------------------
# A key shaped like the real thing, so the "never printed" cases would catch a
# leak of a prefix as well as of the whole value.
SECRET="sk-or-v1-testonly-0123456789abcdef"
cat > "$TMP/env" <<EOF
# a comment, and a blank line follow

BENCH_PROFILE_ANTHROPIC_URL=https://openrouter.ai/api
BENCH_PROFILE_ANTHROPIC_PROVIDER=Anthropic
BENCH_PROFILE_ANTHROPIC_LABEL=openrouter
BENCH_PROFILE_ANTHROPIC_KEY=$SECRET
export BENCH_PROFILE_LEIA_URL="http://leia.packsin.com:7442"
BENCH_PROFILE_TUNED_URL=http://localhost:7442
BENCH_PROFILE_TUNED_ARGS=--think on --temperature 0.2
BENCH_SPEED_HOST=localhost
BENCH_SPEED_LABEL=leia
BENCH_SPEED_BINDIR=/opt/local-ai/bin
BENCH_SPEED_MAC_SSH=mac.local
BENCH_SPEED_MAC_BINDIR=/opt/homebrew/bin
NOT_A_PROFILE=ignored
EOF

# a profile with no _URL is not a profile; it must not resolve
cat > "$TMP/env-broken" <<'EOF'
BENCH_PROFILE_HALF_PROVIDER=Anthropic
EOF

# Scrub every BENCH_* variable the caller exported before invoking bench.sh.
# `bench.sh selftest` runs this from a process that has already loaded the real
# .env and exported its profiles, and load_dotenv lets an existing variable win
# — so without this the fixture's values lose to whatever is really configured,
# and the suite passes or fails depending on the caller's .env.
CLEAN=(-u OPENROUTER_API_KEY)
for v in $(env | sed -n 's/^\(BENCH_[A-Za-z0-9_]*\)=.*/\1/p'); do
  CLEAN+=(-u "$v")
done

B() { env "${CLEAN[@]}" BENCH_ENV="$TMP/env" bash "$BENCH" "$@"; }

PASS=0; FAIL=0

t() { # label expected_rc pattern cmd...
  local label="$1" xrc="$2" pat="$3"; shift 3
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  # -e: most of these patterns start with a dash, which grep would read as a flag
  if [ "$rc" = "$xrc" ] && echo "$out" | grep -q -e "$pat"; then
    echo "  ok   $label"; PASS=$((PASS + 1))
  else
    echo "  FAIL $label  (exit $rc, wanted $xrc; missing /$pat/)"
    echo "$out" | tail -8 | sed 's/^/       | /'
    FAIL=$((FAIL + 1))
  fi
}

n() { # label pattern-that-must-NOT-appear cmd...
  local label="$1" pat="$2"; shift 2
  local out
  out="$("$@" 2>&1)"
  if echo "$out" | grep -q -e "$pat"; then
    echo "  FAIL $label  (found /$pat/ in the output)"
    FAIL=$((FAIL + 1))
  else
    echo "  ok   $label"; PASS=$((PASS + 1))
  fi
}

# ---- cases ------------------------------------------------------------------
echo "bench.sh self-test"

t "--help"                        0 'Subcommands'          B --help
t "no arguments is a usage error" 2 'Usage'                B
t "unknown subcommand exits 2"    2 'unknown subcommand'   B bogus
t "unknown option exits 2"        2 'unknown option'       B -z oneshot
t "--passes wants a number"       2 'whole number'         B -r x oneshot leia m

t "unknown profile exits 2"       2 "no profile 'nope'"    B -n oneshot nope m
t "unknown profile lists the known ones" 2 'anthropic'     B -n oneshot nope m
t "a profile needs a _URL"        2 "no profile 'half'" \
  env -u OPENROUTER_API_KEY BENCH_ENV="$TMP/env-broken" bash "$BENCH" -n oneshot half m

t "profiles lists each profile"   0 'anthropic'            B profiles
t "profiles names the key source" 0 'BENCH_PROFILE_ANTHROPIC_KEY' B profiles
t "profiles marks unauthed URLs"  0 'n/a'                  B profiles
n "profiles never prints the key" "$SECRET"                B profiles

# --- command assembly ---
t "oneshot passes the endpoint"   0 'run_http.py .*-s https://openrouter.ai/api' B -n oneshot anthropic m
t "oneshot pins the provider"     0 '--provider Anthropic' B -n oneshot anthropic m
t "oneshot grades, one pass"      0 '\-r 1 -g'             B -n oneshot anthropic m
t "oneshot3 means three passes"   0 '\-r 3 -g'             B -n oneshot3 anthropic m
t "--passes overrides oneshot3"   0 '\-r 5 -g'             B -n -r 5 oneshot3 anthropic m
t "the model is the last word"    0 'anthropic/claude-sonnet-5$' B -n oneshot anthropic anthropic/claude-sonnet-5
t "several models are all passed" 0 'model-a model-b$'     B -n oneshot anthropic model-a model-b

t "_LABEL picks the results dir"  0 "out $REPO/results/openrouter/oneshot" B -n oneshot anthropic m
t "no _LABEL falls back to the host" 0 "out $REPO/results/leia/oneshot"    B -n oneshot leia m
t "reasoning writes to its own track" 0 "out $REPO/results/leia/reasoning" B -n reasoning leia m
t "_ARGS reaches the runner"      0 '--think on --temperature 0.2'         B -n oneshot tuned m
t "-- passes flags through"       0 '\-\-reasoning-effort medium m' B -n oneshot anthropic m -- --reasoning-effort medium
t "options may precede the subcommand" 0 'run_http.py'     B -n oneshot anthropic m
t "options may follow the subcommand"  0 '\-r 3 -g'        B oneshot -n -r 3 anthropic m
n "a dry run never prints the key" "$SECRET"               B -n oneshot anthropic m

t "models asks for the listing"   0 '--list-models'        B -n models anthropic
t "models takes a filter"         0 '--list-models claude' B -n models anthropic claude
t "grade calls run_all.sh"        0 'run_all.sh /tmp/x'    B -n grade /tmp/x
t "table calls the collator"      0 'collate_results.py'   B -n table
t "table passes flags through"    0 "\-\-label 'or-\*'"    B -n table -- --label 'or-*'
t "scrub defaults to results/"    0 "scrub_results.py .*/results$" B -n scrub
t "scrub takes --check"           0 '\-\-check'            B -n scrub -- --check

# --- agent ---
t "agent calls run_agent.py"      0 'run_agent.py'         B -n agent anthropic m
t "agent writes to its own track" 0 "out $REPO/results/openrouter/agent" B -n agent anthropic m
t "agent defaults to one pass"    0 '\-r 1'                B -n agent anthropic m
t "agent3 means three passes"     0 '\-r 3'                B -n agent3 anthropic m
t "--passes overrides agent3"     0 '\-r 5'                B -n -r 5 agent3 anthropic m
# run_agent.py grades unconditionally and rejects -g, so bench.sh must never
# add it and must refuse it up front rather than aborting mid-run
n "agent never passes -g"         ' \-g'                   B -n agent anthropic m
t "agent refuses a -g passthrough" 2 'always grades'       B -n agent anthropic m -- -g
t "agent needs a model"           2 'usage: ./bench.sh agent' B -n agent anthropic

# --- all ---
t "all runs the coding track"     0 'run_http.py'          B -n all anthropic m
t "all runs the agent track"      0 'run_agent.py'         B -n all anthropic m
t "all runs the reasoning track"  0 'run_reasoning.py'     B -n all anthropic m
t "all defaults to three passes"  0 '\-r 3'                B -n all anthropic m
t "all refuses a -g passthrough"  2 'always grades'        B -n all anthropic m -- -g

# --- speed ---
# A sweep stops llama-server on the box, so both arguments are required and
# neither is guessed at.
t "speed needs a box and a model" 2 'usage: ./bench.sh speed'      B -n speed
t "speed needs a model too"       2 'usage: ./bench.sh speed'      B -n speed leia
t "speed usage lists the models"  2 'Qwen3.8-27B'                  B -n speed
# the box, not the ssh host, decides the directory: with --host localhost the
# underlying script would otherwise write results/localhost/speed and strand the
# numbers away from the scores
t "speed writes under the box"    0 "run_llama_bench.sh .*results/leia/speed"  B -n speed leia all
t "the legacy pair still resolves" 0 '\-H localhost'              B -n speed leia all
t "speed collates afterwards"     0 'collate_bench.py'            B -n speed leia all
n "speed never writes results/localhost" 'results/localhost'      B -n speed leia all
n "all passes no --models filter" '\-\-models'                    B -n speed leia all
t "a model becomes --models"      0 "\-\-models Qwen3.8-27B"      B -n speed leia Qwen3.8-27B
t "several models are one list"   0 "\-\-models 'gpt-oss-20b-Q8,Qwen3.8-27B'" \
  B -n speed leia gpt-oss-20b-Q8 Qwen3.8-27B
t "commas separate models too"    0 "\-\-models 'gpt-oss-20b-Q8,Qwen3.8-27B'" \
  B -n speed leia gpt-oss-20b-Q8,Qwen3.8-27B
t "a .gguf name resolves to its label" 0 "\-\-models gpt-oss-20b-Q8" \
  B -n speed leia gpt-oss-20b-Q8_0.gguf
t "an unknown model exits 2"      2 "no model called 'nope'"      B -n speed leia nope
t "an unknown model lists them"   2 'gpt-oss-20b-Q4'              B -n speed leia nope
t "an ambiguous model exits 2"    2 'could mean any of'           B -n speed leia gemma
t "all excludes naming models"    2 'do not list it beside'       B -n speed leia all Qwen3.8-27B
# an unconfigured box is its own ssh target, which is the ordinary case
t "an unknown box sshes to itself" 0 '\-H otherbox'               B -n speed otherbox all
t "an unknown box gets its own dir" 0 'results/otherbox/speed'    B -n speed otherbox all
t "a per-box _SSH wins"           0 '\-H mac.local'               B -n speed mac all
t "a per-box _BINDIR wins"        0 '\-\-bin-dir /opt/homebrew/bin' B -n speed mac all
t "a box is not a path"           2 'is not a machine name'       B -n speed a/b all

# --- speed-table ---
# read-only: it must never reach the box, so a missing sweep is a usage error
# rather than collate_bench.py's alphabetical guess at another machine.
t "speed-table needs a box"       2 'usage: ./bench.sh speed-table' B -n speed-table
t "speed-table lists swept boxes" 2 'leia'                        B -n speed-table
t "speed-table calls the collator" 0 'collate_bench.py .*results/leia/speed' B -n speed-table leia
n "speed-table runs no sweep"     'run_llama_bench.sh'            B -n speed-table leia
t "speed-table passes flags through" 0 '\-o /tmp/x.md'            B -n speed-table leia -- -o /tmp/x.md
t "an unswept box is a usage error" 2 'has no speed sweep'        B speed-table nosuchbox

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
