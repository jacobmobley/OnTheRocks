import discord

def create_discord_client():
    """Create and configure Discord client with intents"""
    intents = discord.Intents.default()
    intents.message_content = True
    client.user.setPresence()
    return discord.Client(intents=intents) 