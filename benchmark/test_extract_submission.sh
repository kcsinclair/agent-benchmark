#!/usr/bin/env bash
# Self-test for extract_submission.py and llama-cpp.sh.
#
#   ./test_extract_submission.sh
#
# Builds synthetic transcripts in the shapes models actually answer in — prose
# then code, a draft followed by a correction, a usage example after the real
# answer, four SQL blocks labelled and unlabelled, bare source with no fences,
# prose with no code at all — and checks the right bytes land in the right
# filenames. The last case stubs llama-cli so the whole llama-cpp.sh pipeline
# runs end to end and the result is graded, with no model and no GPU.

set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"

# The stub llama-cli replays the reference solutions, and the round-trip case
# grades them — both live in the private harness submodule.
HARNESS="${BENCH_HARNESS:-$REPO/harness}"
[ -d "$HARNESS/solutions" ] || {
  echo "test_extract_submission.sh: no harness at $HARNESS" >&2
  echo "  git submodule update --init   (private repo; see README 'Contributing')" >&2
  exit 1
}
EXTRACT="$ROOT/extract_submission.py"

PY=""
for c in python3 python; do command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -n "$PY" ] || { echo "no python on PATH"; exit 1; }

TMP="$(mktemp -d "${TMPDIR:-/tmp}/extract_test.XXXXXX")" || exit 1
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS + 1)); }
bad()  { echo "  FAIL $1"; shift; [ $# -gt 0 ] && echo "$*" | sed 's/^/       | /'; FAIL=$((FAIL + 1)); }

# extract <problem> <transcript-file> -> $TMP/out
extract() {
  rm -rf "$TMP/out"
  "$PY" "$EXTRACT" "$1" "$2" "$TMP/out" > "$TMP/log" 2>&1
  return $?
}

echo "extract_submission.py self-test"

# --- prose, then one code block ---------------------------------------------
cat > "$TMP/t1.txt" <<'EOF'
Sure! Here is my implementation. I use a regular expression so that the unit
ordering rule is enforced by the pattern itself.

```python
import re

def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return 0.0
```

Let me know if you would like me to explain the regex.
EOF
if extract 01-python-parse-duration "$TMP/t1.txt" \
   && grep -q "def parse_duration" "$TMP/out/parse_duration.py" \
   && ! grep -q "Sure! Here" "$TMP/out/parse_duration.py"; then
  ok "prose + one block -> parse_duration.py"
else
  bad "prose + one block" "$(cat "$TMP/log")"
fi

# --- draft, then a corrected final version -----------------------------------
cat > "$TMP/t2.txt" <<'EOF'
First attempt:

```python
def parse_duration(text):
    return WRONG_FIRST_DRAFT
```

Wait — that misses the TypeError requirement. Corrected version:

```python
def parse_duration(text):
    return CORRECT_FINAL_VERSION
```
EOF
if extract 01-python-parse-duration "$TMP/t2.txt" \
   && grep -q CORRECT_FINAL_VERSION "$TMP/out/parse_duration.py" \
   && ! grep -q WRONG_FIRST_DRAFT "$TMP/out/parse_duration.py"; then
  ok "draft then correction -> the correction wins"
else
  bad "draft then correction" "$(cat "$TMP/out/parse_duration.py" 2>/dev/null)"
fi

# --- real answer, then a usage example ---------------------------------------
cat > "$TMP/t3.txt" <<'EOF'
Here is the cache:

```javascript
export class LruTtlCache {
  constructor({ capacity }) { this.capacity = capacity; }
}
```

Example usage:

```javascript
const c = new LruTtlCache({ capacity: 2 });
c.set("a", 1);
```
EOF
if extract 02-js-lru-ttl-cache "$TMP/t3.txt" \
   && grep -q "export class LruTtlCache" "$TMP/out/cache.mjs" \
   && ! grep -q 'c.set("a", 1)' "$TMP/out/cache.mjs"; then
  ok "answer + usage example -> the class, not the example"
else
  bad "answer + usage example" "$(cat "$TMP/out/cache.mjs" 2>/dev/null)"
fi

# --- four labelled SQL blocks -------------------------------------------------
cat > "$TMP/t4.txt" <<'EOF'
### q1.sql — revenue per customer
```sql
SELECT 'one';
```
### q2.sql — top products
```sql
SELECT 'two';
```
### q3.sql — customers with no orders
```sql
SELECT 'three';
```
### q4.sql — monthly revenue
```sql
SELECT 'four';
```
EOF
if extract 03-sql-analytics "$TMP/t4.txt" \
   && grep -q "'one'"   "$TMP/out/q1.sql" && grep -q "'two'"  "$TMP/out/q2.sql" \
   && grep -q "'three'" "$TMP/out/q3.sql" && grep -q "'four'" "$TMP/out/q4.sql"; then
  ok "four labelled SQL blocks -> q1..q4"
else
  bad "four labelled SQL blocks" "$(cat "$TMP/log")"
fi

# --- four unlabelled SQL blocks ----------------------------------------------
cat > "$TMP/t5.txt" <<'EOF'
Here are the four queries in order.

```sql
SELECT 'alpha';
```
```sql
SELECT 'beta';
```
```sql
SELECT 'gamma';
```
```sql
SELECT 'delta';
```
EOF
if extract 03-sql-analytics "$TMP/t5.txt" \
   && grep -q "'alpha'" "$TMP/out/q1.sql" && grep -q "'delta'" "$TMP/out/q4.sql"; then
  ok "four unlabelled SQL blocks -> mapped in order"
else
  bad "four unlabelled SQL blocks" "$(cat "$TMP/log")"
fi

# --- all four queries inside one block ---------------------------------------
cat > "$TMP/t6.txt" <<'EOF'
```sql
-- q1.sql
SELECT 'first';
-- q2.sql
SELECT 'second';
-- q3.sql
SELECT 'third';
-- q4.sql
SELECT 'fourth';
```
EOF
if extract 03-sql-analytics "$TMP/t6.txt" \
   && grep -q "'first'"  "$TMP/out/q1.sql" && grep -q "'fourth'" "$TMP/out/q4.sql" \
   && ! grep -q "'second'" "$TMP/out/q1.sql"; then
  ok "one block, four labelled queries -> split into q1..q4"
else
  bad "one block, four labelled queries" "$(cat "$TMP/log")"
fi

# --- bare source, no markdown -------------------------------------------------
cat > "$TMP/t7.txt" <<'EOF'
package main

import "context"

type Task func(ctx context.Context) (any, error)

func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	return nil, nil
}
EOF
if extract 04-go-worker-pool "$TMP/t7.txt" && grep -q "func Run(" "$TMP/out/pool.go"; then
  ok "bare source, no fences -> whole transcript"
else
  bad "bare source, no fences" "$(cat "$TMP/log")"
fi

# --- prose only, no code ------------------------------------------------------
printf 'I would approach this by using a regular expression, then validating.\n' \
  > "$TMP/t8.txt"
extract 05-python-scheduler "$TMP/t8.txt"; rc=$?
if [ "$rc" = "1" ] && [ ! -f "$TMP/out/scheduler.py" ] && grep -q MISSING "$TMP/log"; then
  ok "prose with no code -> nothing written, exit 1"
else
  bad "prose with no code" "rc=$rc; $(cat "$TMP/log")"
fi

# --- unknown problem / bad usage ---------------------------------------------
"$PY" "$EXTRACT" 99-nope "$TMP/t1.txt" "$TMP/out" >/dev/null 2>&1
[ $? = 2 ] && ok "unknown problem exits 2" || bad "unknown problem exit code"

# --- end to end through llama-cpp.sh, with a stubbed llama-cli ----------------
# The stub ignores the model and replays the reference solution wrapped in the
# prose a real model would surround it with, so the pipeline is exercised for
# real: prompt -> transcript -> extracted files -> grader.
mkdir -p "$TMP/bin"
cat > "$TMP/bin/llama-cli" <<'STUB'
#!/usr/bin/env bash
# stand-in for llama-cli: finds which PROMPT.md it was handed and echoes the
# matching reference solution as if a model had answered it
prompt=""
while [ $# -gt 0 ]; do
  case "$1" in -f) prompt="$2"; shift 2 ;; *) shift ;; esac
done
dir="$(basename "$(dirname "$prompt")")"
sol="$SOLUTIONS/$dir"
echo "Certainly. Here is my solution to $dir."
echo
case "$dir" in
  03-sql-analytics)
    for q in q1 q2 q3 q4; do
      echo "### $q.sql"
      echo '```sql'
      cat "$sol/$q.sql"
      echo '```'
    done ;;
  *)
    f="$(ls "$sol" | grep -vE '__pycache__|\.pyc$' | head -1)"
    case "$f" in
      *.py)  echo '```python' ;;
      *.mjs) echo '```javascript' ;;
      *.go)  echo '```go' ;;
      *)     echo '```' ;;
    esac
    cat "$sol/$f"
    echo '```' ;;
esac
echo
echo "Let me know if you would like the reasoning behind any of it."
STUB
chmod +x "$TMP/bin/llama-cli"
mkdir -p "$TMP/models" && : > "$TMP/models/stub-model.gguf"

( cd "$REPO" && env PATH="$TMP/bin:$PATH" SOLUTIONS="${BENCH_HARNESS:-$REPO/harness}/solutions" \
    ./llama-cpp.sh --model-dir "$TMP/models" stub-model.gguf ) > "$TMP/pipeline.log" 2>&1
rc=$?
# llama-cpp.sh writes to results/<host>/oneshot/<model>
STUB="$REPO/results/$(hostname -s)/oneshot/stub-model.gguf"
if [ "$rc" = 0 ] && [ -f "$STUB/01-python-parse-duration/parse_duration.py" ]; then
  ok "llama-cpp.sh produces a gradeable results/ directory"
else
  bad "llama-cpp.sh pipeline" "rc=$rc; $(tail -12 "$TMP/pipeline.log")"
fi

if "$ROOT/run_all.sh" -q "$STUB" "stub" 2>/dev/null | grep -q 'TOTAL *68 / 68'; then
  ok "extracted files grade 68/68 (round trip is lossless)"
else
  bad "extracted files grade 68/68" \
      "$("$ROOT/run_all.sh" -q "$STUB" stub 2>&1 | tail -12)"
fi
rm -rf "$STUB"
rmdir "$(dirname "$STUB")" "$(dirname "$(dirname "$STUB")")" 2>/dev/null || true

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
