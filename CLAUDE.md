# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A benchmark harness, not an application. Five self-contained coding problems in
four languages, each with an automated grader, totalling **68 checks**. You run
a model (or human) against the prompts, drop the deliverables into a folder, and
grade them. See [README.md](README.md) for the problem table and fairness rules.

Git repo on `main`, published at `kcsinclair/agent-benchmark`. Clone with
`--recurse-submodules`, or run `git submodule update --init` afterwards; without
the submodule nothing can be graded (see below).

**This repo is public. The harness is not.** Graders, reference solutions and
the hand-authored reasoning traps live in `kcsinclair/agent-benchmark-harness`,
a private repo mounted here as the `harness` submodule. Everything else —
prompts, runners, extraction, results, docs — is public so the results can be.

Consequences to keep in mind when working here:

- **Never move harness material into the public tree**, and never paste a
  grader, a reference solution or a trap into an issue, a commit message, or a
  file outside `harness/`. A leaked grader lets a model code to the hidden edge
  cases; a leaked trap cannot be regenerated, only rewritten.
- **Verbose grader output is grader material.** `run_all.sh` prints each check
  as `PASS  <what it checks>: '<literal input>' == <expected>`, so a full log
  restates the hidden edge cases in plain English. Do not commit a
  full run log to `results/`. `benchmark/scrub_results.py --check results/`
  exits 1 if one is there; without `--check` it strips the per-check lines and
  keeps the scores.
- **The submodule may legitimately be absent.** Anyone without access can run
  models and collect transcripts but cannot grade. `run_all.sh` exits 2 with a
  pointer instead of scoring 0/68, and the reasoning track drops to 88 items.
  Preserve that behaviour — a silent zero reads as a terrible submission.

## Commands

Grade a submission directory (paths are relative to your shell's cwd, not to the
script):

```bash
./benchmark/run_all.sh results/leia/oneshot/<model> "<label>"   # per-check detail + scorecard
./benchmark/run_all.sh -q results/leia/oneshot/<model>          # scorecard only
./benchmark/run_all.sh -o 4 results/leia/oneshot/<model>        # one problem (-o 1,3,5 also works)
./benchmark/run_all.sh -t 30 results/leia/oneshot/<model>       # override per-problem time limits
./benchmark/run_all.sh --no-race results/leia/oneshot/<model>   # problem 4 without the race detector
./benchmark/run_all.sh                               # defaults to benchmark/submissions
```

Exit status is meaningful: `0` = everything graded (a 0 score is a real
result), `1` = a problem could not be graded (missing toolchain, timeout) so
the total is incomplete, `2` = usage error. Check it before recording a score.

Verify the graders themselves — the reference solutions must score 68/68:

```bash
./benchmark/run_all.sh harness/solutions "reference"
```

Self-tests — run the matching one after touching either script:

```bash
./benchmark/test_run_all.sh            # 17 cases: hangs, compile failures, bad flags
./benchmark/test_extract_submission.sh # 11 cases: transcript shapes, full pipeline
```

Reasoning track (general ability, not coding — 102 items, six categories):

```bash
./reasoning/run_reasoning.py -r 3 <model-id>     # median of 3, per-category
./reasoning/run_reasoning.py -c state,trap <model-id>
./reasoning/test_reasoning.py                    # 21 checks on the generators
```

Five categories are generated from a seed and solved in Python and live in
`reasoning/categories.py`; the purpose traps are hand-authored and load from
`harness/reasoning/trap_items.py`, so without the submodule the track is 88
items, not 102, and those two totals are not comparable. Scores are NOT
comparable with the 68-check coding benchmark either. Real discrimination lives in `state` and `constraint` — abstention
and retrieval are at ceiling for every model tested and contribute free points.

Run `test_reasoning.py` after touching a generator: a generator whose computed
answer fails its own checker scores everyone zero and looks like a finding. It
has already caught a trap bank where every answer was "B".

Agent track and speed sweep:

```bash
./benchmark/run_agent.py -g <model-id>          # tool-use track
./benchmark/run_llama_bench.sh                  # stops llama-server on leia!
./benchmark/collate_bench.py                    # speed joined to scores
```

`run_agent.py` gives the model `write_file`/`read_file`/`list_files` and grades
what lands on disk. It has no test-running tool on purpose: exposing the graders
would leak the hidden edge cases and burn the benchmark. It records turns, tool
calls, malformed calls, stray files, and whether the model answered in prose
instead of calling anything.

Some models emit tool calls in their own syntax that llama.cpp does not parse
into `tool_calls` (Qwen3-Coder emits `<function=write_file><parameter=…>` as
plain text). `run_agent.py` recovers those but counts them separately — an
off-the-shelf agent would see nothing, so the two are not the same result.

`test_extract_submission.sh` stubs `llama-cli` with a script that replays the
reference solutions wrapped in prose, so it exercises `llama-cpp.sh` end to end
— prompt → transcript → extracted files → 68/68 — with no model and no GPU.
That is how to test the generation path while `leia` is unavailable.

Run one grader in isolation (each takes a submission dir and prints its own
`SCORE:` line):

```bash
python3 harness/problems/01-python-parse-duration/grade.py results/leia/oneshot/<model>/01-python-parse-duration
node    harness/problems/02-js-lru-ttl-cache/grade.mjs   results/leia/oneshot/<model>/02-js-lru-ttl-cache
python3 harness/problems/03-sql-analytics/grade.py       results/leia/oneshot/<model>/03-sql-analytics
python3 harness/problems/05-python-scheduler/grade.py    results/leia/oneshot/<model>/05-python-scheduler
```

Problem 4 has no standalone entry point: `grader.go` owns `func main`, so
`run_all.sh` copies `go.mod`, `grader.go`, and the submission's `pool.go` into a
temp dir and runs `go run -race .` there. To run it by hand, replicate that.

Four tracks, all documented in README.md and with results in RESULTS.md:
one-shot (`run_http.py`), agent/tool-use (`run_agent.py`), reasoning
(`reasoning/run_reasoning.py`), speed (`run_llama_bench.sh` +
`collate_bench.py`). The runners create their own output directories.
Machines are documented one file per box under `servers/`.

Run models on the llama.cpp server over HTTP — works from any machine, no local
llama.cpp needed. This is the preferred path:

```bash
./benchmark/run_http.py --list-models
./benchmark/run_http.py -g <model-id> [<model-id> ...]   # generate + grade
./benchmark/run_http.py --only 1,3 -g <model-id>
BENCH_SERVER=http://host:port ./benchmark/run_http.py <model-id>
```

Default server is `http://leia.packsin.com:7442` (llama-server with `--jinja`,
swapping models on demand — only one is resident, so a cold model costs a load).

**Thinking is disabled by default (`--think off`).** These are reasoning models,
and under greedy decoding they fall into repetition loops: gemma-4-26B spent all
16k tokens repeating one verification line and returned *empty* content — a 0
that says nothing about coding ability. `chat_template_kwargs.enable_thinking =
false` fixed it and was 18× faster (15s vs 272s, 17/20 vs 0/20). A repeat
penalty at temperature 0 did **not** help. Models whose template ignores the
switch are reported per request and recorded in the transcript metadata.

The reply's `content` and `reasoning_content` are saved separately, and only
`content` reaches the extractor — chain-of-thought is full of half-written code
blocks that would otherwise beat the real answer. Each request also writes a
`.meta.json` with finish reason, token usage, timing, and decode settings, so a
score can always be traced back to how it was produced.

Run a local llama.cpp model with `llama-cli` instead (only where llama.cpp is
installed — `leia`, not the Mac):

```bash
./llama-cpp.sh <model.gguf>              # -> results/<host>/oneshot/<model>/
./llama-cpp.sh --only 1,3 --grade <m>    # subset, then grade in place
MODELDIR=/srv/models ./llama-cpp.sh <m>  # or --model-dir
```

`llama-cli` is a completion front end with no agent loop: it streams an answer
rather than writing files. So the pipeline is transcript → extraction:
`results/<server>/oneshot/<model>/transcripts/<problem>.txt` keeps the raw output, and
`benchmark/extract_submission.py` lifts the code blocks into the filenames the
graders import. A transcript with no code block yields no file, which the
grader then reports as a missing deliverable — the honest result, not an error.

Extraction is heuristic, and the heuristics are the interesting part: a
filename mentioned just before a block wins; otherwise blocks are filtered by
language tag and by required signature (`def parse_duration`, `func Run(`) and
the *last* survivor wins, so a model that corrects itself gets its final
version graded; problem 3 maps four SQL blocks to `q1..q4` in order, or splits
one block containing all four; a transcript with no fences at all is used
whole. `benchmark/test_extract_submission.sh` pins all of that down.

Requirements: Python 3.10+, Node 20+, Go 1.22+ with a C compiler (for `-race`),
bash 3.2+. `timeout`/`gtimeout` is used when present; otherwise `run_all.sh`
falls back to a built-in watchdog, so coreutils is optional. A preflight prints
the resolved tool versions in the run header — quote it when reporting scores.

Note for macOS: `/usr/bin/python3` is 3.9 and shadows a newer Homebrew Python on
the default PATH, so `run_all.sh` probes `python3.14 … python3.10` by name
before falling back, and warns when only 3.9 is available (a submission using
3.10+ syntax would fail to import and score 0 unfairly).

**Portability status.** Every test so far ran on macOS with bash 3.2 and *no*
coreutils, i.e. the built-in watchdog path plus a stand-in `timeout` binary. The
Linux/bash-5/real-GNU-`timeout` combination has not been executed yet — that is
what the GitHub push is for. Run `benchmark/test_run_all.sh` there before
trusting any Linux scorecard, and if something differs, suspect `timeout`
semantics or interpreter discovery before suspecting the graders.

Scores are only comparable across machines when the toolchain matches: the run
header prints the resolved python/node/go versions and whether `-race` was
active. Quote that header alongside any score you record.

## Architecture

**The grader contract.** `run_all.sh` is language-agnostic: it shells out to
each grader, greps stdout for the last `SCORE: <n>/<m>` line, and sums. A grader
that crashes, times out, or fails to print that line scores 0 — which is
deliberate, since a non-compiling submission scoring 0 is signal. Any new
grader just has to print `PASS`/`FAIL` lines and end with `SCORE: n/m`.

Denominators are also declared in the `PROBLEMS` table at the top of
`run_all.sh` (`name|max|runtime|timeout|deliverables`), so a problem that fails
to run still contributes its real max to the total — a broken run reads 0/68,
never 0/11. If a harness gains or loses checks, the script warns about the
mismatch and trusts the grader; update the table to silence it. Adding a
problem means adding a row there plus a case in `exec_grader`.

**Graders are isolated and dependency-free.** Python graders load the submission
via `importlib.util.spec_from_file_location` against a hard-coded filename in
the submission dir; the JS grader dynamic-imports `cache.mjs` via
`pathToFileURL`. Nothing is installed, and nothing outside the standard library
is used. This is why the deliverable filenames in the prompts are strict
contracts — `parse_duration.py`, `cache.mjs`, `q1..q4.sql`, `pool.go`,
`scheduler.py`. Extra files in a submission dir are ignored.

**Graders compute expected answers independently.** Problem 3 seeds a
deterministic SQLite DB in memory and derives expected rows in Python rather
than with SQL, so a submission can't accidentally agree with a buggy reference.
Problem 5 checks against both a brute-force optimum (small n) and an
O(n log n) DP, plus a hard-timed large case. Randomised checks use fixed seeds,
so grading is deterministic.

**Timing and concurrency checks.** Problems 4 and 5 grade on wall-clock
behaviour (bounded concurrency, fail-fast cancellation, O(n log n) runtime).
Margins are generous, but a loaded machine can produce spurious failures — don't
grade while something heavy is running, and don't treat a single 4/5 timing
failure as conclusive.

## Layout and conventions

```
PROMPT_1..5.md                  verbatim copies of the five problems/*/PROMPT.md
benchmark/problems/<n>/PROMPT.md  what a contestant is given
harness/                          PRIVATE submodule (agent-benchmark-harness):
  problems/<n>/                     the graders
  solutions/<n>/                    reference solutions, must score 68/68
  reasoning/trap_items.py           the hand-authored trap bank
benchmark/scrub_results.py        strips grader detail out of results/
benchmark/submissions/            default grading target (currently empty)
results/<server>/{oneshot,agent,speed}/   all measured results, server first
servers/<name>.md                 specs and quirks of each machine
benchmark/extract_submission.py   transcript -> deliverable files
benchmark/test_run_all.sh         self-test for the grading script
benchmark/test_extract_submission.sh  self-test for extraction + llama-cpp.sh
llama-cpp.sh                      local model -> results/<host>/oneshot/ (needs llama.cpp)
benchmark/run_all.sh.orig         gitignored local draft; matches NO commit, so
                                  diff it before deleting — it is not a backup
results/leia/oneshot/<model>/<n>/            one directory per contestant
```

The root `PROMPT_*.md` files are byte-identical to the ones under
`benchmark/problems/`; if you edit a prompt, update both copies.

`harness/` must never be shown to a contestant — the graders contain hidden edge cases, and leaking them lets a
model code to the tests. When asked to "run the benchmark on X", hand over
prompts only.

Grading integrity rules that the harness can't enforce, from the README: take
each contestant's **first** answer, don't fix its syntax errors, and don't
re-prompt. If a model asks a clarifying question, the only reply is "Follow the
prompt."
