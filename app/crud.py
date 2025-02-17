from sqlalchemy.orm import Session
from app.models import User, Question
from app.schemas import UserCreate
from app.utils import hash_password

def create_user(db: Session, user: UserCreate):
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password, token=10, score=0)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


# def add_sample_questions(db: Session):
    
#     sample_questions = [
#         Question(
#             question_text="What is the capital of France?",
#             option_a="Berlin",
#             option_b="Madrid",
#             option_c="Paris",
#             option_d="Rome",
#             correct_option="c"
#         ),
#         Question(
#             question_text="Which planet is known as the Red Planet?",
#             option_a="Earth",
#             option_b="Mars",
#             option_c="Jupiter",
#             option_d="Venus",
#             correct_option="b"
#         ),
#         Question(
#             question_text="Who wrote 'To Kill a Mockingbird'?",
#             option_a="Harper Lee",
#             option_b="J.K. Rowling",
#             option_c="Ernest Hemingway",
#             option_d="Mark Twain",
#             correct_option="a"
#         )
#     ]
    
#     db.add_all(sample_questions)
#     db.commit()
