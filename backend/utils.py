from sqlmodel import Session, select
from .models import User, Drink, UserDrinkLog
from .database import engine
from datetime import datetime
from typing import Optional, Any, List
from .faiss_utils import get_drink_embedding, update_drink_embedding
from .cocktail_api import cocktail_api
import numpy as np
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

def get_or_create_drink_by_name(session, name: str, ingredients_json: Any = None, instructions: Optional[str] = None, created_by_user_id: Optional[int] = None):
    # Fuzzy match before anything else
    drink = fuzzy_drink_exists(session, name)
    if drink:
        return drink
    api_drink_data = cocktail_api.search_drink_by_name(name)
    if api_drink_data:
        formatted_data = cocktail_api.format_drink_for_db(api_drink_data)
        drink = Drink(
            name=formatted_data['name'],
            ingredients_json=formatted_data['ingredients_json'],
            measures_json=formatted_data['measures_json'],
            instructions=formatted_data['instructions'],
            created_by_user_id=created_by_user_id,
            cocktail_db_id=formatted_data['cocktail_db_id'],
            image_url=formatted_data['image_url'],
            category=formatted_data['category'],
            alcoholic=formatted_data['alcoholic'],
            glass=formatted_data['glass']
        )
    else:
        drink = Drink(
            name=name, 
            ingredients_json=ingredients_json, 
            instructions=instructions, 
            created_by_user_id=created_by_user_id
        )
    drink.embedding = compute_embedding(drink)
    session.add(drink)
    return drink

def upsert_drink(name: str, ingredients_json: Any = None, instructions: Optional[str] = None, created_by_user_id: Optional[int] = None) -> Drink:
    with Session(engine) as session:
        drink = get_or_create_drink_by_name(session, name, ingredients_json, instructions, created_by_user_id)
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

def extract_ingredient_names(ingredients: list) -> list:
    """
    Given a list like ["1 1/2 oz Tequila", "1/2 oz Triple sec", "Salt"],
    return ["Tequila", "Triple sec", "Salt"]
    """
    names = []
    for ing in ingredients:
        # Remove leading amount and units, keep last word(s)
        # This regex removes everything up to the last word (ingredient)
        match = re.search(r'([a-zA-Z][a-zA-Z\s]+)$', ing.strip())
        if match:
            names.append(match.group(1).strip())
        else:
            names.append(ing.strip())
    return names

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

def update_user_prefs(user_id: int, drink_ingredients: list, drink_measures: Optional[list] = None, decay: float = 0.8, norm: str = "l1"):
    """
    Update the user's ingredient preference vector using binary presence (all ingredients equal weight).
    - user_id: the user's ID
    - drink_ingredients: list of ingredient names
    - decay: lambda decay/memory factor (0 < decay < 1)
    - norm: 'l1' or 'l2'
    """
    from .models import User
    with Session(engine) as session:
        user = session.exec(select(User).where(User.user_id == user_id)).first()
        if not user:
            return None
        w_prev = user.prefs or {}
        ingredient_names = drink_ingredients
        # Build full ingredient set
        all_ingredients = set(w_prev.keys()) | set(ingredient_names)
        all_ingredients = sorted(all_ingredients)
        # Binary presence vector
        z = np.array([1.0 if ing in ingredient_names else 0.0 for ing in all_ingredients], dtype=np.float32)
        # Build w_prev vector
        w_prev_vec = np.array([w_prev.get(ing, 0.0) for ing in all_ingredients], dtype=np.float32)
        # Exponential moving average
        w_raw = decay * w_prev_vec + (1 - decay) * z
        # Normalize
        if norm == "l1":
            total = np.sum(w_raw)
            if total == 0:
                return w_prev  # avoid div by zero
            w_new_vec = w_raw / total
        else:  # l2
            mag = np.sqrt(np.sum(w_raw ** 2))
            if mag == 0:
                return w_prev
            w_new_vec = w_raw / mag
        # Convert back to dict
        w_new = {ing: float(w_new_vec[i]) for i, ing in enumerate(all_ingredients)}
        user.prefs = w_new
        session.add(user)
        session.commit()
        session.refresh(user)
        return w_new