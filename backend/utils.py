from sqlmodel import Session, select
from .models import User, Drink, UserDrinkLog
from .database import engine
from datetime import datetime
from typing import Optional, Any, List
from .faiss_utils import get_drink_embedding, update_drink_embedding
from .ml_utils import compute_drink_weights, update_user_prefs, suggest_drink
import re
from rapidfuzz import process, fuzz

# Updated embedding function using FAISS utilities
def compute_embedding(drink: Drink) -> List[float]:
    ingredients = drink.ingredients_json if isinstance(drink.ingredients_json, list) else None
    embedding = get_drink_embedding(drink.name, ingredients)
    if drink.drink_id:
        update_drink_embedding(drink.drink_id, drink.name, ingredients)
    return embedding

def get_drink_by_name(name: str) -> Optional[Drink]:
    with Session(engine) as session:
        drink = session.exec(select(Drink).where(Drink.name == name)).first()
        if drink:
            return drink
        drink = session.exec(select(Drink).where(Drink.name.ilike(name))).first()
        if drink:
            return drink
        return None

def fuzzy_drink_exists(session, name: str, threshold: int = 70):
    # Fetch all drinks and print their name and category for debugging
    drinks = session.exec(select(Drink)).all()
    db_names = []
    for drink in drinks:
        if drink.name and len(drink.name.strip()) > 2:
            db_names.append(drink.name)
    if not db_names:
        return None
    match = process.extractOne(name, db_names, scorer=fuzz.token_sort_ratio)
    print(f"Fuzzy match: {match}, name: {name}")
    if match and match[1] >= threshold:
        return session.exec(select(Drink).where(Drink.name == match[0])).first()
    return None

def find_drink_by_name(name: str, threshold: int = 70) -> Optional[Drink]:
    """
    Fuzzy search for a drink by name. Returns the best match or None if not found.
    Never creates a new drink.
    """
    with Session(engine) as session:
        drink = fuzzy_drink_exists(session, name, threshold=threshold)
        return drink

def upsert_user(user_id: int, timezone: Optional[str] = None, prefs: Optional[str] = None) -> User:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.user_id == user_id)).first()
        now = datetime.utcnow()
        if user:
            user.last_seen_at = now
            if timezone:
                user.timezone = timezone
            if prefs:
                user.prefs = prefs
        else:
            user = User(user_id=user_id, first_seen_at=now, last_seen_at=now, timezone=timezone, prefs=prefs)
            session.add(user)
        session.commit()
        session.refresh(user)
        return user

def get_or_create_drink_by_name(session, name: str, ingredients_json: Any = None, measures_json: Any = None, instructions: Optional[str] = None, created_by_user_id: Optional[int] = None):
    # Fuzzy match to find existing drink
    drink = fuzzy_drink_exists(session, name)
    if drink:
        return drink
    
    # If no match found, create a new drink with provided data
    # Since we have a comprehensive database, this should be rare
    # Compute weights for the new drink
    weights = compute_drink_weights(ingredients_json) if ingredients_json else {}
    
    drink = Drink(
        name=name, 
        ingredients_json=ingredients_json, 
        measures_json=measures_json,
        instructions=instructions, 
        created_by_user_id=created_by_user_id,
        weights=weights
    )
    # drink.embedding = compute_embedding(drink)  # Removed: no longer used
    session.add(drink)
    return drink

def upsert_drink(name: str, ingredients_json: Any = None, measures_json: Any = None, instructions: Optional[str] = None, created_by_user_id: Optional[int] = None) -> Drink:
    with Session(engine) as session:
        drink = get_or_create_drink_by_name(session, name, ingredients_json, measures_json, instructions, created_by_user_id)
        session.commit()
        session.refresh(drink)
        return drink

def log_user_drink(user_id: int, drink_id: Optional[int], name: str, quantity: Optional[float], units: Optional[str]) -> UserDrinkLog:
    with Session(engine) as session:
        log = UserDrinkLog(user_id=user_id, drink_id=drink_id, name=name, quantity=quantity, units=units)
        session.add(log)
        session.commit()
        session.refresh(log)
        return log



def parse_measure_amount(measure: str) -> float:
    """
    Parse a measure string like '1 1/2 oz' or '3/4' or '2' and return a float amount.
    Returns 0.0 if parsing fails or measure is empty.
    """
    if not measure or not measure.strip():
        return 0.0
    measure = measure.strip().lower()
    # Remove units (e.g., 'oz', 'cup', etc.)
    measure = re.sub(r'[^0-9/\. ]', '', measure)
    # Handle mixed numbers (e.g., '1 1/2')
    parts = measure.split()
    total = 0.0
    for part in parts:
        if '/' in part:
            try:
                num, denom = part.split('/')
                total += float(num) / float(denom)
            except Exception:
                continue
        else:
            try:
                total += float(part)
            except Exception:
                continue
    return total



def get_user_drink_history(user_id: int) -> List[str]:
    """
    Get list of drink names that a user has logged.
    
    Args:
        user_id: The user's ID
        
    Returns:
        List of drink names the user has consumed
    """
    with Session(engine) as session:
        logs = session.exec(select(UserDrinkLog).where(UserDrinkLog.user_id == user_id)).all()
        return [log.name for log in logs]

def get_popular_drink_not_tried(user_id: int) -> Optional[dict]:
    """
    Get the most popular drink that the user hasn't tried yet.
    
    Args:
        user_id: The user's ID
        
    Returns:
        Dict containing drink information, or None if no popular drink found
    """
    from .cocktail_api import cocktail_api
    
    # Get user's drink history
    user_drinks = get_user_drink_history(user_id)
    print(f"User {user_id} has tried: {user_drinks}")
    
    try:
        # Get popular cocktails from CocktailDB API
        response = cocktail_api.list_popular_cocktails()
        
        if not response.get('drinks'):
            print("No popular cocktails found")
            return None
        
        # Find first popular drink user hasn't tried
        for drink_data in response['drinks']:
            drink_name = drink_data.get('strDrink', '')
            if drink_name and drink_name not in user_drinks:
                print(f"Found popular drink user hasn't tried: {drink_name}")
                
                # Get full drink details
                full_drink = cocktail_api.lookup_cocktail_by_id(drink_data['idDrink'])
                if full_drink.get('drinks'):
                    drink_detail = full_drink['drinks'][0]
                    formatted_data = cocktail_api.format_drink_for_db(drink_detail)
                    
                    return {
                        "name": formatted_data['name'],
                        "category": formatted_data['category'],
                        "alcoholic": formatted_data['alcoholic'],
                        "glass": formatted_data['glass'],
                        "instructions": formatted_data['instructions'],
                        "ingredients": formatted_data['ingredients_json'],
                        "measures": formatted_data['measures_json'],
                        "image_url": formatted_data['image_url'],
                        "similarity_score": 1.0,  # Popular drink, high score
                        "reason": "Popular drink you haven't tried yet!"
                    }
        
        print("User has tried all popular drinks")
        return None
        
    except Exception as e:
        print(f"Error getting popular drinks: {e}")
        return None



