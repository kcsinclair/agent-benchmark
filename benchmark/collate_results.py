#!/usr/bin/env python3
"""One table of every score in results/, across servers, providers and tracks.

    ./benchmark/collate_results.py                  # everything, as markdown
    ./benchmark/collate_results.py -o table.md      # write it out
    ./benchmark/collate_results.py --plain          # aligned text, not markdown
    ./benchmark/collate_results.py --label or-*     # only matching results dirs
    ./benchmark/collate_results.py --sort model     # default: coding score

Distinct from collate_bench.py, which is speed-first: that one starts from a
`results/<server>/speed/` directory of llama-bench JSON and joins scores onto
it, so it only works for a machine that has a speed sweep, and only covers
oneshot and agent. This one starts from the summaries themselves, so it spans
every results directory including hosted ones that can never have a speed track.

**One row per (results directory, model), not per model.** The same weights
served at a different quantisation are a different contestant here — that is why
the provider pin matters — so `gemma-4-26b` on Parasail (bf16) and on DeepInfra
(fp8) are two rows, not one averaged one.

Summaries are timestamped and never overwritten, so a model that was re-run has
several. The newest one wins, per model per track, matching collate_bench.merged
— taking only the newest *file* would instead lose every model that was not in
the last invocation.
"""
import argparse
import fnmatch
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# track -> (subdirectory, summary filename glob, per-pass score key, per-pass
#           denominator key)
TRACKS = {
    "oneshot":   ("oneshot",   "summary-*.json",           "score", "max"),
    "agent":     ("agent",     "agent-summary-*.json",     "score", "max"),
    "reasoning": ("reasoning", "reasoning-summary-*.json", "right", "count"),
}


def merged(pattern, key):
    """-> {model_id: (result, mtime)} with the newest scoring run per model.

    A result carrying no scored pass is skipped rather than recorded as zero:
    a model that was never routable, or whose run died, is absent from the
    table instead of appearing as the worst contestant in it.
    """
    by_model = {}
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path) as fh:
                data = json.load(fh)
        except (ValueError, OSError):
            continue
        stamp = os.path.basename(path).rsplit("-", 2)[-2:]
        stamp = "-".join(stamp).replace(".json", "")
        for r in data.get("results", []):
            if r.get("unrun") or not any(key in p for p in r.get("passes", [])):
                continue
            r["_when"] = stamp
            r["_settings"] = data.get("settings") or {}
            by_model[r["model"]] = r
    return by_model


def cell(rec, key, denom, markdown):
    """median/max, with each pass listed — the spread is the point."""
    passes = rec.get("passes") or []
    got = sorted(p[key] for p in passes if key in p)
    if not got:
        return "", ""
    mx = passes[0].get(denom, "?")
    med = got[len(got) // 2]
    text = "%d/%s" % (med, mx)
    if markdown and mx != "?" and med == mx:
        text = "**%s**" % text
    return text, " · ".join(str(g) for g in got)


def collect(root, patterns):
    """-> rows, one per (results dir, model)."""
    rows = {}
    for label_dir in sorted(glob.glob(os.path.join(root, "*"))):
        if not os.path.isdir(label_dir):
            continue
        label = os.path.basename(label_dir)
        if patterns and not any(fnmatch.fnmatch(label, p) for p in patterns):
            continue
        for track, (sub, pat, key, denom) in TRACKS.items():
            found = merged(os.path.join(label_dir, sub, pat), key)
            for model, rec in found.items():
                row = rows.setdefault((label, model),
                                      {"label": label, "model": model,
                                       "cost": 0.0, "when": "", "provider": ""})
                row[track] = rec
                row["cost"] += sum(p.get("cost_usd", 0) for p in rec["passes"])
                row["when"] = max(row["when"], rec["_when"])
                row["provider"] = (rec["_settings"].get("provider")
                                   or row["provider"])
    return list(rows.values())


def render(rows, markdown, sort):
    head = ["model", "results", "provider", "coding", "passes",
            "reasoning", "agent", "cost", "last run"]
    body = []
    for row in rows:
        coding, spread = cell(row.get("oneshot") or {}, "score", "max", markdown)
        reason, _ = cell(row.get("reasoning") or {}, "right", "count", markdown)
        agent, _ = cell(row.get("agent") or {}, "score", "max", markdown)
        body.append([row["model"], row["label"], row["provider"] or "-",
                     coding or "-", spread or "-", reason or "-", agent or "-",
                     "$%.4f" % row["cost"] if row["cost"] else "-",
                     row["when"]])

    def sort_key(r):
        if sort == "model":
            return (r[0], r[1])
        if sort == "cost":
            return (r[7] == "-", r[7])
        # by coding score, best first; rows without one sink to the bottom
        try:
            n = int(r[3].replace("*", "").split("/")[0])
        except (ValueError, IndexError):
            n = -1
        return (-n, r[0])
    body.sort(key=sort_key)

    if markdown:
        out = ["| " + " | ".join(head) + " |",
               "|" + "|".join(["---"] * len(head)) + "|"]
        out += ["| " + " | ".join(c) + " |" for c in body]
        return "\n".join(out)

    widths = [max(len(str(r[i])) for r in [head] + body)
              for i in range(len(head))]
    fmt = "  ".join("%%-%ds" % w for w in widths)
    out = [fmt % tuple(head), "  ".join("-" * w for w in widths)]
    out += [fmt % tuple(r) for r in body]
    return "\n".join(line.rstrip() for line in out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=os.path.join(REPO, "results"),
                    help="results directory (default: results/)")
    ap.add_argument("-o", "--out", help="write to this file instead of stdout")
    ap.add_argument("--plain", action="store_true",
                    help="aligned text instead of a markdown table")
    ap.add_argument("--label", action="append", default=[], metavar="GLOB",
                    help="only these results dirs, e.g. --label 'or-*'")
    ap.add_argument("--sort", choices=("coding", "model", "cost"),
                    default="coding")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.root):
        sys.exit("collate_results: no such directory %s" % args.root)
    rows = collect(args.root, args.label)
    if not rows:
        sys.exit("collate_results: no scored summaries under %s" % args.root)

    text = render(rows, not args.plain, args.sort)
    note = ("\nMedians, with every pass in the spread column. One row per"
            " (results dir, model): the same weights at a different"
            " quantisation are a different contestant.")
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n" + note + "\n")
        print("wrote %s (%d rows)" % (args.out, len(rows)))
    else:
        print(text)
        print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
