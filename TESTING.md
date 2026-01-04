# Testing & Monitoring Quick Start

Complete testing and monitoring infrastructure for Chatterbox Turbo deployment learning.

## What's New

### ✅ Added Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Prometheus Metrics** | `backend/metrics.py` | Real-time performance tracking |
| **Benchmark Suite** | `tests/benchmark/benchmark.py` | Latency, throughput, detailed analysis |
| **Load Testing** | `tests/load/locustfile.py` | Stress test with concurrent users |
| **Test Runner** | `run_tests.py` | One-command test execution |

---

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
# Backend dependencies (includes Prometheus)
cd backend
pip install -r requirements.txt

# Testing dependencies
cd ../tests
pip install -r requirements.txt
```

### 2. Start Backend

```bash
cd backend
python main.py
```

Backend now runs with metrics at `http://localhost:8000/metrics`

### 3. Run Quick Benchmark

In a new terminal:

```bash
# Quick baseline test (10 requests)
python run_tests.py benchmark --requests 10

# Full output with plots
cd tests/benchmark
python benchmark.py --requests 20 --plot --voice ../audio/reference.wav
```

### 4. Check Metrics

```bash
# See all Prometheus metrics
curl http://localhost:8000/metrics

# Or use the test runner
python run_tests.py metrics
```

### 5. Load Test (Optional)

```bash
# Start Locust web UI
python run_tests.py load --users 10

# Or run headless
python run_tests.py load --headless --users 5 --run-time 30s
```

---

## New File Structure

```
chatterbox/
├── backend/
│   ├── main.py              # Updated with Prometheus metrics
│   ├── model_loader.py      # (unchanged)
│   ├── metrics.py           # NEW: Metrics manager
│   ├── requirements.txt     # Updated with prometheus_client
│   └── Dockerfile
├── tests/                   # NEW directory
│   ├── requirements.txt     # Testing dependencies
│   ├── README.md           # Detailed testing guide
│   ├── load/
│   │   └── locustfile.py  # Locust load tests
│   └── benchmark/
│       └── benchmark.py    # Benchmarking tool
├── run_tests.py            # NEW: Unified test runner
└── TESTING.md              # This file
```

---

## Available Metrics

The `/metrics` endpoint exposes:

| Metric | Description |
|--------|-------------|
| `tts_requests_total` | Total requests (by endpoint, status) |
| `tts_request_duration_seconds` | Request latency (p50, p95, p99) |
| `tts_request_phase_duration_seconds` | Breakdown by phase |
| `tts_gpu_memory_mb` | GPU memory usage |
| `tts_gpu_utilization_percent` | GPU utilization |
| `tts_voice_cache_size` | Cached voice embeddings |
| `tts_model_loaded` | Model loaded status |
| `tts_concurrent_requests` | Active concurrent requests |
| `tts_audio_output_size_bytes` | Output audio size |
| `tts_input_text_length_chars` | Input text length |

---

## Test Commands Cheat Sheet

### Benchmark Tests

```bash
# Basic benchmark
python run_tests.py benchmark --requests 10

# Concurrent benchmark
python run_tests.py benchmark --concurrent --requests 50 --workers 4

# Advanced benchmark (with plots)
cd tests/benchmark
python benchmark.py --requests 100 --plot --output results.json --voice ../audio/reference.wav
```

### Load Tests

```bash
# Web UI mode (interactive)
python run_tests.py load --users 10

# Headless mode (automated)
python run_tests.py load --headless --users 20 --spawn-rate 2 --run-time 60s
```

### Metrics

```bash
# View current metrics
python run_tests.py metrics

# Or directly
curl http://localhost:8000/metrics
```

### Full Suite

```bash
# Run all tests sequentially
python run_tests.py suite
```

---

## Interpreting Results

### Benchmark Output

```
╭─ Benchmark Results ─────────────────────╮
│ Metric            Value                  │
├──────────────────────────────────────────┤
│ Total Requests    50                    │
│ Successful        50                    │
│ Error Rate        0.00%                 │
│ Throughput        2.45 req/s           │
╰──────────────────────────────────────────╯
```

### Key Metrics to Track

| Metric | Good | Needs Work |
|--------|------|------------|
| **Latency (p95)** | < 500ms | > 1000ms |
| **Throughput** | > 2 req/s | < 1 req/s |
| **GPU Utilization** | > 60% | < 40% |
| **Error Rate** | < 1% | > 5% |

---

## What to Test First

### 1. Baseline Performance
```bash
python run_tests.py benchmark --requests 20
```
**Why:** Establish your starting point.

### 2. Single User vs. Concurrent
```bash
# Sequential
python run_tests.py benchmark --requests 20

# Concurrent
python run_tests.py benchmark --concurrent --requests 20 --workers 2
```
**Why:** See how performance degrades under load.

### 3. Max Capacity (Find Breaking Point)
```bash
python run_tests.py load --headless --users 10 --run-time 60s
# Increase --users until errors appear
```
**Why:** Know your limits before deploying.

### 4. Continuous Monitoring
```bash
# In one terminal
watch -n 1 'curl -s http://localhost:8000/metrics | grep tts_concurrent_requests'

# In another, run load test
python run_tests.py load --headless --users 5
```
**Why:** Understand real-time behavior.

---

## Learning Path

### Week 1: Baseline & Observation
- [ ] Run 10-request baseline benchmark
- [ ] Check metrics after each request
- [ ] Understand latency vs. text length correlation

### Week 2: Concurrency Testing
- [ ] Test with 2, 4, 8 concurrent users
- [ ] Monitor GPU utilization during concurrent requests
- [ ] Identify queue behavior (latency increases?)

### Week 3: Load Testing
- [ ] Run 60s load test at various user levels
- [ ] Find your breaking point (OOM, timeout)
- [ ] Document max throughput

### Week 4: Metrics Visualization
- [ ] Set up Prometheus + Grafana (optional)
- [ ] Create dashboards for key metrics
- [ ] Monitor over extended periods

---

## Troubleshooting

### "Backend not running"
```bash
# Start backend
cd backend && python main.py
```

### "Module not found: prometheus_client"
```bash
cd backend
pip install -r requirements.txt
```

### "CUDA out of memory"
```bash
# Reduce concurrency
python run_tests.py benchmark --concurrent --workers 1
```

### "Voice file not found"
```bash
# Provide correct path
python run_tests.py benchmark --voice path/to/your/voice.wav
```

---

## Next Steps

1. **Run your first benchmark:**
   ```bash
   python run_tests.py benchmark --requests 10
   ```

2. **Explore the results** in `benchmark_results.json` and generated plots

3. **Check real-time metrics:**
   ```bash
   watch -n 2 'curl -s http://localhost:8000/metrics'
   ```

4. **Load test when ready:**
   ```bash
   python run_tests.py load --users 5 --headless --run-time 30s
   ```

---

## Documentation

- **Detailed Testing Guide:** `tests/README.md`
- **Code:** `tests/benchmark/benchmark.py`, `tests/load/locustfile.py`
- **Metrics:** `backend/metrics.py`

---

Ready to start? Run:

```bash
python run_tests.py benchmark --requests 10
```
