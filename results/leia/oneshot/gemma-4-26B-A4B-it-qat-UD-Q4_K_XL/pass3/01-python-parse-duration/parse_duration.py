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
    
    # Pattern for a single component: digits (optional .digits) followed by unit
    # Note: We must ensure the number part follows the strict rules:
    # No bare '.', no trailing '.', no exponents.
    component_pattern = re.compile(r'^(\d+(\.\d+)?)(h|m|s|ms)$')
    
    # To ensure no invalid characters exist between components, 
    # we will find all matches and check if they consume the whole string.
    
    # However, a more robust way is to use finditer and check if the 
    # concatenated matches equal the original string.
    
    matches = list(re.finditer(r'(\d+(\.\d+)?)(h|m|s|ms)', text))
    
    if not matches:
        raise ValueError("No valid components found")

    # Check if the matches cover the entire string exactly (no extra chars/spaces)
    # and ensure no invalid characters were skipped.
    current_pos = 0
    total_seconds = 0.0
    seen_units = []
    unit_order = {'h': 3600.0, 'm': 60.0, 's': 1.0, 'ms': 0.001}
    # Order of units for descending check
    unit_rank = {'h': 4, 'm': 3, 's': 2, 'ms': 1}

    for match in matches:
        # If there is a gap between matches, it's invalid (e.g., "1h 30m" or "1h-30m")
        if match.start() != current_pos:
            raise ValueError("Invalid characters or whitespace between components")
        
        num_str = match.group(1)
        unit_str = match.group(3)
        
        # Validate number format strictly (regex handles most, but let's be safe)
        # The regex \d+(\.\d+)? already prevents "5." or ".5" or "5.5.5"
        try:
            val = float(num_str)
        except ValueError:
            raise ValueError(f"Invalid number format: {num_str}")

        # Check unit order and repetition
        if unit_str in seen_units:
            raise ValueError(f"Repeated unit: {unit_str}")
        
        if seen_units:
            last_unit = seen_units[-1]
            if unit_rank[unit_str] >= unit_rank[last_unit]:
                raise ValueError(f"Units must be in descending order: {last_unit} before {unit_str}")

        total_seconds += val * unit_order[unit_str]
        seen_units.append(unit_str)
        current_pos = match.end()

    # If we didn't reach the end of the string, there's trailing garbage
    if current_pos != len(text):
        raise ValueError("Invalid characters at end of string")

    return total_seconds * sign
