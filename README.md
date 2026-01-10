# 🎙️ Chatterbox Turbo - Beginner-Friendly TTS

Realistic AI text-to-speech with voice cloning. Setup in 2 minutes.

![Chatterbox Turbo](https://img.shields.io/badge/Chatterbox-Turbo-blue?style=for-the-badge)

---

## ⚡ Quick Setup

### 1. Install uv (one-time)
**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup
```bash
git clone <repository-url>
cd chatterbox

# Create venv with Python 3.11 (required for compatibility)
uv venv --python 3.11 .cb_venv
.cb_venv\Scripts\activate    # Windows
# source .cb_venv/bin/activate  # Linux/Mac

uv pip install -r requirements.txt
```

### 3. Configure HuggingFace
1. Get your token: https://huggingface.co/settings/tokens
2. Edit `.env` file:
```env
HF_TOKEN=your_token_here
```

### 4. Run (2 terminals)

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
streamlit run app.py
```

### 5. Open Browser
→ http://localhost:8501

---

## 📦 First Run

- **Downloads ~2GB** on first start (Chatterbox Turbo model)
- Model stored in `models/` folder
- Next starts are instant

---

## 🧹 Cleanup

```bash
# Remove venv
rmdir /s .cb_venv                   # Windows
rm -rf .cb_venv                     # Linux/Mac

# Remove models (~2GB)
rmdir /s models                   # Windows
rm -rf models                     # Linux/Mac
```

---

## 💻 Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | RTX 3050 6GB | RTX 3060 12GB+ |
| VRAM | 6GB | 8GB+ |
| RAM | 8GB | 16GB |
| Disk | 10GB free | 20GB free |
| Python | 3.11 | 3.11 |

**Note:** Requires NVIDIA GPU with CUDA support.

---

## 🔧 Troubleshooting

### "CUDA is not available"
PyTorch installed without CUDA. Reinstall with GPU support:

```bash
.cb_venv\Scripts\activate
uv pip uninstall torch torchaudio
uv pip install -r requirements.txt
```

Verify CUDA:
```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### CUDA out of memory
- Close other GPU applications
- Restart backend (Ctrl+C → rerun)
- Reduce text length for generation

### HF token invalid
- Check `.env` has correct token
- Token needs "Read" permission

### Model download fails
- Check internet connection
- Accept license: https://huggingface.co/resemble-ai/chatterbox-turbo

### Audio folder missing
```bash
mkdir audio
```
Add `.wav` or `.mp3` files to `audio/` for quick voice selection.

---

## 📁 Project Structure

```
chatterbox/
├── requirements.txt    # Dependencies (CUDA-enabled PyTorch)
├── .env                # HF token (create this)
├── README.md
├── audio/              # Voice samples (create if needed)
├── models/             # Downloaded models (~2GB)
├── backend/
│   ├── __init__.py
│   ├── main.py        # FastAPI server
│   └── model_loader.py
└── frontend/
    ├── __init__.py
    └── app.py         # Streamlit UI
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/health` | Model status, device, loaded voice |
| POST | `/load_voice` | Load voice from file path |
| POST | `/load_voice_upload` | Upload voice file |
| POST | `/generate` | Generate speech (returns WAV) |

---

## 🙏 Credits

- [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) by Resemble AI
- [FastAPI](https://fastapi.tiangolo.com/)
- [Streamlit](https://streamlit.io/)
- [uv](https://astral.sh/uv) - Ultra-fast Python package manager
- [PyTorch](https://pytorch.org/) - CUDA-enabled deep learning
