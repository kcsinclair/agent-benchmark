# Running the benchmark from a server

`bench.sh` is the entry point for every track. It exists because a run is only
worth publishing if it was produced the same way as the runs it will be compared
against, and a hand-assembled command line is the easiest thing in this repo to
get subtly wrong — a forgotten `--provider` silently reroutes an open-weight
model to a different quantisation, and a forgotten `-r 3` reports one draw from
a distribution as a measurement.

The runners underneath are unchanged. `bench.sh` resolves a **profile** into the
flags they already accept, so anything it can do you can still do by hand, and
scores collected through it are directly comparable with everything already in
[RESULTS.md](RESULTS.md).

```bash
./bench.sh doctor                                    # can this machine run and grade?
./bench.sh selftest                                  # do the graders still agree with it?
./bench.sh oneshot3  anthropic anthropic/claude-sonnet-5    # coding, 3 passes, graded
./bench.sh agent     anthropic anthropic/claude-sonnet-5    # tool-use, always graded
./bench.sh reasoning anthropic anthropic/claude-sonnet-5    # 102 reasoning items
./bench.sh all       anthropic anthropic/claude-sonnet-5    # all three, then one scorecard
./bench.sh speed     leia all                        # llama-bench sweep, collated
```

## Set up a Linux box

**Everything here is standard library and stock tooling — there is nothing to
`pip install`.** The dependencies are the three language runtimes the problems
are written in, because the graders run the submissions.

```bash
sudo apt install -y python3 nodejs golang-go build-essential git openssh-client
git clone --recurse-submodules git@github.com:kcsinclair/agent-benchmark.git
cd agent-benchmark
```

If you cloned without `--recurse-submodules`, run `git submodule update --init`.
Without the `harness` submodule you can run models and collect transcripts but
you cannot grade anything, and the reasoning track quietly becomes 88 items
instead of 102 — which is not a score you can compare against any published row.
`doctor` checks for both.

Then, before recording any number from this machine:

```bash
./bench.sh doctor      # toolchain, harness, profiles, ssh — every line must PASS
./bench.sh selftest    # 123 self-test cases, then the reference solutions
```

`selftest` ends by grading the reference solutions, which **must** score 68/68.
Anything else means the graders disagree with this machine rather than with a
model, and every score it produces is suspect. This matters more than it sounds:
until this move, the whole harness had only ever been exercised on macOS with
bash 3.2 and no coreutils, so Linux exercises the GNU `timeout` path and bash 5
word-splitting for the first time. If something differs, suspect `timeout`
semantics or interpreter discovery before suspecting the graders.

Two failure modes `doctor` is specifically looking for, because both cost you
checks without ever printing an error:

- **No `node` or no `go`** — those problems are skipped and the total silently
  caps at 51/68 or 57/68. `run_all.sh` does exit 1 to say so, but the runners
  discard that exit code when they grade.
- **No C compiler** — problem 4 runs without `-race`, so data races go
  undetected and its 11 checks are not comparable with anyone else's.

## Configure your providers

Copy the template and fill it in:

```bash
cp .env.example .env && chmod 600 .env
```

A profile is a named endpoint. `BENCH_PROFILE_<NAME>_URL` is the only required
field; the rest are optional:

| variable | meaning |
|---|---|
| `_URL` | base server URL, passed to the runners as `-s` |
| `_KEY` | API key, used as a Bearer header and never printed |
| `_KEY_FILE` | path to a key file, if you would rather not put the key in `.env` |
| `_PROVIDER` | OpenRouter upstream pin, passed as `--provider` |
| `_LABEL` | which `results/<label>/` directory the runs belong to |
| `_ARGS` | extra runner flags applied to every run of this profile |

```sh
BENCH_PROFILE_ANTHROPIC_URL=https://openrouter.ai/api
BENCH_PROFILE_ANTHROPIC_PROVIDER=Anthropic
BENCH_PROFILE_ANTHROPIC_LABEL=openrouter
BENCH_PROFILE_ANTHROPIC_KEY=sk-or-v1-...

BENCH_PROFILE_LEIA_URL=http://localhost:7442      # the local llama.cpp server
BENCH_PROFILE_LEIA_LABEL=leia
```

`./bench.sh profiles` shows what resolved, naming where each key came from and
never the key itself. **This repo is public**: `.env` is gitignored, `.env.example`
is not, and a key committed here is a key published.

`_LABEL` is worth setting explicitly. Without it the results directory is the
first dot-segment of the hostname, which is fine for `leia.packsin.com` and
useless the moment you add a second endpoint called `api.something` — both would
land in `results/api/`.

Auth is only attached to URLs containing `openrouter.ai`, so a profile pointing
at some other authenticated endpoint would send an unauthenticated request. That
is a limit of the current runners, not of the profile format; `profiles` prints
`n/a` for those URLs rather than pretending a key is in play.

## Run a model

```bash
./bench.sh models    anthropic claude          # what the endpoint offers, filtered
./bench.sh oneshot   anthropic <model>         # coding, one pass, graded
./bench.sh oneshot3  anthropic <model>         # coding, three passes, graded
./bench.sh agent     anthropic <model>         # tool-use, one pass, always graded
./bench.sh agent3    anthropic <model>         # tool-use, three passes
./bench.sh reasoning anthropic <model> -r 3    # reasoning, three passes
./bench.sh all       anthropic <model>         # all three at three passes, one scorecard
```

`agent` is the same 68 checks as `oneshot` against the same endpoint; what
changes is that the model has to drive `write_file` to score at all, so a model
that writes perfect code into the chat window scores zero. There is no `-g`:
`run_agent.py` always grades, and `bench.sh` refuses a `-- -g` passthrough up
front rather than letting the run abort after the coding track has already
finished.

`all` runs coding, then reasoning, then agent, and ends with one scorecard
covering all three. Agent goes last on purpose: it is the dearest track — every
turn resends the whole conversation — and the one most likely to fail for a
reason that has nothing to do with the answers, so the other two are on disk
before it starts. Budget for it: a full `all` costs appreciably more than the
`oneshot3` + `reasoning` pair it used to be.

Useful flags, in front of or behind the subcommand — both are accepted:

```bash
./bench.sh -n oneshot3 anthropic <model>       # print the command, run nothing
./bench.sh -r 5 oneshot anthropic <model>      # five passes
./bench.sh oneshot anthropic <model> -- --think on --reasoning-effort medium
./bench.sh oneshot anthropic <model> -- -o 1,3 # only problems 1 and 3
```

Everything after `--` reaches the runner verbatim, so the full flag surface of
`run_http.py`, `run_agent.py` and `run_reasoning.py` is still available without
`bench.sh` having to mirror it.

Several models in one invocation is one line:

```bash
./bench.sh all anthropic anthropic/claude-sonnet-5 openai/gpt-5 google/gemini-3-pro
```

**Pin the provider.** For a hosted open-weight model this is the whole
experiment, not a detail. One slug routes to many upstreams —
`openai/gpt-oss-20b` has twelve spanning bf16, fp8 and fp4 — and since this
benchmark scores Q4_K_M and Q8_0 as separate contestants, an unpinned run can
quietly be a worse quantisation than the local GGUF you are comparing it to.
`allow_fallbacks: false` alone does not pin it; the first unpinned run in this
repo served from Amazon Bedrock. List what a slug actually offers first:

```bash
curl -s https://openrouter.ai/api/v1/models/<slug>/endpoints | python3 -m json.tool
```

Then give that upstream its own profile. The runner records the served provider
in every `.meta.json` and flags any pass that drew on more than one.

**But the prefix is not the provider.** `google/gemma-4-31b-it` is served by 16
endpoints, none of them Google — the prefix names who *made* the weights.
Pinning `--provider Google` there empties the endpoint list and returns a bare
404. For closed models the prefix usually is the provider (`anthropic/`,
`openai/`); for open-weight ones it never reliably is. So keep one profile per
serving provider, not one per model vendor:

```sh
BENCH_PROFILE_NOVITA_URL=https://openrouter.ai/api
BENCH_PROFILE_NOVITA_PROVIDER=Novita
BENCH_PROFILE_NOVITA_LABEL=or-novita
```

And prefer a provider that offers exactly **one** endpoint for the slug: a
provider pin is not a quantisation pin. DeepInfra serves `gemma-4-31b-it` at
fp4 *and* fp8 under one name, and `.meta.json` records only the name — so the
pinned run can silently change precision between passes.

## The speed track runs on the box itself

```bash
./bench.sh speed leia all                    # every model on leia, then collate
./bench.sh speed leia Qwen3.8-27B gpt-oss-120b   # just these two
./bench.sh speed leia gpt-oss-20b-Q8_0.gguf  # a .gguf name resolves to its label
./bench.sh -n speed leia all                 # show the two commands, run nothing
./bench.sh speed                             # usage, and the model table
./bench.sh speed-table leia                  # the table again, measuring nothing
```

**Both arguments are required.** A sweep stops the llama.cpp server on the box
it names, so neither the box nor the model list is defaulted into — an
absent-minded `./bench.sh speed` used to take the whole endpoint down for hours.
An unknown model is a usage error listing the table rather than a sweep that
silently measures nothing; an ambiguous one (`gemma`) lists the candidates.

The box names `results/<box>/speed` — the same directory its scores live in,
which is what `collate_bench.py` joins on — and is the ssh target too unless
`.env` says otherwise. `BENCH_SPEED_{HOST,LABEL}` configures the box named by
`BENCH_SPEED_LABEL` (on leia: label `leia`, reached over ssh at whatever
`BENCH_SPEED_HOST` says); any second box is `BENCH_SPEED_<BOX>_{SSH,MODELDIR,BINDIR}`.

The model table itself lives in `benchmark/run_llama_bench.sh` — adding a model
there is what makes it selectable here. Anything after `--` still reaches that
script verbatim (`./bench.sh speed leia all -- -r 5 -c 120`).

`speed-table` is the read-only half: the same table over numbers already
measured, joined to the one-shot and agent scores. It touches nothing on the box,
so unlike a sweep it is safe to run while the endpoint is serving.

```bash
./bench.sh speed-table leia                  # the table this box's sweep produced
./bench.sh speed-table leia -- -o table.md   # write it out instead of printing
./bench.sh speed-table                       # usage, and which boxes have a sweep
```

It takes a box for the same reason `speed` does: `collate_bench.py`'s own default
is the first `results/*/speed` alphabetically, which is a quiet way to read
another machine's numbers. A box with no sweep is a usage error naming the ones
that have one, not an empty table.

This is speed-first and covers one box, the one-shot track and the agent track.
`./bench.sh table` is the complement — every score in `results/`, hosted
endpoints included, but no speed columns. Nothing merges the two.

**This stops `llama-server` for the duration.** The router keeps up to three
models resident, which is memory `llama-bench` needs, and `models_autoload`
means a single stray request would reload one mid-measurement. It is restarted
on exit, including on Ctrl-C — but anything depending on that endpoint is down
while the sweep runs, and a full sweep is not quick.

It reaches the box over ssh even when the box is this box, so there is one code
path whether the harness runs locally or remotely. That needs two things, both
checked by `doctor`:

```bash
ssh-copy-id "$USER@localhost"        # key-based login, BatchMode=yes must work
loginctl enable-linger "$USER"       # or `systemctl --user stop` fails over ssh
```

Without lingering, the systemd user session does not survive a non-login ssh
connection, the stop fails, and the sweep dies before measuring anything.

The box argument is not cosmetic. `run_llama_bench.sh` names its output
directory after the ssh host, so with `BENCH_SPEED_HOST=localhost` the numbers
would land in `results/localhost/speed`, stranded from the scores in
`results/leia/` that `collate_bench.py` joins them to — which is why `bench.sh`
derives the directory from the box you named and passes it explicitly. It passes
it to the collator for the same reason: given no argument,
`collate_bench.py` takes the first `results/*/speed` alphabetically, which need
not be the one just written.

## What each track writes where

```
results/<label>/oneshot/<model>/            one pass  (-r 1)
results/<label>/oneshot/<model>/passN/      several passes
                        transcripts/<problem>.txt           raw reply
                        transcripts/<problem>.reasoning.txt  chain of thought, if any
                        transcripts/<problem>.meta.json      provider, usage, decode, timing
                        <problem>/<deliverables>            extracted, and what gets graded
results/<label>/oneshot/summary-<ts>.json   one per invocation, never overwritten
results/<label>/agent/<model>[/passN]/<problem>/<deliverables>   what it wrote
results/<label>/agent/agent-summary-<ts>.json   plus turns, tool calls, bad calls
results/<label>/reasoning/<model>[/passN]/items.json
results/<label>/reasoning/reasoning-summary-<ts>.json
results/<label>/speed/<model>.json          llama-bench output, plus runlog.jsonl
```

## Run, scrub, publish

`results/` is committed, so a run is not finished until it has been scrubbed:

```bash
./bench.sh all <profile> <model>       # 1. measure
./bench.sh scrub -- --check            # 2. what would leak? exit 1 if anything
./bench.sh scrub                       # 3. redact in place
./bench.sh table                       # 4. the table to paste into RESULTS.md
git add results/ && git commit         # 5. publish
```

**Step 2 is not one-and-done.** The reasoning track rewrites `items.json` on
every pass, so fresh trap answers reappear after every reasoning run — scrub
before each push, not once. Two things leak, and both are unrecoverable if
published: verbose `PASS`/`FAIL` grader output, which restates the hidden edge
cases in plain English, and the `expected`/`reply` fields of **trap** items,
which are a straight answer key for a hand-authored bank that cannot be
regenerated. Scores, timings, tokens, costs and all five generated categories
survive — the point is to publish results, not to redact them.

## One table of everything

`bench.sh table` walks every summary under `results/` and prints one row per
(results directory, model):

```bash
./bench.sh table                                  # markdown, best coding score first
./bench.sh table -- --plain                       # aligned text
./bench.sh table -- --label 'or-*' --sort cost    # only hosted, cheapest first
./bench.sh table -- -o /tmp/table.md
```

**One row per results directory, not per model.** The same weights served at a
different quantisation are a different contestant — `gemma-4-26b` on Parasail
(bf16) and on DeepInfra (fp8) are two rows, and the provider column says which.

Summaries are timestamped and never overwritten, so a re-run leaves several
behind; the newest wins per model per track. A model that was never routable is
absent rather than recorded as zero.

This is not `collate_bench.py`, which is speed-first: that one starts from a
`results/<server>/speed/` directory of llama-bench JSON, so it only works for a
machine that has a speed sweep and only covers oneshot and agent.

## Things that will bite you

**One pass is one draw, not a measurement.** At `temperature 0` on llama.cpp,
continuous batching and a quantised KV cache make the numerics depend on batch
and slot state; five identical requests for one problem scored 0, 0, 11, 0, 11
out of 11. gpt-oss-20b-Q8 scored 51, 65 and 68 across three identical passes.
Use `oneshot3` or `all` and report the median with the spread visible.

**The output layout changes shape at `-r 1`.** One pass writes deliverables
directly into `results/<label>/oneshot/<model>/`; two or more write
`.../<model>/pass1/`, `pass2/`… So a grading path that worked for a single-pass
run is wrong for a three-pass one, and vice versa.

**A `~` in a model id is part of the slug, and your shell will eat it.**
`./bench.sh oneshot3 google ~google/gemini-flash-latest` dies in zsh with `no
such user or named directory: google` before `bench.sh` sees anything — quote
it. `~` also marks a floating alias, which exposes no endpoints to pin and
silently changes what it serves; `~google/gemini-flash-latest` is
`google/gemini-3.7-flash` today. Record the concrete slug, or the row is not
reproducible and the same model shows up twice under two directory names.

**A re-run deletes the previous one.** The runners `rm -rf` the model directory
before starting, unless `-k` or `-o` was passed. Add `-- -k` if you are
re-running a subset and want to keep what is already there.

**A provider can bill for tokens and return nothing.** Novita served
`qwen/qwen3-coder-30b-a3b-instruct` with no content at all, `finish_reason:
stop`, and 791 completion tokens billed; three of five problems came back blank
and it scored 22/68 against 57/68 locally. Other providers returned normal
answers to the identical request. The runner prints `EMPTY answer — no content
at all` when this happens — read the trouble list before recording a score, and
when a hosted model scores far below its local GGUF, check `completion_tokens`
against the transcript size before believing it.

**Some endpoints mandate reasoning, and nothing advertises it.** DeepInfra's
gpt-oss and Google's Gemini both list `reasoning` and `reasoning_effort` as
supported, then reject `effort: none` outright. A one-token **probe** runs
before each model to settle this, so the run header states the decode that will
actually be sent and the refusal is discovered once instead of on every
request. If you already know an endpoint mandates it, skip even that round trip
from the profile:

```sh
BENCH_PROFILE_GOOGLE_ARGS=--think on
```

`-- --no-probe` disables the probe, at the cost of a header that can claim a
setting the requests do not carry.

**Thinking is off by default, and some models ignore that.** These are reasoning
models, and under greedy decoding they fall into repetition loops — gemma-4-26B
once spent all 16k tokens repeating one verification line and returned empty
content, a 0 that says nothing about coding ability. Where the switch is
refused or unavailable it is reported per request and recorded in the
transcript metadata, rather than claimed.

**Sampling is not actually held constant.** The runners set `temperature` and
`max_tokens` and nothing else, so every other knob falls back to a default that
differs between llama.cpp and each OpenRouter provider. A `repetition_penalty`
other than 1.0 changes the output even at temperature 0, because it reweights
the logits before the argmax. This is a live candidate for why two models scored
*lower* hosted at higher precision than they did locally at Q4.

**The five prompts have been public on GitHub since the push.** A recent
frontier model may have seen them; a local GGUF from before it cannot have. Say
so next to the number. And the coding track is saturated at the top — Claude
Sonnet 5 scored 68/68 on its first answer for $0.05 — so look to the reasoning
`state` and `constraint` categories, the agent track, and cost-per-check to tell
strong models apart.

## What bench.sh runs underneath

Nothing here is exclusive to the wrapper. `./bench.sh -n <anything>` prints the
exact command, which you can paste and modify:

```bash
./bench.sh -n all anthropic anthropic/claude-sonnet-5
#   python3 benchmark/run_http.py -s https://openrouter.ai/api --provider Anthropic \
#       --out results/openrouter/oneshot -r 3 -g anthropic/claude-sonnet-5
#   python3 reasoning/run_reasoning.py -s https://openrouter.ai/api --provider Anthropic \
#       --out results/openrouter/reasoning -r 3 anthropic/claude-sonnet-5
```

The agent/tool-use track is not wrapped yet; run it directly, with the same
flags:

```bash
./benchmark/run_agent.py -s https://openrouter.ai/api --provider Anthropic \
    --out results/openrouter/agent anthropic/claude-sonnet-5
```
