import re


def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}")
    
    text = text.strip()
    
    if not text:
        raise ValueError("Empty duration string")
    
    # Check for leading minus
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:]
    
    if not text:
        raise ValueError("No components after minus sign")
    
    # Check for any whitespace in the remaining text
    if any(c.isspace() for c in text):
        raise ValueError("Whitespace not allowed in duration string")
    
    # Define the pattern for a single component: number followed by unit
    # Number: one or more digits, optionally followed by a dot and one or more digits
    # Unit: h, m, s, or ms
    # We need to parse the entire string as a sequence of components
    
    # Let's use a regex to match the entire string
    # Each component: (\d+(?:\.\d+)?)(h|ms|m|s)
    # But we need to be careful: 'ms' should be matched before 'm' and 's'
    # Actually, since units are concatenated, we need to parse them in order.
    
    # Let's use a regex that matches the whole string as a sequence of components
    # The pattern for each component: number + unit
    # Number: \d+(?:\.\d+)?
    # Unit: h|ms|m|s (but we need to handle the fact that 'ms' is two chars)
    
    # Let's try to parse by finding all components
    # We'll use a regex to find all matches of (number)(unit)
    # But we need to ensure the entire string is consumed
    
    # Pattern for a single component:
    # Number: \d+(?:\.\d+)?
    # Unit: h|ms|m|s
    # But 'ms' must be matched as a unit, not 'm' followed by 's'
    
    # Let's use a regex with alternation, putting 'ms' before 'm' and 's'
    # Actually, since the units are in descending order, and each unit appears at most once,
    # we can parse the string by looking for the pattern.
    
    # Let's use a regex to match the entire string:
    # ^(?:\d+(?:\.\d+)?(?:h|ms|m|s))+$
    # But this doesn't enforce the order. We need to check the order separately.
    
    # First, let's extract all components using a regex
    # We need to be careful with the unit matching: 'ms' should be matched as a whole
    
    # Let's use a regex that matches each component:
    # (\d+(?:\.\d+)?)(h|ms|m|s)
    # But we need to ensure that 'ms' is matched before 'm' or 's'
    
    # Let's use a different approach: iterate through the string and parse components
    
    # Actually, let's use a regex with a capturing group for the number and unit
    # and use re.findall or re.finditer
    
    # The pattern for a component: (\d+(?:\.\d+)?)(h|ms|m|s)
    # But we need to ensure the entire string is matched
    
    # Let's use re.fullmatch with a pattern that matches one or more components
    # Pattern: (?:\d+(?:\.\d+)?(?:h|ms|m|s))+
    # But this might not work correctly because of the alternation order
    
    # Let's try:
    component_pattern = r'(\d+(?:\.\d+)?)(h|ms|m|s)'
    
    # We need to find all non-overlapping matches and ensure they cover the entire string
    pos = 0
    components = []
    while pos < len(text):
        m = re.match(component_pattern, text[pos:])
        if not m:
            raise ValueError(f"Invalid component at position {pos}")
        number_str = m.group(1)
        unit = m.group(2)
        components.append((number_str, unit))
        pos += m.end()
    
    if not components:
        raise ValueError("No components found")
    
    # Now validate the order of units
    # Units must be in strictly descending order: h, m, s, ms
    # Each unit may appear at most once
    
    unit_order = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    seen_units = set()
    last_order = -1
    
    for number_str, unit in components:
        if unit in seen_units:
            raise ValueError(f"Repeated unit: {unit}")
        seen_units.add(unit)
        
        current_order = unit_order[unit]
        if current_order <= last_order:
            raise ValueError(f"Units not in descending order: {unit} after previous units")
        last_order = current_order
    
    # Calculate total seconds
    total = 0.0
    for number_str, unit in components:
        value = float(number_str)
        if unit == 'h':
            total += value * 3600.0
        elif unit == 'm':
            total += value * 60.0
        elif unit == 's':
            total += value * 1.0
        elif unit == 'ms':
            total += value * 0.001
    
    if negative:
        total = -total
    
    return total
