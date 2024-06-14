from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from chat import generate_first_response, stt_function, talk_to_gpt, tts_function

app = FastAPI()

@app.get("/")
async def read_index():
    with open("index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/start")
async def start_conversation():
    response = generate_first_response()
    tts_function(response)
    return FileResponse("output.mp3", media_type="audio/mpeg")

@app.post("/conversation")
async def conversation(file: UploadFile = File(...)):
    with open("input.mp3", "wb") as buffer:
        buffer.write(file.file.read())
    text = stt_function("input.mp3")
    response = talk_to_gpt(text)
    tts_function(response)
    return FileResponse("output.mp3", media_type="audio/mpeg")