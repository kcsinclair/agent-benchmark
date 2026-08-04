# Results

Every score here comes from [leia](servers/leia.md) unless stated otherwise.
Scores are not portable between machines *as speed*, and are only portable *as
accuracy* if the decode settings match — so both are recorded.

**Read the caveats before quoting any of this.** The headline finding of the
first sweep was not which model wins; it was that a single run of this benchmark
is not a measurement.

## One-shot track

Model gets the prompt, answers once, code blocks are extracted from the reply.
`temperature 0`, thinking disabled, `max_tokens 16384`, 3 passes, 2026-07-31.

| model | median | passes | pass time |
|---|---|---|---|
| gpt-oss-120b-MXFP4 | **68/68** | 68 · 68 · 68 | 3.5 min |
| gemma-4-31B-it-qat | **68/68** | 68 · 68 · 68 | 5.3 min |
| gemma-4-26B-A4B-it-qat | 65/68 | 54 · 65 · 65 | 1.3 min |
| Qwen3-Coder-30B-A3B | 57/68 | 56 · 57 · 58 | 0.7 min |
| Qwen3.6-27B | 57/68 | 57 · 57 · 66 | 7 min |
| Qwen3.6-35B-A3B | 57/68 | 53 · 57 · 57 | 4.3 min |
| Kimi-Linear-48B-A3B | — | fails to load | — |

## Agent track

Same prompts and same graders, but the model must call `write_file` to produce
the deliverables. One pass, 12-turn limit, 2026-07-31.

| model | score | turns/problem | tool calls | malformed | notes |
|---|---|---|---|---|---|
| gpt-oss-120b-MXFP4 | **68/68** | **2.8** | 1.8 | 0 | cleanest agent |
| gemma-4-26B-A4B | **68/68** | 8.6 | 8.2 | 2 | hit turn limit 3/5, stray files |
| Qwen3.6-27B | 67/68 | 7.2 | 7.0 | 0 | hit turn limit |
| gemma-4-31B-it-qat | 65/68 | **2.4** | 2.0 | 0 | clean on all five |
| Qwen3.6-35B-A3B | 65/68 | 8.4 | 8.6 | 0 | hit turn limit 3/5 |
| Qwen3-Coder-30B | 57/68 | 5.4 | 4.4 | 0 | native tool format, see below |

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
seed 1, 2026-08-01.

| model | median | passes | state | constraint | compliance | abstention | trap | retrieval |
|---|---|---|---|---|---|---|---|---|
| **gpt-oss-120b-MXFP4** | **102/102** | 101·102·102 | **20/20** | **20/20** | 20/20 | 20/20 | 14/14 | 8/8 |
| Qwen3VL-8B-Uncensored | 84/102 | 84·84·84 | **18/20** | 12/20 | 12/20 | 20/20 | 14/14 | 8/8 |
| gemma-4-31B-it-qat | 84/102 | 84·84·84 | 10/20 | 12/20 | 20/20 | 20/20 | 14/14 | 8/8 |
| gemma-4-26B-A4B | 81/102 | 82·81·81 | 7/20 | 13/20 | 20/20 | 20/20 | 13/14 | 8/8 |
| Qwen3.6-27B | 77/102 | 76·77·78 | 6/20 | 11/20 | 19/20 | 20/20 | 13/14 | 8/8 |
| Qwen3.6-35B-A3B | 74/102 | 74·73·75 | **2/20** | 13/20 | 19/20 | 20/20 | 13/14 | 7/8 |
| Qwen3-Coder-30B-A3B | 61/102 | 61·61·60 | 8/20 | **5/20** | **9/20** | 20/20 | 12/14 | 6/8 |

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

**Abstention is dead** — 20/20 for all seven models even after a near-miss
distractor was added (staff numbers present in the report, but for a different
depot). These models reliably decline to answer about the depot that was not
asked about. It contributes 20 free points and compresses the visible spread.

**Retrieval is nearly dead** — 8/8 for five of seven at 43k characters with
decoy hosts and a planned-versus-recorded uptime trap.

**Compliance is saturated except for one model.** Worth keeping only because it
caught Qwen3-Coder.

Real discrimination lives in **state tracking** and **constraint satisfaction**,
which is 40 of the 102 points. Read the totals with that in mind.

## Cross-track summary

| model | coding | agent | reasoning | tok/s | size |
|---|---|---|---|---|---|
| gpt-oss-120b-MXFP4 | 68/68 | 68/68 | **102/102** | 54 | 63 GB |
| gemma-4-31B-it-qat | 68/68 | 65/68 | 84/102 | 12 | 17 GB |
| gemma-4-26B-A4B | 65/68 | 68/68 | 81/102 | 74 | 14 GB |
| Qwen3.6-27B | 57/68 | 67/68 | 77/102 | 13 | 17 GB |
| Qwen3.6-35B-A3B | 57/68 | 65/68 | 74/102 | 62 | 23 GB |
| Qwen3-Coder-30B-A3B | 57/68 | 57/68 | 61/102 | 92 | 18 GB |
| Qwen3VL-8B-Uncensored | not run | not run | 84/102 | not run | ~5 GB |

**gpt-oss-120b wins every track outright.** If 54 tok/s and 63 GB resident are
acceptable, nothing else on this machine has an argument. **gemma-4-26B is the
value pick** — second-best agent score at 74 tok/s in 14 GB.

Open gap: Qwen3VL-8B has only been through the reasoning track. If an 8B holds
up on coding and agent work it changes the value calculation completely, and it
is cheap to find out.

## Speed

See [servers/leia.md](servers/leia.md) for the full table. The short version:
**dense models run 5–7× slower than MoE models of similar size on this
hardware**, which reverses the apparent ranking.

| model | tg@0 | one-shot | agent |
|---|---|---|---|
| Qwen3-Coder-30B-A3B | 92 tok/s | 57/68 | 57/68 |
| gemma-4-26B-A4B | 74 tok/s | 65/68 | 68/68 |
| gpt-oss-120b-MXFP4 | 54 tok/s | 68/68 | 68/68 |
| gemma-4-31B | 12 tok/s | 68/68 | 65/68 |

- **gemma-4-26B-A4B is the value pick** — 68/68 agent, 74 tok/s, 14 GB.
- **gpt-oss-120b is the quality pick** — 68/68 on both tracks with zero variance
  and the most disciplined tool use, at 54 tok/s and 63 GB resident.
- **gemma-4-31B is not the sweet spot it first appeared to be.** Same accuracy
  as gpt-oss on one track, but 12 tok/s — 6× slower than gemma-4-26B for
  3 points.

## Caveats that change the conclusions

**Temperature 0 is not reproducible on llama.cpp.** Continuous batching, MoE
routing and a quantised KV cache make numerics depend on batch and slot state.
Five identical requests for one problem produced answer lengths of 1193, 290,
124, 203 and 100 lines and scores of 0, 0, 11, 0, 11 out of 11.

**A single pass is one draw from a distribution.** The first single-pass sweep
ranked the Qwen models 63 / 53 / 49; three passes put all three at a median of
**57**. Single-run error reaches ±11 points — the top of the "5–10 points is
noise" band in the README, arguably past it. Publish medians of ≥3 with the
spread visible, or the ranking is fiction.

**Item count fixes this, cleverness does not.** The reasoning track's 102
generated items produced pass-to-pass spreads of 0–2 points on the same
hardware and the same decode settings. If you want a stable measurement, add
items rather than passes.

**Only three of six models have a stable score.** gpt-oss-120b, gemma-4-31B and
Qwen3-Coder-30B varied by ≤2 points across passes. The rest swing by up to 11.

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
