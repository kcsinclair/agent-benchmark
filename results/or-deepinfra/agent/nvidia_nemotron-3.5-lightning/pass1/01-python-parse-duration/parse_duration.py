from __future__ import annotations


def parse_duration(text: str) -> float:
    """Parse a human‑readable duration string and return the total seconds as a float.

    Supported units: h (hours), m (minutes), s (seconds), ms (milliseconds).
    Units must appear in strictly descending order and at most once.
    A leading minus sign negates the whole duration.
    Whitespace is only allowed around the whole string; elsewhere it is invalid.

    Raises:
        TypeError: if *text* is not a string.
        ValueError: if the string does not conform to the format rules.
    """
    if not isinstance(text, str):
        raise TypeError("duration must be a string")

    stripped = text.strip()

    if not stripped:
        raise ValueError("duration string is empty")

    # Reject any internal whitespace (any char that isspace inside the middle)
    # We check after stripping leading/trailing whitespace.
    # If the original had internal whitespace, stripped will still contain it.
    # We detect it by comparing: if any char in stripped is whitespace at positions
    # that were not leading/trailing. A simple way: if the stripped string contains
    # any whitespace character at all (since leading/trailing are already stripped,
    # any remaining whitespace is internal).
    if any(c.isspace() for c in stripped):
        raise ValueError("unexpected whitespace in duration string")

    # Optional leading minus
    negative = False
    if stripped[0] == "-":
        negative = True
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("minus sign with no following component")

    # Parsing state
    i = 0
    last_unit_size = 5  # larger than any allowed unit (h=4,m=3,s=1,ms=0)
    seen_units: set[str] = set()
    total_seconds = 0.0

    while i < len(stripped):
        # ---- parse number ----
        num_start = i
        has_digit_before = False
        while i < len(stripped) and stripped[i].isdigit():
            has_digit_before = True
            i += 1

        # optional fractional part
        if i < len(stripped) and stripped[i] == '.':
            i += 1  # skip dot
            has_digit_after = False
            while i < len(stripped) and stripped[i].isdigit():
                has_digit_after = True
                i += 1
            if not has_digit_after:
                raise ValueError("fractional part must contain at least one digit")
            # trailing dot is not allowed – we already consumed the dot,
            # and we require at least one digit after it, so "5." is rejected.
        elif not has_digit_before:
            raise ValueError("number must contain at least one digit")

        num_str = stripped[num_start:i]
        if not num_str or num_str == ".":
            raise ValueError("invalid number format")

        # ---- parse unit ----
        if i >= len(stripped):
            raise ValueError("number without unit")

        unit = stripped[i]
        if unit == "m" and i + 1 < len(stripped) and stripped[i + 1] == "s":
            unit = "ms"
            i += 2
        else:
            i += 1

        if unit not in ("h", "m", "s", "ms"):
            raise ValueError(f"invalid unit '{unit}'")

        # each unit may appear at most once
        if unit in seen_units:
            raise ValueError(f"repeated unit '{unit}'")
        seen_units.add(unit)

        # units must be in strictly descending order
        unit_size = {"h": 4, "m": 3, "s": 1, "ms": 0}[unit]
        if unit_size >= last_unit_size:
            raise ValueError("units must be in strictly descending order")
        last_unit_size = unit_size

        # convert to seconds
        value = float(num_str)
        if unit == "h":
            total_seconds += value * 3600
        elif unit == "m":
            total_seconds += value * 60
        elif unit == "s":
            total_seconds += value
        elif unit == "ms":
            total_seconds += value / 1000.0

    if negative:
        total_seconds = -total_seconds

    return total_seconds


if __name__ == "__main__":
    import doctest
    doctest.testmod()
