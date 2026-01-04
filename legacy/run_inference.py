import os
import sys
import argparse
import shlex
import traceback
import time
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
            allow_patterns=["*.safetensors", "*.json", "*.txt", "*.pt", "*.model"],
        )
        model = ChatterboxTurboTTS.from_local(local_path, device=device)

        # FP16 optimization via autocast in inference loop
        if device == "cuda":
            print("Using CUDA with Autocast (FP16)...")
            # Print GPU info
            print(f"\n🔧 GPU Information:")
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
                print(f"  VRAM: {props.total_memory / 1024**3:.2f} GB")
                print(f"  Compute Capability: {props.major}.{props.minor}")

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
    print(
        "  load_voice <path_to_wav> [exaggeration]  - Load a voice from a reference audio (5-10s)"
    )
    print(
        "  speak <text>                             - Generate speech with the loaded voice"
    )
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
                    with torch.cuda.amp.autocast(enabled=(device == "cuda")):
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
                    generation_start = time.time()

                    with torch.cuda.amp.autocast(enabled=(device == "cuda")):
                        # conds are already set in model.conds by prepare_conditionals
                        wav = model.generate(text)

                    generation_time = time.time() - generation_start

                    output_filename = "output.wav"
                    # Add simple incrementor or timestamp if needed, but keeping it simple for now
                    torchaudio.save(output_filename, wav.float().cpu(), model.sr)

                    # Calculate audio duration and real-time factor
                    audio_duration = len(wav) / model.sr
                    real_time_factor = generation_time / audio_duration

                    print(f"Saved audio to {output_filename}")
                    print(f"\n{'=' * 60}")
                    print(f"📊 Performance Metrics:")
                    print(f"  Generation Time: {generation_time * 1000:.2f}ms")
                    print(f"  Audio Duration: {audio_duration:.2f}s")
                    print(f"  Real-time Factor: {real_time_factor:.2f}x")
                    print(
                        f"  Speed: {'✅ Faster than real-time' if real_time_factor < 1.0 else '⚠️ Slower than real-time'}"
                    )
                    print(f"{'=' * 60}")
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
