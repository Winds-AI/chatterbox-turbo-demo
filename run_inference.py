import os
import sys
import argparse
import shlex
import traceback
from pathlib import Path

# Ensure models are cached locally and symlinks are disabled
os.environ["HF_HOME"] = os.path.abspath("./model_cache")
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

import torch
import torchaudio
from huggingface_hub import snapshot_download
from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID

def load_model(device):
    print(f"Loading Chatterbox Turbo model on {device}...")
    try:
        # Resolve model path (uses cache)
        local_path = snapshot_download(
            repo_id=REPO_ID,
            token=False,
            allow_patterns=["*.safetensors", "*.json", "*.txt", "*.pt", "*.model"]
        )
        model = ChatterboxTurboTTS.from_local(local_path, device=device)
        
        # FP16 optimization via autocast in inference loop
        if device == "cuda":
            print("Using CUDA with Autocast (FP16)...")
        
        return model
    except Exception:
        traceback.print_exc()
        sys.exit(1)

def main():
    print("Initializing Chatterbox Turbo CLI...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")
    
    if device == "cpu":
        print("Warning: Running on CPU. Inference will be slow.")

    model = load_model(device)
    print("\nChatterbox Turbo Ready!")
    print("Commands:")
    print("  load_voice <path_to_wav> [exaggeration]  - Load a voice from a reference audio (5-10s)")
    print("  speak <text>                             - Generate speech with the loaded voice")
    print("  exit                                     - Quit")

    current_voice_path = None
    
    while True:
        try:
            user_input = input("\n> ").strip()
            if not user_input:
                continue
                
            parts = shlex.split(user_input)
            command = parts[0].lower()
            
            if command == "exit":
                break
                
            elif command == "load_voice":
                if len(parts) < 2:
                    print("Usage: load_voice <path_to_wav> [exaggeration]")
                    continue
                
                path = parts[1]
                exaggeration = float(parts[2]) if len(parts) > 2 else 0.5
                
                if not os.path.exists(path):
                    print(f"Error: File not found: {path}")
                    continue
                    
                print(f"Processing voice from {path} (exaggeration={exaggeration})...")
                try:
                    # Prepare conditionals (cache validity)
                    # We utilize the model's prepare_conditionals method which sets model.conds
                    with torch.cuda.amp.autocast(enabled=(device=="cuda")):
                        model.prepare_conditionals(path, exaggeration=exaggeration)
                    current_voice_path = path
                    print("Voice loaded successfully!")
                except Exception as e:
                    print(f"Error loading voice: {e}")

            elif command == "speak":
                if len(parts) < 2:
                    print("Usage: speak <text>")
                    continue
                
                if current_voice_path is None:
                    print("Error: No voice loaded. Use 'load_voice' first.")
                    continue

                text = " ".join(parts[1:])
                print("Generating...")
                
                try:
                    # Use autocast for FP16 inference
                    with torch.cuda.amp.autocast(enabled=(device=="cuda")):
                        # conds are already set in model.conds by prepare_conditionals
                        wav = model.generate(text)
                    
                    output_filename = "output.wav"
                    # Add simple incrementor or timestamp if needed, but keeping it simple for now
                    torchaudio.save(output_filename, wav.float().cpu(), model.sr)
                    print(f"Saved audio to {output_filename}")
                except Exception as e:
                     print(f"Error generating speech: {e}")
            
            else:
                print("Unknown command.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    print("Goodbye!")

if __name__ == "__main__":
    main()
