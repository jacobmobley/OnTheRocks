async def handle_hello_command(message):
    """
    Handle the !hello command
    
    Args:
        message: Discord message object
    """
    await message.channel.send("Hello, world!") 