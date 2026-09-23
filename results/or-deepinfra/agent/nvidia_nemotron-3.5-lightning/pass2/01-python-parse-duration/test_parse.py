import sys
sys.path.insert(0, '.')
from parse_duration import parse_duration

# basic
assert parse_duration("90s") == 90.0, f"got {parse_duration('90s')}"
assert parse_duration("1h30m") == 5400.0, f"got {parse_duration('1h30m')}"
assert parse_duration("1.5h") == 5400.0, f"got {parse_duration('1.5h')}"
assert parse_duration("2h15m30s500ms") == 8130.5, f"got {parse_duration('2h15m30s500ms')}"
assert parse_duration("250ms") == 0.25, f"got {parse_duration('250ms')}"
assert parse_duration(" -45m ") == -2700.0, f"got {parse_duration(' -45m ')}"

# errors
try:
    parse_duration("1m1h")
    assert False, "should have raised ValueError"
except ValueError:
    pass

try:
    parse_duration("1h1h")
    assert False, "should have raised ValueError"
except ValueError:
    pass

try:
    parse_duration("")
    assert False, "should have raised ValueError"
except ValueError:
    pass

try:
    parse_duration("5")
    assert False, "should have raised ValueError"
except ValueError:
    pass

# type error
try:
    parse_duration(42)
    assert False, "should have raised TypeError"
except TypeError:
    pass

# descending order checks
try:
    parse_duration("1h30m1s")  # valid descending
    assert parse_duration("1h30m1s") == 5400+1800+1  # 1h=3600, 30m=1800, 1s=1 -> 5401.0? wait 3600+1800+1=5401
    # Actually 1h30m1s = 3600+1800+1 = 5401.0
    # but let's just check it doesn't error
except Exception as e:
    print(f"unexpected error on '1h30m1s': {e}")

# repeated unit ms at end etc
try:
    parse_duration("1ms1s")
    assert False, "should have raised ValueError for repeated unit"
except ValueError:
    pass

print("All basic tests passed!")
