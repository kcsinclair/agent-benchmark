# leia

The machine most results in this repo were produced on. Quote this file's name
alongside any score from it — the same model scores the same but runs 6× faster
or slower depending on the box, and on this one the architecture of the model
matters more than its size.

## Hardware

| | |
|---|---|
| CPU | AMD Ryzen AI MAX+ 395 (Strix Halo), 32 threads |
| GPU | Radeon 8060S integrated, `RADV STRIX_HALO` (Vulkan) |
| Memory | 89 GB unified (UMA), 7 GB swap |
| Storage | 915 GB NVMe (`/dev/nvme0n1p2`) |
| OS | Ubuntu 26.04 LTS, kernel 7.0.0-28-generic |

Unified memory is the important part: there is no discrete VRAM to run out of
(`rocm-smi` reports a 2 GB carve-out, which is not the real limit — a 63 GB
model loads fine). What you run out of instead is **memory bandwidth**, and that
is what sets the ceiling on generation speed.

Vulkan device capabilities: `uma: 1`, `fp16: 1`, `bf16: 0`, warp size 64,
64 KB shared memory, `KHR_coopmat` matrix cores.

## Serving

`llama-server` runs as a **user** systemd unit — `systemctl --user
{start,stop,status} llama-server.service` — described as "llama.cpp multi-model
router (Vulkan)". Stopping it takes Lexi (the Hermes agent) offline; nothing
else depends on it.

```
llama-server --models-dir /opt/local-ai/models --models-max 2 \
  --ctx-size 262144 --cache-type-k q8_0 --cache-type-v q8_0 \
  --n-gpu-layers 999 --flash-attn on --jinja \
  --log-timestamps --log-verbosity 4 \
  --host 0.0.0.0 --port 7442
```

Endpoint: `http://leia.packsin.com:7442` (OpenAI-compatible). llama.cpp build
**`b10380-0b1bad14f`** since 2026-08-12; everything in the speed table below,
and every score dated on or before 2026-08-11, was measured on the previous
build `b9892-ee445f93d`.

**The router does not log to the journal.** The unit sets
`StandardOutput=append:/opt/local-ai/logs/llama-server.log`, so
`journalctl --user -u llama-server.service` shows only start/stop lines and a
child model's load failure appears nowhere in it. Read the log file instead, or
reproduce the load directly with
`/opt/local-ai/bin/llama-cli -m <path>.gguf -ngl 999 -c 2048 -n 8`, which prints
the real reason in seconds.

Router behaviour worth knowing:

- **`--models-max 2`** keeps up to two models resident and autoloads on
  demand (`models_autoload: true`). On a unified-memory box that is RAM the next
  load needs, and it is the cause of the intermittent
  `HTTP 500 "model failed to load"` errors — the same model that fails under
  memory pressure loads fine on an idle server. Retrying works; three of six
  models failed their first load attempt and succeeded on the second during one
  sweep. Consider `--models-max 1` for serial benchmarking.
- **`POST /models/unload`** with `{"model": "<id>"}` unloads gracefully. It
  returns `{"success":true}` immediately but the unload is **asynchronous** —
  the model still reports `loaded` for a few seconds, and is gone by ~10s.
  There is no matching `/models/load`; loading happens on first use.
- `--jinja` is what makes tool calling work at all. Without it the chat template
  is not applied and no `tool_calls` come back.
- **An `ollama` llama-server also runs on this box**, holding its own model with
  `-c 131072`. It competes for the same unified memory and is a plausible
  contributor to load failures.

Binaries live in **`/opt/local-ai/bin`** (`llama-server`, `llama-bench`, and the
`libggml*.so` they link against). That directory is **not on the PATH of a
non-login shell**, so remote commands need the full path or a login shell:

```bash
ssh leia "bash -lc '/opt/local-ai/bin/llama-bench ...'"   # works
ssh leia "llama-bench ..."                                # command not found
```

**Upgrading llama.cpp.** The source tree is `~keith/llama.cpp`; it is built
there and the good binaries are copied into `/opt/local-ai/bin`. The build dir
is already configured (Vulkan, Release, shared libs, ccache) — `git checkout
<tag> && cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release && cmake
--build build -j 30` takes a few minutes on 32 cores. Then stop the service,
`cp -a ~/llama.cpp/build/bin/. /opt/local-ai/bin/`, and start it again.

Three things to know before doing that:

- `BUILD_SHARED_LIBS=ON`, so the executables and their `libggml*.so` must move
  together. Old sonames accumulate in the directory (0.15.1, 0.15.3, 0.19.0 all
  present) and the unversioned `.so` tracks the newest — copying, not wiping, is
  what keeps this working.
- **`/opt/local-ai/bin` is not exclusively llama.cpp.** `sd-server`, `sd-cli`,
  `z-image`, `qwen-image-edit.sh`, `describe`, `swap` and `lexiperms.sh` live
  there too. Never clear the directory. `sd-server` carries its own statically
  linked ggml and does not follow the `.so` upgrade.
- Back up first (`cp -a /opt/local-ai/bin /opt/local-ai/bin.bak-<build>-<date>`,
  ~600 MB); rolling back is then a copy in the other direction.

## Measured performance

`llama-bench`, 2026-07-31, flags matching the serving config
(`-fa on -ctk q8_0 -ctv q8_0 -ngl 999 -r 3`):

| model | size | pp512 | tg@0 | tg@4k | tg@16k |
|---|---|---|---|---|---|
| Qwen3-Coder-30B-A3B | 18 GB | 1309 | 92 | 81 | 63 |
| gemma-4-26B-A4B | 14 GB | 1375 | 74 | 67 | 62 |
| Qwen3.6-35B-A3B | 23 GB | 1121 | 62 | 61 | 58 |
| gpt-oss-120b-MXFP4 | 63 GB | 624 | 54 | 53 | 49 |
| Qwen3.8-27B ◆ | 16 GB | 351 | 13 | 13 | 12 |
| Qwen3.6-27B | 17 GB | 363 | 13 | 13 | 12 |
| gemma-4-31B ◆ | 17 GB | 287 | 12 | 12 | 11 |
| Muse-Glimmer-30B (Q8) ‡ | 32 GB | 348 | 7.4 | 7.4 | 7.3 |

tokens/sec; `pp` = prompt processing, `tg` = generation, `@N` = context depth.

◆ measured 2026-08-26 on build `b10380`. `gemma-4-31B` was re-run rather than
carried over: it reads 287 / 12.2 / 11.6 / 10.9 against the 288 / 12 / 12 / 11
recorded on `b9892`, so its row is now a b10380 measurement and the two builds
agree on a dense model as well as on the control.

‡ measured 2026-08-12 on build `b10380`, the rest on `b9892`. The two are
comparable: the thermal control model was re-run on the new build and read
74.3 / 74.3 / 74.3 tok/s against 74.0 / 73.8 / 74.1 on the old one — 0.3%, well
inside the noise this control exists to detect. **The upgrade changed no
throughput.**

**Dense models are 5–7× slower than mixture-of-experts models here, at
comparable size.** gemma-4-31B and Qwen3.6-27B are dense: every token reads the
full ~17 GB of weights, and bandwidth caps that at 12–13 tok/s. The A3B/A4B and
MXFP4 models touch only their active experts and reach 54–92 tok/s. On this
machine, *architecture predicts speed far better than parameter count does* —
a 63 GB MoE outruns a 17 GB dense model four to one.

Context depth costs little: everything degrades gracefully to 16k, worst case
−32% (Qwen3-Coder), most under 10%. Multi-turn agent work does not fall off a
cliff.

**Muse-Glimmer is the slowest model measured here and the flattest.** 7.4 tok/s
is bandwidth doing exactly what the dense rule predicts — 32 GB of weights read
per token against gemma-4-31B's 17 GB at 12 tok/s, which scales almost exactly.
But it loses only **1.2%** from depth 0 to 16k, against −32% for the fastest
model in the table, and its prompt processing sits in the dense band (348)
rather than the MoE one. Its published architecture alternates three
2048-token sliding-window layers with a fourth full-attention NoPE layer, so
most layers never see the full context and depth costs it almost nothing. Size
sets its floor; depth does not lower it.

## Thermal behaviour

Idle `Tctl` ~27 °C, peak 63 °C under a full sweep. A control model re-run at the
start, middle and end of a 13-minute sweep varied by **0.1%** (74.1 / 74.0 /
74.1 tok/s). No cooldown between runs is necessary, and scheduled gaps would
cost availability to fix a problem that does not exist. Re-measure with
`run_llama_bench.sh` if the cooling situation changes.

Temperatures are readable via `sensors` (`Tctl`, `edge`); `nvidia-smi` does not
exist here, `rocm-smi` does.

## History

- **2026-08-12** — upgraded llama.cpp from `b9892-ee445f93d` (built 07-18) to
  `b10380-0b1bad14f`, because `Muse-Glimmer-30B` failed to load with
  `unknown model architecture: 'muse-glimmer'`; that architecture was merged
  upstream on 08-10 and first shipped in b10353. Previous binaries are kept at
  `/opt/local-ai/bin.bak-b9892-20260812`. Qwen3-Coder-30B was re-run on the new
  build as a regression check and scored 56/68, inside its own recorded 56·57·58
  spread, so the two builds are treated as comparable for accuracy — and the
  thermal control re-measured on b10380 came back within 0.3%, so they are
  comparable for speed too. Only the Muse-Glimmer row of the speed table was
  measured on the new build; the rest still carry their 07-31 b9892 numbers,
  which the control says is fine.
- **2026-07-31** — `~/bin` and `~/models` were emptied during maintenance while
  the router kept running from its deleted binary. Disk was at 95% (47 GB free),
  which will not fit the 63 GB model. If a benchmark suddenly reports
  `command not found` or every model failing to load, check these first.
- **Kimi-Linear-48B-A3B** has never successfully loaded here — it fails in the
  router and failed under `llama-bench` too, then the binaries disappeared
  before the error could be captured. Unresolved: may need a newer llama.cpp
  build for that architecture. It also appears to take the router down with it,
  so put it last in any fleet run.
