from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.crud import create_user, get_user_by_username
from app.utils import verify_password
from app.schemas import UserCreate
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already exists!"})
    create_user(db, UserCreate(username=username, email=email, password=password))
    return RedirectResponse(url="/auth/login", status_code=303)

@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    response = RedirectResponse(url="/auth/dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))  # Set user ID in cookies
    return response

@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)  # Redirect if not logged in
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@router.post("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("user_id")  # Clear session cookie
    return response

