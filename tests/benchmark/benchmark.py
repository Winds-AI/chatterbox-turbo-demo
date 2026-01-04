import requests
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from tabulate import tabulate

console = Console()

CONFIG = {
    "base_url": "http://localhost:8000",
    "num_requests": 10,
    "concurrent": False,
    "num_workers": 4,
    "output_file": "benchmark_results.json",
    "generate_plots": False,
    "voice_path": "../audio/reference.wav",
    "voice_exaggeration": 0.5,
}


@dataclass
class BenchmarkResult:
    endpoint: str
    status_code: int
    latency_ms: float
    text_length: int
    audio_size_bytes: int
    generation_time_ms: float
    gpu_memory_mb: float
    error: Optional[str] = None


class BenchmarkRunner:
    def __init__(self, base_url: str = ""):
        self.base_url = base_url if base_url else CONFIG["base_url"]
        self.voice_loaded = False
        self.results: List[BenchmarkResult] = []

    def load_voice(self, voice_path: str = "", exaggeration: float = 0.0):
        voice_path = voice_path if voice_path else CONFIG["voice_path"]
        exaggeration = (
            exaggeration if exaggeration != 0.0 else CONFIG["voice_exaggeration"]
        )

        console.print(f"[cyan]Loading voice from {voice_path}...[/cyan]")
        response = requests.post(
            f"{self.base_url}/load_voice",
            json={"voice_path": voice_path, "exaggeration": exaggeration},
        )
        if response.status_code == 200:
            self.voice_loaded = True
            console.print("[green]Voice loaded successfully![/green]")
            return True
        else:
            console.print(f"[red]Failed to load voice: {response.text}[/red]")
            return False

    def generate_speech(self, text: str) -> BenchmarkResult:
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/generate", json={"text": text}, stream=True
            )
            end_time = time.time()

            latency_ms = (end_time - start_time) * 1000

            audio_size = 0
            generation_time = 0

            if response.status_code == 200:
                audio_size = len(response.content)
                generation_time = (
                    float(response.headers.get("X-Generation-Time", 0)) * 1000
                )

                result = BenchmarkResult(
                    endpoint="/generate",
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    text_length=len(text),
                    audio_size_bytes=audio_size,
                    generation_time_ms=generation_time,
                    gpu_memory_mb=0,
                )

                self.results.append(result)
                return result
            else:
                console.print(
                    f"[red]Error: {response.status_code} - {response.text}[/red]"
                )
                return BenchmarkResult(
                    endpoint="/generate",
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    text_length=len(text),
                    audio_size_bytes=0,
                    generation_time_ms=0,
                    gpu_memory_mb=0,
                    error=response.text,
                )

        except Exception as e:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            console.print(f"[red]Exception: {str(e)}[/red]")
            return BenchmarkResult(
                endpoint="/generate",
                status_code=0,
                latency_ms=latency_ms,
                text_length=len(text),
                audio_size_bytes=0,
                generation_time_ms=0,
                gpu_memory_mb=0,
                error=str(e),
            )

    def run_benchmark(
        self, num_requests: int = 0, concurrent: bool = False, num_workers: int = 0
    ):
        num_requests = num_requests if num_requests > 0 else CONFIG["num_requests"]
        concurrent = concurrent
        num_workers = num_workers if num_workers > 0 else CONFIG["num_workers"]

        console.print(
            f"[cyan]Running benchmark: {num_requests} requests, concurrent={concurrent}, workers={num_workers}[/cyan]"
        )

        SAMPLE_TEXTS = [
            "Hello, this is Chatterbox Turbo speaking.",
            "The quick brown fox jumps over the lazy dog.",
            "Text-to-speech technology has advanced significantly in recent years.",
            "Machine learning models can generate realistic human-like voices.",
            "This is a test of emergency broadcast system.",
            "Welcome to the future of voice synthesis.",
            "Chatterbox Turbo delivers high-quality speech generation.",
            "Optimizing performance requires careful measurement and analysis.",
            "Concurrent requests can reveal bottlenecks in the system.",
            "GPU utilization is crucial for real-time inference.",
        ]

        if not self.voice_loaded:
            self.load_voice()

        self.results = []

        if concurrent:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                with Progress(
                    SpinnerColumn(),
                    *Progress.get_default_columns(),
                    TimeElapsedColumn(),
                    console=console,
                ) as progress:
                    task = progress.add_task(
                        "[cyan]Generating requests...", total=num_requests
                    )

                    futures = []
                    for i in range(num_requests):
                        text = SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)]
                        future = executor.submit(self.generate_speech, text)
                        futures.append(future)

                    for future in as_completed(futures):
                        future.result()
                        progress.update(task, advance=1)
        else:
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "[cyan]Generating requests...", total=num_requests
                )
                for i in range(num_requests):
                    text = SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)]
                    self.generate_speech(text)
                    progress.update(task, advance=1)

        return self.results

    def calculate_stats(self) -> Dict:
        if not self.results:
            return {}

        df = pd.DataFrame([asdict(r) for r in self.results])

        numeric_cols = ["latency_ms", "generation_time_ms", "audio_size_bytes"]
        stats = {}

        for col in numeric_cols:
            if col in df.columns:
                stats[col] = {
                    "mean": df[col].mean(),
                    "median": df[col].median(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "std": df[col].std(),
                    "p95": df[col].quantile(0.95),
                    "p99": df[col].quantile(0.99),
                }

        error_rate = (
            (df["status_code"] != 200).sum() / len(df)
            if "status_code" in df.columns
            else 0
        )

        return {
            "throughput_requests_per_sec": len(df) / df["latency_ms"].sum() * 1000
            if "latency_ms" in df.columns
            else 0,
            "error_rate": error_rate,
            "total_requests": len(df),
            "successful_requests": (df["status_code"] == 200).sum()
            if "status_code" in df.columns
            else 0,
            "stats": stats,
        }

    def print_results(self):
        if not self.results:
            console.print("[yellow]No results to display[/yellow]")
            return

        stats = self.calculate_stats()

        console.print("\n[bold green]Benchmark Results[/bold green]\n")

        table = Table(title="Summary")
        table.add_column("Metric", justify="left", style="cyan")
        table.add_column("Value", justify="right", style="green")

        table.add_row("Total Requests", str(stats.get("total_requests", 0)))
        table.add_row("Successful Requests", str(stats.get("successful_requests", 0)))
        table.add_row("Error Rate", f"{stats.get('error_rate', 0):.2%}")
        table.add_row(
            "Throughput", f"{stats.get('throughput_requests_per_sec', 0):.2f} req/s"
        )

        console.print(table)

        if "stats" in stats:
            for metric, values in stats["stats"].items():
                console.print(f"\n[bold cyan]{metric}[/bold cyan]")
                table = Table()
                table.add_column("Statistic", style="cyan")
                table.add_column("Value", style="green")

                for stat_name, stat_value in values.items():
                    table.add_row(stat_name, f"{stat_value:.2f}")

                console.print(table)

    def save_results(self, output_path: str = ""):
        output_path = output_path if output_path else CONFIG["output_file"]
        stats = self.calculate_stats()
        data = {"stats": stats, "results": [asdict(r) for r in self.results]}

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        console.print(f"[green]Results saved to {output_path}[/green]")

    def plot_latency_distribution(self, output_path: str = "latency_distribution.png"):
        if not self.results:
            console.print("[yellow]No results to plot[/yellow]")
            return

        df = pd.DataFrame([asdict(r) for r in self.results])

        if "latency_ms" not in df.columns:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("Performance Analysis", fontsize=16)

        axes[0, 0].hist(df["latency_ms"], bins=30, edgecolor="black", alpha=0.7)
        axes[0, 0].set_xlabel("Latency (ms)")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].set_title("Latency Distribution")
        axes[0, 0].grid(True, alpha=0.3)

        if "generation_time_ms" in df.columns:
            axes[0, 1].hist(
                df["generation_time_ms"],
                bins=30,
                edgecolor="black",
                alpha=0.7,
                color="orange",
            )
            axes[0, 1].set_xlabel("Generation Time (ms)")
            axes[0, 1].set_ylabel("Frequency")
            axes[0, 1].set_title("Generation Time Distribution")
            axes[0, 1].grid(True, alpha=0.3)

        axes[1, 0].plot(
            range(len(df)), df["latency_ms"], marker="o", linestyle="-", alpha=0.7
        )
        axes[1, 0].set_xlabel("Request Number")
        axes[1, 0].set_ylabel("Latency (ms)")
        axes[1, 0].set_title("Latency Over Time")
        axes[1, 0].grid(True, alpha=0.3)

        if "audio_size_bytes" in df.columns:
            axes[1, 1].scatter(df["text_length"], df["latency_ms"], alpha=0.6)
            axes[1, 1].set_xlabel("Text Length (chars)")
            axes[1, 1].set_ylabel("Latency (ms)")
            axes[1, 1].set_title("Latency vs Text Length")
            axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        console.print(f"[green]Plots saved to {output_path}[/green]")
        plt.close()


def run_concurrent_test(base_url: str, num_requests: int, max_workers: int):
    console.print(
        f"[cyan]Running concurrent test: {num_requests} requests, {max_workers} workers[/cyan]"
    )

    runner = BenchmarkRunner(base_url)
    runner.load_voice()

    SAMPLE_TEXTS = [
        "Hello, this is Chatterbox Turbo speaking.",
        "The quick brown fox jumps over the lazy dog.",
        "Text-to-speech technology has advanced significantly in recent years.",
    ]

    def run_single_request(text: str) -> BenchmarkResult:
        return runner.generate_speech(text)

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(num_requests):
            text = SAMPLE_TEXTS[i % len(SAMPLE_TEXTS)]
            future = executor.submit(run_single_request, text)
            futures.append(future)

        results = [future.result() for future in as_completed(futures)]

    end_time = time.time()

    console.print(
        f"\n[green]Concurrent test completed in {end_time - start_time:.2f}s[/green]"
    )
    console.print(
        f"[cyan]Average latency: {np.mean([r.latency_ms for r in results]):.2f}ms[/cyan]"
    )
    console.print(
        f"[cyan]Throughput: {num_requests / (end_time - start_time):.2f} requests/second[/cyan]"
    )

    return runner


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run TTS performance benchmarks")
    parser.add_argument("--url", default=None, help="API base URL")
    parser.add_argument("--requests", type=int, default=None, help="Number of requests")
    parser.add_argument(
        "--concurrent", action="store_true", help="Run concurrent requests"
    )
    parser.add_argument(
        "--workers", type=int, default=None, help="Number of concurrent workers"
    )
    parser.add_argument("--output", default=None, help="Output file for results")
    parser.add_argument(
        "--plot", action="store_true", help="Generate latency distribution plots"
    )
    parser.add_argument("--voice", default=None, help="Path to voice file")

    args = parser.parse_args()

    if args.url:
        CONFIG["base_url"] = args.url
    if args.requests:
        CONFIG["num_requests"] = args.requests
    if args.workers:
        CONFIG["num_workers"] = args.workers
    if args.output:
        CONFIG["output_file"] = args.output
    if args.voice:
        CONFIG["voice_path"] = args.voice
    if args.concurrent:
        CONFIG["concurrent"] = True
    CONFIG["generate_plots"] = args.plot

    runner = BenchmarkRunner()
    runner.load_voice()
    runner.run_benchmark()
    runner.print_results()
    runner.save_results()

    if CONFIG["generate_plots"]:
        runner.plot_latency_distribution()
