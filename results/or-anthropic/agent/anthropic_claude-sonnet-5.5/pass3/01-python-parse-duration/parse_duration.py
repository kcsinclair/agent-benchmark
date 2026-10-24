import re

_NUM = r"(\d+(?:\.\d+)?)"
_PATTERN = re.compile(
    r"(-)?"
    r"(?:" + _NUM + r"h)?"
    r"(?:" + _NUM + r"m(?!s))?"
    r"(?:" + _NUM + r"s)?"
    r"(?:" + _NUM + r"ms)?",
    re.ASCII,
)


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    s = text.strip()
    m = _PATTERN.fullmatch(s)
    if m is None:
        raise ValueError("invalid duration: %r" % (text,))
    neg, h, mi, sec, ms = m.groups()
    if h is None and mi is None and sec is None and ms is None:
        raise ValueError("invalid duration: %r" % (text,))
    total = 0.0
    if h is not None:
        total += float(h) * 3600.0
    if mi is not None:
        total += float(mi) * 60.0
    if sec is not None:
        total += float(sec)
    if ms is not None:
        total += float(ms) / 1000.0
    if neg:
        total = -total
    if total == 0:
        return 0.0
    return total
