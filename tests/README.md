# Testing & Benchmarking Suite

This directory contains comprehensive testing and performance analysis tools for Chatterbox Turbo.

## Directory Structure

```
tests/
├── requirements.txt           # Python dependencies for testing
├── load/                      # Load testing with Locust
│   └── locustfile.py         # Locust configuration for stress testing
├── benchmark/                 # Performance benchmarking
│   └── benchmark.py          # Detailed benchmarking with reports and plots
└── README.md                 # This file
```

## Setup

1. Install testing dependencies:

```bash
cd tests
pip install -r requirements.txt
```

2. Start the backend server:

```bash
cd backend
python main.py
```

3. In a new terminal, run tests (see sections below).

## Benchmarking

### Quick Benchmark

Run a simple benchmark with 10 sequential requests:

```bash
cd tests/benchmark
python benchmark.py --requests 10 --voice ../audio/reference.wav
```

### Concurrent Benchmark

Test with 50 concurrent requests across 4 workers:

```bash
python benchmark.py --requests 50 --concurrent --workers 4
```

### Full Benchmark with Plots

Run comprehensive benchmark with visualization:

```bash
python benchmark.py --requests 100 --plot --output results.json
```

### Benchmark Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | API base URL | `http://localhost:8000` |
| `--requests` | Number of requests | `10` |
| `--concurrent` | Run requests concurrently | `False` |
| `--workers` | Number of concurrent workers | `4` |
| `--output` | Output JSON file | `benchmark_results.json` |
| `--plot` | Generate latency plots | `False` |
| `--voice` | Path to voice file | `../audio/reference.wav` |

### Benchmark Output

- **Console**: Rich-formatted results with statistics
- **JSON file**: Detailed results for analysis
- **PNG plots**: Latency distribution, time series, and correlations

## Load Testing (Locust)

### Start Locust Web UI

```bash
cd tests/load
locust -f locustfile.py --host http://localhost:8000
```

Then open `http://localhost:8089` in your browser.

### Headless Load Test

```bash
locust -f locustfile.py --host http://localhost:8000 --headless \
  --users 10 --spawn-rate 2 --run-time 60s
```

### Locust Options

| Option | Description |
|--------|-------------|
| `--users` | Number of concurrent users |
| `--spawn-rate` | Users spawned per second |
| `--run-time` | Duration of the test |
| `--headless` | Run without web UI |

## Metrics (Prometheus)

The backend exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

### Available Metrics

| Metric | Description | Labels |
|--------|-------------|--------|
| `tts_requests_total` | Total TTS requests | `endpoint`, `status` |
| `tts_request_duration_seconds` | Request duration | `endpoint`, `operation` |
| `tts_request_phase_duration_seconds` | Phase duration | `phase` |
| `tts_gpu_memory_mb` | GPU memory usage | `device` |
| `tts_gpu_utilization_percent` | GPU utilization | `device` |
| `tts_voice_cache_size` | Cached voice count | - |
| `tts_model_loaded` | Model loaded status | - |
| `tts_concurrent_requests` | Concurrent requests | - |
| `tts_audio_output_size_bytes` | Audio output size | - |
| `tts_input_text_length_chars` | Input text length | - |

### Metrics Visualization

Optionally run Prometheus and Grafana:

```bash
# Start Prometheus
prometheus --config.file=prometheus.yml

# Start Grafana
docker run -d -p 3000:3000 grafana/grafana
```

## Performance Tests Summary

### Test Types

| Test | Purpose | What It Measures |
|------|---------|------------------|
| **Baseline Benchmark** | Establish performance baseline | Latency, throughput, error rate |
| **Concurrent Benchmark** | Test parallel processing | Queue behavior, resource contention |
| **Load Test (Locust)** | Stress test with scaling | Max capacity, failure points |
| **Metrics** | Continuous monitoring | Real-time performance |

### Key Metrics to Track

1. **Latency**: Time from request to response
   - Target: < 500ms for short text
   - Monitor: p50, p95, p99 percentiles

2. **Throughput**: Requests per second
   - Baseline: ~2-3 req/s on RTX 3050
   - Monitor: Degradation over time

3. **GPU Utilization**: How efficiently GPU is used
   - Target: > 70% during generation
   - Monitor: Memory and SM utilization

4. **Error Rate**: Failed requests
   - Target: < 1%
   - Monitor: OOM errors, timeouts

## Testing Workflow

1. **Establish Baseline**
   ```bash
   python benchmark.py --requests 10
   ```

2. **Test Concurrency**
   ```bash
   python benchmark.py --requests 50 --concurrent --workers 2
   ```

3. **Load Test**
   ```bash
   locust -f locustfile.py --headless --users 20 --spawn-rate 2 --run-time 120s
   ```

4. **Analyze Metrics**
   ```bash
   curl http://localhost:8000/metrics | grep tts_request_duration
   ```

5. **Optimize and Retest**

## Interpreting Results

### Latency

| Range | Assessment | Action |
|-------|------------|--------|
| < 200ms | Excellent | Ready for production |
| 200-500ms | Good | Monitor under load |
| 500-1000ms | Acceptable | Consider optimizations |
| > 1000ms | Needs work | Investigate bottlenecks |

### GPU Utilization

| Range | Assessment | Action |
|-------|------------|--------|
| > 70% | Excellent | Good hardware usage |
| 40-70% | Good | Room for batching |
| < 40% | Underutilized | Consider smaller model or batch requests |

### Error Rate

| Range | Assessment | Action |
|-------|------------|--------|
| < 1% | Excellent | Production-ready |
| 1-5% | Warning | Monitor closely |
| > 5% | Critical | Stop and investigate |

## Troubleshooting

### Model Not Loaded

```
Error: No voice loaded
```

**Solution**: Load voice before running tests:
```bash
python benchmark.py --voice ../audio/reference.wav
```

### GPU Out of Memory

```
CUDA out of memory
```

**Solution**: Reduce concurrency or workers:
```bash
python benchmark.py --concurrent --workers 1
```

### Connection Refused

```
requests.exceptions.ConnectionError
```

**Solution**: Ensure backend is running:
```bash
cd backend && python main.py
```

## Next Steps

1. Establish baseline with your hardware
2. Test with different voice samples
3. Measure impact of text length on latency
4. Experiment with caching voice embeddings
5. Test concurrent request handling
6. Document performance characteristics for deployment planning
