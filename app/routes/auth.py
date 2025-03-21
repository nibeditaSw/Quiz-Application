import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import func
from app.database import get_db
from app.crud import create_user, get_user_by_username, get_user_login
from app.utils import verify_password, store_questions_in_db, get_current_user
from app.schemas import UserCreate
from app.models import User, Question, QuizAttempt, Admin, UserQuizStats

# Configure logging
logging.basicConfig(
    # filename="user_quiz.log",
    # filemode="a",
    format="{asctime} | {levelname} | {message}",
    datefmt="%d-%b-%y %H:%M:%S",
    level=20,
    style="{"
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/register")
def register_page(request: Request):
    """
    GET /register

    Displays the registration page for the user to input username, email, and password.
    The page is rendered using the register.html template from the app/templates directory.
    The request object is passed to the template to access session data, cookies, etc.

    Returns:
        templates.TemplateResponse: Rendered HTML template for the registration page
    """
    logging.info("Accessed register page")
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Handles user registration by processing form data submitted via POST request.
    
    Args:
        request (Request): The HTTP request object containing metadata about the request.
        username (str): The username provided by the user in the registration form.
        email (str): The email address provided by the user in the registration form.
        password (str): The password provided by the user in the registration form.
        db (Session): The database session used for querying and saving user data.
    
    Returns:
        TemplateResponse: Renders the registration page with an error message if registration fails.
        RedirectResponse: Redirects to the login page upon successful registration.
    
    Logs:
        Warning: If the username or email already exists in the database.
        Info: When a new user is successfully registered.
    """

    user = get_user_by_username(db, username, email)
    if user:
        logging.warning(f"Registration failed: Username {username} & Email {email} already exists.")
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username or Email already exists!"})
    create_user(db, UserCreate(username=username, email=email, password=password))
    logging.info(f"New user registered: {username}")
    return RedirectResponse(url="/login", status_code=303)


@router.get("/")
@router.get("/login")
def login_page(request: Request):
    """
    Handles GET requests to the root URL (/) and the login page (/login), rendering the login.html template.

    Args:
        request (Request): The HTTP request object containing metadata about the request.

    Returns:
        TemplateResponse: Renders the login.html template with the request object as context.
    """
    logging.info("Accessed login page")
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/")
@router.post("/login")
def login_user(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Handles POST requests to the root URL (/) and the login page (/login), validating
    the provided username and password and redirecting to either the admin panel or the
    quiz page based on the user's type.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        username (str): The username provided by the user in the login form.
        password (str): The password provided by the user in the login form.
        db (Session): The database session used for querying and verifying user data.

    Returns:
        TemplateResponse: Renders the login.html template with an error message if the
            credentials are invalid.
        RedirectResponse: Redirects to the admin panel (/admin) if the user is an admin,
            or to the quiz page (/home) if the user is a normal user.

    Logs:
        Info: When an admin or user logs in successfully.
        Warning: When a login attempt fails.
    """
    # First, check if the user is an admin
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin and verify_password(password, admin.hashed_password):
        logging.info(f"Admin login successful: {username}")
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie("is_admin", "true", httponly=True, secure=True)
        return response

    # Otherwise, check if it's a normal user
    user = get_user_login(db, username)  
    if not user or not verify_password(password, user.hashed_password):
        logging.warning(f"Failed login attempt for username: {username}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Invalid credentials"}
        )
    
    logging.info(f"User login successful: {username}")
    response = RedirectResponse(url="/home", status_code=303)
    response.set_cookie("user_id", str(user.id), httponly=True, secure=True)
    return response


@router.get("/questions")
def questions(request: Request, db: Session = Depends(get_db), category: str = None, difficulty: str = None):
    """
    Handles GET requests to the /questions route, fetching and rendering a set of
    questions based on the provided category and difficulty filters.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying and storing questions.
        category (str): The category to filter questions by (optional).
        difficulty (str): The difficulty to filter questions by (optional).

    Returns:
        TemplateResponse: Renders the questions.html template with the request object and
            a list of questions as context.

    Logs:
        Warning: When an unauthorized user attempts to access the questions.
        Info: When a user successfully accesses the questions.
    """
    
    user = get_current_user(request, db)
    if not user:
        logging.warning("Unauthorized access to questions")
        return RedirectResponse(url="/login", status_code=303)

    logging.info(f"User {user.username} accessed questions")
    # Check if questions exist in DB; if not, fetch and store them
    if db.query(Question).count() == 0:
        store_questions_in_db(db)
    
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
    return templates.TemplateResponse("questions.html", {
        "request": request,
        "user": user,
        "questions": questions
    })


@router.post("/logout")
def logout():
    """
    Handles POST requests to the logout endpoint, clearing the session cookie and redirecting
    the user to the login page.

    Returns:
        RedirectResponse: Redirects to the login page and clears the session cookie.

    Logs:
        Info: When a user logs out.
    """
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")  # Clear session cookie
    logging.info("User logged out")
    return response


@router.post("/submit-quiz")
async def submit_quiz(request: Request, db: Session = Depends(get_db)):
    """
    Handles POST requests to the /submit-quiz route, extracting form data, validating
    answers, updating user scores and statistics, and rendering the result page.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying and storing questions and user data.

    Returns:
        TemplateResponse: Renders the result.html template with the request object, score, and
            total attempted questions as context.

    Logs:
        Info: When a user submits a quiz and receives a score.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Retrieve form data
    form_data = await request.form()

    # Generate a unique session ID (e.g., current timestamp)
    session_id = int(datetime.utcnow().timestamp())

    # Extract the question IDs
    question_ids = [int(key[1:]) for key in form_data.keys() if key.startswith("q")]
    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    score = 0

    for q in questions:
        user_answer_key = form_data.get(f"q{q.id}")

        # Mapping user selection to actual answer
        option_mapping = {
            "a": q.option_a,
            "b": q.option_b,
            "c": q.option_c,
            "d": q.option_d,
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
            session_id=session_id,
        )
        db.add(attempt)

        # Update or create user quiz stats
        user_quiz_stat = (
            db.query(UserQuizStats)
            .filter(
                UserQuizStats.user_id == user.id,
                UserQuizStats.category == q.category,
                UserQuizStats.difficulty == q.difficulty,
            )
            .first()
        )

        if user_quiz_stat:
            user_quiz_stat.solved_count += 1  # Increment total attempts
            if is_correct:
                user_quiz_stat.correct_count += 1  # Increment correct answers
        else:
            new_stat = UserQuizStats(
                user_id=user.id,
                category=q.category,
                difficulty=q.difficulty,
                solved_count=1,
                correct_count=1 if is_correct else 0,
            )
            db.add(new_stat)

    user.score += score
    db.commit()

    total_attempted = len(questions)

    logging.info(f"User {user.username} submitted a quiz - Score: {score}/{len(questions)}")
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "score": score,
            "total_attempted": total_attempted,
            "session_id": session_id,  # Pass session_id for review
        },
    )


@router.get("/review-quiz")
async def review_quiz(request: Request, session_id: int, db: Session = Depends(get_db)):
    """
    Handles GET requests to the /review-quiz route, displaying the latest quiz
    submission's results.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        session_id (int): The session ID of the quiz submission to review.
        db (Session): The database session used for querying the user's attempts.

    Returns:
        TemplateResponse: Renders the review.html template with the request object and
            the latest quiz attempts as context.

    Logs:
        Info: When a user reviews a quiz session.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Fetch only the latest session
    latest_attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.session_id == session_id)
        .all()
    )

    logging.info(f"User {user.username} reviewed quiz session {session_id}")
    return templates.TemplateResponse("review.html", {
        "request": request,
        "quiz_attempts": latest_attempts
    })


@router.get("/home")
def start_quiz(request: Request, db: Session = Depends(get_db)):
    """
    Handles GET requests to the /home route, displaying the quiz start page with
    available categories, difficulty levels, top users, and the current user's stats.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying the user's stats and fetching
            available categories and difficulty levels.

    Returns:
        TemplateResponse: Renders the home.html template with the request object, user,
            categories, difficulties, top users, and user stats as context.

    Logs:
        Info: When the quiz start page is rendered.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Fetch available categories from DB (assuming Question has a category field)
    categories = db.query(Question.category).distinct().all()

    # Fetch distinct difficulty levels from the DB and extract the values
    difficulties = db.query(Question.difficulty).distinct().all()
    
    top_users = db.query(User).order_by(User.score.desc()).limit(5).all()
    
    user_stats = db.query(UserQuizStats).order_by(UserQuizStats.correct_count.desc()).all()
    
    logging.info("Rendering quiz start page")
    return templates.TemplateResponse("home.html", {
        "request": request, 
        "user": user, 
        "categories": categories,
        "difficulties": difficulties,
        "top_users": top_users,
        "user_stats": user_stats
    })


@router.post("/home")
async def start_quiz_post(request: Request, db: Session = Depends(get_db)):
    """
    Handles POST requests to the /home route, extracting form data (category and difficulty),
    checking for valid user authentication, logging the quiz start event, and redirecting to
    the questions page with the selected category and difficulty.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying the user's stats and fetching
            available categories and difficulty levels.

    Returns:
        RedirectResponse: Redirects to the questions page with the selected category and
            difficulty.

    Logs:
        Info: When a user starts a new quiz.
    """
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Retrieve form data (category and difficulty)
    form_data = await request.form()
    category = form_data.get("category")
    difficulty = form_data.get("difficulty")

    logging.info(f"Quiz started with category: {category}, difficulty: {difficulty}")
    # Redirect to the questions with the selected category and difficulty
    return RedirectResponse(url=f"/questions?category={category}&difficulty={difficulty}", status_code=303)
