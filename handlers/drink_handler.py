import discord
from utils.command_utils import parse_quoted_argument, validate_drink_name
from utils.embed_utils import build_ingredients_text, add_drink_fields_to_embed, add_ingredients_field_to_embed
from utils.response_utils import send_usage_response, send_error_response, send_success_response
from data.drink_processor import process_drink_logging_workflow, update_user_preferences_workflow

async def handle_drink_command(message):
    """
    Handle the !drink command
    
    Args:
        message: Discord message object
    """
    try:
        # Parse command
        drink_name, qty = parse_quoted_argument(message.content, "!drink")
        
        if not drink_name or not validate_drink_name(drink_name):
            await send_usage_response(message.channel, "Usage: !drink \"Drink Name\" qty:#")
            return
        
        user_id = message.author.id
        
        # Process drink logging workflow
        user, drink, log = process_drink_logging_workflow(drink_name, qty, user_id)
        
        # If drink has no ingredients, treat as not found
        if not drink or not getattr(drink, 'ingredients_json', None):
            await send_error_response(
                message.channel,
                f'No drink found for "{drink_name}". Use `!adddrink "{drink_name}" | Ingredient1,Ingredient2 | Measure1,Measure2` to add it to the database!'
            )
            return
        
        # Update user preferences
        update_user_preferences_workflow(user.user_id, drink)
        
        # Build ingredients text
        ingredients_text = build_ingredients_text(drink)
        
        # Create embed
        embed = discord.Embed(
            title="Drink Logged!",
            description=f"{message.author.display_name} logged {qty}x {drink.name}",
            color=0xee88c0
        )
        
        # Add fields
        embed.add_field(name="Drink ID", value=str(drink.drink_id), inline=True)
        add_drink_fields_to_embed(embed, drink)
        add_ingredients_field_to_embed(embed, ingredients_text)
        if getattr(drink, 'tags', None):
            embed.add_field(name="Tags", value=", ".join(drink.tags), inline=False)
        embed.add_field(name="User ID", value=str(user.user_id), inline=True)
        
        # Add thumbnail if available
        if drink.image_url:
            embed.set_thumbnail(url=drink.image_url)
        
        # Send response
        await send_success_response(message.channel, embed)
        
    except Exception as e:
        await send_error_response(message.channel, str(e)) 