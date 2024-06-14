from openai import OpenAI
import os
import random
import csv

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_first_response():
    
    prompts = [
        "사용자에게 인사를 건넴",
        "사용자에게 안부를 물음",
        "사용자에게 오늘 무슨일을 했는지 물음",
        "사용자에게 오늘 날씨가 어땟는지 물음"
    ]

    prompt = random.choice(prompts)
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
            {"role": "system", "content": "You are a friendly chatbot that engages in casual conversation. You must answer in Korean."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1000,
    )

    print(response.choices[0].message.content)

    reply = response.choices[0].message.content
    log_gpt_response(reply)
    return reply

def stt_function(audio_file):
    """
    주어진 오디오 파일을 텍스트로 변환합니다.
    """
    audio_file= open("input.mp3", "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )
    text = transcription.text

    print(text)

    log_user_input(text)
    return text

def tts_function(text):
    """
    주어진 텍스트를 음성 파일로 변환합니다.
    """

    response = client.audio.speech.create(
        model="tts-1",
        input=text,
        voice="echo",
        response_format="mp3",
        speed=1,
    )

    return response.stream_to_file("output.mp3")


def talk_to_gpt(prompt):
    """
    주어진 프롬프트를 사용하여 GPT-4o 모델과 대화합니다.
    """

    conversation_history = load_conversation_history()
    conversation_history.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=conversation_history,
        temperature=1.0,
        max_tokens=2048,
    )
    
    print(response.choices[0].message.content)

    reply = response.choices[0].message.content
    log_gpt_response(reply)
    return reply


def log_user_input(user_input):
    """
    사용자 입력을 CSV 파일에 기록합니다.
    """
    with open('conversation_log.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([user_input, ""])

def log_gpt_response(gpt_response):
    """
    GPT 응답을 CSV 파일에 기록합니다.
    """
    with open('conversation_log.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["", gpt_response])

def load_conversation_history(limit=20):
    """
    CSV 파일에서 대화 기록을 불러옵니다. 최근 limit개의 대화만 가져옵니다.
    """
    conversation_history = []
    if os.path.exists('conversation_log.csv'):
        with open('conversation_log.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            recent_rows = rows[-limit:]  # 최신 limit개의 대화만 가져오기
            for row in recent_rows:
                user_input, gpt_response = row
                if user_input:
                    conversation_history.append({"role": "user", "content": user_input})
                if gpt_response:
                    conversation_history.append({"role": "assistant", "content": gpt_response})
    return conversation_history
