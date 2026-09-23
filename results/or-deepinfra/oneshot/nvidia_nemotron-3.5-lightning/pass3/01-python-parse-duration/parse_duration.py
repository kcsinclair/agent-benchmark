# parse_duration.py

import re
from typing import Tuple


def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds.

    Raises:
        TypeError if *text* is not a string.
    Raises ValueError if the string does not conform to the format rules.

    Supported units (in descending order of size):
        h  -> hours
        m  -> minutes
        s  -> seconds
        ms -> milliseconds
    """
    if not isinstance(text, str):
        raise TypeError("duration must be a string")

    # Strip leading/trailing whitespace; internal whitespace is not allowed
    stripped = text.strip()
    if stripped != text:
        raise ValueError("leading or trailing whitespace is not allowed")

    if not stripped:
        raise ValueError("empty duration string")

    # Tokenise: a number (digits with optional fractional part) followed by a unit
    # Pattern explanation:
    #   (\d+(?:\.\d+)?)   – one or more digits, optionally followed by a dot and
    #                      one or more digits (e.g. 2, 1.5, 0.25). Rejects "5.", ".5", etc.
    #   (h|m|s|ms)       – one of the allowed units
    token_pattern = r"(\d+(?:\.\d+)?)(h|m|s|ms)"
    tokens = re.findall(token_pattern, stripped)

    # Rule 3: at least one component is required
    if not tokens:
        raise ValueError("no valid components found")

    # Reject any leftover characters that were not part of a valid token
    # Build the expected concatenation from the tokens and compare
    expected = "".join(num + unit for num, unit in tokens)
    if expected != stripped:
        raise ValueError("invalid characters in duration string")

    # Rule 2: units must appear in strictly descending order and at most once
    seen_units = set()
    prev_multiplier = None  # multiplier of the previous unit (h=3600, m=60, s=1, ms=0.001)

    # Multipliers for each unit in seconds per unit
    multipliers = {"h": 3600, "m": 60, "s": 1, "ms": 0.001}

    for num_str, unit in tokens:
        # Rule 2: each unit may appear at most once
        if unit in seen_units:
            raise ValueError(f"repeated unit '{unit}'")
        seen_units.add(unit)

        # Enforce descending order
        cur_multiplier = multipliers[unit]
        if prev_multiplier is not None and cur_multiplier > prev_multiplier:
            raise ValueError("units not in strictly descending order")
        prev_multiplier = cur_multiplier

        # Convert the number part to float
        try:
            value = float(num_str)
        except ValueError:
            # Should not happen because the regex already guarantees a valid
            # decimal format, but we keep it as a safety net.
            raise ValueError(f"invalid number '{num_str}'")

        # Accumulate total seconds
        #   value * (seconds per unit)
        #   e.g. "1.5h" -> 1.5 * 3600 = 5400.0
        #        "500ms" -> 500 * 0.001 = 0.5
        total_seconds = value * cur_multiplier  # we will sum later

        # Store for later summation to avoid floating‑point accumulation order issues
        # (though simple addition works fine for these small values)
        # We'll just accumulate into a running total.
        # To keep it simple, we accumulate here.
        # But we need the running total, so we keep a variable outside the loop.
        # We'll restructure slightly.

    # The loop above set up validation but didn't accumulate.
    # Re-iterate to compute the total.
    total = 0.0
    prev_multiplier = None
    for num_str, unit in tokens:
        cur_multiplier = multipliers[unit]
        if prev_multiplier is not None and cur_multiplier > prev_multiplier:
            # This should never pass because we already checked order,
            # but keep as a safety net.
            raise ValueError("units not in strictly descending order")
        value = float(num_str)
        total += value * cur_multiplier
        prev_multiplier = cur_multiplier

    # Rule 4: a leading minus sign negates the whole duration
    # The minus sign, if present, must be the very first character of the stripped string.
    if stripped[0] == "-":
        total = -total

    return total
