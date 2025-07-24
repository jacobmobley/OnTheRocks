from handlers.hello_handler import handle_hello_command
from handlers.howto_handler import handle_howto_command
from handlers.drink_handler import handle_drink_command
from handlers.suggest_handler import handle_suggest_command
from handlers.help_handler import handle_help_command
from handlers.add_drink_handler import handle_add_drink_command

async def route_command(message):
    """
    Route incoming message to appropriate command handler
    
    Args:
        message: Discord message object
    """
    content = message.content.lower()
    
    if content == "!hello":
        await handle_hello_command(message)
    elif content.startswith("!howto"):
        await handle_howto_command(message)
    elif content.startswith("!drinkhelp"):
        await handle_help_command(message) 
    elif content.startswith("!adddrink"):
        await handle_add_drink_command(message)
    elif content.startswith("!drink"):
        await handle_drink_command(message)
    elif content.startswith("!suggestdrink"):
        await handle_suggest_command(message)
    