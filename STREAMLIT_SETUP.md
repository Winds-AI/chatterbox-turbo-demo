# Chatterbox Turbo - Streamlit + FastAPI

Streamlit frontend with FastAPI backend for Chatterbox Turbo TTS.

## Project Structure
```
chatterbox/
├── backend/              # FastAPI backend
│   ├── main.py          # API endpoints
│   ├── model_loader.py  # Model management
│   └── requirements.txt
├── frontend/             # Streamlit UI
│   ├── app.py           # Streamlit app
│   └── requirements.txt
└── docker-compose.yml    # Docker deployment
```

## Local Development (Recommended)

### Prerequisites
- Python 3.11
- NVIDIA GPU with CUDA (or CPU fallback)
- Virtual environment already set up with chatterbox-tts installed

### 1. Install Backend Dependencies
```bash
# Activate your existing venv
.venv_chatterbox/Scripts/activate  # Windows
# or: source .venv_chatterbox/bin/activate  # Linux/Mac

# Install FastAPI and dependencies
pip install -r backend/requirements.txt
```

### 2. Install Frontend Dependencies
```bash
pip install -r frontend/requirements.txt
```

### 3. Run Both Services

**Option A: Two Terminal Windows**

Terminal 1 (Backend):
```bash
cd backend
python main.py
# Backend runs on http://localhost:8000
```

Terminal 2 (Frontend):
```bash
cd frontend
streamlit run app.py
# Frontend runs on http://localhost:8501
```

**Option B: PowerShell (Windows)**
```powershell
# Run backend in background
Start-Process -FilePath "python" -ArgumentList "backend\main.py" -NoNewWindow

# Run frontend in foreground
streamlit run frontend\app.py
```

**Option C: Bash (Linux/Mac)**
```bash
# Run backend in background
cd backend && python main.py &
cd ..

# Run frontend
streamlit run frontend/app.py
```

### 4. Use the App
1. Open http://localhost:8501 in your browser
2. Upload a voice file (5-10 seconds of clear speech)
3. Set exaggeration (0.5 = default, 0.7+ = more expressive)
4. Enter text to synthesize
5. Click "Generate Speech" and download the audio

## Docker Deployment

### Prerequisites
- Docker Desktop with NVIDIA Container Toolkit
- (Optional) Docker Compose

### Build and Run
```bash
# Create Dockerfiles (see below)
docker-compose up -d --build
```

The app will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

### Load Voice (from local file)
```bash
POST http://localhost:8000/load_voice
Content-Type: application/json

{
  "voice_path": "path/to/voice.wav",
  "exaggeration": 0.5
}
```

### Load Voice (upload file)
```bash
POST http://localhost:8000/load_voice_upload
Content-Type: multipart/form-data

voice_file: <file>
exaggeration: 0.5
```

### Generate Speech
```bash
POST http://localhost:8000/generate
Content-Type: application/json

{
  "text": "Hello, this is a test."
}

# Returns: audio/wav file
```

## Troubleshooting

### Backend not responding
- Check backend is running: http://localhost:8000/health
- Check console for CUDA/GPU errors

### CORS errors
- CORS is enabled for all origins in backend/main.py
- Clear browser cache if issues persist

### Out of memory errors
- Reduce batch size if implemented
- Close unused applications
- Check VRAM usage with `nvidia-smi`

### Voice loading fails
- Ensure voice file is 5-10 seconds
- Check file format (WAV/MP3/FLAC recommended)
- Verify file path is correct

## Next Steps

- Add user authentication
- Implement voice library management
- Add streaming response support
- Add request queue for concurrent users
- Add telemetry/monitoring
- Containerize for cloud deployment
