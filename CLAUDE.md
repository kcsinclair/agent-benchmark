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

`bench.sh` is the front door and the thing to reach for first. It resolves a
**profile** — a named endpoint in the gitignored `.env` — into flags the runners
already accept, so it adds no behaviour of its own and scores produced through it
stay comparable with every row in RESULTS.md. `-n` prints the command instead of
running it, which is the fastest way to check what a profile expands to.

```bash
./bench.sh doctor [box]                  # toolchain, harness, profiles, ssh
./bench.sh selftest                      # 123 self-test cases, then reference = 68/68
./bench.sh profiles                      # what is configured; never prints a key
./bench.sh models    <profile> [filter]
./bench.sh oneshot   <profile> <model>…  # coding, 1 pass, graded
./bench.sh oneshot3  <profile> <model>…  # coding, 3 passes, graded
./bench.sh agent     <profile> <model>…  # tool-use, 1 pass, always graded
./bench.sh agent3    <profile> <model>…  # tool-use, 3 passes
./bench.sh reasoning <profile> <model>…
./bench.sh all       <profile> <model>…  # all three at 3 passes + scorecard
./bench.sh speed <box> <model|all>       # llama-bench sweep, then collate
./bench.sh speed-table <box>             # that table again, measuring nothing
./bench.sh table                         # one table of every score in results/
./bench.sh scrub -- --check              # redact traps before publishing
./bench.sh grade <dir> [label]           # -> run_all.sh
./bench.sh -n oneshot3 <profile> <model> # print the command, run nothing
./bench.sh oneshot <profile> <model> -- --think on   # after --, verbatim to the runner
```

Profiles are `BENCH_PROFILE_<NAME>_{URL,KEY,KEY_FILE,PROVIDER,LABEL,ARGS}`; only
`_URL` is required. `.env` is parsed by both `bench.sh` and
`run_http.read_dotenv` with the same rules and is never sourced. Two things
worth knowing when editing this:

- **`_LABEL` exists because `server_label()` collides.** It takes the first
  dot-segment of the hostname, so `api.openai.com` and `api.anthropic.com` both
  become `api`. `bench.sh` therefore always passes an explicit `--out
  results/<label>/<track>` rather than letting the runner derive it.
- **The key is bridged through `$OPENROUTER_API_KEY`**, which `load_key` checks
  first — that is why no runner needed changing. `resolve_profile` restores the
  pre-existing value between profiles, so walking every profile in one process
  (`profiles`, `doctor`) cannot report profile B as working on profile A's key.
  Auth still only attaches to `openrouter.ai` URLs; widening that means changing
  `is_openrouter`/`load_key`, not `bench.sh`.

`bench.sh speed <box> <model|all>` reaches the box over ssh even when it is the
local box, keeping one code path. **Both arguments are required** — a sweep
stops `llama-server` on the box for hours, so it is never entered by accident.
The box names `results/<box>/speed`, which is deliberately not the ssh host:
`run_llama_bench.sh` names its output after the host, and with
`BENCH_SPEED_HOST=localhost` the numbers would land in `results/localhost/speed`
where `collate_bench.py` can no longer join them to the scores. The legacy
`BENCH_SPEED_{HOST,LABEL,MODELDIR,BINDIR}` pair configures the box named by
`_LABEL`; a second box is `BENCH_SPEED_<BOX>_{SSH,MODELDIR,BINDIR}`, defaulting
to the box name as the ssh target. `speed` also passes the output directory to
`collate_bench.py` explicitly, whose no-argument default is the first
`results/*/speed` alphabetically.

Model labels are read back out of `run_llama_bench.sh --list` rather than
duplicated in `bench.sh`, so the `MODELS` table there stays the one place a
model is declared. A label matches case-insensitively, by `.gguf` basename, or
by unique substring; an unknown one prints the table and exits 2, an ambiguous
one prints the candidates. `all` sends no `--models` filter at all.

Full workflow, Linux setup and the failure modes are in RUNNING.md.

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
./benchmark/test_bench.sh              # 74 cases: profile resolution, track flags, key never printed
```

`test_bench.sh` runs entirely under `bench.sh -n` against a throwaway `.env`, so
it needs no model, no network and no grading. Two of its cases assert that a
dummy key never appears in any output — keep those if you touch `profiles` or
`key_source`.

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
./benchmark/run_agent.py <model-id>             # tool-use track (grades automatically)
./benchmark/run_llama_bench.sh                  # stops llama-server on leia!
./benchmark/collate_bench.py                    # speed joined to scores
./benchmark/collate_results.py                  # every score, across all labels
```

`bench.sh agent`/`agent3` is the profile-driven route to the same script, and
`bench.sh all` now runs coding, reasoning and agent — agent last, because it is
the dearest (every turn resends the whole conversation) and the likeliest to
fail for a reason unrelated to the answers, so the other two are on disk first.
The combined scorecard gained an agent column beside coding; both are out of 68
and differ only in whether the model had to operate a tool to score.

`run_agent.py` gives the model `write_file`/`read_file`/`list_files` and grades
whatever lands in `results/<server>/agent/<model>/`. Note there is **no `-g`**:
unlike `run_http.py`, grading here is unconditional, so passing `-g` is an
error that aborts the run before a single request — `track_agent` therefore
never adds it and rejects a `-- -g` passthrough up front, since in `all` that
would otherwise blow up only after the coding track had finished. It has no test-running tool
on purpose: exposing the graders
would leak the hidden edge cases and burn the benchmark. It records turns, tool
calls, malformed calls, stray files, and whether the model answered in prose
instead of calling anything.

Some models emit tool calls in their own syntax that llama.cpp does not parse
into `tool_calls` (Qwen3-Coder emits `<function=write_file><parameter=…>` as
plain text). `run_agent.py` recovers those but counts them separately — an
off-the-shelf agent would see nothing, so the two are not the same result.
OpenRouter normalises tool calls across vendors, so `native_calls` should read
zero there; the same model scoring differently local vs hosted **because of the
serving stack rather than the weights** is the point of running both.

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
Machines are documented one file per box under `servers/`. `servers/openrouter.md`
is the exception that proves the rule: OpenRouter is a router, not a machine, so
the unit that pins a hosted score is the **provider endpoint** recorded in each
`.meta.json`, not the server name in the path.

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

**Frontier models go through the same script**, pointed at OpenRouter. One
client, one code path — a per-vendor adapter layer would make every difference
between those layers a confound with the models they serve, which is the same
reason llama.cpp is a fair comparison across local models:

```bash
./benchmark/run_http.py -s https://openrouter.ai/api --list-models claude
./benchmark/run_http.py  -s https://openrouter.ai/api --provider Anthropic -g anthropic/claude-sonnet-5
./benchmark/run_agent.py -s https://openrouter.ai/api --provider Anthropic anthropic/claude-sonnet-5
./reasoning/run_reasoning.py -s https://openrouter.ai/api --provider Anthropic anthropic/claude-sonnet-5
```

All three tracks take the same `-s`, `--provider` and `--key-file`, and share
one payload builder (`run_http.decorate`), so "only the model varies" holds
across tracks as well as within one.

The key is read from `$OPENROUTER_API_KEY`, then `OPENROUTER_API_KEY=` in the
gitignored `.env`, then `--key-file` (default `~/.config/openrouter/key`). **This
repo is public — never commit a key, and never paste one into a transcript.**

Three things differ from the llama.cpp path and all three are traps:

- **`--provider` is not optional for a result you intend to publish**, and for
  open-weight models it is the whole experiment. One slug routes to many
  upstreams — `anthropic/claude-sonnet-5` has eight endpoints across Amazon
  Bedrock, Anthropic, Google and Azure, and `openai/gpt-oss-20b` has twelve
  spanning **bf16, fp8 and fp4** — and `allow_fallbacks: false` alone does *not*
  pin it: the first unpinned run here served from Amazon Bedrock. Since this
  benchmark scores Q4_K_M and Q8_0 as separate contestants, an unpinned
  open-weight run can silently be a worse quantisation than the local GGUF it is
  being compared against. List the endpoints and their quantisation with
  `/v1/models/<slug>/endpoints` before choosing. The runner records the served
  provider in every `.meta.json` and flags a pass that drew on more than one.
- **Decode parameters are per model, not fleet-wide.** Frontier Claude models
  reject `temperature`, so the runner drops it for any model whose
  `supported_parameters` omit it and prints `temperature OMITTED` instead of
  claiming a temperature the request did not carry. Thinking is likewise
  reported per model (`reasoning.effort`, not `chat_template_kwargs`) because it
  is on by default on some models and cannot be disabled on others. Treat
  OpenRouter's parameter list as a hint, not gospel — it lists `temperature` as
  supported on `claude-opus-5`, which the vendor docs say rejects it.
- **A refused thinking switch is probed for, retried, and remembered — never
  scored.** DeepInfra's gpt-oss and Google's Gemini endpoints reject
  `reasoning.effort: none` with *"Reasoning is mandatory for this endpoint and
  cannot be disabled"*. Before that was handled, gpt-oss-20b and gpt-oss-120b
  recorded **0/68 on every track** — a total failure that was really a rejected
  parameter the model never saw. `run_http.send` drops the switch, retries once,
  records `think=on (this endpoint mandates reasoning)`, and stores it in
  `opts["think_refused"][model]` so `decorate` sends the accepted shape from
  then on. `run_http.probe` triggers that discovery up front with a one-token
  request, because **no metadata predicts it** — those endpoints advertise both
  `reasoning` and `reasoning_effort` and refuse the value anyway, so the
  rejection is the only signal. Two reasons it is worth a request: the run
  header would otherwise claim `think=off` on requests that carry `think=on`,
  and every request would re-pay the rejection (15 on a 3-pass coding sweep, 306
  on a 3-pass reasoning run). `--no-probe` turns it off. Any new back end that
  refuses a decode parameter belongs in `send` too: a silent zero reads as a
  terrible model.
- **A run that was never routable is `unrun`, not a score.** `probe` returns a
  *fatal* error only for the deterministic class — "no endpoints found", i.e.
  the filters on the request emptied the endpoint list — because that will
  happen identically on every request. Five rules follow, and they are the
  whole point of the flag: the probe runs **before** `rm -rf base`, so a
  misconfigured run cannot destroy the previous good one; the model is skipped;
  the summary cell reads **`NOT RUN (see above)`**, never `FAILED TO LOAD`
  (nothing was loaded) and never `0/68` (nothing was asked); **no summary JSON
  is written when no model produced a pass**, since summaries are timestamped
  and never overwritten, so a junk one outlives every later run; and the
  process **exits 1**, which is what makes `bench.sh all` skip the reasoning
  track instead of hitting the same wall and printing the error twice.
  `explain_no_endpoints` says which filter did it — a `--provider` that serves
  none of this model, or a `max_tokens` above every endpoint's cap — because
  the two need opposite fixes.
- **Cost is billed, not estimated.** `usage.cost` lands in each `.meta.json` and
  totals in the summary, which makes cost-per-check nearly free to compute.
- **A provider can bill for tokens and return nothing.** Novita served
  `qwen/qwen3-coder-30b-a3b-instruct` with `content: None`, `reasoning: None`,
  `refusal: None` and `finish_reason: stop` while billing 791 completion
  tokens — three of five problems came back blank and the model scored 22/68
  against 57/68 locally. SiliconFlow, Alibaba and DigitalOcean all returned
  2700–3000 characters for the identical request, so it was the provider, not
  the model. `run_http.py` already prints `EMPTY answer — no content at all`
  for this; **read the trouble list before recording a score**, and when a
  hosted model scores far below its local GGUF, check `completion_tokens`
  against the transcript size before believing it.

**Open question — sampling is not actually held constant.** The runner sets
`temperature` and `max_tokens` and nothing else, so every other sampling knob
falls back to a default that differs between llama.cpp and each OpenRouter
provider. `qwen3-coder-30b` accepts `top_p`, `top_k` and `repetition_penalty`;
`gemma-4-31b` also accepts `min_p` and `top_a`. A default `repetition_penalty`
other than 1.0 changes the output **even at temperature 0**, because it
reweights the logits before the argmax — greedy decoding is not automatically
identical decoding. This is a live candidate for why two separate models
(gemma-4-31b, qwen3-coder-30b) scored *lower* hosted at higher precision than
they did locally at Q4: the serving stack's defaults, not the weights. Pinning
`top_p: 1, top_k: 0, repetition_penalty: 1` where `supported_parameters` allows
it would make decoding explicit rather than inherited — but it changes decode
semantics, so everything collected before the change becomes incomparable and
would need re-running. Decide before the next sweep, not during one.

Two caveats when reporting a frontier score. The 68-check coding track is
**saturated** — Claude Sonnet 5 scored 68/68 on its first answer for $0.05 — so
it no longer discriminates at the top; look to the reasoning `state`/`constraint`
categories, the agent track, and cost-per-check. And the five prompts have been
public on GitHub since the push, so a recent frontier model may have seen them
while a local GGUF from before it cannot have — say so next to the number.

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

**Portability status.** Every test up to the Linux move ran on macOS with bash
3.2 and *no* coreutils, i.e. the built-in watchdog path plus a stand-in
`timeout` binary. Linux exercises bash 5, real GNU `timeout` and a different
interpreter-discovery outcome for the first time. `./bench.sh doctor` followed by
`./bench.sh selftest` is the check to run on any new box before trusting a
scorecard from it, and if something differs, suspect `timeout` semantics or
interpreter discovery before suspecting the graders. A missing `node` or `go`
caps the total silently — `run_all.sh` exits 1 to say so, but `run_http.grade`
discards that exit code, which is why `doctor` checks for them up front.

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
bench.sh                        one entry point for every track, profile-driven
.env.example                    profile template; committed via a !negation in
                                .gitignore, which `.env.*` would otherwise eat
RUNNING.md                      server setup + day-to-day workflow
PROMPT_1..5.md                  verbatim copies of the five problems/*/PROMPT.md
benchmark/problems/<n>/PROMPT.md  what a contestant is given
harness/                          PRIVATE submodule (agent-benchmark-harness):
  problems/<n>/                     the graders
  solutions/<n>/                    reference solutions, must score 68/68
  reasoning/trap_items.py           the hand-authored trap bank
benchmark/scrub_results.py        strips grader detail out of results/
benchmark/collate_results.py      one table of every score across results/*/
                                  (summary-first; collate_bench.py is
                                  speed-first and needs a speed sweep)
benchmark/submissions/            default grading target (currently empty)
results/<server>/{oneshot,agent,speed}/   all measured results, server first
servers/<name>.md                 specs and quirks of each machine
servers/openrouter.md             the hosted "server": a router, not a box —
                                  the provider endpoint is the real unit
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
