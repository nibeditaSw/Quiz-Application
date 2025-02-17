import random
import requests
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import Question

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Fetch Questions from Open Trivia API
# def fetch_questions_from_api():
#     url = "https://opentdb.com/api.php?amount=10&category=18&difficulty=easy"
#     response = requests.get(url)

#     if response.status_code == 200:
#         data = response.json()
#         return data.get("results", [])  # Extract the results list
#     return []


# Store Questions in Database
def store_questions_in_db(db: Session):
    url = "https://opentdb.com/api.php?amount=10&category=18&difficulty=easy"
    response = requests.get(url).json()

    if isinstance(response, dict) and 'results' in response:
        questions = response['results']

        for item in questions:
            question_text = item['question']
            correct_answer = item['correct_answer']
            incorrect_answers = item['incorrect_answers']
            category = item.get('category', 'General Knowledge')  # Default category if not present
            difficulty = item.get('difficulty', 'easy')  # Default difficulty if not present

            # Shuffle answers
            all_answers = [correct_answer] + [incorrect_answers]
            random.shuffle(all_answers)

            # Ensure answers list contains 4 options
            if len(all_answers) < 4:
                continue

            option_a = all_answers[0]
            option_b = all_answers[1]
            option_c = all_answers[2] if len(all_answers) > 2 else None
            option_d = all_answers[3] if len(all_answers) > 3 else None

            # Ensure category, difficulty, and all options are provided when creating the Question
            new_question = Question(
                category=category,
                difficulty=difficulty,
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_option=correct_answer
            )
            db.add(new_question)

        db.commit()
    else:
        print("Error: Response format is incorrect or 'results' key not found.")
