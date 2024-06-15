from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import pandas as pd
import os
import openai
from .utils import get_random_question, get_gpt_response, save_response, contains_question, save_user, load_users, verify_user, load_conversation, get_all_dates_in_month, summarize_responses, generate_dall_e_image, base_dir

# Blueprint 객체 생성
main_bp = Blueprint('main', __name__)

# 메인 페이지 라우트
@main_bp.route('/')
def main():
    return render_template('main.html')

# 로그인 페이지 라우트
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # 로그인 폼 제출 시
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):  # 사용자 인증
            session['username'] = username
            session['conversation'] = load_conversation(username)
            return redirect(url_for('main.main'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# 회원가입 페이지 라우트
@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':  # 회원가입 폼 제출 시
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        save_user(username, password, age)
        flash('Signup successful, please login')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

# 챗봇 인터페이스 라우트
@main_bp.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if 'conversation' not in session:  # 새로운 대화 시작 시 초기 설정
        session['conversation'] = []
        initial_question = get_random_question()
        session['current_question'] = initial_question
        session['conversation'].append({"role": "system", "content": initial_question})
        session['last_interaction_date'] = datetime.now().strftime('%Y-%m-%d')

    last_interaction_date = session.get('last_interaction_date')
    today_date = datetime.now().strftime('%Y-%m-%d')
    if last_interaction_date != today_date:  # 새로운 날에 대화 초기화
        session['conversation'] = []
        session['current_question'] = None
        session['last_interaction_date'] = today_date
        initial_question = get_random_question()
        session['current_question'] = initial_question
        session['conversation'].append({"role": "system", "content": initial_question})

    if request.method == 'POST':  # 사용자 응답 제출 시
        response = request.form['response']
        date = datetime.now().strftime('%Y-%m-%d')
        last_question = session.get('current_question', '')
        session['conversation'].append({"role": "user", "content": response})

        current_question = session.get('current_question', '')
        gpt_response = get_gpt_response(session['conversation'], current_question)
        session['conversation'].append({"role": "system", "content": gpt_response})

        if not contains_question(gpt_response):  # GPT 응답에 질문이 포함되지 않은 경우
            next_question = get_random_question(exclude_question=current_question)
            session['conversation'].append({"role": "system", "content": next_question})
            session['current_question'] = next_question
            save_response(session['username'], date, last_question, gpt_response, response)
        else:
            save_response(session['username'], date, last_question, gpt_response, response)

        session['last_interaction_date'] = date

        if len(session['conversation']) > 10:  # 대화 기록이 10개를 넘으면 최근 10개만 유지
            session['conversation'] = session['conversation'][-10:]

        return render_template('chatbot.html', conversation=session['conversation'])

    return render_template('chatbot.html', conversation=session['conversation'])

# 대화 리셋 라우트
@main_bp.route('/reset', methods=['POST'])
def reset():
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.chat'))

# 로그아웃 라우트
@main_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.main'))

# 인지 기능 테스트 라우트
@main_bp.route('/cognitive_test', methods=['GET', 'POST'])
def cognitive_test():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if 'cognitive_test_index' not in session:
        session['cognitive_test_index'] = 0

    data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
    df = pd.read_csv(data_path, encoding='utf-8-sig')
    user_data = df[df['User'] == session['username']]

    recent_dates = pd.to_datetime(user_data['Date']).drop_duplicates().nlargest(10).tolist()
    recent_data = user_data[user_data['Date'].isin([d.strftime('%Y-%m-%d') for d in recent_dates])]

    recent_data = recent_data.groupby('Date').first().reset_index()
    test_data = recent_data[['Date', 'Question', 'Response']].to_dict(orient='records')

    if request.method == 'POST':  # 사용자 응답 제출 시
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

# 캘린더 보기 라우트
@main_bp.route('/calendar', defaults={'year': None, 'month': None})
@main_bp.route('/calendar/<int:year>/<int:month>')
def calendar_view(year, month):
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    current_month_dates = get_all_dates_in_month(year, month)
    
    data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')
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

# 기록 보기 및 일기 생성 라우트
@main_bp.route('/record/<date>', methods=['GET', 'POST'])
def record(date):
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':  # 일기 생성 요청 시
        data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        user_records = df[(df['Date'] == date) & (df['User'] == session['username'])]

        responses = user_records['Response'].tolist()
        diary_entry = summarize_responses(responses)
        image_prompt = f"초등학생 그림일기 느낌의 그림을 생성해 주세요. 내용: {diary_entry}"
        image_url = generate_dall_e_image(image_prompt)

        return render_template('record.html', date=date, diary_entry=diary_entry, image_url=image_url)

    return render_template('record.html', date=date)
