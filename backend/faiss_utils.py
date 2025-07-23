import faiss
import numpy as np
from typing import List, Tuple, Optional
from sqlmodel import Session, select
from .models import Drink
from .database import engine

class DrinkVectorIndex:
    def __init__(self, dimension: int = 10):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance for similarity
        self.drink_ids = []  # Keep track of drink_id order in index
        
    def add_drink_embedding(self, drink_id: int, embedding: List[float]) -> None:
        """Add a drink embedding to the FAISS index"""
        vector = np.array(embedding, dtype=np.float32).reshape(1, -1)
        self.index.add(vector)
        self.drink_ids.append(drink_id)
        
    def search_similar_drinks(self, query_embedding: List[float], k: int = 5) -> List[Tuple[int, float]]:
        """Search for similar drinks using a query embedding"""
        query_vector = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_vector, k)
        
        results = []
        for i, distance in zip(indices[0], distances[0]):
            if i < len(self.drink_ids):  # Valid index
                drink_id = self.drink_ids[i]
                results.append((drink_id, float(distance)))
        return results
    
    def rebuild_index_from_database(self) -> None:
        """Rebuild the FAISS index from all drinks in the database"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.drink_ids = []
        
        with Session(engine) as session:
            drinks = session.exec(select(Drink)).all()
            for drink in drinks:
                if drink.embedding:
                    self.add_drink_embedding(drink.drink_id, drink.embedding)

# Global instance
drink_index = DrinkVectorIndex()

def get_drink_embedding(drink_name: str, ingredients: Optional[List[str]] = None) -> List[float]:
    """
    Generate embedding for a drink based on name and ingredients.
    This is a simple placeholder - replace with actual embedding model.
    """
    # Simple hash-based embedding for now
    # In production, use a proper embedding model (e.g., sentence-transformers)
    import hashlib
    
    text = drink_name.lower()
    if ingredients:
        text += " " + " ".join(ingredients).lower()
    
    # Create a hash and convert to 10-dimensional vector
    hash_obj = hashlib.md5(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert bytes to float values between -1 and 1
    embedding = []
    for i in range(0, len(hash_bytes), 2):
        if len(embedding) >= 10:
            break
        if i + 1 < len(hash_bytes):
            # Combine two bytes into a float
            combined = (hash_bytes[i] << 8) + hash_bytes[i + 1]
            normalized = (combined / 65535.0) * 2 - 1  # Scale to [-1, 1]
            embedding.append(normalized)
    
    # Pad to 10 dimensions if needed
    while len(embedding) < 10:
        embedding.append(0.0)
    
    return embedding[:10]

def update_drink_embedding(drink_id: int, drink_name: str, ingredients: Optional[List[str]] = None) -> List[float]:
    """Update a drink's embedding and add to FAISS index"""
    embedding = get_drink_embedding(drink_name, ingredients)
    
    # Update database
    with Session(engine) as session:
        drink = session.get(Drink, drink_id)
        if drink:
            drink.embedding = embedding
            session.commit()
    
    # Update FAISS index
    drink_index.add_drink_embedding(drink_id, embedding)
    
    return embedding

def find_similar_drinks(drink_name: str, ingredients: Optional[List[str]] = None, k: int = 5) -> List[Tuple[int, float]]:
    """Find similar drinks using FAISS"""
    query_embedding = get_drink_embedding(drink_name, ingredients)
    return drink_index.search_similar_drinks(query_embedding, k) 