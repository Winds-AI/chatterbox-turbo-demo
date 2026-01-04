# Deployment Branch - Summary

## What Changed

This branch refactors the project to use **Streamlit + FastAPI** architecture with proper setup/cleanup workflows.

## New File Structure

```
chatterbox/
├── backend/                    # NEW: FastAPI backend
│   ├── main.py                # API endpoints with error handling
│   ├── model_loader.py         # Model singleton management
│   ├── requirements.txt        # Backend dependencies
│   ├── exceptions.py          # Custom exceptions (optional)
│   └── Dockerfile
├── frontend/                   # NEW: Streamlit UI
│   ├── app.py                 # Web interface
│   ├── requirements.txt        # Frontend dependencies
│   └── Dockerfile
├── model_cache/               # Model download location (gitignored)
├── .venv_chatterbox/          # Virtual environment (gitignored)

# Scripts
├── setup_env.py              # UPDATED: Works with backend/frontend
├── cleanup.py                # UPDATED: Shows disk space before cleanup
├── deload.py                # NEW: Unload model from GPU only
├── start_windows.bat         # NEW: Quick start for Windows
└── start_linux.sh           # NEW: Quick start for Linux/Mac

# Documentation
├── README.md                 # UPDATED: Full project docs
├── MODEL_LIFECYCLE.md      # NEW: Model loading/unloading details
├── STREAMLIT_SETUP.md      # NEW: Detailed Streamlit guide
└── AGENTS.md                # Existing: Agent support notes

# Docker
└── docker-compose.yml        # NEW: Run both services
```

## Key Improvements

### 1. Proper Environment Management
- **setup_env.py**: Creates venv, installs dependencies for both backend/frontend
- **cleanup.py**: Removes everything (shows disk usage before cleanup)
- **deload.py**: NEW - Unloads model from GPU but keeps libraries installed

### 2. Error Handling in Backend
- **503 Error**: Environment not setup (missing libraries or models)
- **400 Error**: No voice loaded
- **400 Error**: Voice file not found
- **500 Error**: Generic errors with stack traces

### 3. Model Lifecycle Clarity
- Documented in [MODEL_LIFECYCLE.md](MODEL_LIFECYCLE.md)
- Shows exactly when model loads/unloads in CLI vs FastAPI
- Guides user on cleanup vs de-load decisions

### 4. One-Command Startup
- **Windows**: `start_windows.bat` - Starts backend + frontend
- **Linux/Mac**: `./start_linux.sh` - Starts backend + frontend
- **Docker**: `docker-compose up` - Containerized deployment

### 5. Web Interface
- Streamlit UI for easy voice upload and text input
- Real-time generation status
- Audio playback in browser
- Download generated audio
- Health status in sidebar

## Model Loading Behavior

### Old CLI (run_inference.py)
```
Start script → Load model (2-5s) → Stay loaded → Exit → Auto-unload
```

### New FastAPI (backend/main.py)
```
Start server → Load model (2-5s) → Stay loaded → Stop server → Auto-unload
              (or delay to first request if startup fails)
```

### Key Difference
- **CLI**: Model loaded once, single user
- **FastAPI**: Model loaded once, serves multiple users/concurrent requests

## Memory Management for RTX 3050 (6GB)

| Action | Command | What Frees | Time |
|---------|----------|-------------|------|
| Stop server | `Ctrl+C` | Model from GPU (~2-3 GB) | Instant |
| De-load model | `python deload.py` | Model from GPU (~2-3 GB) | 1-2s |
| Full cleanup | `python cleanup.py` | Everything (~3-5 GB) | 5-10s |

**Recommendation**:
- Use `setup_env.py` when starting work session
- Stop server with `Ctrl+C` when done for the day
- Use `deload.py` if switching to GPU work (gaming, rendering)
- Use `cleanup.py` only when done for 4+ days

## Error Detection by Backend

### 1. Environment Not Setup (503)
```json
{
  "error": "environment_not_setup",
  "message": "Required libraries not installed. Please run: python setup_env.py",
  "solution": "Run: python setup_env.py"
}
```

### 2. Model Files Missing (503)
```json
{
  "error": "environment_not_setup",
  "message": "Model files not found in cache directory: ./model_cache",
  "solution": "Run: python setup_env.py to download models"
}
```

### 3. No Voice Loaded (400)
```json
{
  "error": "no_voice_loaded",
  "message": "No voice has been loaded",
  "solution": "Call POST /load_voice or POST /load_voice_upload first"
}
```

### 4. Voice File Not Found (400)
```json
{
  "error": "voice_file_not_found",
  "message": "Voice file not found: /path/to/file.wav",
  "solution": "Provide a valid path to a WAV/MP3 file"
}
```

## Files to Remove (From Previous Version)

These files are deprecated but can be archived:
- `run_inference.py` - Old CLI interface
- `download_models.py` - Manual model download (now done by setup_env.py)
- `test_cuda.py` - GPU testing (can be useful, keep for debugging)
- `patch_watermark.py` - Watermark patching (no longer needed)
- `backend/exceptions.py` - Exception moved to model_loader.py

**Suggested Action**: Archive these in `legacy/` folder or remove them.

## Quick Start Commands

```bash
# First time setup
python setup_env.py

# Start application
start_windows.bat          # Windows
./start_linux.sh           # Linux/Mac

# Stop application
Ctrl+C (in terminal)

# Free GPU only (keep libraries)
python deload.py

# Full cleanup (done for 4+ days)
python cleanup.py
```

## Next Steps

1. Test the setup:
   ```bash
   python setup_env.py
   start_windows.bat
   ```

2. Test cleanup:
   ```bash
   python deload.py
   python cleanup.py
   ```

3. Commit changes:
   ```bash
   git add .
   git commit -m "Refactor to Streamlit + FastAPI with setup/cleanup scripts"
   ```

4. Test on clean machine (optional):
   ```bash
   # On a different machine/VM
   git clone <repo>
   git checkout deployment
   python setup_env.py
   start_windows.bat
   ```

## Notes for Agents/Support

- User is on Windows 10 with RTX 3050 6GB
- Space is limited, so cleanup script is important
- Model should auto-load on server startup or first request
- Backend detects missing environment and returns 503 error
- De-load script exists to free GPU without removing libraries
- Full cleanup frees ~3-5 GB (venv + models + cache)
