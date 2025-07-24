import discord
from utils.command_utils import parse_quoted_argument, validate_drink_name
from utils.embed_utils import build_ingredients_text, create_drink_embed, add_ingredients_field_to_embed
from utils.response_utils import send_usage_response, send_error_response, send_success_response
from data.drink_processor import get_drink_by_name_from_db

async def handle_howto_command(message):
    """
    Handle the !howto command
    
    Args:
        message: Discord message object
    """
    try:
        # Parse command
        drink_name, _ = parse_quoted_argument(message.content, "!howto")
        
        if not drink_name or not validate_drink_name(drink_name):
            await send_usage_response(message.channel, "Usage: !howto \"Drink Name\"")
            return
        
        # Get drink from database
        drink = get_drink_by_name_from_db(drink_name)
        
        if not drink:
            await send_error_response(message.channel, f"No drink found for '{drink_name}'.")
            return
        
        # Build ingredients text
        ingredients_text = build_ingredients_text(drink)
        
        # Create embed
        embed = create_drink_embed(drink, f"How to make {drink.name}", 0x88c0ee)
        add_ingredients_field_to_embed(embed, ingredients_text)
        
        # Send response
        await send_success_response(message.channel, embed)
        
    except Exception as e:
        await send_error_response(message.channel, str(e)) 