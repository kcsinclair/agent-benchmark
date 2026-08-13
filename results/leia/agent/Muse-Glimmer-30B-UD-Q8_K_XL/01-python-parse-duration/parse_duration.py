def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("text must be a str")

    s = text.strip()
    if not s:
        raise ValueError("empty duration")

    # No internal whitespace allowed
    if any(c.isspace() for c in s):
        raise ValueError("whitespace inside duration")

    sign = 1
    if s[0] == '-':
        sign = -1
        s = s[1:]
        if not s:
            raise ValueError("missing duration after sign")
    if s[0] == '+':
        raise ValueError("leading + not allowed")
    if '-' in s:
        raise ValueError("minus sign only allowed at start")

    rank_map = {'h': 3, 'm': 2, 's': 1, 'ms': 0}
    seconds_per = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}

    n = len(s)
    i = 0
    total = 0.0
    prev_rank = None
    seen = set()

    while i < n:
        # parse number
        if not s[i].isdigit():
            raise ValueError(f"expected digit at position {i}")
        start_num = i
        while i < n and s[i].isdigit():
            i += 1
        # optional fractional part
        if i < n and s[i] == '.':
            i += 1
            if i >= n or not s[i].isdigit():
                raise ValueError("invalid fractional part")
            while i < n and s[i].isdigit():
                i += 1
        num_str = s[start_num:i]
        if i >= n:
            raise ValueError("missing unit after number")

        # parse unit, ms must be checked before m
        if s.startswith('ms', i):
            unit = 'ms'
            i += 2
        elif s[i] == 'h':
            unit = 'h'
            i += 1
        elif s[i] == 'm':
            unit = 'm'
            i += 1
        elif s[i] == 's':
            unit = 's'
            i += 1
        else:
            raise ValueError(f"invalid unit at position {i}")

        if unit in seen:
            raise ValueError(f"duplicate unit {unit}")
        seen.add(unit)

        rank = rank_map[unit]
        if prev_rank is not None and rank >= prev_rank:
            raise ValueError("units not in strictly descending order")
        prev_rank = rank

        try:
            num = float(num_str)
        except ValueError:
            raise ValueError("invalid number")

        total += num * seconds_per[unit]

    if not seen:
        raise ValueError("no components found")
    if i != n:
        raise ValueError("trailing characters")

    return sign * total
