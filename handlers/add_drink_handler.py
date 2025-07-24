import discord
import re
from utils.response_utils import send_success_response, send_error_response
from backend.utils import upsert_drink

def parse_adddrink_command(content):
    # Regex: !adddrink "Name" | ingredients | measures | [category] | [alcoholic] | [glass] | [instructions] | [image_url] | [tags]
    pattern = r'^!adddrink\s+"([^"]+)"\s*\|\s*([^|]+)\|\s*([^|]+)(?:\|\s*([^|]*))?(?:\|\s*([^|]*))?(?:\|\s*([^|]*))?(?:\|\s*([^|]*))?(?:\|\s*([^|]*))?(?:\|\s*([^|]*))?$'
    match = re.match(pattern, content.strip())
    if not match:
        return None
    name = match.group(1).strip()
    ingredients = [i.strip() for i in match.group(2).split(',') if i.strip()]
    measures = [m.strip() for m in match.group(3).split(',') if m.strip()]
    category = match.group(4).strip() if match.group(4) else None
    alcoholic = match.group(5).strip() if match.group(5) else None
    glass = match.group(6).strip() if match.group(6) else None
    instructions = match.group(7).strip() if match.group(7) else None
    image_url = match.group(8).strip() if match.group(8) else None
    tags = [t.strip() for t in match.group(9).split(',')] if match.group(9) and match.group(9).strip() else None
    return {
        'name': name,
        'category': category,
        'alcoholic': alcoholic,
        'glass': glass,
        'ingredients_json': ingredients,
        'measures_json': measures,
        'instructions': instructions,
        'image_url': image_url,
        'tags': tags
    }

async def handle_add_drink_command(message):
    parsed = parse_adddrink_command(message.content)
    if not parsed or not parsed['name'] or not parsed['ingredients_json'] or not parsed['measures_json']:
        await send_error_response(
            message.channel,
            "Invalid format. Usage: `!adddrink \"Drink Name\" | Ingredient1,Ingredient2 | Measure1,Measure2 | Category (optional) | Alcoholic (optional) | Glass (optional) | Instructions (optional) | ImageURL (optional) | Tags (optional, comma-separated)`"
        )
        return
    try:
        drink = upsert_drink(
            name=parsed['name'],
            ingredients_json=parsed['ingredients_json'],
            measures_json=parsed['measures_json'],
            instructions=parsed['instructions'],
            created_by_user_id=message.author.id,
            # Only pass tags if present
            **({'tags': parsed['tags']} if parsed['tags'] else {})
        )
        # Fuzzy match check: if the returned drink's name is not an exact (case-insensitive) match, it's a fuzzy match
        if drink.name.strip().lower() != parsed['name'].strip().lower():
            embed = discord.Embed(
                title=f"⚠️ A similar drink already exists: '{drink.name}'",
                description=f"Category: {drink.category}\nType: {drink.alcoholic}\nGlass: {drink.glass}",
                color=0xffcc00
            )
            if drink.image_url:
                embed.set_image(url=drink.image_url)
            embed.add_field(name="Ingredients", value=", \n".join(drink.ingredients_json or []), inline=False)
            embed.add_field(name="Instructions", value=drink.instructions or "No instructions.", inline=False)
            if getattr(drink, 'tags', None):
                embed.add_field(name="Tags", value=", ".join(drink.tags), inline=False)
            await send_error_response(message.channel, f"A similar drink already exists. See details below:")
            await send_success_response(message.channel, embed)
            return
        # Success embed for new or updated drink
        embed = discord.Embed(
            title=f"✅ Drink '{drink.name}' added!",
            description=f"Category: {drink.category or 'N/A'}\nType: {drink.alcoholic or 'N/A'}\nGlass: {drink.glass or 'N/A'}",
            color=0x00ff88
        )
        if drink.image_url:
            embed.set_image(url=drink.image_url)
        if getattr(drink, 'tags', None):
            embed.add_field(name="Tags", value=", ".join(drink.tags), inline=False)
        await send_success_response(message.channel, embed)
    except Exception as e:
        await send_error_response(message.channel, f"Error adding drink: {e}") 