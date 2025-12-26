import subprocess
import shutil
import sys
import os

VENV_DIR = ".venv_chatterbox"

def check_uv():
    if not shutil.which("uv"):
        print("[Error] uv is not installed or not in PATH.")
        sys.exit(1)

def setup():
    print("[Setup] Setup using uv...")
    check_uv()
    
    if os.path.exists(VENV_DIR):
        print("[Setup] Virtual environment already exists.")
    else:
        print(f"[Setup] Creating virtual environment (Python 3.11) in {VENV_DIR}...")
        subprocess.run(["uv", "venv", VENV_DIR, "--python", "3.11"], check=True)
        
    print("[Setup] Installing dependencies using uv pip...")
    
    # Install torch with CUDA support
    subprocess.run([
        "uv", "pip", "install", "--python", VENV_DIR, 
        "torch==2.5.1+cu121", "torchaudio==2.5.1+cu121", 
        "--index-url", "https://download.pytorch.org/whl/cu121"
    ], check=True)
    
    # Install other dependencies
    subprocess.run([
        "uv", "pip", "install", "--python", VENV_DIR,
        "chatterbox-tts", "librosa", "soundfile", "ipython", "hf_xet", "python-dotenv"
    ], check=True)
    
    # Apply patch to disable watermarking (if file exists)
    patch_script = "patch_library.py"
    if os.path.exists(patch_script):
        print("[Setup] Applying library patch...")
        python_exe = os.path.join(VENV_DIR, "Scripts", "python.exe")
        subprocess.run([python_exe, patch_script], check=True)
    
    print("[Setup] Done.")
    print(f"To activate: { os.path.join(VENV_DIR, 'Scripts', 'activate') }")

if __name__ == "__main__":
    setup()
