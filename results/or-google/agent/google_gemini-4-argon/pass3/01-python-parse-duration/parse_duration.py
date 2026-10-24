import re

_DURATION_RE = re.compile(
    r"^(?P<neg>-)?"
    r"(?:(?P<h>[0-9]+(?:\.[0-9]+)?)h)?"
    r"(?:(?P<m>[0-9]+(?:\.[0-9]+)?)m(?!s))?"
    r"(?:(?P<s>[0-9]+(?:\.[0-9]+)?)s)?"
    r"(?:(?P<ms>[0-9]+(?:\.[0-9]+)?)ms)?$"
)


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("Duration must be a string")

    stripped = text.strip()
    if not stripped or stripped == "-":
        raise ValueError(f"Invalid duration string: {text!r}")

    match = _DURATION_RE.match(stripped)
    if not match:
        raise ValueError(f"Invalid duration string: {text!r}")

    groups = match.groupdict()
    if not any(groups[u] is not None for u in ("h", "m", "s", "ms")):
        raise ValueError(f"Invalid duration string: {text!r}")

    total = 0.0
    if groups["h"] is not None:
        total += float(groups["h"]) * 3600.0
    if groups["m"] is not None:
        total += float(groups["m"]) * 60.0
    if groups["s"] is not None:
        total += float(groups["s"])
    if groups["ms"] is not None:
        total += float(groups["ms"]) / 1000.0

    if groups["neg"] is not None:
        total = -total

    return total
