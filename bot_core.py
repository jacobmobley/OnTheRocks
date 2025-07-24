from handlers.command_router import route_command

def on_ready_handler(client):
    """
    Handle bot ready event
    
    Args:
        client: Discord client
    """
    print(f"Logged in as {client.user}")

async def message_handler(message):
    """
    Handle incoming messages
    
    Args:
        message: Discord message object
    """
    if message.author.bot:
        return
    
    await route_command(message) 