import discord
from utils.response_utils import send_success_response

async def handle_help_command(message):
    help_text = (
        "**OnTheRocks Bot Help**\n\n"
        "**!drink \"Drink Name\" qty:#**\n"
        "Log a drink you have consumed. Example: `!drink \"Margarita\" qty:2`\n\n"
        "**!adddrink \"Drink Name\" | Ingredient1,Ingredient2 | Measure1,Measure2 | Category (optional) | Alcoholic (optional) | Glass (optional) | Instructions (optional) | ImageURL (optional) | Tags (optional, comma-separated)**\n"
        "Add a new drink to the database. Example: `!adddrink \"My Drink\" | Vodka,Orange Juice | 1 oz,3 oz | Cocktail | Alcoholic | Highball | Shake and serve! | https://example.com/image.jpg | Summer, Fruity, Available at harrys`\n\n"
        "**!suggestdrink [k]**\n"
        "Get a list of drink suggestions based on your preferences. Optionally specify `k` to get the top k matches (e.g., `!suggestdrink 5`).\n"
        "The bot uses a KNN (nearest neighbors) algorithm to recommend drinks you haven't logged yet, based on your ingredient preferences.\n\n"
        "**!howto \"Drink Name\"**\n"
        "Get instructions and ingredients for making a specific drink. Example: `!howto \"Old Fashioned\"`\n\n"
        "**!drinkhelp**\n"
        "Show this help message.\n\n"
        "**How suggestions work:**\n"
        "- The more drinks you log, the better your recommendations!\n"
        "- The bot learns your ingredient preferences and finds similar drinks you haven't tried.\n"
        "- You can request more than one suggestion at a time with `!suggestdrink k`.\n\n"
        "If you have questions or feedback, contact the bot admin. Cheers! 🥂"
    )
    embed = discord.Embed(title="🍸 OnTheRocks Bot Help", description=help_text, color=0x88c0ee)
    await send_success_response(message.channel, embed) 