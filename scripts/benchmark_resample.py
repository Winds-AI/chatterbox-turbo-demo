import time
import json
import numpy as np
import torch
import torchaudio
import librosa
from pathlib import Path


def benchmark_resample(audio_path: str, target_sr: int = 16000, iterations: int = 3):
    results = {
        "audio_file": audio_path,
        "target_sample_rate": target_sr,
        "iterations": iterations,
        "cuda_available": torch.cuda.is_available(),
        "device_name": torch.cuda.get_device_name(0)
        if torch.cuda.is_available()
        else "N/A",
        "methods": {},
    }

    print(f"Loading audio: {audio_path}")
    waveform_librosa, orig_sr_librosa = librosa.load(audio_path, sr=None)
    waveform_torch, orig_sr_torch = torchaudio.load(audio_path)

    print(f"Original sample rate: {orig_sr_librosa} Hz")
    print(f"Target sample rate: {target_sr} Hz")
    print(f"CUDA available: {results['cuda_available']}")

    # Method 1: librosa (CPU resample + CPU->GPU transfer)
    times_librosa = []
    times_librosa_transfer = []
    for i in range(iterations):
        # Resample on CPU
        start = time.time()
        resampled = librosa.resample(
            waveform_librosa, orig_sr=orig_sr_librosa, target_sr=target_sr
        )
        resample_time = time.time() - start

        # Transfer to GPU
        torch.cuda.synchronize()
        start = time.time()
        resampled_gpu = torch.from_numpy(resampled).unsqueeze(0).cuda()
        torch.cuda.synchronize()
        transfer_time = time.time() - start

        total_time = resample_time + transfer_time
        times_librosa.append(total_time)
        times_librosa_transfer.append(transfer_time)
        print(
            f"  librosa iteration {i + 1}: {resample_time * 1000:.2f}ms resample + {transfer_time * 1000:.2f}ms transfer = {total_time * 1000:.2f}ms total"
        )

    results["methods"]["librosa"] = {
        "mean_ms": np.mean(times_librosa) * 1000,
        "std_ms": np.std(times_librosa) * 1000,
        "times_ms": [t * 1000 for t in times_librosa],
        "mean_transfer_ms": np.mean(times_librosa_transfer) * 1000,
    }

    # Method 2: torchaudio CPU (CPU resample + CPU->GPU transfer)
    times_torch_cpu = []
    times_torch_cpu_transfer = []
    resampler = torchaudio.transforms.Resample(orig_sr_torch, target_sr)
    for i in range(iterations):
        # Resample on CPU
        start = time.time()
        resampled = resampler(waveform_torch)
        resample_time = time.time() - start

        # Transfer to GPU
        torch.cuda.synchronize()
        start = time.time()
        resampled_gpu = resampled.cuda()
        torch.cuda.synchronize()
        transfer_time = time.time() - start

        total_time = resample_time + transfer_time
        times_torch_cpu.append(total_time)
        times_torch_cpu_transfer.append(transfer_time)
        print(
            f"  torchaudio CPU iteration {i + 1}: {resample_time * 1000:.2f}ms resample + {transfer_time * 1000:.2f}ms transfer = {total_time * 1000:.2f}ms total"
        )

    results["methods"]["torchaudio_cpu"] = {
        "mean_ms": np.mean(times_torch_cpu) * 1000,
        "std_ms": np.std(times_torch_cpu) * 1000,
        "times_ms": [t * 1000 for t in times_torch_cpu],
        "mean_transfer_ms": np.mean(times_torch_cpu_transfer) * 1000,
    }

    if torch.cuda.is_available():
        # Method 3: torchaudio GPU (CPU->GPU transfer + GPU resample)
        times_torch_gpu = []
        times_torch_gpu_transfer = []
        resampler_gpu = torchaudio.transforms.Resample(orig_sr_torch, target_sr).cuda()

        for i in range(iterations):
            # Transfer to GPU first
            torch.cuda.synchronize()
            start = time.time()
            waveform_gpu = waveform_torch.cuda()
            torch.cuda.synchronize()
            transfer_time = time.time() - start

            # Resample on GPU
            torch.cuda.synchronize()
            start = time.time()
            resampled = resampler_gpu(waveform_gpu)
            torch.cuda.synchronize()
            resample_time = time.time() - start

            total_time = transfer_time + resample_time
            times_torch_gpu.append(total_time)
            times_torch_gpu_transfer.append(transfer_time)
            print(
                f"  torchaudio GPU iteration {i + 1}: {transfer_time * 1000:.2f}ms transfer + {resample_time * 1000:.2f}ms resample = {total_time * 1000:.2f}ms total"
            )

        results["methods"]["torchaudio_gpu"] = {
            "mean_ms": np.mean(times_torch_gpu) * 1000,
            "std_ms": np.std(times_torch_gpu) * 1000,
            "times_ms": [t * 1000 for t in times_torch_gpu],
            "mean_transfer_ms": np.mean(times_torch_gpu_transfer) * 1000,
        }

    print("\nComparison (total end-to-end including GPU transfer):")
    print(
        f"  librosa:           {results['methods']['librosa']['mean_ms']:.2f}ms (transfer: {results['methods']['librosa']['mean_transfer_ms']:.2f}ms)"
    )
    print(
        f"  torchaudio CPU:    {results['methods']['torchaudio_cpu']['mean_ms']:.2f}ms (transfer: {results['methods']['torchaudio_cpu']['mean_transfer_ms']:.2f}ms)"
    )
    if "torchaudio_gpu" in results["methods"]:
        print(
            f"  torchaudio GPU:    {results['methods']['torchaudio_gpu']['mean_ms']:.2f}ms (transfer: {results['methods']['torchaudio_gpu']['mean_transfer_ms']:.2f}ms)"
        )

    output_path = Path("resample_benchmark_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    audio_path = "S:\\Random_stuff\\chatterbox\\reference.wav"
    target_sr = 16000
    iterations = 200

    benchmark_resample(audio_path, target_sr, iterations)
