"""
Machine Learning utilities for drink recommendations and weight computations.
Contains sklearn KNN functionality and weight computation logic.
"""

import numpy as np
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from .models import User, Drink
from .database import engine
from sklearn.neighbors import NearestNeighbors
import random


def compute_drink_weights(ingredients_json: list) -> dict:
    """
    Compute normalized weights for drink ingredients.
    Assigns weight 1 to each ingredient and normalizes the vector.
    Returns a dict mapping ingredient names to normalized weights.
    """
    if not ingredients_json:
        return {}
    
    # ingredients_json already contains clean ingredient names from strIngredient fields
    # No need to extract - use them directly
    ingredient_names = ingredients_json
    
    # Assign weight 1 to each ingredient
    weights = {ingredient: 1.0 for ingredient in ingredient_names}
    
    # Normalize (L1 normalization - sum to 1)
    total_weight = sum(weights.values())
    if total_weight > 0:
        normalized_weights = {ingredient: weight / total_weight for ingredient, weight in weights.items()}
    else:
        normalized_weights = weights
    
    return normalized_weights


def update_user_prefs(user_id: int, drink_ingredients: list, drink_measures: Optional[list] = None, decay: float = 0.8, norm: str = "l1"):
    """
    Update the user's ingredient preference vector using binary presence (all ingredients equal weight).
    - user_id: the user's ID
    - drink_ingredients: list of clean ingredient names (from strIngredient fields)
    - decay: lambda decay/memory factor (0 < decay < 1)
    - norm: 'l1' or 'l2'
    """
    with Session(engine) as session:
        user = session.exec(select(User).where(User.user_id == user_id)).first()
        if not user:
            return None
        w_prev = user.prefs or {}
        # drink_ingredients already contains clean ingredient names from strIngredient fields
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


def suggest_drink(user_weights: dict, k: int = 1, logged_drinks: Optional[list] = None) -> Optional[list]:
    """
    Suggest up to k drinks using sklearn KNN based on user preference weights, skipping already-logged drinks.
    Args:
        user_weights: Dict mapping ingredient names to user preference weights
        k: Number of neighbors for KNN (default 1)
        logged_drinks: List of drink names to skip (already logged by user)
    Returns:
        List of up to k drink dicts, sorted by similarity (best first)
    """
    if logged_drinks is None:
        logged_drinks = []
    # 1. Gather all drinks with weights, skipping logged
    with Session(engine) as session:
        drinks = session.exec(select(Drink)).all()
        drinks = [d for d in drinks if d.weights and isinstance(d.weights, dict) and len(d.weights) > 0 and d.name not in logged_drinks]
        if not drinks:
            return None
        # 2. Build ingredient set
        all_ingredients = set()
        for d in drinks:
            all_ingredients.update(d.weights.keys())
        all_ingredients.update(user_weights.keys())
        all_ingredients = sorted(all_ingredients)
        ingredient_index = {ing: i for i, ing in enumerate(all_ingredients)}
        # 3. Build drink matrix
        drink_matrix = np.zeros((len(drinks), len(all_ingredients)), dtype=np.float32)
        for i, d in enumerate(drinks):
            for ing, w in d.weights.items():
                if ing in ingredient_index:
                    drink_matrix[i, ingredient_index[ing]] = w
        # 4. Build user vector
        user_vec = np.zeros((1, len(all_ingredients)), dtype=np.float32)
        for ing, w in user_weights.items():
            if ing in ingredient_index:
                user_vec[0, ingredient_index[ing]] = w
        # 5. KNN search
        n_neighbors = min(k, len(drinks))
        nbrs = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
        nbrs.fit(drink_matrix)
        distances, indices = nbrs.kneighbors(user_vec)
        # 6. Collect top k drinks (sorted by similarity)
        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            d = drinks[idx]
            results.append({
                "name": d.name,
                "category": d.category,
                "alcoholic": d.alcoholic,
                "glass": d.glass,
                "instructions": d.instructions,
                "ingredients": d.ingredients_json,
                "measures": d.measures_json,
                "image_url": d.image_url,
                "similarity_score": 1.0 - float(dist),
                "reason": f"Rank {rank+1} of top {k} by ingredient profile",
                "tags": d.tags
            })
        return results 