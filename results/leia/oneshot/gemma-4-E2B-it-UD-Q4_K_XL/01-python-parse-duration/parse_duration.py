import re

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of seconds as a float.

    Args:
        text: The duration string to parse.

    Returns:
        The total duration in seconds as a float.

    Raises:
        TypeError: If the input is not a string.
        ValueError: If the duration string violates any parsing rules.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    # 1. Strip leading/trailing whitespace
    stripped_text = text.strip()

    if not stripped_text:
        raise ValueError("Duration string cannot be empty.")

    # Regex to capture components: (number)(unit)
    # Number pattern: digits, optional decimal point followed by digits.
    # This pattern enforces Rule 1 (no leading +, no bare ., no trailing dot)
    number_pattern = r"(\d+\.?\d*|\.\d+)"
    
    # Unit patterns
    h_pattern = r"h"
    m_pattern = r"m"
    s_pattern = r"s"
    ms_pattern = r"ms"

    # Define the structure for parsing: optional sign, followed by components
    # We use a comprehensive pattern to tokenize the string based on the allowed components.
    
    # The overall structure: [optional sign] [component1] [component2] ...
    
    # Tokenization approach: Find all valid number-unit pairs.
    # We need to handle the optional leading minus sign separately.
    
    sign = 1.0
    if stripped_text.startswith('-'):
        sign = -1.0
        stripped_text = stripped_text[1:].strip()

    # Combined pattern for all valid components: (number)(unit)
    # We use non-capturing groups for the units to simplify matching.
    component_pattern = re.compile(
        rf"({number_pattern})({h_pattern}|{m_pattern}|{s_pattern}|{ms_pattern})"
    )

    # Find all matches in the stripped string
    matches = component_pattern.findall(stripped_text)

    if not matches:
        # This handles cases like "5" or invalid formats that don't match the component structure
        raise ValueError("Invalid duration format or missing unit.")

    total_seconds = 0.0
    seen_units = set()
    
    # Check for unit ordering and calculate total
    for number_str, unit in matches:
        # Validate number format (Rule 1 check is partially done by regex, but we check for edge cases)
        try:
            value = float(number_str)
        except ValueError:
            # Should theoretically not happen if regex is perfect, but good safeguard
            raise ValueError(f"Invalid number format encountered: {number_str}")

        # Validate unit presence and ordering (Rule 2)
        if unit == 'h':
            if 'h' in seen_units:
                raise ValueError("Repeated unit 'h'.")
            seen_units.add('h')
            total_seconds += value * 3600.0
        elif unit == 'm':
            if 'm' in seen_units:
                raise ValueError("Repeated unit 'm'.")
            if 'h' in seen_units:
                # If 'h' was seen, 'm' is fine, but we must ensure order is maintained
                # The strict ordering check is better done by checking the sequence of units found.
                pass 
            seen_units.add('m')
            total_seconds += value * 60.0
        elif unit == 's':
            if 's' in seen_units:
                raise ValueError("Repeated unit 's'.")
            if 'h' in seen_units or 'm' in seen_units:
                # If we see 's' but 'h' or 'm' hasn't been seen yet, it's an ordering violation
                # This check is implicitly handled by the sequential processing below, 
                # but we must ensure the *set* of units found respects the hierarchy.
                pass
            seen_units.add('s')
            total_seconds += value
        elif unit == 'ms':
            if 'ms' in seen_units:
                raise ValueError("Repeated unit 'ms'.")
            # Check if any larger unit has been seen (Rule 2 violation)
            if 'h' in seen_units or 'm' in seen_units or 's' in seen_units:
                raise ValueError("Unit 'ms' appeared after a larger unit.")
            seen_units.add('ms')
            total_seconds += value / 1000.0
        else:
            # Should not happen due to regex, but safety net
            raise ValueError(f"Unknown unit encountered: {unit}")

    # Final check for strict descending order (Rule 2)
    # We check the sequence of units found in the original matches to ensure strict order.
    
    unit_order = ['h', 'm', 's', 'ms']
    
    # Re-extract units in order of appearance from the matches
    actual_units_found = [unit for _, unit in matches]
    
    for i in range(len(actual_units_found) - 1):
        current_unit = actual_units_found[i]
        next_unit = actual_units_found[i+1]
        
        # Find indices in the hierarchy
        current_idx = unit_order.index(current_unit)
        next_idx = unit_order.index(next_unit)
        
        if next_idx <= current_idx:
            # This catches cases like "1m1h" or "1s1m"
            raise ValueError("Units must appear in strictly descending order of size.")

    return sign * total_seconds

if __name__ == '__main__':
    # --- Examples Verification ---
    
    # Valid examples
    print(f"90s: {parse_duration('90s')}")  # Expected: 90.0
    print(f"1h30m: {parse_duration('1h30m')}")  # Expected: 5400.0
    print(f"1.5h: {parse_duration('1.5h')}")  # Expected: 5400.0
    print(f"2h15m30s500ms: {parse_duration('2h15m30s500ms')}")  # Expected: 8130.5
    print(f"250ms: {parse_duration('250ms')}")  # Expected: 0.25
    print(f" -45m : {parse_duration(' -45m ')}")  # Expected: -2700.0
    print(f"0.5h: {parse_duration('0.5h')}") # Expected: 1800.0
    print(f"1.25s: {parse_duration('1.25s')}") # Expected: 1.25
    print(f"1ms: {parse_duration('1ms')}") # Expected: 0.001
    print(f"1h1m: {parse_duration('1h1m')}") # Expected: ValueError (wrong order)
    print(f"1h1h: {parse_duration('1h1h')}") # Expected: ValueError (repeated unit)
    print(f"Empty string: {parse_duration('')}") # Expected: ValueError
    print(f"No unit: {parse_duration('5')}") # Expected: ValueError
    print(f"Invalid number format (e.g., 1.2.3h):")
    try:
        parse_duration("1.2.3h")
    except ValueError as e:
        print(f"Caught expected error for invalid number: {e}")

    # Invalid Type
    try:
        parse_duration(123)
    except TypeError as e:
        print(f"Caught expected error for wrong type: {e}")
        
    # Invalid whitespace (Rule 5)
    try:
        parse_duration("1h 30m")
    except ValueError as e:
        print(f"Caught expected error for internal whitespace: {e}")
