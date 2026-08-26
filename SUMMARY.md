# Summary

Seventeen local models, four tracks, one machine. Everything below was measured
on [leia](servers/leia.md) — AMD Ryzen AI MAX+ 395, unified memory, llama.cpp on
Vulkan — at `temperature 0` with thinking disabled. Full numbers and methodology
in [RESULTS.md](RESULTS.md).

Not every model has been through every track. Twelve have all four; the rest are
marked ‡ and were run on the one-shot and speed tracks only, as single passes.
**The gemma-4 suite added on 2026-08-13 is a first look, not a verdict** — full
testing to follow.

**The bottom line: a 20 GB-class model now does what took 63 GB.**
gpt-oss-20b-Q8 lands within 4 points of gpt-oss-120b on every track, at a fifth
of the memory and 1.4× the speed. Below that, the ranking depends entirely on
which track you weight — and three models score well on reasoning while being
unable to deliver working code at all.

| pick | model | why |
|---|---|---|
| **Quality** | gpt-oss-120b | 68/68 coding, 68/68 agent, 102/102 reasoning, zero variance across passes |
| **Value** | gpt-oss-20b-Q8 | matches it within 4 points everywhere, 12 GB, 75 tok/s |
| **Throughput** | Qwen3-Coder-30B | 92 tok/s, 57/68 — but see the retention chart before believing that number |
| **Smallest useful** | gemma-4-E2B ‡ | 103 tok/s in **3 GB** — fastest here by a distance, but 34/68 |
| **Avoid** | Llama-3-14B-Instruct-v1 | 0/68 on both coding tracks, 25 tok/s, never calls a tool |

## Quality across the three scored tracks

### One-shot coding, median of 3 passes (68 checks)

```
gemma-4-31B         ██████████████████████████████████  68/68
gpt-oss-120b        ██████████████████████████████████  68/68
Muse-Glimmer-30B ‡  ██████████████████████████████████  68/68
gemma-4-26B         ████████████████████████████████▌   65/68
gpt-oss-20b Q8      ████████████████████████████████▌   65/68
gemma-4-26B heretic ██████████████████████████████▌     61/68 ‡
gemma-4-26B Q8      ██████████████████████████████      60/68 ‡
Qwen3-Coder-30B     ████████████████████████████▌       57/68
Qwen3.6-27B         ████████████████████████████▌       57/68
Qwen3.6-35B         ████████████████████████████▌       57/68
gemma-4-E4B         ██████████████████▌                 37/68 ‡
gemma-4-E2B         █████████████████                   34/68 ‡
Qwen3VL-8B          ███████████████▌                    31/68
gpt-oss-20b Q4      ████████████▌                       25/68
Hermes-4-14B        ███████████▌                        23/68
Llama-3.1-8B        █████████▌                          19/68
Llama-3-14B                                             0/68
```

‡ rows are a single pass. Given that the models with three passes swing by up to
17 points between identical runs, a single result places a model in a band, not
at a rank.

### Agent track — same problems, but the model must call `write_file`

```
gemma-4-26B         ██████████████████████████████████  68/68
gpt-oss-120b        ██████████████████████████████████  68/68
gpt-oss-20b Q8      ██████████████████████████████████  68/68
Qwen3.6-27B         █████████████████████████████████▌  67/68
Qwen3.6-35B         ████████████████████████████████▌   65/68
gemma-4-31B         ████████████████████████████████▌   65/68
Qwen3-Coder-30B     ████████████████████████████▌       57/68
Qwen3VL-8B          ████████████████████▌               41/68
gpt-oss-20b Q4      ██████████████████▌                 37/68
Muse-Glimmer-30B    ██████████████                      28/68
Hermes-4-14B        ████                                8/68
Llama-3-14B                                             0/68
Llama-3.1-8B                                            0/68
```

Tool use *raises* scores for the mid-table models and annihilates the bottom
two. Llama-3-14B answered all five problems in prose and called a tool exactly
zero times. Meta-Llama-3.1-8B does call tools, and still scores 0 — it writes
files, just never the ones the grader asks for.

**Muse-Glimmer is the exception that isn't about tool use at all.** It scores
68/68 one-shot and 28/68 here, on the same five problems. Three of the five
recorded exactly 8192 completion tokens — the per-turn cap, to the token — with
zero tool calls: it never finished reasoning, so it never got as far as writing
a file. Where it did call, 13 calls came back with zero malformed. The 40-point
drop measures a token ceiling, not an inability to drive an agent.

### Reasoning, median of 3 passes (102 generated items)

```
gpt-oss-120b     ██████████████████████████████████ 102/102
gpt-oss-20b Q8   ████████████████████████████████▊  98/102
gpt-oss-20b Q4   ███████████████████████████████▊   95/102
Qwen3VL-8B       ████████████████████████████       84/102
gemma-4-31B      ████████████████████████████       84/102
gemma-4-26B      ███████████████████████████        81/102
Qwen3.6-27B      █████████████████████████▊         77/102
Qwen3.6-35B      ████████████████████████▊          74/102
Hermes-4-14B     █████████████████████              63/102
Qwen3-Coder-30B  ████████████████████▍              61/102
Llama-3-14B      ███████████████████▊               59/102
Llama-3.1-8B     █████████████████▍                 52/102
```

The five newest models are absent by choice. For Muse-Glimmer the track's
2048-token answer limit is a quarter of the budget it had already been seen to
exhaust without answering, so a pass would have recorded its verbosity at a cost
of most of a day. The gemma-4 variants are simply not done yet.

## Reasoning ability does not predict useful output

Compare the three charts and the orderings barely agree. Three independent cases
make the same point:

| model | reasoning | coding | the gap |
|---|---|---|---|
| Qwen3VL-8B | 84/102 | 31/68 | reasons at gemma-4-31B's level, writes code at half its score |
| Llama-3-14B | 59/102 | 0/68 | answers 58% of reasoning items, delivers nothing runnable |
| gpt-oss-20b-Q4 | 95/102 | 25/68 | 3 points off its Q8 twin, then 40 points behind it on code |

A reasoning benchmark tells you whether a model can follow a chain of state. It
does not tell you whether it will emit a complete, parseable, correctly-named
file — which is the thing you actually need.

## Quantisation is a speed dial, not a quality dial

Two experiments on the same question, pointing the same way.

**gpt-oss-20b, Q4 against Q8 — 40 points apart on code, 3 on reasoning:**

```
                 reasoning /102   coding /68   agent /68   empty answers
gpt-oss-20b Q8        98              65          68            1
gpt-oss-20b Q4        95              25          37            6
```

The cause is not lost ability — Q4 matches Q8 exactly on both *discriminating*
reasoning categories (20/20 state, 20/20 constraint). It became verbose. It runs
past `max_tokens` mid-answer and returns empty content, six times across three
passes, at 10.4 min/pass against Q8's 6.1.

**gemma-4-26B, the same model at three quants — nothing separates them on
score:**

```
                        coding /68     tok/s     resident
gemma-4-26B qat-Q4       65 (54-65-65)    74       14 GB
gemma-4-26B heretic Q4   61 (one pass)    66       17 GB
gemma-4-26B Q8_K_XL      60 (one pass)    45       28 GB
```

A 5-point range, against a model whose own three passes spanned 11. Doubling the
quantisation bought nothing measurable and cost 14 GB and 39% of throughput.
(The `heretic` row is an uncensored abliterated finetune — whatever it removed,
it was not the ability to write a parser.)

**Together: quantisation damage shows up as generation length and throughput,
not as reasoning.** A benchmark that only asked short questions would have
scored every one of these pairs as equivalent.

## Speed

### Generation at empty context (tok/s)

```
gemma-4-E2B ‡       ██████████████████████████████████  103
Qwen3-Coder-30B     ██████████████████████████████▍     92
gpt-oss-20b Q4      ██████████████████████████▊         81
gpt-oss-20b Q8      ████████████████████████▊           75
gemma-4-26B         ████████████████████████▍           74
gemma-4-E4B ‡       █████████████████████▊              66
gemma-4-26B heretic █████████████████████▊              66 ‡
Qwen3.6-35B         ████████████████████▊               63
gpt-oss-120b        █████████████████▉                  54
gemma-4-26B Q8 ‡    ██████████████▉                     45
Llama-3.1-8B        ██████████████▌                     44
Qwen3VL-8B          ██████████████▌                     44
Llama-3-14B         ████████▎                           25
Hermes-4-14B        ████████▎                           25
Qwen3.6-27B         ████▎                               13
gemma-4-31B         ████                                12
Muse-Glimmer-30B    ██▌                                 7.4
```

Dense models run 5–7× slower than MoE models of comparable size on this
hardware, which reverses the apparent ranking: gemma-4-31B and Qwen3.6-27B score
at the top and generate at 12–13 tok/s. Muse-Glimmer is the extreme case — a
dense 30B at Q8, 32 GB read per token, 68/68 at 7.4 tok/s.

### Throughput retained at 16k context

```
Muse-Glimmer-30B    ███████████████████████   99%   7.4 -> 7.3
Qwen3.6-27B         ██████████████████████▎   96%   12.7 -> 12.2
Qwen3.6-35B         █████████████████████▋    93%   62.7 -> 58.2
gpt-oss-120b        █████████████████████▏    91%   53.7 -> 48.7
gemma-4-26B Q8      ████████████████████▋     89%   44.6 -> 39.7
gemma-4-31B         ████████████████████▋     89%   12.2 -> 10.9
gpt-oss-20b Q8      ████████████████████▋     89%   74.9 -> 66.6
gpt-oss-20b Q4      ████████████████████▎     87%   80.9 -> 70.3
gemma-4-E2B         ███████████████████▊      85%   103.4 -> 87.9
Hermes-4-14B        ███████████████████▌      84%   24.8 -> 20.9
gemma-4-26B         ███████████████████▌      84%   74.0 -> 61.8
gemma-4-26B heretic ███████████████████▌      84%   65.8 -> 55.2
gemma-4-E4B         ███████████████████▎      83%   65.9 -> 54.7
Llama-3-14B         ██████████████████▏       78%   24.9 -> 19.5
Llama-3.1-8B        ██████████████████▏       78%   44.3 -> 34.6
Qwen3VL-8B          █████████████████▉        77%   43.6 -> 33.4
Qwen3-Coder-30B     ████████████████          69%   91.7 -> 63.5
```

**This is the chart that changes a decision.** Qwen3-Coder leads at empty
context by 22% over gpt-oss-20b-Q8 and *trails* it at 16k — 63.5 against 66.6
tok/s. Agent work lives at depth, so ranking models by headline tok/s mis-sorts
exactly the workload you'd pick a fast model for.

Muse-Glimmer tops this chart and it changes nothing: 99% of 7.4 tok/s is still
7.3. Its architecture alternates sliding-window layers with a full-attention
one, so most layers never read the whole context — depth is nearly free for it,
and it still finishes last. Retention is a tie-breaker between models of similar
speed, not a substitute for speed.

### Speed against accuracy

```
one-shot
score
 68 │    ● Muse-Glimmer-30B      ● gpt-oss-120b
    │      ● gemma-4-31B                    ● gemma-4-26B
    │       ● Qwen3.6-27B                    ● gpt-oss-20b Q8
    │                                   ● gemma-4-26B heretic
 51 │                        ● gemma-4-26B Q8         ● Qwen3-Coder-30B
    │                                 ● Qwen3.6-35B
    │                                   ● gemma-4-E4B
 34 │                                                      ● gemma-4-E2B
    │                       ● Qwen3VL-8B
    │             ● Hermes-4-14B                ● gpt-oss-20b Q4
 17 │                       ● Llama-3.1-8B
    │
    │
    │
  0 │             ● Llama-3-14B
    └────────────────────────────────────────────────────────────
     0        25        50        75       100
     generation speed at empty context (tok/s)
```

Positions are approximate — labels are nudged to avoid overlap. The useful
corner is top-right, and it is still thinly populated. **gemma-4-26B and
gpt-oss-20b-Q8 occupy the same point** — 74 vs 75 tok/s, both 65/68 — so the
choice between them comes down to the axes this plot doesn't show: reasoning
(81 vs 98) and memory (14 GB vs 12 GB). The two extremes are instructive:
Muse-Glimmer is top-left at 68/68 and 7.4 tok/s, gemma-4-E2B is bottom-right at
103 tok/s and 34/68. Neither is a choice anyone makes on those axes alone.

### Reasoning score per GB resident

What a memory budget buys, which on a unified-memory box is the binding
constraint. Only the twelve models with a reasoning score appear:

```
Qwen3VL-8B       ████████████████████▏    16.7 pts/GB  (84/102 in 5 GB)
Llama-3.1-8B     ████████████▊            10.6 pts/GB  (52/102 in 5 GB)
gpt-oss-20b Q4   █████████▉                8.2 pts/GB  (95/102 in 12 GB)
gpt-oss-20b Q8   █████████▊                8.1 pts/GB  (98/102 in 12 GB)
Hermes-4-14B     ████████▌                 7.0 pts/GB  (63/102 in 9 GB)
Llama-3-14B      ████████▍                 6.9 pts/GB  (59/102 in 9 GB)
gemma-4-26B      ██████▉                   5.7 pts/GB  (81/102 in 14 GB)
gemma-4-31B      █████▉                    4.9 pts/GB  (84/102 in 17 GB)
Qwen3.6-27B      █████▌                    4.5 pts/GB  (77/102 in 17 GB)
Qwen3-Coder-30B  ████▎                     3.5 pts/GB  (61/102 in 18 GB)
Qwen3.6-35B      ████                      3.3 pts/GB  (74/102 in 23 GB)
gpt-oss-120b     ██                        1.6 pts/GB  (102/102 in 63 GB)
```

Read this one carefully: it rewards being small, and Qwen3VL-8B tops it while
scoring 31/68 on coding. It answers "what fits", not "what works".

## One run is not a measurement

The three-pass scores above are medians, because single passes disagree with
themselves badly. Range across three identical passes at `temperature 0`, same
prompt, same settings:

```
                 0        17        34        51       68
                 |---------|---------|---------|--------|
gpt-oss-20b Q8                                     ├───────────┤  51-68  (spread 17)
Qwen3VL-8B                           ├─────────┤                  31-45  (spread 14)
gpt-oss-20b Q4                   ├────────┤                       24-37  (spread 13)
gemma-4-26B                                          ├──────┤     54-65  (spread 11)
Hermes-4-14B                   ├─────┤                            22-31  (spread  9)
Qwen3.6-27B                                            ├─────┤    57-66  (spread  9)
Qwen3.6-35B                                         ├──┤          53-57  (spread  4)
Qwen3-Coder-30B                                       ├─┤         56-58  (spread  2)
Llama-3-14B      │                                                 0- 0  (spread  0)
Llama-3.1-8B                 │                                    19-19  (spread  0)
gemma-4-31B                                                    │  68-68  (spread  0)
gpt-oss-120b                                                   │  68-68  (spread  0)
```

The value pick swings **17 points — a quarter of the whole scale — between
identical runs.** `temperature 0` is not reproducible on llama.cpp: continuous
batching, MoE routing and a quantised KV cache make numerics depend on batch and
slot state. Only four of the twelve models run three times have a stable score,
and two of those are stable at 0/68 and 19/68.

This is the reason the ‡ rows carry a warning rather than a rank. gemma-4-26B's
own three passes covered 54 to 65; its Q8 sibling's single 60 tells you the two
are in the same band and nothing finer.

The fix is more items, not more passes: the 102-item reasoning track produces
pass-to-pass spreads of 0–2 points on the same hardware, against up to 17 on the
68-check coding benchmark.

## What to actually run

- **Have 63 GB spare and want it right:** gpt-oss-120b. Nothing else is
  perfect on every track, and its variance is zero.
- **Want one model resident all day:** gpt-oss-20b-Q8. 12 GB, 75 tok/s, 89%
  throughput retained at depth, top-3 on every track.
- **Don't use Q4 of a model you benchmarked at Q8** without re-running the
  coding tracks — and don't pay for Q8 expecting a score. Quantisation moved
  throughput by 39% and memory by 14 GB here without moving the score at all.
- **Ignore headline tok/s for agent work.** Rank by throughput at the context
  depth you actually operate at.
- **Check a model's token budget before blaming its ability.** Two of the
  largest score drops in this repo — gpt-oss-20b-Q4 and Muse-Glimmer — are
  models running out of tokens mid-answer, not models that cannot do the work.

## Provenance

Coding and agent tracks run 2026-07-31 and 2026-08-04; reasoning 2026-08-01 and
2026-08-05; speed swept 2026-08-05 in a single thermal session with drift
controls at start, middle and end agreeing within 0.2%. Models carried over
between speed sessions reproduced within 1%.

Muse-Glimmer-30B was added 2026-08-12 and the gemma-4 variants 2026-08-13, both
on llama.cpp build `b10380` after the box was upgraded from `b9892` — the older
build did not know the `muse-glimmer` architecture. The two builds are treated as
one dataset on evidence, not assumption: Qwen3-Coder-30B re-run on the new build
scored 56/68, inside its recorded 56-57-58 spread, and the speed control model
read 74.3–74.7 tok/s against 74.0 before the upgrade.

**Still outstanding.** The gemma-4 suite — `26B-A4B` at Q8_K_XL, the
`ultra-uncensored-heretic` finetune, and the `E4B`/`E2B` small models — has one
pass on the one-shot and speed tracks and nothing on agent or reasoning. **Full
testing is to follow**, at which point those rows get three passes and the ‡
comes off. Muse-Glimmer's reasoning track was cancelled deliberately rather than
deferred, for the token-budget reason given above.

One older caveat is now closed: **gemma-4-31B's speed row was re-measured on
2026-08-26** and reproduced the carried-over 2026-08-04 number within 1%.
**Kimi-Linear-48B has never been scored** — it fails to load and takes the
server down with it.

Scores are comparable only within this machine and these decode settings. The
agent track is a single pass, so treat ±3 there as noise; the ±17 above applies
to the one-shot column.
