import re
from typing import Union

def parse_duration(text: str) -> float:
    """
    Parses a human-readable duration string and returns the total number of 
    seconds as a float.
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    text = text.strip()
    if not text:
        raise ValueError("Duration string cannot be empty.")

    # 1. Handle optional leading minus sign
    is_negative = text.startswith('-')
    if is_negative:
        text = text[1:]
        if not text:
            raise ValueError("Duration string cannot be just a minus sign.")

    # Define units and their multipliers in descending order of size
    UNITS = [
        ('h', 3600.0),
        ('m', 60.0),
        ('s', 1.0),
        ('ms', 0.001)
    ]
    
    # Regex to match a valid number (non-negative decimal)
    # Rules: digits with optional fractional part, no leading +, no exponents, no bare ., no trailing dot
    # Matches: 2, 1.5, 0.25. Fails: .5, 5.
    NUMBER_PATTERN = r"(\d+(\.\d+)?)"
    
    # Regex to match a component: Number followed immediately by a unit
    # We use a capturing group for the number and a capturing group for the unit
    COMPONENT_PATTERN = re.compile(f"({NUMBER_PATTERN})([hms])")
    
    # We need a more complex pattern to handle 'ms' as well, 
    # but the strict ordering requirement simplifies things.
    # Let's iterate through the expected units to ensure strict ordering and uniqueness.
    
    # We will use a state machine/iterative parsing approach based on the required order.
    
    total_seconds = 0.0
    seen_units = set()
    current_index = 0
    
    # The expected order of units to enforce Rule 2
    expected_units = ['h', 'm', 's', 'ms']
    
    # We iterate through the expected units to find them in the correct order
    for unit_char in expected_units:
        unit_len = len(unit_char)
        
        # Check if the current position starts with the unit
        if text[current_index:].startswith(unit_char):
            # If we found a unit, we must have a number immediately preceding it
            
            # Find the start of the potential number segment
            start_of_number = current_index
            
            # Scan backwards from the unit start to find the end of the number
            # The number must be composed of digits and at most one dot.
            
            # Find the end of the number segment (which is current_index)
            # We need to find the start of the number segment.
            
            # A simpler approach: use regex to find all components, then validate order/uniqueness.
            # However, the strict ordering requirement makes simple regex matching difficult 
            # because we need to ensure the *first* match is 'h' if present, etc.
            
            # Let's stick to iterative parsing based on the required order.
            
            # 1. Find the number preceding the unit_char
            # The number must end exactly where the unit starts.
            
            # Scan backwards from current_index to find the start of the number
            number_str = ""
            i = current_index - 1
            while i >= 0 and (text[i].isdigit() or text[i] == '.'):
                number_str = text[i] + number_str
                i -= 1
            
            if not number_str:
                # Unit found but no preceding number
                raise ValueError(f"Invalid format: Unit '{unit_char}' found without preceding number.")
            
            # 2. Validate the number format
            try:
                # Check for invalid number formats: bare '.', trailing dot, multiple dots
                if number_str.startswith('.') or number_str.endswith('.') or number_str.count('.') > 1:
                    raise ValueError
                
                value = float(number_str)
            except ValueError:
                raise ValueError(f"Invalid number format: '{number_str}'")

            # 3. Validate unit usage
            if unit_char in seen_units:
                raise ValueError(f"Repeated unit found: {unit_char}")
            
            # 4. Update state
            multiplier = next(m for u, m in UNITS if u == unit_char)
            total_seconds += value * multiplier
            seen_units.add(unit_char)
            
            # Advance the index past the number and the unit
            current_index += len(number_str) + unit_len
        
        # If we are looking for 'h' and don't find it, we continue to 'm'.
        # If we find 'h', we must consume it and then look for 'm' starting from the new index.
        # This structure inherently enforces the order if we process the string sequentially.
        
    # --- Re-evaluating the parsing strategy based on strict ordering ---
    # The iterative approach above is flawed because it assumes we know *which* unit comes next 
    # based on the predefined list, but the input string dictates the order.
    # Example: "1h30m" -> We find 'h', then we must find 'm' starting after 'h'.
    # Example: "1m1h" -> We find 'm', but then we expect 'h' to be next, which violates the rule.
    
    # Let's use regex to find all components and then validate the sequence.
    
    # Pattern to capture (Number)(Unit)
    # Number: \d+(\.\d+)? (Handles valid decimals)
    # Unit: (h|m|s|ms)
    # We must ensure the number part doesn't consume the unit part, and vice versa.
    
    # Since units are single or double characters, we can try to match them greedily 
    # but ensure the number part is valid.
    
    # A component is: (Valid Number) followed by (h|m|s|ms)
    # We use lookahead/lookbehind or careful grouping to ensure the number is valid.
    
    # Let's define the regex to capture the number and the unit, ensuring the number is valid.
    # Valid number: digits, optional dot, more digits.
    # We must ensure the dot is not at the start or end.
    VALID_NUMBER_REGEX = r"(\d+(?:\.\d+)?)"
    
    # The full component regex: (Number)(Unit)
    # We use a non-capturing group for the unit options to simplify the match structure.
    COMPONENT_REGEX = re.compile(rf"({VALID_NUMBER_REGEX})([hms])")
    
    # This simple regex fails for 'ms' because 'm' is also a unit.
    # We must prioritize matching 'ms' over 'm'.
    
    # Order of matching in regex: longest unit first.
    COMPONENT_REGEX = re.compile(r"(\d+(?:\.\d+)?)(ms|h|m|s)")
    
    matches = list(COMPONENT_REGEX.finditer(text))
    
    if not matches:
        # Check if the string is just a number (Rule 5: missing unit)
        if re.fullmatch(r"[\d.]+", text):
            raise ValueError("Missing unit in duration string.")
        # If it's not a number and no components matched, it's invalid syntax
        raise ValueError("Invalid duration format.")

    parsed_components = []
    
    for match in matches:
        num_str = match.group(1)
        unit = match.group(2)
        
        # Validate number format again (regex might allow things like "1.2.3" if not careful, 
        # but the pattern above is restrictive enough for standard floats)
        try:
            value = float(num_str)
        except ValueError:
            # Should not happen if regex is correct, but good for safety
            raise ValueError(f"Invalid number format detected: {num_str}")

        # Check for invalid number formats explicitly (e.g., trailing dot, leading dot)
        if num_str.startswith('.') or num_str.endswith('.') or num_str.count('.') > 1:
             raise ValueError(f"Invalid number format: {num_str}")

        parsed_components.append({'value': value, 'unit': unit})

    # --- Validation Steps ---
    
    # 1. Check for repeated units (Rule 2)
    units_found = [c['unit'] for c in parsed_components]
    if len(units_found) != len(set(units_found)):
        raise ValueError("Repeated unit found.")

    # 2. Check for strict descending order (Rule 2)
    # Map units to their required order index
    unit_order = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    
    for i in range(len(parsed_components) - 1):
        current_unit = parsed_components[i]['unit']
        next_unit = parsed_components[i+1]['unit']
        
        if unit_order[current_unit] > unit_order[next_unit]:
            raise ValueError("Units must appear in strictly descending order of size.")

    # 3. Check for extraneous characters (Rule 5)
    # The concatenation of all matched components must equal the stripped input text.
    reconstructed_text = "".join(f"{c['value'] if c['value'] == int(c['value']) else str(c['value'])}*{c['unit']}" 
                                 for c in parsed_components)
    
    # Since we used regex matching on the raw string, we must ensure no characters were skipped.
    # We reconstruct the string using the original number strings to be precise.
    reconstructed_text_precise = "".join(f"{c['value'] if c['value'] == int(c['value']) else str(c['value'])}*{c['unit']}" 
                                        for c in parsed_components)
    
    # A simpler check: if the sum of lengths of matched parts doesn't equal the length of the stripped text, 
    # there are invalid characters (Rule 5).
    total_matched_length = sum(len(match.group(0)) for match in matches)
    if total_matched_length != len(text):
        raise ValueError("Invalid characters or misplaced whitespace detected.")

    # --- Calculation ---
    
    final_total = 0.0
    for component in parsed_components:
        value = component['value']
        unit = component['unit']
        
        if unit == 'h':
            final_total += value * 3600.0
        elif unit == 'm':
            final_total += value * 60.0
        elif unit == 's':
            final_total += value * 1.0
        elif unit == 'ms':
            final_total += value * 0.001
            
    if is_negative:
        return -final_total
    return final_total
