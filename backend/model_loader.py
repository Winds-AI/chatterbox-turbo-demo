import os
import logging
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

load_dotenv()

os.environ["HF_HOME"] = os.path.abspath("../model_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
os.environ["HF_HUB_ENABLE_HF_XET"] = "0"


class EnvironmentError(Exception):
    pass


import torch
import torchaudio
from huggingface_hub import snapshot_download
from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID


class ModelManager:
    _instance = None
    _model = None
    _device = None
    _current_voice = None
    _initialization_state = "not_started"
    _initialization_progress = 0.0
    _initialization_error = None
    _initialization_stage = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def check_environment(self):
        try:
            import torch
            import torchaudio
            import huggingface_hub
            from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID

            return True
        except ImportError as e:
            raise EnvironmentError(
                f"Required libraries not installed. Please run: python setup_env.py\n"
                f"Missing: {str(e)}"
            )

    def get_initialization_state(self):
        return self._initialization_state

    def get_initialization_progress(self):
        return self._initialization_progress

    def get_initialization_error(self):
        return self._initialization_error

    def get_initialization_stage(self):
        return self._initialization_stage

    def _set_initialization_state(self, state, stage=None, progress=None, error=None):
        self._initialization_state = state
        if stage is not None:
            self._initialization_stage = stage
        if progress is not None:
            self._initialization_progress = progress
        if error is not None:
            self._initialization_error = error

    def load_model(self):
        self.check_environment()

        if self._model is None:
            self._set_initialization_state(
                "initializing", stage="checking_device", progress=0.1
            )
            if not torch.cuda.is_available():
                error_msg = (
                    "CUDA is not available. This application requires GPU support. "
                    "Please install CUDA version of PyTorch or ensure you have a compatible GPU."
                )
                self._set_initialization_state("error", error=error_msg)
                raise RuntimeError(error_msg)
            device = "cuda"
            self._device = device
            logger.info(f"Loading Chatterbox Turbo model on {device}...")
            logger.info("This may take 10-20 minutes for the first download (~4GB)")

            try:
                self._set_initialization_state(
                    "initializing", stage="downloading_model", progress=0.2
                )
                # Path relative to project root (chatterbox directory)
                cache_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "model_cache", "hub"
                )
                cache_dir = os.path.abspath(cache_dir)
                logger.info(f"Model cache directory: {cache_dir}")

                local_path = snapshot_download(
                    repo_id=REPO_ID,
                    token=False,
                    allow_patterns=[
                        "*.safetensors",
                        "*.json",
                        "*.txt",
                        "*.pt",
                        "*.model",
                    ],
                    local_dir=cache_dir,
                )
                logger.info(f"Model files loaded from: {local_path}")

                self._set_initialization_state(
                    "initializing", stage="loading_model", progress=0.8
                )
                self._model = ChatterboxTurboTTS.from_local(local_path, device=device)
                logger.info("Model loaded successfully!")

                self._set_initialization_state("ready", stage="complete", progress=1.0)
            except Exception as e:
                if (
                    "no such file or directory" in str(e).lower()
                    or "cannot find" in str(e).lower()
                ):
                    error_msg = (
                        f"Model files not found in cache directory: {os.environ.get('HF_HOME', './model_cache')}\n"
                        f"Please run: python setup_env.py to download models"
                    )
                    self._set_initialization_state("error", error=error_msg)
                    raise EnvironmentError(error_msg)
                logger.error(f"Failed to load model: {e}")
                self._set_initialization_state("error", error=str(e))
                raise

        return self._model

    def load_voice(self, voice_path: str, exaggeration: float = 0.5):
        import time

        logger.info(f"Loading voice from: {voice_path}")
        logger.info(f"Exaggeration level: {exaggeration}")

        model = self.load_model()

        if not os.path.exists(voice_path):
            logger.error(f"Voice file not found: {voice_path}")
            raise FileNotFoundError(f"Voice file not found: {voice_path}")

        file_size = os.path.getsize(voice_path)
        logger.info(f"Voice file size: {file_size / (1024 * 1024):.2f} MB")

        logger.info("Preparing voice conditionals...")
        total_start = time.time()

        if self._device == "cuda":
            step1_start = time.time()
            logger.info("Step 1/4: Loading audio file...")
            waveform, sr = torchaudio.load(voice_path)
            step1_time = time.time() - step1_start
            logger.info(
                f"Step 1/4: Audio loaded in {step1_time:.2f}s (shape: {waveform.shape}, sr: {sr})"
            )

            step2_start = time.time()
            target_sr = 16000
            logger.info(
                f"Step 2/4: Resampling to target sample rate ({target_sr} Hz)..."
            )
            if sr != target_sr:
                resampler = torchaudio.transforms.Resample(sr, target_sr)
                waveform = resampler(waveform)
                sr = target_sr
            step2_time = time.time() - step2_start
            logger.info(f"Step 2/4: Resampling completed in {step2_time:.2f}s")

            logger.info(
                f"GPU memory before Step 3: {torch.cuda.memory_allocated(1e6):.2f} MB"
            )

            step3_start = time.time()
            logger.info("Step 3/4: Moving data to GPU and computing conditionals...")

            substep1_start = time.time()
            logger.info("Step 3.1: Moving audio data to GPU...")
            waveform_gpu = waveform.to(self._device)
            substep1_time = time.time() - substep1_start
            logger.info(f"Step 3.1: GPU transfer completed in {substep1_time:.2f}s")

            substep2_start = time.time()
            logger.info("Step 3.2: Extracting audio features/embeddings...")
            with torch.amp.autocast("cuda"):
                model.prepare_conditionals(voice_path, exaggeration=exaggeration)
            substep2_time = time.time() - substep2_start
            logger.info(
                f"Step 3.2: Feature extraction completed in {substep2_time:.2f}s"
            )
            logger.info(
                f"GPU memory after Step 3: {torch.cuda.memory_allocated(1e6):.2f} MB"
            )

            step3_time = time.time() - step3_start
            logger.info(
                f"Step 3/4: GPU conditional computation completed in {step3_time:.2f}s"
            )
        else:
            step1_start = time.time()
            logger.info("Step 1/4: Loading audio file...")
            waveform, sr = torchaudio.load(voice_path)
            step1_time = time.time() - step1_start
            logger.info(
                f"Step 1/4: Audio loaded in {step1_time:.2f}s (shape: {waveform.shape}, sr: {sr})"
            )

            step2_start = time.time()
            target_sr = 16000
            logger.info(
                f"Step 2/4: Resampling to target sample rate ({target_sr} Hz)..."
            )
            if sr != target_sr:
                resampler = torchaudio.transforms.Resample(sr, target_sr)
                waveform = resampler(waveform)
                sr = target_sr
            step2_time = time.time() - step2_start
            logger.info(f"Step 2/4: Resampling completed in {step2_time:.2f}s")

            step3_start = time.time()
            logger.info("Step 3/4: Computing conditionals on CPU...")
            model.prepare_conditionals(voice_path, exaggeration=exaggeration)
            step3_time = time.time() - step3_start
            logger.info(
                f"Step 3/4: Conditional computation completed in {step3_time:.2f}s"
            )

        total_time = time.time() - total_start
        logger.info(
            f"Voice conditionals prepared successfully (total: {total_time:.2f}s)"
        )

        self._current_voice = voice_path
        logger.info(f"Voice loaded successfully: {voice_path}")
        return True

    def generate_speech(self, text: str):
        if self._current_voice is None:
            logger.error("No voice loaded")
            raise ValueError("No voice loaded")

        model = self.load_model()
        logger.info(
            f"Generating speech for text: {text[:50]}{'...' if len(text) > 50 else ''}"
        )

        if self._device == "cuda":
            with torch.amp.autocast("cuda"):
                wav = model.generate(text)
        else:
            wav = model.generate(text)

        logger.info(f"Speech generated successfully, shape: {wav.shape}")
        return wav

    def unload_model(self):
        if self._model is not None:
            logger.info("Unloading model from GPU...")
            del self._model
            self._model = None
            self._current_voice = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                import gc

                gc.collect()
            logger.info("Model unloaded from GPU.")


model_manager = ModelManager()
