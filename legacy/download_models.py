import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure models are cached locally and symlinks are disabled (fixes WinError 1314)
os.environ["HF_HOME"] = os.path.abspath("./model_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
# Enable hf_xet if installed (though huggingface_hub usually auto-detects it)
# We can't easily force it if not detected, but installing it is the main step.

import torch
from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID
from huggingface_hub import snapshot_download

def download_model():
    print("Setting up model cache at:", os.environ["HF_HOME"])
    print("Downloading Chatterbox Turbo model... This may take a few minutes.")
    
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("Warning: HF_TOKEN not found in .env. Downloading seamlessly might fail for gated repos.")
    else:
        print("HF_TOKEN found.")

    try:
        # Download with token if available, using hf_xet implicitly if installed
        local_path = snapshot_download(
            repo_id=REPO_ID,
            token=hf_token,
            allow_patterns=["*.safetensors", "*.json", "*.txt", "*.pt", "*.model"]
        )
        print(f"Model downloaded to: {local_path}")
        
        # Verify loading works
        model = ChatterboxTurboTTS.from_local(local_path, device="cpu")
        print("Model verified successfully!")
             
    except Exception as e:
        print(f"Error downloading model: {e}")

if __name__ == "__main__":
    download_model()
