from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List, Any
from datetime import datetime
import sqlalchemy as sa

class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    timezone: Optional[str] = None
    prefs: Optional[dict] = Field(default=None, sa_column=Column(sa.JSON))  # {ingredient: weight, ...}
    drinks: List["Drink"] = Relationship(back_populates="creator")
    logs: List["UserDrinkLog"] = Relationship(back_populates="user")

class Drink(SQLModel, table=True):
    drink_id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    ingredients_json: Optional[Any] = Field(default=None, sa_column=Column(sa.JSON))
    measures_json: Optional[Any] = Field(default=None, sa_column=Column(sa.JSON))  # Parallel to ingredients_json
    instructions: Optional[str] = None
    created_by_user_id: Optional[int] = Field(default=None, foreign_key="user.user_id")
    embedding: Optional[List[float]] = Field(default=None, sa_column=Column(sa.PickleType))
    # TheCocktailDB fields
    cocktail_db_id: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    alcoholic: Optional[str] = None
    glass: Optional[str] = None
    creator: Optional[User] = Relationship(back_populates="drinks")
    logs: List["UserDrinkLog"] = Relationship(back_populates="drink")

class UserDrinkLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id")
    drink_id: Optional[int] = Field(default=None, foreign_key="drink.drink_id")
    name: str  # Always store the drink name
    quantity: Optional[float] = None
    units: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user: Optional[User] = Relationship(back_populates="logs")
    drink: Optional[Drink] = Relationship(back_populates="logs") 