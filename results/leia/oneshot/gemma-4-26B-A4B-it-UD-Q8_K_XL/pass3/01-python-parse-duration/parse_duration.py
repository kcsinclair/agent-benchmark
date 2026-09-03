import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total seconds as a float.
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
    # Group 1: The number (digits, optional dot, digits)
    # Group 2: The unit (h, m, s, or ms)
    # We use a lookahead to ensure we don't allow trailing dots or invalid number formats
    # The pattern ensures we capture valid decimals like '1.5' but not '5.' or '.5'
    pattern = r'^(\d+(?:\.\d+)?)(h|m|s|ms)$'
    
    # To handle the "no whitespace anywhere else" and "concatenated" rules,
    # we will find all matches and ensure they consume the entire string.
    
    # We'll use a regex to find all components, but we must validate the whole string.
    # A component is a number followed by a unit.
    # We'll use finditer to extract components and check if they cover the whole string.
    
    components = []
    # This regex finds valid components: digits + optional decimal + unit
    # We use a non-greedy approach or specific structure to ensure we don't skip chars
    comp_regex = re.compile(r'(\d+(?:\.\d+)?)(h|m|s|ms)')
    
    # First, validate that the string only contains valid characters for our components
    # and that there are no spaces inside.
    if ' ' in text:
        raise ValueError("Whitespace is not allowed within the duration string")

    # We need to manually parse to ensure strict adherence to rules (order, repetition, etc.)
    # Let's find all matches and check if they are contiguous and cover the string.
    matches = list(comp_regex.finditer(text))
    
    if not matches:
        raise ValueError("No valid components found")

    # Check if the matches cover the entire string without gaps
    current_pos = 0
    for match in matches:
        if match.start() != current_pos:
            raise ValueError("Invalid format or unexpected characters")
        current_pos = match.end()
    
    if current_pos != len(text):
        raise ValueError("Invalid format or trailing characters")

    # Unit multipliers
    multipliers = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Unit order for validation (descending)
    unit_order = ['h', 'm', 's', 'ms']
    last_unit_idx = -1
    
    total_seconds = 0.0
    
    for match in matches:
        val_str, unit = match.groups()
        
        # Validate number format (Rule 1: no bare '.', no trailing '.')
        # The regex \d+(?:\.\d+)? already handles this, but we must ensure 
        # we didn't miss cases like '5.' which the regex wouldn't match fully.
        # However, since we check if matches cover the whole string, '5.h' would 
        # fail because '5.' doesn't match the number part of the regex.
        
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Invalid number: {val_str}")

        # Validate order and uniqueness (Rule 2)
        current_unit_idx = unit_order.index(unit)
        if current_unit_idx <= last_unit_idx:
            raise ValueError(f"Units must be in descending order and unique: {unit}")
        
        last_unit_idx = current_unit_idx
        total_seconds += val * multipliers[unit]

    if is_negative:
        total_seconds = -total_seconds

    return total_seconds
