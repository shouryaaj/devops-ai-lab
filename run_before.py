"""PHASE 1 - BEFORE AI. Measures the plain pipeline. Ollama is NOT used.

    python run_before.py

1. Manual diagnosis of 6 failed builds (interactive, stopwatch) - ideally a classmate
2. Regex-only secret scan on 12 test diffs
3. Naive Dockerfile: size, build/rebuild time, start-up, root user
Then writes results/SUMMARY.md with the "Before" column filled in.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, AI_ASSIST="0")


def run(*args, optional=False):
    print(f"\n######## {' '.join(args)} ########", flush=True)
    rc = subprocess.run([sys.executable, *args], cwd=ROOT, env=env).returncode
    if rc and not optional:
        sys.exit(f"{args[0]} failed (exit {rc})")
    if rc:
        print(f"{args[0]} skipped (is Docker Desktop running?)")


if "--skip-manual" not in sys.argv:
    run("bench/manual_timer.py")
run("bench/secret_scan_bench.py", "--before")
run("bench/docker_bench.py", "naive", optional=True)
run("bench/summarize.py")
print("\nBEFORE phase done. Now switch AI on and run:  python run_after.py")
