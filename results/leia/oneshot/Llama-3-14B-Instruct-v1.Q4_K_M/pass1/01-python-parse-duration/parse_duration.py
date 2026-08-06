import re

def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds as a float.
    """
    units = {'h': 3600.0, 'h ': 3600.0, 'm': 60.0, 'm ': 60.0, 's': 1.0, 's ': 1.0, 'ms': 0.001, 'ms ': 0.001}
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
                    value = float(f"{float(value[:-1].replace(' ', '')}.{int(len(value) - 1):02d}e-{'0' * (len(value) - 1 - int(len(value) - 1))}")")
                else:
                    value = float(value.replace(' ', ''))
                if unit:
                    if unit == 'ms':
                        value /= 1000.0
                    elif unit == 's':
                        pass
                    else:
                        value *= units[unit]
                else:
                    raise ValueError("Missing unit")
                result += sign * float(value)
                text = match.group(0)[len(match.group(0).replace(' ', '')):].strip()
            else:
                raise ValueError("Invalid duration string")

            while text:
                match = re.match(r'([0-9]+\.?){0,}([hms]?m?|h?([0-9]+\.?){0,}s?)*', text)
                if match:
                    if match.group(0):
                        if match.group(0).endswith('s'):
                            value, unit = match.group(0[:-1]).replace('.', '').replace(' ', '').split('.')
                            if '.' in value:
                                value = float(f"{float(value[:-1].replace(' ', '')}.{int(len(value) - 1):02d}e-{'0' * (len(value) - 1 - int(len(value) - 1))}")")
                            else:
                                value = float(value.replace(' ', ''))
                            if unit:
                                if unit == 'ms':
                                    value /= 1000.0
                                elif unit == 's':
                                    pass
                                else:
                                    raise ValueError("Invalid unit")
                            else:
                                raise ValueError("Missing unit")
                            result += sign * float(value * units.get(unit, float('inf')))
                            text = match.group(0)[len(match.group(0).replace(' ', '')):].strip()
                            break
                        else:
                            raise ValueError("Invalid duration string")
                    else:
                        raise ValueError("Invalid duration string")
                else:
                    raise ValueError("Invalid duration string")

            if '.' not in str(result):
                result = int(result)
            else:
                parts = str(result).split('.')
                if len(parts) > 2:
                    raise ValueError("Invalid duration string")
                result -= int(parts[0].replace(' ', '') * 10 ** -int(len(parts[0].replace(' ', '')) - 1) * 10 ** -int(len(parts[1].replace(' ', '')))
                if '.' in str(result):
                    parts = str(result).split('.')
                    if len(parts) > 2:
                        raise ValueError("Invalid duration string")
                    result -= int(parts[0].replace(' ', '')) * 10 ** -int(len(parts[0].replace(' ', '')) - 1)
                if '.' in str(result):
                    raise ValueError("Invalid duration string")
                result = float(f"{int(result)}")

            if result % 1 != 0:
                parts = str(int(result)).split('.')
                if len(parts) > 2:
                    raise ValueError("Invalid duration string")
                result -= int(parts[0].replace(' ', '')) * 10 ** -int(len(parts[0].replace(' ', '')) - 1)
                if '.' in str(result):
                    raise ValueError("Invalid duration string")
                result = float(f"{int(result)}")

        else:
            raise ValueError("Invalid duration string")

        return sign * result

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
