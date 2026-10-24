import re

_PATTERN = re.compile(
    r"^(-?)"
    r"(?:([0-9]+(?:\.[0-9]+)?)h)?"
    r"(?:([0-9]+(?:\.[0-9]+)?)m)?"
    r"(?:([0-9]+(?:\.[0-9]+)?)s)?"
    r"(?:([0-9]+(?:\.[0-9]+)?)ms)?$"
)


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")

    stripped = text.strip()
    match = _PATTERN.fullmatch(stripped)
    if match is None:
        raise ValueError(f"Invalid duration string: {text!r}")

    sign, hours, minutes, seconds, milliseconds = match.groups()
    if hours is None and minutes is None and seconds is None and milliseconds is None:
        raise ValueError(f"Invalid duration string: {text!r}")

    total = 0.0
    if hours is not None:
        total += float(hours) * 3600.0
    if minutes is not None:
        total += float(minutes) * 60.0
    if seconds is not None:
        total += float(seconds)
    if milliseconds is not None:
        total += float(milliseconds) / 1000.0

    return -total if sign == "-" else total
