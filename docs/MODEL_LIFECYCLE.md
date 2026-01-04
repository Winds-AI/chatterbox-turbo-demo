# Model Lifecycle Documentation

## Overview

Understanding when the Chatterbox Turbo model loads and unloads from GPU/CPU is crucial for managing memory on your laptop.

## Old CLI Implementation (run_inference.py)

### Model Loading
- **When**: At startup (line 55)
- **How**: `model = load_model(device)`
- **Duration**: Model stays loaded for entire CLI session
- **Location**: GPU (if CUDA available) or CPU

### Model Unloading
- **When**: When script exits or user types "exit"
- **How**: Python garbage collection (automatic)
- **Memory**: Freed from GPU/CPU automatically when process terminates

**Memory Behavior**:
```
Start Script
  ↓
Load Model (~2-3 GB VRAM)
  ↓
Model stays loaded
  ↓
[Generate speech multiple times]
  ↓
Script exits → Model automatically freed
```

## New FastAPI Backend Implementation

### Model Loading
- **When**: Two scenarios
  1. **Startup** (preferred): `@app.on_event("startup")` loads model at server start
  2. **Lazy load**: If startup fails, model loads on first API request

- **How**: `model_manager.load_model()` (singleton pattern)
- **Duration**: Model stays loaded while server is running
- **Location**: GPU (if CUDA available) or CPU

### Model Unloading
- **When**: Server stops (Ctrl+C, process kill)
- **How**: Python garbage collection (automatic)
- **Additional**: `model_manager.unload_model()` method available for manual unload

**Memory Behavior**:
```
Start FastAPI Server
  ↓
Load Model (~2-3 GB VRAM) [or delay to first request]
  ↓
Model stays loaded
  ↓
[Handle API requests]
  ↓
Server stops → Model automatically freed
```

## Key Differences

| Aspect | CLI | FastAPI |
|--------|-----|---------|
| **Load Trigger** | Script startup | Server startup (or first request) |
| **Load Time** | 2-5 seconds once | 2-5 seconds at server start |
| **Memory** | ~2-3 GB for CLI session | ~2-3 GB for server lifetime |
| **Unload Trigger** | Script exit | Server stop |
| **Manual Unload** | Not available | `model_manager.unload_model()` |
| **Concurrent Access** | Single user | Multiple users (same model) |

## Memory Management for Your Use Case

### Scenario 1: Working on Project (Daily)

```bash
# 1. Setup environment (do this once per work session)
python setup_env.py

# 2. Start server (model loads automatically)
cd backend
python main.py
# Model stays in memory (~2-3 GB VRAM) while server runs

# 3. Work all day (generate speech, test features)

# 4. Stop server when done
Ctrl+C  # Model automatically unloaded
```

### Scenario 2: Not Working (4+ Days)

**Option A: Full Cleanup** (Recommended)
```bash
python cleanup.py
# Removes:
# - Virtual environment (~2-3 GB)
# - Model cache (~1-2 GB)
# - Generated audio files
# Total freed: ~3-5 GB
```

**Option B: Model Only De-load** (Keep libraries installed)
```bash
# Use deload.py to free GPU memory while keeping torch/torchaudio installed
python deload.py
# Frees:
# - Model from GPU (~2-3 GB VRAM)
# Keeps:
# - Python libraries installed
# - Model cache on disk
# Total freed: ~2-3 GB VRAM only
```

### Scenario 3: Daily Workflow

```bash
# Morning: Setup and start
python setup_env.py        # Creates venv if needed
cd backend && python main.py
# Model loads into GPU

# Throughout day: Generate speech via Streamlit UI
# Model stays loaded (fast response)

# Evening: Stop working
Ctrl+C  # Model automatically unloaded

# Next morning: Just start server again
# No need to re-setup unless you ran cleanup.py
cd backend && python main.py
# Model loads into GPU
```

## Decision Guide: Cleanup vs De-load

| Situation | Command | What Gets Freed | What Remains |
|-----------|----------|----------------|--------------|
| **Done for 4+ days** | `python cleanup.py` | Venv, models, cache (~3-5 GB) | Nothing (project clean) |
| **Done for 1-2 days** | `python deload.py` | Model from GPU (~2-3 GB VRAM) | Venv, libraries, cache |
| **Taking a break (hours)** | Stop server (Ctrl+C) | Model from GPU/CPU | Venv, libraries, cache, models |
| **Switching to GPU work** | `python deload.py` | Model from GPU | Libraries ready for next use |
| **Disk space critical** | `python cleanup.py` | Everything (~3-5 GB) | Nothing |

## FastAPI Server Memory Behavior

### With Model Loaded
- **GPU Memory**: ~2-3 GB (model weights)
- **CPU Memory**: ~500 MB - 1 GB (Python process + overhead)
- **Per Request**: Additional ~100-200 MB VRAM during generation (temporary)

### Without Model (Environment Check)
- **GPU Memory**: 0 GB (until model loads)
- **CPU Memory**: ~50 MB (FastAPI server only)
- **Startup Time**: <1 second

### Error Detection

The backend automatically detects and reports these errors:

1. **Libraries not installed** (503 error)
   - Message: "Required libraries not installed. Run: python setup_env.py"
   - When: Trying to import torch/torchaudio

2. **Model files missing** (503 error)
   - Message: "Model files not found in cache. Run: python setup_env.py"
   - When: `HF_HOME` directory doesn't contain downloaded models

3. **No voice loaded** (400 error)
   - Message: "No voice has been loaded"
   - Solution: Call `/load_voice` or `/load_voice_upload` first

4. **Voice file not found** (400 error)
   - Message: "Voice file not found: {path}"
   - Solution: Provide valid path to WAV/MP3 file

## Recommendations for Your RTX 3050 (6GB)

### VRAM Budget
- Model: ~2.5 GB
- Operating system: ~1.5 GB
- Available: ~2 GB (tight!)

### Best Practices
1. **Stop server when not in use** (Ctrl+C) - frees VRAM immediately
2. **Use `deload.py`** if switching to other GPU work (gaming, rendering)
3. **Run `cleanup.py`** only when done for extended periods (4+ days)
4. **Close other GPU apps** when running Chatterbox (Chrome hardware accel, etc.)

### Monitoring VRAM
```bash
# Watch VRAM usage
nvidia-smi -l 1

# Python script to check VRAM
import torch
if torch.cuda.is_available():
    print(f"Allocated: {torch.cuda.memory_allocated(0) / 1024**3:.2f} GB")
    print(f"Reserved: {torch.cuda.memory_reserved(0) / 1024**3:.2f} GB")
```

## Summary

**For your use case (personal laptop, occasional use)**:

1. **Use `setup_env.py`** when starting work session
2. **Run server with `start_windows.bat`** (or `start_linux.sh`)
3. **Stop server (Ctrl+C)** when done for the day
4. **Run `deload.py`** only if switching to GPU-intensive work
5. **Run `cleanup.py`** when done for 4+ days to free 3-5 GB

**Don't use `cleanup.py` daily** - re-downloading models takes time and bandwidth.
