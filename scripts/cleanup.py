import shutil
import os
import sys
from pathlib import Path

VENV_DIR = ".venv_chatterbox"
CACHE_DIR = "model_cache"
OUTPUT_FILES = ["*.wav", "*.mp3"]


def get_directory_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def format_size(bytes_size):
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def cleanup():
    print("=" * 60)
    print("Chatterbox Turbo - Project Cleanup")
    print("=" * 60)
    print()

    if not os.path.exists(VENV_DIR) and not os.path.exists(CACHE_DIR):
        print("[Cleanup] Nothing to clean. No environment or cache found.")
        return

    total_size = 0
    if os.path.exists(VENV_DIR):
        venv_size = get_directory_size(VENV_DIR)
        total_size += venv_size
        print(f"[Cleanup] Virtual environment: {format_size(venv_size)}")

    if os.path.exists(CACHE_DIR):
        cache_size = get_directory_size(CACHE_DIR)
        total_size += cache_size
        print(f"[Cleanup] Model cache: {format_size(cache_size)}")

    print(f"[Cleanup] Total space to free: {format_size(total_size)}")
    print()

    print("[Cleanup] WARNING: This will delete:")
    print(f"  - Virtual environment ({VENV_DIR})")
    print(f"  - Downloaded models ({CACHE_DIR})")
    print(f"  - Generated audio files ({OUTPUT_FILES})")
    print()

    choice = input(
        "Are you sure you want to proceed? (type 'yes' to confirm): "
    ).strip()
    if choice.lower() != "yes":
        print("[Cleanup] Aborted.")
        return

    print()

    if os.path.exists(VENV_DIR):
        print("[Cleanup] Removing virtual environment...")
        shutil.rmtree(VENV_DIR)
    else:
        print("[Cleanup] Virtual environment not found.")

    if os.path.exists(CACHE_DIR):
        print("[Cleanup] Removing model cache...")
        shutil.rmtree(CACHE_DIR)
    else:
        print("[Cleanup] Model cache not found.")

    print("[Cleanup] Removing generated audio files...")
    for pattern in OUTPUT_FILES:
        for file in Path(".").glob(pattern):
            if file.is_file() and file.name not in [".gitkeep"]:
                try:
                    file.unlink()
                    print(f"  Removed: {file.name}")
                except Exception as e:
                    print(f"  Failed to remove {file.name}: {e}")

    print("[Cleanup] Removing __pycache__ folders...")
    for pycache in Path(".").rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)

    if os.path.exists(".env"):
        choice_env = input("Do you want to remove .env file? (y/N): ").strip().lower()
        if choice_env == "y":
            print("[Cleanup] Removing .env file...")
            os.remove(".env")

    print()
    print("[Cleanup] Cleanup complete!")
    print(f"[Cleanup] Freed approximately {format_size(total_size)}")
    print()


if __name__ == "__main__":
    cleanup()
