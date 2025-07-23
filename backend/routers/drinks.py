from fastapi import APIRouter, HTTPException, Depends, Query
from sqlmodel import Session, select
from ..models import Drink
from ..database import engine
from ..faiss_utils import find_similar_drinks
from ..cocktail_api import cocktail_api
from typing import List, Optional

router = APIRouter(prefix="/drinks", tags=["drinks"])

def get_session():
    with Session(engine) as session:
        yield session

@router.post("/", response_model=Drink)
def create_drink(drink: Drink, session: Session = Depends(get_session)):
    session.add(drink)
    session.commit()
    session.refresh(drink)
    return drink

@router.get("/", response_model=List[Drink])
def read_drinks(created_by_user_id: Optional[int] = Query(None), session: Session = Depends(get_session)):
    query = select(Drink)
    if created_by_user_id is not None:
        query = query.where(Drink.created_by_user_id == created_by_user_id)
    drinks = session.exec(query).all()
    return drinks

@router.get("/{drink_id}", response_model=Drink)
def read_drink(drink_id: int, session: Session = Depends(get_session)):
    drink = session.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    return drink

@router.delete("/{drink_id}")
def delete_drink(drink_id: int, session: Session = Depends(get_session)):
    drink = session.get(Drink, drink_id)
    if not drink:
        raise HTTPException(status_code=404, detail="Drink not found")
    session.delete(drink)
    session.commit()
    return {"ok": True}

@router.get("/similar/{drink_name}")
def get_similar_drinks(drink_name: str, k: int = Query(5, ge=1, le=20), session: Session = Depends(get_session)):
    """Find similar drinks using FAISS similarity search"""
    similar_drinks = find_similar_drinks(drink_name, k=k)
    
    results = []
    for drink_id, distance in similar_drinks:
        drink = session.get(Drink, drink_id)
        if drink:
            results.append({
                "drink_id": drink.drink_id,
                "name": drink.name,
                "similarity_score": 1.0 / (1.0 + distance),  # Convert distance to similarity
                "distance": distance
            })
    
    return {"query": drink_name, "similar_drinks": results}

@router.get("/search/cocktaildb/{drink_name}")
def search_cocktail_db(drink_name: str):
    """Search for drinks using TheCocktailDB API"""
    drink_data = cocktail_api.search_drink_by_name(drink_name)
    if drink_data:
        formatted_data = cocktail_api.format_drink_for_db(drink_data)
        return {"found": True, "drink": formatted_data}
    return {"found": False, "message": f"No drink found with name '{drink_name}'"}

@router.get("/random/cocktaildb")
def get_random_cocktail():
    """Get a random drink from TheCocktailDB API"""
    drink_data = cocktail_api.get_random_drink()
    if drink_data:
        formatted_data = cocktail_api.format_drink_for_db(drink_data)
        return {"found": True, "drink": formatted_data}
    return {"found": False, "message": "Could not fetch random drink"} 