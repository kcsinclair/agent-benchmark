#!/usr/bin/env python3
"""Reasoning track: general-purpose ability, for judging models as agents.

Usage:
    run_reasoning.py [options] <model-id> [<model-id> ...]

Six categories, all graded mechanically — no LLM judge anywhere:

  state       apply N operations to a starting state, report the result
  constraint  small scheduling puzzles with exactly one valid arrangement
  compliance  strict output-format instructions, checked by regex
  abstention  half answerable from the text, half not; UNKNOWN is the right
              answer to the latter, so hallucinating and over-abstaining are
              punished equally
  trap        the pattern-matched answer is wrong for a specific reason
  retrieval   two facts buried far apart in a long log, combined to answer

Every category except `trap` is generated from a seed and solved in Python, so
items cannot be memorised from training data, there are as many as you want, and
the answer key never exists as text a model could have seen. `trap` is
hand-authored because genuine surprise does not generate well; keep it as
private as the coding graders.

Scores from here are NOT comparable with the 68-check coding benchmark. This
measures whether a model can be trusted to run an agent loop, not whether it can
write a parser.

Options:
  -s, --server URL      llama.cpp server (default $BENCH_SERVER or leia), or
                        https://openrouter.ai/api for frontier models
      --key-file PATH   OpenRouter key ($OPENROUTER_API_KEY, then .env, then
                        this path)
      --provider NAME   pin the upstream provider and disable fallbacks
  -c, --categories LIST which to run (default all), e.g. -c trap,state
  -n, --count N         items per category (overrides per-category defaults)
      --seed N          item seed (default 1; change it for a fresh set)
      --out DIR         output root (default results/<server>/reasoning)
  -m, --max-tokens N    per answer (default 2048)
  -t, --timeout SECS    per request (default 900)
      --temperature F   default 0
      --think on|off    default off, same reasoning as the coding tracks
      --reasoning-effort E   low|medium|high for models that take it
  -r, --repeat N        passes per model; report median and spread
      --no-warmup       skip the load request before timing
      --no-probe        skip the one-token request that settles the decode
                        before the run (see run_http.probe)
      --show-failures N print N wrong answers per category (default 2)
  -h, --help            this message
"""
import json
import os
import sys
import time
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "benchmark"))

import categories as cat                                        # noqa: E402
from run_http import (ApiError, build_payload, send, prepare,  # noqa: E402
                      price_per_mtok, slug, warmup, probe, server_label,
                      DEFAULT_SERVER, DEFAULT_KEY_FILE)


def ask(server, model, prompt, opts):
    """-> (content, finish_reason, completion_tokens, seconds, dollars)"""
    payload, _, _ = build_payload(model, prompt, opts)
    t0 = time.time()
    body, _ = send(server, payload, opts)
    choice = (body.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    usage = body.get("usage") or {}
    return (msg.get("content") or "", choice.get("finish_reason"),
            usage.get("completion_tokens", 0), time.time() - t0,
            float(usage.get("cost") or 0))


def run_pass(model, opts, outdir):
    os.makedirs(outdir, exist_ok=True)
    results, totals = [], {}
    for name in opts["categories"]:
        spec = cat.CATEGORIES[name]
        count = opts["count"] or spec["n"]
        items = cat.build(name, count, opts["seed"])
        right, elapsed, wrong, spent, failed = 0, 0.0, [], 0.0, 0
        print("\n== %s (%d items) ==" % (spec["label"], count))
        sys.stdout.flush()
        for i, (prompt, answer, check) in enumerate(items):
            try:
                reply, finish, tokens, secs, cost = ask(opts["server"], model,
                                                        prompt, opts)
            except (ApiError, urllib.error.URLError, OSError, ValueError) as e:
                # counted apart from a wrong answer: the model never saw this
                # item, so folding it into the score would deflate the result
                # for an infrastructure reason and read as a worse model
                print("  item %d: REQUEST FAILED (%s)" % (i + 1, e))
                failed += 1
                wrong.append({"item": i + 1, "expected": answer,
                              "reply": "request failed: %s" % e})
                continue
            elapsed += secs
            spent += cost
            ok = False
            try:
                ok = bool(check(reply, answer))
            except Exception:
                ok = False
            if ok:
                right += 1
            else:
                wrong.append({"item": i + 1, "expected": answer,
                              "reply": (reply or "").strip()[-400:],
                              "finish": finish})
            results.append({"category": name, "item": i + 1, "ok": ok,
                            "expected": answer, "seconds": round(secs, 1),
                            "tokens": tokens, "finish": finish,
                            "reply": (reply or "").strip()[-2000:]})
        totals[name] = {"right": right, "count": count,
                        "seconds": round(elapsed, 1), "failed": failed}
        if spent:
            totals[name]["cost_usd"] = round(spent, 4)
        pct = 100.0 * right / count if count else 0
        print("  %d/%d correct (%.0f%%), %.0fs%s"
              % (right, count, pct, elapsed, ", $%.4f" % spent if spent else ""))
        if failed >= count:
            print("  NO items in this category got a reply — this category"
                  " measured nothing. Do not read the 0 as a model result.")
        elif failed:
            print("  %d item(s) never got a reply — scored wrong, but that is"
                  " the transport failing, not the model. Effective score"
                  " %d/%d." % (failed, right, count - failed))
        for w in wrong[:opts["show_failures"]]:
            print("    item %d wanted %r, got: %s"
                  % (w["item"], w["expected"],
                     (w["reply"] or "").replace("\n", " ")[:110]))
        sys.stdout.flush()

    with open(os.path.join(outdir, "items.json"), "w") as fh:
        json.dump({"model": model, "seed": opts["seed"], "results": results},
                  fh, indent=2)
    return totals


def run_model(model, opts):
    base = os.path.join(opts["out"], slug(model))
    result = {"model": model, "load_seconds": None, "passes": []}

    # settled before anything is claimed or written; see run_http.probe
    fatal = None
    if opts["openrouter"] and opts["probe"]:
        _, fatal = probe(model, opts)
    if fatal is not None:
        print("=" * 62)
        print(" Model:   %s  (reasoning track)" % model)
        print(" NOT RUN: %s" % fatal)
        print(" No request was sent and nothing was written.")
        print("=" * 62)
        print()
        sys.stdout.flush()
        result["error"] = str(fatal)
        result["unrun"] = True
        return result

    print("=" * 62)
    print(" Model:   %s  (reasoning track)" % model)
    print(" Items:   %s" % ", ".join(opts["categories"]))
    if not cat.TRAPS_AVAILABLE:
        print(" Note:    no trap bank (private harness absent) — scores are out"
              " of 88, not 102, and are not comparable with published runs")
    # built from a real payload: the header must not claim a decode setting the
    # requests do not carry
    _, _, decode = build_payload(model, "", opts)
    temp = ("temperature %s" % decode["temperature"]
            if decode.get("temperature") is not None
            else "temperature OMITTED (%s)" % decode["temperature_note"])
    if opts["openrouter"]:
        rec = opts["models"].get(model) or {}
        print(" Server:  %s  (OpenRouter, %s)"
              % (opts["server"],
                 "provider pinned to %s" % opts["provider"] if opts["provider"]
                 else "fallbacks off"))
        print(" Price:   %s per Mtok in/out" % (price_per_mtok(rec) or "unknown"))
    print(" Decode:  %s, %s, seed %d" % (temp, decode["thinking"], opts["seed"]))
    print("=" * 62)
    sys.stdout.flush()


    if opts["warmup"] and not opts["openrouter"]:
        secs, err = warmup(opts["server"], model, opts["timeout"], opts["key"])
        result["load_seconds"] = round(secs, 1)
        if err:
            print(" load FAILED after %.0fs: %s\n skipping\n" % (secs, err))
            result["error"] = err
            return result
        print(" model resident after %.0fs" % secs)
        if opts["probe"]:
            settled, _ = probe(model, opts)
            if settled != decode["thinking"]:
                print(" decode revised by probe: %s" % settled)

    for n in range(1, opts["repeat"] + 1):
        outdir = base if opts["repeat"] == 1 else os.path.join(base, "pass%d" % n)
        if opts["repeat"] > 1:
            print("\n--- pass %d of %d ---" % (n, opts["repeat"]))
        totals = run_pass(model, opts, outdir)
        right = sum(t["right"] for t in totals.values())
        count = sum(t["count"] for t in totals.values())
        print("\n  pass total: %d/%d (%.0f%%)"
              % (right, count, 100.0 * right / count if count else 0))
        spent = sum(t.get("cost_usd", 0) for t in totals.values())
        if spent:
            print("  pass cost: $%.4f" % spent)
        nofail = sum(t.get("failed", 0) for t in totals.values())
        if nofail:
            print("  WARNING: %d of %d items never got a reply. Quote %d/%d,"
                  " not %d/%d." % (nofail, count, right, count - nofail,
                                   right, count))
        result["passes"].append({"pass": n, "dir": outdir, "totals": totals,
                                 "right": right, "count": count,
                                 **({"cost_usd": round(spent, 4)} if spent else {})})
        sys.stdout.flush()
    return result


def summarise(results, wall, opts):
    cats = opts["categories"]
    print()
    print("=" * (30 + 12 * len(cats)))
    print(" REASONING TRACK — %d model(s), %d pass(es), seed %d"
          % (len(results), opts["repeat"], opts["seed"]))
    print("=" * (30 + 12 * len(cats)))
    head = " %-34s %9s " % ("model", "total") + " ".join(
        "%10s" % c[:10] for c in cats)
    print(head)
    print(" " + "-" * (len(head) - 1))
    for r in results:
        if r.get("error"):
            print(" %-34s %s" % (r["model"][:34],
                  "NOT RUN (see above)" if r.get("unrun") else "FAILED TO LOAD"))
            continue
        scores = [p["right"] for p in r["passes"]]
        count = r["passes"][0]["count"]
        med = sorted(scores)[len(scores) // 2]
        cell = "%d/%d" % (med, count)
        if len(scores) > 1:
            cell += "*"
        row = " %-34s %9s " % (r["model"][:34], cell)
        for c in cats:
            got = [p["totals"].get(c, {}).get("right", 0) for p in r["passes"]]
            tot = r["passes"][0]["totals"].get(c, {}).get("count", 0)
            row += "%10s " % ("%d/%d" % (sorted(got)[len(got) // 2], tot))
        print(row)
    print(" " + "-" * (len(head) - 1))
    if opts["repeat"] > 1 and any(r.get("passes") for r in results):
        print(" * median of %d passes" % opts["repeat"])
    print(" wall clock: %.0f min" % (wall / 60.0))
    spent = sum(p.get("cost_usd", 0) for r in results for p in r["passes"])
    if spent:
        print(" total cost: $%.4f (billed, not estimated)" % spent)

    # never overwritten, so one written for a run that measured nothing would
    # survive every later run and read as a result
    if not any(r.get("passes") for r in results):
        print(" no summary written: nothing was measured")
        return

    path = os.path.join(opts["out"], "reasoning-summary-%s.json"
                        % time.strftime("%Y%m%d-%H%M%S"))
    try:
        os.makedirs(opts["out"], exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"wall_seconds": round(wall, 1), "track": "reasoning",
                       "settings": {k: opts[k] for k in
                                    ("temperature", "max_tokens", "think",
                                     "repeat", "seed", "server", "categories",
                                     "provider")},
                       "results": results}, fh, indent=2)
        print(" full detail: %s" % path)
    except OSError as e:
        print(" (could not write summary: %s)" % e)


def main(argv):
    opts = {"server": DEFAULT_SERVER, "categories": list(cat.CATEGORIES),
            "count": 0, "seed": 1, "out": None, "max_tokens": 2048,
            "timeout": 900, "temperature": 0.0, "think": "off",
            "reasoning_effort": "", "repeat": 1, "warmup": True, "probe": True,
            "think_refused": {},
            "show_failures": 2, "key_file": DEFAULT_KEY_FILE, "provider": "",
            "key": None, "openrouter": False, "models": {}}
    models, i = [], 0
    while i < len(argv):
        a = argv[i]
        def val():
            if i + 1 >= len(argv):
                sys.exit("run_reasoning: %s needs an argument" % a)
            return argv[i + 1]
        if a in ("-h", "--help"):        print(__doc__.strip()); return 0
        elif a in ("-s", "--server"):    opts["server"] = val(); i += 2
        elif a == "--key-file":          opts["key_file"] = val(); i += 2
        elif a == "--provider":          opts["provider"] = val(); i += 2
        elif a in ("-c", "--categories"):
            opts["categories"] = [x for x in val().replace(" ", "").split(",") if x]
            i += 2
        elif a in ("-n", "--count"):     opts["count"] = int(val()); i += 2
        elif a == "--seed":              opts["seed"] = int(val()); i += 2
        elif a == "--out":               opts["out"] = val(); i += 2
        elif a in ("-m", "--max-tokens"): opts["max_tokens"] = int(val()); i += 2
        elif a in ("-t", "--timeout"):   opts["timeout"] = float(val()); i += 2
        elif a == "--temperature":       opts["temperature"] = float(val()); i += 2
        elif a == "--think":             opts["think"] = val(); i += 2
        elif a == "--reasoning-effort":  opts["reasoning_effort"] = val(); i += 2
        elif a in ("-r", "--repeat"):    opts["repeat"] = int(val()); i += 2
        elif a == "--no-warmup":         opts["warmup"] = False; i += 1
        elif a == "--no-probe":          opts["probe"] = False; i += 1
        elif a == "--show-failures":     opts["show_failures"] = int(val()); i += 2
        elif a.startswith("-"):          sys.exit("run_reasoning: unknown option %r" % a)
        else:                            models.append(a); i += 1

    for c in opts["categories"]:
        if c not in cat.CATEGORIES:
            if c == "trap" and not cat.TRAPS_AVAILABLE:
                sys.exit("run_reasoning: the trap category is hand-authored and "
                         "lives in the private harness submodule, which is not "
                         "checked out.\n  git submodule update --init   (or set "
                         "BENCH_HARNESS)\nThe other categories run without it.")
            sys.exit("run_reasoning: unknown category %r (have: %s)"
                     % (c, ", ".join(cat.CATEGORIES)))
    if opts["out"] is None:
        opts["out"] = os.path.join(REPO, "results",
                                   server_label(opts["server"]), "reasoning")
    if not models:
        print(__doc__.strip())
        return 2
    source = prepare(opts)
    for m in models:
        if m not in opts["models"]:
            sys.exit("run_reasoning: %r is not on %s" % (m, opts["server"]))
    if source:
        print("Key: %s" % source)

    started = time.time()
    results = [run_model(m, opts) for m in models]
    summarise(results, time.time() - started, opts)
    # nothing was ever asked: a configuration error, not a result — exit
    # non-zero so a caller chaining tracks stops instead of repeating it
    return 1 if results and all(r.get("unrun") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
