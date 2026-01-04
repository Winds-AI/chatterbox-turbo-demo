import subprocess
import shutil
import sys
import os
from pathlib import Path

VENV_DIR = ".venv_chatterbox"
CACHE_DIR = "model_cache"


def check_uv():
    if not shutil.which("uv"):
        print("[Setup] Installing uv package manager...")
        subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)


def setup():
    print("=" * 60)
    print("Chatterbox Turbo - Project Setup")
    print("=" * 60)

    check_uv()

    if os.path.exists(VENV_DIR):
        print(f"[Setup] Virtual environment already exists at {VENV_DIR}")
        choice = (
            input("Recreate environment? This will delete existing venv. (y/N): ")
            .strip()
            .lower()
        )
        if choice == "y":
            print(f"[Setup] Removing existing environment...")
            shutil.rmtree(VENV_DIR)
        else:
            print("[Setup] Keeping existing environment.")
    else:
        print(f"[Setup] Creating virtual environment (Python 3.11) in {VENV_DIR}...")

    if not os.path.exists(VENV_DIR):
        subprocess.run(["uv", "venv", VENV_DIR, "--python", "3.11"], check=True)

    print("[Setup] Installing dependencies...")

    backend_reqs = Path("backend/requirements.txt")
    frontend_reqs = Path("frontend/requirements.txt")

    print("[Setup] Installing frontend dependencies...")
    if frontend_reqs.exists():
        subprocess.run(
            ["uv", "pip", "install", "--python", VENV_DIR, "-r", str(frontend_reqs)],
            check=True,
        )
    else:
        print("[Setup] Warning: frontend/requirements.txt not found")

    print("[Setup] Installing backend dependencies with CUDA support...")
    if backend_reqs.exists():
        subprocess.run(
            [
                "uv",
                "pip",
                "install",
                "--python",
                VENV_DIR,
                "--extra-index-url",
                "https://download.pytorch.org/whl/cu126",
                "-r",
                str(backend_reqs),
            ],
            check=True,
        )

        venv_python = (
            Path(VENV_DIR) / "Scripts" / "python.exe"
            if os.name == "nt"
            else Path(VENV_DIR) / "bin" / "python"
        )

        patch_script = Path(__file__).parent / "patch_watermark.py"
        if patch_script.exists():
            print("[Setup] Applying watermark patch...")
            subprocess.run([str(venv_python), str(patch_script)], check=False)
    else:
        print("[Setup] Warning: backend/requirements.txt not found")

    print("[Setup] Creating necessary directories...")
    os.makedirs(CACHE_DIR, exist_ok=True)

    print("[Setup] Setup complete!")
    print()
    print("Next steps:")
    print("  1. Activate venv:")
    if os.name == "nt":
        print(f"     {VENV_DIR}\\Scripts\\activate")
    else:
        print(f"     source {VENV_DIR}/bin/activate")
    print()
    print("  2. Download models (optional - will download on first run):")
    if os.name == "nt":
        print(
            f"     {VENV_DIR}\\Scripts\\python.exe -c 'from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID; from huggingface_hub import snapshot_download; snapshot_download(repo_id=REPO_ID)'"
        )
    else:
        print(
            f"     {VENV_DIR}/bin/python -c 'from chatterbox.tts_turbo import ChatterboxTurboTTS, REPO_ID; from huggingface_hub import snapshot_download; snapshot_download(repo_id=REPO_ID)'"
        )
    print()
    print("  3. Start the application:")
    print("     Windows: start_windows.bat")
    print("     Linux/Mac: ./start_linux.sh")
    print()


if __name__ == "__main__":
    setup()
