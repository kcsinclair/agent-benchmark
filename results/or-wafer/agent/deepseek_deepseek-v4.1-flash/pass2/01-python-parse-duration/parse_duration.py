"""Parse human-readable duration strings into seconds.

Supported units (must appear at most once each, in descending size order):
    h  hours
    m  minutes
    s  seconds
    ms milliseconds
"""

import re

__all__ = ["parse_duration"]

# Number: digits with an optional fractional part. No leading '.', no trailing
# '.', no sign, no exponent.
_NUMBER = r"\d+(?:\.\d+)?"

# Units in descending order of magnitude.
_UNITS = ["h", "m", "s", "ms"]

# One component: a number immediately followed by one of the units. The
# alternation is ordered so that "ms" is matched before "m".
_COMPONENT = r"(?P<value>{num})(?P<unit>ms|h|m|s)".format(num=_NUMBER)

_PATTERN = re.compile(
    r"(?P<sign>-)?(?P<components>(?:{comp})*)".format(comp=_COMPONENT)
)

_SCALE = {
    "h": 3600.0,
    "m": 60.0,
    "s": 1.0,
    "ms": 0.001,
}

_UNIT_RANK = {unit: i for i, unit in enumerate(_UNITS)}


def parse_duration(text: str) -> float:
    """Return the total number of seconds represented by *text*.

    Raises:
        TypeError: if *text* is not a string.
        ValueError: if *text* is not a valid duration string.
    """
    if not isinstance(text, str):
        raise TypeError("duration must be a string, got %r" % type(text).__name__)

    s = text.strip()

    match = _PATTERN.fullmatch(s)
    if match is None:
        raise ValueError("invalid duration: %r" % (text,))

    components = match.group("components")
    if not components:
        raise ValueError("invalid duration: %r" % (text,))

    total = 0.0
    last_rank = -1
    pos = 0

    for comp in re.finditer(_COMPONENT, components):
        # Components must be contiguous and cover the whole string.
        if comp.start() != pos:
            raise ValueError("invalid duration: %r" % (text,))
        pos = comp.end()

        unit = comp.group("unit")
        rank = _UNIT_RANK[unit]

        # Strictly descending order of size, no repeats.
        if rank <= last_rank:
            raise ValueError("invalid duration: %r" % (text,))
        last_rank = rank

        total += float(comp.group("value")) * _SCALE[unit]

    if pos != len(components):
        raise ValueError("invalid duration: %r" % (text,))

    if match.group("sign"):
        total = -total

    return total
