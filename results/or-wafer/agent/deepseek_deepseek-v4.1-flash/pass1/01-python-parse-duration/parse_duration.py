import re

_UNITS = [
    ("h", 3600.0),
    ("m", 60.0),
    ("s", 1.0),
    ("ms", 0.001),
]

_COMPONENT_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?$")


def parse_duration(text):
    if not isinstance(text, str):
        raise TypeError("expected str, got %r" % type(text).__name__)

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    if s.startswith("-"):
        negative = True
        s = s[1:]

    if not s:
        raise ValueError("no component after sign")

    # Tokenize into (number, unit) pairs, requiring full consumption.
    pos = 0
    components = []
    while pos < len(s):
        m = _COMPONENT_RE.match(s, pos)
        if not m:
            raise ValueError("invalid duration component at position %d: %r" % (pos, s[pos:]))
        num_str, unit = m.group(1), m.group(2)
        # Trailing dot check: regex requires digit after '.', so "5." fails to
        # match the fraction and would leave '.' unconsumed -> invalid.
        components.append((float(num_str), unit))
        pos = m.end()
        if pos == m.start():
            raise ValueError("no progress parsing duration")

    if not components:
        raise ValueError("no components found")

    # Enforce strictly descending unit order and uniqueness.
    order = {u: i for i, (u, _) in enumerate(_UNITS)}
    factor = {u: f for u, f in _UNITS}

    total = 0.0
    prev_rank = -1
    for value, unit in components:
        rank = order[unit]
        if rank <= prev_rank:
            raise ValueError("units out of order or repeated: %r" % unit)
        prev_rank = rank
        total += value * factor[unit]

    return -total if negative else total
