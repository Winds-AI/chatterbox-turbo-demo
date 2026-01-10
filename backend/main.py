from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import torch
import torchaudio
import io
import time
import os
from pathlib import Path
import tempfile
from logging_config import logger, get_gpu_stats, log_request_end
from model_loader import model_manager, EnvironmentError


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Chatterbox Turbo API server...")

    import asyncio

    async def initialize_model_async():
        try:
            logger.info("Loading model...")
            model_manager.load_model()
            gpu_stats = get_gpu_stats()
            if gpu_stats:
                logger.info(
                    f"Model loaded. GPU Memory: {gpu_stats['memory_used_mb']:.0f}MB "
                    f"({gpu_stats['memory_percent']:.0f}%), Utilization: {gpu_stats['utilization_percent']}%"
                )
            else:
                logger.info("Model loaded (CPU mode)")
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

        gpu_stats = get_gpu_stats()

        return {
            "status": status,
            "model_loaded": model_manager._model is not None,
            "device": model_manager._device,
            "current_voice": model_manager._current_voice,
            "initialization_state": init_state,
            "initialization_stage": model_manager.get_initialization_stage(),
            "initialization_progress": model_manager.get_initialization_progress(),
            "initialization_error": model_manager.get_initialization_error(),
            "gpu_stats": gpu_stats,
        }
    except EnvironmentError:
        return {
            "status": "error",
            "error": "environment_not_setup",
            "message": "Required libraries not installed. Run: pip install -r requirements.txt",
        }


@app.post("/load_voice")
async def load_voice(request: LoadVoiceRequest):
    start_time = time.time()
    logger.info(
        f"[Voice Load] Request: path={request.voice_path}, exaggeration={request.exaggeration}"
    )

    try:
        model_manager.load_voice(request.voice_path, request.exaggeration)

        elapsed = time.time() - start_time
        gpu_stats = get_gpu_stats()
        log_request_end(logger, "Voice Load", elapsed, gpu_stats)

        return {
            "status": "success",
            "message": "Voice loaded successfully",
            "time_seconds": round(elapsed, 2),
        }
    except EnvironmentError as e:
        elapsed = time.time() - start_time
        logger.error(f"[Voice Load] FAILED in {elapsed:.2f}s: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "environment_not_setup",
                "message": str(e),
                "solution": "Run: pip install -r requirements.txt",
            },
        )
    except FileNotFoundError as e:
        elapsed = time.time() - start_time
        logger.error(f"[Voice Load] FAILED in {elapsed:.2f}s: Voice file not found")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "voice_file_not_found",
                "message": f"Voice file not found: {request.voice_path}",
                "solution": "Provide a valid path to a WAV/MP3 file",
            },
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Voice Load] FAILED in {elapsed:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/load_voice_upload")
async def load_voice_upload(
    voice_file: UploadFile = File(...), exaggeration: float = Form(0.5)
):
    start_time = time.time()
    logger.info(f"[Voice Upload] Request: file={voice_file.filename}")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await voice_file.read()
            file_size_mb = len(content) / (1024 * 1024)
            logger.info(f"[Voice Upload] File size: {file_size_mb:.2f} MB")
            tmp.write(content)
            tmp_path = tmp.name

        model_manager.load_voice(tmp_path, exaggeration)

        elapsed = time.time() - start_time
        gpu_stats = get_gpu_stats()
        log_request_end(logger, "Voice Upload", elapsed, gpu_stats)

        return {
            "status": "success",
            "message": "Voice uploaded and loaded successfully",
            "time_seconds": round(elapsed, 2),
        }
    except EnvironmentError as e:
        elapsed = time.time() - start_time
        logger.error(f"[Voice Upload] FAILED in {elapsed:.2f}s: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "environment_not_setup",
                "message": str(e),
                "solution": "Run: pip install -r requirements.txt",
            },
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Voice Upload] FAILED in {elapsed:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


@app.post("/generate")
async def generate_speech(request: GenerateRequest):
    start_time = time.time()

    text_preview = request.text[:50] + "..." if len(request.text) > 50 else request.text
    logger.info(f"[Generate] Request: {len(request.text)} chars, text='{text_preview}'")

    if model_manager._current_voice is None:
        logger.error("[Generate] FAILED: No voice loaded")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "no_voice_loaded",
                "message": "No voice has been loaded",
                "solution": "Call POST /load_voice or POST /load_voice_upload first",
            },
        )

    try:
        wav = model_manager.generate_speech(request.text)
        generation_time = time.time() - start_time

        audio_bytes = io.BytesIO()
        torchaudio.save(
            audio_bytes, wav.float().cpu(), model_manager._model.sr, format="wav"
        )
        audio_bytes.seek(0)

        output_size = len(audio_bytes.getvalue())
        gpu_stats = get_gpu_stats()

        if gpu_stats:
            logger.info(
                f"[Generate] SUCCESS in {generation_time:.2f}s. "
                f"Audio: {wav.shape}, {output_size / (1024 * 1024):.2f}MB, "
                f"GPU: {gpu_stats['memory_used_mb']:.0f}MB ({gpu_stats['memory_percent']:.0f}%), "
                f"Util: {gpu_stats['utilization_percent']}%"
            )
            gpu_mem_header = str(round(gpu_stats["memory_used_mb"], 2))
            gpu_util_header = str(gpu_stats["utilization_percent"])
        else:
            logger.info(
                f"[Generate] SUCCESS in {generation_time:.2f}s. "
                f"Audio: {wav.shape}, {output_size / (1024 * 1024):.2f}MB (CPU mode)"
            )
            gpu_mem_header = "N/A"
            gpu_util_header = "N/A"

        return StreamingResponse(
            audio_bytes,
            media_type="audio/wav",
            headers={
                "X-Generation-Time": str(round(generation_time, 2)),
                "X-GPU-Memory-MB": gpu_mem_header,
                "X-GPU-Utilization": gpu_util_header,
                "Content-Disposition": "attachment; filename=output.wav",
            },
        )
    except EnvironmentError as e:
        elapsed = time.time() - start_time
        logger.error(f"[Generate] FAILED in {elapsed:.2f}s: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "environment_not_setup",
                "message": str(e),
                "solution": "Run: pip install -r requirements.txt",
            },
        )
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Generate] FAILED in {elapsed:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
