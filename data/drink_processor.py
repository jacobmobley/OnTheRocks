import backend.utils as backend_utils
from backend.ml_utils import update_user_prefs
from backend.utils import get_or_create_drink_by_name
from backend.database import engine
from sqlmodel import Session

def process_drink_logging_workflow(drink_name, qty, user_id):
    """
    Process the complete drink logging workflow
    
    Args:
        drink_name: Name of the drink to log
        qty: Quantity consumed
        user_id: Discord user ID
        
    Returns:
        tuple: (user, drink, log) objects
    """
    # Upsert user
    user = backend_utils.upsert_user(user_id)
    
    # Find drink (never create)
    drink = backend_utils.find_drink_by_name(drink_name)
    if not drink:
        return user, None, None
    
    # Log drink
    log = backend_utils.log_user_drink(
        user_id=user.user_id,
        drink_id=drink.drink_id,
        name=drink.name,
        quantity=qty,
        units=None
    )
    
    return user, drink, log

def update_user_preferences_workflow(user_id, drink):
    """
    Update user preferences based on consumed drink
    
    Args:
        user_id: User ID
        drink: Drink object with ingredients
    """
    if drink.ingredients_json:
        update_user_prefs(user_id, drink.ingredients_json, drink.measures_json)

def get_drink_by_name_from_db(drink_name):
    """
    Get drink from database by name
    
    Args:
        drink_name: Name of the drink to find
        
    Returns:
        Drink object or None if not found
    """
    with Session(engine) as session:
        drink = get_or_create_drink_by_name(session, drink_name)
        session.commit()
        session.refresh(drink)
        return drink 