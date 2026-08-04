import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds.
    
    Supported units: h (hours), m (minutes), s (seconds), ms (milliseconds).
    Units must be in descending order and appear at most once.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")

    # Check for leading sign
    sign = 1.0
    if text.startswith('-'):
        sign = -1.0
        text = text[1:]
    elif text.startswith('+'):
        # Rule 1: No leading '+' allowed
        raise ValueError("Leading '+' is not allowed")

    # Regex to capture components: (number)(unit)
    # Number: digits, optional dot followed by digits
    # Unit: h, m, s, or ms
    # We use a lookahead/lookbehind approach or simply find all matches and 
    # validate the structure manually to ensure no invalid characters exist.
    
    # Pattern for a single component: digits(.digits)? followed by unit
    # Note: We must ensure the number part follows the strict rules:
    # No bare '.', no trailing '.', no exponents.
    component_pattern = re.compile(r'^(\d+(\.\d+)?)(h|m|s|ms)$')
    
    # To ensure no invalid characters and correct structure, we'll split the string
    # into potential components. Since units are fixed, we can use regex to find them.
    # However, a more robust way is to find all matches and check if they consume the whole string.
    
    matches = []
    current_pos = 0
    
    # We use a regex that finds valid components
    # We must ensure that the components are contiguous and cover the whole string
    # We'll use finditer to find all valid components
    pattern = re.compile(r'(\d+(\.\d+)?)(h|m|s|ms)')
    
    # Find all matches
    all_matches = list(pattern.finditer(text))
    
    if not all_matches:
        raise ValueError("No valid components found")

    # Check if the matches cover the entire string without gaps or invalid chars
    # (e.g., "1h 30m" or "1h-30m" should fail)
    last_end = 0
    for match in all_matches:
        if match.start() != last_end:
            raise ValueError("Invalid characters or whitespace between components")
        last_end = match.end()
    
    if last_end != len(text):
        raise ValueError("Trailing invalid characters")

    # Unit conversion factors to seconds
    units_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Order of units allowed (descending)
    unit_order = ['h', 'm', 's', 'ms']
    seen_units = []
    total_seconds = 0.0

    for match in all_matches:
        val_str = match.group(1)
        unit_str = match.group(3)
        
        # Validate number format (already partially handled by regex, 
        # but regex \d+(\.\d+)? handles the "no trailing dot" and "no bare dot" rules)
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {val_str}")

        # Rule 2: Units must be in strictly descending order
        if unit_str in seen_units:
            raise ValueError(f"Repeated unit: {unit_str}")
        
        if seen_units:
            last_unit = seen_units[-1]
            if unit_order.index(unit_str) <= unit_order.index(last_unit):
                raise ValueError(f"Units out of order: {last_unit} before {unit_str}")
        
        seen_units.append(unit_str)
        total_seconds += val * units_map[unit_str]

    return total_seconds * sign
