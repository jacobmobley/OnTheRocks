async def send_error_response(channel, error_message):
    """
    Send error response to Discord channel
    
    Args:
        channel: Discord channel to send to
        error_message: Error message to send
    """
    await channel.send(f"Error: {error_message}")

async def send_usage_response(channel, usage_text):
    """
    Send usage instructions to Discord channel
    
    Args:
        channel: Discord channel to send to
        usage_text: Usage instructions to send
    """
    await channel.send(usage_text)

async def send_success_response(channel, embed):
    """
    Send success response with embed to Discord channel
    
    Args:
        channel: Discord channel to send to
        embed: Discord embed to send
    """
    await channel.send(embed=embed) 