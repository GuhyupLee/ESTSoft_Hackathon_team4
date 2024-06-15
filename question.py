from openai import OpenAI
import os
import random
import csv
import math
import numpy as np
import scipy.stats as stats
from .question_data import question_data
import csv
from datetime import datetime

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

used_questions = []

state = {
    "total_questions": 0,
    "correct_answers": 0,
    "accuracy_data": []
}

#이미 사용한 질문은 사용하지 않게 하는 기능
def generate_question():
    available_questions = list(set(question_data.keys()) - set(used_questions)) 
    if not available_questions:
        used_questions.clear()
        available_questions = list(question_data.keys())
    question = random.choice(available_questions)
    used_questions.append(question)
    return question


def stt_function(audio_file):
    audio_file = open("input.mp3", "rb")
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    text = transcription.text
    print(text)
    return text

def tts_function(text):
    response = client.audio.speech.create(
        model="tts-1",
        input=text,
        voice="nova",
        response_format="mp3",
        speed=1,
    )
    return response.stream_to_file("output.mp3")

def check_answer(user_answer, question):
    correct_answer = question_data[question]
    if correct_answer.lower() in user_answer.lower():
        return True
    else:
        return False

def save_question(question):
    with open('question_log.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([question])

def load_last_question():
    with open('question_log.csv', mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
        if rows:
            return rows[-1][0]
        else:
            return ""
        
def calculate_average_score(age):
    """
    인지능력 검사(MMSE) 평균 점수 분포를 통해 계산
    """
    if age <= 25:
        return 95
    elif 25 < age < 45:
        return 95 - (age - 25) * (95 - 83) / 20
    elif 45 <= age < 50:
        return 83 - (age - 45) * (83 - 76) / 5
    elif 50 <= age < 55:
        return 76 - (age - 50) * (76 - 70) / 5
    elif 55 <= age < 60:
        return 70 - (age - 55) * (70 - 63) / 5
    elif 60 <= age < 65:
        return 63 - (age - 60) * (63 - 56) / 5
    elif 65 <= age < 70:
        return 56 - (age - 65) * (56 - 50) / 5
    elif 70 <= age <= 100:
        return 50 - 14 * (1 - math.exp(-0.1 * (age - 70)))
    else:
        return 36
    
def calculate_std_dev(age):
    """
    나이에 따른 표준편차 계산
    """
    if age <= 20:
        return 5
    elif age >= 100:
        return 20
    else:
        return 5 + (age - 20) * (20 - 5) / (100 - 20)

    
def percentile_for_age_and_score(age, score):
    """
    특정 나이와 점수에 대해 상위 몇 %에 속하는지 계산
    """
    mean_score = calculate_average_score(age)
    std_dev = calculate_std_dev(age)
    
    # 정규분포에서 퍼센타일 계산
    percentile = stats.norm.cdf(score, mean_score, std_dev) * 100
    return percentile

def save_response_question(username, question, answer, is_correct):
    date = datetime.now().strftime('%Y-%m-%d')
    with open('responses.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([username, date, question, answer, is_correct])

def load_responses(username):
    responses = []
    try:
        with open('responses.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == username:
                    responses.append({
                        "date": row[1],
                        "question": row[2],
                        "answer": row[3],
                        "is_correct": row[4] == 'True'
                    })
    except FileNotFoundError:
        pass
    return responses