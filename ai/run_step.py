"""Run a command, stream its output AND append it to a log file (portable `tee`).

    python ai/run_step.py build.log python -m pytest -v

Exit code is the command's exit code, so Jenkins still fails the stage.
"""
import subprocess
import sys

log_path, cmd = sys.argv[1], sys.argv[2:]
with open(log_path, "a", encoding="utf-8") as log:
    log.write(f"\n$ {' '.join(cmd)}\n")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    except FileNotFoundError:
        msg = f"ERROR: command not found: '{cmd[0]}' is not installed or not on PATH for this Jenkins agent\n"
        sys.stdout.write(msg)
        log.write(msg)
        sys.exit(127)
    for line in proc.stdout:
        sys.stdout.write(line)
        log.write(line)
    proc.wait()
sys.exit(proc.returncode)
