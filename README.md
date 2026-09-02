# TL;DR

# Get it and setup your environment
Check .env.example and docs [[RUNNING.md]]

You will need to ask for access to the harness submodule which is deliberately not public to keep it out of training data.  Happy to share to humans.

```
git clone --recurse-submodules git@github.com:kcsinclair/agent-benchmark.git
cd agent-benchmark
cp .env.example .env && chmod 600 .env    # then paste your key and profiles
./bench.sh doctor
./bench.sh selftest
```

# Run a benchmark
```
./bench.sh all google google/gemini-2.5-flash
```

# Scrub results to redact test results
```
./benchmark/scrub_results.py --check results/    # read-only, exit 1 if anything leaks
./benchmark/scrub_results.py results/            # rewrite in place
```

# Update summary table
```
./bench.sh table
```

# Coding Model Benchmark — 5 Problems, Mixed Languages

A small benchmark for comparing how well models (or humans) actually write code.
Five self-contained problems of graduated difficulty across four languages, each
with an automated grader: **68 checks**, every one decided by a script — no LLM
judge, no rubric, no credit for code that merely looks right.

| # | Problem | Language | Difficulty | Checks | What it probes |
|---|---------|----------|------------|--------|----------------|
| 1 | Duration string parser | Python | Easy | 20 | Spec reading, input validation, edge cases |
| 2 | LRU cache with TTL | JavaScript (Node) | Medium | 17 | Data-structure design, API contracts, injected clock |
| 3 | SQL analytics | SQLite | Medium | 8 | Joins, aggregation, filtering, ordering |
| 4 | Bounded worker pool | Go | Hard | 11 | Concurrency, cancellation, fail-fast, race-freedom |
| 5 | Weighted interval scheduling | Python | Hard | 12 | Algorithms, O(n log n) performance, reconstruction |

Four tracks run against it, measuring different things:

| track | what it asks | what it tells you |
|---|---|---|
| **one-shot** | answer the prompt once, in prose | raw code generation |
| **agent** | write the files using a `write_file` tool | whether it can drive a coding agent |
| **reasoning** | 102 generated items across six categories | general fitness to run an agent |
| **speed** | `llama-bench` at several context depths | tokens/sec, which decides if it is usable |

Measured results live in [RESULTS.md](RESULTS.md), with the headline findings
and charts in [SUMMARY.md](SUMMARY.md); the machine they came from is described
in [servers/leia.md](servers/leia.md).

**Not every model has been through every track.** Twelve have all four. Rows
marked ‡ in the results are a single pass on the one-shot and speed tracks only,
which — given that three-pass models swing by up to 17 points between identical
runs — places a model in a band rather than at a rank.

> **Full testing to follow for the gemma-4 suite.** The variants added on
> 2026-08-13 — `gemma-4-26B-A4B` at `Q8_K_XL`, the `ultra-uncensored-heretic`
> finetune, and the `E4B` and `E2B` small models — have one one-shot pass and a
> speed measurement each, and have not been run on the agent or reasoning
> tracks. Treat their numbers as a first look. They get three passes and the
> full four tracks in a later sweep, at which point the ‡ comes off.

## This repo is half the benchmark

The graders, the reference solutions and the hand-authored reasoning traps are
in a **private** repo, `agent-benchmark-harness`, mounted here as the `harness`
submodule. Prompts, runners, extraction, results and docs are public.

That split is what makes publishing the results safe. A grader carries the
hidden edge cases a contestant is supposed to derive from the spec, so a
published grader stops measuring anything — the model just codes to the tests.
The trap bank is worse: fourteen items written by hand, and unlike every other
reasoning category they cannot be regenerated from a seed if they leak.

With access to the submodule:

```bash
git submodule update --init          # or --recurse-submodules on clone
./benchmark/run_all.sh harness/solutions "reference"    # must print 68 / 68
```

Without it, everything except grading still works — you can run models and
collect transcripts. `run_all.sh` then stops with a pointer to this section
rather than scoring a silent 0/68, and the reasoning track runs 88 of its 102
items (the 14 traps being the private ones) and says so in its header.
`BENCH_HARNESS=/path/to/checkout` points at a copy held elsewhere.

Two things leak the harness without containing any of it, so check before
publishing a results tree:

```bash
./benchmark/scrub_results.py --check results/     # exits 1 if anything is exposed
```

A saved verbose run log is the grader in prose — `run_all.sh` prints one line
per check, of the form `PASS  <what it checks>: '<literal input>' == <expected>`,
which is most of what the grader knows. And a reasoning `items.json` carries the
answer key for the traps.
The scrubber drops the per-check lines, keeps every `SCORE:` line and the
scorecard, and redacts trap answers only.

## Quick start

Grade an existing submissions directory:

```bash
./benchmark/run_all.sh results/leia/oneshot/<model>/pass1 "Some Model"
```

Run a model and grade it in one pass. `bench.sh` takes a **profile** — a named
endpoint defined in the gitignored `.env`, carrying the URL, the key and the
provider pin — so the only thing you type per run is the model:

```bash
cp .env.example .env && chmod 600 .env   # then edit it
./bench.sh doctor                        # can this machine run and grade?
./bench.sh profiles                      # what is configured (never the keys)

./bench.sh oneshot3  <profile> <model>   # coding, 3 passes, graded
./bench.sh reasoning <profile> <model>   # reasoning track
./bench.sh all       <profile> <model>   # both, then one combined scorecard
./bench.sh speed                         # llama-bench sweep, collated
```

[RUNNING.md](RUNNING.md) covers setting a server up, configuring providers, and
the failure modes that produce a confident wrong number.

The wrapper only assembles flags the runners already accept, so every track is
still available directly — `./bench.sh -n <anything>` prints the command it
would run:

```bash
./benchmark/run_http.py --list-models
./benchmark/run_http.py -r 3 -g <model-id>          # one-shot, 3 passes
./benchmark/run_agent.py <model-id>                 # agent track (grades automatically)
./reasoning/run_reasoning.py -r 3 <model-id>        # reasoning, 3 passes
./benchmark/run_llama_bench.sh                      # speed, over ssh
./benchmark/collate_bench.py                        # join speed to scores
```

## How to run a fair comparison

1. **Give each contestant the prompt only.** Hand over the five
   `benchmark/problems/*/PROMPT.md` files — nothing else. Never show the
   `harness/` folders: the graders contain hidden edge cases, and showing them
   lets a contestant code to the tests.

2. **Collect the deliverables** into one folder per contestant, mirroring the
   problem names:

   ```
   01-python-parse-duration/parse_duration.py
   02-js-lru-ttl-cache/cache.mjs
   03-sql-analytics/q1.sql  q2.sql  q3.sql  q4.sql
   04-go-worker-pool/pool.go
   05-python-scheduler/scheduler.py
   ```

   Take each contestant's **first answer** — no retries, no fixing their syntax
   errors (a non-compiling submission scoring 0 is signal, not noise).

   `run_http.py`, `run_agent.py` and `llama-cpp.sh` do all of this for local
   models, keeping the raw replies under `transcripts/` and extracting the code
   blocks into the deliverable filenames.

3. **Grade:**

   ```bash
   ./benchmark/run_all.sh <dir> "<label>"
   ```

   Per-check PASS/FAIL detail and a scorecard. Useful flags (`--help` for all):
   `-q` scorecard only, `-o 4` a single problem, `-t N` per-problem time limit.

   The exit status says whether to trust the total: `0` everything graded (a 0
   score is a real result), `1` something could not be graded — missing
   toolchain or timeout — so the total is incomplete, `2` usage error.

## The reasoning track

Beyond coding: 102 items across state tracking, constraint satisfaction,
instruction compliance, abstention, purpose traps, and retrieval at depth.
Everything is graded mechanically — exact match, a number, or a regex, and
**no LLM judge anywhere**.

Five of the six categories are **generated from a seed and solved in Python**,
which is what makes the track trustworthy: no item exists as text a model could
have trained on, there are as many items as you want, and `--seed 2` produces a
completely fresh set if you ever suspect leakage. Those five generators are
public for the same reason — publishing a generator gives nothing away when the
items do not exist until you run it.

The purpose traps are the exception, because genuine surprise does not generate
well. They are hand-authored, they live in the private submodule, and they are
the only part of this track that a leak would permanently damage. Published
`items.json` files have their trap answers redacted by
`benchmark/scrub_results.py`; everything else, including every generated item's
expected answer, is left intact.

```bash
./reasoning/run_reasoning.py -r 3 <model-id>
./reasoning/run_reasoning.py -c state,constraint -n 40 <model-id>
./reasoning/test_reasoning.py          # 21 checks on the generators themselves
```

Run the self-test after touching a generator. It exists to catch the failure
that would otherwise look like a finding: a generator whose computed answer does
not satisfy its own checker scores every model zero. It has already caught a
trap bank where every correct answer was "B" — a model that always replied B
would have scored 100% and looked like the best reasoner in the fleet.

## Run it three times

**A single pass is one draw from a distribution, not a measurement.** On
llama.cpp, `temperature 0` is not reproducible: continuous batching, MoE routing
and a quantised KV cache make the numerics depend on batch and slot state. Five
identical requests for one problem here produced scores of 0, 0, 11, 0, 11 out
of 11.

The first single-pass sweep ranked three models 63 / 53 / 49; three passes put
all three at a median of **57**. Use `-r 3` and report the median with the
spread visible.

## Scoring reasoning models

**Extended thinking is disabled by default** (`--think off` in `run_http.py`).
Under greedy decoding these models fall into repetition loops and never reach an
answer — one model spent all 16,384 tokens repeating a single verification line
and returned empty content, scoring 0 on a problem it otherwise gets 17/20 on.
Disabling thinking fixed it and was 18× faster; a repeat penalty did not help.
Say so when quoting scores: they measure these models *without* extended
thinking. Some models (gpt-oss) ignore the switch and use `reasoning_effort`
instead — `--reasoning-effort` is there for those.

`reasoning_content` is saved next to each transcript but never fed to the
extractor: chain-of-thought is full of abandoned draft code blocks that would
beat the real answer.

## Requirements

- Python 3.10+ (problems 1, 3, 5 — standard library only)
- Node.js 20+ (problem 2)
- Go 1.22+ with a C compiler (problem 4 uses `go run -race`)
- bash 3.2+ (stock macOS is fine)

Nothing to install beyond those: every script here is standard library only.

`timeout`/`gtimeout` is used when installed; without it `run_all.sh` falls back
to its own watchdog, so GNU coreutils is not required. macOS ships Python 3.9 at
`/usr/bin/python3` — `run_all.sh` looks for a newer `python3.x` on PATH and
warns if it can only find 3.9, since submissions using 3.10+ syntax would
otherwise fail to load and score 0 unfairly.

`./bench.sh doctor` checks all of this on the machine you are about to run on,
and `./bench.sh selftest` follows it with every self-test plus the reference
solutions, which must score 68/68. Run both on a new box before recording a
score: a missing `node` or `go` caps the total silently, and a missing C
compiler drops the race detector from problem 4. See
[RUNNING.md](RUNNING.md) for the Linux setup.

## Fairness rules (worth enforcing)

- Same prompt text, verbatim, to every contestant; one attempt each.
- If a model asks clarifying questions, reply only: "Follow the prompt."
- Score strictly from the grader output. Ties can be broken by secondary
  criteria (runtime on problem 5's large case, code length, readability) — but
  report those separately from the objective score.
- Record the decode settings and the server alongside the score. The same model
  scores differently with thinking on or off, and runs 6× faster or slower on
  different hardware.
- Randomized checks use fixed seeds, so grading is deterministic; problem 4's
  timing checks have generous margins but avoid grading on a loaded machine.

## Contributing

Results from other machines and other models are welcome — that is most of what
a benchmark this small is short of. Open an issue before doing the work so we
can agree what to run and how to label it.

**Grading stays with me**, and that is the awkward part rather than a
formality: handing out the graders so contributors could score themselves is
precisely the leak the split above exists to prevent. So the workflow is
submission-based — you run the prompts and send the transcripts or the
submission directory, I grade them and record the result with its server and
toolchain header. `run_http.py` and `run_agent.py` produce exactly the right
shape, including the `.meta.json` files that say how each answer was decoded.

If you want to run the benchmark privately against your own graders, fork it and
write your own `harness` — the contract is one `SCORE: n/m` line on stdout.

## Layout

```
bench.sh                              one entry point for every track
.env.example                          profile template — copy to .env (gitignored)
RUNNING.md                            server setup and the day-to-day workflow
benchmark/problems/<name>/PROMPT.md   what you give to the contestant
harness/problems/<name>/              the grader — PRIVATE submodule
harness/solutions/<name>/             reference solutions — PRIVATE submodule
harness/reasoning/trap_items.py       hand-authored traps — PRIVATE submodule
benchmark/run_all.sh                  grades a directory, prints a scorecard
benchmark/scrub_results.py            strips grader detail out of results/
benchmark/run_http.py                 one-shot track against a llama.cpp server
benchmark/run_agent.py                agent / tool-use track
benchmark/extract_submission.py       transcript -> deliverable files
benchmark/run_llama_bench.sh          speed sweep over ssh
benchmark/collate_bench.py            joins speed to scores
benchmark/test_*.sh                   self-tests for the above, incl. bench.sh
reasoning/categories.py               item generators + mechanical checkers
reasoning/run_reasoning.py            reasoning track runner
reasoning/test_reasoning.py           self-test for the generators
llama-cpp.sh                          local llama-cli driver
servers/<name>.md                     one file per machine results came from
results/<server>/oneshot/<model>/      one-shot output (pass1..N per model)
results/<server>/agent/<model>/        agent track output
results/<server>/speed/                llama-bench json + run log
results/<server>/reasoning/<model>/    per-item reasoning results
```

Results are grouped **server first**:

```
results/leia/oneshot/gemma-4-26B-A4B-it-qat-UD-Q4_K_XL/pass1/01-python-parse-duration/…
results/leia/agent/gemma-4-26B-A4B-it-qat-UD-Q4_K_XL/01-python-parse-duration/…
results/leia/speed/gemma-4-26B.json
```

Server first rather than a `leia-gemma-4-26B` prefix, because model names are
already full of hyphens and dots — `leia-gemma-4-26B-A4B-it-qat-UD-Q4_K_XL` has
no parseable boundary — and because a contribution from someone else's machine
then arrives as one self-contained directory with a matching `servers/<name>.md`.
Both comparisons stay easy: `results/leia/*` is one machine's models,
`results/*/oneshot/gemma-4-26B-A4B` is one model across machines.

The runners derive this from the server they were pointed at, so it happens by
itself: `--server http://newbox:8080` writes to `results/newbox/…`. `--out`
overrides it. A directory suffixed `--llama-cli` is a transcript-extraction run
rather than an HTTP one.

## A note on interpretation

Scores measure functional correctness against the written spec — not style,
documentation, or maintainability. With 5 problems this is a useful screen, not
a rigorous eval. Treat a 5–10 point gap as noise; on the evidence in
[RESULTS.md](RESULTS.md), single-run error alone reaches ±11, so that band is if
anything generous. A 20+ point gap between medians of three is meaningful.
