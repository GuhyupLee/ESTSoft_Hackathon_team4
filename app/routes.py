from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from datetime import datetime, timedelta
import pandas as pd
import os
from .utils import get_random_question, get_gpt_response, save_response, contains_question, save_user, load_users, verify_user, load_conversation, get_all_dates_in_month, summarize_responses, generate_dall_e_image, save_guardian, load_guardian, verify_guardian, base_dir
import random
from .question_data import question_data
from .question import generate_question, stt_function, check_answer, save_question, load_last_question, percentile_for_age_and_score, save_response_question, load_responses, calculate_average_score, tts_function
import requests

main_bp = Blueprint('main', __name__)

state = {
    "total_questions": 0,
    "correct_answers": 0,
    "accuracy_data": []
}

@main_bp.route('/')
def main():
    """메인 페이지 렌더링"""
    yesterday_diary = None
    cognitive_results = None

    if 'username' in session:
        username = session['username']
        yesterday_date = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        image_filename = f'{yesterday_date}_{username}.png'
        image_path = os.path.join('app', 'static', 'images', image_filename)

        if os.path.exists(image_path):
            yesterday_diary = {
                'image_path': f'images/{image_filename}'
            }

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

        cognitive_results = {
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": round(accuracy, 2),
            "percentile": round(percentile, 2),
            "weekly_questions": weekly_questions,
            "accuracy_data": cumulative_accuracy,
            "average_accuracy_global": average_accuracy_global,
            "average_questions_per_day": average_questions_per_day
        }

    return render_template('main.html', yesterday_diary=yesterday_diary, cognitive_results=cognitive_results)

@main_bp.route('/select')
def select():
    """기능 선택 페이지 렌더링"""
    return render_template('select.html')

@main_bp.route('/select2')
def select2():
    return render_template('select2.html')

@main_bp.route('/cognitive_result')
def cognitive_result():
    """인지 테스트 결과 페이지 렌더링"""
    return render_template('cognitive_result.html')

@main_bp.route('/cognitive_test', methods=['GET'])
def cognitive_test():
    """인지 테스트 페이지 렌더링"""
    return render_template('cognitive_test.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if verify_user(username, password):
            session['username'] = username
            session['login_type'] = 'user'  # 일반 사용자 로그인 타입 설정
            session['conversation'] = load_conversation(username)
            users = load_users()
            for user in users:
                if user['Username'] == username:
                    session['age'] = user['Age']  # age를 세션에 저장
                    break
            return redirect(url_for('main.main'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@main_bp.route('/guardian_main')
def guardian_main():
    if 'username' not in session or session.get('role') != 'guardian':
        return redirect(url_for('main.login'))

    ward_username = session.get('ward_username')
    return render_template('guardian_main.html', ward_username=ward_username)

@main_bp.route('/guardian_login', methods=['GET', 'POST'])
def guardian_login():
    """보호자 로그인 페이지 렌더링 및 로그인 처리"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        ward_username = request.form['ward_username']
        if verify_guardian(username, password, ward_username):
            session['username'] = username
            session['role'] = 'guardian'
            session['login_type'] = 'guardian'  # 보호자 로그인 타입 설정
            session['ward_username'] = ward_username
            session['conversation'] = load_conversation(ward_username)
            guardians = load_guardian()
            for guardian in guardians:
                if guardian['Username'] == username:
                    session['age'] = guardian['Age']  # age를 세션에 저장
                    break
            return redirect(url_for('main.guardian_main'))
        else:
            flash('Invalid username, password, or ward username')
    return render_template('guardian_login.html')

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """회원가입 페이지 렌더링 및 회원가입 처리"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        age = request.form['age']
        account_type = request.form['account_type']
        
        if account_type == 'guardian':
            ward_username = request.form['ward_username']
            save_guardian(username, password, age, ward_username)
            flash('Guardian signup successful, please login')
            return redirect(url_for('main.guardian_login'))  # 보호자 로그인 페이지로 리디렉션
        else:
            save_user(username, password, age)
            flash('Signup successful, please login')
            return redirect(url_for('main.login'))  # 일반 로그인 페이지로 리디렉션
    
    return render_template('signup.html')

@main_bp.route('/chat', methods=['GET', 'POST'])
def chat():
    """챗봇 페이지 렌더링 및 대화 처리"""
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
    """대화 상태 초기화"""
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.chat'))

@main_bp.route('/logout', methods=['POST'])
def logout():
    """로그아웃 처리"""
    session.pop('username', None)
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.main'))

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
    correct_response = [
        "우와! 정답이에요 😄",
        "훌륭해요.",
        "정답입니다!",
        "정말 대단해요"
    ]
    incorrect_response = [
        "아쉽지만 오답입니다.",
        "아쉽게도 틀리셨어요.",
        "아깝네요.",
        "아쉽네요. 다음문제에 도전할까요?",
        "틀렸습니다. 하지만 잘하고 있어요!"
    ]

    random_correct_response = random.choice(correct_response)
    random_incorrect_response = random.choice(incorrect_response)
    
    file = request.files['file']
    state["total_questions"] += 1
    file.save("input.mp3")
    user_answer = stt_function("input.mp3")
    question = load_last_question()
    is_correct = check_answer(user_answer, question)
    if is_correct:
        state["correct_answers"] += 1
        response_text = random_correct_response
    else:
        response_text = f"{random_incorrect_response} 정답은 {question_data[question]}입니다."
    
    # 기록 저장
    save_response_question(session['username'], question, user_answer, is_correct)
    
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
    """정확도 가져오기"""
    accuracy = state["correct_answers"] / state["total_questions"] * 100 if state["total_questions"] > 0 else 0
    return jsonify({"accuracy": accuracy})

@main_bp.route('/accuracy_data')
def get_accuracy_data():
    """정확도 데이터 가져오기"""
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

@main_bp.route('/start_random')
def start_random_question():
    """랜덤 질문 시작"""
    question = random.choice(list(question_data.keys()))  # question_data에서 랜덤 질문 선택
    tts_function(question)  # TTS 음성 파일 생성
    save_question(question)  # 현재 질문 저장
    return send_file("output.mp3", mimetype="audio/mpeg", as_attachment=True, download_name="output.mp3")

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

    if session.get('role') == 'guardian':
        username = session.get('ward_username')
    else:
        username = session['username']

    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    current_month_dates = get_all_dates_in_month(year, month)
    
    data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        recorded_dates = df[df['User'] == username]['Date'].unique().tolist()  # 'User' 열을 사용하여 필터링
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

@main_bp.route('/view_ward_diary', defaults={'year': None, 'month': None})
@main_bp.route('/view_ward_diary/<int:year>/<int:month>')
def view_ward_diary(year, month):
    if 'username' not in session or session.get('role') != 'guardian':
        return redirect(url_for('main.login'))

    ward_username = session.get('ward_username')

    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month

    current_month_dates = get_all_dates_in_month(year, month)
    
    data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        recorded_dates = df[df['User'] == ward_username]['Date'].unique().tolist()  # Use ward's username
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

    if session.get('role') == 'guardian':
        username = session.get('ward_username')
    else:
        username = session['username']

    data_path = os.path.join(base_dir, 'app', 'data', 'responses.csv')

    # Load or create CSV file
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        if 'Image_Path' not in df.columns:
            df['Image_Path'] = None
        if 'Diary_Entry' not in df.columns:
            df['Diary_Entry'] = None
    else:
        df = pd.DataFrame(columns=['User', 'Date', 'Response', 'Image_Path', 'Diary_Entry'])
        df.to_csv(data_path, index=False, encoding='utf-8-sig')

    if request.method == 'POST':  # When diary entry is created
        user_records = df[(df['Date'] == date) & (df['User'] == username)]

        responses = user_records['Response'].tolist()
        diary_entry = summarize_responses(responses)
        image_prompt = f"초등학생 그림일기 느낌의 그림을 생성해 주세요.  내용: {diary_entry}"
        image_url = generate_dall_e_image(image_prompt)

        # Save the image
        image_save_dir = os.path.join(base_dir, 'app', 'static', 'images')
        os.makedirs(image_save_dir, exist_ok=True)
        
        image_data = requests.get(image_url).content
        image_path = os.path.join(image_save_dir, f"{date}_{username}.png")
        with open(image_path, 'wb') as handler:
            handler.write(image_data)

        # Save diary entry and image path to CSV
        if user_records.empty:
            new_record = pd.DataFrame([{
                'User': username,
                'Date': date,
                'Response': None,
                'Diary_Entry': diary_entry,
                'Image_Path': image_path
            }])
            df = pd.concat([df, new_record], ignore_index=True)
        else:
            df.loc[user_records.index, 'Diary_Entry'] = diary_entry
            df.loc[user_records.index, 'Image_Path'] = image_path

        df.to_csv(data_path, index=False, encoding='utf-8-sig')

        return render_template('record.html', date=date, diary_entry=diary_entry, image_url=image_url)

    user_records = df[(df['Date'] == date) & (df['User'] == username)]
    diary_entry = user_records['Diary_Entry'].iloc[0] if not user_records['Diary_Entry'].isnull().all() else None
    image_path = user_records['Image_Path'].iloc[0] if not user_records['Image_Path'].isnull().all() else None
    image_url = url_for('static', filename=f'images/{os.path.basename(image_path)}') if image_path else None

    return render_template('record.html', date=date, diary_entry=diary_entry, image_url=image_url)

@main_bp.route('/tts', methods=['POST'])
def tts():
    """텍스트를 음성으로 변환하여 파일로 전송"""
    text = request.json.get('text')
    tts_function(text)
    return send_file("output.mp3", mimetype="audio/mpeg", as_attachment=True, download_name="output.mp3")

@main_bp.route('/results_data')
def get_results_data():
    if 'username' not in session:
        return jsonify({"error": "User data not available"})

    login_type = session.get('login_type')
    if login_type == 'user':
        username = session['username']
        responses = load_responses(username)
    elif login_type == 'guardian':
        username = session['ward_username']
        responses = load_responses(username)
    else:
        return jsonify({"error": "Invalid login type"})

    total_questions = len(responses)
    correct_answers = sum(1 for response in responses if response['is_correct'])
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    users = load_users()
    user = next((u for u in users if u['Username'] == username), None)
    if user:
        age = int(user['Age'])
    else:
        age = 30  # 기본값 설정

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
        "username": session['username'],
        "ward_username": session.get('ward_username'),
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(accuracy, 2),
        "percentile": round(percentile, 2),  # 상위 퍼센타일 반환
        "weekly_questions": weekly_questions,
        "accuracy_data": cumulative_accuracy,
        "average_accuracy_global": average_accuracy_global,
        "average_questions_per_day": average_questions_per_day
    }
    return jsonify(data)

@main_bp.route('/guardian_cognitive_result')
def guardian_cognitive_result():
    if 'username' not in session or session.get('role') != 'guardian':
        return redirect(url_for('main.login'))

    ward_username = session.get('ward_username')

    # Load cognitive test results for the ward
    responses = load_responses(ward_username)
    total_questions = len(responses)
    correct_answers = sum(1 for response in responses if response['is_correct'])
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

    age = int(session.get('age', 30))  # Assuming guardian's age is also stored in session
    percentile = percentile_for_age_and_score(age, accuracy)

    data = {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "accuracy": round(accuracy, 2),
        "percentile": round(percentile, 2),
    }

    return render_template('guardian_cognitive_result.html', data=data, ward_username=ward_username)
