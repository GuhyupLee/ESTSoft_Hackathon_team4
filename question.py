from openai import OpenAI
import os
import random
import csv
from question_data import question_data

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

used_questions = []

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
        voice="echo",
        response_format="mp3",
        speed=1,
    )
    return response.stream_to_file("output.mp3")

def check_answer(user_answer, question):
    correct_answer = question_data[question]
    if user_answer.lower() == correct_answer.lower():
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