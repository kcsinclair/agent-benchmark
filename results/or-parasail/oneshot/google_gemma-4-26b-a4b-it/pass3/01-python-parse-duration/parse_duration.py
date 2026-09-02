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
    sign = 1.0
    if s.startswith('-'):
        sign = -1.0
        s = s[1:]
    elif s.startswith('+'):
        # Rule 1: No leading '+' allowed
        raise ValueError("Leading '+' is not allowed")

    if not s:
        raise ValueError("No components found after sign")

    # 3. Define units and their multipliers
    # Order is important for the regex and the validation logic
    units_info = [
        ('h', 3600.0),
        ('m', 60.0),
        ('s', 1.0),
        ('ms', 0.001)
    ]
    
    # Create a regex pattern to capture components.
    # Number: digits, optional dot, followed by digits. 
    # Must not be just '.' or end in '.' or start with '.'.
    # We use a lookahead/lookbehind or specific structure to enforce Rule 1.
    # Rule 1: "2", "1.5", "0.25". No ".5", no "5.", no exponents.
    # Pattern for number: \d+(\.\d+)?
    
    # We will use a regex that finds all (number)(unit) pairs.
    # Since units are strictly descending, we can match the whole string 
    # against a pattern that enforces the order.
    
    # Pattern for a single component: (number)(unit)
    # Number part: \d+(\.\d+)?
    # Unit part: h|m|s|ms
    # Note: 'ms' must be checked before 'm' to avoid partial matching.
    
    # To enforce strict descending order and no repeats, we'll parse components
    # and validate them manually.
    
    # Regex to find all components:
    # This regex looks for a number followed by one of the units.
    # We use a non-capturing group for the units to ensure 'ms' is matched correctly.
    pattern = re.compile(r'^(\d+(?:\.\d+)?)(h|m|s|ms)$')
    
    # However, the string is a concatenation of these. 
    # We can't just use findall because we need to ensure the whole string is consumed
    # and that no invalid characters/whitespace exist between components.
    
    total_seconds = 0.0
    last_unit_index = -1 # Index in units_info
    
    # We will manually slice the string to ensure we consume it perfectly
    current_pos = 0
    while current_pos < len(s):
        # Try to find the next component
        # We look for the unit first to know where the number ends
        match = None
        # Check units in order of length (ms then m, s, h) to avoid greedy errors
        for unit_str, multiplier in units_info:
            # Find if the current position starts with a unit? No, units follow numbers.
            # We need to find the number + unit.
            pass
        
        # Let's use a different approach: 
        # Find all matches of (number)(unit) and check if they cover the whole string.
        # But we need to ensure the units are in order.
        
        # Let's use a regex that matches the entire string structure:
        # ^(num h)?(num m)?(num s)?(num ms)?$
        # But numbers are decimals.
        
        # Construct a regex for the whole string:
        # Each component is (\d+(?:\.\d+)?)(h|m|s|ms)
        # We'll build a regex that allows any combination of these in order.
        
        # Actually, the simplest way to enforce "strictly descending" and "no repeats"
        # is to iterate through the units and see if they exist in the string.
        
        # Let's try to find all components using a regex that captures (number, unit)
        # and then validate the sequence.
        
        # This regex captures a number and a unit.
        # We use a lookahead to ensure we don't match 'm' inside 'ms' incorrectly.
        # We'll use a regex that matches the whole string by repeating the component pattern.
        
        # Component pattern: (\d+(?:\.\d+)?)(ms|h|m|s)
        # Note: ms must come before m in the alternation.
        comp_regex = r'(\d+(?:\.\d+)?)(ms|h|m|s)'
        
        # We'll find all matches
        matches = list(re.finditer(comp_regex, s))
        
        if not matches:
            raise ValueError("No valid components found")
            
        # Check if the matches perfectly reconstruct the string
        reconstructed = ""
        for m in matches:
            reconstructed += m.group(0)
        
        if reconstructed != s:
            # This handles cases like "1h 30m" (whitespace), "1h1h" (overlap/repeat), 
            # or "5" (missing unit) or "1.h" (invalid number)
            raise ValueError("Invalid format or unexpected characters")

        # Validate order and uniqueness
        unit_to_idx = {u[0]: i for i, u in enumerate(units_info)}
        
        for i, m in enumerate(matches):
            val = float(m.group(1))
            unit = m.group(2)
            u_idx = unit_to_idx[unit]
            
            if u_idx <= last_unit_index:
                raise ValueError("Units must be in strictly descending order and unique")
            
            last_unit_index = u_idx
            
            # Find multiplier
            multiplier = 0.0
            for u_str, mult in units_info:
                if u_str == unit:
                    multiplier = mult
                    break
            
            total_seconds += val * multiplier
            
        return total_seconds * sign

    # The logic above is inside a loop that shouldn't be a loop. 
    # Let's clean up the implementation.

def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    s = text.strip()
    if not s:
        raise ValueError("Empty duration string")

    sign = 1.0
    if s.startswith('-'):
        sign = -1.0
        s = s[1:]
    elif s.startswith('+'):
        raise ValueError("Leading '+' is not allowed")

    if not s:
        raise ValueError("No components found")

    # Regex for a single component: number + unit
    # Number: \d+(?:\.\d+)?
    # Unit: ms|h|m|s (ms first to avoid 'm' matching 'ms')
    comp_pattern = r'^(\d+(?:\.\d+)?)(ms|h|m|s)$'
    
    # To handle multiple components, we'll use a regex that matches the whole string
    # as a sequence of components.
    # We'll use finditer and then verify the string is fully consumed.
    
    # We need to be careful: 'm' is a substring of 'ms'. 
    # The regex engine handles this if we put 'ms' before 'm'.
    full_pattern = re.compile(r'(\d+(?:\.\d+)?)(ms|h|m|s)')
    
    matches = list(full_pattern.finditer(s))
    
    if not matches:
        raise ValueError("No valid components found")
    
    # Check if the concatenated matches equal the original string
    # This ensures no whitespace or invalid chars between components
    if "".join(m.group(0) for m in matches) != s:
        raise ValueError("Invalid format or unexpected characters")

    units_info = [('h', 3600.0), ('m', 60.0), ('s', 1.0), ('ms', 0.001)]
    unit_to_idx = {u[0]: i for i, u in enumerate(units_info)}
    unit_to_mult = {u[0]: u[1] for u in units_info}

    total_seconds = 0.0
    last_unit_idx = -1

    for m in matches:
        val_str = m.group(1)
        unit_str = m.group(2)
        
        # Rule 1: Validate number format (no trailing dot, no leading dot)
        # The regex \d+(?:\.\d+)? already enforces:
        # - No leading dot (must start with digit)
        # - No trailing dot (if dot exists, must be followed by digit)
        # - No exponents
        # - No bare '.'
        
        u_idx = unit_to_idx[unit_str]
        if u_idx <= last_unit_idx:
            raise ValueError("Units must be in strictly descending order and unique")
        
        last_unit_idx = u_idx
        total_seconds += float(val_str) * unit_to_mult[unit_str]

    return total_seconds * sign
