"""Test parse_duration function."""
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

for text, expected in tests:
    result = parse_duration(text)
    status = "PASS" if result == expected else "FAIL"
    print(f"{status}: parse_duration({text!r}) = {result} (expected {expected})")

# Test error cases
error_cases = [
    ("1m1h", "wrong order"),
    ("1h1h", "repeated unit"),
    ("", "empty string"),
    ("5", "missing unit"),
]

for text, reason in error_cases:
    try:
        result = parse_duration(text)
        print(f"FAIL: parse_duration({text!r}) should raise ValueError ({reason}), got {result}")
    except ValueError:
        print(f"PASS: parse_duration({text!r}) raised ValueError ({reason})")

# Test TypeError
try:
    parse_duration(123)
    print("FAIL: parse_duration(123) should raise TypeError")
except TypeError:
    print("PASS: parse_duration(123) raised TypeError")

# Additional edge cases
print("\nAdditional tests:")
print(f"0s: {parse_duration('0s')}")
print(f"0.5s: {parse_duration('0.5s')}")
print(f"-0s: {parse_duration('-0s')}")
print(f"1ms: {parse_duration('1ms')}")
print(f"1h: {parse_duration('1h')}")
print(f"1m: {parse_duration('1m')}")
print(f"1s: {parse_duration('1s')}")
print(f"1h1m1s1ms: {parse_duration('1h1m1s1ms')}")

# Test invalid cases
invalid_cases = [
    ".5s",      # leading dot
    "5.s",      # trailing dot
    "1h 30m",   # internal whitespace
    "1h1m1h",   # wrong order
    "1h2h",     # repeated unit
    "1ms1s",    # wrong order (ms before s)
]

print("\nInvalid cases:")
for text in invalid_cases:
    try:
        result = parse_duration(text)
        print(f"FAIL: parse_duration({text!r}) should raise ValueError, got {result}")
    except ValueError as e:
        print(f"PASS: parse_duration({text!r}) raised ValueError: {e}")
