"""AI build-failure analyser.

Reads a CI log (file path or stdin), keeps the useful tail, and asks the local
LLM for a root cause + fix. Used by the Jenkinsfile's post { failure } block and
by bench/log_analysis_bench.py.

    python ai/analyze_log.py build.log
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ollama_client import AI_ENABLED, OllamaError, ask  # noqa: E402

MAX_LINES = 120  # small local models have small context windows; the tail holds the error

SYSTEM = (
    "You are a senior DevOps engineer reading a failed CI build log for a Python "
    "Flask project. Be precise and brief. Only state what the log supports."
)

PROMPT = """Here is the end of a failed CI log:

----- LOG START -----
{log}
----- LOG END -----

Reply in exactly this format, max 8 lines total:
ROOT CAUSE: <one sentence>
LOCATION: <file and line if visible, else 'unknown'>
FIX: <concrete change to make>
CONFIDENCE: <high/medium/low>
"""


def trim_log(log_text, max_lines=MAX_LINES):
    lines = log_text.splitlines()
    return "\n".join(lines[-max_lines:]), len(lines)


def analyze(log_text):
    trimmed, total_lines = trim_log(log_text)
    result = ask(PROMPT.format(log=trimmed), system=SYSTEM)
    result["log_lines"] = total_lines
    result["answer_lines"] = len([ln for ln in result["text"].splitlines() if ln.strip()])
    return result


def main():
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8", errors="ignore") as f:
            log_text = f.read()
    else:
        log_text = sys.stdin.read()

    if not AI_ENABLED:
        print("[AI] AI_ASSIST=0 - no AI analysis. Read the log above to find the problem.")
        return 0
    if not log_text.strip():
        print("[AI] Empty log, nothing to analyse.")
        return 0

    print("=" * 64)
    print("  AI BUILD FAILURE ANALYSIS (local LLM via Ollama)")
    print("=" * 64)
    try:
        r = analyze(log_text)
    except OllamaError as e:
        print(f"[AI] Skipped: {e}")
        return 0  # never let the AI step itself break the pipeline
    print(r["text"])
    print("-" * 64)
    print(
        f"model={r['model']}  time={r['latency_s']}s  "
        f"log={r['log_lines']} lines -> summary={r['answer_lines']} lines"
    )
    print("NOTE: AI suggestion - verify before applying.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
