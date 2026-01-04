# Chatterbox Turbo - Streamlit + FastAPI

Full-stack TTS application with Streamlit UI and FastAPI backend for Chatterbox Turbo voice cloning.

## Quick Start

### 1. Setup (do this once per work session)
```bash
python scripts/setup_env.py
```
This creates a virtual environment and installs all dependencies (~3-5 GB).

### 2. Run Application

You need 2 terminal windows:

**Terminal 1 - FastAPI Backend:**
```bash
cd backend
python main.py
```
Backend runs on http://localhost:8000

**Terminal 2 - Streamlit Frontend:**
```bash
cd frontend
streamlit run app.py
```
Frontend runs on http://localhost:8501

### 3. Cleanup (when done for 4+ days)
```bash
python scripts/cleanup.py
```
Removes venv, models, and cache (~3-5 GB freed).

### 4. De-load Model (free GPU only)
```bash
python scripts/deload.py
```
Unloads model from GPU but keeps libraries installed (~2-3 GB VRAM freed).

## Documentation

- [MODEL_LIFECYCLE.md](docs/MODEL_LIFECYCLE.md) - Model loading/unloading details
- [STREAMLIT_SETUP.md](docs/STREAMLIT_SETUP.md) - Detailed Streamlit guide
- [DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md) - Deployment branch changes
- [AGENTS.md](docs/AGENTS.md) - Notes for future agents/support

## Project Structure

```
chatterbox/
├── scripts/                    # Utility scripts
│   ├── setup_env.py           # Setup environment
│   ├── cleanup.py             # Full cleanup
│   ├── deload.py             # GPU model unload
│   └── README.md             # Script documentation
├── backend/                   # FastAPI backend
│   ├── main.py               # API endpoints with error handling
│   ├── model_loader.py        # Model singleton management
│   ├── requirements.txt      # Backend dependencies
│   └── Dockerfile
├── frontend/                  # Streamlit UI
│   ├── app.py                # Web interface
│   ├── requirements.txt      # Frontend dependencies
│   └── Dockerfile
├── audio/                     # Audio files
│   ├── reference.wav         # Voice sample for cloning
│   ├── output.wav           # Generated audio (temporary)
│   └── README.md             # Audio management guide
├── docs/                      # Documentation
│   ├── MODEL_LIFECYCLE.md
│   ├── STREAMLIT_SETUP.md
│   ├── DEPLOYMENT_SUMMARY.md
│   └── AGENTS.md
├── legacy/                    # Deprecated scripts
│   ├── run_inference.py
│   ├── download_models.py
│   ├── test_cuda.py
│   └── patch_watermark.py
├── model_cache/               # Downloaded model files (~1-2 GB)
└── .venv_chatterbox/          # Python virtual environment (~2-3 GB)
```

## API Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```
Returns model status, device, and loaded voice.

### Load Voice (local file)
```bash
POST http://localhost:8000/load_voice
Content-Type: application/json

{
  "voice_path": "path/to/voice.wav",
  "exaggeration": 0.5
}
```

### Load Voice (upload)
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
  "text": "Hello, this is Chatterbox Turbo."
}

# Returns: audio/wav file
```

## Model Lifecycle

### When Does Model Load?

**Old CLI**:
- Loads at script start
- Stays loaded for entire session
- Unloads when script exits

**New FastAPI**:
- Loads at server startup (preferred) OR
- Loads on first API request (if startup fails)
- Stays loaded while server runs
- Unloads when server stops

**Key Difference**: In FastAPI, model loads once and serves multiple requests.

### Memory Management

| Action | Command | Memory Freed | Time |
|---------|----------|--------------|------|
| Stop server | `Ctrl+C` | Model from GPU (~2-3 GB) | Instant |
| De-load model | `python scripts/deload.py` | Model from GPU (~2-3 GB) | 1-2s |
| Full cleanup | `python scripts/cleanup.py` | Everything (~3-5 GB) | 5-10s |

**See [docs/MODEL_LIFECYCLE.md](docs/MODEL_LIFECYCLE.md) for detailed documentation.**

## Error Handling

The backend detects and reports specific errors:

1. **503 - Environment Not Setup**
   - Missing libraries or model files
   - Solution: `python setup_env.py`

2. **400 - No Voice Loaded**
   - No voice loaded before generation
   - Solution: Call `/load_voice` or `/load_voice_upload` first

3. **400 - Voice File Not Found**
   - Invalid voice file path
   - Solution: Provide valid WAV/MP3 file

4. **500 - Generation Error**
   - Text processing or model error
   - Check logs for details

## Usage Workflow

### Daily Workflow (Recommended)
```bash
# 1. Setup (only if needed)
python scripts/setup_env.py

# 2. Start application (2 terminals)
# Terminal 1:
cd backend
python main.py

# Terminal 2:
cd frontend
streamlit run app.py

# 3. Open browser: http://localhost:8501
#    - Upload voice sample (5-10s clear speech)
#    - Set exaggeration (0.5 default, 0.7+ expressive)
#    - Enter text and click "Generate Speech"
#    - Download generated audio

# 4. When done working: Stop both servers (Ctrl+C in each)
#    Model automatically unloaded from GPU

# 5. Next day: Just run the commands in step 2
#    Model loads into GPU automatically
```

### Extended Break Workflow (4+ days)
```bash
# 1. Clean up completely
python scripts/cleanup.py
# Frees 3-5 GB (venv + models + cache)

# 2. When ready to work again
python scripts/setup_env.py
# Re-installs everything (takes 5-10 minutes)

# 3. Run application (2 terminals)
# Terminal 1:
cd backend
python main.py

# Terminal 2:
cd frontend
streamlit run app.py
```

## Hardware Requirements

- **GPU**: NVIDIA RTX 3050 6GB (or any CUDA-capable GPU)
- **VRAM**: ~3 GB minimum (model + OS)
- **CPU**: Any modern CPU (CPU fallback available)
- **RAM**: 8 GB minimum, 16 GB recommended
- **Disk**: 5 GB free for venv + models

## Supported Voice Formats

- WAV (recommended)
- MP3
- FLAC
- M4A
- OGG

**Best Results**:
- 5-10 seconds of clear speech
- No background noise
- Consistent speaking style

## Supported Tags

Insert these tags anywhere in text for emotions/sounds:

**Actions**: `[chuckle]`, `[clear throat]`, `[cough]`, `[gasp]`, `[laugh]`, `[shush]`, `[sigh]`, `[sniff]`

**Emotions**: `[advertisement]`, `[angry]`, `[crying]`, `[dramatic]`, `[fear]`, `[happy]`, `[narration]`, `[sarcastic]`, `[surprised]`, `[whispering]`

**Example**: `[laugh] That was amazing! [sigh] I'm so relieved.`

## Troubleshooting

### Server won't start
- Check if venv exists: `python scripts/setup_env.py`
- Check port availability: `netstat -an | findstr 8000`
- Check CUDA: `nvidia-smi`

### Out of memory
- Stop server: `Ctrl+C`
- Run `python scripts/deload.py` to free GPU
- Close other GPU applications

### Model download fails
- Check internet connection
- Check HF_TOKEN in `.env` (for gated models)
- See [scripts/README.md](scripts/README.md) for details

### Voice loading fails
- Check file format (WAV/MP3/FLAC)
- Check file duration (5-10s recommended)
- Check file path is correct

### Generation fails
- Check if voice is loaded: `curl http://localhost:8000/health`
- Check text length (very long text may timeout)
- Check GPU VRAM: `nvidia-smi`

### Script errors
- See [scripts/README.md](scripts/README.md) for detailed documentation
- Check Python version: `python --version` (need 3.11+)
- Check `uv` installation: `uv --version`

## Next Steps

- Add user authentication
- Implement voice library management (save/load multiple voices)
- Add streaming audio support (lower latency)
- Add request queue for concurrent users
- Add telemetry and monitoring
- Docker deployment for cloud hosting

## Credits

- Chatterbox TTS: [Resemble AI](https://github.com/resemble-ai/chatterbox)
- Streamlit: [Streamlit.io](https://streamlit.io/)
- FastAPI: [FastAPI.tiangolo.com](https://fastapi.tiangolo.com/)

## License

See individual component licenses.
