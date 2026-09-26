"""Minimal Ollama client using only the Python standard library (no pip installs).

Config via environment variables:
  OLLAMA_URL    default http://localhost:11434
                (use http://host.docker.internal:11434 if Jenkins runs inside Docker)
  OLLAMA_MODEL  default llama3.2  -- set this to a model shown by `ollama list`
  AI_ASSIST     1 (default) = AI on,  0 = AI off ("before AI" mode)
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

# AI_ASSIST=0 turns every AI step off -> the "before AI" pipeline
AI_ENABLED = os.environ.get("AI_ASSIST", "1").strip().lower() not in ("0", "false", "no", "off")

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")


class OllamaError(RuntimeError):
    pass


def ask(prompt, system=None, temperature=0.1, timeout=600):
    """Send one prompt to Ollama. Returns dict with text, latency and token stats."""
    body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if system:
        body["system"] = system
    req = urllib.request.Request(
        OLLAMA_URL + "/api/generate",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as e:
        raise OllamaError(f"Ollama returned HTTP {e.code}: {e.read().decode(errors='ignore')}") from e
    except urllib.error.URLError as e:
        raise OllamaError(
            f"Cannot reach Ollama at {OLLAMA_URL} ({e.reason}). Is `ollama serve` running?"
        ) from e
    latency = time.perf_counter() - start

    eval_count = data.get("eval_count") or 0
    eval_ns = data.get("eval_duration") or 0
    return {
        "text": data.get("response", "").strip(),
        "latency_s": round(latency, 2),
        "output_tokens": eval_count,
        "tokens_per_s": round(eval_count / (eval_ns / 1e9), 1) if eval_ns else None,
        "model": OLLAMA_MODEL,
    }


def extract_code_block(text):
    """Return the first fenced code block in text, or the text itself if none."""
    m = re.search(r"```[a-zA-Z]*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip() + "\n"
