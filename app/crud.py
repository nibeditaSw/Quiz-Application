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

def get_user_by_username(db: Session, username: str, email: str):
    return db.query(User).filter((User.username == username) | (User.email == email)).first()

def get_user_login(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


