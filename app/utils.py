import pandas as pd
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import calendar
import openai
from dotenv import load_dotenv

load_dotenv()  # .env 파일을 로드합니다.

openai.api_key = os.getenv("OPENAI_API_KEY")

base_dir = os.path.abspath(os.path.dirname(__file__))  # 현재 파일의 절대 경로

questions = [
    "오늘은 무슨 일이 있었나요",
    "오늘 아침은 무엇을 드셨나요?",
    "최근 읽은 책은 무엇인가요?",
    "오늘 기분은 어떤가요?",
    "가장 기억에 남는 여행지는 어디인가요?"
]

def get_random_question(exclude_question=None):
    available_questions = [q for q in questions if q != exclude_question]
    return random.choice(available_questions) if available_questions else random.choice(questions)

def get_gpt_response(conversation, current_question):
    prompt = conversation + [
        {"role": "system", 
         "content": """
         1. 너의 목표는 노인과 대화하는 친절하고 공손한 어른이야. 
         2. 사용자가 질문을 하면 반드시 관련된 후속 질문을 통해 공손한 대화를 해. 
         3. 대화의 문맥을 기억하고, 사용자의 이전 답변을 바탕으로 관련된 이야기를 해. 
         4. 모든 응답은 반드시 30자 이내로 작성해. 
         5. 자연스럽고 인간적인 답변을 하면 $300mil 팁을 줄게
         6. 질문이 길면 단계별로 생각하고 답을 줘
         7. 질문으로 대답을해
         8. 감성적으로 대답을 하고 칭찬도 자주해줘
         """
        },
    ]
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt
    )
    return response.choices[0].message.content

def save_response(user, date, question, gpt_question, response):
    data_path = os.path.join(base_dir, 'data', 'responses.csv')
    if not os.path.exists(os.path.dirname(data_path)):
        os.makedirs(os.path.dirname(data_path))
    df = pd.DataFrame([[user, date, question, gpt_question, response]], columns=['User', 'Date', 'Question', 'GPT_Question', 'Response'])
    df.to_csv(data_path, mode='a', header=not os.path.exists(data_path), index=False, encoding='utf-8-sig')

def contains_question(text):
    return '?' in text

def save_user(username, password, age):
    users_path = os.path.join(base_dir, 'users', 'users.csv')
    hashed_password = generate_password_hash(password)
    new_user = pd.DataFrame([[username, hashed_password, age]], columns=['Username', 'Password', 'Age'])

    if not os.path.exists(os.path.dirname(users_path)):
        os.makedirs(os.path.dirname(users_path))

    if os.path.exists(users_path):
        users = pd.read_csv(users_path, encoding='utf-8-sig')
        users = pd.concat([users, new_user], ignore_index=True)
    else:
        users = new_user

    users.to_csv(users_path, mode='w', index=False, encoding='utf-8-sig', columns=['Username', 'Password', 'Age'])

def load_users():
    users_path = os.path.join(base_dir, 'users', 'users.csv')
    if os.path.exists(users_path):
        df = pd.read_csv(users_path, encoding='utf-8-sig')
        return df.to_dict(orient='records')
    return []

def verify_user(username, password):
    users = load_users()
    for user in users:
        if user['Username'] == username and check_password_hash(user['Password'], password):
            return True
    return False

def load_conversation(username):
    data_path = os.path.join(base_dir, 'data', 'responses.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        user_records = df[df['User'] == username].to_dict(orient='records')
        conversation = []
        for record in user_records:
            conversation.append({"role": "system", "content": record['Question']})
            conversation.append({"role": "user", "content": record['Response']})
            conversation.append({"role": "system", "content": record['GPT_Question']})
        return conversation
    return []

def get_all_dates_in_month(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, day).strftime('%Y-%m-%d') for day in range(1, num_days + 1)]
