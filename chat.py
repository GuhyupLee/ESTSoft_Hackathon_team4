from openai import OpenAI
import os
import random
import csv
import difflib
import time

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


#A 리스트는 일상적인 대화를 기록합니다. 대화 목록이 많으면 외부에서 불러와야합니다.
A = [ 
    "오늘은 무슨 일이 있었나요",
    "오늘 아침은 무엇을 드셨나요?"
]

#B는 딕셔너리입니다. 질문과 정답의 쌍으로 구성되어있습니다.
B = { 
    "2 더하기 2는?": "4",
    "3 곱하기 3은?": "9",
    "5 빼기 2는?": "3",
}

#C 리스트는 인지장애검사 설문지입니다.
C = [
    "예전에 비해 성격이 변한거 같으신가요?",
    "최근에 자기가 놔둔 물건을 찾지 못하는 일이 있으신가요?",
    "최근에 길을 잃거나 헤맨 적이 있으신가요?"
]

#stt를 불러오는 함수
def stt_function(audio_file):
    """
    주어진 오디오 파일을 텍스트로 변환합니다.
    """
    audio_file= open("input.mp3", "rb")
    transcription = client.audio.transcriptions.create(
    model="whisper-1", 
    file=audio_file
    )
    return transcription.text


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
    """주어진 프롬프트를 사용하여 GPT-4o 모델과 대화합니다."""
    category = random.choices(['A', 'B', 'C'], weights=[2, 7, 1], k=1)[0]

    if category == 'A':
        prompt = random.choice(A)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a friendly chatbot that engages in casual conversation. You must answer in Korean."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            max_tokens=2048,
        )
        question = None
    elif category == 'B':
        question = random.choice(list(B.keys()))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a chatbot that asks brain training questions and checks the user's answers. Write the prompt exactly as it is entered. You must communicate in Korean."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": question}
            ],
            temperature=1.0,
            max_tokens=2048,
        )
    else:  # category == 'C'
        question = random.choice(C)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a chatbot that conducts a cognitive impairment survey. Write the prompt exactly as it is entered. You must ask questions in Korean."},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": question}
            ],
            temperature=1.0,
            max_tokens=2048,
        )

    print(response.choices[0].message.content)

    reply = response.choices[0].message.content
    return reply, category, question

def save_to_csv(filename, data):
    """데이터를 CSV 파일에 저장합니다."""
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(data[0].keys())
        writer.writerow(data[0].values())

def check_brain_training(question, user_answer):
    """두뇌트레이닝 점수를 기록합니다."""
    correct_answer = B.get(question)
    if correct_answer:
        is_correct = user_answer == correct_answer
        data = [{
            "Question": question,
            "User Answer": user_answer,
            "Correct Answer": correct_answer,
            "Is Correct": is_correct
        }]
        save_to_csv('brain_training_scores.csv', data)
        return is_correct
    return None

def cognitive_test_response(question, user_answer):
    """인지능력 설문에 대한 점수를 기록합니다."""
    answers = {
        "아니": 0,
        "모르겠어": 1,
        "그래": 2
    }

    closest_match = difflib.get_close_matches(user_answer.strip(), answers.keys(), n=1, cutoff=0.6)
    answer_value = answers[closest_match[0]] if closest_match else -1

    data = [{
        "Question": question,
        "User Answer": user_answer,
        "Answer Value": answer_value
    }]
    save_to_csv('cognitive_test_responses.csv', data)

    return answer_value