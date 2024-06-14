from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
import os
import chat

app = FastAPI()

@app.get("/")
async def serve_index_html():
    with open("index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.post("/start_conversation")
async def start_conversation():
    prompt = "안녕하세요"
    gpt_reply, category, question = chat.talk_to_gpt(prompt)
    chat.tts_function(gpt_reply)

    return FileResponse("output.mp3", media_type="audio/mpeg")

@app.post("/process_audio")
async def process_audio(audio: UploadFile = File(...)):
    with open("input.mp3", "wb") as f:
        f.write(await audio.read())

    user_answer = chat.stt_function("input.mp3")
    gpt_reply, category, question = chat.talk_to_gpt(user_answer)
    chat.tts_function(gpt_reply)

    if category == 'A':
        data = [{
            "Category": category,
            "GPT Question": question,
            "User Answer": user_answer,
            "GPT Reply": gpt_reply
        }]
        chat.save_to_csv('conversation_history.csv', data)
    elif category == 'B':
        user_answer_to_question = chat.stt_function("input.mp3")
        is_correct = chat.check_brain_training(question, user_answer_to_question)
        if is_correct is not None:
            feedback = "맞았습니다! 잘하셨어요." if is_correct else "아쉽게도 틀렸습니다. 정답은 {}입니다.".format(chat.B[question])
            chat.tts_function(feedback)
    elif category == 'C':
        user_answer_to_question = chat.stt_function("input.mp3")
        answer_value = chat.cognitive_test_response(question, user_answer_to_question)
        feedback = "답변 감사합니다. 당신의 인지 능력은 매우 좋아 보입니다." if answer_value == 0 else "답변 감사합니다. 인지 능력에 약간의 변화가 있는 것 같네요."
        chat.tts_function(feedback)

    return FileResponse("output.mp3", media_type="audio/mpeg")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)