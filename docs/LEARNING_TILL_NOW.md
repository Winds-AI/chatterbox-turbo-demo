[Topic: Resampling Performance - CPU vs. GPU]
Librosa is CPU based, works with Numpy arrays. Chatterbox uses librosa internally to convert input audio's sampling rate to 16 kHz. Output Sampling rate is 24kHz. It will be faster if you convert Sampling rate on GPU. When using librosa (ext library) for resampling, because it uses CPU for resampling, so in my testing 44100 Hz -> 16000 Hz took around 39-49ms. Same results for torchaudio on CPU.

But when using GPU, the first resampling request takes warmup for CUDA kernels to compile so it took 612 ms but after that each run took 7-8 ms only. So GPU is faster if you have spare VRAM available and confirming that it will not interfere with inference if we are running both. This testing did not account for the additional roundtrip it takes for librosa from CPU to GPU because voiceencoder is on GPU so we need to transfer file and we don't have to if we used GPU directly for resampling.

So I did another test with accounting for this overhead but for 3 runs CPU was faster because of GPU warmup. Latency decreases when you are running 100 resamplings together then there is some minor difference but generally CPU is better. Chatterbox turbo's default was right, I got to learn a lot though. GPU is faster in isolation but slower in System context.


[Topic: Audio Pipeline & Embeddings]
After resampling it trims the silence. Now i got another question: resampling then trimming or trimming then resampling?
I'll explore this when i get time.

Now utterance embeddings & Single consolidated Speaker embedding. In utterance we provide small broken down samples [which] are processed to produce an L2 normalized embedding here "as_spk" is false.

For Single Consolidated Speaker Embedding it represents the overall voice char[acteristics] of a Speaker. [It] combines multiple utterance embeddings and renormalizes the result. utt_to_spk_embed static method in voicemcoder is specifically designed for so that it takes array of L2 normalized utterance embeddings, computes mean, normalize mean to Smooth out variations happening in Short utterances. as_spk is true so it automatically calls utt_to_spk_emb.


[Topic: Metrics using Prometheus]
Prometheus is an open-source monitoring and alerting toolkit designed for tracking metrics.

Instead of just logging "took 500ms", Prometheus stores:
- Timestamp: 2026-01-03 10:15:30
- Metric: tts_request_duration_seconds
- Value: 0.5
- Labels: voice_id="voice1", status="success"

You get a time series that you can query: "show me average latency in the last 5 minutes"
2. Metric Types
- Counter: Only goes up (e.g., total requests processed)
- Gauge: Goes up/down (e.g., current GPU memory usage)
- Histogram: Distribution of values (e.g., latency buckets: <100ms, <500ms, <1s, etc.)
- Summary: Similar to histogram but client-side quantiles (e.g., request latency percentiles)
Reference: https://prometheus.io/docs/concepts/metric_types

Example for latency metric:
- p50 = 200ms: Half of requests complete in ≤200ms
- p95 = 500ms: 95% of requests complete in ≤500ms
- p99 = 1.2s: 99% complete in ≤1.2s (the worst 1% take longer)

3. Architecture
Your App → /metrics endpoint → Prometheus Server → Grafana Dashboard
(exposes data) (scrapes every 15s) (visualizes)

4. Prometheus Client vs Server
- Client: Library in your app that creates metrics and exposes /metrics endpoint
- Server: Separate service that pulls (scrapes) metrics from your app every 15s
- Why separate: Monitoring system shouldn't go down if your app fails

5. Global Registry vs CollectorRegistry
- Global Registry: Default registry that collects ALL metrics from your app automatically
- CollectorRegistry: Custom registry you create for isolation and control
- Why custom: Keeps your metrics separate, easier testing, prevents conflicts with other libraries

Prometheus Best Practices: https://prometheus.io/docs/practices/{one_of_below}
- naming
- consoles
- instrumentation
- histograms
- alerting
- rules
- pushing
- remote_write