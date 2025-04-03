import random
import requests
from fastapi import Request
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models import Question, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()


def store_questions_in_db(db: Session):
    # URLs for fetching questions
    urls = [
        "https://opentdb.com/api.php?amount=50&category=18&type=multiple",
        "https://opentdb.com/api.php?amount=50&category=9&type=multiple",
        "https://opentdb.com/api.php?amount=50&category=23&type=multiple"
    ]

    # Delete all existing questions from the database before adding new ones
    # db.query(Question).delete()

    # Iterate over each URL and fetch the questions
    for url in urls:
        print(f"Fetching questions from: {url}")
        try:
            response = requests.get(url).json()

            # Print the entire response to understand the structure
            print(f"Response from URL {url}: {response}")

            # Check for a valid response and handle empty results
            if response.get("response_code") == 5:
                print(f"Error: No questions found for URL: {url}")
                continue

            # Check if the response contains 'results' and is valid
            if isinstance(response, dict) and 'results' in response:
                questions = response['results']
                print(f"Found {len(questions)} questions from URL: {url}")

                # Loop through the questions and insert into the database
                for item in questions:
                    question_text = item['question']
                    correct_answer = item['correct_answer']
                    incorrect_answers = item['incorrect_answers']
                    category = item.get('category', 'General Knowledge')
                    difficulty = item.get('difficulty', 'easy')

                    # Shuffle answers
                    all_answers = [correct_answer] + incorrect_answers
                    random.shuffle(all_answers)

                    # Ensure answers list contains 4 options
                    if len(all_answers) < 4:
                        continue

                    option_a = all_answers[0]
                    option_b = all_answers[1]
                    option_c = all_answers[2] if len(all_answers) > 2 else None
                    option_d = all_answers[3] if len(all_answers) > 3 else None

                    # Add new question to the database
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

                # Commit after processing each URL's questions
                db.commit()

                print(f"Successfully added {len(questions)} questions from URL: {url}")
            else:
                print(f"Error: No 'results' key found in the response for URL: {url}")

        except requests.exceptions.RequestException as e:
            print(f"Request error for URL {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for URL {url}: {e}")

    print("All questions from all URLs have been processed and stored.")
