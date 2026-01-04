# Chatterbox Turbo - Scripts

This folder contains utility scripts for managing the Chatterbox Turbo environment and application.

## Scripts

### setup_env.py
**Purpose**: Set up virtual environment and install dependencies

**When to run**: 
- First time setting up project
- After running `cleanup.py` (when starting work again)

**What it does**:
- Creates virtual environment at `.venv_chatterbox/`
- Installs backend dependencies (FastAPI, torch, torchaudio, chatterbox-tts)
- Installs frontend dependencies (Streamlit, requests)
- Creates `model_cache/` directory

**Usage**:
```bash
python scripts/setup_env.py
```

**Disk usage**: ~3-5 GB
**Time**: 5-10 minutes (depends on internet speed)

---

### cleanup.py
**Purpose**: Remove all project artifacts (venv, models, cache)

**When to run**: 
- Done working on project for 4+ days
- Need to free 3-5 GB of disk space

**What it does**:
- Deletes `.venv_chatterbox/` (virtual environment)
- Deletes `model_cache/` (downloaded models)
- Deletes generated audio files
- Deletes `__pycache__` folders
- Optionally deletes `.env` file

**Usage**:
```bash
python scripts/cleanup.py
```

**Disk freed**: ~3-5 GB
**Time**: 5-10 seconds

**Warning**: Prompts for confirmation before deleting

---

### deload.py
**Purpose**: Unload model from GPU while keeping libraries installed

**When to run**: 
- Need to free GPU memory for other work (gaming, rendering)
- Stopping server for a few hours but will restart same day
- Want to keep torch/torchaudio installed but free VRAM

**What it does**:
- Clears CUDA cache
- Runs Python garbage collection
- Unloads model from GPU (~2-3 GB freed)
- Keeps virtual environment and model cache on disk

**Usage**:
```bash
python scripts/deload.py
```

**VRAM freed**: ~2-3 GB
**Time**: 1-2 seconds
**Note**: Does NOT remove libraries or models from disk

---

## Workflow Guide

### First Time Setup
```bash
python scripts/setup_env.py
```

### Daily Workflow (Starting Work)
```bash
# Terminal 1: Start FastAPI backend
cd backend
python main.py

# Terminal 2: Start Streamlit frontend
cd frontend
streamlit run app.py
```

### Daily Workflow (Done for Day)
```bash
# Stop both terminals with Ctrl+C
# Model automatically unloaded from GPU
```

### Switching to GPU Work (Gaming, Rendering)
```bash
python scripts/deload.py
# Frees ~2-3 GB VRAM, keeps libraries installed
```

### Extended Break (4+ Days)
```bash
python scripts/cleanup.py
# Frees ~3-5 GB, removes everything

# When ready to work again:
python scripts/setup_env.py
# Re-installs everything (5-10 minutes)
```

## Comparison

| Script | Purpose | Disk Freed | Time | When to Use |
|--------|---------|-------------|-------|-------------|
| `setup_env.py` | Install everything | Uses 3-5 GB | 5-10 min | First time, after cleanup |
| `cleanup.py` | Remove everything | Frees 3-5 GB | 5-10 sec | Done for 4+ days |
| `deload.py` | Unload model only | Frees 2-3 GB VRAM | 1-2 sec | Switching to GPU work |
| Stop server | Unload model | Frees 2-3 GB VRAM | Instant | Done for day |

## Error Handling

### setup_env.py fails
- Check internet connection
- Check `uv` is installed: `uv --version`
- Check Python version: `python --version` (need 3.11)
- Check disk space (need 5 GB free)

### cleanup.py fails
- Close any running services (FastAPI, Streamlit)
- Check file permissions
- Windows: Run as administrator if needed

### deload.py fails
- Check CUDA is available: `nvidia-smi`
- Stop FastAPI server first (Ctrl+C)
- Check if other processes are using GPU

## Troubleshooting

### Scripts not found
```bash
# Make sure you're in project root
python scripts/setup_env.py
```

### Permission denied
**Windows**: Run Command Prompt as Administrator
**Linux/Mac**: Use `sudo` or check file permissions

### Virtual environment issues
```bash
# Delete and recreate
rm -rf .venv_chatterbox
python scripts/setup_env.py
```

### Model cache issues
```bash
# Clear cache and re-download
rm -rf model_cache/
python scripts/setup_env.py
```

## Notes

- All scripts can be run from project root
- Virtual environment is created at `.venv_chatterbox/`
- Model cache is created at `model_cache/`
- Scripts require Python 3.11+
- `uv` package manager is installed automatically if missing
