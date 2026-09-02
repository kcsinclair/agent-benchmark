# openrouter

Where the hosted-model results come from. Quote this file's name alongside any
score under `results/openrouter/`, the same way `leia` is quoted — but read the
next paragraph first, because this file cannot do what `servers/leia.md` does.

**OpenRouter is not a machine.** `servers/leia.md` pins a score to fixed
hardware: one CPU, one GPU, one memory bandwidth, one llama.cpp build. That is
what makes two scores on leia comparable. OpenRouter is a *router* over many
independent providers, each with its own hardware, its own quantisation and its
own serving defaults — and one model slug can be served by any of them.
`anthropic/claude-sonnet-5` has eight endpoints across four vendors;
`openai/gpt-oss-20b` has twelve spanning bf16, fp8 **and** fp4.

So the unit that plays leia's role here is **the provider endpoint, not the
server**. It is recorded per request in every `.meta.json` as `provider`, and it
is the first thing to check before comparing two hosted scores.

## Pinning is mandatory

`--provider NAME` pins the upstream and disables fallbacks. Without it,
OpenRouter picks — and it picked **Amazon Bedrock** for the first unpinned
Sonnet run here, not Anthropic. `allow_fallbacks: false` alone does *not* pin;
it only stops failover after the choice is made.

This matters more than it does for a frontier model. This benchmark scores
Q4_K_M and Q8_0 as **separate contestants**, so an unpinned open-weight run can
silently land on a *worse* quantisation than the local GGUF it is being compared
against — inverting the comparison it exists to make.

Enumerate before choosing:

```bash
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models/<vendor>/<slug>/endpoints \
  | python3 -m json.tool | grep -E 'provider_name|quantization|max_completion'
```

## What the recorded results were pinned to

| model | provider | quantisation |
|---|---|---|
| `anthropic/claude-sonnet-5` | Anthropic | n/a (closed weights) |
| `openai/gpt-oss-20b` | DeepInfra | bf16 |
| `openai/gpt-oss-120b` | DeepInfra | bf16 |
| `google/gemma-4-31b-it` | Novita | bf16 |
| `qwen/qwen3-coder-30b-a3b-instruct` | SiliconFlow | fp8 |
| `qwen/qwen3.6-27b` | DeepInfra | fp8 |
| `qwen/qwen3.6-35b-a3b` | DeepInfra | fp8 |

Each was pinned to the highest fidelity that provider offered. Where a model
appears in a `.meta.json` under a *different* provider than the row above, that
result predates a correction and should not be read — see below.

## Quirks worth knowing

- **A `~` prefix marks a floating alias, which cannot be pinned and must not be
  recorded.** `~google/gemini-flash-latest` returns an *empty* `endpoints` list
  from `/v1/models/<slug>/endpoints`, so there is no provider to pin and no
  quantisation to read — the one thing this file says is mandatory is
  structurally unavailable. It currently resolves to `google/gemini-3.7-flash`
  (identical $0.75/$3.75 pricing, confirmed by testing), but *currently* is the
  problem: what it serves changes without the slug changing, so the row cannot
  be reproduced later. It also scores under a different directory —
  `google_gemini-flash-latest` rather than `google_gemini-3.7-flash` — so the
  same model recorded under both names reads as two contestants. Use an alias to
  look, the concrete slug to record.
- **Some endpoints mandate reasoning, and no metadata says which.** DeepInfra's
  gpt-oss and Google's Gemini both reject `reasoning: {effort: "none"}` with
  *"Reasoning is mandatory for this endpoint and cannot be disabled"* — while
  advertising both `reasoning` and `reasoning_effort` in
  `supported_parameters`. The refusal is the only signal, so `run_http.probe`
  asks for it deliberately with a one-token request before the run, and
  `send` remembers it per model. Without that memo every request rediscovered
  it: 15 rejected round trips on a 3-pass coding sweep, 306 on a 3-pass
  reasoning run. Consequence unchanged: those scores are **not**
  decode-comparable with leia's `--think off` runs, and the header and
  `.meta.json` say so rather than claiming `think=off`.
- **A vendor prefix in the slug is not the provider.** `google/gemma-4-31b-it`
  is served by **16 endpoints and not one of them is Google** — the prefix names
  who made the weights. Pinning `--provider Google` removed every candidate and
  returned a bare `404 No endpoints found`, which reads like the model does not
  exist. `run_http.explain_no_endpoints` now asks the endpoints API which
  filter actually emptied the list and names the providers that do serve it, and
  `probe` treats it as fatal so the model is skipped rather than failing
  identically once per problem per pass. The rule: a **closed** model's prefix
  usually is its provider (`anthropic/`, `openai/`), an **open-weight** one's
  never reliably is.
- **A provider pin is not a quantisation pin.** DeepInfra offers
  `gemma-4-31b-it` on three endpoints — `deepinfra/turbo` at fp4,
  `deepinfra/fp8`, and `deepinfra/ultra` at fp8 — so `--provider DeepInfra`
  still leaves fp4-vs-fp8 to the router, and `.meta.json` records the provider
  name, not the tier. Since this benchmark scores Q4_K_M and Q8_0 as separate
  contestants, prefer a provider offering exactly **one** endpoint for that
  slug; there, the pin fixes the quantisation too. For `gemma-4-31b-it` that is
  everyone except DeepInfra — e.g. Novita (bf16), CoreWeave (fp4), Cerebras
  (fp16), SiliconFlow (fp8).
- **Check the cap before pinning.** The runner asks for `max_tokens 16384` by
  default, which alone rules out Venice (8192), Friendli (8192) and
  `deepinfra/ultra` (8192) for this model — the same bare 404, a different
  cause.
- **`Google` means Vertex; `Google AI Studio` is the other one.** Both are
  Google serving the same weights, but OpenRouter's display name for Vertex AI
  is bare `Google`, so `--provider Google` does *not* mean "let Google pick".
  The difference that matters here: **no Vertex endpoint advertises
  `temperature`** (checked across all six `gemini-3.7-flash` endpoints), while
  all three AI Studio ones do. `decorate` decides whether to send temperature
  from the *model-level* `supported_parameters`, which is the union over
  endpoints and therefore includes it — so pinning Vertex sends a temperature
  the endpoint does not claim to accept, and reports it as sent. Prefer
  `Google AI Studio` for a temperature-0 run. Watch the tier too: the
  `google-vertex/global/flex` endpoint was at 79% uptime over 24h while plain
  `google-vertex/global` was at 99.6%.
- **Endpoints cap `max_tokens` independently, and exceeding it makes a request
  unroutable.** DeepInfra serves `qwen3.6-35b-a3b` at 16384 completion tokens;
  asking for 32768 with the provider pinned returns a bare
  `404 No endpoints found` and scores 0/68. The runner now explains this.
  SiliconFlow caps `gpt-oss-20b` at 8192 while DeepInfra allows 131072 — the
  same slug, wildly different ceilings.
- **A provider can bill for tokens and return nothing.** Novita served
  `qwen3-coder-30b` with `content: None`, `reasoning: None`, `refusal: None`,
  `finish_reason: stop` and 791 billed completion tokens. Three of five problems
  came back blank (22/68 against 57/68 local). SiliconFlow, Alibaba and
  DigitalOcean returned 2700–3000 characters for the identical request. gemma-
  4-31b on the same provider was unaffected, so it is per-model, not blanket.
- **Transient failures are common enough to invalidate single runs.** One agent
  problem went 0/17 → 17/17 unchanged on retry; one reasoning run lost 18 of 102
  items including the whole retrieval category, and the same requests succeeded
  on manual retry. leia runs at `-r 3`; hosted runs need the same before they
  are comparable with it.
- **Sampling is not held constant** — the open one. The runner sets
  `temperature` and `max_tokens` only, so `top_p`, `top_k`, `repetition_penalty`
  and friends fall back to each provider's defaults, which differ from
  llama.cpp's. A `repetition_penalty` other than 1.0 changes output **even at
  temperature 0**. This is the leading suspect for two models scoring *lower*
  hosted at higher precision than locally at Q4. See CLAUDE.md.

## No speed track

`results/openrouter/speed/` does not exist and should not. `llama-bench`
measures leia's GPU under controlled conditions; a hosted timing measures
network latency plus whatever else that provider was serving at the time, on
hardware whose specification is not published. The two are not the same
quantity and must not share a column. Per-request wall-clock is still recorded
in each `.meta.json` (`seconds`) for cost and throughput context — treat it as
an observation about the service, never about the model.

## Cost

Unlike leia, every request here is billed, and OpenRouter returns the real
figure in `usage.cost` — so it lands in each `.meta.json` and totals in the run
summary. A full 68-check one-shot sweep of Claude Sonnet 5 cost $0.05; the
mid-sized open-weight models run at fractions of a cent. Cost-per-check is
therefore nearly free to compute here and impossible on leia, where the cost is
electricity and a machine you already own.
