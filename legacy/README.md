# Legacy Files

This folder contains deprecated scripts from the original CLI-based Chatterbox Turbo implementation.

## Files

- **run_inference.py** - Old CLI interface (replaced by FastAPI backend + Streamlit UI)
- **download_models.py** - Manual model download (now handled by `setup_env.py`)
- **test_cuda.py** - GPU testing script (kept for debugging purposes)
- **patch_watermark.py** - Watermark patching script (no longer needed)

## Migration

These scripts have been replaced by the new architecture:

| Old Script | New Equivalent | Description |
|------------|----------------|-------------|
| `run_inference.py` | `backend/main.py` + `frontend/app.py` | CLI → Web UI |
| `download_models.py` | `setup_env.py` | Manual download → Auto download on setup |
| N/A | `cleanup.py` | Full cleanup script |
| N/A | `deload.py` | GPU model unload only |

## Usage

If you need to use the old CLI:
```bash
cd legacy
python run_inference.py
```

However, this is **not recommended**. Use the new Streamlit + FastAPI interface instead.

## Backward Compatibility

The legacy files are kept for:
- Reference purposes
- Debugging old workflows
- Comparing behavior
- Testing edge cases

They are **not maintained** and may not work with the latest model versions.
