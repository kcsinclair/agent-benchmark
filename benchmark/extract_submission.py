#!/usr/bin/env python3
"""Pull a problem's deliverable files out of a raw model transcript.

Usage:
    extract_submission.py <problem> <transcript> <output_dir>
    extract_submission.py --list

A completion-mode model (llama-cli and friends) answers with prose and fenced
code blocks, not files. This turns one such transcript into the exact filenames
the graders import, so the result can be graded like any other submission.

Selection rules, in order:

1. If a deliverable's filename is mentioned just before a code block ("### q1.sql"
   or "**cache.mjs**"), that block wins. A later mention beats an earlier one, so
   a model that corrects itself gets its final version used.
2. Otherwise, blocks are filtered to the problem's language and to those
   containing the required signature ("def parse_duration", "func Run(", ...),
   and the last survivor wins — again, later beats earlier.
3. Problem 3 wants four files: four or more SQL blocks map to q1..q4 in order,
   and a single block holding all four queries is split on its query separators.
4. If the transcript has no fenced blocks at all but does contain the required
   signature, the whole transcript is treated as the code — some runs emit bare
   source with no markdown.

Nothing is written when nothing matches: a missing file makes the grader report
MISSING deliverable, which is the honest outcome. Exits 1 if any deliverable
could not be extracted.
"""
import os
import re
import sys

PROBLEMS = {
    "01-python-parse-duration": {
        "files": ["parse_duration.py"],
        "langs": {"python", "py", "python3"},
        "markers": ["def parse_duration"],
    },
    "02-js-lru-ttl-cache": {
        "files": ["cache.mjs"],
        "langs": {"javascript", "js", "mjs", "node", "typescript", "ts"},
        "markers": ["class LruTtlCache"],
    },
    "03-sql-analytics": {
        "files": ["q1.sql", "q2.sql", "q3.sql", "q4.sql"],
        "langs": {"sql", "sqlite", "sqlite3"},
        "markers": ["select"],
    },
    "04-go-worker-pool": {
        "files": ["pool.go"],
        "langs": {"go", "golang"},
        "markers": ["func Run("],
    },
    "05-python-scheduler": {
        "files": ["scheduler.py"],
        "langs": {"python", "py", "python3"},
        "markers": ["def best_schedule"],
    },
}

FENCE = re.compile(
    r"^[ \t]*(?P<fence>`{3,}|~{3,})[ \t]*(?P<lang>[\w+#.-]*)[ \t]*\n"
    r"(?P<body>.*?)"
    r"^[ \t]*(?P=fence)[ \t]*$",
    re.S | re.M,
)

PREAMBLE = 200   # chars before a block searched for a filename mention


class Block:
    def __init__(self, lang, body, preamble, index):
        self.lang = lang.lower()
        self.body = body
        self.preamble = preamble
        self.index = index

    def has_marker(self, markers):
        low = self.body.lower()
        return any(m.lower() in low for m in markers)


def parse_blocks(text):
    blocks = []
    for i, m in enumerate(FENCE.finditer(text)):
        start = m.start()
        blocks.append(Block(
            m.group("lang"),
            m.group("body"),
            text[max(0, start - PREAMBLE):start],
            i,
        ))
    return blocks


def split_multi_sql(body, files):
    """A single block holding all four queries -> one chunk per file."""
    # labelled form: "-- q1.sql" / "q1.sql:" separators
    positions = []
    for name in files:
        hits = [m.start() for m in re.finditer(re.escape(name), body)]
        if hits:
            positions.append((hits[0], name))
    if len(positions) == len(files):
        positions.sort()
        chunks = {}
        for n, (pos, name) in enumerate(positions):
            end = positions[n + 1][0] if n + 1 < len(positions) else len(body)
            chunk = body[pos:end]
            # drop the label line itself
            chunk = chunk.split("\n", 1)[1] if "\n" in chunk else ""
            if chunk.strip():
                chunks[name] = chunk
        if len(chunks) == len(files):
            return chunks
    # unlabelled: exactly one SELECT statement per file, in order
    statements = [s.strip() for s in body.split(";") if s.strip()]
    if len(statements) == len(files):
        return {name: statements[n] + ";" for n, name in enumerate(files)}
    return {}


def choose(problem, text):
    """-> (dict of filename -> source, dict of filename -> how it was found)"""
    spec = PROBLEMS[problem]
    files, langs, markers = spec["files"], spec["langs"], spec["markers"]
    blocks = parse_blocks(text)
    chosen, how = {}, {}

    # 1. explicit filename mentioned right before a block
    taken = set()
    for b in blocks:
        named = [f for f in files if f in b.preamble]
        if len(named) == 1:
            chosen[named[0]] = b.body
            how[named[0]] = "labelled block #%d" % (b.index + 1)
            taken.add(b.index)

    remaining = [f for f in files if f not in chosen]
    if not remaining:
        return chosen, how

    # 2. narrow by language tag, then by required signature
    pool = [b for b in blocks if b.index not in taken]
    tagged = [b for b in pool if b.lang in langs]
    if tagged:
        pool = tagged
    else:
        pool = [b for b in pool if not b.lang] or pool
    with_marker = [b for b in pool if b.has_marker(markers)]
    if with_marker:
        pool = with_marker

    if len(remaining) == 1:
        if pool:
            best = pool[-1]
            chosen[remaining[0]] = best.body
            how[remaining[0]] = "block #%d%s" % (
                best.index + 1, " (%s)" % best.lang if best.lang else "")
        elif any(m.lower() in text.lower() for m in markers) and not blocks:
            # 4. bare source, no markdown at all
            chosen[remaining[0]] = text
            how[remaining[0]] = "whole transcript (no code fences)"
        return chosen, how

    # 3. several files still wanted: map blocks to them in order
    if len(pool) >= len(remaining):
        for name, b in zip(remaining, pool[-len(remaining):]):
            chosen[name] = b.body
            how[name] = "block #%d in order" % (b.index + 1)
    elif len(pool) == 1:
        for name, body in split_multi_sql(pool[0].body, remaining).items():
            chosen[name] = body
            how[name] = "split from block #%d" % (pool[0].index + 1)
    return chosen, how


def extract_to(problem, text, outdir, log=print):
    """Write a problem's deliverables from a transcript. -> (written, missing)"""
    chosen, how = choose(problem, text)
    os.makedirs(outdir, exist_ok=True)
    written, missing = [], []
    for name in PROBLEMS[problem]["files"]:
        body = chosen.get(name, "").strip()
        if not body:
            missing.append(name)
            log("  MISSING  %s — no code block matched" % name)
            continue
        with open(os.path.join(outdir, name), "w") as fh:
            fh.write(body + "\n")
        written.append(name)
        log("  wrote    %s  (%s, %d lines)"
            % (name, how.get(name, "?"), body.count("\n") + 1))
    return written, missing


def main():
    args = [a for a in sys.argv[1:]]
    if "--list" in args:
        for name, spec in sorted(PROBLEMS.items()):
            print("%-28s %s" % (name, " ".join(spec["files"])))
        return 0
    if len(args) != 3 or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        return 2
    problem, transcript, outdir = args
    if problem not in PROBLEMS:
        print("extract_submission: unknown problem %r (try --list)" % problem,
              file=sys.stderr)
        return 2
    try:
        with open(transcript, "r", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        print("extract_submission: cannot read %s (%s)" % (transcript, e),
              file=sys.stderr)
        return 2

    _, missing = extract_to(problem, text, outdir)
    if missing:
        print("  %d of %d deliverable(s) not found in %s"
              % (len(missing), len(PROBLEMS[problem]["files"]), transcript))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
