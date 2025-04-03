import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Question, QuizAttempt

# Configure logging
logging.basicConfig(
    # filename="admin_quiz.log",
    # filemode="a",
    format="{asctime} | {levelname} | {message}",
    datefmt="%d-%b-%y %H:%M:%S",
    level=20,
    style="{"
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    """
    Handles GET requests to the /admin route, rendering the admin home page
    if the user is authenticated as an admin.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying user data.

    Returns:
        RedirectResponse: Redirects to the login page if the user is not authenticated as an admin.
        TemplateResponse: Renders the admin.html template with the request object and a list of users.

    Logs:
        Info: When the admin accesses the home page.
    """

    is_admin = request.cookies.get("is_admin")
    
    if is_admin != "true":
        return RedirectResponse(url="/login", status_code=303)

    # questions = db.query(Question).all()  # Fetch all questions
    users = db.query(User).all()  # Fetch all users

    logging.info("Admin accessed the Home page.")
    return templates.TemplateResponse("admin.html", {
        "request": request,
        # "questions": questions,
        "users": users,
    })

@router.post("/admin-logout")
def logout():
    """
    Handles POST requests to the admin logout endpoint, clearing the admin session
    cookie and redirecting the user to the login page.

    Returns:
        RedirectResponse: Redirects to the login page and clears the admin session cookie.

    Logs:
        Info: When an admin logs out.
    """

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("is_admin")  # Clear session cookie
    logging.info("Admin logged out.")
    return response


# Edit User Page 
@router.get("/admin/edit/{user_id}")
def edit_user_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Handles GET requests to the admin edit user endpoint, displaying the edit user page
    for the specified user ID.

    Args:
        user_id (int): The ID of the user to edit.
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying and verifying user data.

    Returns:
        TemplateResponse: Renders the edit_user.html template with the specified user's data.

    Raises:
        HTTPException: If the user is not found or the admin session cookie is invalid.

    Logs:
        Info: When an admin accesses the edit page for a user.
    """
    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    logging.info(f"Admin accessed edit page for user {user_id}.")
    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})

# Update User Data 
@router.post("/admin/edit/{user_id}")
def update_user(request: Request, user_id: int, score: int = Form(...), db: Session = Depends(get_db)):
    """
    Handles POST requests to the admin edit user endpoint, updating the user's score.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        user_id (int): The ID of the user to edit.
        score (int): The new score for the user.
        db (Session): The database session used for querying and verifying user data.

    Returns:
        RedirectResponse: Redirects to the admin page after updating the user's score.

    Raises:
        HTTPException: If the user is not found or the admin session cookie is invalid.

    Logs:
        Info: When an admin updates a user's score.
    """

    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.score = score
    db.commit()
    logging.info(f"Admin updated user {user_id}'s score to {score}.")
    return RedirectResponse(url="/admin", status_code=303)

# Delete User
@router.post("/admin/delete/{user_id}")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    """
    Handles POST requests to the admin delete user endpoint, deleting the user.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        user_id (int): The ID of the user to delete.
        db (Session): The database session used for querying and verifying user data.

    Returns:
        RedirectResponse: Redirects to the admin page after deleting the user.

    Raises:
        HTTPException: If the user is not found or the admin session cookie is invalid.

    Logs:
        Info: When an admin deletes a user.
    """

    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    logging.info(f"Admin deleted user {user_id}.")
    return RedirectResponse(url="/admin", status_code=303)


# Question List Page
@router.get("/admin/questions")
def admin_questions(request: Request, db: Session = Depends(get_db), search: str = ""):
    """
    Handles GET requests to the admin questions endpoint, displaying a list of questions
    that match the search query.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        db (Session): The database session used for querying and verifying question data.
        search (str): The search query to filter questions by.

    Returns:
        TemplateResponse: Renders the admin_questions.html template with the list of questions
            and the search query as context.

    Raises:
        HTTPException: If the admin session cookie is invalid.

    Logs:
        Info: When an admin accesses the question list.
    """
    query = db.query(Question)

    if search:
        # filtering by ID if the search is numeric
        if search.isdigit():
            query = query.filter(Question.id == int(search))
        else:
            # search by category or difficulty or question text
            query = query.filter(
                (Question.category.ilike(f"%{search}%")) | 
                (Question.difficulty.ilike(f"%{search}%")) |
                (Question.question_text.ilike(f"%{search}%"))
            )

    questions = query.all()

    logging.info("Admin accessed the question list.")
    return templates.TemplateResponse(
        "admin_questions.html",
        {"request": request, "questions": questions, "search_query": search}
    )


# Create Question Page (GET)
@router.get("/admin/create-question")
def create_question_page(request: Request):
    """
    Handles GET requests to the admin create-question endpoint, rendering the
    page for creating a new question.

    Args:
        request (Request): The HTTP request object containing metadata about the request.

    Returns:
        TemplateResponse: Renders the create_question.html template with the request object.

    Logs:
        Info: When the admin accesses the create question page.
    """

    logging.info("Admin accessed create question page.")
    return templates.TemplateResponse("create_question.html", {"request": request})

# Create Question (POST)
@router.post("/admin/create-question")
def create_question(
    request: Request,
    question_text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Handles POST requests to the /admin/create-question endpoint, creating a new
    question in the database.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        question_text (str): The text of the new question.
        option_a, option_b, option_c, option_d (str): The four options for the question.
        correct_option (str): The correct answer for the question.
        category (str): The category of the question.
        difficulty (str): The difficulty of the question.
        db (Session): The database session used for querying and storing questions.

    Returns:
        RedirectResponse: Redirects to the /admin/questions page after creating the question.

    Logs:
        Info: When the admin creates a new question.
    """
    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/login", status_code=303)
    
    options_map = {
        "A": option_a,
        "B": option_b,
        "C": option_c,
        "D": option_d
    }
    correct_answer_value = options_map.get(correct_option, "")
    
    new_question = Question(
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_answer_value,
        category=category,
        difficulty=difficulty,
        admincreated=True,
    )

    db.add(new_question)
    db.commit()
    logging.info("Admin created a new question.")
    return RedirectResponse(url="/admin/questions", status_code=303)


# edit Question(GET)
@router.get("/admin/edit-question/{id}")
def edit_question(request: Request, id: int, db: Session = Depends(get_db)):
    """
    Handles GET requests to the /admin/edit-question/{id} endpoint, rendering the
    edit_question.html template with the question data if the question exists.

    Args:
        request (Request): The HTTP request object containing metadata about the request.
        id (int): The ID of the question to edit.
        db (Session): The database session used for querying questions.

    Returns:
        TemplateResponse: Renders the edit_question.html template with the question data.
        dict: Returns a dictionary with an "error" key if the question is not found.

    Logs:
        Warning: When a question with the given ID is not found.
        Info: When the edit_question.html template is rendered.
    """
    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        logging.warning(f"Question with ID {id} not found.")
        return {"error": "Question not found"}
    logging.info(f"Rendering edit_question.html for Question ID {id}")
    return templates.TemplateResponse("edit_question.html", {"request": request, "question": question})


# edit Question(POST)
@router.post("/admin/edit-question/{id}")
def update_question(
    id: int,
    question_text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_option: str = Form(...),
    category: str = Form(...),
    difficulty: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Handles POST requests to the /admin/edit-question/{id} endpoint, updating the
    existing question in the database with the given ID.

    Args:
        id (int): The ID of the question to update.
        question_text (str): The new text for the question.
        option_a, option_b, option_c, option_d (str): The new options for the question.
        correct_option (str): The new correct answer for the question.
        category (str): The new category for the question.
        difficulty (str): The new difficulty for the question.
        db (Session): The database session used for querying and updating questions.

    Returns:
        RedirectResponse: Redirects to the /admin/questions page after updating the question.

    Logs:
        Warning: When a question with the given ID is not found.
        Info: When the question is updated and redirected to /admin/questions.
    """
    db_question = db.query(Question).filter(Question.id == id).first()
    if not db_question:
        logging.warning(f"Question with ID {id} not found for update.")
        return {"error": "Question not found"}
    
    options_map = {
        "A": option_a,
        "B": option_b,
        "C": option_c,
        "D": option_d
    }
    correct_answer_value = options_map.get(correct_option, "")

    db_question.question_text = question_text
    db_question.option_a = option_a
    db_question.option_b = option_b
    db_question.option_c = option_c
    db_question.option_d = option_d
    db_question.correct_option = correct_answer_value
    db_question.category = category
    db_question.difficulty = difficulty

    db.commit()
    logging.info(f"Updated Question ID {id} and redirecting to /admin/questions")
    return RedirectResponse(url="/admin/questions", status_code=303)

# Delete Question
@router.post("/admin/delete-question/{id}")
def delete_question(id: int, db: Session = Depends(get_db)):
    """
    Handles POST requests to delete a question by ID from the database.

    Args:
        id (int): The ID of the question to delete.
        db (Session): The database session used for querying and deleting question data.

    Returns:
        RedirectResponse: Redirects to the /admin/questions page after deletion.
        dict: Returns a dictionary with an "error" key if the question is not found.

    Logs:
        Warning: When a question with the given ID is not found for deletion.
        Info: When a question is successfully deleted and redirected to /admin/questions.
    """

    question = db.query(Question).filter(Question.id == id).first()
    if not question:
        logging.warning(f"Question with ID {id} not found for deletion.")
        return {"error": "Question not found"}
    
    # Delete related quiz attempts before deleting the question
    db.query(QuizAttempt).filter(QuizAttempt.question_id == id).delete()

    db.delete(question)
    db.commit()
    logging.info(f"Deleted Question ID {id} and redirecting to /admin/questions")
    return RedirectResponse(url="/admin/questions", status_code=303)