from fastapi import FastAPI
from app.routes import auth

app = FastAPI()

app.include_router(auth.router, prefix="/auth")

@app.get("/")
def home():
    return {"message": "Welcome to FastAPI Quiz Application"}
