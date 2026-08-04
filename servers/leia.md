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
llama-server --models-dir /opt/local-ai/models --models-max 3 \
  --ctx-size 262144 --cache-type-k q8_0 --cache-type-v q8_0 \
  --n-gpu-layers 999 --flash-attn on --jinja \
  --host 0.0.0.0 --port 7442
```

Endpoint: `http://leia.packsin.com:7442` (OpenAI-compatible). llama.cpp build
`b9892-ee445f93d` at time of measurement.

Router behaviour worth knowing:

- **`--models-max 3`** keeps up to three models resident and autoloads on
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

Binaries live in `~/bin` (`llama-server`, `llama-bench`, and the `libggml*.so`
they link against). **`~/bin` is not on the PATH of a non-login shell**, so
remote commands need wrapping:

```bash
ssh leia "bash -lc 'llama-bench ...'"    # works
ssh leia "llama-bench ..."               # command not found
```

## Measured performance

`llama-bench`, 2026-07-31, flags matching the serving config
(`-fa on -ctk q8_0 -ctv q8_0 -ngl 999 -r 3`):

| model | size | pp512 | tg@0 | tg@4k | tg@16k |
|---|---|---|---|---|---|
| Qwen3-Coder-30B-A3B | 18 GB | 1309 | 92 | 81 | 63 |
| gemma-4-26B-A4B | 14 GB | 1375 | 74 | 67 | 62 |
| Qwen3.6-35B-A3B | 23 GB | 1121 | 62 | 61 | 58 |
| gpt-oss-120b-MXFP4 | 63 GB | 624 | 54 | 53 | 49 |
| Qwen3.6-27B | 17 GB | 363 | 13 | 13 | 12 |
| gemma-4-31B | 17 GB | 288 | 12 | 12 | 11 |

tokens/sec; `pp` = prompt processing, `tg` = generation, `@N` = context depth.

**Dense models are 5–7× slower than mixture-of-experts models here, at
comparable size.** gemma-4-31B and Qwen3.6-27B are dense: every token reads the
full ~17 GB of weights, and bandwidth caps that at 12–13 tok/s. The A3B/A4B and
MXFP4 models touch only their active experts and reach 54–92 tok/s. On this
machine, *architecture predicts speed far better than parameter count does* —
a 63 GB MoE outruns a 17 GB dense model four to one.

Context depth costs little: everything degrades gracefully to 16k, worst case
−32% (Qwen3-Coder), most under 10%. Multi-turn agent work does not fall off a
cliff.

## Thermal behaviour

Idle `Tctl` ~27 °C, peak 63 °C under a full sweep. A control model re-run at the
start, middle and end of a 13-minute sweep varied by **0.1%** (74.1 / 74.0 /
74.1 tok/s). No cooldown between runs is necessary, and scheduled gaps would
cost availability to fix a problem that does not exist. Re-measure with
`run_llama_bench.sh` if the cooling situation changes.

Temperatures are readable via `sensors` (`Tctl`, `edge`); `nvidia-smi` does not
exist here, `rocm-smi` does.

## History

- **2026-07-31** — `~/bin` and `~/models` were emptied during maintenance while
  the router kept running from its deleted binary. Disk was at 95% (47 GB free),
  which will not fit the 63 GB model. If a benchmark suddenly reports
  `command not found` or every model failing to load, check these first.
- **Kimi-Linear-48B-A3B** has never successfully loaded here — it fails in the
  router and failed under `llama-bench` too, then the binaries disappeared
  before the error could be captured. Unresolved: may need a newer llama.cpp
  build for that architecture. It also appears to take the router down with it,
  so put it last in any fleet run.
