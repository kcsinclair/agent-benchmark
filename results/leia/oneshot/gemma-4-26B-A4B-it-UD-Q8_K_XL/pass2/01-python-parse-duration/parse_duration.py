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
    # We use a non-capturing group for the decimal part to keep it clean.
    comp_regex = re.compile(r'(\d+(?:\.\d+)?)(h|m|s|ms)')
    
    # First, validate that the string contains ONLY valid components and no spaces
    # We can do this by checking if the concatenated components match the original text.
    
    # However, the rule "No bare . or .5" and "No trailing dot" is strictly handled 
    # by the regex \d+(?:\.\d+)? which requires a digit before and after the dot.
    
    # Let's find all matches
    matches = list(comp_regex.finditer(text))
    
    if not matches:
        raise ValueError("No valid components found")

    # Check if the matches perfectly reconstruct the string (no extra chars/spaces)
    reconstructed = "".join(m.group(0) for m in matches)
    if reconstructed != text:
        raise ValueError("Invalid characters or whitespace in duration string")

    # Unit order and uniqueness
    unit_order = {'h': 3, 'm': 2, 's': 1, 'ms': 0}
    last_rank = 4 # Higher than any unit rank
    
    total_seconds = 0.0
    seen_units = set()

    for m in matches:
        val_str, unit = m.groups()
        
        # Rule 1: Validate number format (already partially handled by regex)
        # The regex \d+(?:\.\d+)? ensures:
        # - No leading . (must start with digit)
        # - No trailing . (must end with digit if dot is present)
        # - No exponents
        try:
            val = float(val_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {val_str}")

        # Rule 2: Strictly descending order and uniqueness
        current_rank = unit_order[unit]
        if unit in seen_units:
            raise ValueError(f"Repeated unit: {unit}")
        if current_rank >= last_rank:
            raise ValueError(f"Units out of order: {unit}")
        
        seen_units.add(unit)
        last_rank = current_rank

        # Convert to seconds
        if unit == 'h':
            total_seconds += val * 3600
        elif unit == 'm':
            total_seconds += val * 60
        elif unit == 's':
            total_seconds += val
        elif unit == 'ms':
            total_seconds += val / 1000.0

    if is_negative:
        total_seconds = -total_seconds

    return total_seconds
