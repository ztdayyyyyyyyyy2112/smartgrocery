"""Small, safe HTTP load probe for release evidence.

Usage: python scripts/load_test.py --requests 50 --concurrency 10
"""

import argparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import httpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/health")
    parser.add_argument("--requests", type=int, choices=(50, 100, 200), default=50)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    def probe(_: int) -> tuple[int, float]:
        started = time.perf_counter()
        try:
            response = httpx.get(args.url, timeout=10)
            return response.status_code, (time.perf_counter() - started) * 1000
        except httpx.HTTPError:
            return 0, (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        results = list(pool.map(probe, range(args.requests)))
    elapsed = time.perf_counter() - started
    statuses = [status for status, _ in results]
    latencies = [latency for _, latency in results]
    successes = sum(status == 200 for status in statuses)
    print(f"requests={args.requests} concurrency={args.concurrency} successes={successes} errors={args.requests - successes}")
    print(f"elapsed_seconds={elapsed:.3f} throughput_rps={args.requests / elapsed:.2f}")
    ordered = sorted(latencies)
    percentile = lambda ratio: ordered[min(len(ordered) - 1, int(len(ordered) * ratio))]
    print(f"latency_ms p50={statistics.median(latencies):.2f} p95={percentile(0.95):.2f} p99={percentile(0.99):.2f} max={max(latencies):.2f}")
    if successes != args.requests:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
