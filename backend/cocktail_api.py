import requests
import json
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

COCKTAIL_KEY = os.getenv("COCKTAILDB_TOKEN")

class CocktailDBAPI:
    def __init__(self):
        # Use v2 with token if available, otherwise fall back to v1
        if COCKTAIL_KEY:
            self.base_url = f"https://www.thecocktaildb.com/api/json/v2/{COCKTAIL_KEY}"
        else:
            self.base_url = "https://www.thecocktaildb.com/api/json/v1/1"

    def _get(self, endpoint: str, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def search_cocktail_by_name(self, name: str):
        return self._get("/search.php", {"s": name})

    def list_cocktails_by_first_letter(self, letter: str):
        return self._get("/search.php", {"f": letter})

    def search_ingredient_by_name(self, name: str):
        return self._get("/search.php", {"i": name})

    def lookup_cocktail_by_id(self, drink_id: str):
        return self._get("/lookup.php", {"i": drink_id})

    def lookup_ingredient_by_id(self, ingredient_id: str):
        return self._get("/lookup.php", {"iid": ingredient_id})

    def lookup_random_cocktail(self):
        return self._get("/random.php")

    def lookup_random_selection(self):
        return self._get("/randomselection.php")

    def list_popular_cocktails(self):
        return self._get("/popular.php")

    def list_latest_cocktails(self):
        return self._get("/latest.php")

    def search_by_ingredient(self, ingredient: str):
        return self._get("/filter.php", {"i": ingredient})

    def filter_by_multi_ingredient(self, ingredients: List[str]):
        # Ingredients should be comma-separated
        return self._get("/filter.php", {"i": ",".join(ingredients)})

    def filter_by_alcoholic(self, alcoholic: str):
        return self._get("/filter.php", {"a": alcoholic})

    def filter_by_category(self, category: str):
        return self._get("/filter.php", {"c": category})

    def filter_by_glass(self, glass: str):
        return self._get("/filter.php", {"g": glass})

    def list_categories(self):
        return self._get("/list.php", {"c": "list"})

    def list_glasses(self):
        return self._get("/list.php", {"g": "list"})

    def list_ingredients(self):
        return self._get("/list.php", {"i": "list"})

    def list_alcoholic_filters(self):
        return self._get("/list.php", {"a": "list"})

    def search_drink_by_name(self, drink_name: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/search.php?s={drink_name}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('drinks') and len(data['drinks']) > 0:
                return data['drinks'][0]  # Return first match
            return None
        except Exception:
            return None
    
    def get_drink_by_id(self, drink_id: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/lookup.php?i={drink_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('drinks') and len(data['drinks']) > 0:
                return data['drinks'][0]
            return None
        except Exception:
            return None
    
    def get_random_drink(self) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.base_url}/random.php"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('drinks') and len(data['drinks']) > 0:
                return data['drinks'][0]
            return None
        except Exception:
            return None
    
    def parse_ingredients_and_measures(self, drink_data: Dict[str, Any]) -> (List[str], List[str]):
        ingredients = []
        measures = []
        for i in range(1, 16):
            ingredient = drink_data.get(f'strIngredient{i}')
            measure = drink_data.get(f'strMeasure{i}')
            if ingredient and ingredient.strip():
                ingredients.append(ingredient.strip())
                measures.append(measure.strip() if measure and measure.strip() else "")
        return ingredients, measures

    def format_drink_for_db(self, drink_data: Dict[str, Any]) -> Dict[str, Any]:
        ingredients, measures = self.parse_ingredients_and_measures(drink_data)
        return {
            'name': drink_data.get('strDrink', ''),
            'ingredients_json': ingredients,
            'measures_json': measures,
            'instructions': drink_data.get('strInstructions', ''),
            'cocktail_db_id': drink_data.get('idDrink'),
            'image_url': drink_data.get('strDrinkThumb'),
            'category': drink_data.get('strCategory'),
            'alcoholic': drink_data.get('strAlcoholic'),
            'glass': drink_data.get('strGlass')
        }

# Global instance
cocktail_api = CocktailDBAPI() 