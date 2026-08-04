#!/usr/bin/env python3
"""Join llama-bench speed numbers to the accuracy scores.

Usage:
    collate_bench.py [results/<server>/speed] [-o out.md]

Reads the llama-bench JSON written by run_llama_bench.sh, plus the newest
summary-*.json (one-shot track) and agent-summary-*.json (tool-use track), and
prints one table: how fast each model is, and how well it scored.

Speed alone ranks the small models first and quality alone ranks the big ones
first; the point of the join is that neither is the answer on its own. The
depth columns matter most for agent work — a model that generates quickly at
depth 0 and collapses at 16k context is slow where an agent actually lives.
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def load_bench(d):
    """-> {label: {"pp": {depth: ts}, "tg": {depth: ts}, "size": bytes}}"""
    out = {}
    for path in sorted(glob.glob(os.path.join(d, "*.json"))):
        label = os.path.basename(path)[:-5]
        try:
            with open(path) as fh:
                rows = json.load(fh)
        except (ValueError, OSError):
            continue
        if not isinstance(rows, list) or not rows:
            continue
        entry = {"pp": {}, "tg": {}, "size": rows[0].get("model_size"),
                 "params": rows[0].get("model_n_params")}
        for r in rows:
            depth = r.get("n_depth", 0)
            if r.get("n_prompt"):
                entry["pp"][depth] = r.get("avg_ts")
            elif r.get("n_gen"):
                entry["tg"][depth] = r.get("avg_ts")
        out[label] = entry
    return out


def merged(pattern):
    """Merge every summary, newest last so a re-run supersedes an older score.

    Taking only the newest file loses models: a single-model retry writes its
    own summary, which would then be the only row that matches.
    """
    out = {"results": []}
    by_model = {}
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (ValueError, OSError):
            continue
        for r in data.get("results", []):
            if any("score" in p for p in r.get("passes", [])):
                by_model[r["model"]] = r
    out["results"] = list(by_model.values())
    return out


def score_map(summary):
    """-> {model_id: (median, max, passes)}"""
    out = {}
    for r in (summary or {}).get("results", []):
        scores = [p["score"] for p in r.get("passes", []) if "score" in p]
        if not scores:
            continue
        mx = r["passes"][0].get("max", 68)
        out[r["model"]] = (sorted(scores)[len(scores) // 2], mx, sorted(scores))
    return out


def match(label, model_ids):
    """llama-bench labels are short; server ids are long. Match on the stem."""
    key = re.sub(r"[^a-z0-9]", "", label.lower())
    best = None
    for mid in model_ids:
        norm = re.sub(r"[^a-z0-9]", "", mid.lower())
        if key in norm or norm.startswith(key[:12]):
            if best is None or len(norm) < len(best[1]):
                best = (mid, norm)
    return best[0] if best else None


def fmt(v, unit=""):
    return "-" if v is None else "%.0f%s" % (v, unit)


def main(argv):
    d = argv[0] if argv and not argv[0].startswith("-") else None
    if d is None:
        found = sorted(glob.glob(os.path.join(REPO, "results", "*", "speed")))
        d = found[0] if found else os.path.join(REPO, "bench-results")
    if not os.path.isdir(d):
        sys.exit("collate_bench: no such directory %s" % d)
    bench = load_bench(d)
    if not bench:
        sys.exit("collate_bench: no llama-bench json found in %s" % d)

    # summaries live in the sibling track directories of results/<server>/
    server_dir = os.path.dirname(os.path.abspath(d))
    oneshot = score_map(merged(os.path.join(server_dir, "oneshot",
                                            "summary-*.json")))
    agent = score_map(merged(os.path.join(server_dir, "agent",
                                          "agent-summary-*.json")))
    if not oneshot:   # pre-restructure layout
        oneshot = score_map(merged(os.path.join(REPO, "runs", "summary-*.json")))
        agent = score_map(merged(os.path.join(REPO, "runs-agent",
                                              "agent-summary-*.json")))

    controls = {k: v for k, v in bench.items() if k.startswith("control-")}
    models = {k: v for k, v in bench.items() if not k.startswith("control-")}
    depths = sorted({dep for m in models.values() for dep in m["tg"]})

    lines = []
    head = ["model", "size", "pp512"] + ["tg@%s" % (dep or "0") for dep in depths]
    head += ["one-shot", "agent"]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("|" + "---|" * len(head))

    order = sorted(models, key=lambda k: -(models[k]["tg"].get(0) or 0))
    for label in order:
        m = models[label]
        gb = "%.0fGB" % (m["size"] / 1e9) if m.get("size") else "-"
        row = [label, gb, fmt(m["pp"].get(0))]
        row += [fmt(m["tg"].get(dep)) for dep in depths]
        for table in (oneshot, agent):
            mid = match(label, table)
            if mid:
                med, mx, all_s = table[mid]
                cell = "%d/%d" % (med, mx)
                if len(all_s) > 1:
                    cell += " (%s)" % "-".join(str(s) for s in all_s)
            else:
                cell = "-"
            row.append(cell)
        lines.append("| " + " | ".join(row) + " |")

    out = "\n".join(lines)
    print(out)

    if controls:
        print("\nThermal control (%s re-run through the sequence):" %
              os.environ.get("CONTROL", "same model"))
        base = None
        for tag in ("control-start", "control-middle", "control-end"):
            if tag not in controls:
                continue
            ts = controls[tag]["tg"].get(0)
            if ts is None:
                continue
            if base is None:
                base = ts
            print("  %-16s %6.1f tok/s   %+.1f%% vs start"
                  % (tag.replace("control-", ""), ts, 100 * (ts - base) / base))
        print("  A drift under ~2%% means back-to-back running is fine and the"
              " table above needs no caveat.")

    log = os.path.join(d, "runlog.jsonl")
    if os.path.isfile(log):
        print("\nRun log (wall clock and Tctl per model):")
        with open(log) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if r.get("error"):
                    print("  %-18s FAILED" % r.get("label"))
                else:
                    print("  %-18s %5ss   %sC -> %sC"
                          % (r.get("label"), r.get("seconds"),
                             r.get("temp_before") or "?", r.get("temp_after") or "?"))

    for flag in ("-o", "--out"):
        if flag in argv:
            path = argv[argv.index(flag) + 1]
            with open(path, "w") as fh:
                fh.write(out + "\n")
            print("\nwritten to %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
