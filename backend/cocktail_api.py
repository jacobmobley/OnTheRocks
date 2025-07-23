import requests
import json
from typing import Optional, Dict, Any, List

class CocktailDBAPI:
    def __init__(self):
        self.base_url = "https://www.thecocktaildb.com/api/json/v1/1"
    
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