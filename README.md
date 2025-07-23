# OnTheRocks Backend

## Drink Database Schema
```json
{
  "name": string,
  "ingredients_json": [string],
  "measures_json": [string],
  "instructions": string,
  "cocktail_db_id": string | null,
  "image_url": string | null,
  "category": string | null,
  "alcoholic": string | null,
  "glass": string | null
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
- **Drink**: drink_id, name, ingredients_json, measures_json, instructions, created_by_user_id, embedding, cocktail_db_id, image_url, category, alcoholic, glass
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

## Discord Bot Commands
- `!drink "Drink Name" qty:#` - Log a drink consumption (searches TheCocktailDB first)

---

*This backend is separate from the Discord bot in `index.py`.* 