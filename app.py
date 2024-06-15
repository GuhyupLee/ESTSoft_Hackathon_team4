from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import random
from datetime import datetime, timedelta, date
import calendar
import openai
import os
from dotenv import load_dotenv

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
        model="gpt-4",
        messages=prompt
    )
    return response.choices[0].message.content

# 응답을 CSV 파일에 저장하는 함수
def save_response(date, question, gpt_question, response):
    if not os.path.exists('data'):
        os.makedirs('data')
    df = pd.DataFrame([[date, question, gpt_question, response]], columns=['Date', 'Question', 'GPT_Question', 'Response'])
    df.to_csv('data/responses.csv', mode='a', header=False, index=False, encoding='EUC-KR')

# 텍스트에 질문 또는 느낌표가 포함되어 있는지 확인하는 함수
def contains_question(text):
    return '?' in text

# 메인 페이지 라우트
@app.route('/', methods=['GET', 'POST'])
def index():
    # 세션에서 대화 내역을 초기화
    if 'conversation' not in session:
        session['conversation'] = []
        initial_question = get_random_question()
        session['current_question'] = initial_question
        session['conversation'].append({"role": "system", "content": initial_question})
        session['last_interaction_date'] = datetime.now().strftime('%Y-%m-%d')

    # 사용자가 응답을 제출한 경우
    if request.method == 'POST':
        response = request.form['response']
        date = datetime.now().strftime('%Y-%m-%d')
        last_question = session.get('current_question', '')
        session['conversation'].append({"role": "user", "content": response})

        # 유저의 답변에 대한 GPT-4 모델의 응답 생성
        current_question = session.get('current_question', '')
        gpt_response = get_gpt_response(session['conversation'], current_question)
        session['conversation'].append({"role": "system", "content": gpt_response})

        # GPT-4의 응답에 질문 또는 느낌표가 없으면 새로운 질문 생성
        if not contains_question(gpt_response):
            next_question = get_random_question(exclude_question=current_question)
            session['conversation'].append({"role": "system", "content": next_question})
            session['current_question'] = next_question
            save_response(date, last_question, gpt_response, response)  # Save with API response as GPT_Question
        else:
            save_response(date, last_question, gpt_response, response)  # Save with API response as GPT_Question

        session['last_interaction_date'] = date  # Update the last interaction date

        return render_template('index.html', conversation=session['conversation'])

    # GET 요청에서 날짜가 넘어갔는지 확인하고 새로운 질문을 설정
    last_interaction_date = session.get('last_interaction_date')
    today_date = datetime.now().strftime('%Y-%m-%d')
    if last_interaction_date != today_date:
        next_question = get_random_question(exclude_question=session.get('current_question', ''))
        session['conversation'].append({"role": "system", "content": next_question})
        session['current_question'] = next_question
        session['last_interaction_date'] = today_date

    return render_template('index.html', conversation=session['conversation'])

# 채팅 내역을 초기화하는 라우트
@app.route('/reset', methods=['POST'])
def reset():
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('index'))

def get_all_dates_in_month(year, month):
    num_days = calendar.monthrange(year, month)[1]
    return [date(year, month, day).strftime('%Y-%m-%d') for day in range(1, num_days + 1)]

@app.route('/calendar', defaults={'year': None, 'month': None})
@app.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    current_month_dates = get_all_dates_in_month(year, month)
    
    # Get all dates with records
    if os.path.exists('data/responses.csv'):
        df = pd.read_csv('data/responses.csv', names=['Date', 'Question', 'GPT_Question', 'Response'], encoding='EUC-KR')
        recorded_dates = df['Date'].unique().tolist()
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

# 특정 날짜의 기록을 보여주는 라우트
@app.route('/record/<date>')
def record(date):
    df = pd.read_csv('data/responses.csv', names=['Date', 'Question', 'GPT_Question', 'Response'], encoding='EUC-KR')
    records = df[df['Date'] == date].to_dict(orient='records')
    return render_template('record.html', records=records, date=date)

if __name__ == '__main__':
    app.run(debug=True)
