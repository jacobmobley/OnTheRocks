import os
import discord
from dotenv import load_dotenv
import backend.utils as backend_utils
import json
import re
from backend.database import create_db_and_tables

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Ensure database and tables are created at bot startup
create_db_and_tables()

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower() == "!hello":
        await message.channel.send("Hello, world!")
    # !drink command: !drink "Margarita" qty:2
    if message.content.lower().startswith("!drink"):
        try:
            # Parse command: !drink "Margarita" qty:2
            match = re.match(r'!drink\s+["“”]([^"“”]+)["“”](?:\s+qty:(\d+(?:\.\d+)?))?', message.content)
            if not match:
                await message.channel.send("Usage: !drink \"Drink Name\" qty:#")
                return
            drink_name = match.group(1)
            qty = float(match.group(2)) if match.group(2) else 1.0
            user_id = message.author.id
            
            # Upsert user
            user = backend_utils.upsert_user(user_id)
            
            # Upsert drink (handles DB, API, and custom logic)
            drink = backend_utils.upsert_drink(drink_name)
            
            # Log drink
            log = backend_utils.log_user_drink(
                user_id=user.user_id,
                drink_id=drink.drink_id,
                name=drink.name,
                quantity=qty,
                units=None
            )

            # Update user preferences with drink ingredients and measures
            if drink.ingredients_json:
                backend_utils.update_user_prefs(user.user_id, drink.ingredients_json, drink.measures_json)
            
            # Respond with embed
            embed = discord.Embed(
                title="Drink Logged!",
                description=f"{message.author.display_name} logged {qty}x {drink.name}",
                color=0xee88c0
            )
            embed.add_field(name="Drink ID", value=str(drink.drink_id), inline=True)
            if drink.category:
                embed.add_field(name="Category", value=drink.category, inline=True)
            if drink.alcoholic:
                embed.add_field(name="Type", value=drink.alcoholic, inline=True)
            if drink.glass:
                embed.add_field(name="Glass", value=drink.glass, inline=True)
            if drink.image_url:
                embed.set_thumbnail(url=drink.image_url)
            if drink.ingredients_json and len(drink.ingredients_json) > 0:
                # Pretty print: '1 1/2 oz Tequila' or just 'Tequila' if no measure
                lines = []
                for i, ing in enumerate(drink.ingredients_json):
                    amt = ""
                    if drink.measures_json and i < len(drink.measures_json):
                        amt = drink.measures_json[i]
                    line = f"{amt} {ing}".strip()
                    lines.append(line)
                ingredients_text = "\n".join(lines)
                embed.add_field(name="Ingredients", value=ingredients_text, inline=False)
            embed.add_field(name="User ID", value=str(user.user_id), inline=True)
            await message.channel.send(embed=embed)
        except Exception as e:
            await message.channel.send(f"Error: {e}")

client.run(TOKEN)