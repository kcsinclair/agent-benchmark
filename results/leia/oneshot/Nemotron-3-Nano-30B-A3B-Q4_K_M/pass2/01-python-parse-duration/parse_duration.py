def parse_duration(text: str) -> float:
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    s = text.strip()
    if not s:
        raise ValueError("Empty string")
    
    sign = 1
    if s[0] == '-':
        sign = -1
        s = s[1:]
        if not s:
            raise ValueError("Invalid format after minus sign")
    
    tokens = []
    i = 0
    n = len(s)
    while i < n:
        if not s[i].isdigit():
            raise ValueError("Invalid token: expected digit at start")
        j = i
        while j < n and s[j].isdigit():
            j += 1
        if j >= n:
            raise ValueError("Number not followed by unit")
        num_str = s[i:j]
        if '.' in num_str:
            parts = num_str.split('.')
            if len(parts) != 2:
                raise ValueError("Invalid number format")
            if parts[0] == '' or parts[1] == '':
                raise ValueError("Invalid number format")
        unit_str = s[j:j+2]
        if unit_str not in ['h', 'm', 's', 'ms']:
            raise ValueError("Invalid unit")
        unit = unit_str[0]
        tokens.append((unit, num_str))
        i = j + len(unit_str)
    
    if not tokens:
        raise ValueError("No components found")
    
    units = [unit for unit, _ in tokens]
    if len(units) != len(set(units)):
        raise ValueError("Duplicate units")
    
    order_map = {'h': 0, 'm': 1, 's': 2, 'ms': 3}
    for idx in range(1, len(units)):
        if order_map[units[idx-1]] >= order_map[units[idx]]:
            raise ValueError("Units not in descending order")
    
    total_seconds = 0.0
    for unit, num_str in tokens:
        if unit == 'h':
            multiplier = 3600.0
        elif unit == 'm':
            multiplier = 60.0
        elif unit == 's':
            multiplier = 1.0
        else:  # 'ms'
            multiplier = 1.0 / 1000.0
        num_val = float(num_str)
        total_seconds += num_val * multiplier
    
    return sign * total_seconds
