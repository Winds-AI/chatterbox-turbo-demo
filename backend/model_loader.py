import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

os.environ["HF_HOME"] = os.path.abspath("../model_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

import torch
import torchaudio
from huggingface_hub import snapshot_download
from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID


class ModelManager:
    _instance = None
    _model = None
    _device = None
    _current_voice = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_model(self):
        if self._model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._device = device
            print(f"Loading Chatterbox Turbo model on {device}...")

            local_path = snapshot_download(
                repo_id=REPO_ID,
                token=False,
                allow_patterns=["*.safetensors", "*.json", "*.txt", "*.pt", "*.model"],
            )
            self._model = ChatterboxTurboTTS.from_local(local_path, device=device)
            print("Model loaded successfully!")

        return self._model

    def load_voice(self, voice_path: str, exaggeration: float = 0.5):
        model = self.load_model()

        if not os.path.exists(voice_path):
            raise FileNotFoundError(f"Voice file not found: {voice_path}")

        with torch.cuda.amp.autocast(enabled=(self._device == "cuda")):
            model.prepare_conditionals(voice_path, exaggeration=exaggeration)

        self._current_voice = voice_path
        return True

    def generate_speech(self, text: str):
        if self._current_voice is None:
            raise ValueError("No voice loaded")

        model = self.load_model()

        with torch.cuda.amp.autocast(enabled=(self._device == "cuda")):
            wav = model.generate(text)

        return wav


model_manager = ModelManager()
