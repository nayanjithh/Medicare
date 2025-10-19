from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import vosk
import wave
import json
import uuid
import datetime
from pymongo import MongoClient
import gemini
import gemini_chatbot

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = "mongodb+srv://nayanjithajith_db_user:nayanjith%408831@cluster0.tx2dkmn.mongodb.net/medicaredb?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["medicaredb"]
collection = db["Patients"]

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MODEL_PATH = "vosk-model-small-en-us-0.15"
model = vosk.Model(MODEL_PATH)

def speech_text(file_path: str) -> str:
    wf = wave.open(file_path, "rb")
    rec = vosk.KaldiRecognizer(model, wf.getframerate())
    transcript = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            transcript += " " + result.get("text", "")

    final_result = json.loads(rec.FinalResult())
    transcript += " " + final_result.get("text", "")
    return transcript.strip()

@app.post("/upload_audio")
async def upload_audio(
    file: UploadFile = File(...),
    name: str = Form(...),
    age: int = Form(...)
):
    if not file.content_type.startswith("audio/"):
        return {"error": "Only audio files are allowed."}

    try:
        filename = "report_audio.wav"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        transcript = speech_text(file_path)
        response_text = gemini.generate(transcript)
        response_json = json.loads(response_text)

        record = {
            "patient_id": str(uuid.uuid4()),
            "name": name.lower(),
            "age": age,
            "date": datetime.datetime.now().isoformat(),
            "source": "voice_note",
            **response_json
        }

        collection.insert_one(record)
        os.remove(file_path)

        return {"message": "Inserted Successfully"}

    except Exception as e:
        return {"error": f"Failed processing audio: {str(e)}"}

@app.post("/chatbot")
async def chat_bot(request: Request):
    data = await request.json()
    user_input = data.get("input", "")
    response = gemini_chatbot.generate(user_input)
    return {"response": response}
