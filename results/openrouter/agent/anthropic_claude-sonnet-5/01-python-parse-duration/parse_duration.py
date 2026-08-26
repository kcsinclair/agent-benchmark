import re

_UNIT_ORDER = ['h', 'm', 's', 'ms']
_UNIT_SECONDS = {
    'h': 3600.0,
    'm': 60.0,
    's': 1.0,
    'ms': 0.001,
}

_COMPONENT_RE = re.compile(r'(\d+(?:\.\d+)?)(h|ms|m|s)')


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("parse_duration expects a string")

    s = text.strip()
    if not s:
        raise ValueError("empty duration string")

    negative = False
    if s[0] == '-':
        negative = True
        s = s[1:]

    if not s:
        raise ValueError("no components after sign")

    pos = 0
    length = len(s)
    total = 0.0
    last_unit_index = -1
    found_any = False

    while pos < length:
        match = _COMPONENT_RE.match(s, pos)
        if not match:
            raise ValueError(f"invalid duration string: {text!r}")

        number_str, unit = match.groups()

        if number_str.endswith('.'):
            raise ValueError(f"invalid number in duration: {number_str!r}")

        try:
            unit_index = _UNIT_ORDER.index(unit)
        except ValueError:
            raise ValueError(f"invalid unit: {unit!r}")

        if unit_index <= last_unit_index:
            raise ValueError("units must be strictly descending and unique")

        last_unit_index = unit_index

        value = float(number_str)
        total += value * _UNIT_SECONDS[unit]
        found_any = True

        pos = match.end()

    if not found_any:
        raise ValueError(f"invalid duration string: {text!r}")

    if pos != length:
        raise ValueError(f"invalid duration string: {text!r}")

    if negative:
        total = -total

    return total
