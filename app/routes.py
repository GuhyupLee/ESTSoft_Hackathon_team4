from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime
import pandas as pd
import os
from .utils import get_random_question, get_gpt_response, save_response, contains_question, save_user, load_users, verify_user, load_conversation, get_all_dates_in_month, summarize_responses, generate_dall_e_image, base_dir
import random
from .question_data import question_data
from .question import generate_question, stt_function, tts_function, check_answer, save_question, load_last_question, percentile_for_age_and_score, save_response, load_responses, calculate_average_score

main_bp = Blueprint('main', __name__)

state = {
    "total_questions": 0,
    "correct_answers": 0,
    "accuracy_data": []
}

@main_bp.route('/')
def main():
    return render_template('main.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['username'] = username
            session['conversation'] = load_conversation(username)
            users = load_users()
            for user in users:
                if user['Username'] == username:
                    session['age'] = user['Age']
                    break
            return redirect(url_for('main.main'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        save_user(username, password, age)
        session['age'] = age
        flash('Signup successful, please login')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

@main_bp.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if 'conversation' not in session:
        session['conversation'] = []
        initial_question = get_random_question()
        session['current_question'] = initial_question
        session['conversation'].append({"role": "system", "content": initial_question})
        session['last_interaction_date'] = datetime.now().strftime('%Y-%m-%d')

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

        if len(session['conversation']) > 10:
            session['conversation'] = session['conversation'][-10:]

        return render_template('chatbot.html', conversation=session['conversation'])

    return render_template('chatbot.html', conversation=session['conversation'])

@main_bp.route('/reset', methods=['POST'])
def reset():
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.chat'))

@main_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.main'))

@main_bp.route('/cognitive_test')
def cognitive_test():
    if 'username' not in session:
        return redirect(url_for('main.login'))
    return render_template('cognitive_test.html')

@main_bp.route('/cognitive_result')
def cognitive_result():
    if 'username' not in session:
        return redirect(url_for('main.login'))
    return render_template('cognitive_result.html')

@main_bp.route('/start')
def start_question():
    question = generate_question()
    save_question(question)
    tts_function(question)
    return jsonify({"question": question})

@main_bp.route('/audio')
def get_audio():
    return send_file("output.mp3", mimetype="audio/mpeg")

@main_bp.route('/answer', methods=['POST'])
def answer_question():
    """질문에 대한 답변 처리"""
    file = request.files['file']
    state["total_questions"] += 1
    file.save("input.mp3")
    user_answer = stt_function("input.mp3")
    question = load_last_question()
    is_correct = check_answer(user_answer, question)
    if is_correct:
        state["correct_answers"] += 1
        response_text = "정답입니다!"
    else:
        response_text = f"틀렸습니다. 정답은 {question_data[question]}입니다."
    
    # 기록 저장
    save_response(session['username'], question, user_answer, is_correct)
    
    tts_function(response_text)
    accuracy = state["correct_answers"] / state["total_questions"] * 100
    state["accuracy_data"].append(accuracy)
    if len(state["accuracy_data"]) > 10:
        state["accuracy_data"].pop(0)
    return jsonify({"result": response_text, "user_answer": user_answer})

@main_bp.route('/answer_audio')
def get_answer_audio():
    return send_file("output.mp3", mimetype="audio/mpeg", as_attachment=True, download_name="output.mp3")


@main_bp.route('/accuracy')
def get_accuracy():
    accuracy = state["correct_answers"] / state["total_questions"] * 100 if state["total_questions"] > 0 else 0
    return jsonify({"accuracy": accuracy})

@main_bp.route('/accuracy_data')
def get_accuracy_data():
    return jsonify(state["accuracy_data"])

@main_bp.route('/user_data')
def get_user_data():
    if 'username' not in session or 'age' not in session:
        return jsonify({"error": "User data not available"})
    
    user_data = {
        "Name": session['username'],
        "Age": session['age']
    }
    return jsonify(user_data)

@main_bp.route('/percentile')
def get_percentile():
    if 'age' not in session:
        return jsonify({"error": "Age data not available"})
    
    age = int(session['age'])
    accuracy = state["correct_answers"] / state["total_questions"] * 100 if state["total_questions"] > 0 else 0
    percentile = percentile_for_age_and_score(age, accuracy)
    return jsonify({"percentile": round(percentile, 2)})  # 백분율로 반올림하여 반환

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

@main_bp.route('/record/<date>', methods=['GET', 'POST'])
def record(date):
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        user_records = df[(df['Date'] == date) & (df['User'] == session['username'])]

        responses = user_records['Response'].tolist()
        diary_entry = summarize_responses(responses)
        image_prompt = f"초등학생 그림일기 느낌의 그림을 생성해 주세요. 내용: {diary_entry}"
        image_url = generate_dall_e_image(image_prompt)

        return render_template('record.html', date=date, diary_entry=diary_entry, image_url=image_url)

    return render_template('record.html', date=date)

@main_bp.route('/results_data')
def get_results_data():
    if 'username' not in session:
        return jsonify({"error": "User data not available"})

    username = session['username']
    responses = load_responses(username)
    
    total_questions = len(responses)
    correct_answers = sum(1 for response in responses if response['is_correct'])
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    age = int(session.get('age', 30))
    percentile = percentile_for_age_and_score(age, accuracy)
    
    # 오늘 날짜 데이터 필터링
    today = datetime.now().strftime('%Y-%m-%d')
    today_responses = [response for response in responses if response['date'] == today]
    
    # 주간 질문 수 생성
    weekly_questions = [0] * 7
    day_of_week = datetime.now().weekday()  # 오늘 요일 (0: 월요일, 6: 일요일)
    weekly_questions[day_of_week] = len(today_responses)
    
    # 오늘 날짜의 정답 여부를 기반으로 정답률 데이터 생성
    accuracy_data = [1 if response['is_correct'] else 0 for response in today_responses]
    
    # 정답률 누적 계산
    cumulative_accuracy = []
    correct_count = 0
    for i, value in enumerate(accuracy_data):
        correct_count += value
        cumulative_accuracy.append((correct_count / (i + 1)) * 100)
    
    average_accuracy_global = calculate_average_score(age)
    
    average_questions_per_day = round(len(today_responses) / 1, 2)  # 오늘 날짜 기준으로 평균 계산
    
    data = {
        "username": username,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(accuracy, 2),
        "percentile": round(percentile, 2),
        "weekly_questions": weekly_questions,
        "accuracy_data": cumulative_accuracy,  # 누적 정답률 데이터
        "average_accuracy_global": average_accuracy_global,
        "average_questions_per_day": average_questions_per_day
    }
    return jsonify(data)