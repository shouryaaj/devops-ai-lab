"""PHASE 2 - AFTER AI. Same measurements with the local LLM (Ollama) switched on.

    python run_after.py

1. LLM optimises Dockerfile.naive -> Dockerfile.ai
2. Regex + LLM secret scan on the same 12 diffs
3. LLM diagnoses the same 6 failed builds
4. Dockerfile.ai: size, build/rebuild time, start-up, user
Then writes results/SUMMARY.md with Before vs After side by side.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
env = dict(os.environ, AI_ASSIST="1")


def run(*args):
    print(f"\n######## {' '.join(args)} ########", flush=True)
    return subprocess.run([sys.executable, *args], cwd=ROOT, env=env).returncode


for step in (["ai/optimize_dockerfile.py"], ["bench/secret_scan_bench.py"], ["bench/log_analysis_bench.py"]):
    if run(*step):
        sys.exit(f"{step[0]} failed - is Ollama running and OLLAMA_MODEL set to a model from `ollama list`?")

if run("bench/docker_bench.py", "ai"):
    print("\nDockerfile.ai did NOT build. That's a real finding - mention it in the report.")
    print("Measuring the reviewed Dockerfile.optimized instead ...")
    if run("bench/docker_bench.py", "optimized"):
        print("Docker comparison skipped (is Docker Desktop running?)")
run("bench/summarize.py")
print("\nAFTER phase done. Open results/SUMMARY.md and results/after/log_analysis_answers.md")
