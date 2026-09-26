"""Docker image: naive Dockerfile (before AI) vs AI-optimised Dockerfile (after AI).

    python bench/docker_bench.py naive      # BEFORE AI  -> results/before/docker.csv
    python bench/docker_bench.py ai         # AFTER AI   -> results/after/docker.csv
    python bench/docker_bench.py optimized  # reviewed fallback, also saved as "after"

Measures image size, layers, cold build time, rebuild time after a code change,
container start-up time, and whether it runs as root.
"""
import csv
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sh(cmd, check=True):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=check)


def timed_build(dockerfile, tag, no_cache):
    cmd = ["docker", "build", "-q", "-f", dockerfile, "-t", tag, "."]
    if no_cache:
        cmd.insert(2, "--no-cache")
    t = time.perf_counter()
    r = sh(cmd, check=False)
    if r.returncode != 0:
        raise SystemExit(f"Build of {dockerfile} failed:\n{r.stderr[-2000:]}")
    return round(time.perf_counter() - t, 1)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def startup_seconds(tag):
    port = free_port()
    cid = sh(["docker", "run", "-d", "--rm", "-p", f"{port}:5000", tag]).stdout.strip()
    t = time.perf_counter()
    try:
        while time.perf_counter() - t < 60:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
                return round(time.perf_counter() - t, 2)
            except Exception:
                time.sleep(0.1)
        return None
    finally:
        sh(["docker", "stop", cid], check=False)


def bench(variant):
    dockerfile = f"Dockerfile.{variant}"
    if not os.path.exists(os.path.join(ROOT, dockerfile)):
        raise SystemExit(f"{dockerfile} not found")
    tag = f"devops-ai-lab:{variant}"

    # Pre-pull base images so network speed doesn't distort build times
    for base in re.findall(r"(?im)^FROM\s+(\S+)", open(os.path.join(ROOT, dockerfile)).read()):
        if base.lower() != "scratch" and not base.startswith("$"):
            sh(["docker", "pull", "-q", base], check=False)

    print(f"[{variant}] cold build (no cache) ...", flush=True)
    cold = timed_build(dockerfile, tag, no_cache=True)

    print(f"[{variant}] rebuild after editing app.py ...", flush=True)
    app = os.path.join(ROOT, "app.py")
    original = open(app, encoding="utf-8").read()
    try:
        with open(app, "a", encoding="utf-8") as f:
            f.write(f"\n# cache-bust {time.time()}\n")
        warm = timed_build(dockerfile, tag, no_cache=False)
    finally:
        with open(app, "w", encoding="utf-8") as f:
            f.write(original)
    timed_build(dockerfile, tag, no_cache=False)  # rebuild clean copy for size/startup

    size_mb = round(int(sh(["docker", "image", "inspect", "-f", "{{.Size}}", tag]).stdout) / 1e6, 1)
    layers = len(sh(["docker", "history", "-q", tag]).stdout.split())
    user = sh(["docker", "image", "inspect", "-f", "{{.Config.User}}", tag]).stdout.strip() or "root"
    print(f"[{variant}] start-up time ...", flush=True)
    start = startup_seconds(tag)

    return {"variant": variant, "image_mb": size_mb, "layers": layers, "cold_build_s": cold,
            "rebuild_after_code_change_s": warm, "startup_s": start, "runs_as": user}


def main():
    variants = sys.argv[1:] or ["naive"]
    for v in variants:
        row = bench(v)
        phase = "before" if v == "naive" else "after"
        out_dir = os.path.join(ROOT, "results", phase)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "docker.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=row.keys())
            w.writeheader()
            w.writerow(row)
        print("  ".join(f"{k}={val}" for k, val in row.items()))
        print(f"Saved results/{phase}/docker.csv")


if __name__ == "__main__":
    main()
