# Chatterbox Turbo - Local Inference

This project allows you to run Resemble AI's Chatterbox Turbo model locally on your machine (RTX 3050 6GB optimized). Supports Windows, Linux, and macOS.

## 🚀 Setup

1.  **Install Environment**:
    Run `setup_env.py` to create the Python environment and install all dependencies (using `uv`).
    ```batch
    python setup_env.py
    ```

2.  **Test GPU Access**:
    Verify that your GPU is accessible and PyTorch CUDA installation is working correctly.
    ```batch
    .\.venv_chatterbox\Scripts\python.exe test_cuda.py
    ```
    This will check CUDA availability, display GPU information, and test basic tensor operations.

3.  **Download Models**:
    Run the download script to fetch the model weights to the local `./model_cache` folder.

    **Windows:**
    ```batch
    .\.venv_chatterbox\Scripts\python.exe download_models.py
    ```

    **Linux/macOS:**
    ```bash
    ./.venv_chatterbox/bin/python download_models.py
    ```

## 🎤 Usage

1.  **Start the CLI**:
    Launch the interactive inference tool.

    **Windows:**
    ```batch
    .\.venv_chatterbox\Scripts\python.exe run_inference.py
    ```

    **Linux/macOS:**
    ```bash
    ./.venv_chatterbox/bin/python run_inference.py
    ```

2.  **Load a Voice**:
    You need a 5-10 second reference `.wav` file (e.g., `reference.wav`).
    ```text
    > load_voice reference.wav
    ```
    *Optionally, specify exaggeration (0.25-2.0, default 0.5, recommended 0.7+ for more expressiveness):*
    ```text
    > load_voice reference.wav 0.8
    ```
    *(Note: Exaggeration is set during voice loading and affects all subsequent generations for that voice.)*

3.  **Generate Speech**:
    Type `speak` followed by your text.
    ```text
    > speak Hello, this is a test.
    ```
    The audio will be saved to `output.wav` in the current directory.

## 🎭 Supported Tags

You can insert these tags anywhere in your text to add emotions or non-speech sounds.

### Actions
*   `[chuckle]`
*   `[clear throat]`
*   `[cough]`
*   `[gasp]`
*   `[laugh]`
*   `[shush]`
*   `[sigh]`
*   `[sniff]`

### Emotions & Styles
*   `[advertisement]`
*   `[angry]`
*   `[crying]`
*   `[dramatic]`
*   `[fear]`
*   `[happy]`
*   `[narration]`
*   `[sarcastic]`
*   `[surprised]`
*   `[whispering]`

### Example
```text
> speak [laugh] I can't believe you did that! [sigh] I am so relieved.
```
```text
> [whispering] I can't believe you did that! [sigh] I am so relieved.
```
## 🛠 Troubleshooting
*   **Permissions/Symlink Errors**: The scripts are configured to disable symlinks and copy files directly to `model_cache` to avoid permission issues across platforms.
*   **Watermarking**: The `resemble-perth` library (watermarking) has been patched to be disabled if it causes crashes.
*   **Disk Space**: I made this to test and run in my personal laptop so you can clean up properly. The model and environment take up ~4-5GB. If you need to uninstall, run `python cleanup.py`.
