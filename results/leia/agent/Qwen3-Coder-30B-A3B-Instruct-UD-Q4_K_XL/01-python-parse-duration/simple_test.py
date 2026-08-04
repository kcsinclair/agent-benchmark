from parse_duration import parse_duration

# Test a few key cases
test_cases = [
    ("90s", 90.0),
    ("1h30m", 5400.0),
    ("2h15m30s500ms", 8130.5),
    (" -45m ", -2700.0),
]

for text, expected in test_cases:
    try:
        result = parse_duration(text)
        print(f"{text} -> {result} (expected {expected}) {'✓' if result == expected else '✗'}")
    except Exception as e:
        print(f"{text} -> Error: {e}")
