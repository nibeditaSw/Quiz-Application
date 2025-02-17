from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.database import SessionLocal
from app.crud import create_user, get_user_by_username
from app.utils import verify_password, store_questions_in_db
from app.schemas import UserCreate
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import User, Question

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
    
    # Check if questions exist in DB; if not, fetch and store them
    if db.query(Question).count() == 0:
        store_questions_in_db(db)

    # Retrieve 5 random questions from DB
    questions = db.query(Question).order_by(func.random()).limit(5).all()

    # # Fetch all quiz questions
    # questions = db.query(Question).all()
    print(f"Loaded {len(questions)} questions from DB")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "questions": questions})


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("user_id")  # Clear session cookie
    return response


# @router.post("/submit-quiz")
# async def submit_quiz(
#     request: Request,
#     db: Session = Depends(get_db)
# ):
#     user_id = request.cookies.get("user_id")

#     if not user_id:
#         return RedirectResponse(url="/auth/login", status_code=303)

#     user = db.query(User).filter(User.id == int(user_id)).first()
#     if not user:
#         return RedirectResponse(url="/auth/login", status_code=303)

#     # Await form data retrieval
#     form_data = await request.form()

#     questions = db.query(Question).all()
#     score = 0

#     for q in questions:
#         user_answer = form_data.get(f"q{q.id}")  # Retrieve user's answer
#         if user_answer and user_answer == q.correct_option:
#             score += 1  # Increase score for correct answers

#     user.score += score  # Update user's score
#     db.commit()

#     return RedirectResponse(url="/auth/dashboard", status_code=303)


@router.post("/submit-quiz")
async def submit_quiz(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = request.cookies.get("user_id")

    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Retrieve form data
    form_data = await request.form()
    # print("Form Data Received:", form_data)  

    # Extract the question IDs (remove 'q' prefix) from the form data
    question_ids = [int(key[1:]) for key in form_data.keys() if key.startswith('q')]

    # questions = db.query(Question).all()
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    score = 0

    for q in questions:
        user_answer_key = form_data.get(f"q{q.id}")  # Get user's selected option ('a', 'b', 'c', 'd')
        
        # Mapping user selection to actual answer
        option_mapping = {
            "a": q.option_a,
            "b": q.option_b,
            "c": q.option_c,
            "d": q.option_d
        }

        user_answer = option_mapping.get(user_answer_key)  # Convert 'a' -> 'actual full answer'

        # print(f"Q{q.id}: User Selected = {user_answer_key} ({user_answer}), Correct Answer = {q.correct_option}")  

        if user_answer and user_answer == q.correct_option:
            # print(f"Correct Answer for Q{q.id}!")  
            score += 1  # Increase score for correct answers

    # print(f"User Score Before Update: {user.score}, New Score: {score}")

    # Update user's score
    user.score += score
    db.commit()

    total_attempted = len(questions)

    # Redirect to results page with necessary data
    return templates.TemplateResponse("result.html", {"request": request, "score": score, "total_attempted": total_attempted})
