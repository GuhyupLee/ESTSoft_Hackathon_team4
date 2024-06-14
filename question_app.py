from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from question import generate_question, stt_function, tts_function, check_answer, save_question, load_last_question
from question_data import question_data, user_data
from typing import Union
from pydantic import BaseModel

app = FastAPI()

# 전역 상태 변수
state = {
    "total_questions": 0,
    "correct_answers": 0,
    "accuracy_data": []
}

class AccuracyUpdate(BaseModel):
    accuracy: float

@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css", media_type="text/css")

@app.get("/user_data")
async def get_user_data():
    return JSONResponse(content=user_data)

@app.get("/")
async def read_index():
    with open("question_index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/start")
async def start_question():
    question = generate_question()
    save_question(question)  # 현재 질문 저장
    tts_function(question)
    return FileResponse("output.mp3", media_type="audio/mpeg")

@app.post("/answer")
async def answer_question(file: UploadFile = File(...)):
    state["total_questions"] += 1
    with open("input.mp3", "wb") as buffer:
        buffer.write(file.file.read())
    user_answer = stt_function("input.mp3")
    question = load_last_question()
    is_correct = check_answer(user_answer, question)
    if is_correct:
        state["correct_answers"] += 1
        response_text = "정답입니다!"
    else:
        response_text = f"틀렸습니다. 정답은 {question_data[question]}입니다."
    tts_function(response_text)
    accuracy = state["correct_answers"] / state["total_questions"] * 100
    state["accuracy_data"].append(accuracy)
    if len(state["accuracy_data"]) > 10:
        state["accuracy_data"].pop(0)
    return FileResponse("output.mp3", media_type="audio/mpeg", headers={"Content-Disposition": "attachment; filename=output.mp3"})

@app.get("/accuracy")
async def get_accuracy():
    accuracy = state["correct_answers"] / state["total_questions"] * 100 if state["total_questions"] > 0 else 0
    return {"accuracy": accuracy}

@app.get("/accuracy_data")
async def get_accuracy_data():
    return JSONResponse(content=state["accuracy_data"])

@app.post("/update_accuracy")
async def update_accuracy(accuracy_update: AccuracyUpdate):
    accuracy = accuracy_update.accuracy
    state["accuracy_data"].append(accuracy)
    if len(state["accuracy_data"]) > 10:
        state["accuracy_data"].pop(0)
    return {"message": "Accuracy data updated"}