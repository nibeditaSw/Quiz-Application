from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.database import SessionLocal, get_db
from app.crud import create_user, get_user_by_username
from app.utils import verify_password, store_questions_in_db
from app.schemas import UserCreate
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import User, Question, QuizAttempt

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


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
    response = RedirectResponse(url="/auth/start-quiz", status_code=303)
    response.set_cookie(key="user_id", value=str(user.id))  # Set user ID in cookies
    return response



@router.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), category: str = None, difficulty: str = None):
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Check if questions exist in DB; if not, fetch and store them
    # if db.query(Question).count() == 0:
    #     store_questions_in_db(db)
    
    # Build the query for fetching questions
    query = db.query(Question)
    
    # Apply filters based on category and difficulty if provided
    if category:
        query = query.filter(Question.category == category)
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    # Limit to 5 questions
    questions = query.order_by(func.random()).limit(5).all()

    # Render the template with the questions
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "questions": questions
    })



@router.post("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("user_id")  # Clear session cookie
    return response


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

    # Generate a unique session ID (e.g., current timestamp)
    session_id = int(datetime.utcnow().timestamp())

    # Extract the question IDs
    question_ids = [int(key[1:]) for key in form_data.keys() if key.startswith('q')]
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    score = 0

    for q in questions:
        user_answer_key = form_data.get(f"q{q.id}")  
        
        # Mapping user selection to actual answer
        option_mapping = {
            "a": q.option_a,
            "b": q.option_b,
            "c": q.option_c,
            "d": q.option_d
        }
        user_answer = option_mapping.get(user_answer_key)  

        # Check if correct
        is_correct = user_answer == q.correct_option
        if is_correct:
            score += 1  

        # Store the attempt
        attempt = QuizAttempt(
            user_id=user.id,
            question_id=q.id,
            user_answer=user_answer,
            correct_answer=q.correct_option,
            is_correct=is_correct,
            session_id=session_id
        )
        db.add(attempt)

    user.score += score
    db.commit()

    total_attempted = len(questions)

    return templates.TemplateResponse("result.html", {
        "request": request,
        "score": score,
        "total_attempted": total_attempted,
        "session_id": session_id  # Pass session_id for review
    })


@router.get("/review-quiz")
async def review_quiz(request: Request, session_id: int, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Fetch only the latest session
    latest_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.session_id == session_id)
        .all()
    )

    return templates.TemplateResponse("review.html", {
        "request": request,
        "quiz_attempts": latest_attempts
    })


@router.get("/start-quiz")
def start_quiz(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)  # Redirect if not logged in
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    # Fetch available categories from DB (assuming Question has a category field)
    categories = db.query(Question.category).distinct().all()

    # Fetch distinct difficulty levels from the DB and extract the values
    difficulties = [difficulty[0] for difficulty in db.query(Question.difficulty).distinct().all()]
    
    top_users = db.query(User).order_by(User.score.desc()).limit(5).all()
    
    return templates.TemplateResponse("quiz_start.html", {
        "request": request, 
        "user": user, 
        "categories": categories,
        "difficulties": difficulties,
        "top_users": top_users
    })


@router.post("/start-quiz")
async def start_quiz_post(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    
    # Retrieve form data (category and difficulty)
    form_data = await request.form()
    category = form_data.get("category")
    difficulty = form_data.get("difficulty")

    # Redirect to the dashboard with the selected category and difficulty
    return RedirectResponse(url=f"/auth/dashboard?category={category}&difficulty={difficulty}", status_code=303)
