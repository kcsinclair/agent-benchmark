import re

_COMPONENT = r"(\d+(?:\.\d+)?)(ms|h|m|s)"
_FULL = re.compile(rf"^(?:{_COMPONENT})+$")
_PART = re.compile(_COMPONENT)

_SECONDS = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}
_ORDER = {"h": 0, "m": 1, "s": 2, "ms": 3}


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    sign = 1.0
    if s.startswith("-"):
        sign = -1.0
        s = s[1:]

    if not s or not _FULL.fullmatch(s):
        raise ValueError(f"invalid duration string: {text!r}")

    total = 0.0
    last_rank = -1
    seen = set()
    for number, unit in _PART.findall(s):
        rank = _ORDER[unit]
        if rank <= last_rank:
            raise ValueError(f"units out of order or repeated in {text!r}")
        if unit in seen:
            raise ValueError(f"repeated unit {unit!r} in {text!r}")
        seen.add(unit)
        last_rank = rank
        total += float(number) * _SECONDS[unit]

    return sign * total
