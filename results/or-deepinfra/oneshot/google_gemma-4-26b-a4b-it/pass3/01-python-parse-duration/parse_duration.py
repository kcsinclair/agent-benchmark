import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    text = text.strip()
    if not text:
        raise ValueError("Empty duration string")

    # Check for sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
    elif text.startswith('+'):
        # Rule 1: No leading '+'
        raise ValueError("Leading '+' is not allowed")

    if not text:
        raise ValueError("No components found after sign")

    # Regex explanation:
    # (\d+(?:\.\d+)?) : Captures a non-negative decimal (digits, optional dot and digits)
    # (h|m|s|ms)      : Captures the unit
    # The pattern ensures we don't match bare '.' or trailing '.' via the \d+ requirement
    pattern = re.compile(r'^(\d+(?:\.\d+)?)(h|m|s|ms)$')
    
    # We need to split the string into components. 
    # Since components are concatenated, we find all matches and check if they cover the whole string.
    # However, a simpler way is to use findall and then verify the reconstructed string matches the input.
    
    # Find all components using a regex that looks for number+unit pairs
    # We use a lookahead/lookbehind approach or simply find all matches and check continuity.
    # Let's use finditer to ensure we can validate the sequence.
    
    components = []
    current_pos = 0
    
    # Unit multipliers to seconds
    multipliers = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Order of units for validation
    unit_order = ['h', 'm', 's', 'ms']
    last_unit_index = -1

    # We use a regex to find all valid components
    # We must ensure there are no gaps or invalid characters between components
    # We'll iterate through the string manually or use a regex that matches the whole string structure
    
    # This regex matches the entire string as a sequence of (number)(unit)
    # We use a non-capturing group for the repetition
    full_pattern = re.compile(r'^((?:\d+(?:\.\d+)?(?:h|m|s|ms))+)$')
    match_full = full_pattern.match(text)
    
    if not match_full:
        raise ValueError("Invalid duration format or invalid characters")

    # Now parse the individual components from the validated string
    # We use findall on the validated text
    component_matches = re.findall(r'(\d+(?:\.\d+)?)(h|m|s|ms)', text)
    
    # Check if the number of characters consumed matches the text length
    # (This handles cases like "1h.5m" which the regex might partially match)
    reconstructed = ""
    for val, unit in component_matches:
        reconstructed += val + unit
    if reconstructed != text:
        raise ValueError("Invalid component structure")

    total_seconds = 0.0
    
    for val_str, unit in component_matches:
        # Rule 1: Validate number format (already partially handled by regex, 
        # but we ensure no weirdness like '0..5')
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Invalid number: {val_str}")

        # Rule 2: Strictly descending order and no repeats
        current_unit_index = unit_order.index(unit)
        if current_unit_index <= last_unit_index:
            raise ValueError(f"Units must be in descending order and unique: {unit}")
        
        last_unit_index = current_unit_index
        total_seconds += val * multipliers[unit]

    if is_negative:
        total_seconds = -total_seconds

    return total_seconds
