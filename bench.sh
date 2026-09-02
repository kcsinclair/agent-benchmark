#!/usr/bin/env bash
# One entry point for every benchmark track, driven by named provider profiles.
#
# Usage:
#   ./bench.sh [options] <subcommand> [options] [profile] [model ...]
#
# A profile is a named endpoint defined in the gitignored .env file: a base URL,
# an optional API key, an optional OpenRouter upstream pin, and the results
# directory its runs belong to. It exists so that the thing you type is the
# thing that varies — the model — rather than four flags you have to remember
# identically every time, on a server where the whole point is repeating a sweep
# and comparing it against RESULTS.md.
#
#   BENCH_PROFILE_<NAME>_URL        base server URL          (required)
#   BENCH_PROFILE_<NAME>_KEY        API key                  (optional)
#   BENCH_PROFILE_<NAME>_KEY_FILE   path to a key file       (optional)
#   BENCH_PROFILE_<NAME>_PROVIDER   OpenRouter upstream pin  (optional)
#   BENCH_PROFILE_<NAME>_LABEL      results/<label>/ dir     (optional)
#   BENCH_PROFILE_<NAME>_ARGS       extra flags, every run   (optional)
#
# See .env.example for a working file, and RUNNING.md for the whole workflow.
#
# Subcommands:
#   profiles                     list the configured profiles (never the keys)
#   models    <profile> [filter] list the models the endpoint offers
#   oneshot   <profile> <model>… coding track, graded          (default 1 pass)
#   oneshot3  <profile> <model>… coding track, graded          (3 passes)
#   reasoning <profile> <model>… reasoning track               (default 1 pass)
#   all       <profile> <model>… coding + reasoning at 3 passes, then a
#                                combined scorecard
#   speed     [options]          llama-bench sweep on the local box, collated
#   table     [options]          one table of every score in results/
#   scrub     [--check] [dir]    redact trap answers and grader detail before
#                                publishing; --check only reports (exit 1 if
#                                anything leaks). Run it after every reasoning
#                                run — the track rewrites items.json each time.
#   grade     <dir> [label]      run the graders over a submission directory
#   doctor                       check this machine can run and grade
#   selftest                     run every self-test, then the reference
#                                solutions, which must score 68/68
#
# Options:
#   -r, --passes N   passes per track (oneshot3 and all default to 3)
#   -n, --dry-run    print the command that would run, and stop
#   -h, --help       this message
#   --               everything after this is appended to the runner verbatim,
#                    e.g.  -- --think on --reasoning-effort medium
#
# Exit status: 0 = every track ran, 1 = a track failed, 2 = usage error.

set -u

REPO="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="${BENCH_ENV:-$REPO/.env}"
HARNESS="${BENCH_HARNESS:-$REPO/harness}"

usage() { awk 'NR > 1 { if ($0 !~ /^#/) exit; sub(/^# ?/, ""); print }' "$0"; }
die() { echo "bench.sh: $*" >&2; exit 2; }

# ------------------------------------------------------------------- python --

# The same probe run_all.sh uses: stock macOS puts 3.9 at /usr/bin/python3 ahead
# of a newer one, and the runners' `env python3` shebang would then pick the
# wrong interpreter. Duplicated rather than shared because run_all.sh is a
# program, not a library.
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

# --------------------------------------------------------------------- .env --

# Parsed with the same rules as run_http.read_dotenv, so one file configures
# both. Deliberately not sourced: it holds a credential and is never executed.
# An already-exported variable wins, matching run_http.load_key's precedence.
load_dotenv() {
  local line name value
  [ -f "$ENV_FILE" ] || return 0
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line#"${line%%[![:space:]]*}"}"          # ltrim
    case "$line" in ''|'#'*) continue ;; *'='*) ;; *) continue ;; esac
    name="${line%%=*}"; value="${line#*=}"
    name="${name#export }"
    name="$(printf '%s' "$name" | tr '[:lower:]-' '[:upper:]_' | tr -cd 'A-Za-z0-9_')"
    case "$name" in ''|[0-9]*) continue ;; esac
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"       # rtrim
    case "$value" in
      \"*\") value="${value#\"}"; value="${value%\"}" ;;
      \'*\') value="${value#\'}"; value="${value%\'}" ;;
    esac
    [ -n "${!name:-}" ] || export "$name=$value"
  done < "$ENV_FILE"
}
load_dotenv

# Whatever the environment (or a bare OPENROUTER_API_KEY= line in .env) supplied
# before any profile was resolved. Captured so that resolving profile B cannot
# leave profile A's key in place — `profiles` and `doctor` walk every profile in
# one process, and an inherited key would report a working profile that is not.
BASE_KEY="${OPENROUTER_API_KEY:-}"

var_of() { printf 'BENCH_PROFILE_%s_%s' \
  "$(printf '%s' "$1" | tr '[:lower:]-' '[:upper:]_' | tr -cd 'A-Za-z0-9_')" "$2"; }

# Every name that has a _URL is a profile; anything else is a stray variable.
list_profile_names() {
  compgen -v 2>/dev/null | sed -n 's/^BENCH_PROFILE_\(.*\)_URL$/\1/p' \
    | tr '[:upper:]' '[:lower:]' | sort
}

P_NAME=""; P_URL=""; P_KEY=""; P_KEYFILE=""; P_PROVIDER=""; P_LABEL=""; P_ARGS=""

# http://leia.packsin.com:7442 -> leia, the same rule as run_http.server_label.
# Only a fallback: two hosts called api.* collide under it, which is exactly
# what _LABEL exists to prevent.
label_from_url() {
  local h="${1#*://}"; h="${h%%/*}"; h="${h%%:*}"
  echo "${h%%.*}"
}

resolve_profile() {
  local name="${1:-}" v
  [ -n "$name" ] || die "which profile? (./bench.sh profiles)"
  v="$(var_of "$name" URL)"; P_URL="${!v:-}"
  if [ -z "$P_URL" ]; then
    { echo "bench.sh: no profile '$name' in $ENV_FILE"
      echo "configured profiles:"
      if [ -n "$(list_profile_names)" ]; then list_profile_names | sed 's/^/  /'
      else echo "  (none — cp .env.example .env and edit it)"; fi
    } >&2
    exit 2
  fi
  P_NAME="$name"
  v="$(var_of "$name" KEY)";      P_KEY="${!v:-}"
  v="$(var_of "$name" KEY_FILE)"; P_KEYFILE="${!v:-}"
  v="$(var_of "$name" PROVIDER)"; P_PROVIDER="${!v:-}"
  v="$(var_of "$name" LABEL)";    P_LABEL="${!v:-}"
  v="$(var_of "$name" ARGS)";     P_ARGS="${!v:-}"
  [ -n "$P_LABEL" ] || P_LABEL="$(label_from_url "$P_URL")"
  # The runners check $OPENROUTER_API_KEY first, so exporting the profile's key
  # here needs no change to them. It is used as a header only: it never reaches
  # a transcript, a .meta.json, a summary, or anything this script prints.
  if [ -n "$P_KEY" ]; then export OPENROUTER_API_KEY="$P_KEY"
  elif [ -n "$BASE_KEY" ]; then export OPENROUTER_API_KEY="$BASE_KEY"
  else unset OPENROUTER_API_KEY
  fi
}

# Describes where the key came from, for `profiles` and `doctor`. Never prints
# the key, and never prints a prefix of it either — a public repo's transcripts
# are the last place a credential should be recoverable from.
key_source() {
  case "$P_URL" in
    *openrouter.ai*) ;;
    *) echo "n/a (no auth is sent to a non-OpenRouter URL)"; return ;;
  esac
  if [ -n "$P_KEY" ]; then echo "$(var_of "$P_NAME" KEY)"
  elif [ -n "$BASE_KEY" ]; then echo "OPENROUTER_API_KEY"
  elif [ -n "$P_KEYFILE" ] && [ -s "$P_KEYFILE" ]; then echo "$P_KEYFILE"
  elif [ -s "$HOME/.config/openrouter/key" ]; then echo "~/.config/openrouter/key"
  else echo "MISSING"
  fi
}

# --------------------------------------------------------------- assembling --

CMD=()
quoted() { # printable form of CMD, safe to paste back into a shell
  local a out=""
  for a in ${CMD[@]+"${CMD[@]}"}; do
    case "$a" in
      *[!A-Za-z0-9_./:=@-]*|'') out="$out '$(printf '%s' "$a" | sed "s/'/'\\\\''/g")'" ;;
      *) out="$out $a" ;;
    esac
  done
  printf '%s' "${out# }"
}

# The front of every runner invocation: endpoint, pin, and an explicit --out so
# results are grouped by the profile's label rather than by whatever
# server_label() makes of the hostname.
add_common() { # track
  CMD+=(-s "$P_URL")
  [ -z "$P_PROVIDER" ] || CMD+=(--provider "$P_PROVIDER")
  [ -z "$P_KEYFILE" ] || CMD+=(--key-file "$P_KEYFILE")
  CMD+=(--out "$REPO/results/$P_LABEL/$1")
  # deliberately unquoted: _ARGS is a flag list, not one argument
  # shellcheck disable=SC2206
  [ -z "$P_ARGS" ] || CMD+=($P_ARGS)
}

run_cmd() { # run CMD, or print it under --dry-run
  if [ "$DRY" = "1" ]; then echo "  $(quoted)"; return 0; fi
  "${CMD[@]}"
}

# ------------------------------------------------------------------- tracks --

track_oneshot() { # passes, models...
  local n="$1"; shift
  CMD=("$PYTHON" "$REPO/benchmark/run_http.py")
  add_common oneshot
  CMD+=(-r "$n" -g)
  CMD+=(${EXTRA[@]+"${EXTRA[@]}"})
  CMD+=("$@")
  run_cmd
}

track_reasoning() { # passes, models...
  local n="$1"; shift
  CMD=("$PYTHON" "$REPO/reasoning/run_reasoning.py")
  add_common reasoning
  CMD+=(-r "$n")
  CMD+=(${EXTRA[@]+"${EXTRA[@]}"})
  CMD+=("$@")
  run_cmd
}

# `all` ends with one scorecard instead of two tables scrolled a few hundred
# lines apart. Reads the newest summary of each track rather than re-deriving
# anything, so the numbers here are the runners' own.
combined_scorecard() { # models...
  [ -n "$PYTHON" ] || return 0
  "$PYTHON" - "$REPO/results/$P_LABEL" "$@" <<'PY'
import glob, json, os, sys

root, models = sys.argv[1], sys.argv[2:]

def newest(track, prefix):
    files = sorted(glob.glob(os.path.join(root, track, prefix + "-*.json")))
    if not files:
        return {}
    try:
        with open(files[-1]) as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    return {r.get("model"): r for r in data.get("results", [])}

code = newest("oneshot", "summary")
reason = newest("reasoning", "reasoning-summary")

def cell(rec, right, total):
    """median score over the passes, as the runners report it."""
    passes = (rec or {}).get("passes") or []
    got = sorted(p[right] for p in passes if right in p)
    if not got:
        return "—"
    return "%d/%s" % (got[len(got) // 2], passes[0].get(total, "?"))

def spent(rec):
    return sum(p.get("cost_usd", 0) for p in (rec or {}).get("passes") or [])

total_cost = 0.0
print()
print("  %-44s %10s %10s %10s" % ("model", "coding", "reasoning", "cost"))
print("  " + "-" * 76)
for m in models:
    c, r = code.get(m), reason.get(m)
    cost = spent(c) + spent(r)
    total_cost += cost
    print("  %-44s %10s %10s %10s"
          % (m[:44], cell(c, "score", "max"), cell(r, "right", "count"),
             ("$%.4f" % cost) if cost else "—"))
print("  " + "-" * 76)
if total_cost:
    print("  $%.4f billed in total." % total_cost)
print("  Medians. Per-pass scores, spread and timings are in the summary JSONs")
print("  under %s/." % root)
print("  A coding median of 68/68 is the ceiling: read the reasoning state and")
print("  constraint categories to tell strong models apart.")
PY
}

# -------------------------------------------------------------------- speed --

SPEED_HOST="${BENCH_SPEED_HOST:-localhost}"
SPEED_LABEL="${BENCH_SPEED_LABEL:-leia}"

# The speed sweep reaches the box over ssh even when that box is this box, so
# there is one code path whether the harness runs locally or remotely. The label
# is pinned because run_llama_bench.sh names its output directory after the ssh
# host: with --host localhost it would write results/localhost/speed, splitting
# the speed numbers away from the scores collate_bench.py joins them to.
cmd_speed() {
  local out="$REPO/results/$SPEED_LABEL/speed"
  CMD=("$REPO/benchmark/run_llama_bench.sh" -H "$SPEED_HOST" -o "$out")
  [ -z "${BENCH_SPEED_MODELDIR:-}" ] || CMD+=(--model-dir "$BENCH_SPEED_MODELDIR")
  [ -z "${BENCH_SPEED_BINDIR:-}" ] || CMD+=(--bin-dir "$BENCH_SPEED_BINDIR")
  CMD+=(${EXTRA[@]+"${EXTRA[@]}"})
  if [ "$DRY" = "1" ]; then
    echo "  $(quoted)"
    CMD=("$PYTHON" "$REPO/benchmark/collate_bench.py" "$out")
    echo "  $(quoted)"
    return 0
  fi
  "${CMD[@]}" || return 1
  echo
  # always passed explicitly: given no argument collate_bench.py takes the first
  # results/*/speed alphabetically, which need not be the one just written
  "$PYTHON" "$REPO/benchmark/collate_bench.py" "$out"
}

# ------------------------------------------------------------------- doctor --

reach() { # is there an OpenAI-compatible endpoint at this URL?
  [ -n "$PYTHON" ] || return 1
  "$PYTHON" - "$1" <<'PY' >/dev/null 2>&1
import sys, urllib.error, urllib.request
url = sys.argv[1].rstrip("/") + "/v1/models"
try:
    urllib.request.urlopen(urllib.request.Request(url), timeout=15).read(1)
except urllib.error.HTTPError as e:
    sys.exit(0 if e.code in (401, 403) else 1)   # reachable, merely unauthenticated
except Exception:
    sys.exit(1)
PY
}

DOC_FAIL=0
ck() { # label, ok|warn|fail, detail
  case "$2" in
    ok)   printf '  PASS  %-28s %s\n' "$1" "$3" ;;
    warn) printf '  WARN  %-28s %s\n' "$1" "$3" ;;
    *)    printf '  FAIL  %-28s %s\n' "$1" "$3"; DOC_FAIL=1 ;;
  esac
}

cmd_doctor() {
  local p names mode src
  echo "bench.sh doctor — $(uname -s) $(uname -r), bash ${BASH_VERSION%%(*}"

  echo
  echo "toolchain"
  case "$PY_RC" in
    0) ck python ok "$PYTHON $("$PYTHON" -c 'import platform;print(platform.python_version())')" ;;
    3) ck python fail "$("$PYTHON" -V 2>&1) is below the 3.10 minimum — submissions using 3.10+ syntax would score 0 unfairly" ;;
    *) ck python fail "no python3 found" ;;
  esac
  if command -v node >/dev/null 2>&1; then ck node ok "$(node -v)"
  else ck node fail "not found — problem 2 (17 checks) cannot be graded"; fi
  if command -v go >/dev/null 2>&1; then
    ck go ok "$(go env GOVERSION)"
    if [ "$(go env CGO_ENABLED 2>/dev/null)" = "1" ] && command -v cc >/dev/null 2>&1; then
      ck "C compiler (-race)" ok "$(go env CC)"
    else
      ck "C compiler (-race)" warn "absent — problem 4 runs without the race detector, so its score is not comparable"
    fi
  else
    ck go fail "not found — problem 4 (11 checks) cannot be graded"
  fi
  if command -v timeout >/dev/null 2>&1 || command -v gtimeout >/dev/null 2>&1; then
    ck timeout ok "present"
  else
    ck timeout warn "absent — run_all.sh uses its built-in watchdog instead"
  fi

  echo
  echo "harness"
  if [ -d "$HARNESS/problems" ]; then ck graders ok "$HARNESS/problems"
  else ck graders fail "missing — nothing can be graded: git submodule update --init"; fi
  if [ -f "$HARNESS/reasoning/trap_items.py" ]; then ck "reasoning traps" ok "102 items"
  else ck "reasoning traps" warn "absent — the reasoning track is 88 items, which is not comparable with a 102-item score"; fi

  echo
  echo "profiles ($ENV_FILE)"
  if [ ! -f "$ENV_FILE" ]; then
    ck ".env" fail "not found — cp .env.example .env"
  else
    mode="$(ls -l "$ENV_FILE" | cut -c1-10)"
    case "$mode" in
      -rw-------) ck ".env permissions" ok "$mode" ;;
      *) ck ".env permissions" warn "$mode — it holds a key: chmod 600 $ENV_FILE" ;;
    esac
  fi
  names="$(list_profile_names)"
  if [ -n "$names" ]; then ck profiles ok "$(echo "$names" | tr '\n' ' ')"
  else ck profiles fail "none defined — see .env.example"; fi
  for p in $names; do
    resolve_profile "$p"
    src="$(key_source)"
    if [ "$src" = "MISSING" ]; then
      ck "$p" fail "$P_URL — no key resolves, so every request would be rejected"
    elif reach "$P_URL"; then
      ck "$p" ok "$P_URL -> results/$P_LABEL${P_PROVIDER:+, pinned to $P_PROVIDER}"
    else
      ck "$p" fail "$P_URL is unreachable (/v1/models)"
    fi
  done

  echo
  echo "speed track (ssh $SPEED_HOST -> results/$SPEED_LABEL/speed)"
  if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SPEED_HOST" true 2>/dev/null; then
    ck "ssh $SPEED_HOST" ok "key-based login works"
    if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SPEED_HOST" \
         "bash -lc 'export PATH=${BENCH_SPEED_BINDIR:-/opt/local-ai/bin}:\$PATH; command -v llama-bench'" \
         >/dev/null 2>&1; then
      ck llama-bench ok "on the remote PATH"
    else
      ck llama-bench fail "not in ${BENCH_SPEED_BINDIR:-/opt/local-ai/bin} on $SPEED_HOST"
    fi
    if command -v loginctl >/dev/null 2>&1 &&
       [ "$(loginctl show-user "$USER" -p Linger --value 2>/dev/null)" = "yes" ]; then
      ck "systemd linger" ok "systemctl --user works over ssh"
    else
      ck "systemd linger" warn "off or unknown — stopping llama-server.service over ssh may fail: loginctl enable-linger $USER"
    fi
  else
    ck "ssh $SPEED_HOST" fail "no key-based login — ssh-copy-id $USER@$SPEED_HOST"
  fi

  echo
  if [ "$DOC_FAIL" = "0" ]; then
    echo "  Ready. Next: ./bench.sh selftest"
  else
    echo "  NOT ready — fix the FAIL lines above before recording any score." >&2
  fi
  return "$DOC_FAIL"
}

# ----------------------------------------------------------------- selftest --

cmd_selftest() {
  local rc=0
  echo "== run_all.sh ==";           "$REPO/benchmark/test_run_all.sh"           || rc=1
  echo; echo "== extract_submission =="; "$REPO/benchmark/test_extract_submission.sh" || rc=1
  echo; echo "== reasoning ==";      "$PYTHON" "$REPO/reasoning/test_reasoning.py" || rc=1
  echo; echo "== bench.sh ==";       "$REPO/benchmark/test_bench.sh"             || rc=1
  echo; echo "== reference solutions =="
  "$REPO/benchmark/run_all.sh" -q "$HARNESS/solutions" reference || rc=1
  echo
  if [ "$rc" = "0" ]; then
    echo "  All self-tests passed. A reference total of anything but 68/68 above"
    echo "  means the graders disagree with this machine, not with a model."
  else
    echo "  SELF-TESTS FAILED — do not record a score from this machine." >&2
  fi
  return "$rc"
}

# --------------------------------------------------------------------- main --

PASSES=""; DRY=0; EXTRA=(); ARGS=(); CMDNAME=""

# One loop for both sides of the subcommand, so `bench.sh -n oneshot leia m` and
# `bench.sh oneshot -n leia m` mean the same thing. The first bare word is the
# subcommand; the rest are its arguments.
while [ $# -gt 0 ]; do
  case "$1" in
    -r|--passes)
      [ $# -ge 2 ] || die "--passes needs an argument"
      case "$2" in ''|*[!0-9]*) die "--passes wants a whole number, got '$2'" ;; esac
      [ "$2" -ge 1 ] || die "--passes wants at least 1"
      PASSES="$2"; shift 2 ;;
    -n|--dry-run) DRY=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    --)           shift; EXTRA=("$@"); break ;;
    -*)           die "unknown option '$1' (try --help)" ;;
    *)
      if [ -z "$CMDNAME" ]; then CMDNAME="$1"; else ARGS+=("$1"); fi
      shift ;;
  esac
done
set -- ${ARGS[@]+"${ARGS[@]}"}

[ -n "$CMDNAME" ] || { usage; exit 2; }
[ -n "$PYTHON" ] || die "no python3 on PATH (./bench.sh doctor)"

case "$CMDNAME" in
  profiles)
    names="$(list_profile_names)"
    [ -n "$names" ] || { echo "no profiles in $ENV_FILE — cp .env.example .env"; exit 0; }
    printf '%-12s %-38s %-12s %-20s %s\n' PROFILE URL PROVIDER RESULTS KEY
    for p in $names; do
      resolve_profile "$p"
      printf '%-12s %-38s %-12s %-20s %s\n' \
        "$p" "$P_URL" "${P_PROVIDER:--}" "results/$P_LABEL" "$(key_source)"
    done ;;

  models)
    [ $# -ge 1 ] || die "usage: ./bench.sh models <profile> [filter]"
    resolve_profile "$1"; shift
    CMD=("$PYTHON" "$REPO/benchmark/run_http.py" -s "$P_URL" --list-models)
    [ -z "$P_KEYFILE" ] || CMD+=(--key-file "$P_KEYFILE")
    [ $# -eq 0 ] || CMD+=("$1")
    run_cmd ;;

  oneshot|oneshot3)
    [ $# -ge 2 ] || die "usage: ./bench.sh $CMDNAME <profile> <model> [model ...]"
    resolve_profile "$1"; shift
    if [ "$CMDNAME" = "oneshot3" ]; then track_oneshot "${PASSES:-3}" "$@"
    else track_oneshot "${PASSES:-1}" "$@"; fi ;;

  reasoning)
    [ $# -ge 2 ] || die "usage: ./bench.sh reasoning <profile> <model> [model ...]"
    resolve_profile "$1"; shift
    track_reasoning "${PASSES:-1}" "$@" ;;

  all)
    [ $# -ge 2 ] || die "usage: ./bench.sh all <profile> <model> [model ...]"
    resolve_profile "$1"; shift
    n="${PASSES:-3}"; rc=0
    echo "== coding, $n pass(es) =="
    if ! track_oneshot "$n" "$@"; then
      # The runners exit non-zero only when no model was asked anything, which
      # is a configuration error — the same one would stop the reasoning track
      # too, so running it just prints the error twice and writes nothing.
      echo >&2
      echo "bench.sh: the coding track ran no model, so the reasoning track" >&2
      echo "  was skipped. Fix the configuration above and re-run." >&2
      exit 1
    fi
    echo
    echo "== reasoning, $n pass(es) =="
    track_reasoning "$n" "$@" || { rc=1; echo "bench.sh: the reasoning track failed" >&2; }
    [ "$DRY" = "1" ] || combined_scorecard "$@"
    exit "$rc" ;;

  table)
    CMD=("$PYTHON" "$REPO/benchmark/collate_results.py"
         ${EXTRA[@]+"${EXTRA[@]}"} "$@")
    run_cmd ;;

  scrub)
    CMD=("$PYTHON" "$REPO/benchmark/scrub_results.py"
         ${EXTRA[@]+"${EXTRA[@]}"} "$@")
    [ $# -gt 0 ] || CMD+=("$REPO/results")
    run_cmd ;;

  speed)    cmd_speed ;;

  grade)
    [ $# -ge 1 ] || die "usage: ./bench.sh grade <dir> [label]"
    CMD=("$REPO/benchmark/run_all.sh" ${EXTRA[@]+"${EXTRA[@]}"} "$@")
    run_cmd ;;

  doctor)   cmd_doctor ;;
  selftest) cmd_selftest ;;
  help)     usage ;;
  *)        die "unknown subcommand '$CMDNAME' (try --help)" ;;
esac
