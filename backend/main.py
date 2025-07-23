from fastapi import FastAPI
from .routers import users, drinks, logs
from .faiss_utils import drink_index

app = FastAPI()

@app.on_event("startup")
def on_startup():
    # Rebuild FAISS index from existing drinks in database
    drink_index.rebuild_index_from_database()

app.include_router(users.router)
app.include_router(drinks.router)
app.include_router(logs.router) 