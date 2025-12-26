import shutil
import os
import glob

VENV_DIR = ".venv_chatterbox"
CACHE_DIR = "model_cache"

def cleanup():
    print("[Cleanup] WARNING: This will delete the virtual environment AND the downloaded models.")
    print(f"Directories to be deleted:\n - {VENV_DIR}\n - {CACHE_DIR}\n")
    
    choice = input("Are you sure you want to proceed? (y/N): ").strip().lower()
    if choice != 'y':
        print("[Cleanup] Aborted.")
        return

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

    print("[Cleanup] Removing __pycache__ folders...")
    for pycache in glob.glob("**/__pycache__", recursive=True):
        if os.path.exists(pycache):
            shutil.rmtree(pycache)

    if os.path.exists(".env"):
        choice_env = input("Do you want to remove the .env file containing your token? (y/N): ").strip().lower()
        if choice_env == 'y':
            print("[Cleanup] Removing .env file...")
            os.remove(".env")
            
    print("[Cleanup] Done.")

if __name__ == "__main__":
    cleanup()
