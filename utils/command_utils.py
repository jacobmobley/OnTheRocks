import re

def parse_quoted_argument(message_content, command_prefix):
    """
    Parse a quoted argument from a command
    Handles straight, curly, single, and double quotes.
    Args:
        message_content: Full message content
        command_prefix: Command prefix (e.g., "!howto")
    Returns:
        tuple: (argument, quantity) or (None, None) if parsing fails
    """
    # Match any of: straight double, straight single, curly double, curly single quotes
    quote_chars = '"\'‘’“”'
    pattern = rf'{re.escape(command_prefix)}\s*([{quote_chars}])(.+?)\1(?:\s+qty:(\d+(?:\.\d+)?))?'
    match = re.match(pattern, message_content)
    if not match:
        return None, None
    argument = match.group(2)
    quantity = float(match.group(3)) if match.group(3) else 1.0
    return argument, quantity

def validate_drink_name(drink_name):
    """
    Validate drink name
    Args:
        drink_name: Drink name to validate
    Returns:
        bool: True if valid, False otherwise
    """
    return drink_name and len(drink_name.strip()) > 0 