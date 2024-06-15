import pandas as pd
import random
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import calendar
import openai
from dotenv import load_dotenv


load_dotenv()  # .env 파일을 로드합니다.

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

openai.api_key = os.getenv("OPENAI_API_KEY")

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


def summarize_responses(responses):
    prompt = "다음은 사용자의 응답 목록입니다. 이 응답들을 요약하여 일기 형태로 작성하세요:\n\n"
    for response in responses:
        prompt += f"- {response}\n"
    
    prompt += "\n요약된 일기:"
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",  
        messages=[{"role": "system", "content": prompt}]
    )
    
    summary = response.choices[0].message.content
    return summary

def save_response(user, date, question, gpt_question, response):
    data_dir = os.path.join(base_dir, 'app', 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, 'responses.csv')
    df = pd.DataFrame([[user, date, question, gpt_question, response]], columns=['User', 'Date', 'Question', 'GPT_Question', 'Response'])
    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False, encoding='utf-8-sig')

def save_user(username, password, age):
    user_dir = os.path.join(base_dir, 'app', 'users')
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, 'users.csv')
    df = pd.DataFrame([[username, generate_password_hash(password), age]], columns=['Username', 'Password', 'Age'])
    df.to_csv(file_path, mode='a', header=not os.path.exists(file_path), index=False, encoding='utf-8-sig')

def load_users():
    file_path = os.path.join(base_dir, 'app', 'users', 'users.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        return df.to_dict(orient='records')
    return []

def verify_user(username, password):
    users = load_users()
    for user in users:
        if user['Username'] == username and check_password_hash(user['Password'], password):
            return True
    return False
def save_guardian(username,password,age,ward_username):
    guardian_dir=os.path.join(base_dir,'app','guardian')
    os.makedirs(guardian_dir,exist_ok=True)
    file_path=os.path.join(guardian_dir,'guardian.csv')
    df = pd.DataFrame([[username, generate_password_hash(password), age, ward_username]], columns=['Username', 'Password', 'Age', 'Ward_username'])
    df.to_csv(file_path,mode='a',header=not os.path.exists(file_path),index=False,encoding='utf-8-sig')

def load_guardian():
    file_path=os.path.join(base_dir,'app','guardian','guardian.csv')
    if os.path.exists(file_path):
        df=pd.read_csv(file_path,encoding='utf-8-sig')
        return df.to_dict(orient='records')
    return []

def verify_guardian(username,password,ward_username):
    guardians=load_guardian()
    for guardian in guardians:
        if guardian['Username']==username and check_password_hash(guardian['Password'],password) and guardian['Ward_username']==ward_username:
            return True
    return False

def load_conversation(username):
    file_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, encoding='utf-8-sig')
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


def contains_question(text):
    return '?' in text