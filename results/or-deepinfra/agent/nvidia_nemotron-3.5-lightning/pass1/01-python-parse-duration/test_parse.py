import sys
sys.path.insert(0, ".")
from parse_duration import parse_duration

# Examples from the problem statement
tests = [
    ("90s", 90.0),
    ("1h30m", 5400.0),
    ("1.5h", 5400.0),
    ("2h15m30s500ms", 8130.5),
    ("250ms", 0.25),
    (" -45m ", -2700.0),
    ("1m1h", None),       # ValueError   (wrong order)
    ("1h1h", None),       # ValueError   (repeated unit)
    ("", None),           # ValueError
    ("5", None),          # ValueError   (missing unit)
]

print("=== Core examples ===")
for s, expected in tests:
    try:
        result = parse_duration(s)
        if expected is None:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected ValueError")
        elif abs(result - expected) < 1e-9:
            print(f"PASS: parse_duration({s!r}) -> {result}")
        else:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected {expected}")
    except ValueError as e:
        if expected is None:
            print(f"PASS: parse_duration({s!r}) -> ValueError as expected")
        else:
            print(f"FAIL: parse_duration({s!r}) -> ValueError({e}), expected {expected}")
    except TypeError as e:
        print(f"TYPE: parse_duration({s!r}) -> TypeError({e})")

# Additional edge cases
print("\n=== Extra tests ===")
extra = [
    ("-1h30m", -5400.0),        # negate
    ("0.5h", 1800.0),           # fractional
    ("1h0m", None),              # ascending order (0h1h would be? Actually 0h not valid but 1h0m is ascending -> error)
    ("1s1m", None),              # ascending
    ("1ms1s", None),             # ascending
    ("  1h  ", 3600.0),         # surrounding whitespace only
    ("1h 30m", None),            # internal whitespace
    ("-5", None),                # minus with no unit
    (123, None),                 # non-string input
]

for s, expected in extra:
    try:
        result = parse_duration(s)
        if expected is None:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected ValueError")
        elif abs(result - expected) < 1e-9:
            print(f"PASS: parse_duration({s!r}) -> {result}")
        else:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected {expected}")
    except ValueError as e:
        if expected is None:
            print(f"PASS: parse_duration({s!r}) -> ValueError as expected (got: {e})")
        else:
            print(f"FAIL: parse_duration({s!r}) -> ValueError({e}), expected {expected}")
    except TypeError as e:
        if expected is None:
            print(f"PASS: parse_duration({s!r}) -> TypeError as expected")
        else:
            print(f"FAIL: parse_duration({s!r}) -> TypeError({e}), expected {expected}")
