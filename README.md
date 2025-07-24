# OnTheRocks Backend

## Drink Database Schema
```json
{
  "name": string,
  "ingredients_json": [string],  // Clean ingredient names from strIngredient fields
  "measures_json": [string],     // Parallel to ingredients_json
  "instructions": string,
  "cocktail_db_id": string | null,
  "image_url": string | null,
  "category": string | null,
  "alcoholic": string | null,
  "glass": string | null,
  "weights": {                   // Normalized ingredient weights for KNN recommendations
    "ingredient_name": float     // L1 normalized (sums to 1.0)
  }
}
```

## Backend Structure

- `backend/` - Contains all backend code for the database and API (users, drinks, logs)
- Uses `sqlmodel` and `sqlalchemy` for ORM/database
- Uses `FastAPI` for API endpoints
- Uses `FAISS` for vector similarity search
- Integrates with [TheCocktailDB API](https://www.thecocktaildb.com/) for drink data

## Setup

1. Install dependencies:
   ```bash
   pip install sqlmodel sqlalchemy fastapi uvicorn faiss-cpu numpy requests
   ```
2. Run the backend server:
   ```bash
   uvicorn backend.main:app --reload
   ```

## Database Models
- **User**: user_id, first_seen_at, last_seen_at, timezone, prefs
- **Drink**: drink_id, name, ingredients_json, measures_json, instructions, created_by_user_id, embedding, cocktail_db_id, image_url, category, alcoholic, glass, weights
- **UserDrinkLog**: id, user_id, drink_id, name, quantity, units, timestamp

## API Endpoints
- CRUD for users, drinks, logs
- `/drinks/similar/{drink_name}` - Find similar drinks using FAISS vector search
- `/drinks/search/cocktaildb/{drink_name}` - Search TheCocktailDB API
- `/drinks/random/cocktaildb` - Get random drink from TheCocktailDB

## TheCocktailDB Integration
- Automatic drink lookup when logging drinks
- Access to 636+ drinks with ingredients, instructions, and images
- Populates drink metadata: category, alcoholic type, glass type, image URL
- Falls back to custom drinks when not found in API

## FAISS Integration
- Automatic embedding generation for drinks (name + ingredients)
- Vector similarity search for drink recommendations
- Index rebuilds on startup from existing database

## Ingredient Weight System
- Automatic weight computation for all drinks (equal weighting + L1 normalization)
- Clean ingredient names from CocktailDB API strIngredient fields
- Normalized vectors ready for sklearn KNN recommendations
- Weights stored as JSON: `{"Tequila": 0.25, "Triple sec": 0.25, "Lime juice": 0.25, "Salt": 0.25}`

## Discord Bot Commands
- `!hello` - Simple greeting command
- `!howto "Drink Name"` - Get instructions and ingredients for a drink
- `!drink "Drink Name" qty:#` - Log a drink consumption (searches TheCocktailDB first)
- `!suggest` - Get drink recommendations based on preferences or popular drinks

## Project Structure
```
OnTheRocks/
├── index.py              # Main Discord bot entry point
├── bot_core.py           # Bot event handlers
├── handlers/             # Command handlers
│   ├── hello_handler.py
│   ├── howto_handler.py
│   ├── drink_handler.py
│   ├── suggest_handler.py
│   └── command_router.py
├── utils/                # Utility functions
│   ├── embed_utils.py    # Discord embed creation
│   ├── command_utils.py  # Command parsing
│   └── response_utils.py # Response handling
├── data/                 # Data processing
│   ├── drink_processor.py
│   └── user_processor.py
├── config/               # Configuration
│   ├── setup.py
│   └── bot_config.py
└── backend/              # Backend API and database
```

---

*The Discord bot is now modular and organized for easy maintenance and extension.* 