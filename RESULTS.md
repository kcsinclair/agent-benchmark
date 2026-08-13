# Results

Every score here comes from [leia](servers/leia.md) unless stated otherwise.
Scores are not portable between machines *as speed*, and are only portable *as
accuracy* if the decode settings match — so both are recorded.

**Read the caveats before quoting any of this.** The headline finding of the
first sweep was not which model wins; it was that a single run of this benchmark
is not a measurement.

## One-shot track

Model gets the prompt, answers once, code blocks are extracted from the reply.
`temperature 0`, thinking disabled, `max_tokens 16384`, 3 passes. Run 2026-07-31
(first sweep) and 2026-08-04 (second sweep), identical settings.

| model | median | passes | pass time | run |
|---|---|---|---|---|
| Muse-Glimmer-30B (Q8_K_XL) † | **68/68** | 68 — *one pass only* | 73 min | 08-12 |
| gpt-oss-120b-MXFP4 | **68/68** | 68 · 68 · 68 | 3.5 min | 07-31 |
| gemma-4-31B-it-qat | **68/68** | 68 · 68 · 68 | 5.3 min | 07-31 |
| gemma-4-26B-A4B-it-qat | 65/68 | 54 · 65 · 65 | 1.3 min | 07-31 |
| gpt-oss-20b-Q8_0 | 65/68 | 51 · 65 · 68 | 6.1 min | 08-04 |
| Qwen3-Coder-30B-A3B | 57/68 | 56 · 57 · 58 | 0.7 min | 07-31 |
| Qwen3.6-27B | 57/68 | 57 · 57 · 66 | 7 min | 07-31 |
| Qwen3.6-35B-A3B | 57/68 | 53 · 57 · 57 | 4.3 min | 07-31 |
| Qwen3VL-8B-Uncensored | 31/68 | 45 · 31 · 31 | 22.5 min | 08-04 |
| gpt-oss-20b-Q4_K_M | 25/68 | 37 · 25 · 24 | 10.4 min | 08-04 |
| Hermes-4-14B | 23/68 | 23 · 22 · 31 | 3.2 min | 08-04 |
| Meta-Llama-3.1-8B-Instruct | 19/68 | 19 · 19 · 19 | 1.2 min | 08-04 |
| Llama-3-14B-Instruct-v1 | 0/68 | 0 · 0 · 0 | 15.0 min | 08-04 |
| Kimi-Linear-48B-A3B | — | fails to load | — | — |

† **Muse-Glimmer-30B is one pass, not three, and on a different llama.cpp
build.** Every other row was produced on `b9892-ee445f93d`; this architecture
did not exist in that build, so leia was upgraded to `b10380-0b1bad14f` on
08-12 to run it (see [servers/leia.md](servers/leia.md)). Qwen3-Coder-30B re-run
on the new build scored 56/68, inside its recorded 56 · 57 · 58 spread, which is
the only evidence so far that the two builds are comparable. Given the sweep's
own headline finding — one run is not a measurement — a single 68/68 should be
read as "did not drop a single check on the day", not as a tie with the two
models that held 68 across three passes.

Its problem 2 was generated on a **second attempt after the first request hit
the harness's 1800s timeout with no reply at all**. Nothing of the model's first
answer existed to preserve, so this is not a re-prompt under the README rules —
but it is the reason the row is dated 08-12 rather than being a clean single
sitting, and it is recorded here rather than left implicit.

**Muse-Glimmer ignores `enable_thinking: false` silently.** Every request was
sent with the switch and logged as `think=off`, and every one came back with
`reasoning_content` — 38k characters on problem 2, 48k on problem 4. The
template neither errors nor honours it, so `run_http.py`'s retry path (which
only catches templates that *reject* the switch) does not fire and the metadata
records `think=off` for a run that plainly thought. The reasoning is saved
separately and never reaches the extractor, so the scores are unaffected; the
`mode` field is what is wrong.

That verbosity is most of the cost. At **7.3 tok/s** — dense 30B at Q8, 32 GB of
weights, bandwidth-bound on this box exactly as the dense/MoE split in
[servers/leia.md](servers/leia.md) predicts — it spent 9,573 and 10,947
completion tokens on problems 2 and 4 alone. 73 minutes a pass against
gpt-oss-120b's 3.5 for the same 68/68.

**The Q4 and Q8 quants of gpt-oss-20b are 40 points apart — on generation, not
ability.** Q4 truncated and returned *empty* content 6 times across its three
passes against Q8's 1, and burned 10.4 min/pass to Q8's 6.1. On the reasoning
track, where answers are short, the same two quants land 95 and 98 out of 102.
The quantisation did not make it worse at the problems; it made it verbose
enough to run out of tokens before finishing them.

**Llama-3-14B-Instruct-v1 scores a true 0/68** in all three passes: repetition
loops on 7 of 15 problem-passes, and deliverables that never appear in the
transcript at all. It is also the slowest of the small models at 15 min/pass.

## Agent track

Same prompts and same graders, but the model must call `write_file` to produce
the deliverables. One pass, 12-turn limit. Run 2026-07-31 and 2026-08-04;
the second sweep used `max_tokens 8192`.

| model | score | turns/problem | tool calls | malformed | notes |
|---|---|---|---|---|---|
| gpt-oss-120b-MXFP4 | **68/68** | **2.8** | 1.8 | 0 | cleanest agent |
| gemma-4-26B-A4B | **68/68** | 8.6 | 8.2 | 2 | hit turn limit 3/5, stray files |
| gpt-oss-20b-Q8_0 | **68/68** | 3.0 | 2.0 | 0 | no missing files, no strays |
| Qwen3.6-27B | 67/68 | 7.2 | 7.0 | 0 | hit turn limit |
| gemma-4-31B-it-qat | 65/68 | **2.4** | 2.0 | 0 | clean on all five |
| Qwen3.6-35B-A3B | 65/68 | 8.4 | 8.6 | 0 | hit turn limit 3/5 |
| Qwen3-Coder-30B | 57/68 | 5.4 | 4.4 | 0 | native tool format, see below |
| Qwen3VL-8B-Uncensored | 41/68 | 2.0 | 1.6 | 1 | 1 deliverable never written |
| Muse-Glimmer-30B-Q8 | 28/68 | 2.4 | 2.6 | 0 | 3 of 5 out of tokens before calling |
| gpt-oss-20b-Q4_K_M | 37/68 | 2.4 | 1.4 | 0 | 2 missing, stops after 1 turn |
| Hermes-4-14B | 8/68 | 1.2 | 0.8 | 0 | 4 of 5 deliverables missing |
| Meta-Llama-3.1-8B | 0/68 | 1.8 | 0.8 | 0 | 5 missing, calls tools uselessly |
| Llama-3-14B-Instruct-v1 | 0/68 | 1.0 | **0.0** | 0 | prose only on all five |

**Llama-3-14B never called a tool once.** Five problems, five prose answers,
zero `write_file` calls, one turn each — the failure mode the track was built to
detect. Meta-Llama-3.1-8B does call tools and still scores 0: it writes
something for 4 of 5 problems but never the file the grader asks for.

**gpt-oss-20b-Q8 is the second cleanest agent measured** — 3.0 turns, 2.0 calls,
nothing missing, nothing stray, 68/68. Its Q4 sibling stops after a single turn
on two problems and loses 31 points to files that were never written.

**Muse-Glimmer drops 40 points between the one-shot and agent tracks — every one
of them to its own reasoning, not to tool use.** It scores 68/68 one-shot and
28/68 here on the same five problems. Problems 2, 4 and 5 each record exactly
`tokens: 8192` — the per-turn cap, to the token — with **zero tool calls** and
`prose_only: false`. It did not answer in prose instead of calling a tool, and
it did not call one badly: it never finished thinking. Its reasoning consumed
the entire turn budget and the turn ended mid-thought, so no file was ever
written. The two problems it completed it completed perfectly (20/20 and 8/8),
with **0 malformed calls** across 13 calls — when it does emit a call, the call
is well-formed. This is the gpt-oss-20b-Q4 failure again and more extreme: the
score measures verbosity against a token ceiling, not agent ability. A larger
`--max-tokens` would very likely move this number a long way, which is exactly
why it should not be read as a capability ranking.

Its one clean multi-call problem also shows the milder version: 12 tool calls
for 4 files on problem 3, rewriting `q4.sql` three times. Redundant, not wrong.

**Tools raised scores rather than lowering them.** Qwen3.6-27B gained 10 points
over its one-shot median, Qwen3.6-35B gained 8. Likely because writing into a
file sidesteps the repetition loop that ate their prose answers. This column is
a single pass, so treat ±3 as noise.

**Turn efficiency does not track score.** gpt-oss and gemma-4-31B finish in
2–3 turns; gemma-4-26B needs 8.6 and hits the 12-turn limit on three of five
problems — same 68/68, four times the tool calls and cost.

**Several models wrote test files nobody asked for** (`test_parse_duration.py`,
`run_tests.py`). They are reaching for self-verification and finding no
execution tool, so this track measures them below their ceiling.


## Reasoning track

Six categories, 102 items, all graded mechanically. Five categories are
generated from a seed and solved in Python, so nothing here can have been
memorised from training data. `temperature 0`, thinking off, **3 passes**,
seed 1. Run 2026-08-01 and 2026-08-05, identical settings. Category columns are
from the median pass.

| model | median | passes | state | constraint | compliance | abstention | trap | retrieval |
|---|---|---|---|---|---|---|---|---|
| **gpt-oss-120b-MXFP4** | **102/102** | 101·102·102 | **20/20** | **20/20** | 20/20 | 20/20 | 14/14 | 8/8 |
| gpt-oss-20b-Q8_0 | 98/102 | 98·99·98 | **20/20** | **20/20** | 20/20 | 20/20 | 13/14 | 5/8 |
| gpt-oss-20b-Q4_K_M | 95/102 | 95·96·91 | **20/20** | **20/20** | 18/20 | 20/20 | 13/14 | 4/8 |
| Qwen3VL-8B-Uncensored | 84/102 | 84·84·84 | 18/20 | 12/20 | 12/20 | 20/20 | 14/14 | 8/8 |
| gemma-4-31B-it-qat | 84/102 | 84·84·84 | 10/20 | 12/20 | 20/20 | 20/20 | 14/14 | 8/8 |
| gemma-4-26B-A4B | 81/102 | 82·81·81 | 7/20 | 13/20 | 20/20 | 20/20 | 13/14 | 8/8 |
| Qwen3.6-27B | 77/102 | 76·77·78 | 6/20 | 11/20 | 19/20 | 20/20 | 13/14 | 8/8 |
| Qwen3.6-35B-A3B | 74/102 | 74·73·75 | **2/20** | 13/20 | 19/20 | 20/20 | 13/14 | 7/8 |
| Hermes-4-14B | 63/102 | 63·63·63 | 4/20 | 6/20 | 12/20 | 20/20 | 13/14 | 8/8 |
| Qwen3-Coder-30B-A3B | 61/102 | 61·61·60 | 8/20 | **5/20** | **9/20** | 20/20 | 12/14 | 6/8 |
| Llama-3-14B-Instruct-v1 | 59/102 | 59·57·61 | 10/20 | **5/20** | 14/20 | 20/20 | 10/14 | **0/8** |
| Meta-Llama-3.1-8B | 52/102 | 52·50·52 | **2/20** | 9/20 | 7/20 | 20/20 | 11/14 | 3/8 |
| Muse-Glimmer-30B-Q8 | not run | — | — | — | — | — | — | — |

**Muse-Glimmer was not run on this track, deliberately.** At 7.3 tok/s a single
pass of 102 items is a 4–8 hour measurement, and the track's default
`max_tokens` is **2048** — a quarter of the 8192 budget the model had already
been observed to exhaust on 3 of 5 agent problems without producing an answer.
The expected result was a near-zero recording how long it thinks rather than how
well, at a cost of most of a day. Raising the cap would measure the model but
would not be comparable with the twelve rows above, which were all run at 2048.
Either way the number would not have meant what the column header says, so the
run was cancelled rather than published with a caveat longer than the result.

**A 20B model reaches 98/102.** gpt-oss-20b-Q8 is perfect on state, constraint,
compliance and abstention, and loses its four points almost entirely to
retrieval. It is 4 points off the 120B at a fifth of the memory, and 14 points
clear of every non-gpt-oss model tested.

**Quantisation costs 3 points here and 40 on the coding track.** Q4 matches Q8
exactly on the two discriminating categories (20/20 state, 20/20 constraint) —
further evidence that its coding collapse is an output-length failure rather
than a reasoning one.

**This track is far more stable than the coding benchmark** — spreads of 0–2
points across three passes, against ±11 on the 68 checks. More items beat
cleverer items; 102 binary questions simply average out the sampling noise that
dominates a 68-check run.

**gpt-oss-120b has saturated it.** 102/102 and 101/102. The track can no longer
measure this model, only rank everything beneath it.

**Parameter count does not predict state tracking.** Qwen3VL-8B-Uncensored ties
gemma-4-31B on the total while being roughly a quarter of the parameters, and beats
every model except gpt-oss at tracking sequential state — 18/20 against 10, 7, 6
and 2 for models three to fifteen times larger. Its weakness is the opposite of
the gemmas': it reasons well and follows formatting instructions badly.

**Qwen3.6-35B scores 2/20 on state tracking**, in all three passes. Six
operations on three bins and it is essentially never right. The same model
produced the repetition loops and the 49/68 coding outlier.

**Qwen3-Coder-30B is the only model the hardened compliance items caught** —
9/20 where everyone else scores 19–20, specifically on bare-JSON-without-a-code
-fence and forbidden-letter constraints. Consistent with it emitting tool calls
in a format llama.cpp cannot parse: a pattern of not doing what the protocol
asks, which matters more for an agent than raw ability.

### Categories that no longer earn their place

**Abstention is dead** — 20/20 for all twelve models even after a near-miss
distractor was added (staff numbers present in the report, but for a different
depot). These models reliably decline to answer about the depot that was not
asked about. It contributes 20 free points and compresses the visible spread.

**Retrieval is not dead — that was a ceiling effect of the first seven models.**
It read as free points at 8/8 for five of seven, but the second sweep scores
0/8, 3/8, 4/8 and 5/8 on it. Llama-3-14B gets *none* of the eight right at 43k
characters with decoy hosts and a planned-versus-recorded uptime trap, and it is
the only category separating the two gpt-oss-20b quants from the 120B. Long-
context retrieval is the one place where model size still clearly shows.

**Compliance is saturated except for two models.** Worth keeping only because it
caught Qwen3-Coder.

Real discrimination lives in **state tracking** and **constraint satisfaction**,
which is 40 of the 102 points. Read the totals with that in mind.

## Cross-track summary

| model | coding | agent | reasoning | tok/s | size |
|---|---|---|---|---|---|
| gpt-oss-120b-MXFP4 | 68/68 | 68/68 | **102/102** | 54 | 63 GB |
| gemma-4-31B-it-qat | 68/68 | 65/68 | 84/102 | 12 | 17 GB |
| Muse-Glimmer-30B-Q8 † | 68/68 | 28/68 | not run | **7.4** | 32 GB |
| **gpt-oss-20b-Q8_0** | 65/68 | 68/68 | 98/102 | 75 | **12 GB** |
| gemma-4-26B-A4B | 65/68 | 68/68 | 81/102 | 74 | 14 GB |
| Qwen3.6-27B | 57/68 | 67/68 | 77/102 | 13 | 17 GB |
| Qwen3.6-35B-A3B | 57/68 | 65/68 | 74/102 | 62 | 23 GB |
| Qwen3-Coder-30B-A3B | 57/68 | 57/68 | 61/102 | 92 | 18 GB |
| Qwen3VL-8B-Uncensored | 31/68 | 41/68 | 84/102 | 44 | 5 GB |
| gpt-oss-20b-Q4_K_M | 25/68 | 37/68 | 95/102 | 81 | 12 GB |
| Hermes-4-14B | 23/68 | 8/68 | 63/102 | 25 | 9 GB |
| Meta-Llama-3.1-8B | 19/68 | 0/68 | 52/102 | 44 | 5 GB |
| Llama-3-14B-Instruct-v1 | 0/68 | 0/68 | 59/102 | 25 | 9 GB |

**gpt-oss-120b still wins every track outright.** If 54 tok/s and 63 GB resident
are acceptable, nothing else on this machine has an argument.

† **Muse-Glimmer-30B is a single run on every track, and its testing was stopped
early.** It ties the top of the coding table at 68/68 and is the slowest model
ever measured here at 7.4 tok/s — a combination that makes the remaining
measurements expensive and, as the agent track showed, mostly a record of how
many tokens it spends thinking. One pass of the reasoning track would have cost
most of a day to produce a number about its verbosity, so it was cancelled. Read
the row as two solid results and two deliberate gaps, not as a model that failed
three tracks.

**Muse-Glimmer is the sharpest example yet of the gap this benchmark keeps
finding.** 68/68 given one shot and a large budget; 28/68 when the same five
problems require it to finish thinking and then act inside 8192 tokens a turn.
Nothing about its coding ability changed between those two runs — only whether
it was allowed to ramble first. gpt-oss-120b scores 68/68 on both.

**gpt-oss-20b-Q8 replaces gemma-4-26B as the value pick.** It matches it on both
coding tracks (65/68 and 68/68), beats it by 17 points on reasoning, and does so
in 2 GB less memory at the same speed. There is no track on which gemma-4-26B is
now the better choice.

**Reasoning ability does not imply usable output.** Three models make the point
in opposite directions: Qwen3VL-8B reasons at gemma-4-31B's level (84/102) and
writes code at half its score; Llama-3-14B answers 59/102 reasoning items while
scoring 0/68 on *both* coding tracks; gpt-oss-20b-Q4 is 3 reasoning points off
its Q8 twin and 40 coding points behind it. Whatever these tracks measure, a
model can hold one and not the other — so a reasoning benchmark is not a proxy
for whether a model can do the work.

## Speed

All 12 models, `llama-bench` build 9892 (`ee445f93d`), Vulkan on Strix Halo,
`-fa on -ctk/-ctv q8_0 -ngl 999`, 3 reps, 2026-08-05. The short version:
**dense models run 5–7× slower than MoE models of similar size on this
hardware**, which reverses the apparent ranking.

| model | size | pp512 | tg@0 | tg@16k | retained | one-shot | agent |
|---|---|---|---|---|---|---|---|
| Qwen3-Coder-30B-A3B | 18 GB | 1303 | **92** | 64 | 69% | 57/68 | 57/68 |
| gpt-oss-20b-Q4_K_M | 12 GB | **1658** | 81 | 70 | 87% | 25/68 | 37/68 |
| gpt-oss-20b-Q8_0 | 12 GB | 1641 | 75 | **70** | **89%** | 65/68 | 68/68 |
| gemma-4-26B-A4B | 14 GB | 1388 | 74 | 62 | 84% | 65/68 | 68/68 |
| Qwen3.6-35B-A3B | 23 GB | 1115 | 63 | 58 | 93% | 57/68 | 65/68 |
| gpt-oss-120b-MXFP4 | 63 GB | 630 | 54 | 49 | 91% | 68/68 | 68/68 |
| Meta-Llama-3.1-8B | 5 GB | 1281 | 44 | 35 | 78% | 19/68 | 0/68 |
| Qwen3VL-8B-Uncensored | 5 GB | 1261 | 44 | 33 | 77% | 31/68 | 41/68 |
| Hermes-4-14B | 9 GB | 750 | 25 | 21 | 84% | 23/68 | 8/68 |
| Llama-3-14B-Instruct-v1 | 9 GB | 679 | 25 | 20 | 78% | 0/68 | 0/68 |
| Qwen3.6-27B | 17 GB | 360 | 13 | 12 | 96% | 57/68 | 67/68 |
| gemma-4-31B-it-qat | 17 GB | 288 | 12 | 11 | 89% | 68/68 | 65/68 |
| Muse-Glimmer-30B-Q8 ‡ | 32 GB | 348 | 7.4 | 7.3 | **99%** | 68/68 | — |

- **gpt-oss-20b-Q8 is the value pick** — 68/68 agent, 98/102 reasoning, 75 tok/s,
  12 GB, and it holds 89% of its throughput out to 16k context.
- **gpt-oss-120b is the quality pick** — 68/68 on both tracks with zero variance
  and the most disciplined tool use, at 54 tok/s and 63 GB resident.
- **gemma-4-31B is not the sweet spot it first appeared to be.** Same accuracy
  as gpt-oss on one track, but 12 tok/s — 6× slower than gemma-4-26B for
  3 points.
- **The 14B dense models are dominated outright** — 25 tok/s *and* bottom-table
  scores. There is no budget at which they are the right answer.

**Throughput at depth is not proportional across models, and agent work lives at
depth.** Qwen3-Coder leads at empty context by 22% over gpt-oss-20b-Q8 and
*trails* it at 16k. A ranking taken at `tg@0` — which is what a headline tok/s
number is — mis-sorts the models you would actually run a multi-turn agent on.

‡ **Muse-Glimmer's row is 2026-08-12 on build `b10380`**, the rest are `b9892`.
The builds are interchangeable for speed: the same control model on the new
build read 74.29 / 74.34 / 74.31 tok/s against 74.04 / 73.82 / 74.05 on the old,
a 0.3% difference against a control whose whole job is to detect drift smaller
than that.

**Muse-Glimmer is the slowest model measured and the least damaged by depth.**
It retains **99%** of its throughput out to 16k, where the fastest model in the
table keeps 69%. Its architecture alternates three 2048-token sliding-window
layers with a fourth full-attention NoPE layer, so most of its layers never read
the whole context. That is the opposite trade from Qwen3-Coder: Muse-Glimmer
starts slow and stays there, which for long multi-turn agent work is the more
predictable failure mode — but it starts so slow (7.4 tok/s, 32 GB read per
token, dense) that 99% retention never overtakes anything. It closes the gap to
gemma-4-31B from 62% to 33% across the depth sweep and still loses.

Measurement conditions: drift controls at the start, middle and end of the run
came in at 74.04, 73.82 and 74.05 tok/s (0.2% spread), and the five models
carried over from the 2026-08-04 run reproduced within 1%, so the table needs no
thermal caveat. **gemma-4-31B's row is the 2026-08-04 measurement** — its model
file had been deleted from the box, and the re-run is pending.

## Caveats that change the conclusions

**Temperature 0 is not reproducible on llama.cpp.** Continuous batching, MoE
routing and a quantised KV cache make numerics depend on batch and slot state.
Five identical requests for one problem produced answer lengths of 1193, 290,
124, 203 and 100 lines and scores of 0, 0, 11, 0, 11 out of 11.

**A single pass is one draw from a distribution.** The first single-pass sweep
ranked the Qwen models 63 / 53 / 49; three passes put all three at a median of
**57**. The second sweep widened the worst case: gpt-oss-20b-Q8 scored 51, 65
and 68 on identical settings — a **17-point spread**, a quarter of the whole
scale, on the model that otherwise looks like the value pick. Qwen3VL-8B spread
14 and gpt-oss-20b-Q4 spread 13. Single-run error is well past the "5–10 points
is noise" band in the README. Publish medians of ≥3 with the spread visible, or
the ranking is fiction.

**Item count fixes this, cleverness does not.** The reasoning track's 102
generated items produced pass-to-pass spreads of 0–2 points on the same
hardware and the same decode settings. If you want a stable measurement, add
items rather than passes.

**Only three of twelve models have a stable non-zero score.** gpt-oss-120b,
gemma-4-31B and Qwen3-Coder-30B varied by ≤2 points across passes. Everything
else swings by 9 to 17. (Llama-3-14B and Meta-Llama-3.1-8B are also perfectly
consistent, at 0/68 and 19/68 — consistency is not the same as competence.)

**Extended thinking had to be disabled to measure anything.** Under greedy
decoding these models fall into repetition loops: gemma-4-26B spent all 16,384
tokens repeating one verification line and returned *empty* content, scoring
0/20 on a problem it otherwise gets 17/20 on. `enable_thinking: false` fixed it
and was 18× faster. A repeat penalty at temperature 0 did **not** help. So this
table measures these models *without* extended thinking. Whether thinking
changes the ranking is untested.

**gpt-oss ignores the thinking switch** — it uses `reasoning_effort` instead and
kept producing 2–6k characters of reasoning. Its scores are *with* thinking,
unlike everyone else's.

**Qwen3-Coder's tool calls are invisible to a standard client.** It emits
`<function=write_file><parameter=path>…` as plain text and llama.cpp does not
parse it into `tool_calls`. The harness has a fallback parser, which took it
from 0/68 to 57/68 — but an off-the-shelf coding agent would see the 0. That is
a server/build integration gap, not a model limitation.

**Load failures are common and intermittent.** Three of six models failed their
first load in one sweep and succeeded on retry. A model reporting `failed to
load` once is not evidence it is broken.
