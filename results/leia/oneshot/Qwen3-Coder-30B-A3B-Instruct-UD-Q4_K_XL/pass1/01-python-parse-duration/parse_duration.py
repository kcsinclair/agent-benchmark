import re

def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    text = text.strip()
    if not text:
        raise ValueError("Empty string is not a valid duration")
    
    # Check for invalid whitespace
    if text != text.strip():
        raise ValueError("Invalid whitespace")
    
    # Check for leading minus
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:].strip()
    
    if not text:
        raise ValueError("Missing components after minus sign")
    
    # Parse components
    components = re.findall(r'(\d+(?:\.\d+)?)([a-z]+)', text)
    if not components:
        raise ValueError("Invalid format: missing components")
    
    # Validate components
    units_order = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    last_unit = None
    
    total_seconds = 0.0
    
    for value, unit in components:
        # Validate unit
        if unit not in units_order:
            raise ValueError(f"Invalid unit: {unit}")
        
        # Check order
        if last_unit is not None and units_order[unit] >= units_order[last_unit]:
            raise ValueError(f"Invalid order: {unit} must come before {last_unit}")
        
        last_unit = unit
        
        # Validate value
        try:
            num_value = float(value)
            if num_value < 0:
                raise ValueError("Negative numbers are not allowed")
        except ValueError:
            raise ValueError(f"Invalid number: {value}")
        
        # Convert to seconds
        if unit == 'h':
            total_seconds += num_value * 3600
        elif unit == 'm':
            total_seconds += num_value * 60
        elif unit == 's':
            total_seconds += num_value
        elif unit == 'ms':
            total_seconds += num_value / 1000
    
    # Check for repeated units
    units_found = [unit for _, unit in components]
    if len(units_found) != len(set(units_found)):
        raise ValueError("Repeated units are not allowed")
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
