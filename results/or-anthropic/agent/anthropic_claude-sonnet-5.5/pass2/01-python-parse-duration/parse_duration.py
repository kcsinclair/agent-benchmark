import re

_NUM = r"([0-9]+(?:\.[0-9]+)?)"
_PATTERN = re.compile(
    r"(-)?"
    + r"(?:" + _NUM + r"h)?"
    + r"(?:" + _NUM + r"m(?!s))?"
    + r"(?:" + _NUM + r"s)?"
    + r"(?:" + _NUM + r"ms)?"
)


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    s = text.strip()
    if not s:
        raise ValueError("empty duration")
    m = _PATTERN.fullmatch(s)
    if m is None:
        raise ValueError("invalid duration: %r" % (text,))
    neg, h, mi, sec, ms = m.groups()
    if h is None and mi is None and sec is None and ms is None:
        raise ValueError("no components in duration: %r" % (text,))
    total = 0.0
    if h is not None:
        total += float(h) * 3600.0
    if mi is not None:
        total += float(mi) * 60.0
    if sec is not None:
        total += float(sec)
    if ms is not None:
        total += float(ms) / 1000.0
    if neg and total != 0.0:
        total = -total
    return total
