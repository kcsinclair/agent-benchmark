"""Parse human-readable duration strings into seconds.

Format: optional leading ``-`` followed by one or more concatenated
components, each a non-negative decimal number followed by a unit
(``h``, ``m``, ``s`` or ``ms``).  Units must be in strictly descending
order of size and each may appear at most once.
"""

import re

__all__ = ["parse_duration"]

# Unit name -> seconds per unit.  Order here is descending by size and is
# also the required order of appearance in the input.
_UNITS = (
    ("h", 3600.0),
    ("m", 60.0),
    ("s", 1.0),
    ("ms", 0.001),
)
_UNIT_MULTIPLIER = dict(_UNITS)

# number: digits with an optional fractional part (no leading/trailing dot)
_NUMBER = r"\d+(?:\.\d+)?"

# One component: number + unit, recorded as (number, unit).
_COMPONENT_RE = re.compile(r"(" + _NUMBER + r")(h|ms|s|m)")

# Full-string pattern: optional sign, one or more components, nothing else.
_FULL_RE = re.compile(r"-?(?:" + _NUMBER + r"(?:h|ms|s|m))+")

# Ordering rank of each unit (smaller index == larger unit).
_ORDER = {unit: index for index, (unit, _) in enumerate(_UNITS)}


def parse_duration(text: str) -> float:
    """Return the number of seconds described by *text*.

    Raises:
        TypeError: if *text* is not a ``str``.
        ValueError: if *text* is not a valid duration string.
    """
    if not isinstance(text, str):
        raise TypeError(
            "parse_duration() expected a str, got {!r}".format(
                type(text).__name__
            )
        )

    stripped = text.strip()
    if not stripped or not _FULL_RE.fullmatch(stripped):
        raise ValueError("invalid duration string: {!r}".format(text))

    body = stripped[1:] if stripped.startswith("-") else stripped

    total = 0.0
    position = 0
    last_rank = -1
    saw_component = False

    for match in _COMPONENT_RE.finditer(body):
        # Components must tile the body with no gaps.
        if match.start() != position:
            raise ValueError("invalid duration string: {!r}".format(text))
        position = match.end()

        number_text, unit = match.group(1), match.group(2)
        rank = _ORDER[unit]
        if rank <= last_rank:
            raise ValueError("invalid duration string: {!r}".format(text))
        last_rank = rank

        total += float(number_text) * _UNIT_MULTIPLIER[unit]
        saw_component = True

    if not saw_component or position != len(body):
        raise ValueError("invalid duration string: {!r}".format(text))

    return -total if stripped.startswith("-") else total
