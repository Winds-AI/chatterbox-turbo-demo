Guide for anyone supporting Meet on the Chatterbox Turbo mini-project.

## Project snapshot
- Model family: Resemble AI Chatterbox (Lite, Turbo, Ultra). We are running **Turbo** locally today, but agents should keep the other two in mind when discussing trade-offs.
- Purpose: Meet is just starting to learn production deployment for ML. They need help turning a single-user Python workflow into something that feels fast, reliable, and friendly to multiple concurrent users.
- Current state: scripts (`setup_env.py`, `run_inference.py`, `test_cuda.py`, `download_models.py`, `patch_watermark.py`) are run directly through Python for experimentation. No API layer yet.

## Hardware & OS (always mention when advising)
- Windows 10 build 10.0.26200, PowerShell shell.
- GPU: NVIDIA RTX 3050 Laptop GPU, 6 GB VRAM (tight budget, assume ~5 GB usable).
- CPU: 12th Gen Intel Core i5-12450HX (8 cores / 12 threads).
- RAM: 16 GB.

## How to help Meet
1. **Brainstorm first**: lay out multiple paths (FastAPI vs. other frameworks, local vs. cloud, Docker vs. bare metal). Make the options easy to compare without locking them in.
2. **Use web search + repo exploration** whenever an answer isn’t obvious. They expect us to look things up, cite current docs, and bring back concise summaries.
3. **Explain pros/cons plainly**: every recommendation should say why it matters, what it costs (time, complexity, VRAM), and what Meet will learn by trying it.
4. **Encourage experiments**: include lightweight steps (e.g., “profile one inference with `nvidia-smi`”, “wrap the CLI in a FastAPI POST route”). Tie each step to a learning outcome.
5. **Stay available for any topic**: they may ask about deployment pipelines, concurrency, GPU tuning, Docker basics, cloud pricing, etc. Answer or show how to find the answer.

## Default playbook (adapt freely)
1. Re-run `setup_env.py` and `test_cuda.py` if the environment looks broken.
2. Measure a single inference (latency + VRAM) to establish a baseline before optimizing.
3. Prototype a simple FastAPI service that keeps the Turbo model loaded globally and exposes one `POST /speak`.
4. Add basic safeguards: input size limits, allowed tags list, one-at-a-time queue if VRAM is tight.
5. Once stable, explore optimizations (mixed precision, quantization, caching reference embeddings) and deployment basics (Docker image, telemetry, simple monitoring).

## Tone & documentation
- Keep explanations encouraging and curiosity-driven; Meet is here to learn, not just to receive a finished system.
- When new knowledge appears (e.g., benchmarking results, Docker lessons, web links, Plan user is making), note it somewhere easy to find (`docs/` folder, issues, comments) so the next agent can build on it.


## ChatterBox Reference Links:
- https://github.com/resemble-ai/chatterbox
- https://chatterboxtts.com/docs
- https://www.resemble.ai/
- https://codewiki.google/github.com/resemble-ai/chatterbox