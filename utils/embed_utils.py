import discord

def build_ingredients_text(drink):
    """
    Build formatted ingredients text from drink object
    
    Args:
        drink: Drink object with ingredients_json and measures_json
        
    Returns:
        str: Formatted ingredients text
    """
    if not drink.ingredients_json:
        return "No ingredients available."
    
    lines = []
    for i, ing in enumerate(drink.ingredients_json):
        amt = ""
        if drink.measures_json and i < len(drink.measures_json):
            amt = drink.measures_json[i]
        line = f"{amt} {ing}".strip()
        lines.append(line)
    
    return "\n".join(lines)

def build_ingredients_text_from_dict(suggested_drink):
    """
    Build formatted ingredients text from suggestion dictionary
    
    Args:
        suggested_drink: Dict with 'ingredients' and 'measures' lists
        
    Returns:
        str: Formatted ingredients text
    """
    ingredients = suggested_drink.get("ingredients", [])
    measures = suggested_drink.get("measures", [])
    
    if not ingredients:
        return "No ingredients available."
    
    lines = []
    for i, ing in enumerate(ingredients):
        amt = ""
        if i < len(measures):
            amt = measures[i]
        line = f"{amt} {ing}".strip()
        lines.append(line)
    
    return "\n".join(lines)

def create_drink_embed(drink, title, color):
    """
    Create a Discord embed for a drink
    
    Args:
        drink: Drink object
        title: Embed title
        color: Embed color
        
    Returns:
        discord.Embed: Formatted embed
    """
    embed = discord.Embed(
        title=title,
        description=drink.instructions or "No instructions available.",
        color=color
    )
    
    if drink.image_url:
        embed.set_thumbnail(url=drink.image_url)
    
    return embed

def add_drink_fields_to_embed(embed, drink):
    """
    Add drink metadata fields to embed
    
    Args:
        embed: Discord embed to modify
        drink: Drink object with metadata
    """
    if drink.category:
        embed.add_field(name="Category", value=drink.category, inline=True)
    if drink.alcoholic:
        embed.add_field(name="Type", value=drink.alcoholic, inline=True)
    if drink.glass:
        embed.add_field(name="Glass", value=drink.glass, inline=True)

def add_ingredients_field_to_embed(embed, ingredients_text):
    """
    Add ingredients field to embed
    
    Args:
        embed: Discord embed to modify
        ingredients_text: Formatted ingredients text
    """
    embed.add_field(name="Ingredients", value=ingredients_text, inline=False) 