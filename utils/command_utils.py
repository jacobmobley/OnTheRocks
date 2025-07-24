import re
import unicodedata

def normalize_quotes(s):
    # Replace all common Unicode quote characters with straight double quotes
    return (s
        .replace('“', '"').replace('”', '"')
        .replace('‟', '"').replace('„', '"')
        .replace('«', '"').replace('»', '"')
        .replace('‘', '"').replace('’', '"')
        .replace("'", '"')
    )

def parse_quoted_argument(message_content, command_prefix):
    """
    Parse a quoted argument from a command
    Handles straight, curly, single, double, and exotic Unicode quotes by normalizing to ".
    Args:
        message_content: Full message content
        command_prefix: Command prefix (e.g., "!howto")
    Returns:
        tuple: (argument, quantity) or (None, None) if parsing fails
    """
    # Normalize Unicode and quotes
    message_content = unicodedata.normalize('NFKC', message_content).strip()
    message_content = normalize_quotes(message_content)
    pattern = rf'{re.escape(command_prefix)}\s*"(.+?)"(?:\s+qty:(\d+(?:\.\d+)?))?'
    match = re.search(pattern, message_content)
    if not match:
        return None, None
    argument = match.group(1)
    quantity = float(match.group(2)) if match.group(2) else 1.0
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