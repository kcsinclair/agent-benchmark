import re

def parse_duration(text: str) -> float:
    """
    Parse a human-readable duration string and return the total number of seconds as a float.

    Args:
        text (str): A human-readable duration string.

    Returns:
        float: The total number of seconds.

    Raises:
        ValueError: If the input string is invalid.
        TypeError: If the input is not a string.
    """

    # Check if input is a string
    if not isinstance(text, str):
        raise TypeError("Input must be a string")

    # Remove leading and trailing whitespace
    text = text.strip()

    # Check if input string is empty
    if not text:
        raise ValueError("Input string is empty")

    # Check for leading minus sign
    if text[0] == '-':
        sign = -1
        text = text[1:]
    else:
        sign = 1

    # Split the input string into components
    components = re.split(r'\s+', text)

    # Check if there is at least one component
    if len(components) < 1:
        raise ValueError("At least one component is required")

    # Initialize the total duration
    total_duration = 0

    # Iterate over the components
    for component in components:
        # Check if the component is a number
        match = re.match(r'^\d+(?:\.\d+)?$', component)
        if not match:
            raise ValueError("Invalid component")

        # Extract the number
        number = float(match.group())

        # Check if the component has a unit
        if not re.search(r'[hms]', component):
            raise ValueError("Missing unit")

        # Extract the unit
        unit = re.search(r'[hms]', component).group()

        # Convert the number to seconds based on the unit
        if unit == 'h':
            total_duration += sign * number * 3600
        elif unit == 'm':
            total_duration += sign * number * 60
        elif unit == 's':
            total_duration += sign * number
        elif unit == 'ms':
            total_duration += sign * number / 1000

    # Check if there are any repeated units
    if len(components) != len(set(components)):
        raise ValueError("Repeated unit")

    # Check if the units are in strictly descending order of size
    if 'h' in components and 'm' in components and components.index('h') > components.index('m'):
        raise ValueError("Wrong order")
    if 'm' in components and 's' in components and components.index('m') > components.index('s'):
        raise ValueError("Wrong order")
    if 's' in components and 'ms' in components and components.index('s') > components.index('ms'):
        raise ValueError("Wrong order")

    # Return the total duration
    return total_duration
