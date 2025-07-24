import os
import json
from datetime import datetime, timedelta
from sqlmodel import SQLModel, create_engine, Session, select
from .models import User, Drink, UserDrinkLog, DatabaseMetadata
from rapidfuzz import process, fuzz

DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL, echo=True)

def get_metadata_value(key: str, default: str = None) -> str:
    """Get a metadata value from the database"""
    with Session(engine) as session:
        metadata = session.exec(select(DatabaseMetadata).where(DatabaseMetadata.key == key)).first()
        return metadata.value if metadata else default

def set_metadata_value(key: str, value: str):
    """Set a metadata value in the database"""
    with Session(engine) as session:
        metadata = session.exec(select(DatabaseMetadata).where(DatabaseMetadata.key == key)).first()
        if metadata:
            metadata.value = value
            metadata.updated_at = datetime.utcnow()
        else:
            metadata = DatabaseMetadata(key=key, value=value)
            session.add(metadata)
        session.commit()

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

def drink_exists_by_cocktail_db_id(session, cocktail_db_id: str):
    """Check if a drink exists by its CocktailDB ID"""
    return session.exec(select(Drink).where(Drink.cocktail_db_id == cocktail_db_id)).first()

def populate_hardcoded_drinks():
    """Populate database with hardcoded drinks from JSON file"""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "drinks_hardcoded.json")
    if not os.path.exists(path):
        return
    
    with open(path, "r") as f:
        drinks = json.load(f)
    
    with Session(engine) as session:
        for d in drinks:
            # Fuzzy match in local DB
            exists = fuzzy_drink_exists(session, d["name"])
            if not exists:
                # Check CocktailDB API for this drink
                from backend.cocktail_api import cocktail_api
                from backend.ml_utils import compute_drink_weights
                api_drink_data = cocktail_api.search_drink_by_name(d["name"])
                if api_drink_data:
                    formatted_data = cocktail_api.format_drink_for_db(api_drink_data)
                    # Compute weights for the drink
                    weights = compute_drink_weights(formatted_data['ingredients_json'])
                    # Preserve tags and image_url from hardcoded if present
                    tags = d.get('tags') if d.get('tags') else formatted_data.get('tags')
                    image_url = d.get('image_url') if d.get('image_url') else formatted_data.get('image_url')
                    drink = Drink(
                        name=formatted_data['name'],
                        ingredients_json=formatted_data['ingredients_json'],
                        measures_json=formatted_data['measures_json'],
                        instructions=formatted_data['instructions'],
                        cocktail_db_id=formatted_data['cocktail_db_id'],
                        image_url=image_url,
                        category=formatted_data['category'],
                        alcoholic=formatted_data['alcoholic'],
                        glass=formatted_data['glass'],
                        weights=weights,
                        tags=tags
                    )
                else:
                    # Compute weights for hardcoded drink
                    weights = compute_drink_weights(d["ingredients_json"])
                    drink = Drink(
                        name=d["name"],
                        ingredients_json=d["ingredients_json"],
                        measures_json=d.get("measures_json"),
                        instructions=d.get("instructions"),
                        cocktail_db_id=d.get("cocktail_db_id"),
                        image_url=d.get("image_url"),
                        category=d.get("category"),
                        alcoholic=d.get("alcoholic"),
                        glass=d.get("glass"),
                        weights=weights,
                        tags=d.get('tags')
                    )
                session.add(drink)
        session.commit()

def populate_from_cocktaildb_by_letter():
    """Populate database with all cocktails from CocktailDB API by listing each letter"""
    from backend.cocktail_api import cocktail_api
    
    # Letters A-Z
    letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    
    with Session(engine) as session:
        for letter in letters:
            try:
                print(f"Fetching cocktails starting with letter: {letter}")
                response = cocktail_api.list_cocktails_by_first_letter(letter)
                
                if response.get('drinks'):
                    for drink_data in response['drinks']:
                        # Check if drink already exists by CocktailDB ID
                        if drink_data.get('idDrink'):
                            existing = drink_exists_by_cocktail_db_id(session, drink_data['idDrink'])
                            if existing:
                                continue
                        
                        # Get full drink details
                        full_drink = cocktail_api.lookup_cocktail_by_id(drink_data['idDrink'])
                        if full_drink.get('drinks'):
                            drink_detail = full_drink['drinks'][0]
                            formatted_data = cocktail_api.format_drink_for_db(drink_detail)
                            
                            # Compute weights for the drink
                            from backend.ml_utils import compute_drink_weights
                            weights = compute_drink_weights(formatted_data['ingredients_json'])
                            
                            drink = Drink(
                                name=formatted_data['name'],
                                ingredients_json=formatted_data['ingredients_json'],
                                measures_json=formatted_data['measures_json'],
                                instructions=formatted_data['instructions'],
                                cocktail_db_id=formatted_data['cocktail_db_id'],
                                image_url=formatted_data['image_url'],
                                category=formatted_data['category'],
                                alcoholic=formatted_data['alcoholic'],
                                glass=formatted_data['glass'],
                                weights=weights
                            )
                            session.add(drink)
                
                # Commit after each letter to avoid large transactions
                session.commit()
                print(f"Added cocktails for letter: {letter}")
                
            except Exception as e:
                print(f"Error processing letter {letter}: {e}")
                session.rollback()
                continue

def update_latest_cocktails():
    """Update database with latest cocktails from CocktailDB API"""
    from backend.cocktail_api import cocktail_api
    
    try:
        # Get latest cocktails
        response = cocktail_api.list_latest_cocktails()
        
        if not response.get('drinks'):
            print("No latest cocktails found")
            return
        
        with Session(engine) as session:
            for drink_data in response['drinks']:
                # Check if drink already exists by CocktailDB ID
                if drink_data.get('idDrink'):
                    existing = drink_exists_by_cocktail_db_id(session, drink_data['idDrink'])
                    if existing:
                        print(f"Drink {drink_data.get('strDrink', 'Unknown')} already exists, stopping update")
                        return  # Stop when we hit an existing drink
                
                # Get full drink details
                full_drink = cocktail_api.lookup_cocktail_by_id(drink_data['idDrink'])
                if full_drink.get('drinks'):
                    drink_detail = full_drink['drinks'][0]
                    formatted_data = cocktail_api.format_drink_for_db(drink_detail)
                    
                    # Compute weights for the drink
                    from backend.ml_utils import compute_drink_weights
                    weights = compute_drink_weights(formatted_data['ingredients_json'])
                    
                    drink = Drink(
                        name=formatted_data['name'],
                        ingredients_json=formatted_data['ingredients_json'],
                        measures_json=formatted_data['measures_json'],
                        instructions=formatted_data['instructions'],
                        cocktail_db_id=formatted_data['cocktail_db_id'],
                        image_url=formatted_data['image_url'],
                        category=formatted_data['category'],
                        alcoholic=formatted_data['alcoholic'],
                        glass=formatted_data['glass'],
                        weights=weights
                    )
                    session.add(drink)
                    print(f"Added new cocktail: {formatted_data['name']}")
            
            session.commit()
            print("Latest cocktails update completed")
            
    except Exception as e:
        print(f"Error updating latest cocktails: {e}")

def should_update_database() -> bool:
    """Check if database should be updated based on last update time"""
    last_update_str = get_metadata_value("last_cocktaildb_update")
    
    if not last_update_str:
        return True  # No previous update, should update
    
    try:
        last_update = datetime.fromisoformat(last_update_str)
        # Update if last update was more than 24 hours ago
        return datetime.utcnow() - last_update > timedelta(hours=24)
    except:
        return True  # Invalid date, should update

def update_database():
    """Main function to update the database intelligently"""
    print("Checking if database needs update...")
    
    # First ensure tables exist
    SQLModel.metadata.create_all(engine)
    
    if should_update_database():
        print("Database update needed, starting update process...")
        
        # Check if database exists and has data
        with Session(engine) as session:
            drink_count = session.exec(select(Drink)).all()
            database_exists = len(drink_count) > 0
        
        if not database_exists:
            print("Database is empty, performing full population...")
            # Populate with hardcoded drinks first
            populate_hardcoded_drinks()
            # Then populate with all CocktailDB data
            populate_from_cocktaildb_by_letter()
        else:
            print("Database exists, checking for latest cocktails...")
            # Only add latest cocktails
            update_latest_cocktails()
        
        # Update the last update timestamp
        set_metadata_value("last_cocktaildb_update", datetime.utcnow().isoformat())
        print("Database update completed")
    else:
        print("Database is up to date")

def create_db_and_tables():
    """Create database tables and populate with initial data"""
    update_database() 