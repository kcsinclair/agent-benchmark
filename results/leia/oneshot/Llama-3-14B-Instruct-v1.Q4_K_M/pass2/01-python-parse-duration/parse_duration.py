import re

def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds as a float.
    """
    units = {'h': 3600.0, 'h ': 3600.0, 'm': 60.0, 'm ': 60.0, 's': 1.0, 's ': 1.0, 'ms': 0.001, 'ms ': 0.0001}
    pattern = r'[-]?([0-9]+\.?){0,}([hms]?m?|h?([0-9]+\.?){0,}s?|([0-9]+\.?){0,}s?)(?:[+-]?([0-9]+\.?){0,}s?)*'
    if not re.match(pattern, text.strip()):
        raise ValueError("Invalid duration string")

    result = 0.0
    sign = 1.0
    if text[0] == '-':
        sign = -1.0
        text = text[1:]

    match = re.match(r'([0-9]+\.?){0,}([hms]?m?|h?([0-9]+\.?){0,}s?)*', text)
    if match:
        if match.group(0):
            if match.group(0).endswith('s'):
                value, unit = match.group(0[:-1]).replace('.', '').replace(' ', '').split('.')
                if '.' in value:
                    value = float(f"{float(value[:-1].replace(' ', '')}}.{int(float(value[-1:]) * 10**(-len(value[-2:].strip()) if len(value[-2:].strip()) > 0) / 10**(-len(value[-2:].strip()) if len(value[-2:].strip()) > 0))}")
                else:
                    value = float(value.replace(' ', ''))
                if unit:
                    if unit == 'ms':
                        unit = 'ms'
                    else:
                        unit = units[unit]
                    result += sign * float(value) * float(unit)
                else:
                    raise ValueError("Missing unit")
            else:
                value = float(match.group(0).replace(' ', ''))
                result += sign * float(value)
        else:
            raise ValueError("Invalid duration string")

        if match.group(0).strip().endswith('s'):
            match = re.match(r'([0-9]+\.?){0,}s?$', match.group(0))
            if match:
                value, unit = match.group(0[:-1]).replace('.', '').replace(' ', '').split('.')
                if '.' in value:
                    value = float(f"{float(value[:-1].replace(' ', '')}}.{int(float(value[-1:]) * 10**(-len(value[-2:].strip()) if len(value[-2:].strip()) > 0) / 10**(-len(value[-2:].strip()) if len(value[-2:].strip()) > 0))}")
                else:
                    value = float(value.replace(' ', ''))
                if unit:
                    if unit == 'ms':
                        unit = 'ms'
                    else:
                        unit = units[unit]
                    result += sign * float(value) * float(unit)
                else:
                    raise ValueError("Missing unit")
        else:
            return result * sign
    else:
        raise ValueError("Invalid duration string")

if __name__ == '__main__':
    print(parse_duration("90s"))  # 90.0
    print(parse_duration("1h30m"))  # 5400.0
    print(parse_duration("1.5h"))  # 5400.0
    print(parse_duration("2h15m30s500ms"))  # 8130.5
    print(parse_duration("250ms"))  # 0.25
    print(parse_duration(" -45m "))  # -2700.0
    print(parse_duration("1m1h"))  # ValueError   (wrong order)
    print(parse_duration("1h1h"))  # ValueError   (repeated unit)
    print(parse_duration(""))  # ValueError
    print(parse_duration("5"))  # ValueError   (missing unit)
