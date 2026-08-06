def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total
    number of seconds as a float.
    """
    
    # Check if input is a string
    if not isinstance(text, str):
        raise TypeError()
    
    # Strip leading and trailing whitespace
    text = text.strip()
    
    # Check if string is empty
    if not text:
        raise ValueError()
    
    # Check for leading minus sign
    is_negative = text[0] == '-'
    if is_negative:
        text = text[1:]
    
    # Define unit conversion factors
    unit_factors = {
        'h': 3600.0,
        'm': 60.0,
        's': 1.0,
        'ms': 0.001
    }
    
    # Define valid units in descending order
    valid_units = ['h', 'm', 's', 'ms']
    
    # Initialize result
    total_seconds = 0.0
    
    # Process each unit in order
    for unit in valid_units:
        # Find the position of the unit
        pos = text.find(unit)
        
        # If unit is found, extract the number before it
        if pos != -1:
            # Extract the number part (everything before the unit)
            num_str = text[:pos]
            
            # Check if the number is valid
            try:
                num = float(num_str)
                
                # Check if the number is non-negative
                if num < 0:
                    raise ValueError()
                
                # Add to total
                total_seconds += num * unit_factors[unit]
                
                # Remove the processed part from text
                text = text[pos + len(unit):]
                
                # Check if there are any remaining units
                if text and text[0] in valid_units:
                    raise ValueError()
            except ValueError:
                raise ValueError()
    
    # If there's still text left, it's invalid
    if text:
        raise ValueError()
    
    # Return the result with the correct sign
    return total_seconds if not is_negative else -total_seconds
