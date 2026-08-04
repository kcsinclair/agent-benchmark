def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds as a float.
    
    Args:
        text: A duration string with optional minus sign followed by components
              like '1h30m', '2.5s', etc.
              
    Returns:
        float: Total duration in seconds
        
    Raises:
        ValueError: If the input string is invalid
        TypeError: If the input is not a string
    """
    # Check if input is a string
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    # Check for empty string
    if not text:
        raise ValueError("Empty string is not a valid duration")
    
    # Check for leading minus sign
    negative = False
    if text.startswith('-'):
        negative = True
        text = text[1:].strip()
    
    # Check if there's content after minus sign
    if not text:
        raise ValueError("Invalid duration format")
    
    # Parse components
    components = []
    i = 0
    while i < len(text):
        # Find the start of the number
        number_start = i
        while i < len(text) and (text[i].isdigit() or text[i] == '.'):
            i += 1
        
        # Check if we found a number
        if number_start == i:
            raise ValueError("Invalid duration format")
        
        # Extract the number
        number_str = text[number_start:i]
        
        # Validate number format
        try:
            number = float(number_str)
            if number < 0:
                raise ValueError("Numbers must be non-negative")
        except ValueError:
            raise ValueError("Invalid number format")
        
        # Find unit
        unit = ""
        if i < len(text):
            if text[i] == 'm' and i + 1 < len(text) and text[i + 1] == 's':
                unit = "ms"
                i += 2
            elif text[i] == 'h':
                unit = "h"
                i += 1
            elif text[i] == 'm':
                unit = "m"
                i += 1
            elif text[i] == 's':
                unit = "s"
                i += 1
            else:
                raise ValueError("Invalid unit")
        else:
            raise ValueError("Missing unit")
        
        components.append((unit, number))
    
    # Validate components: check for repeated units and correct order
    units_order = ["h", "m", "s", "ms"]
    seen_units = set()
    
    for unit, number in components:
        # Check if unit is repeated
        if unit in seen_units:
            raise ValueError("Repeated unit")
        seen_units.add(unit)
    
    # Check that units are in descending order
    unit_indices = []
    for unit, number in components:
        unit_indices.append(units_order.index(unit))
    
    # Check if indices are in strictly descending order
    for j in range(len(unit_indices) - 1):
        if unit_indices[j] <= unit_indices[j + 1]:
            raise ValueError("Units must be in descending order")
    
    # Calculate total seconds
    total_seconds = 0.0
    for unit, number in components:
        if unit == "h":
            total_seconds += number * 3600
        elif unit == "m":
            total_seconds += number * 60
        elif unit == "s":
            total_seconds += number
        elif unit == "ms":
            total_seconds += number / 1000
    
    if negative:
        total_seconds = -total_seconds
    
    return total_seconds
