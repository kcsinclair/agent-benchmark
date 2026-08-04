#!/usr/bin/env python3
"""Run the benchmark prompts against an OpenAI-compatible llama.cpp server.

Usage:
    run_http.py [options] <model-id> [<model-id> ...]
    run_http.py --list-models

Each problem is one request: the PROMPT.md goes in as a single user message,
greedy decoding, no system prompt, no retries — the contestant's first answer,
same rule as every other entry in this benchmark. The reply is saved and the
code blocks are extracted into the deliverable filenames, producing
results/<server>/oneshot/<model>/ ready for run_all.sh.

Options:
  -s, --server URL      llama.cpp server base (default $BENCH_SERVER or
                        http://leia.packsin.com:7442)
  -o, --only LIST       problems to run, e.g. -o 1  or  -o 1,3,5
      --out DIR         output root (default results/<server>/oneshot)
  -m, --max-tokens N    generation cap (default 16384 — reasoning models spend
                        a lot before they answer)
  -t, --timeout SECS    per-request timeout (default 1800; a cold model load on
                        a swapping server can take minutes)
      --temperature F   default 0
      --think on|off    extended thinking, default off. Reasoning models fall
                        into repetition loops under greedy decoding and never
                        reach an answer, so thinking is disabled via
                        chat_template_kwargs; models whose template ignores the
                        switch are reported per request. Use --think on only
                        with --temperature 0.6 or so.
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


def server_label(url):
    """http://leia.packsin.com:7442 -> 'leia'. Results are grouped per machine,
    because a score without a machine says nothing about speed."""
    host = re.sub(r"^\w+://", "", url).split("/")[0].split(":")[0]
    return host.split(".")[0] or "unknown"


def default_out(url, track):
    return os.path.join(REPO, "results", server_label(url), track)


PROBLEMS = sorted(ex.PROBLEMS)


class ApiError(Exception):
    """An HTTP error with the server's own explanation attached."""
    def __init__(self, code, detail):
        super().__init__("HTTP %s: %s" % (code, detail))
        self.code, self.detail = code, detail


def api(server, path, payload=None, timeout=60):
    url = server.rstrip("/") + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # llama-server puts the real reason ("failed to load") in the body;
        # a bare "HTTP 500" sends you looking in the wrong place
        body = e.read().decode(errors="replace")
        try:
            detail = json.loads(body)["error"]["message"]
        except Exception:
            detail = body.strip()[:200] or e.reason
        raise ApiError(e.code, detail)


def list_models(server):
    try:
        body = api(server, "/v1/models", timeout=30)
    except (urllib.error.URLError, OSError) as e:
        sys.exit("run_http: cannot reach %s (%s)" % (server, e))
    out = []
    for m in body.get("data", []):
        mods = (m.get("architecture") or {}).get("output_modalities") or []
        if mods and "text" not in mods:
            continue
        out.append((m["id"], (m.get("status") or {}).get("value", "?")))
    return out


def slug(model_id):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", model_id).strip("_")


def ask(server, model, prompt, opts):
    """-> (content, reasoning, finish_reason, usage, seconds, mode)"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": opts["temperature"],
        "max_tokens": opts["max_tokens"],
    }
    mode = "think=on"
    if opts["think"] == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
        mode = "think=off"
    if opts["reasoning_effort"]:
        payload["reasoning_effort"] = opts["reasoning_effort"]
        mode += ", effort=%s" % opts["reasoning_effort"]
    t0 = time.time()
    try:
        body = api(server, "/v1/chat/completions", payload, opts["timeout"])
    except ApiError as e:
        # a model that cannot load is the server's problem, not the template's
        if "chat_template_kwargs" not in payload or "failed to load" in e.detail:
            raise
        print("  (template rejected enable_thinking: %s — retrying with"
              " thinking left on)" % e.detail[:80])
        payload.pop("chat_template_kwargs")
        mode = "think=on (no switch)"
        body = api(server, "/v1/chat/completions", payload, opts["timeout"])
    took = time.time() - t0
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    return (msg.get("content") or "",
            msg.get("reasoning_content") or "",
            choice.get("finish_reason"),
            body.get("usage") or {},
            took, mode)


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


def warmup(server, model, timeout, attempts=3, pause=30):
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
                 "max_tokens": 1}, timeout)
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
    """One full sweep of the problems. -> (trouble, seconds_generating)"""
    tdir = os.path.join(outdir, "transcripts")
    os.makedirs(tdir, exist_ok=True)
    trouble = []
    elapsed = 0.0
    for problem in PROBLEMS:
        if opts["only"] and not selected(problem, opts["only"]):
            continue
        prompt_path = os.path.join(HERE, "problems", problem, "PROMPT.md")
        with open(prompt_path) as fh:
            prompt = fh.read()

        print("\n== %s ==" % problem)
        sys.stdout.flush()
        try:
            content, reasoning, finish, usage, took, mode = ask(
                opts["server"], model, prompt, opts)
        except (ApiError, urllib.error.URLError, OSError, ValueError) as e:
            print("  REQUEST FAILED: %s" % e)
            trouble.append("%s: request failed" % problem)
            continue

        with open(os.path.join(tdir, problem + ".txt"), "w") as fh:
            fh.write(content)
        if reasoning:
            with open(os.path.join(tdir, problem + ".reasoning.txt"), "w") as fh:
                fh.write(reasoning)
        with open(os.path.join(tdir, problem + ".meta.json"), "w") as fh:
            json.dump({"model": model, "finish_reason": finish, "mode": mode,
                       "temperature": opts["temperature"],
                       "max_tokens": opts["max_tokens"],
                       "usage": usage, "seconds": round(took, 1)}, fh, indent=2)

        elapsed += took
        ct = usage.get("completion_tokens", "?")
        print("  %.0fs, %s completion tokens, %s, finish=%s%s"
              % (took, ct, mode, finish,
                 ", %d chars of reasoning" % len(reasoning) if reasoning else ""))
        if looped(content, finish):
            print("  REPETITION LOOP — stopped producing new lines and cycled"
                  " until the %d token cap; not a size problem"
                  % opts["max_tokens"])
            trouble.append("%s: repetition loop" % problem)
        elif finish == "length":
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

    if trouble:
        print()
        print("Problems worth a look before trusting this score:")
        for t in trouble:
            print("  - %s" % t)
        print("Raw replies are under %s" % tdir)
    return trouble, elapsed


def run_model(model, opts):
    base = os.path.join(opts["out"], slug(model))
    if not opts["keep"] and os.path.isdir(base) and not opts["only"]:
        subprocess.call(["rm", "-rf", base])

    print("=" * 60)
    print(" Model:   %s" % model)
    print(" Server:  %s" % opts["server"])
    print(" Output:  %s" % base)
    print(" Decode:  temperature %s, max_tokens %d, thinking %s"
          % (opts["temperature"], opts["max_tokens"], opts["think"]))
    if opts["repeat"] > 1:
        print(" Repeats: %d passes (same request each time — these models are"
              " not reproducible at temperature 0)" % opts["repeat"])
    print("=" * 60)
    sys.stdout.flush()

    result = {"model": model, "load_seconds": None, "passes": []}

    if opts["warmup"]:
        secs, err = warmup(opts["server"], model, opts["timeout"])
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
        trouble, gen = run_pass(model, opts, outdir)
        wall = time.time() - t0
        entry = {"pass": n, "dir": outdir, "generate_seconds": round(gen, 1),
                 "wall_seconds": round(wall, 1), "trouble": trouble}
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
            "repeat": 1, "warmup": True}
    models = []
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
            for mid, status in list_models(opts["server"]):
                print("%-50s %s" % (mid, status))
            return 0
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

    if not models:
        print(__doc__.strip())
        return 2

    known = dict(list_models(opts["server"]))
    for m in models:
        if m not in known:
            sys.exit("run_http: %r is not on %s (try --list-models)"
                     % (m, opts["server"]))

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
    print(" SUMMARY — %d model(s), %d pass(es) each, temperature %s, thinking %s"
          % (len(results), opts["repeat"], opts["temperature"], opts["think"]))
    print("=" * 78)
    print(" %-42s %-18s %7s %8s" % ("model", "score", "load", "gen"))
    print(" " + "-" * 76)
    for r in results:
        scores = [p["score"] for p in r["passes"] if "score" in p]
        gen = sum(p["generate_seconds"] for p in r["passes"])
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
        print(" %-42s %-18s %7s %7.0fs" % (r["model"][:42], cell, load, gen))
    print(" " + "-" * 76)
    print(" total wall clock: %.0f min" % (wall / 60.0))
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
                                     "repeat", "reasoning_effort", "server")},
                       "results": results}, fh, indent=2)
        print(" full detail: %s" % path)
    except OSError as e:
        print(" (could not write summary json: %s)" % e)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
