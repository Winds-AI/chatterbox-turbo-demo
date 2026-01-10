# Chatterbox Turbo - Beginner-Friendly Setup

## Quick Setup (5 minutes)

### 1. Clone and Enter Directory
```bash
git clone <repository-url>
cd chatterbox
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure HuggingFace
1. Get your HF token: https://huggingface.co/settings/tokens
2. Edit `.env` file:
```env
HF_TOKEN=your_token_here
```

### 5. Run Application (2 terminals)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```
Backend: http://localhost:8000

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```
Frontend: http://localhost:8501

### 6. Open Browser
Go to http://localhost:8501 and start generating speech!

---

## First Run (Downloads ~2GB)
- First startup downloads Chatterbox Turbo model
- Model stored in `models/` folder (~2GB)
- Subsequent starts are instant

---

## Cleanup (When Done)

### Stop Servers
Press `Ctrl+C` in both terminals

### Free Disk Space (~5GB)
```bash
# Remove virtual environment
rmdir /s venv                    # Windows
rm -rf venv                      # Linux/Mac

# Remove models
rmdir /s models                  # Windows
rm -rf models                    # Linux/Mac
```

---

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 3050 6GB | RTX 3060 12GB+ |
| RAM | 8GB | 16GB |
| Disk | 5GB free | 10GB free |
| Python | 3.11 | 3.11 |

---

## Troubleshooting

### "CUDA out of memory"
- Close other GPU applications
- Restart backend: `Ctrl+C`, then restart

### "HF token invalid"
- Check `.env` file has correct token
- Token needs "Read" permission

### Model download fails
- Check internet connection
- Accept model license: https://huggingface.co/resemble-ai/chatterbox-turbo

---

## Project Structure

```
chatterbox/
├── requirements.txt    # Install this
├── .env                # Your HF token
├── backend/            # FastAPI server
│   ├── main.py
│   ├── model_loader.py
│   └── metrics.py
├── frontend/           # Streamlit UI
│   └── app.py
├── models/             # Downloaded models (~2GB)
└── audio/              # Your audio files
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET / | API status |
| GET /health | Model status |
| GET /metrics | Prometheus metrics |
| POST /load_voice | Load voice from file |
| POST /generate | Generate speech |

---

## Credits

- [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) by Resemble AI
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
