import os
import json
from sqlmodel import SQLModel, create_engine, Session, select
from .models import User, Drink, UserDrinkLog
from rapidfuzz import process, fuzz

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def fuzzy_drink_exists(session, name: str, threshold: int = 70):
    drinks = session.exec(select(Drink)).all()
    db_names = []
    for drink in drinks:
        if drink.name and len(drink.name.strip()) > 2:
            db_names.append(drink.name)
    if not db_names:
        return None
    match = process.extractOne(name, db_names, scorer=fuzz.token_sort_ratio)
    if match and match[1] >= threshold:
        return session.exec(select(Drink).where(Drink.name == match[0])).first()
    return None

def load_hardcoded_drinks():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "drinks_hardcoded.json")
    if not os.path.exists(path):
        return
    with open(path, "r") as f:
        drinks = json.load(f)
    with Session(engine) as session:
        for d in drinks:
            # Fuzzy match in local DB
            exists, matched_name = fuzzy_drink_exists(session, d["name"]), None
            if not exists:
                # Check CocktailDB API for this drink
                from backend.cocktail_api import cocktail_api
                api_drink_data = cocktail_api.search_drink_by_name(d["name"])
                if api_drink_data:
                    formatted_data = cocktail_api.format_drink_for_db(api_drink_data)
                    drink = Drink(
                        name=formatted_data['name'],
                        ingredients_json=formatted_data['ingredients_json'],
                        measures_json=formatted_data['measures_json'],
                        instructions=formatted_data['instructions'],
                        cocktail_db_id=formatted_data['cocktail_db_id'],
                        image_url=formatted_data['image_url'],
                        category=formatted_data['category'],
                        alcoholic=formatted_data['alcoholic'],
                        glass=formatted_data['glass']
                    )
                else:
                    drink = Drink(
                        name=d["name"],
                        ingredients_json=d["ingredients_json"],
                        measures_json=d.get("measures_json"),
                        instructions=d.get("instructions"),
                        cocktail_db_id=d.get("cocktail_db_id"),
                        image_url=d.get("image_url"),
                        category=d.get("category"),
                        alcoholic=d.get("alcoholic"),
                        glass=d.get("glass")
                    )
                session.add(drink)
        session.commit()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    load_hardcoded_drinks() 