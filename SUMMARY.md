# Summary

Twelve local models, four tracks, one machine. Everything below was measured on
[leia](servers/leia.md) — AMD Ryzen AI MAX+ 395, unified memory, llama.cpp build
9892 on Vulkan — at `temperature 0` with thinking disabled. Full numbers and
methodology in [RESULTS.md](RESULTS.md).

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
| **Avoid** | Llama-3-14B-Instruct-v1 | 0/68 on both coding tracks, 25 tok/s, never calls a tool |

## Quality across the three scored tracks

### One-shot coding, median of 3 passes (68 checks)

```
gemma-4-31B      ██████████████████████████████████ 68/68
gpt-oss-120b     ██████████████████████████████████ 68/68
gemma-4-26B      ████████████████████████████████▋  65/68
gpt-oss-20b Q8   ████████████████████████████████▋  65/68
Qwen3-Coder-30B  ████████████████████████████▋      57/68
Qwen3.6-27B      ████████████████████████████▋      57/68
Qwen3.6-35B      ████████████████████████████▋      57/68
Qwen3VL-8B       ███████████████▋                   31/68
gpt-oss-20b Q4   ████████████▋                      25/68
Hermes-4-14B     ███████████▋                       23/68
Llama-3.1-8B     █████████▋                         19/68
Llama-3-14B                                         0/68
```

### Agent track — same problems, but the model must call `write_file`

```
gemma-4-26B      ██████████████████████████████████ 68/68
gpt-oss-120b     ██████████████████████████████████ 68/68
gpt-oss-20b Q8   ██████████████████████████████████ 68/68
Qwen3.6-27B      █████████████████████████████████▋ 67/68
Qwen3.6-35B      ████████████████████████████████▋  65/68
gemma-4-31B      ████████████████████████████████▋  65/68
Qwen3-Coder-30B  ████████████████████████████▋      57/68
Qwen3VL-8B       ████████████████████▋              41/68
gpt-oss-20b Q4   ██████████████████▋                37/68
Hermes-4-14B     ████                               8/68
Llama-3-14B                                         0/68
Llama-3.1-8B                                        0/68
```

Tool use *raises* scores for the mid-table models and annihilates the bottom
two. Llama-3-14B answered all five problems in prose and called a tool exactly
zero times. Meta-Llama-3.1-8B does call tools, and still scores 0 — it writes
files, just never the ones the grader asks for.

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

## The Q4 lesson: same model, same size, 40 points

gpt-oss-20b at Q4 and Q8 are within 5% of each other on disk and 3 points apart
on reasoning. On the coding tracks they are barely the same model:

```
                 reasoning /102   coding /68   agent /68   empty answers
gpt-oss-20b Q8        98              65          68            1
gpt-oss-20b Q4        95              25          37            6
```

The cause is not lost ability — Q4 matches Q8 exactly on both *discriminating*
reasoning categories (20/20 state, 20/20 constraint). It became verbose. It runs
past `max_tokens` mid-answer and returns empty content, six times across three
passes, at 10.4 min/pass against Q8's 6.1. **Quantisation damage showed up as a
generation-length failure, not a reasoning one** — and a benchmark that only
asked short questions would have scored the two quants as equivalent.

## Speed

### Generation at empty context (tok/s)

```
Qwen3-Coder-30B  ██████████████████████████████████ 92
gpt-oss-20b Q4   ██████████████████████████████     81
gpt-oss-20b Q8   ███████████████████████████▊       75
gemma-4-26B      ███████████████████████████▍       74
Qwen3.6-35B      ███████████████████████▎           63
gpt-oss-120b     ███████████████████████▉           54
Llama-3.1-8B     ████████████████▍                  44
Qwen3VL-8B       ████████████████▎                  44
Llama-3-14B      █████████▎                         25
Hermes-4-14B     █████████▎                         25
Qwen3.6-27B      ████▊                              13
gemma-4-31B      ████▋                              12
```

Dense models run 5–7× slower than MoE models of comparable size on this
hardware, which reverses the apparent ranking: gemma-4-31B and Qwen3.6-27B score
at the top and generate at 12–13 tok/s.

### Throughput retained at 16k context

```
Qwen3.6-27B      ███████████████████████   96%    12.7 -> 12.2 tok/s
Qwen3.6-35B      ██████████████████████▍   93%    62.7 -> 58.2 tok/s
gpt-oss-120b     █████████████████████▉    91%    53.7 -> 48.7 tok/s
gemma-4-31B      █████████████████████▌    89%    12.2 -> 10.9 tok/s
gpt-oss-20b Q8   █████████████████████▍    89%    74.9 -> 66.6 tok/s
gpt-oss-20b Q4   █████████████████████     87%    80.9 -> 70.3 tok/s
Hermes-4-14B     ████████████████████▎     84%    24.8 -> 20.9 tok/s
gemma-4-26B      ████████████████████      84%    74.0 -> 61.8 tok/s
Llama-3-14B      ██████████████████▉       78%    24.9 -> 19.5 tok/s
Llama-3.1-8B     ██████████████████▊       78%    44.3 -> 34.6 tok/s
Qwen3VL-8B       ██████████████████▍       77%    43.6 -> 33.4 tok/s
Qwen3-Coder-30B  ████████████████▊         69%    91.7 -> 63.5 tok/s
```

**This is the chart that changes a decision.** Qwen3-Coder leads at empty
context by 22% over gpt-oss-20b-Q8 and *trails* it at 16k — 63.5 against 66.6
tok/s. Agent work lives at depth, so ranking models by headline tok/s mis-sorts
exactly the workload you'd pick a fast model for.

### Speed against accuracy

```mermaid
quadrantChart
    title Generation speed vs one-shot coding score
    x-axis "12 tok/s" --> "92 tok/s"
    y-axis "0/68" --> "68/68"
    quadrant-1 "fast and accurate"
    quadrant-2 "accurate but slow"
    quadrant-3 "slow and weak"
    quadrant-4 "fast and weak"
    "gpt-oss-120b": [0.537, 1.0]
    "gpt-oss-20b Q8": [0.749, 0.956]
    "gemma-4-26B": [0.740, 0.956]
    "Qwen3-Coder-30B": [0.917, 0.838]
    "Qwen3.6-35B": [0.627, 0.838]
    "Qwen3.6-27B": [0.127, 0.838]
    "gemma-4-31B": [0.122, 1.0]
    "Qwen3VL-8B": [0.436, 0.456]
    "gpt-oss-20b Q4": [0.809, 0.368]
    "Hermes-4-14B": [0.248, 0.338]
    "Llama-3.1-8B": [0.443, 0.279]
    "Llama-3-14B": [0.249, 0.0]
```

### Reasoning score per GB resident

What a memory budget buys, which on a unified-memory box is the binding
constraint:

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

Every score above is a median of three identical passes, because single passes
disagree with themselves badly. Range across three runs at `temperature 0`,
same prompt, same settings:

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
slot state. Only four models here have a stable score, and two of those are
stable at 0/68 and 19/68.

The fix is more items, not more passes: the 102-item reasoning track produces
pass-to-pass spreads of 0–2 points on the same hardware, against up to 17 on the
68-check coding benchmark.

## What to actually run

- **Have 63 GB spare and want it right:** gpt-oss-120b. Nothing else is
  perfect on every track, and its variance is zero.
- **Want one model resident all day:** gpt-oss-20b-Q8. 12 GB, 75 tok/s, 89%
  throughput retained at depth, top-3 on every track.
- **Don't use Q4 of a model you benchmarked at Q8** without re-running the
  coding tracks. The quality loss hides from short-answer evaluations.
- **Ignore headline tok/s for agent work.** Rank by throughput at the context
  depth you actually operate at.

## Provenance

Coding and agent tracks run 2026-07-31 and 2026-08-04; reasoning 2026-08-01 and
2026-08-05; speed swept 2026-08-05 in a single thermal session with drift
controls at start, middle and end agreeing within 0.2%. Models carried over
between speed sessions reproduced within 1%.

Two caveats on the data: **gemma-4-31B's speed row is the 2026-08-04
measurement** (its model file was deleted from the box, and the re-run has since
failed twice with an ssh reset mid-model — the controls justify carrying the
earlier number). **Kimi-Linear-48B has never been scored** — it fails to load
and takes the server down with it.

Scores are comparable only within this machine and these decode settings. The
agent track is a single pass, so treat ±3 there as noise; the ±17 above applies
to the one-shot column.
