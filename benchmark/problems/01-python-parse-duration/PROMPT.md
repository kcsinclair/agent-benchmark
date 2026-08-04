# Problem 1 — Duration String Parser (Python, easy)

Write a Python 3 module in a single file named `parse_duration.py` that defines one function:

```python
def parse_duration(text: str) -> float:
    ...
```

The function parses a human-readable duration string and returns the total
number of **seconds** as a `float`.

## Format

A duration string is an optional minus sign followed by one or more
*components*, concatenated with no separators. Each component is a number
followed by a unit:

| Unit | Meaning       |
|------|---------------|
| `h`  | hours         |
| `m`  | minutes       |
| `s`  | seconds       |
| `ms` | milliseconds  |

Rules:

1. Numbers are non-negative decimals: digits with an optional fractional part
   (`2`, `1.5`, `0.25`). No leading `+`, no exponents, no bare `.` or `.5`,
   and no trailing dot (`5.` is invalid).
2. Units must appear in strictly descending order of size (`h` before `m`
   before `s` before `ms`) and each unit may appear at most once.
3. At least one component is required.
4. A single leading `-` (before the first component) negates the whole
   duration: `-1h30m` is -5400.0 seconds.
5. Leading and trailing whitespace must be tolerated (stripped). Whitespace
   anywhere else is invalid.
6. Anything that violates the rules above must raise `ValueError`. Passing a
   non-string must raise `TypeError`.

## Examples

```
parse_duration("90s")            -> 90.0
parse_duration("1h30m")          -> 5400.0
parse_duration("1.5h")           -> 5400.0
parse_duration("2h15m30s500ms")  -> 8130.5
parse_duration("250ms")          -> 0.25
parse_duration(" -45m ")         -> -2700.0
parse_duration("1m1h")           -> ValueError   (wrong order)
parse_duration("1h1h")           -> ValueError   (repeated unit)
parse_duration("")               -> ValueError
parse_duration("5")              -> ValueError   (missing unit)
```

## Constraints

- Standard library only.
- The file must contain the function at module top level so it can be
  imported as `from parse_duration import parse_duration`.
- Do not print anything on import.

**Deliverable: exactly one file, `parse_duration.py`.**
