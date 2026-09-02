import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # 1. Strip leading/trailing whitespace
    s = text.strip()
    if not s:
        raise ValueError("Empty duration string")

    # 2. Handle sign
    multiplier = 1.0
    if s.startswith('-'):
        multiplier = -1.0
        s = s[1:]
    elif s.startswith('+'):
        # Rule 1: No leading '+' allowed
        raise ValueError("Leading '+' is not allowed")

    if not s:
        raise ValueError("No components found after sign")

    # 3. Define units and their conversion to seconds
    # Order is important for validation: h, m, s, ms
    units_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    unit_order = ['h', 'm', 's', 'ms']

    # 4. Regex to find components
    # Pattern: (digits + optional . + digits) followed by (unit)
    # We use a lookahead to ensure we don't consume the whole string if it's invalid
    # but for strictness, we will find all matches and then check if they cover the whole string.
    # Component pattern: (\d+(?:\.\d+)?) followed by (h|m|s|ms)
    pattern = r'^(\d+(?:\.\d+)?)(h|m|s|ms)'
    
    total_seconds = 0.0
    last_unit_index = -1
    consumed_length = 0
    
    # We iterate through the string to find components one by one
    remaining = s
    while remaining:
        match = re.match(pattern, remaining)
        if not match:
            # If the remaining string doesn't start with a valid component, it's invalid
            raise ValueError(f"Invalid component or format in: {remaining}")
        
        val_str, unit_str = match.groups()
        
        # Validate number format (Rule 1: no bare '.' or trailing '.')
        # The regex \d+(?:\.\d+)? already handles this:
        # It requires digits before and after the dot if a dot exists.
        
        # Validate unit order (Rule 2)
        current_unit_index = unit_order.index(unit_str)
        if current_unit_index <= last_unit_index:
            raise ValueError(f"Units must be in descending order and unique: {unit_str}")
        
        # Calculate value
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Invalid number: {val_str}")
            
        total_seconds += val * units_map[unit_str]
        
        # Update state
        last_unit_index = current_unit_index
        consumed_length += len(match.group(0))
        remaining = remaining[len(match.group(0)):]

    # 5. Final check: Did we consume the entire string?
    # If there's leftover text that wasn't part of a component, it's invalid.
    if consumed_length != len(s):
        raise ValueError("String contains invalid characters or malformed components")

    return total_seconds * multiplier
