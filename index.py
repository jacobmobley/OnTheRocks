import discord
import os
from dotenv import load_dotenv
from backend.database import update_database
from config.bot_config import create_discord_client
from bot_core import on_ready_handler, message_handler

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="!drinkhelp for help"))
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await message_handler(message)

if __name__ == "__main__":
    update_database()
    client.run(TOKEN) 