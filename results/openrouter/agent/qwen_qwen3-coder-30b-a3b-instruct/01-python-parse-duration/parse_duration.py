def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds as a float.
    
    Args:
        text: A duration string with optional minus sign followed by components
              (e.g., "1h30m", "2.5h", "-45m")
              
    Returns:
        float: Total duration in seconds
        
    Raises:
        TypeError: If input is not a string
        ValueError: If input format is invalid
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
        text = text[1:]
    
    # Check if text is empty after removing minus sign
    if not text:
        raise ValueError("Invalid duration format")
    
    # Define valid units and their conversion factors to seconds
    unit_map = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Define valid unit order (descending by size)
    valid_order = ['h', 'm', 's', 'ms']
    
    # Parse components
    components = []
    i = 0
    
    while i < len(text):
        # Find the unit
        unit = None
        for u in valid_order:
            if text[i:].startswith(u):
                unit = u
                break
        
        if not unit:
            raise ValueError("Invalid unit or format")
        
        # Find the number before the unit
        num_start = i
        while num_start > 0 and (text[num_start-1].isdigit() or text[num_start-1] == '.'):
            num_start -= 1
            
        # Extract the number
        num_str = text[num_start:i]
        if not num_str:
            raise ValueError("Missing number before unit")
        
        # Validate number format
        try:
            number = float(num_str)
            if number < 0:
                raise ValueError("Numbers must be non-negative")
        except ValueError:
            raise ValueError("Invalid number format")
        
        # Check if unit already used
        for comp in components:
            if comp[1] == unit:
                raise ValueError("Repeated unit")
        
        components.append((number, unit))
        i += len(unit)
    
    # Validate order
    for j in range(len(components) - 1):
        current_unit = components[j][1]
        next_unit = components[j+1][1]
        current_index = valid_order.index(current_unit)
        next_index = valid_order.index(next_unit)
        if current_index <= next_index:
            raise ValueError("Units must be in descending order")
    
    # Calculate total seconds
    total_seconds = 0.0
    for number, unit in components:
        total_seconds += number * unit_map[unit]
    
    if negative:
        total_seconds = -total_seconds
        
    return total_seconds
