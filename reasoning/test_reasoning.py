#!/usr/bin/env python3
"""Self-test for the reasoning item generators.

    ./test_reasoning.py

The failure this exists to catch: a generator whose computed answer does not
satisfy its own checker. That would score every model zero on that category and
look like a finding rather than a bug. So each category is fed its own correct
answer (as a model would phrase it, with padding) and must pass, then fed a
wrong answer and must fail.

Also checks that generation is deterministic for a seed, that constraint puzzles
really do have exactly one solution, and that the trap bank has no duplicated or
mis-keyed items.
"""
import random
import sys

import categories as cat

PASS = FAIL = 0


def ok(msg):
    global PASS
    print("  ok   %s" % msg); PASS += 1


def bad(msg, detail=""):
    global FAIL
    print("  FAIL %s" % msg)
    if detail:
        print("       | %s" % str(detail).replace("\n", " ")[:200])
    FAIL += 1


print("reasoning generators self-test")

# --- every category accepts its own answer, in the shapes models reply in ----
for name in cat.CATEGORIES:
    items = cat.build(name, 12, seed=7)
    good = bad_count = 0
    for prompt, answer, check in items:
        # compliance items are meant to reject padding — that is the whole test
        phrasings = [answer] if name == "compliance" else [
            answer, "The answer is %s." % answer,
            "Let me think about this.\n\n%s" % answer]
        if not all(check(p, answer) for p in phrasings):
            good = -1
            bad("%s accepts its own answer" % name,
                "answer=%r prompt=%s" % (answer, prompt[:120]))
            break
        good += 1
    if good > 0:
        ok("%s accepts its own answer (%d items, 3 phrasings each)" % (name, good))

# --- and rejects a wrong one -------------------------------------------------
for name in cat.CATEGORIES:
    items = cat.build(name, 12, seed=7)
    leaks = 0
    for prompt, answer, check in items:
        wrong = "999999"
        if name == "trap":
            wrong = next(l for l in "ABC" if l != answer)
        if name == "compliance":
            wrong = "I am afraid I cannot help with that, sorry!"
        if name == "abstention":
            wrong = "42" if answer == "UNKNOWN" else "UNKNOWN"
        if check(wrong, answer):
            leaks += 1
    if leaks == 0:
        ok("%s rejects a wrong answer" % name)
    else:
        bad("%s rejects a wrong answer" % name, "%d items accepted junk" % leaks)

# --- deterministic for a seed -------------------------------------------------
a = [p for p, _, _ in cat.build("state", 5, seed=3)]
b = [p for p, _, _ in cat.build("state", 5, seed=3)]
c = [p for p, _, _ in cat.build("state", 5, seed=4)]
ok("same seed gives the same items") if a == b else bad("seed determinism")
ok("different seed gives different items") if a != c else bad("seeds collide")

# --- constraint puzzles have exactly one solution -----------------------------
import re
bad_puzzles = 0
for prompt, answer, _ in cat.build("constraint", 8, seed=11):
    names = re.match(r"([\w, ]+) are standing", prompt).group(1).split(", ")
    clues = re.findall(r"^- (.+)$", prompt, re.M)
    sols = [p for p in cat._perms(names) if cat._fits(p, clues)]
    if len(sols) != 1:
        bad_puzzles += 1
if bad_puzzles == 0:
    ok("constraint puzzles have exactly one solution")
else:
    bad("constraint puzzles unique", "%d puzzles were ambiguous" % bad_puzzles)

# --- state tracking is actually solvable from the text ------------------------
prompt, answer, _ = cat.build("state", 1, seed=5)[0]
ok("state items carry their working") if "bins:" in prompt and answer.isdigit() \
    else bad("state item shape", prompt[:120])

# --- trap bank hygiene --------------------------------------------------------
texts = [t[0] for t in cat.TRAP_ITEMS]
if len(set(texts)) == len(texts):
    ok("trap bank has no duplicates (%d items)" % len(texts))
else:
    bad("trap bank duplicates")
letters = [a for _, a, _ in cat.build("trap", 14, seed=9)]
if set(letters) <= {"A", "B", "C"}:
    ok("trap answers are all valid letters")
else:
    bad("trap answer keys", letters)
# a bank where the answer is always the same letter measures letter preference,
# not reasoning — a model that always replies B would score 100%
if len(set(letters)) == 3 and max(letters.count(x) for x in "ABC") <= 8:
    ok("trap answer letters are spread across A/B/C (%s)"
       % "/".join("%s:%d" % (x, letters.count(x)) for x in "ABC"))
else:
    bad("trap answers cluster on one letter",
        "/".join("%s:%d" % (x, letters.count(x)) for x in "ABC"))
# the correct option must not be identifiable by length alone
import statistics
lens = []
for prompt, ans, _ in cat.build("trap", 14, seed=9):
    opts = re.findall(r"^([ABC])\) (.+)$", prompt, re.M)
    correct = [t for l, t in opts if l == ans]
    others = [t for l, t in opts if l != ans]
    if correct and others:
        lens.append(len(correct[0]) - statistics.mean(len(o) for o in others))
if abs(statistics.mean(lens)) < 25:
    ok("correct option is not systematically longer (mean delta %.0f chars)"
       % statistics.mean(lens))
else:
    bad("correct option is length-cued", "mean delta %.0f chars" % statistics.mean(lens))

# --- retrieval really is deep -------------------------------------------------
prompt, answer, check = cat.build("retrieval", 1, seed=2)[0]
if len(prompt) > 4000 and check("the answer is %s" % answer, answer):
    ok("retrieval items are long and self-consistent (%d chars)" % len(prompt))
else:
    bad("retrieval item", "%d chars" % len(prompt))

print("\n  %d passed, %d failed" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
