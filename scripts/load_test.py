#!/usr/bin/env python3
"""Generate sustained API traffic to push backend CPU above the HPA target.

Standard library only, so it runs anywhere Python 3 does.

  python3 scripts/load_test.py --url http://localhost --host deskflow.local --duration 180 --workers 64

Watch the autoscaler in another terminal:
  kubectl get hpa -n deskflow -w
"""
import argparse
import http.client
import random
import threading
import time
from collections import Counter
from urllib.parse import urlparse

PATHS = [
    "/api/tickets",
    "/api/tickets/stats",
    "/api/tickets?status=open",
    "/api/tickets?priority=urgent",
    "/api/activity",
    "/api/agents",
    "/api/tickets/1",
    "/api/tickets/999999",  # deliberate 404s so the error panels have data
]


def worker(target, host_header, deadline, counts, latencies, lock):
    conn = None
    while time.monotonic() < deadline:
        path = random.choice(PATHS)
        try:
            if conn is None:
                cls = http.client.HTTPSConnection if target.scheme == "https" else http.client.HTTPConnection
                conn = cls(target.hostname, target.port, timeout=10)
            start = time.monotonic()
            conn.request("GET", path, headers={"Host": host_header} if host_header else {})
            resp = conn.getresponse()
            resp.read()
            elapsed = time.monotonic() - start
            with lock:
                counts[resp.status] += 1
                latencies.append(elapsed)
        except Exception:  # noqa: BLE001 - count and reconnect
            with lock:
                counts["error"] += 1
            if conn is not None:
                conn.close()
            conn = None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost", help="base URL of the ingress or service")
    parser.add_argument("--host", default="deskflow.local", help="Host header to send (empty to skip)")
    parser.add_argument("--duration", type=int, default=180, help="seconds to run")
    parser.add_argument("--workers", type=int, default=64, help="concurrent connections")
    args = parser.parse_args()

    target = urlparse(args.url)
    counts, latencies, lock = Counter(), [], threading.Lock()
    deadline = time.monotonic() + args.duration
    threads = [
        threading.Thread(target=worker, args=(target, args.host, deadline, counts, latencies, lock), daemon=True)
        for _ in range(args.workers)
    ]
    print(f"Load test: {args.workers} workers for {args.duration}s against {args.url} (Host: {args.host})")
    for t in threads:
        t.start()

    started = time.monotonic()
    last_total = 0
    while any(t.is_alive() for t in threads):
        time.sleep(10)
        with lock:
            total = sum(counts.values())
        print(f"  t={time.monotonic() - started:5.0f}s  requests={total:7d}  rate={(total - last_total) / 10:7.1f}/s")
        last_total = total

    lat = sorted(latencies)
    total = sum(counts.values())
    print("\nSummary")
    print(f"  total requests : {total}")
    print(f"  avg rate       : {total / args.duration:.1f} req/s")
    if lat:
        print(f"  latency p50    : {lat[len(lat) // 2] * 1000:.0f} ms")
        print(f"  latency p95    : {lat[int(len(lat) * 0.95)] * 1000:.0f} ms")
    print(f"  status codes   : {dict(counts)}")


if __name__ == "__main__":
    main()
