import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # 5. Leading and trailing whitespace must be tolerated
    text = text.strip()

    if not text:
        raise ValueError("Empty duration string")

    # 4. Handle optional leading minus sign
    is_negative = False
    if text.startswith('-'):
        is_negative = True
        text = text[1:]
    elif text.startswith('+'):
        # Rule 1: No leading '+'
        raise ValueError("Leading '+' is not allowed")

    if not text:
        raise ValueError("No components found after sign")

    # Regex for a single component:
    # 1. Number: digits, optional dot, followed by digits. 
    #    Must have digits on both sides of dot or just digits to avoid bare '.' or '5.'
    #    Actually, the rule says: "digits with an optional fractional part (2, 1.5, 0.25). 
    #    No bare '.', no '.5', no trailing dot ('5.')"
    #    This means: [0-9]+(\.[0-9]+)?
    # 2. Unit: h, m, s, or ms
    
    # We use a regex to find all components and ensure no invalid characters exist in between.
    # The pattern captures the number and the unit.
    pattern = r'^([0-9]+(?:\.[0-9]+)?)(h|m|s|ms)$'
    
    # Since components are concatenated with no separators, we can't just use findall 
    # if there's garbage in between. We will manually slice the string.
    
    total_seconds = 0.0
    units_found = []
    unit_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    # Order for rule 2: h > m > s > ms
    unit_order = ['h', 'm', 's', 'ms']
    
    current_pos = 0
    while current_pos < len(text):
        # Try to match a component at the current position
        match = re.match(r'^([0-9]+(?:\.[0-9]+)?)(h|m|s|ms)', text[current_pos:])
        
        if not match:
            # If no match, it's either invalid number format or invalid unit or garbage
            raise ValueError("Invalid component format or missing unit")
        
        val_str, unit_str = match.groups()
        
        # Rule 1: Check for invalid number formats like ".5" or "5." 
        # (The regex [0-9]+(?:\.[0-9]+)? already handles this by requiring digits before and after dot)
        
        # Rule 2: Check for repeated units or wrong order
        if unit_str in units_found:
            raise ValueError(f"Repeated unit: {unit_str}")
        
        if units_found:
            last_unit = units_found[-1]
            if unit_order.index(unit_str) >= unit_order.index(last_unit):
                raise ValueError(f"Units must be in descending order: {last_unit} then {unit_str}")
        
        units_found.append(unit_str)
        total_seconds += float(val_str) * unit_map[unit_str]
        
        # Advance position
        current_pos += len(match.group(0))

    # Final check: if we didn't consume the whole string, there was whitespace or garbage in the middle
    if current_pos != len(text):
        raise ValueError("Invalid characters or whitespace found within duration")

    # Rule 3: At least one component is required
    if not units_found:
        raise ValueError("No components found")

    return -total_seconds if is_negative else total_seconds
