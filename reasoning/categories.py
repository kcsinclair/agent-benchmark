#!/usr/bin/env python3
"""Item generators and answer checkers for the reasoning track.

Every item is a (prompt, answer, check) triple where the answer is computed in
Python, never written by hand and never shown to a model. Most categories are
generated from a seed, which buys three things a hand-written question bank
cannot: unlimited items so sampling noise stops dominating, immunity to training
-data contamination, and difficulty you can dial.

Grading is mechanical — exact match, a number, or a regex. No LLM judge: the
whole value of this repo is that the grader has no opinions.

Models pad answers with prose no matter how firmly you ask them not to, so
checkers read the LAST non-empty line of the reply and normalise it. That is the
one piece of leniency, applied identically to everyone.
"""
import importlib.util
import json
import os
import random
import re

# --------------------------------------------------------------- answer utils

def last_line(text):
    lines = [l.strip() for l in (text or "").strip().split("\n") if l.strip()]
    return lines[-1] if lines else ""


def norm(text):
    return re.sub(r"[\s.,!;:*_`\"']+", " ", (text or "").strip().lower()).strip()


def last_number(text):
    """Trailing number anywhere in the reply — models like to say 'is 42.'"""
    nums = re.findall(r"-?\d+(?:\.\d+)?", (text or "").replace(",", ""))
    return nums[-1] if nums else None


def check_number(reply, answer):
    got = last_number(last_line(reply)) or last_number(reply)
    if got is None:
        return False
    try:
        return abs(float(got) - float(answer)) < 1e-6
    except ValueError:
        return False


def check_exact(reply, answer):
    return norm(last_line(reply)) == norm(answer)


def check_letter(reply, answer):
    """Forced choice: find a lone A/B/C, preferring the last line."""
    for chunk in (last_line(reply), reply or ""):
        hits = re.findall(r"\b([ABC])\b", chunk.upper())
        if hits:
            return hits[-1] == answer.upper()
    return False


# ------------------------------------------------------- 1. state tracking

def gen_state(rng, steps=6):
    names = rng.sample(["A", "B", "C", "D"], 3)
    state = {n: rng.randint(2, 9) for n in names}
    lines = ["You have three bins: " +
             ", ".join("%s=%d" % (n, state[n]) for n in names) + "."]
    for i in range(steps):
        kind = rng.choice(["move", "add", "remove", "double", "swap"])
        a, b = rng.sample(names, 2)
        # never emit an operation that would drive a bin negative: "remove 5"
        # from a bin holding 3 is ambiguous (does it clamp at zero?) and would
        # mark a reasonable model wrong for a flaw in the question
        if kind in ("move", "remove") and state[a] < 1:
            kind = "add"
        if kind == "move":
            k = rng.randint(1, state[a])
            state[a] -= k; state[b] += k
            lines.append("%d. Move %d from %s to %s." % (i + 1, k, a, b))
        elif kind == "add":
            k = rng.randint(1, 6)
            state[a] += k
            lines.append("%d. Add %d to %s." % (i + 1, k, a))
        elif kind == "remove":
            k = rng.randint(1, state[a])
            state[a] -= k
            lines.append("%d. Remove %d from %s." % (i + 1, k, a))
        elif kind == "double":
            state[a] *= 2
            lines.append("%d. Double %s." % (i + 1, a))
        else:
            state[a], state[b] = state[b], state[a]
            lines.append("%d. Swap the contents of %s and %s." % (i + 1, a, b))
    target = rng.choice(names)
    prompt = ("\n".join(lines) +
              "\n\nApply the steps in order. How many are in %s at the end?"
              "\nReply with a single number and nothing else." % target)
    return prompt, str(state[target]), check_number


# ------------------------------------------------- 2. constraint satisfaction

def gen_constraints(rng, n=4):
    people = rng.sample(["Ana", "Ben", "Cara", "Dan", "Eve", "Fay"], n)
    while True:
        order = people[:]
        rng.shuffle(order)
        pos = {p: i + 1 for i, p in enumerate(order)}
        clues, seen = [], set()
        for _ in range(n + 2):
            kind = rng.choice(["before", "not_at", "adjacent", "at_end"])
            a, b = rng.sample(people, 2)
            if kind == "before" and pos[a] < pos[b]:
                clues.append("%s is somewhere before %s." % (a, b))
            elif kind == "not_at":
                bad = rng.choice([i for i in range(1, n + 1) if i != pos[a]])
                clues.append("%s is not in position %d." % (a, bad))
            elif kind == "adjacent" and abs(pos[a] - pos[b]) == 1:
                clues.append("%s and %s are next to each other." % (a, b))
            elif kind == "at_end" and pos[a] == n:
                clues.append("%s is last." % a)
        clues = [c for c in clues if not (c in seen or seen.add(c))]
        if len(clues) < 3:
            continue
        # keep only puzzles with exactly one consistent arrangement
        sols = [p for p in _perms(people) if _fits(p, clues)]
        if len(sols) == 1:
            break
    target = rng.choice(people)
    prompt = ("%s are standing in a queue, positions 1 to %d.\n\n"
              % (", ".join(people), n) + "\n".join("- " + c for c in clues) +
              "\n\nWhat position is %s in?"
              "\nReply with a single number and nothing else." % target)
    return prompt, str(pos[target]), check_number


def _perms(items):
    if len(items) <= 1:
        yield list(items); return
    for i, x in enumerate(items):
        for rest in _perms(items[:i] + items[i + 1:]):
            yield [x] + rest


def _fits(order, clues):
    pos = {p: i + 1 for i, p in enumerate(order)}
    for c in clues:
        m = re.match(r"(\w+) is somewhere before (\w+)\.", c)
        if m and not pos[m.group(1)] < pos[m.group(2)]:
            return False
        m = re.match(r"(\w+) is not in position (\d+)\.", c)
        if m and pos[m.group(1)] == int(m.group(2)):
            return False
        m = re.match(r"(\w+) and (\w+) are next to each other\.", c)
        if m and abs(pos[m.group(1)] - pos[m.group(2)]) != 1:
            return False
        m = re.match(r"(\w+) is last\.", c)
        if m and pos[m.group(1)] != len(order):
            return False
    return True


# ------------------------------------------------------ 3. instruction compliance

def gen_compliance(rng):
    kind = rng.choice(["words", "json", "upper", "number_only",
                       "positional", "avoid_letter", "ordering", "exact_count"])
    animal = rng.choice(["otter", "heron", "badger", "lynx", "raven"])
    if kind == "words":
        prompt = ("Name three colours. Reply with exactly three lowercase words "
                  "separated by single spaces. No punctuation, no other text.")
        def check(reply, _):
            line = last_line(reply)
            return bool(re.fullmatch(r"[a-z]+ [a-z]+ [a-z]+", line))
        return prompt, "red green blue", check
    if kind == "json":
        x, y = rng.randint(3, 40), rng.randint(3, 40)
        prompt = ('Reply with a bare JSON object and nothing else — no code '
                  'fence, no commentary. It must have exactly the keys '
                  '"animal", "x" and "total", where animal is "%s", x is %d, '
                  'and total is %d plus %d.' % (animal, x, x, y))
        def check(reply, _):
            text = (reply or "").strip()
            if "```" in text:          # the decoration models cannot resist
                return False
            try:
                obj = json.loads(text)
            except ValueError:
                return False
            return (set(obj) == {"animal", "x", "total"}
                    and norm(str(obj["animal"])) == animal
                    and str(obj.get("x")) == str(x)
                    and str(obj.get("total")) == str(x + y))
        return prompt, '{"animal":"%s","x":%d,"total":%d}' % (animal, x, x + y), check
    if kind == "upper":
        prompt = ("What is the capital of France? Reply with the answer in "
                  "capital letters only, no punctuation, no other text.")
        def check(reply, _):
            return last_line(reply).strip(" .") == "PARIS"
        return prompt, "PARIS", check
    if kind == "positional":
        word = rng.choice(["blue", "north", "seven", "quiet"])
        n = rng.randint(4, 6)
        filler = ["the", word] + ["quiet", "river", "runs", "far"][:n - 2]
        prompt = ("Write a sentence of exactly %d lowercase words where the "
                  "second word is '%s'. No punctuation of any kind, no other "
                  "text." % (n, word))
        def check(reply, _):
            line = last_line(reply)
            if not re.fullmatch(r"[a-z]+(?: [a-z]+)*", line):
                return False
            parts = line.split()
            return len(parts) == n and parts[1] == word
        return prompt, " ".join(filler), check

    if kind == "avoid_letter":
        letter = rng.choice(["e", "a", "o"])
        pool = ["Chile", "Peru", "Fiji", "Egypt", "Kenya", "Nepal", "Brazil",
                "Spain", "Turkey", "Cyprus", "Sweden", "Norway", "Iraq",
                "Bolivia", "Tonga", "Cuba", "Mali", "Oman"]
        valid = [c for c in pool if letter not in c.lower()]
        prompt = ("Name a country. Your answer must not contain the letter "
                  "'%s' in either case. Reply with the country name only — no "
                  "punctuation, no other text." % letter)
        def check(reply, _):
            line = last_line(reply).strip(" .")
            return (bool(re.fullmatch(r"[A-Za-z][A-Za-z \-]*", line))
                    and letter not in line.lower() and len(line) > 2)
        return prompt, valid[0], check

    if kind == "ordering":
        prompt = ("List these three words in reverse alphabetical order: "
                  "cedar, alder, birch. Separate them with commas and no "
                  "spaces. Reply with the list only.")
        def check(reply, _):
            return last_line(reply).strip(" .") == "cedar,birch,alder"
        return prompt, "cedar,birch,alder", check

    if kind == "exact_count":
        n = rng.randint(3, 5)
        example = " ".join(["vast", "blue", "salty", "cold", "deep"][:n])
        prompt = ("Reply with exactly %d words describing the sea. Do not use "
                  "any punctuation. Do not add anything else." % n)
        def check(reply, _):
            line = last_line(reply)
            return (bool(re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+)*", line))
                    and len(line.split()) == n)
        return prompt, example, check

    a, b = rng.randint(11, 49), rng.randint(11, 49)
    prompt = ("What is %d plus %d? Reply with only the digits — no words, no "
              "punctuation, no explanation." % (a, b))
    def check(reply, _):
        return last_line(reply).strip() == str(a + b)
    return prompt, str(a + b), check


# ------------------------------------------------------------- 4. abstention

def gen_abstention(rng):
    """Three kinds, mixed: directly stated, derivable, and genuinely absent.

    The first version was too easy — every model scored 20/20 — because the
    absent facts were obviously absent. Now the report carries a near-miss for
    the missing fact (the same quantity for a DIFFERENT site, or a related but
    distinct quantity), so answering requires noticing that the number on the
    page is not the number asked for. The derivable third punishes the opposite
    failure: a model that abstains whenever arithmetic is required.
    """
    site = rng.choice(["Fairwater", "Kelso", "Brindle", "Otterby"])
    other = rng.choice([s for s in ["Fairwater", "Kelso", "Brindle", "Otterby"]
                        if s != site])
    bays = rng.randint(3, 9)
    per_bay = rng.randint(2, 5)
    staff_other = rng.randint(10, 60)
    report = ("Site report.\n"
              "- The %s depot has %d loading bays.\n"
              "- Each bay at %s handles %d lorries per day.\n"
              "- The %s depot employs %d staff.\n"
              "- Both depots opened in March and share a maintenance contract."
              % (site, bays, site, per_bay, other, staff_other))
    kind = rng.choice(["stated", "derivable", "absent", "absent"])
    if kind == "stated":
        q = "How many loading bays does the %s depot have?" % site
        answer = str(bays)
        def check(reply, _):
            return check_number(reply, answer)
    elif kind == "derivable":
        q = ("How many lorries per day can the %s depot handle in total?" % site)
        answer = str(bays * per_bay)
        def check(reply, _):
            return check_number(reply, answer)
    else:
        # the near-miss: staff numbers ARE in the report, for the other depot
        q = "How many staff does the %s depot employ?" % site
        answer = "UNKNOWN"
        def check(reply, _):
            return "unknown" in norm(last_line(reply))
    prompt = (report + "\n\n" + q +
              "\nUse only the report. If the report does not give the answer "
              "for the depot asked about, reply with exactly UNKNOWN. Reply "
              "with a number or UNKNOWN and nothing else.")
    return prompt, answer, check


# ------------------------------------------------------- 5. constraint traps

# The bank itself is hand-authored and lives in the private harness submodule,
# at harness/reasoning/trap_items.py. It is the one category that cannot be
# regenerated: every other generator here computes its own answers from a seed,
# so publishing it gives nothing away, but a model that has seen these fourteen
# items scores 14/14 on the category that discriminates hardest.
#
# Without the submodule the category is dropped rather than faked — the track
# then runs 88 items instead of 102 and says so in its header. BENCH_HARNESS
# overrides where to look.
#
# Stored as (scenario, correct, [distractors]) and the options are SHUFFLED per
# item at build time. An earlier version wrote the options out longhand and the
# answer was "B" every time — a model that always replies B would have scored
# 100% and looked like the best reasoner in the fleet.

def _load_trap_items():
    root = os.environ.get("BENCH_HARNESS") or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), os.pardir, "harness")
    path = os.path.join(root, "reasoning", "trap_items.py")
    if not os.path.isfile(path):
        return []
    spec = importlib.util.spec_from_file_location("_trap_items", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(getattr(module, "TRAP_ITEMS", []))


TRAP_ITEMS = _load_trap_items()
TRAPS_AVAILABLE = bool(TRAP_ITEMS)

def gen_trap(rng, used=None):
    if not TRAP_ITEMS:
        raise RuntimeError(
            "the trap category needs the private harness submodule: "
            "git submodule update --init, or set BENCH_HARNESS")
    pool = [t for t in TRAP_ITEMS if used is None or t[0] not in used]
    if not pool:
        pool = TRAP_ITEMS
    scenario, correct, distractors = rng.choice(pool)
    options = [correct] + list(distractors)
    rng.shuffle(options)                      # so the answer is not always B
    letter = "ABC"[options.index(correct)]
    body = "\n".join("%s) %s" % ("ABC"[i], o) for i, o in enumerate(options))
    return (scenario + "\n" + body +
            "\n\nReply with a single letter and nothing else.",
            letter, check_letter)


# ------------------------------------------------------- 6. retrieval at depth

FILLER = [
    "Router {i} completed its scheduled firmware audit without incident.",
    "Switch {i} reported nominal port utilisation during the review window.",
    "Link {i} was re-certified by the cabling contractor.",
    "Cabinet {i} passed its quarterly thermal inspection.",
    "Circuit {i} remains under the standard maintenance agreement.",
]


def gen_retrieval(rng, depth_lines=700):
    """Two facts, far apart, plus decoys that reward sloppy matching.

    The first version was too easy — 8/8 for every model — because only one
    host had an uptime at all. Now several do, one host in the target region
    carries a PLANNED uptime rather than a recorded one, and the regions are
    stated separately from the uptimes, so the answer needs both facts joined
    rather than one keyword found.
    """
    regions = ["north", "south", "east", "west"]
    region = rng.choice(regions)
    host = "srv-%d" % rng.randint(100, 399)
    decoy_same = "srv-%d" % rng.randint(400, 699)
    decoy_other = "srv-%d" % rng.randint(700, 999)
    uptime = rng.randint(101, 999)
    lines = [FILLER[i % len(FILLER)].format(i=i) for i in range(depth_lines)]

    def place(frac, text):
        lines.insert(int(depth_lines * frac), text)

    place(0.08, "Host %s is located in the %s region." % (host, region))
    place(0.21, "Host %s is located in the %s region." % (decoy_same, region))
    place(0.37, "Host %s is located in the %s region."
          % (decoy_other, rng.choice([r for r in regions if r != region])))
    place(0.55, "Host %s recorded an uptime of %d days."
          % (decoy_other, rng.randint(101, 999)))
    # a plausible near-miss: right region, but a PLANNED figure, not recorded
    place(0.72, "Host %s has a planned uptime target of %d days."
          % (decoy_same, rng.randint(101, 999)))
    place(0.93, "Host %s recorded an uptime of %d days." % (host, uptime))

    prompt = ("Operations log:\n\n" + "\n".join(lines) +
              "\n\nWhich recorded uptime, in days, belongs to a host in the %s "
              "region? Planned targets do not count.\nReply with a single "
              "number and nothing else." % region)
    return prompt, str(uptime), check_number


# ------------------------------------------------------------------ registry

CATEGORIES = {
    "state":      {"gen": gen_state,       "n": 20, "label": "state tracking"},
    "constraint": {"gen": gen_constraints, "n": 20, "label": "constraint satisfaction"},
    "compliance": {"gen": gen_compliance,  "n": 20, "label": "instruction compliance"},
    "abstention": {"gen": gen_abstention,  "n": 20, "label": "abstention"},
    "trap":       {"gen": gen_trap,        "n": 14, "label": "constraint traps"},
    "retrieval":  {"gen": gen_retrieval,   "n": 8,  "label": "retrieval at depth"},
}

if not TRAPS_AVAILABLE:                 # no private bank -> 88 items, not 102
    del CATEGORIES["trap"]


def build(category, count, seed):
    """-> [(prompt, answer, check)] — deterministic for a given seed."""
    rng = random.Random("%s/%d" % (category, seed))
    spec = CATEGORIES[category]
    items, used = [], set()
    for _ in range(count):
        if category == "trap":
            item = spec["gen"](rng, used)
            used.add(item[0].split("\n")[0])
        else:
            item = spec["gen"](rng)
        items.append(item)
    return items


if __name__ == "__main__":
    import sys
    cat = sys.argv[1] if len(sys.argv) > 1 else "state"
    for p, a, _ in build(cat, int(sys.argv[2]) if len(sys.argv) > 2 else 3, 1):
        print("-" * 60)
        print(p[:1200])
        print("ANSWER:", a)
