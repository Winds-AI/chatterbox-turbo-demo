from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import torch
import torchaudio
import io
import time
import logging
from pathlib import Path
import tempfile
import os
from model_loader import model_manager, EnvironmentError
from metrics import metrics_manager, track_request_duration, track_phase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Chatterbox Turbo API server...")

    import asyncio

    async def initialize_model_async():
        try:
            model_manager.load_model()
            metrics_manager.update_model_loaded(True)
            logger.info("Server startup complete")
        except EnvironmentError as e:
            logger.warning(f"[Startup] Warning: {e}")
            logger.info("[Startup] Model will load on first request")
        except Exception as e:
            logger.error(f"[Startup] Model initialization failed: {e}")

    model_init_task = asyncio.create_task(initialize_model_async())
    logger.info("Model initialization started in background...")

    yield

    logger.info("Shutting down Chatterbox Turbo API server...")
    metrics_manager.update_model_loaded(False)
    if not model_init_task.done():
        model_init_task.cancel()
        try:
            await model_init_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Chatterbox Turbo API", lifespan=lifespan)

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


@app.get("/")
async def root():
    return {"status": "ok", "message": "Chatterbox Turbo API is running"}


@app.get("/health")
async def health():
    metrics_manager.update_gpu_metrics()
    try:
        init_state = model_manager.get_initialization_state()

        if init_state == "ready":
            status = "healthy"
        elif init_state == "initializing":
            status = "initializing"
        elif init_state == "error":
            status = "error"
        else:
            status = "starting"

        return {
            "status": status,
            "model_loaded": model_manager._model is not None,
            "device": model_manager._device,
            "current_voice": model_manager._current_voice,
            "initialization_state": init_state,
            "initialization_stage": model_manager.get_initialization_stage(),
            "initialization_progress": model_manager.get_initialization_progress(),
            "initialization_error": model_manager.get_initialization_error(),
        }
    except EnvironmentError:
        return {
            "status": "error",
            "error": "environment_not_setup",
            "message": "Required libraries not installed. Run: python setup_env.py",
        }


@app.get("/metrics")
async def metrics():
    metrics_manager.update_gpu_metrics()
    return Response(
        content=metrics_manager.get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.post("/load_voice")
async def load_voice(request: LoadVoiceRequest):
    logger.info(f"Received load_voice request for path: {request.voice_path}")
    try:
        model_manager.load_voice(request.voice_path, request.exaggeration)
        logger.info("Voice loaded successfully via API")
        return {"status": "success", "message": "Voice loaded successfully"}
    except EnvironmentError as e:
        logger.error(f"Environment error loading voice: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "environment_not_setup",
                "message": str(e),
                "solution": "Run: python setup_env.py",
            },
        )
    except FileNotFoundError as e:
        logger.error(f"Voice file not found: {request.voice_path}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "voice_file_not_found",
                "message": f"Voice file not found: {request.voice_path}",
                "solution": "Provide a valid path to a WAV/MP3 file",
            },
        )
    except Exception as e:
        logger.error(f"Error loading voice: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load_voice_upload")
async def load_voice_upload(
    voice_file: UploadFile = File(...), exaggeration: float = Form(0.5)
):
    logger.info(f"Received voice upload request: {voice_file.filename}")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await voice_file.read()
            logger.info(f"Uploaded file size: {len(content) / (1024 * 1024):.2f} MB")
            tmp.write(content)
            tmp_path = tmp.name
            logger.info(f"File saved to temp path: {tmp_path}")

        model_manager.load_voice(tmp_path, exaggeration)
        logger.info("Voice uploaded and loaded successfully")
        return {
            "status": "success",
            "message": "Voice uploaded and loaded successfully",
        }
    except EnvironmentError as e:
        logger.error(f"Environment error during voice upload: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "environment_not_setup",
                "message": str(e),
                "solution": "Run: python setup_env.py",
            },
        )
    except Exception as e:
        logger.error(f"Error during voice upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            logger.info(f"Cleaning up temp file: {tmp_path}")
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")


@app.post("/generate")
@track_request_duration(endpoint="/generate", operation="total")
async def generate_speech(request: GenerateRequest):
    logger.info(
        f"Received generate request: {request.text[:50]}{'...' if len(request.text) > 50 else ''}"
    )

    metrics_manager.record_text_length(len(request.text))
    metrics_manager.update_gpu_metrics()

    if model_manager._current_voice is None:
        logger.error("No voice loaded - refusing generation request")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "no_voice_loaded",
                "message": "No voice has been loaded",
                "solution": "Call POST /load_voice or POST /load_voice_upload first",
            },
        )

    try:
        start_time = time.time()
        wav = model_manager.generate_speech(request.text)
        generation_time = time.time() - start_time

        logger.info(
            f"Generated audio shape: {wav.shape}, sample rate: {model_manager._model.sr}, time: {generation_time:.2f}s"
        )

        audio_bytes = io.BytesIO()
        torchaudio.save(
            audio_bytes, wav.float().cpu(), model_manager._model.sr, format="wav"
        )
        audio_bytes.seek(0)

        output_size = len(audio_bytes.getvalue())
        metrics_manager.record_audio_output(output_size)
        metrics_manager.update_gpu_metrics()
        logger.info(f"Output audio size: {output_size / (1024 * 1024):.2f} MB")

        return StreamingResponse(
            audio_bytes,
            media_type="audio/wav",
            headers={
                "X-Generation-Time": str(generation_time),
                "Content-Disposition": "attachment; filename=output.wav",
            },
        )
    except EnvironmentError as e:
        logger.error(f"Environment error during generation: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "environment_not_setup",
                "message": str(e),
                "solution": "Run: python setup_env.py",
            },
        )
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
