from fastapi import APIRouter, Depends, HTTPException, Request, Form
from sqlalchemy.orm import Session
from app.database import get_db
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.models import User, Question, AdminQuestion

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin")
def admin_page(request: Request, db: Session = Depends(get_db)):
    is_admin = request.cookies.get("is_admin")
    
    if is_admin != "true":
        return RedirectResponse(url="/auth/login", status_code=303)

    # questions = db.query(Question).all()  # Fetch all questions
    users = db.query(User).all()  # Fetch all users

    return templates.TemplateResponse("admin.html", {
        "request": request,
        # "questions": questions,
        "users": users,
    })

# Edit User Page 
@router.get("/admin/edit/{user_id}")
def edit_user_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("edit_user.html", {"request": request, "user": user})

# Update User Data 
@router.post("/admin/edit/{user_id}")
def update_user(request: Request, user_id: int, score: int = Form(...), db: Session = Depends(get_db)):
    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/auth/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.score = score
    db.commit()
    return RedirectResponse(url="/admin/admin", status_code=303)

# Delete User
@router.post("/admin/delete/{user_id}")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/auth/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin/admin", status_code=303)


# Question List Page
@router.get("/admin/questions")
def admin_questions(request: Request, db: Session = Depends(get_db)):
    questions = db.query(AdminQuestion).all()
    return templates.TemplateResponse("admin_questions.html", {"request": request, "questions": questions})


# Create Question Page (GET)
@router.get("/admin/create-question")
def create_question_page(request: Request):
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
    is_admin = request.cookies.get("is_admin")

    if is_admin != "true":
        return RedirectResponse(url="/auth/login", status_code=303)
    
    new_question = AdminQuestion(
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_option=correct_option,
        category=category,
        difficulty=difficulty,
    )

    db.add(new_question)
    db.commit()
    return RedirectResponse(url="/admin/admin/questions", status_code=303)


# edit Question(GET)
@router.get("/admin/edit-question/{id}")
def edit_question(request: Request, id: int, db: Session = Depends(get_db)):
    question = db.query(AdminQuestion).filter(AdminQuestion.id == id).first()
    if not question:
        return {"error": "Question not found"}
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
    db_question = db.query(AdminQuestion).filter(AdminQuestion.id == id).first()
    if not db_question:
        return {"error": "Question not found"}

    db_question.question_text = question_text
    db_question.option_a = option_a
    db_question.option_b = option_b
    db_question.option_c = option_c
    db_question.option_d = option_d
    db_question.correct_option = correct_option
    db_question.category = category
    db_question.difficulty = difficulty

    db.commit()
    return RedirectResponse(url="/admin/admin/questions", status_code=303)

# Delete Question
@router.post("/admin/delete-question/{id}")
def delete_question(id: int, db: Session = Depends(get_db)):
    question = db.query(AdminQuestion).filter(AdminQuestion.id == id).first()
    if not question:
        return {"error": "Question not found"}

    db.delete(question)
    db.commit()
    return RedirectResponse(url="/admin/admin/questions", status_code=303)