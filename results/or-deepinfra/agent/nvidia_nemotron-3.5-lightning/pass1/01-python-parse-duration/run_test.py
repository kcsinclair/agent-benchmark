import sys
sys.path.insert(0, ".")
from parse_duration import parse_duration

tests = [
    ("90s", 90.0),
    ("1h30m", 5400.0),
    ("1.5h", 5400.0),
    ("2h15m30s500ms", 8130.5),
    ("250ms", 0.25),
    (" -45m ", -2700.0),
    ("1m1h", None),
    ("1h1h", None),
    ("", None),
    ("5", None),
]

all_pass = True
for s, expected in tests:
    try:
        result = parse_duration(s)
        if expected is None:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected ValueError")
            all_pass = False
        elif abs(result - expected) < 1e-9:
            print(f"PASS: parse_duration({s!r}) -> {result}")
        else:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected {expected}")
            all_pass = False
    except ValueError as e:
        if expected is None:
            print(f"PASS: parse_duration({s!r}) -> ValueError as expected")
        else:
            print(f"FAIL: parse_duration({s!r}) -> ValueError({e}), expected {expected}")
            all_pass = False
    except TypeError as e:
        print(f"TYPE: parse_duration({s!r}) -> TypeError({e})")
        all_pass = False

extra = [
    ("-1h30m", -5400.0),
    ("0.5h", 1800.0),
    ("1h0m", None),
    ("1s1m", None),
    ("1ms1s", None),
    ("  1h  ", 3600.0),
    ("1h 30m", None),
    ("-5", None),
    (123, None),
]

for s, expected in extra:
    try:
        result = parse_duration(s)
        if expected is None:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected ValueError")
            all_pass = False
        elif abs(result - expected) < 1e-9:
            print(f"PASS: parse_duration({s!r}) -> {result}")
        else:
            print(f"FAIL: parse_duration({s!r}) -> {result}, expected {expected}")
            all_pass = False
    except ValueError as e:
        if expected is None:
            print(f"PASS: parse_duration({s!r}) -> ValueError as expected (got: {e})")
        else:
            print(f"FAIL: parse_duration({s!r}) -> ValueError({e}), expected {expected}")
            all_pass = False
    except TypeError as e:
        if expected is None:
            print(f"PASS: parse_duration({s!r}) -> TypeError as expected")
        else:
            print(f"FAIL: parse_duration({s!r}) -> TypeError({e}), expected {expected}")
            all_pass = False

print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
