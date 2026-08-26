"""Duration string parser module."""


def parse_duration(text: str) -> float:
    """Parse a human-readable duration string and return total seconds as a float.
    
    Args:
        text: A duration string like "1h30m", "250ms", "-1.5h", etc.
        
    Returns:
        Total duration in seconds as a float.
        
    Raises:
        TypeError: If text is not a string.
        ValueError: If the duration string is invalid.
    """
    if not isinstance(text, str):
        raise TypeError("Expected a string")
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    # Check for empty string
    if not text:
        raise ValueError("Empty duration string")
    
    # Check for internal whitespace (after stripping)
    if ' ' in text or '\t' in text or '\n' in text or '\r' in text:
        raise ValueError("Internal whitespace is not allowed")
    
    # Determine sign
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:]
        if not text:
            raise ValueError("No components after minus sign")
    
    # Define units in descending order with their values in seconds
    # Order matters: h, m, s, ms (descending by size)
    units = [
        ('h', 3600.0),
        ('m', 60.0),
        ('s', 1.0),
        ('ms', 0.001),
    ]
    
    pos = 0
    total_seconds = 0.0
    last_unit_index = -1  # Index in units list of the last unit seen
    
    while pos < len(text):
        # Try to match a number
        # Number must start with a digit
        if pos >= len(text) or not text[pos].isdigit():
            raise ValueError(f"Expected a number at position {pos}")
        
        # Find the end of the number
        num_start = pos
        while pos < len(text) and text[pos].isdigit():
            pos += 1
        
        # Check for decimal point
        if pos < len(text) and text[pos] == '.':
            pos += 1  # skip the dot
            # Must have at least one digit after the dot
            if pos >= len(text) or not text[pos].isdigit():
                raise ValueError("Trailing dot in number")
            while pos < len(text) and text[pos].isdigit():
                pos += 1
        
        num_str = text[num_start:pos]
        
        # Parse the number
        try:
            value = float(num_str)
        except ValueError:
            raise ValueError(f"Invalid number: {num_str}")
        
        # Now expect a unit
        if pos >= len(text):
            raise ValueError("Missing unit after number")
        
        # Try to match a unit
        # We need to check "ms" before "m" to avoid partial matches
        # But we also need to maintain the order constraint
        # Strategy: check all possible units at this position, but only accept
        # ones that are in valid order
        
        unit_found = False
        for i, (unit, unit_value) in enumerate(units):
            unit_len = len(unit)
            if pos + unit_len <= len(text) and text[pos:pos+unit_len] == unit:
                # Check that the unit is complete (not followed by more letters)
                # For "ms", we need to make sure it's not "mss" or similar
                # For "m", we need to make sure it's not "ms" (which would be caught above)
                # Actually, since we check "ms" before "m" in the list... wait, no we don't
                # "m" comes before "ms" in our list
                
                # Check if this is a complete unit match
                # The next character (if any) should be a digit (start of next component)
                # or we're at the end
                next_pos = pos + unit_len
                if next_pos < len(text) and text[next_pos].isalpha():
                    # This unit is followed by more letters, so it's not a complete match
                    # For example, "m" followed by "s" means we should have matched "ms"
                    continue
                
                # Check order: this unit must come after the last unit
                if i <= last_unit_index:
                    raise ValueError(f"Units must be in descending order")
                
                last_unit_index = i
                total_seconds += value * unit_value
                pos = next_pos
                unit_found = True
                break
        
        if not unit_found:
            raise ValueError(f"Invalid unit at position {pos}")
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
