from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import random
from datetime import datetime, timedelta, date
import calendar
import openai
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()

# 질문 목록
questions = [
    "오늘은 무슨 일이 있었나요",
    "오늘 아침은 무엇을 드셨나요?",
    "최근 읽은 책은 무엇인가요?",
    "오늘 기분은 어떤가요?",
    "가장 기억에 남는 여행지는 어디인가요?"
]

# 랜덤한 질문을 반환하는 함수
def get_random_question(exclude_question=None):
    available_questions = [q for q in questions if q != exclude_question]
    return random.choice(available_questions) if available_questions else random.choice(questions)

# GPT-4 모델의 응답을 생성하는 함수
def get_gpt_response(conversation, current_question):
    prompt = conversation + [
        {"role": "system", "content": "당신은 노인과 대화하는 챗봇입니다. 공손한 말투를 사용하며, 사용자의 질문에 답하고, 대화를 계속하기 위해 후속 질문을 하세요. 대화의 문맥을 기억하고, 사용자의 이전 답변을 바탕으로 관련된 이야기를 하세요. 그리고 각 응답은 30자 이내로 작성하세요."},
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt
    )
    return response.choices[0].message.content

# 응답을 CSV 파일에 저장하는 함수
def save_response(user, date, question, gpt_question, response):
    if not os.path.exists('data'):
        os.makedirs('data')
    df = pd.DataFrame([[user, date, question, gpt_question, response]], columns=['User', 'Date', 'Question', 'GPT_Question', 'Response'])
    df.to_csv('data/responses.csv', mode='a', header=not os.path.exists('data/responses.csv'), index=False, encoding='EUC-KR')

# 텍스트에 질문이 포함되어 있는지 확인하는 함수
def contains_question(text):
    return '?' in text

# 사용자 정보를 CSV 파일에 저장하는 함수
def save_user(username, password):
    if not os.path.exists('users'):
        os.makedirs('users')
    df = pd.DataFrame([[username, generate_password_hash(password)]], columns=['Username', 'Password'])
    df.to_csv('users/users.csv', mode='a', header=not os.path.exists('users/users.csv'), index=False, encoding='EUC-KR')

# 사용자 정보를 로드하는 함수
def load_users():
    if os.path.exists('users/users.csv'):
        df = pd.read_csv('users/users.csv', encoding='EUC-KR')
        return df.to_dict(orient='records')
    return []

# 사용자 검증 함수
def verify_user(username, password):
    users = load_users()
    for user in users:
        if user['Username'] == username and check_password_hash(user['Password'], password):
            return True
    return False

# 사용자 대화 기록을 불러오는 함수
def load_conversation(username):
    if os.path.exists('data/responses.csv'):
        df = pd.read_csv('data/responses.csv', encoding='EUC-KR')
        user_records = df[df['User'] == username].to_dict(orient='records')
        conversation = []
        for record in user_records:
            conversation.append({"role": "system", "content": record['Question']})
            conversation.append({"role": "user", "content": record['Response']})
            conversation.append({"role": "system", "content": record['GPT_Question']})
        return conversation
    return []

@app.route('/')
def main():
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['username'] = username
            session['conversation'] = load_conversation(username)  # Load user's conversation history
            return redirect(url_for('main'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        save_user(username, password)
        flash('Signup successful, please login')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/chat', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'conversation' not in session:
        session['conversation'] = []
        initial_question = get_random_question()
        session['current_question'] = initial_question
        session['conversation'].append({"role": "system", "content": initial_question})
        session['last_interaction_date'] = datetime.now().strftime('%Y-%m-%d')

    # 날짜가 바뀌면 세션 초기화
    last_interaction_date = session.get('last_interaction_date')
    today_date = datetime.now().strftime('%Y-%m-%d')
    if last_interaction_date != today_date:
        session['conversation'] = []
        session['current_question'] = None
        session['last_interaction_date'] = today_date
        initial_question = get_random_question()
        session['current_question'] = initial_question
        session['conversation'].append({"role": "system", "content": initial_question})

    if request.method == 'POST':
        response = request.form['response']
        date = datetime.now().strftime('%Y-%m-%d')
        last_question = session.get('current_question', '')
        session['conversation'].append({"role": "user", "content": response})

        current_question = session.get('current_question', '')
        gpt_response = get_gpt_response(session['conversation'], current_question)
        session['conversation'].append({"role": "system", "content": gpt_response})

        if not contains_question(gpt_response):
            next_question = get_random_question(exclude_question=current_question)
            session['conversation'].append({"role": "system", "content": next_question})
            session['current_question'] = next_question
            save_response(session['username'], date, last_question, gpt_response, response)
        else:
            save_response(session['username'], date, last_question, gpt_response, response)

        session['last_interaction_date'] = date

        # 세션의 대화 기록을 최대 10개까지만 유지
        if len(session['conversation']) > 10:
            session['conversation'] = session['conversation'][-10:]

        return render_template('index.html', conversation=session['conversation'])

    return render_template('index.html', conversation=session['conversation'])

@app.route('/reset', methods=['POST'])
def reset():
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main'))

# 인지 기능 검사 라우트
@app.route('/cognitive_test', methods=['GET', 'POST'])
def cognitive_test():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'cognitive_test_index' not in session:
        session['cognitive_test_index'] = 0

    df = pd.read_csv('data/responses.csv', encoding='EUC-KR')
    user_data = df[df['User'] == session['username']]

    recent_dates = pd.to_datetime(user_data['Date']).drop_duplicates().nlargest(10).tolist()
    recent_data = user_data[user_data['Date'].isin([d.strftime('%Y-%m-%d') for d in recent_dates])]

    recent_data = recent_data.groupby('Date').first().reset_index()  # 날짜별 첫 번째 질문만 가져오기
    test_data = recent_data[['Date', 'Question', 'Response']].to_dict(orient='records')

    if request.method == 'POST':
        user_answer = request.form['answer']
        current_question = test_data[session['cognitive_test_index']]
        correct_answer = current_question['Response']

        if user_answer.strip() == correct_answer.strip():
            feedback = "정답입니다!"
        else:
            feedback = f"틀렸습니다. 정답은 '{correct_answer}' 입니다."

        session['cognitive_test_index'] += 1
        if session['cognitive_test_index'] >= len(test_data):
            session['cognitive_test_index'] = 0

        return render_template('cognitive_test.html', question=test_data[session['cognitive_test_index']], feedback=feedback)

    return render_template('cognitive_test.html', question=test_data[session['cognitive_test_index']])


def get_all_dates_in_month(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, day).strftime('%Y-%m-%d') for day in range(1, num_days + 1)]

@app.route('/calendar', defaults={'year': None, 'month': None})
@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    if 'username' not in session:
        return redirect(url_for('login'))

    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    current_month_dates = get_all_dates_in_month(year, month)
    
    if os.path.exists('data/responses.csv'):
        df = pd.read_csv('data/responses.csv', names=['User', 'Date', 'Question', 'GPT_Question', 'Response'], encoding='EUC-KR')
        recorded_dates = df[df['User'] == session['username']]['Date'].unique().tolist()
    else:
        recorded_dates = []

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    current_month = month
    current_year = year

    return render_template('calendar.html', current_year=current_year, current_month=current_month, dates=current_month_dates, recorded_dates=recorded_dates,
                           prev_year=prev_year, prev_month=prev_month, next_year=next_year, next_month=next_month)

@app.route('/record/<date>')
def record(date):
    if 'username' not in session:
        return redirect(url_for('login'))

    df = pd.read_csv('data/responses.csv', names=['User', 'Date', 'Question', 'GPT_Question', 'Response'], encoding='EUC-KR')
    records = df[(df['Date'] == date) & (df['User'] == session['username'])].to_dict(orient='records')
    return render_template('record.html', records=records, date=date)

if __name__ == '__main__':
    app.run(debug=True)
