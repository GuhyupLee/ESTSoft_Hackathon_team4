from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import pandas as pd
import os
from datetime import datetime
from .utils import get_random_question, get_gpt_response, save_response, contains_question, save_user, load_users, verify_user, load_conversation, get_all_dates_in_month, base_dir

main_bp = Blueprint('main', __name__)

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
        flash('Signup successful, please login')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

@main_bp.route('/chat', methods=['GET', 'POST'])
@main_bp.route('/chat', methods=['GET', 'POST'])
def index():
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
    return redirect(url_for('main.index'))

@main_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    session.pop('conversation', None)
    session.pop('current_question', None)
    session.pop('last_interaction_date', None)
    return redirect(url_for('main.main'))

@main_bp.route('/cognitive_test', methods=['GET', 'POST'])
def cognitive_test():
    if 'username' not in session:
        return redirect(url_for('main.login'))

    if 'cognitive_test_index' not in session:
        session['cognitive_test_index'] = 0

    data_path = os.path.join(base_dir, 'data', 'responses.csv')
    df = pd.read_csv(data_path, encoding='utf-8-sig')
    user_data = df[df['User'] == session['username']]

    recent_dates = pd.to_datetime(user_data['Date']).drop_duplicates().nlargest(10).tolist()
    recent_data = user_data[user_data['Date'].isin([d.strftime('%Y-%m-%d') for d in recent_dates])]

    recent_data = recent_data.groupby('Date').first().reset_index()
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
    
    data_path = os.path.join(base_dir, 'data', 'responses.csv')
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

@main_bp.route('/record/<date>')
def record(date):
    if 'username' not in session:
        return redirect(url_for('main.login'))

    data_path = os.path.join(base_dir, 'data', 'responses.csv')
    if os.path.exists(data_path):
        df = pd.read_csv(data_path, encoding='utf-8-sig')
        records = df[(df['Date'] == date) & (df['User'] == session['username'])].to_dict(orient='records')
        return render_template('record.html', records=records, date=date)
    return render_template('record.html', records=[], date=date)
