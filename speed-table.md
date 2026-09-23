| model | size | pp512 | tg@0 | tg@4096 | tg@16384 | one-shot | agent |
|---|---|---|---|---|---|---|---|
| gemma-4-E2B | 3GB | 3365 | 103 | 98 | 88 | 34/68 | - |
| Qwen3-Coder-30B | 18GB | 1303 | 92 | 81 | 64 | 57/68 (56-57-58) | 57/68 |
| gpt-oss-20b-Q4 | 12GB | 1658 | 81 | 77 | 70 | 25/68 (24-25-37) | 37/68 |
| gpt-oss-20b-Q8 | 12GB | 1641 | 75 | 71 | 67 | 65/68 (51-65-68) | 68/68 |
| gemma-4-26B | 14GB | 1388 | 74 | 68 | 62 | 65/68 (54-65-65) | 68/68 |
| gemma-4-E4B | 4GB | 1977 | 66 | 62 | 55 | 37/68 | - |
| gemma-4-26B-heretic | 17GB | 1246 | 66 | 60 | 55 | 61/68 | - |
| gpt-oss-20b-UD-Q8_K_XL | 13GB | 1610 | 65 | 62 | 59 | 64/68 (63-64-65) | 48/68 |
| Qwen3.6-35B | 23GB | 1115 | 63 | 61 | 58 | 57/68 (53-57-57) | 65/68 |
| gpt-oss-120b | 63GB | 630 | 54 | 52 | 49 | 68/68 (68-68-68) | 68/68 |
| gemma-4-26B-Q8 | 28GB | 1211 | 45 | 42 | 40 | 54/68 (54-54-54) | 57/68 |
| Llama-3.1-8B | 5GB | 1281 | 44 | 41 | 35 | 19/68 (19-19-19) | 0/68 |
| Qwen3VL-8B | 5GB | 1261 | 44 | 40 | 33 | 31/68 (31-31-45) | 41/68 |
| Llama-3-14B | 9GB | 679 | 25 | 23 | 19 | 0/68 (0-0-0) | 0/68 |
| Hermes-4-14B | 9GB | 750 | 25 | 24 | 21 | 23/68 (22-23-31) | 8/68 |
| Qwen3.8-27B | 16GB | 351 | 13 | 13 | 12 | 68/68 (57-68-68) | - |
| Qwen3.6-27B | 17GB | 360 | 13 | 13 | 12 | 57/68 (57-57-66) | 67/68 |
| gemma-4-31B | 17GB | 287 | 12 | 12 | 11 | 68/68 (68-68-68) | 65/68 |
| Muse-Glimmer-30B | 32GB | 348 | 7 | 7 | 7 | 68/68 | 28/68 |

Thermal control (same model re-run through the sequence):
  start              74.1 tok/s   +0.0% vs start
  middle             74.1 tok/s   +0.0% vs start
  end                74.1 tok/s   +0.0% vs start
  A drift under ~2%% means back-to-back running is fine and the table above needs no caveat.

Run log (wall clock and Tctl per model):
  control-start          8s   26.5C -> 41.0C
  gemma-4-31B          241s   39.4C -> 61.1C
  gemma-4-26B           49s   58.9C -> 59.2C
  gpt-oss-120b         132s   57.2C -> 56.5C
  Qwen3-Coder-30B       69s   54.8C -> 62.2C
  control-middle        14s   59.9C -> 56.9C
  Qwen3.6-27B          195s   54.9C -> 63.0C
  Qwen3.6-35B           64s   60.6C -> 60.6C
  control-end           10s   45.6C -> 55.9C
  control-start         13s   30.5C -> 45.5C
  gemma-4-26B           48s   41.5C -> 53.6C
  gpt-oss-120b         136s   51.8C -> 55.9C
  Qwen3-Coder-30B       69s   54.4C -> 62.1C
  Qwen3.6-27B          195s   60.0C -> 64.5C
  Qwen3.6-35B           65s   62.1C -> 61.8C
  control-middle        14s   59.6C -> 59.4C
  gpt-oss-20b-Q8        47s   57.5C -> 63.5C
  gpt-oss-20b-Q4        45s   61.4C -> 64.2C
  Hermes-4-14B         119s   62.0C -> 65.4C
  Llama-3-14B          129s   63.1C -> 65.4C
  Qwen3VL-8B            74s   63.4C -> 66.5C
  Llama-3.1-8B          71s   64.2C -> 66.1C
  control-end           13s   63.9C -> 61.5C
  control-start         12s   31.1C -> 45.8C
  Muse-Glimmer-30B     266s   44.1C -> 63.1C
  control-middle        11s   61.1C -> 60.4C
  control-end            7s   58.4C -> 60.0C
  control-start         12s   42.1C -> 57.8C
  gemma-4-26B-Q8        73s   55.9C -> 61.4C
  gemma-4-26B-heretic    58s   59.4C -> 62.6C
  control-middle        13s   60.8C -> 60.5C
  gemma-4-E4B           41s   58.9C -> 61.4C
  gemma-4-E2B           27s   59.6C -> 63.4C
  control-end            7s   61.5C -> 62.0C
  control-start         12s   30.2C -> 45.8C
  gemma-4-31B          239s   44.2C -> 64.9C
  control-middle         8s   62.6C -> 62.2C
  Qwen3.8-27B          191s   60.4C -> 67.4C
  control-end            8s   65.1C -> 64.4C
  control-start         13s   30.8C -> 46.0C
  gpt-oss-20b-UD-Q8_K_XL    50s   44.0C -> 57.0C
  control-middle         7s   54.4C -> 54.1C
  control-end            7s   52.0C -> 54.2C
  control-start          7s   31.2C -> 46.8C
  gemma-4-31B          240s   44.8C -> 65.1C
  control-middle         8s   62.5C -> 63.1C
  control-end            8s   60.9C -> 62.6C
