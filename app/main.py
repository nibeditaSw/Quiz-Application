from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import auth

app = FastAPI()

# app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router, prefix="/auth")

@app.get("/")
def home():
    return {"message": "Welcome to FastAPI Quiz Application"}
