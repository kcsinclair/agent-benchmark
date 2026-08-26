"""Test the parse_duration function."""

from parse_duration import parse_duration

# Test cases from the problem
tests = [
    ("90s", 90.0),
    ("1h30m", 5400.0),
    ("1.5h", 5400.0),
    ("2h15m30s500ms", 8130.5),
    ("250ms", 0.25),
    (" -45m ", -2700.0),
]

print("Testing valid cases:")
for text, expected in tests:
    result = parse_duration(text)
    status = "PASS" if result == expected else "FAIL"
    print(f"  {status} parse_duration({text!r}) = {result} (expected {expected})")

# Test error cases
error_cases = [
    ("1m1h", "wrong order"),
    ("1h1h", "repeated unit"),
    ("", "empty string"),
    ("5", "missing unit"),
]

print("\nTesting error cases:")
for text, reason in error_cases:
    try:
        result = parse_duration(text)
        print(f"  FAIL parse_duration({text!r}) = {result} (expected ValueError for: {reason})")
    except ValueError as e:
        print(f"  PASS parse_duration({text!r}) raised ValueError: {e}")
    except Exception as e:
        print(f"  FAIL parse_duration({text!r}) raised {type(e).__name__}: {e}")

# Test TypeError
print("\nTesting TypeError:")
try:
    parse_duration(123)
    print("  FAIL parse_duration(123) did not raise TypeError")
except TypeError as e:
    print(f"  PASS parse_duration(123) raised TypeError: {e}")

# Additional edge cases
print("\nAdditional tests:")
additional = [
    ("0s", 0.0),
    ("0h0m0s0ms", 0.0),
    ("1ms", 0.001),
    ("1h", 3600.0),
    ("1m", 60.0),
    ("1s", 1.0),
    ("0.5s", 0.5),
    ("0.001s", 0.001),
]

for text, expected in additional:
    result = parse_duration(text)
    status = "PASS" if result == expected else "FAIL"
    print(f"  {status} parse_duration({text!r}) = {result} (expected {expected})")

# More error cases
print("\nMore error cases:")
more_errors = [
    ("1h 30m", "internal whitespace"),
    ("+1h", "leading plus"),
    (".5h", "bare dot"),
    ("5.h", "trailing dot"),
    ("1h2h", "repeated unit"),
    ("1s1m", "wrong order"),
    ("1ms1s", "wrong order"),
]

for text, reason in more_errors:
    try:
        result = parse_duration(text)
        print(f"  FAIL parse_duration({text!r}) = {result} (expected ValueError for: {reason})")
    except ValueError as e:
        print(f"  PASS parse_duration({text!r}) raised ValueError: {e}")
    except Exception as e:
        print(f"  FAIL parse_duration({text!r}) raised {type(e).__name__}: {e}")
