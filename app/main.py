from fastapi import FastAPI
from app.routes import auth
from app.routes import admin

app = FastAPI()

app.include_router(auth.router, prefix="/auth")
app.include_router(admin.router, prefix="/admin")

@app.get("/")
def home():
    return {"message": "Welcome to FastAPI Quiz Application"}
