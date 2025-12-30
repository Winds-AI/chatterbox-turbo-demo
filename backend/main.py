from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import torchaudio
import io
import time
from pathlib import Path
import tempfile
from model_loader import model_manager

app = FastAPI(title="Chatterbox Turbo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    text: str


class LoadVoiceRequest(BaseModel):
    voice_path: str
    exaggeration: float = 0.5


@app.on_event("startup")
async def startup_event():
    model_manager.load_model()


@app.get("/")
async def root():
    return {"status": "ok", "message": "Chatterbox Turbo API is running"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model_loaded": model_manager._model is not None,
        "device": model_manager._device,
        "current_voice": model_manager._current_voice,
    }


@app.post("/load_voice")
async def load_voice(request: LoadVoiceRequest):
    try:
        model_manager.load_voice(request.voice_path, request.exaggeration)
        return {"status": "success", "message": "Voice loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load_voice_upload")
async def load_voice_upload(
    voice_file: UploadFile = File(...), exaggeration: float = Form(0.5)
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await voice_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        model_manager.load_voice(tmp_path, exaggeration)
        return {
            "status": "success",
            "message": "Voice uploaded and loaded successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
async def generate_speech(request: GenerateRequest):
    if model_manager._current_voice is None:
        raise HTTPException(status_code=400, detail="No voice loaded")

    try:
        start_time = time.time()
        wav = model_manager.generate_speech(request.text)
        generation_time = time.time() - start_time

        audio_bytes = io.BytesIO()
        torchaudio.save(
            audio_bytes, wav.float().cpu(), model_manager._model.sr, format="wav"
        )
        audio_bytes.seek(0)

        return StreamingResponse(
            audio_bytes,
            media_type="audio/wav",
            headers={
                "X-Generation-Time": str(generation_time),
                "Content-Disposition": "attachment; filename=output.wav",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
