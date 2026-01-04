"""
Quick test runner script for Chatterbox Turbo testing suite.
Run all tests or specific test types.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

CONFIG = {
    "base_url": "http://localhost:8000",
    "benchmark_requests": 10,
    "benchmark_concurrent": False,
    "benchmark_workers": 4,
    "load_test_users": 10,
    "load_test_spawn_rate": 2,
    "load_test_run_time": "60s",
    "load_test_headless": False,
    "voice_path": "../audio/reference.wav",
}


def check_backend_running(base_url: str = ""):
    """Check if backend is running."""
    import requests

    base_url = base_url if base_url else CONFIG["base_url"]

    try:
        response = requests.get(f"{base_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def run_quick_benchmark(args):
    """Run a quick baseline benchmark."""
    console.print(Panel.fit("[bold cyan]Quick Benchmark Test[/bold cyan]"))

    if not check_backend_running():
        console.print("[red]Error: Backend is not running![/red]")
        console.print("Start backend with: cd backend && python main.py")
        return False

    requests_count = getattr(args, "requests", CONFIG["benchmark_requests"])
    voice_path = getattr(args, "voice", CONFIG["voice_path"])

    cmd = [
        "python",
        "benchmark/benchmark.py",
        "--requests",
        str(requests_count),
        "--voice",
        voice_path,
    ]

    if args.concurrent:
        workers = getattr(args, "workers", CONFIG["benchmark_workers"])
        cmd.extend(["--concurrent", "--workers", str(workers)])

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd, cwd="tests")
    return result.returncode == 0


def run_load_test(args):
    """Run Locust load test."""
    console.print(Panel.fit("[bold cyan]Load Test (Locust)[/bold cyan]"))

    if not check_backend_running():
        console.print("[red]Error: Backend is not running![/red]")
        return False

    url = getattr(args, "url", CONFIG["base_url"])
    users = getattr(args, "users", CONFIG["load_test_users"])
    spawn_rate = getattr(args, "spawn_rate", CONFIG["load_test_spawn_rate"])
    run_time = getattr(args, "run_time", CONFIG["load_test_run_time"])
    headless = getattr(args, "headless", CONFIG["load_test_headless"])

    if headless:
        cmd = [
            "locust",
            "-f",
            "load/locustfile.py",
            "--host",
            url,
            "--headless",
            "--users",
            str(users),
            "--spawn-rate",
            str(spawn_rate),
            "--run-time",
            run_time,
        ]
    else:
        cmd = ["locust", "-f", "load/locustfile.py", "--host", url]
        console.print("[yellow]Opening Locust web UI at http://localhost:8089[/yellow]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")

    console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
    result = subprocess.run(cmd, cwd="tests")
    return result.returncode == 0


def show_metrics(args):
    """Show current Prometheus metrics."""
    console.print(Panel.fit("[bold cyan]Prometheus Metrics[/bold cyan]"))

    import requests

    url = getattr(args, "url", CONFIG["base_url"])

    try:
        response = requests.get(f"{url}/metrics")
        if response.status_code == 200:
            metrics = response.text
            key_metrics = [
                line
                for line in metrics.split("\n")
                if line and not line.startswith("#")
            ]

            console.print("\n[bold green]Key Metrics:[/bold green]\n")
            for metric in key_metrics[:20]:
                console.print(metric)

            if len(key_metrics) > 20:
                console.print(f"\n[dim]... and {len(key_metrics) - 20} more[/dim]")
        else:
            console.print(f"[red]Failed to fetch metrics: {response.status_code}[/red]")
    except Exception as e:
        console.print(f"[red]Error fetching metrics: {e}[/red]")


def run_full_suite(args):
    """Run complete testing suite."""
    console.print(Panel.fit("[bold yellow]Full Testing Suite[/bold yellow]"))

    if not check_backend_running():
        console.print("[red]Error: Backend is not running![/red]")
        return False

    url = getattr(args, "url", CONFIG["base_url"])
    requests_count = getattr(args, "requests", CONFIG["benchmark_requests"])
    voice_path = getattr(args, "voice", CONFIG["voice_path"])

    console.print("\n[bold cyan]Phase 1: Quick Benchmark[/bold cyan]")
    run_quick_benchmark(args)

    console.print("\n[bold cyan]Phase 2: Show Metrics[/bold cyan]")
    show_metrics(args)

    console.print("\n[bold cyan]Phase 3: Load Test (30s)[/bold cyan]")
    subprocess.run(
        [
            "locust",
            "-f",
            "load/locustfile.py",
            "--host",
            url,
            "--headless",
            "--users",
            "5",
            "--spawn-rate",
            "1",
            "--run-time",
            "30s",
        ],
        cwd="tests",
    )

    console.print("\n[bold green]Full suite completed![/bold green]")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Chatterbox Turbo Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick benchmark (10 requests)
  python run_tests.py benchmark --requests 10

  # Concurrent benchmark (50 requests, 4 workers)
  python run_tests.py benchmark --concurrent --requests 50 --workers 4

  # Load test with web UI
  python run_tests.py load --users 10

  # Headless load test (60s)
  python run_tests.py load --headless --users 10 --spawn-rate 2 --run-time 60s

  # Show current metrics
  python run_tests.py metrics

  # Run full suite
  python run_tests.py suite
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Test type")

    # Benchmark arguments
    benchmark_parser = subparsers.add_parser("benchmark", help="Run benchmark tests")
    benchmark_parser.add_argument(
        "--requests",
        type=int,
        default=CONFIG["benchmark_requests"],
        help="Number of requests",
    )
    benchmark_parser.add_argument(
        "--concurrent", action="store_true", help="Run concurrent requests"
    )
    benchmark_parser.add_argument(
        "--workers",
        type=int,
        default=CONFIG["benchmark_workers"],
        help="Number of workers",
    )
    benchmark_parser.add_argument(
        "--voice", default=CONFIG["voice_path"], help="Voice file path"
    )

    # Load test arguments
    load_parser = subparsers.add_parser("load", help="Run Locust load tests")
    load_parser.add_argument(
        "--headless", action="store_true", help="Run without web UI"
    )
    load_parser.add_argument(
        "--users", type=int, default=CONFIG["load_test_users"], help="Number of users"
    )
    load_parser.add_argument(
        "--spawn-rate",
        type=int,
        default=CONFIG["load_test_spawn_rate"],
        help="Users per second",
    )
    load_parser.add_argument(
        "--run-time", default=CONFIG["load_test_run_time"], help="Test duration"
    )
    load_parser.add_argument("--url", default=CONFIG["base_url"], help="API URL")

    # Metrics arguments
    metrics_parser = subparsers.add_parser("metrics", help="Show Prometheus metrics")
    metrics_parser.add_argument("--url", default=CONFIG["base_url"], help="API URL")

    # Suite arguments
    suite_parser = subparsers.add_parser("suite", help="Run full test suite")
    suite_parser.add_argument(
        "--requests",
        type=int,
        default=CONFIG["benchmark_requests"],
        help="Benchmark requests",
    )
    suite_parser.add_argument(
        "--voice", default=CONFIG["voice_path"], help="Voice file path"
    )
    suite_parser.add_argument("--url", default=CONFIG["base_url"], help="API URL")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    command_handlers = {
        "benchmark": run_quick_benchmark,
        "load": run_load_test,
        "metrics": show_metrics,
        "suite": run_full_suite,
    }

    return 0 if command_handlers[args.command](args) else 1


if __name__ == "__main__":
    sys.exit(main())
