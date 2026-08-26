#!/usr/bin/env python3
"""Run the benchmark prompts against an OpenAI-compatible server.

Usage:
    run_http.py [options] <model-id> [<model-id> ...]
    run_http.py --list-models

Each problem is one request: the PROMPT.md goes in as a single user message,
greedy decoding, no system prompt, no retries — the contestant's first answer,
same rule as every other entry in this benchmark. The reply is saved and the
code blocks are extracted into the deliverable filenames, producing
results/<server>/oneshot/<model>/ ready for run_all.sh.

Two back ends, one client. Point --server at a llama.cpp server (the default)
or at OpenRouter to run frontier models through the same code path — the whole
fairness argument here is that only the model varies, so a per-vendor adapter
layer would make every difference between those layers a confound. OpenRouter
mode is entered automatically when the server host is openrouter.ai, and it
changes four things: requests are authenticated, the thinking switch moves from
llama.cpp's chat_template_kwargs to OpenRouter's `reasoning` field, decode
parameters the model does not accept are dropped *and reported* rather than
silently sent, and the upstream provider that served each request is recorded.

Options:
  -s, --server URL      server base (default $BENCH_SERVER or
                        http://leia.packsin.com:7442). Set it to
                        https://openrouter.ai/api for frontier models.
      --key-file PATH   OpenRouter key file. Looked for in
                        $OPENROUTER_API_KEY, then OPENROUTER_API_KEY= in the
                        repo's gitignored .env, then this path (default
                        ~/.config/openrouter/key)
      --provider NAME   pin the upstream provider and disable fallbacks. One
                        OpenRouter slug can route to several providers at
                        differing quantisation, and this benchmark treats
                        Q4_K_M and Q8_0 as separate contestants, so silent
                        routing would undo that distinction. The provider that
                        actually served each request is always recorded.
  -o, --only LIST       problems to run, e.g. -o 1  or  -o 1,3,5
      --out DIR         output root (default results/<server>/oneshot)
  -m, --max-tokens N    generation cap (default 16384 — reasoning models spend
                        a lot before they answer)
  -t, --timeout SECS    per-request timeout (default 1800; a cold model load on
                        a swapping server can take minutes)
      --temperature F   default 0. Frontier Claude models reject temperature,
                        top_p and top_k outright; against OpenRouter the field
                        is dropped for any model whose supported_parameters
                        omit it, and both the header and the .meta.json say so
                        rather than claiming a temperature the request did not
                        carry.
      --think on|off    extended thinking, default off. Reasoning models fall
                        into repetition loops under greedy decoding and never
                        reach an answer, so thinking is disabled via
                        chat_template_kwargs (llama.cpp) or reasoning.effort
                        (OpenRouter); models that ignore or reject the switch
                        are reported per request. Thinking cannot be held
                        constant across a frontier fleet — it is on by default
                        on some models and cannot be disabled at all on others
                        — so the effective setting is recorded per model rather
                        than asserted fleet-wide. Use --think on only with
                        --temperature 0.6 or so.
      --reasoning-effort E  low|medium|high, for models that take it (gpt-oss)
                        instead of the enable_thinking switch
  -r, --repeat N        run the whole set N times per model and report the
                        median plus every pass. Identical requests at
                        temperature 0 do NOT return identical output on
                        llama.cpp (batching, MoE routing, quantised KV cache),
                        and a single problem has been seen to swing 0/11 to
                        11/11 across repeats, so a single pass is one draw from
                        a distribution, not a measurement.
      --no-warmup       skip the load request that makes a swapping server
                        resident before timing starts
  -g, --grade           run run_all.sh on each model when it finishes
  -k, --keep            keep an existing output dir instead of clearing it
  -h, --help            this message

These servers separate thinking from the answer: `reasoning_content` is saved
beside the transcript but never fed to the extractor, because chain-of-thought
is full of half-written code blocks that would beat the real answer. A reply cut
off by the token cap is reported loudly — that scores 0 for a reason that has
nothing to do with the model's ability.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_submission as ex   # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
DEFAULT_SERVER = os.environ.get("BENCH_SERVER", "http://leia.packsin.com:7442")
DEFAULT_KEY_FILE = os.path.expanduser("~/.config/openrouter/key")


def server_label(url):
    """http://leia.packsin.com:7442 -> 'leia'. Results are grouped per machine,
    because a score without a machine says nothing about speed."""
    host = re.sub(r"^\w+://", "", url).split("/")[0].split(":")[0]
    return host.split(".")[0] or "unknown"


def is_openrouter(url):
    return "openrouter.ai" in url


def read_dotenv(path):
    """-> {name: value} from a KEY=value file. Quotes and `export ` stripped,
    blanks and # comments skipped. Not a shell: no interpolation, no sourcing —
    this file holds a credential and is never executed."""
    out = {}
    try:
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, _, value = line.partition("=")
                name = name.strip()
                if name.startswith("export "):
                    name = name[len("export "):].strip()
                # tolerate the shapes a hand-written .env picks up — lowercase,
                # or a hyphen where a shell would need an underscore. Failing a
                # run over the spelling of a working key helps nobody.
                name = name.replace("-", "_").upper()
                out[name] = value.strip().strip("'\"")
    except OSError:
        pass
    return out


def load_key(key_file):
    """-> bearer token, and where it came from.

    Looked for in $OPENROUTER_API_KEY, then the repo's gitignored .env, then a
    key file. The key is read here and used only as a header — it never reaches
    a transcript, a .meta.json or a summary.
    """
    env = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if env:
        return env, "$OPENROUTER_API_KEY"
    dotenv = os.path.join(REPO, ".env")
    for name in ("OPENROUTER_API_KEY", "OPENROUTER_KEY"):
        value = read_dotenv(dotenv).get(name, "").strip()
        if value:
            return value, "%s in %s" % (name, dotenv)
    try:
        with open(key_file) as fh:
            key = fh.read().strip()
    except OSError:
        key = ""
    if not key:
        sys.exit("run_http: no OpenRouter key. Put one in $OPENROUTER_API_KEY,"
                 " in %s as OPENROUTER_API_KEY=..., or in %s"
                 % (dotenv, key_file))
    return key, key_file


def default_out(url, track):
    return os.path.join(REPO, "results", server_label(url), track)


PROBLEMS = sorted(ex.PROBLEMS)


class ApiError(Exception):
    """An HTTP error with the server's own explanation attached."""
    def __init__(self, code, detail):
        super().__init__("HTTP %s: %s" % (code, detail))
        self.code, self.detail = code, detail


def api(server, path, payload=None, timeout=60, key=None):
    url = server.rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {}
    if data:
        headers["Content-Type"] = "application/json"
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.load(r)
    except urllib.error.HTTPError as e:
        # llama-server puts the real reason ("failed to load") in the body;
        # a bare "HTTP 500" sends you looking in the wrong place
        raw = e.read().decode(errors="replace")
        try:
            detail = json.loads(raw)["error"]["message"]
        except Exception:
            detail = raw.strip()[:200] or e.reason
        raise ApiError(e.code, detail)
    # OpenRouter reports upstream failures as an error object inside a 200, so
    # a status-only check would record an empty answer as a real 0
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        err = body["error"]
        raise ApiError(err.get("code", 200), str(err.get("message", err))[:200])
    return body


def fetch_models(server, key=None):
    """-> {model_id: raw record}. Text-output models only."""
    try:
        body = api(server, "/v1/models", timeout=30, key=key)
    except (urllib.error.URLError, OSError) as e:
        sys.exit("run_http: cannot reach %s (%s)" % (server, e))
    out = {}
    for m in body.get("data", []):
        mods = (m.get("architecture") or {}).get("output_modalities") or []
        if mods and "text" not in mods:
            continue
        out[m["id"]] = m
    return out


def price_per_mtok(rec):
    """-> '$3.00/$15.00' or ''. OpenRouter quotes dollars per token."""
    p = rec.get("pricing") or {}
    try:
        return "$%.2f/$%.2f" % (float(p["prompt"]) * 1e6,
                                float(p["completion"]) * 1e6)
    except (KeyError, TypeError, ValueError):
        return ""


def print_models(server, key, pattern):
    """--list-models. llama-server hosts a handful of models and reports a
    resident/idle status; OpenRouter hosts hundreds and reports none, so the
    columns differ and a substring filter is the only way to read the list."""
    models = fetch_models(server, key)
    rows = sorted(k for k in models if pattern.lower() in k.lower())
    if not rows:
        print("no model matching %r on %s (%d text models offered)"
              % (pattern, server, len(models)))
        return
    for mid in rows:
        rec = models[mid]
        if is_openrouter(server):
            params = rec.get("supported_parameters") or []
            print("%-46s %14s  %s"
                  % (mid[:46], price_per_mtok(rec),
                     ",".join(sorted(set(params) &
                                     {"temperature", "reasoning",
                                      "include_reasoning", "tools"}))))
        else:
            print("%-50s %s" % (mid, (rec.get("status") or {}).get("value", "?")))
    if is_openrouter(server):
        print()
        print("%d shown of %d text models. Columns: price per Mtok in/out,"
              " then which of temperature/reasoning/tools the model accepts."
              % (len(rows), len(models)))


def slug(model_id):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model_id).strip("_")


def prepare(opts):
    """Resolve the back end before any request is made. -> key source, or None.

    Every track calls this, so one-shot, agent and reasoning runs all reach a
    hosted model through the same code — the comparability argument for this
    benchmark is that only the model varies, and that has to hold across tracks
    as well as within one.
    """
    opts["openrouter"] = is_openrouter(opts["server"])
    source = None
    if opts["openrouter"]:
        opts["key"], source = load_key(opts["key_file"])
    opts["models"] = fetch_models(opts["server"], opts["key"])
    return source


def decorate(payload, model, opts):
    """Add the decode parameters that depend on the model and the back end.
    Mutates `payload`. -> (mode, decode)

    `mode` is the human-readable thinking setting for the console; `decode` is
    what actually went on the wire, so a score can always be traced back to the
    request that produced it. The two exist because the fleet-wide flag and the
    per-model reality diverge: thinking is on by default on some frontier
    models and cannot be disabled on others, and the Claude models reject
    `temperature` outright. Printing a decode setting the request did not carry
    is the failure this function exists to prevent.
    """
    decode = {"max_tokens": payload.get("max_tokens")}
    rec = opts["models"].get(model) or {}
    # empty for llama.cpp, which advertises no such list — there, send
    # everything and let the server complain
    accepts = set(rec.get("supported_parameters") or [])

    if accepts and "temperature" not in accepts:
        decode["temperature"] = None
        decode["temperature_note"] = "not accepted by this model; field omitted"
    else:
        payload["temperature"] = opts["temperature"]
        decode["temperature"] = opts["temperature"]

    mode = "think=on"
    if opts["openrouter"]:
        if opts["think"] == "off":
            if accepts and "reasoning" not in accepts:
                mode = "think=n/a (no reasoning switch on this model)"
            else:
                payload["reasoning"] = {"effort": "none"}
                mode = "think=off"
        if opts["provider"]:
            payload["provider"] = {"order": [opts["provider"]],
                                   "allow_fallbacks": False}
        else:
            # no silent failover to a second provider mid-run: one slug can
            # route to several, and this benchmark treats differing
            # quantisations as separate contestants
            payload["provider"] = {"allow_fallbacks": False}
    elif opts["think"] == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
        mode = "think=off"

    if opts["reasoning_effort"]:
        payload["reasoning_effort"] = opts["reasoning_effort"]
        mode += ", effort=%s" % opts["reasoning_effort"]
    decode["thinking"] = mode
    return mode, decode


def send(server, payload, opts, decode=None):
    """POST a completion, retrying once if the *thinking switch* was refused.
    -> (body, replacement mode or None)

    Two different back ends refuse it two different ways: a llama.cpp template
    that does not implement `enable_thinking`, and a hosted endpoint that
    mandates reasoning (DeepInfra's gpt-oss does exactly this, with
    "Reasoning is mandatory for this endpoint and cannot be disabled").

    Both must be retried rather than recorded, because the alternative is a
    0/68 that reads as a model which cannot code when in fact every request was
    rejected before the model saw it. The retry drops the switch and the run
    says so, so the score is still honest about what was measured.
    """
    try:
        return api(server, "/v1/chat/completions", payload, opts["timeout"],
                   opts["key"]), None
    except ApiError as e:
        # OpenRouter routes by capability, so an over-large max_tokens silently
        # removes every candidate endpoint and the failure arrives as a bare
        # 404 that reads like the model does not exist. Raising --max-tokens to
        # cure a truncation once made a whole run unroutable and scored 0/68.
        if "no endpoints found" in (e.detail or "").lower():
            cap = payload.get("max_tokens")
            raise ApiError(e.code, "%s — no endpoint can serve this request. "
                           "max_tokens=%s may exceed the pinned provider's "
                           "max_completion_tokens; check "
                           "/v1/models/<slug>/endpoints" % (e.detail, cap))
        # `e` is unbound once this block ends, so keep what the retry needs
        detail = e.detail or ""
        low = detail.lower()
        if "chat_template_kwargs" in payload and "failed to load" not in low:
            payload.pop("chat_template_kwargs")
            note = "think=on (template ignores the switch)"
        elif "reasoning" in payload and "reasoning" in low:
            payload.pop("reasoning")
            note = "think=on (this endpoint mandates reasoning)"
        else:
            raise
    print("  (%s — retrying with %s)" % (detail[:70], note))
    sys.stdout.flush()
    if decode is not None:
        decode["thinking"] = note
    return api(server, "/v1/chat/completions", payload, opts["timeout"],
               opts["key"]), note


def build_payload(model, prompt, opts):
    """One user message, decorated for the back end. -> (payload, mode, decode)"""
    payload = {"model": model,
               "messages": [{"role": "user", "content": prompt}],
               "max_tokens": opts["max_tokens"]}
    mode, decode = decorate(payload, model, opts)
    return payload, mode, decode


def ask(server, model, prompt, opts):
    """-> dict with the reply and everything needed to reproduce it"""
    payload, mode, decode = build_payload(model, prompt, opts)
    t0 = time.time()
    body, note = send(server, payload, opts, decode)
    mode = note or mode
    took = time.time() - t0
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    return {
        "content": msg.get("content") or "",
        # llama.cpp calls it reasoning_content, OpenRouter calls it reasoning;
        # either way it is kept out of the extractor, because chain-of-thought
        # is full of half-written code blocks that would beat the real answer
        "reasoning": msg.get("reasoning_content") or msg.get("reasoning") or "",
        "finish": choice.get("finish_reason"),
        "native_finish": choice.get("native_finish_reason"),
        "usage": body.get("usage") or {},
        "provider": body.get("provider"),
        "served_model": body.get("model"),
        "id": body.get("id"),
        "seconds": took,
        "mode": mode,
        "decode": decode,
    }


def looped(content, finish):
    """A repetition loop, as distinct from an answer that ran out of room.

    Once a model starts cycling it stops introducing new lines, so the ratio of
    unique to total lines collapses — 97 unique lines out of 1193 in the case
    that prompted this. Calling that 'truncated' points at the token cap, which
    is the wrong culprit and costs an hour of looking in the wrong place.
    """
    lines = [l for l in content.split("\n") if l.strip()]
    if finish != "length" or len(lines) < 40:
        return False
    return len(set(lines)) / float(len(lines)) < 0.25


def warmup(server, model, timeout, key=None, attempts=3, pause=30):
    """Force a swapping server to load the model. -> (seconds, error)

    Loads fail intermittently on a swapping server — a model that loaded in
    0.1s an hour earlier can 500 while something else is still resident or the
    disk is busy. One failure is not evidence the model is broken, so retry
    before writing it off.
    """
    t0 = time.time()
    last = None
    for n in range(attempts):
        try:
            api(server, "/v1/chat/completions",
                {"model": model, "messages": [{"role": "user", "content": "hi"}],
                 "max_tokens": 1}, timeout, key)
            return time.time() - t0, None
        except (ApiError, urllib.error.URLError, OSError) as e:
            last = str(e)
            if n + 1 < attempts:
                print("  load attempt %d failed (%s) — retrying in %ds"
                      % (n + 1, last[:60], pause))
                sys.stdout.flush()
                time.sleep(pause)
    return time.time() - t0, last


def grade(outdir, label):
    """Run the grader and return (score, max) — None if it could not."""
    p = subprocess.run([os.path.join(HERE, "run_all.sh"), "-q", outdir, label],
                       capture_output=True, text=True)
    sys.stdout.write(p.stdout)
    m = re.search(r"^ TOTAL\s+(\d+) / (\d+)", p.stdout, re.M)
    return (int(m.group(1)), int(m.group(2))) if m else None


def run_pass(model, opts, outdir):
    """One full sweep of the problems. -> (trouble, seconds, dollars)"""
    tdir = os.path.join(outdir, "transcripts")
    os.makedirs(tdir, exist_ok=True)
    trouble = []
    elapsed = 0.0
    cost = 0.0
    providers = set()
    for problem in PROBLEMS:
        if opts["only"] and not selected(problem, opts["only"]):
            continue
        prompt_path = os.path.join(HERE, "problems", problem, "PROMPT.md")
        with open(prompt_path) as fh:
            prompt = fh.read()

        print("\n== %s ==" % problem)
        sys.stdout.flush()
        try:
            r = ask(opts["server"], model, prompt, opts)
        except (ApiError, urllib.error.URLError, OSError, ValueError) as e:
            print("  REQUEST FAILED: %s" % e)
            trouble.append("%s: request failed" % problem)
            continue

        content, reasoning = r["content"], r["reasoning"]
        usage, took = r["usage"], r["seconds"]
        with open(os.path.join(tdir, problem + ".txt"), "w") as fh:
            fh.write(content)
        if reasoning:
            with open(os.path.join(tdir, problem + ".reasoning.txt"), "w") as fh:
                fh.write(reasoning)
        meta = {"model": model, "served_model": r["served_model"],
                "provider": r["provider"], "request_id": r["id"],
                "server": opts["server"],
                "finish_reason": r["finish"],
                "native_finish_reason": r["native_finish"],
                "mode": r["mode"], "decode": r["decode"],
                "usage": usage, "seconds": round(took, 1)}
        with open(os.path.join(tdir, problem + ".meta.json"), "w") as fh:
            json.dump(meta, fh, indent=2)

        elapsed += took
        cost += float(usage.get("cost") or 0)
        if r["provider"]:
            providers.add(r["provider"])
        ct = usage.get("completion_tokens", "?")
        print("  %.0fs, %s completion tokens, %s, finish=%s%s%s%s"
              % (took, ct, r["mode"], r["finish"],
                 ", %d chars of reasoning" % len(reasoning) if reasoning else "",
                 ", via %s" % r["provider"] if r["provider"] else "",
                 ", $%.4f" % usage["cost"] if usage.get("cost") else ""))
        if looped(content, r["finish"]):
            print("  REPETITION LOOP — stopped producing new lines and cycled"
                  " until the %d token cap; not a size problem"
                  % opts["max_tokens"])
            trouble.append("%s: repetition loop" % problem)
        elif r["finish"] == "length":
            print("  TRUNCATED — hit the %d token cap" % opts["max_tokens"])
            trouble.append("%s: truncated" % problem)
        if not content.strip():
            # the classic greedy-decoding failure: it thought itself in circles
            print("  EMPTY answer — no content at all%s"
                  % (" (all %d tokens went to reasoning; that is a repetition"
                     " loop, not a hard problem)" % usage.get("completion_tokens", 0)
                     if reasoning else ""))
            trouble.append("%s: empty answer" % problem)
            continue

        _, missing = ex.extract_to(problem, content,
                                   os.path.join(outdir, problem))
        if missing:
            trouble.append("%s: %s not extracted" % (problem, ", ".join(missing)))

    # an open-weight slug can be served by several providers at differing
    # quantisation, and this benchmark scores Q4_K_M and Q8_0 as separate
    # contestants — so a score assembled from two providers is not one result
    if len(providers) > 1:
        trouble.append("served by %d providers in one pass (%s) — pin one with"
                       " --provider before trusting this score"
                       % (len(providers), ", ".join(sorted(providers))))
    if trouble:
        print()
        print("Problems worth a look before trusting this score:")
        for t in trouble:
            print("  - %s" % t)
        print("Raw replies are under %s" % tdir)
    return trouble, elapsed, cost


def run_model(model, opts):
    base = os.path.join(opts["out"], slug(model))
    if not opts["keep"] and os.path.isdir(base) and not opts["only"]:
        subprocess.call(["rm", "-rf", base])

    # the header must describe the request that will actually be sent, so it
    # is derived from the built payload rather than from the flags
    _, mode, decode = build_payload(model, "", opts)
    temp = ("temperature %s" % decode["temperature"]
            if decode.get("temperature") is not None
            else "temperature OMITTED (%s)" % decode["temperature_note"])
    rec = opts["models"].get(model) or {}

    print("=" * 60)
    print(" Model:   %s" % model)
    print(" Server:  %s%s" % (opts["server"],
                              "  (OpenRouter)" if opts["openrouter"] else ""))
    if opts["openrouter"]:
        print(" Price:   %s per Mtok in/out%s"
              % (price_per_mtok(rec) or "unknown",
                 ", provider pinned to %s" % opts["provider"]
                 if opts["provider"] else ", fallbacks off"))
    print(" Output:  %s" % base)
    print(" Decode:  %s, max_tokens %d, %s" % (temp, opts["max_tokens"], mode))
    if opts["repeat"] > 1:
        print(" Repeats: %d passes (same request each time — these models are"
              " not reproducible at temperature 0)" % opts["repeat"])
    print("=" * 60)
    sys.stdout.flush()

    result = {"model": model, "load_seconds": None, "passes": []}

    # a hosted model has nothing to load, so a warmup there is a paid request
    # that measures network latency and calls it a load time
    if opts["warmup"] and not opts["openrouter"]:
        secs, err = warmup(opts["server"], model, opts["timeout"], opts["key"])
        result["load_seconds"] = round(secs, 1)
        if err:
            print(" load FAILED after %.0fs: %s" % (secs, err))
            print(" skipping this model\n")
            result["error"] = err
            return result
        print(" model resident after %.0fs (load time excluded from the"
              " per-problem timings below)\n" % secs)
        sys.stdout.flush()

    for n in range(1, opts["repeat"] + 1):
        outdir = base if opts["repeat"] == 1 else os.path.join(base, "pass%d" % n)
        if opts["repeat"] > 1:
            print("\n" + "-" * 60)
            print(" pass %d of %d" % (n, opts["repeat"]))
            print("-" * 60)
        t0 = time.time()
        trouble, gen, cost = run_pass(model, opts, outdir)
        wall = time.time() - t0
        entry = {"pass": n, "dir": outdir, "generate_seconds": round(gen, 1),
                 "wall_seconds": round(wall, 1), "trouble": trouble}
        if cost:
            entry["cost_usd"] = round(cost, 4)
        if opts["grade"]:
            print()
            sys.stdout.flush()
            scored = grade(outdir, "%s pass %d" % (model, n))
            if scored:
                entry["score"], entry["max"] = scored
        result["passes"].append(entry)
        sys.stdout.flush()

    return result


def selected(problem, only):
    num = problem.split("-")[0]
    for item in only.replace(" ", "").split(","):
        if not item:
            continue
        if item == problem or item.zfill(2) == num:
            return True
    return False


def main(argv):
    opts = {"server": DEFAULT_SERVER, "only": "", "out": None,
            "max_tokens": 16384, "timeout": 1800, "temperature": 0.0,
            "think": "off", "reasoning_effort": "", "grade": False, "keep": False,
            "repeat": 1, "warmup": True, "key_file": DEFAULT_KEY_FILE,
            "provider": "", "key": None, "openrouter": False, "models": {}}
    models = []
    listing = None
    i = 0
    while i < len(argv):
        a = argv[i]
        def val():
            if i + 1 >= len(argv):
                sys.exit("run_http: %s needs an argument" % a)
            return argv[i + 1]
        if a in ("-h", "--help"):
            print(__doc__.strip()); return 0
        elif a == "--list-models":
            # an optional substring filter: against OpenRouter the unfiltered
            # list is hundreds of rows
            nxt = argv[i + 1] if i + 1 < len(argv) else ""
            listing = nxt if nxt and not nxt.startswith("-") else ""
            i += 2 if listing else 1
        elif a == "--key-file":         opts["key_file"] = val(); i += 2
        elif a == "--provider":         opts["provider"] = val(); i += 2
        elif a in ("-s", "--server"):   opts["server"] = val(); i += 2
        elif a in ("-o", "--only"):     opts["only"] = val(); i += 2
        elif a == "--out":              opts["out"] = val(); i += 2
        elif a in ("-m", "--max-tokens"): opts["max_tokens"] = int(val()); i += 2
        elif a in ("-t", "--timeout"):  opts["timeout"] = float(val()); i += 2
        elif a == "--temperature":      opts["temperature"] = float(val()); i += 2
        elif a == "--think":
            opts["think"] = val()
            if opts["think"] not in ("on", "off"):
                sys.exit("run_http: --think wants 'on' or 'off'")
            i += 2
        elif a == "--reasoning-effort": opts["reasoning_effort"] = val(); i += 2
        elif a in ("-r", "--repeat"):   opts["repeat"] = int(val()); i += 2
        elif a == "--no-warmup":        opts["warmup"] = False; i += 1
        elif a in ("-g", "--grade"):    opts["grade"] = True; i += 1
        elif a in ("-k", "--keep"):     opts["keep"] = True; i += 1
        elif a.startswith("-"):         sys.exit("run_http: unknown option %r" % a)
        else:                           models.append(a); i += 1

    if opts["out"] is None:
        opts["out"] = default_out(opts["server"], "oneshot")

    if listing is not None:
        opts["openrouter"] = is_openrouter(opts["server"])
        if opts["openrouter"]:
            opts["key"], _ = load_key(opts["key_file"])
        print_models(opts["server"], opts["key"], listing)
        return 0

    if not models:
        print(__doc__.strip())
        return 2

    source = prepare(opts)
    for m in models:
        if m not in opts["models"]:
            sys.exit("run_http: %r is not on %s (try --list-models)"
                     % (m, opts["server"]))
    if source:
        print("Key: %s" % source)

    started = time.time()
    results = []
    for n, model in enumerate(models):
        if n:
            print()
        results.append(run_model(model, opts))

    summarise(results, time.time() - started, opts)
    return 0


def summarise(results, wall, opts):
    print()
    print("=" * 78)
    if opts["openrouter"]:
        # a fleet-wide claim would be false here: thinking is on by default on
        # some frontier models and cannot be disabled on others, and the Claude
        # models reject temperature outright. Per-model reality is in the
        # run headers above and in each .meta.json.
        print(" SUMMARY — %d model(s), %d pass(es) each, thinking requested %s;"
              " effective decode is per model" % (len(results), opts["repeat"],
                                                  opts["think"]))
    else:
        print(" SUMMARY — %d model(s), %d pass(es) each, temperature %s,"
              " thinking %s" % (len(results), opts["repeat"],
                                opts["temperature"], opts["think"]))
    print("=" * 78)
    priced = any("cost_usd" in p for r in results for p in r["passes"])
    print(" %-42s %-18s %7s %8s%s"
          % ("model", "score", "load", "gen", "     cost" if priced else ""))
    print(" " + "-" * 76)
    for r in results:
        scores = [p["score"] for p in r["passes"] if "score" in p]
        gen = sum(p["generate_seconds"] for p in r["passes"])
        spent = sum(p.get("cost_usd", 0) for p in r["passes"])
        load = "%.0fs" % r["load_seconds"] if r["load_seconds"] is not None else "-"
        if r.get("error"):
            cell = "FAILED TO LOAD"
        elif not scores:
            cell = "not graded"
        elif len(scores) == 1:
            cell = "%d/%d" % (scores[0], r["passes"][0].get("max", 68))
        else:
            mx = r["passes"][0].get("max", 68)
            med = sorted(scores)[len(scores) // 2]
            cell = "%d/%d  (%s)" % (med, mx, "-".join(str(s) for s in sorted(scores)))
        print(" %-42s %-18s %7s %7.0fs%s"
              % (r["model"][:42], cell, load, gen,
                 "  $%7.4f" % spent if priced else ""))
    print(" " + "-" * 76)
    print(" total wall clock: %.0f min" % (wall / 60.0))
    if priced:
        total = sum(p.get("cost_usd", 0) for r in results for p in r["passes"])
        print(" total cost: $%.4f (as billed by the provider, not estimated)"
              % total)
    if opts["repeat"] > 1:
        print(" score column shows the median, with every pass in brackets;"
              " spread is sampling noise,")
        print(" not model quality — identical requests at temperature 0 do not"
              " return identical output here.")

    path = os.path.join(opts["out"], "summary-%s.json"
                        % time.strftime("%Y%m%d-%H%M%S"))
    try:
        with open(path, "w") as fh:
            json.dump({"wall_seconds": round(wall, 1),
                       "settings": {k: opts[k] for k in
                                    ("temperature", "max_tokens", "think",
                                     "repeat", "reasoning_effort", "server",
                                     "provider")},
                       "results": results}, fh, indent=2)
        print(" full detail: %s" % path)
    except OSError as e:
        print(" (could not write summary json: %s)" % e)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
