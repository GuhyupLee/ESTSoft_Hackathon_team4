from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from question import generate_question, stt_function, tts_function, check_answer, save_question, load_last_question
from question_data import question_data

app = FastAPI()

total_questions = 0
correct_answers = 0

@app.get("/")
async def read_index():
    with open("question_index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/start")
async def start_question():
    global total_questions
    total_questions += 1
    question = generate_question()
    save_question(question)  # 현재 질문 저장
    tts_function(question)
    return FileResponse("output.mp3", media_type="audio/mpeg")

@app.post("/answer")
async def answer_question(file: UploadFile = File(...)):
    global total_questions, correct_answers
    total_questions += 1
    with open("input.mp3", "wb") as buffer:
        buffer.write(file.file.read())
    user_answer = stt_function("input.mp3")
    question = load_last_question()
    is_correct = check_answer(user_answer, question)
    if is_correct:
        correct_answers += 1
        response_text = "정답입니다!"
    else:
        response_text = f"틀렸습니다. 정답은 {question_data[question]}입니다."
    tts_function(response_text)
    accuracy = correct_answers / total_questions * 100
    return FileResponse("output.mp3", media_type="audio/mpeg", headers={"Content-Disposition": "attachment; filename=output.mp3"})

@app.get("/accuracy")
async def get_accuracy():
    accuracy = correct_answers / total_questions * 100 if total_questions > 0 else 0
    return {"accuracy": accuracy}