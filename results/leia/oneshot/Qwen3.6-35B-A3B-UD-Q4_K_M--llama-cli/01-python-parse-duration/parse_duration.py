"""Parse human-readable duration strings into total seconds."""

import re

_UNITS = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}
_UNIT_ORDER = {"h": 4, "m": 3, "s": 2, "ms": 1}
_COMPONENT_RE = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")


def parse_duration(text: str) -> float:
    """Parse a duration string and return total seconds as a float.

    Supported units (strictly descending order): h, m, s, ms.
    Each unit may appear at most once.  A leading ``-`` negates the result.

    Raises
    ------
    TypeError   *text* is not a string.
    ValueError  The string violates any format rule.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    text = text.strip()
    if not text:
        raise ValueError("empty duration string")

    negative = False
    if text.startswith("-"):
        negative = True
        text = text[1:]
    if not text:
        raise ValueError("no components after minus sign")

    matches = list(_COMPONENT_RE.finditer(text))

    if not matches:
        raise ValueError("no valid duration components found")

    # ---- structural validation ----

    # Every match must be contiguous and cover the entire (sign-stripped) text.
    for i, m in enumerate(matches):
        if i == 0 and m.start() != 0:
            raise ValueError("leading characters before first component")
        if i < len(matches) - 1 and m.end() != matches[i + 1].start():
            raise ValueError("no separator allowed between components")
    if matches[-1].end() != len(text):
        raise ValueError("trailing characters after last component")

    # ---- semantic validation ----

    seen: set[str] = set()
    prev_order = 99  # sentinel larger than any unit's order

    for m in matches:
        val = m.group(1)
        unit = m.group(2)
        if unit in seen:
            raise ValueError(f"duplicate unit '{unit}'")
        seen.add(unit)
        order = _UNIT_ORDER[unit]
        if order > prev_order:
            raise ValueError(
                f"units not in descending size order: '{unit}'"
            )
        prev_order = order

    # ---- compute total seconds ----

    total = sum(float(m.group(1)) * _UNITS[m.group(2)] for m in matches)

    return -total if negative else total
