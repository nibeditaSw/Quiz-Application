from fastapi import FastAPI
from app.routes import auth
from app.routes import admin

app = FastAPI()

app.include_router(auth.router)
app.include_router(admin.router)

# @app.get("/")
# def home():
#     return {"message": "Welcome to FastAPI Quiz Application"}
