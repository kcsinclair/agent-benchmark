#!/usr/bin/env python3
"""Run the benchmark as an agent task: the model writes files with tools.

Usage:
    run_agent.py [options] <model-id> [<model-id> ...]

The one-shot track (run_http.py) asks for an answer and lifts code blocks out of
the reply. This one hands the model a `write_file` tool and grades whatever it
actually writes. Same prompts, same graders, so the scores are directly
comparable — what changes is that the model has to *use a tool correctly* to
score at all, which is the thing that decides whether it can drive a coding
agent.

Deliberately no test-running tool. Letting a model run the graders would leak
the hidden edge cases and destroy the benchmark; letting it run arbitrary code
is a different (and riskier) experiment. So this measures tool discipline and
one-shot correctness together, not self-repair.

Options:
  -s, --server URL      llama.cpp server (default $BENCH_SERVER or leia), or
                        https://openrouter.ai/api for frontier models
      --key-file PATH   OpenRouter key ($OPENROUTER_API_KEY, then .env, then
                        this path)
      --provider NAME   pin the upstream provider and disable fallbacks
  -o, --only LIST       problems to run, e.g. -o 1,3
      --out DIR         output root (default results/<server>/agent)
  -m, --max-tokens N    per turn (default 8192)
      --max-turns N     tool-call rounds before giving up (default 12)
  -t, --timeout SECS    per request (default 1800)
      --temperature F   default 0
      --think on|off    default off, same reasoning as the one-shot track
      --reasoning-effort E  low|medium|high for models that take it
  -r, --repeat N        N passes per model, report median and spread
  -k, --keep            keep existing output instead of clearing
      --no-warmup       skip the load request before timing
      --no-probe        skip the one-token request that settles the decode
                        before the run (see run_http.probe)
  -h, --help            this message

Beyond the score, each problem records how the model behaved: turns used, tool
calls made, malformed calls, files written under names nobody asked for, and
whether it ignored the tools and answered in prose instead. A model that writes
perfect code into the chat window scores zero here, which is the correct result
for an agent that cannot operate a filesystem.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_submission as ex          # noqa: E402
from run_http import (ApiError, decorate, send, prepare, price_per_mtok,  # noqa: E402
                      slug, warmup, probe, grade, selected, default_out,
                      DEFAULT_SERVER, DEFAULT_KEY_FILE, HERE, REPO)

PROBLEMS = sorted(ex.PROBLEMS)

INSTRUCTION = """

---
You are working as an agent. Use the `write_file` tool to create the deliverable
file(s) named in the task above, exactly as named. The files you write are the
only thing that will be graded — code printed in your reply is ignored. Write
each file once, then stop.
"""

TOOLS = [
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write text to a file in the working directory. "
                       "Overwrites an existing file of the same name.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string",
                         "description": "Filename, e.g. parse_duration.py"},
                "contents": {"type": "string",
                             "description": "Full file contents"},
            },
            "required": ["path", "contents"]}}},
    {"type": "function", "function": {
        "name": "list_files",
        "description": "List files already written in the working directory.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read back a file you have written.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]}}},
]


# Some models emit tool calls in their own syntax and llama.cpp hands the text
# through as plain content instead of parsing it into tool_calls. Qwen3-Coder
# does exactly this. Ignoring it would score the server, not the model — but a
# native-format call is NOT the same as a clean OpenAI one, because an
# off-the-shelf agent would not see it either, so the two are counted apart.
# OpenRouter normalises tool calls across vendors, so this should stay at zero
# there — if it does not, that is a finding, not something to quietly paper over.
NATIVE_FN = re.compile(r"<function=([\w.-]+)>(.*?)(?:</function>|\Z)", re.S)
NATIVE_ARG = re.compile(r"<parameter=([\w.-]+)>\n?(.*?)\n?(?:</parameter>|\Z)", re.S)
TOOL_CALL_JSON = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.S)


def parse_native_calls(content):
    """-> list of OpenAI-shaped tool calls recovered from raw content."""
    calls = []
    for n, m in enumerate(NATIVE_FN.finditer(content or "")):
        args = {k: v for k, v in NATIVE_ARG.findall(m.group(2))}
        calls.append({"id": "native_%d" % n, "type": "function",
                      "function": {"name": m.group(1),
                                   "arguments": json.dumps(args)}})
    for n, m in enumerate(TOOL_CALL_JSON.finditer(content or "")):
        try:
            obj = json.loads(m.group(1))
        except ValueError:
            continue
        args = obj.get("arguments", obj.get("parameters", {}))
        calls.append({"id": "native_j%d" % n, "type": "function",
                      "function": {"name": obj.get("name", ""),
                                   "arguments": args if isinstance(args, str)
                                   else json.dumps(args)}})
    return calls


def safe_path(outdir, path):
    """Keep the model inside its own directory. -> absolute path or None."""
    if not path or os.path.isabs(path):
        return None
    full = os.path.normpath(os.path.join(outdir, path))
    if not full.startswith(os.path.realpath(outdir) + os.sep) and \
       not full.startswith(outdir + os.sep):
        return None
    return full


def dispatch(call, outdir, stats):
    """Run one tool call. -> string result for the model."""
    name = (call.get("function") or {}).get("name")
    raw = (call.get("function") or {}).get("arguments") or "{}"
    try:
        args = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(args, dict):
            raise ValueError("arguments must be a JSON object")
    except (ValueError, TypeError) as e:
        stats["bad_calls"] += 1
        return "ERROR: could not parse arguments as JSON (%s)" % e

    if name == "write_file":
        path, contents = args.get("path"), args.get("contents")
        if not isinstance(path, str) or not isinstance(contents, str):
            stats["bad_calls"] += 1
            return "ERROR: write_file needs string 'path' and 'contents'"
        full = safe_path(outdir, path)
        if not full:
            stats["bad_calls"] += 1
            stats["rejected_paths"].append(path)
            return "ERROR: path must be a plain filename inside the working directory"
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write(contents if contents.endswith("\n") else contents + "\n")
        stats["files"].append(path)
        return "wrote %s (%d bytes)" % (path, len(contents))

    if name == "list_files":
        got = sorted(os.listdir(outdir)) if os.path.isdir(outdir) else []
        return json.dumps(got)

    if name == "read_file":
        full = safe_path(outdir, args.get("path") or "")
        if not full or not os.path.isfile(full):
            stats["bad_calls"] += 1
            return "ERROR: no such file"
        with open(full) as fh:
            return fh.read()[:8000]

    stats["bad_calls"] += 1
    stats["unknown_tools"].append(name)
    return "ERROR: no such tool %r" % name


def agent_turn(server, model, messages, opts):
    payload = {"model": model, "messages": messages, "tools": TOOLS,
               "max_tokens": opts["max_tokens"]}
    # decode settings are per model and per back end — see run_http.decorate
    decorate(payload, model, opts)
    body, _ = send(server, payload, opts)
    choice = (body.get("choices") or [{}])[0]
    return (choice.get("message") or {}, choice.get("finish_reason"),
            body.get("usage") or {}, body.get("provider"))


def run_problem(model, problem, opts, outdir):
    with open(os.path.join(HERE, "problems", problem, "PROMPT.md")) as fh:
        prompt = fh.read() + INSTRUCTION
    os.makedirs(outdir, exist_ok=True)

    stats = {"problem": problem, "turns": 0, "tool_calls": 0, "bad_calls": 0,
             "files": [], "rejected_paths": [], "unknown_tools": [],
             "tokens": 0, "stop": None, "prose_only": False,
             "native_calls": 0, "cost": 0.0, "provider": None,
             "truncated_turns": 0, "empty_replies": 0}
    messages = [{"role": "user", "content": prompt}]
    t0 = time.time()

    for turn in range(opts["max_turns"]):
        stats["turns"] = turn + 1
        try:
            msg, finish, usage, provider = agent_turn(
                opts["server"], model, messages, opts)
        except (ApiError, urllib.error.URLError, OSError, ValueError) as e:
            stats["stop"] = "request failed: %s" % e
            break
        stats["tokens"] += usage.get("completion_tokens", 0) or 0
        stats["cost"] += float(usage.get("cost") or 0)
        stats["provider"] = provider or stats["provider"]
        if finish == "length":
            stats["truncated_turns"] += 1
        # a turn that bills tokens and returns neither text nor a tool call is
        # the provider failing, not the model: Novita did exactly this for
        # qwen3-coder-30b (791 tokens, content None) and it read as a model
        # that could not answer. The agent track keeps no transcript, so this
        # counter is the only trace left afterwards.
        if not (msg.get("content") or "").strip() and not msg.get("tool_calls"):
            stats["empty_replies"] += 1
        content = msg.get("content") or ""
        calls = msg.get("tool_calls") or []
        native = []
        if not calls:
            native = parse_native_calls(content)
            if native:
                stats["native_calls"] += len(native)
                calls = native
        messages.append({"role": "assistant", "content": content,
                         **({"tool_calls": calls} if calls and not native else {})})
        if not calls:
            # no tool call: either it is finished, or it answered in chat
            stats["stop"] = "stopped after %d turn(s)" % stats["turns"]
            if not stats["files"]:
                stats["prose_only"] = "```" in content
            break
        for call in calls:
            stats["tool_calls"] += 1
            result = dispatch(call, outdir, stats)
            if native:
                # no tool_call_id exists server-side; feed the result back as
                # a user turn so the conversation stays valid
                messages.append({"role": "user",
                                 "content": "tool result: %s" % result})
            else:
                messages.append({"role": "tool",
                                 "tool_call_id": call.get("id", ""),
                                 "content": result})
    else:
        stats["stop"] = "hit the %d turn limit" % opts["max_turns"]

    stats["seconds"] = round(time.time() - t0, 1)
    wanted = ex.PROBLEMS[problem]["files"]
    stats["missing"] = [f for f in wanted if not os.path.isfile(
        os.path.join(outdir, f))]
    stats["extra"] = sorted(set(stats["files"]) - set(wanted))

    flags = []
    if stats["bad_calls"]:
        flags.append("%d malformed call(s)" % stats["bad_calls"])
    if stats["extra"]:
        flags.append("wrote unrequested: %s" % ", ".join(stats["extra"][:3]))
    if stats["missing"]:
        flags.append("MISSING %s" % ", ".join(stats["missing"]))
    if stats["native_calls"]:
        flags.append("%d native-format call(s) — llama.cpp did not parse these"
                     % stats["native_calls"])
    if stats["prose_only"]:
        flags.append("ANSWERED IN PROSE — never called a tool")
    # a turn that hits the cap before emitting a tool call is a budget artefact,
    # not tool indiscipline. It bites hardest when an endpoint mandates
    # reasoning: the chain of thought eats a max_tokens tuned for models that
    # answer directly, and the model never gets to call write_file. Scoring that
    # as 0 says the model cannot drive an agent, which is not what was measured.
    if stats["truncated_turns"]:
        flags.append("TRUNCATED on %d turn(s) at the %d-token cap — raise"
                     " --max-tokens before reading this score"
                     % (stats["truncated_turns"], opts["max_tokens"]))
    if stats["empty_replies"]:
        flags.append("EMPTY reply on %d turn(s) — billed tokens, no content and"
                     " no tool call; suspect the provider, not the model"
                     % stats["empty_replies"])
    print("  %-26s %2d turn(s) %2d call(s) %5.0fs %s %s"
          % (problem[:26], stats["turns"], stats["tool_calls"],
             stats["seconds"],
             "$%.4f" % stats["cost"] if stats["cost"] else "",
             "; ".join(flags) or "clean"))
    sys.stdout.flush()
    return stats


def run_model(model, opts):
    base = os.path.join(opts["out"], slug(model))
    if not opts["keep"] and os.path.isdir(base) and not opts["only"]:
        subprocess.call(["rm", "-rf", base])

    # settle the decode first, so the header cannot claim a setting the
    # requests do not carry (a hosted endpoint has nothing to load)
    fatal = None
    if opts["openrouter"] and opts["probe"]:
        _, fatal = probe(model, opts)

    # derived from a real payload for the same reason
    sample = {"max_tokens": opts["max_tokens"]}
    _, decode = decorate(sample, model, opts)
    temp = ("temperature %s" % decode["temperature"]
            if decode.get("temperature") is not None
            else "temperature OMITTED (%s)" % decode["temperature_note"])

    print("=" * 60)
    print(" Model:   %s  (agent / tool-use track)" % model)
    if opts["openrouter"]:
        rec = opts["models"].get(model) or {}
        tools_ok = "tools" in (rec.get("supported_parameters") or [])
        print(" Server:  %s  (OpenRouter, %s)%s"
              % (opts["server"],
                 "provider pinned to %s" % opts["provider"] if opts["provider"]
                 else "fallbacks off",
                 "" if tools_ok else
                 "\n WARNING: this model does not advertise tool support"))
        print(" Price:   %s per Mtok in/out" % (price_per_mtok(rec) or "unknown"))
    print(" Output:  %s" % base)
    print(" Limits:  %d turns, %d tokens per turn, %s, %s"
          % (opts["max_turns"], opts["max_tokens"], temp, decode["thinking"]))
    print("=" * 60)
    sys.stdout.flush()

    result = {"model": model, "track": "agent", "load_seconds": None, "passes": []}
    if fatal is not None:
        print(" NOT RUN: %s\n No request was sent and nothing was written.\n"
              % fatal)
        result["error"] = str(fatal)
        result["unrun"] = True
        return result
    if opts["warmup"] and not opts["openrouter"]:
        secs, err = warmup(opts["server"], model, opts["timeout"], opts["key"])
        result["load_seconds"] = round(secs, 1)
        if err:
            print(" load FAILED after %.0fs: %s\n skipping this model\n" % (secs, err))
            result["error"] = err
            return result
        print(" model resident after %.0fs" % secs)
        if opts["probe"]:
            settled, _ = probe(model, opts)
            if settled != decode["thinking"]:
                print(" decode revised by probe: %s" % settled)
        print()

    for n in range(1, opts["repeat"] + 1):
        outdir = base if opts["repeat"] == 1 else os.path.join(base, "pass%d" % n)
        if opts["repeat"] > 1:
            print("\n pass %d of %d" % (n, opts["repeat"]))
        stats = []
        for problem in PROBLEMS:
            if opts["only"] and not selected(problem, opts["only"]):
                continue
            stats.append(run_problem(model, problem, opts,
                                     os.path.join(outdir, problem)))
        entry = {"pass": n, "dir": outdir, "problems": stats,
                 "seconds": round(sum(s["seconds"] for s in stats), 1)}
        spent = sum(s["cost"] for s in stats)
        if spent:
            entry["cost_usd"] = round(spent, 4)
        print()
        scored = grade(outdir, "%s agent pass %d" % (model, n))
        if scored:
            entry["score"], entry["max"] = scored
        result["passes"].append(entry)
        sys.stdout.flush()
    return result


def summarise(results, wall, opts):
    print()
    print("=" * 84)
    print(" AGENT TRACK — %d model(s), %d pass(es), %d-turn limit"
          % (len(results), opts["repeat"], opts["max_turns"]))
    print("=" * 84)
    priced = any("cost_usd" in p for r in results for p in r["passes"])
    print(" %-40s %-16s %6s %7s %6s %s%s"
          % ("model", "score", "turns", "calls", "bad",
             "cost      " if priced else "", "notes"))
    print(" " + "-" * 82)
    for r in results:
        if r.get("error"):
            print(" %-40s %s" % (r["model"][:40],
                  "NOT RUN (see above)" if r.get("unrun") else "FAILED TO LOAD"))
            continue
        allp = [p for pas in r["passes"] for p in pas["problems"]]
        scores = [p["score"] for p in r["passes"] if "score" in p]
        mx = r["passes"][0].get("max", 68)
        cell = ("%d/%d" % (sorted(scores)[len(scores) // 2], mx)
                if scores else "not graded")
        if len(scores) > 1:
            cell += " (%s)" % "-".join(str(s) for s in sorted(scores))
        notes = []
        if any(p["native_calls"] for p in allp):
            notes.append("native tool format")
        if any(p["prose_only"] for p in allp):
            notes.append("%d prose-only" % sum(1 for p in allp if p["prose_only"]))
        if any(p["extra"] for p in allp):
            notes.append("stray files")
        if any("limit" in (p["stop"] or "") for p in allp):
            notes.append("hit turn limit")
        trunc = sum(p.get("truncated_turns", 0) for p in allp)
        if trunc:
            notes.append("TRUNCATED %dx — score not trustworthy" % trunc)
        blank = sum(p.get("empty_replies", 0) for p in allp)
        if blank:
            notes.append("EMPTY %dx — suspect the provider" % blank)
        # differing providers can mean differing quantisation, which this
        # benchmark scores as a different contestant, not the same one
        served = {p["provider"] for p in allp if p["provider"]}
        if len(served) > 1:
            notes.append("MIXED PROVIDERS: %s — pin one" % ", ".join(sorted(served)))
        elif served:
            notes.append("via %s" % served.pop())
        spent = sum(p.get("cost_usd", 0) for p in r["passes"])
        print(" %-40s %-16s %6.1f %7.1f %6d %s%s"
              % (r["model"][:40], cell,
                 sum(p["turns"] for p in allp) / float(len(allp)),
                 sum(p["tool_calls"] for p in allp) / float(len(allp)),
                 sum(p["bad_calls"] for p in allp),
                 "$%-9.4f" % spent if priced else "", ", ".join(notes)))
    print(" " + "-" * 82)
    print(" turns/calls are per problem, averaged. total wall clock: %.0f min"
          % (wall / 60.0))
    if priced:
        print(" total cost: $%.4f (billed, not estimated). An agent run costs"
              " more than a one-shot"
              % sum(p.get("cost_usd", 0) for r in results for p in r["passes"]))
        print(" because every turn resends the whole conversation.")
    # never overwritten, so one written for a run that measured nothing would
    # survive every later run and read as a result
    if not any(r.get("passes") for r in results):
        print(" no summary written: nothing was measured")
        return

    path = os.path.join(opts["out"], "agent-summary-%s.json"
                        % time.strftime("%Y%m%d-%H%M%S"))
    try:
        os.makedirs(opts["out"], exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"wall_seconds": round(wall, 1), "track": "agent",
                       "settings": {k: opts[k] for k in
                                    ("temperature", "max_tokens", "max_turns",
                                     "think", "repeat", "server", "provider")},
                       "results": results}, fh, indent=2)
        print(" full detail: %s" % path)
    except OSError as e:
        print(" (could not write summary json: %s)" % e)


def main(argv):
    opts = {"server": DEFAULT_SERVER, "only": "", "out": None,
            "max_tokens": 8192, "max_turns": 12, "timeout": 1800,
            "temperature": 0.0, "think": "off", "reasoning_effort": "",
            "repeat": 1, "keep": False, "warmup": True, "probe": True,
            "think_refused": {},
            "key_file": DEFAULT_KEY_FILE, "provider": "", "key": None,
            "openrouter": False, "models": {}}
    models, i = [], 0
    while i < len(argv):
        a = argv[i]
        def val():
            if i + 1 >= len(argv):
                sys.exit("run_agent: %s needs an argument" % a)
            return argv[i + 1]
        if a in ("-h", "--help"):       print(__doc__.strip()); return 0
        elif a in ("-s", "--server"):   opts["server"] = val(); i += 2
        elif a == "--key-file":         opts["key_file"] = val(); i += 2
        elif a == "--provider":         opts["provider"] = val(); i += 2
        elif a in ("-o", "--only"):     opts["only"] = val(); i += 2
        elif a == "--out":              opts["out"] = val(); i += 2
        elif a in ("-m", "--max-tokens"): opts["max_tokens"] = int(val()); i += 2
        elif a == "--max-turns":        opts["max_turns"] = int(val()); i += 2
        elif a in ("-t", "--timeout"):  opts["timeout"] = float(val()); i += 2
        elif a == "--temperature":      opts["temperature"] = float(val()); i += 2
        elif a == "--think":            opts["think"] = val(); i += 2
        elif a == "--reasoning-effort": opts["reasoning_effort"] = val(); i += 2
        elif a in ("-r", "--repeat"):   opts["repeat"] = int(val()); i += 2
        elif a in ("-k", "--keep"):     opts["keep"] = True; i += 1
        elif a == "--no-warmup":        opts["warmup"] = False; i += 1
        elif a == "--no-probe":         opts["probe"] = False; i += 1
        elif a.startswith("-"):         sys.exit("run_agent: unknown option %r" % a)
        else:                           models.append(a); i += 1

    if opts["out"] is None:
        opts["out"] = default_out(opts["server"], "agent")

    if not models:
        print(__doc__.strip())
        return 2
    source = prepare(opts)
    for m in models:
        if m not in opts["models"]:
            sys.exit("run_agent: %r is not on %s" % (m, opts["server"]))
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
