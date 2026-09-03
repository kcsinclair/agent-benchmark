import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds as a float.
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
        # Rule 1 says "No leading +" for numbers, and rule 4 says "A single leading '-'".
        # It doesn't explicitly forbid '+' for the whole string, but usually, 
        # if it's not mentioned, it's not allowed.
        raise ValueError("Invalid sign")

    if not text:
        raise ValueError("No components found after sign")

    # Units in order
    units_order = ['h', 'm', 's', 'ms']
    unit_values = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # We need to match components one by one.
    # A component is a number followed by a unit.
    # Number: \d+(\.\d+)?
    # Unit: h, m, s, or ms. 
    # Note: 'ms' must be checked before 'm' if using a simple regex, 
    # but here we are matching the unit part specifically.
    
    # To avoid 'm' matching the 'm' in 'ms', we can use a regex that 
    # looks for the longest possible unit or uses specific patterns.
    # Since we are consuming the string, we can use a regex that matches 
    # the unit part carefully.
    
    # Let's use a regex that matches the number and then the unit.
    # We'll use a lookahead or just order the units in the regex.
    comp_regex = re.compile(r'^(\d+(?:\.\d+)?)(ms|h|m|s)')
    
    current_pos = 0
    last_unit_idx = -1
    total_seconds = 0.0
    
    # We need to ensure that 'ms' is not partially matched as 'm'.
    # The regex (ms|h|m|s) handles this because 'ms' is tried first.
    
    while current_pos < len(text):
        match = comp_regex.match(text[current_pos:])
        if not match:
            raise ValueError("Invalid component or format")
        
        val_str, unit = match.groups()
        
        # Check unit order
        unit_idx = units_order.index(unit)
        if unit_idx <= last_unit_idx:
            raise ValueError("Units must be in strictly descending order and unique")
        
        last_unit_idx = unit_idx
        
        # Convert value
        val = float(val_str)
        total_seconds += val * unit_values[unit]
        
        # Advance position
        current_pos += len(match.group(0))

    if current_pos != len(text):
        raise ValueError("Invalid characters in duration string")
        
    if last_unit_idx == -1:
        raise ValueError("At least one component is required")

    return -total_seconds if is_negative else total_seconds
