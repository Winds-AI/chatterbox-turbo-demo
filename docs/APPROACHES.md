# Deployment Approaches (TL;DR)

- **Ray Serve (FastAPI ingress, vLLM-like)**  
  - One deployment per GPU (`num_gpus=1`, `max_concurrency=1–2`) to protect 6 GB VRAM; Serve handles queueing/backpressure.  
  - Keep current FastAPI routes (`/generate`, `/load_voice`, `/health`, `/metrics`) via `@serve.ingress`; reuse Prometheus metrics and add Ray queue metrics.  
  - Scale via more replicas/GPUs (Ray autoscaling on queue depth/QPS). Best fit for quick iteration and Python-native serving.

- **NVIDIA Triton (Python backend)**  
  - Package model as Triton Python backend; instance group `count:1`, `gpus:1`, `max_batch_size:1` for safety.  
  - Use Triton’s HTTP/gRPC + built-in Prometheus at `:8002/metrics`; front with NGINX/Envoy for auth/rate limits.  
  - Strong when you want infra-standard serving/metrics; more setup overhead than Ray.

- **BentoML (GPU runner)**  
  - Wrap model as a Bento service; runner with `resources={"gpu":1}` and small worker pool.  
  - Prometheus metrics baked in; build bento → container → deploy on K8s with NVIDIA runtime.  
  - Simple CI/CD packaging; fewer built-in queueing knobs than Ray, lighter than Triton.
