#!/usr/bin/env python3
"""Strip grader-derived secrets out of results/ before they are published.

Two things in a results tree give away material that contestants must not see:

  1. Verbose run logs. `run_all.sh` prints one PASS/FAIL line per check, of the
     form `PASS  <what it checks>: '<literal input>' == <expected>`. That is the
     grader in English — enough to code to the hidden edge cases without ever
     reading grade.py.

  2. Reasoning items.json, trap category only. Five of the six categories are
     generated from a seed, so their answers are reproducible by anyone with
     categories.py and nothing is given away by storing them. The traps are
     hand-authored and unregenerable, so `expected` (and `reply`, which equals
     it whenever ok is true) is a straight answer key for a bank that cannot be
     replaced without writing fourteen new items.

Scores, timings, token counts, finish reasons and every non-trap item survive:
the point is to publish results, not to redact them.

    ./benchmark/scrub_results.py results/          # rewrite in place
    ./benchmark/scrub_results.py --check results/  # exit 1 if anything leaks

--check makes no changes and is the one to run before a push.
"""

import argparse
import json
import pathlib
import re
import sys

# "  PASS  simple seconds: '90s' == 90.0" / "  FAIL  ..."
CHECK_LINE = re.compile(r"^\s*(PASS|FAIL)\s")

REDACTED = "[redacted: hand-authored trap bank]"


def scrub_log(path, check_only):
    """Drop per-check PASS/FAIL lines, keep SCORE lines and the scorecard."""
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines(keepends=True)
    kept = [ln for ln in lines if not CHECK_LINE.match(ln)]
    n = len(lines) - len(kept)
    if n and not check_only:
        path.write_text("".join(kept), encoding="utf-8")
    return n


def scrub_items(path, check_only):
    """Redact expected/reply on trap items only; leave generated ones alone."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    results = data.get("results") if isinstance(data, dict) else None
    if not isinstance(results, list):
        return 0
    n = 0
    for item in results:
        if not isinstance(item, dict) or item.get("category") != "trap":
            continue
        for key in ("expected", "reply"):
            if item.get(key) not in (None, REDACTED):
                item[key] = REDACTED
                n += 1
    if n and not check_only:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default="results",
                    help="results directory to scrub (default: results)")
    ap.add_argument("--check", action="store_true",
                    help="report what would be scrubbed, change nothing, "
                         "exit 1 if anything is still exposed")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    if not root.exists():
        print("no such directory: %s" % root, file=sys.stderr)
        return 2

    findings = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix == ".txt":
            n = scrub_log(path, args.check)
            what = "check lines"
        elif path.name == "items.json":
            n = scrub_items(path, args.check)
            what = "trap answers"
        else:
            continue
        if n:
            findings += n
            print("%s  %-13s %4d  %s"
                  % ("LEAK " if args.check else "clean", what, n, path))

    if args.check:
        if findings:
            print("\n%d exposed value(s). Run without --check to scrub."
                  % findings, file=sys.stderr)
            return 1
        print("clean: no grader detail or trap answers in %s" % root)
        return 0
    print("\nscrubbed %d value(s)." % findings if findings
          else "nothing to scrub.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
