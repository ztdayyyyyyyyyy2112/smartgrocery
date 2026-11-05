# Load test results

Run `services/api/scripts/load_test.py` while the API is running. The probe
uses `/health` so it does not mutate orders or inventory. Record the output for
50, 100, and 200 requests here before release.

## Verified run — 2026-11-05

| Requests | Concurrency | Success | Errors | Throughput | p50/p95/p99 | Max |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 10 | 50 | 0 | 203.20 req/s | 27.80/97.22/136.63 ms | 136.63 ms |
| 100 | 20 | 100 | 0 | 251.27 req/s | 65.11/138.95/186.13 ms | 186.13 ms |
| 200 | 40 | 200 | 0 | 341.90 req/s | 99.27/196.84/217.17 ms | 219.18 ms |

Percentile column format: `p50/p95/p99`.

Target endpoint: `/health`. The probe was read-only and did not mutate orders or inventory.
