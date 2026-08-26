import re


def parse_duration(text: str) -> float:
    """Parse a human‑readable duration string and return the total number of seconds.

    The string may contain an optional leading minus sign, followed by one or more
    components.  Each component consists of a non‑negative decimal number followed
    by a unit: ``h`` (hours), ``m`` (minutes), ``s`` (seconds) or ``ms``
    (milliseconds).  Units must appear in strictly descending order and may
    appear at most once.

    Leading and trailing whitespace is ignored; any other whitespace causes a
    :class:`ValueError`.

    Parameters
    ----------
    text: str
        The duration string to parse.

    Returns
    -------
    float
        The total duration in seconds.

    Raises
    ------
    TypeError
        If *text* is not a string.
    ValueError
        If the string does not conform to the format rules.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    s = text.strip()
    if not s:
        raise ValueError("Empty duration string")

    sign = 1
    if s[0] == '-':
        sign = -1
        s = s[1:]
    elif s[0] == '+':
        raise ValueError("Leading '+' not allowed")

    if not s:
        raise ValueError("No duration components")

    # Regular expression to match a number followed by a unit.
    # Number: one or more digits, optional fractional part.
    # Unit: h, m, s, or ms.
    component_re = re.compile(r"(\d+(?:\.\d+)?)(h|m|s|ms)")
    units = ['h', 'm', 's', 'ms']

    pos = 0
    total_seconds = 0.0
    last_unit_index = -1

    for match in component_re.finditer(s):
        if match.start() != pos:
            # There is a gap (e.g., whitespace or invalid characters)
            raise ValueError("Invalid format")

        number_str, unit = match.group(1), match.group(2)
        try:
            number = float(number_str)
        except ValueError:
            raise ValueError("Invalid number")

        unit_index = units.index(unit)
        if unit_index <= last_unit_index:
            raise ValueError("Units out of order or repeated")
        last_unit_index = unit_index

        if unit == 'h':
            total_seconds += number * 3600
        elif unit == 'm':
            total_seconds += number * 60
        elif unit == 's':
            total_seconds += number
        elif unit == 'ms':
            total_seconds += number / 1000

        pos = match.end()

    if pos != len(s):
        # Remaining characters that were not matched
        raise ValueError("Invalid format")

    return sign * total_seconds
