import re

_COMPONENT = r"(\d+(?:\.\d+)?)(ms|h|m|s)"
_FULL = re.compile(rf"(?:{_COMPONENT})+")
_TOKEN = re.compile(_COMPONENT)

_SECONDS = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}

# Strictly descending order of size; index used to enforce ordering.
_ORDER = {"h": 0, "m": 1, "s": 2, "ms": 3}


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError(f"parse_duration expects str, got {type(text).__name__}")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    if s.startswith("-"):
        negative = True
        s = s[1:]

    if not s:
        raise ValueError("no components after sign")

    # The whole remainder must be a valid concatenation of components.
    if _FULL.fullmatch(s) is None:
        raise ValueError(f"invalid duration string: {text!r}")

    total = 0.0
    last_rank = -1
    seen = set()
    for number, unit in _TOKEN.findall(s):
        rank = _ORDER[unit]
        if rank <= last_rank:
            raise ValueError(f"units out of order or repeated in {text!r}")
        if unit in seen:  # defensive; implied by ordering check
            raise ValueError(f"repeated unit {unit!r} in {text!r}")
        seen.add(unit)
        last_rank = rank
        total += float(number) * _SECONDS[unit]

    return -total if negative else total
