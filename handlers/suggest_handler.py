import discord
from utils.embed_utils import build_ingredients_text_from_dict
from utils.response_utils import send_error_response, send_success_response
from data.user_processor import get_user_with_history, determine_user_suggestion_strategy, get_drink_suggestion_workflow

async def handle_suggest_command(message):
    """
    Handle the !suggest command
    
    Args:
        message: Discord message object
    """
    try:
        user_id = message.author.id
        
        # Parse k from message (e.g., !suggestdrink 3)
        content = message.content.strip().split()
        k = 1
        if len(content) > 1:
            try:
                k = int(content[1])
                if k < 1:
                    k = 1
            except Exception:
                k = 1
        
        # Get user and their drink history
        user, user_drink_history, drink_count = get_user_with_history(user_id)
        
        # Determine suggestion strategy
        strategy = determine_user_suggestion_strategy(drink_count, user.prefs, k_threshold=1)
        
        if strategy == 'popular':
            print(f"User {user_id} has {drink_count} drinks logged (< 1), suggesting popular drink")
        else:
            print(f"User {user_id} weights: {user.prefs}")
        
        # Get drink suggestion (pass k)
        suggested_drinks = get_drink_suggestion_workflow(user_id, strategy, k=k)
        
        if not suggested_drinks:
            if strategy == 'popular':
                await send_error_response(message.channel, "You haven't logged any drinks yet! Try using `!drink \"Drink Name\"` first to build your preferences.")
            else:
                await send_error_response(message.channel, "Sorry, I couldn't find a drink suggestion for you right now.")
            return
        
        # If popular, wrap in a list for uniformity
        if strategy == 'popular':
            suggested_drinks = [suggested_drinks]
        
        # Send one embed per drink
        for i, drink in enumerate(suggested_drinks, 1):
            ingredients_text = build_ingredients_text_from_dict(drink)
            title = f"🍹 Suggestion #{i} for {message.author.display_name}: {drink.get('name', 'Unknown')} (Score: {drink.get('similarity_score', 0):.2f})"
            embed = discord.Embed(
                title=title,
                description=drink.get('instructions', 'No instructions available.'),
                color=0x00ff88
            )
            # Add fields
            embed.add_field(name="Category", value=drink.get("category", "Unknown"), inline=True)
            embed.add_field(name="Type", value=drink.get("alcoholic", "Unknown"), inline=True)
            embed.add_field(name="Glass", value=drink.get("glass", "Unknown"), inline=True)
            embed.add_field(name="Ingredients", value=ingredients_text, inline=False)
            if drink.get('tags'):
                embed.add_field(name="Tags", value=", ".join(drink['tags']), inline=False)
            if drink.get('reason'):
                embed.add_field(name="Reason", value=drink['reason'], inline=False)
            # Add image if available
            if drink.get("image_url"):
                embed.set_image(url=drink["image_url"])
            # Send response
            await send_success_response(message.channel, embed)
        
    except Exception as e:
        await send_error_response(message.channel, f"Error getting suggestion: {e}") 