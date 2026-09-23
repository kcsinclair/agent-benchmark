from __future__ import annotations


def parse_duration(text: str) -> float:
    """Parse a human‑readable duration string and return the total seconds as a float.

    Supported units: h (hours), m (minutes), s (seconds), ms (milliseconds).
    Rules:
      * Optional leading minus sign for negation.
      * Numbers are non‑negative decimals (digits with optional fractional part).
      * Units must appear in strictly descending order: h > m > s > ms.
      * Each unit may appear at most once.
      * At least one component is required.
      * Whitespace is only allowed leading/trailing (stripped); elsewhere it is invalid.
      * Violations raise ValueError; non‑string input raises TypeError.
    """
    if not isinstance(text, str):
        raise TypeError("duration must be a string")

    s = text.strip()

    if not s:
        raise ValueError("duration string is empty")

    # Check for a leading minus sign
    negative = False
    if s[0] == "-":
        negative = True
        s = s[1:].strip()
        if not s:
            raise ValueError("duration string is empty after minus sign")

    if not isinstance(s, str):
        raise TypeError("duration must be a string")

    # Component regex: one or more digits, optional fractional part (.digits)
    # No leading +, no exponent, no bare . or .5, no trailing dot.
    # Pattern: \d+(\.\d+)?  but we must also reject things like "5." or ".5"
    # The regex \d+(\.\d+)? covers valid numbers like 2, 1.5, 0.25 and rejects 5., .5

    import re

    # Pattern for a single component: number followed by unit
    # Unit can be ms, s, m, h
    component_pat = re.compile(r'^(\d+(?:\.\d+)?) (ms|m|s|h)$')  # spaced – not our case
    # Actually components are concatenated with no separator, so we need to
    # extract number+unit pairs from the string.

    # We'll use a pattern that matches <number><unit> repeatedly.
    pair_pat = re.compile(r'(\d+(?:\.\d+)?)(ms|m|s|h)')

    # But we also need to enforce descending order and no repeats.
    # Let's find all matches and check coverage.
    remaining = s
    components = []  # list of (value_in_seconds, unit)

    # To enforce order, we track the expected maximum unit index.
    # Index: h=0, m=1, s=2, ms=3
    max_unit_idx = 4  # start with highest possible

    # We'll scan left‑to‑right, repeatedly matching the next component.
    # Because units must be descending, after we consume a unit we set
    # the max allowed index to that unit's index.
    pos = 0
    n = len(remaining)

    while pos < n:
        match = pair_pat.match(remaining, pos)
        if not match:
            raise ValueError(f"invalid duration component at position {pos}")
        num_str = match.group(1)
        unit = match.group(2)

        # Validate the number format: no trailing dot, no leading +, etc.
        # \d+(?:\.\d+)? already ensures at least one digit before dot and
        # at least one digit after dot if dot present.
        # However we must also reject things like "00" leading zeros? Not required,
        # but we accept them.

        # Convert to float
        try:
            num = float(num_str)
        except ValueError:
            raise ValueError(f"invalid number '{num_str}'")

        # Check unit order
        unit_idx = {"h": 0, "m": 1, "s": 2, "ms": 3}.get(unit)
        if unit_idx is None:
            raise ValueError(f"unknown unit '{unit}'")
        if unit_idx >= max_unit_idx:
            raise ValueError(
                f"unit '{unit}' cannot appear after '{['h','m','s','ms'][max_unit_idx-1]}'"
            )
        max_unit_idx = unit_idx

        # Check repeated unit (we will detect later by also tracking seen units)
        # Store for now
        components.append((num, unit_idx, unit))

        # Move position past this match
        pos = match.end()

    # After loop, ensure we consumed the whole string (pos should be n)
    if pos != n:
        raise ValueError("invalid characters in duration string")

    # Check that each unit appears at most once
    seen_units = set()
    for _, unit_idx, unit in components:
        if unit in seen_units:
            raise ValueError(f"repeated unit '{unit}'")
        seen_units.add(unit)

    # Compute total seconds
    total = 0.0
    for num, unit_idx, unit in components:
        if unit_idx == 0:   # h
            total += num * 3600
        elif unit_idx == 1: # m
            total += num * 60
        elif unit_idx == 2: # s
            total += num
        elif unit_idx == 3: # ms
            total += num / 1000.0

    if negative:
        total = -total

    return total
