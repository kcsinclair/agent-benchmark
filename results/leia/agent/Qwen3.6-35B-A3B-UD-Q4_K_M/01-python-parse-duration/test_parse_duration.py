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
error_tests = [
    ("1m1h", ValueError),
    ("1h1h", ValueError),
    ("", ValueError),
    ("5", ValueError),
]

for text, expected_error in error_tests:
    try:
        result = parse_duration(text)
        print(f"FAIL: parse_duration({text!r}) should have raised {expected_error.__name__}, got {result}")
    except expected_error:
        print(f"PASS: parse_duration({text!r}) raised {expected_error.__name__}")
    except Exception as e:
        print(f"FAIL: parse_duration({text!r}) raised {type(e).__name__} instead of {expected_error.__name__}")

# Test TypeError
try:
    parse_duration(123)
    print("FAIL: parse_duration(123) should have raised TypeError")
except TypeError:
    print("PASS: parse_duration(123) raised TypeError")
except Exception as e:
    print(f"FAIL: parse_duration(123) raised {type(e).__name__} instead of TypeError")
