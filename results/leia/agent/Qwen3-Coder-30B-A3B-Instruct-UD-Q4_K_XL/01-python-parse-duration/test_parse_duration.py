from parse_duration import parse_duration

# Test cases from the problem
test_cases = [
    ("90s", 90.0),
    ("1h30m", 5400.0),
    ("1.5h", 5400.0),
    ("2h15m30s500ms", 8130.5),
    ("250ms", 0.25),
    (" -45m ", -2700.0),
    ("1m1h", ValueError),  # wrong order
    ("1h1h", ValueError),  # repeated unit
    ("", ValueError),      # empty string
    ("5", ValueError),     # missing unit
]

print("Testing parse_duration function:")
for i, (input_text, expected) in enumerate(test_cases):
    try:
        result = parse_duration(input_text)
        if expected == ValueError:
            print(f"Test {i+1}: FAIL - Expected ValueError but got {result}")
        elif result == expected:
            print(f"Test {i+1}: PASS - {input_text} -> {result}")
        else:
            print(f"Test {i+1}: FAIL - Expected {expected} but got {result}")
    except ValueError as e:
        if expected == ValueError:
            print(f"Test {i+1}: PASS - {input_text} -> ValueError (as expected)")
        else:
            print(f"Test {i+1}: FAIL - Expected {expected} but got ValueError: {e}")
    except Exception as e:
        print(f"Test {i+1}: ERROR - {input_text} -> Unexpected error: {e}")
