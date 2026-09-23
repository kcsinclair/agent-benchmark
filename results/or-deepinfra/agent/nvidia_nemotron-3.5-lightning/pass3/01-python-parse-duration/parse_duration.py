from __future__ import annotations


def parse_duration(text: str) -> float:
    """Parse a human‑readable duration string and return the total seconds as a float.

    Rules
    -----
    * Optional leading ``-`` to negate the result.
    * Components are ``<number><unit>`` with unit one of ``h``, ``m``, ``s``, ``ms``.
    * Numbers are non‑negative decimals (digits with optional fractional part).
    * Units must appear in strictly descending order: ``h`` > ``m`` > ``s`` > ``ms``.
    * Each unit may appear at most once.
    * At least one component is required.
    * Whitespace is only allowed leading/trailing (stripped); elsewhere it is invalid.
    * Anything that violates the rules raises ``ValueError``.
    * Passing a non‑string raises ``TypeError``.
    """
    if not isinstance(text, str):
        raise TypeError("duration must be a string")

    # Strip leading/trailing whitespace
    stripped = text.strip()
    if not stripped:
        raise ValueError("duration string is empty after stripping whitespace")

    # Check for internal whitespace
    if any(ch.isspace() for ch in stripped):
        raise ValueError("whitespace found inside duration string")

    # Check for a leading minus sign
    negative = False
    if stripped[0] == "-":
        negative = True
        stripped = stripped[1:]
        if not stripped:
            raise ValueError("minus sign with no duration after it")

    # ------------------------------------------------------------------
    # Parse components
    # ------------------------------------------------------------------
    # Mapping unit -> seconds multiplier
    unit_multiplier = {
        "h": 3600.0,
        "m": 60.0,
        "s": 1.0,
        "ms": 0.001,
    }

    # Order of units for descending‑check
    unit_order = ["h", "m", "s", "ms"]

    # We'll walk through the string manually.
    i = 0
    n = len(stripped)

    # Storage for found units and accumulated seconds
    found_units = {}          # unit -> parsed number (float)
    prev_unit_rank = 999      # rank of the previous unit; used for descending order

    while i < n:
        # ---- parse the number ----
        # A number must start with at least one digit.
        if not stripped[i].isdigit():
            raise ValueError(f"expected a number at position {i}, got '{stripped[i]}'")

        # Collect integer part
        start = i
        while i < n and stripped[i].isdigit():
            i += 1

        # Optional fractional part
        if i < n and stripped[i] == ".":
            i += 1
            # Fractional part must have at least one digit and no trailing dot
            frac_start = i
            while i < n and stripped[i].isdigit():
                i += 1
            if i == frac_start:          # no digits after the dot
                raise ValueError(f"invalid number at position {start}: fractional part missing")
        else:
            # Ensure we didn't end with a dot (handled by the check above, but be safe)
            pass

        num_str = stripped[start:i]
        try:
            value = float(num_str)
        except ValueError:
            raise ValueError(f"cannot parse number '{num_str}'")

        # ---- parse the unit ----
        if i >= n:
            raise ValueError(f"number at position {start} has no unit")

        unit = stripped[i]
        i += 1

        # Handle "ms" (two‑character unit)
        if unit == "m" and i < n and stripped[i] == "s":
            unit = "ms"
            i += 1
        # After reading "ms", we must not have another 's' unit later.

        if unit not in unit_multiplier:
            raise ValueError(f"unknown unit '{unit}' at position {i - 1}")

        # ---- descending order & uniqueness check ----
        rank = unit_order.index(unit)   # 0=h, 1=m, 2=s, 3=ms
        if rank >= prev_unit_rank:
            raise ValueError(
                f"units must be in strictly descending order; "
                f"previous unit rank was {prev_unit_rank}, got {unit} (rank {rank})"
            )
        if unit in found_units:
            raise ValueError(f"unit '{unit}' appears more than once")

        found_units[unit] = value
        prev_unit_rank = rank

    # ------------------------------------------------------------------
    # At least one component required – already guaranteed by the loop,
    # but guard against edge cases.
    # ------------------------------------------------------------------
    if not found_units:
        raise ValueError("no components found")

    # Compute total seconds
    total = 0.0
    for unit, num in found_units.items():
        total += num * unit_multiplier[unit]

    if negative:
        total = -total

    return total
