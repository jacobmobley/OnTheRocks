import re

def parse_quoted_argument(message_content, command_prefix):
    """
    Parse a quoted argument from a command
    
    Args:
        message_content: Full message content
        command_prefix: Command prefix (e.g., "!howto")
        
    Returns:
        tuple: (argument, quantity) or (None, None) if parsing fails
    """
    # Handle both straight and curly quotes
    pattern = rf'{command_prefix}\s+["""]([^"""]+)["""](?:\s+qty:(\d+(?:\.\d+)?))?'
    match = re.match(pattern, message_content)
    
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