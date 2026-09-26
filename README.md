# DevOps LT-I: AI-assisted CI pipeline with a local LLM (Ollama)

A Flask app with a Jenkins CI pipeline where a **local LLM running in Ollama** helps at three stages:

| Stage | Syllabus | Without AI (before) | With AI (after) |
|---|---|---|---|
| Code / commit | Module 2, Git | Regex secret scan, hand-written commit messages | LLM secret check + auto Conventional Commit message (git hooks) |
| Build failure | Module 3, Jenkins | Developer scrolls through the console log | `post { failure }` stage: LLM reads `build.log` and prints root cause + fix |
| Container | Module 1, build/deploy | Naive `Dockerfile.naive` | LLM-optimised `Dockerfile.ai` |

Every before/after number is **measured on your laptop** by the scripts in `bench/`.

---

## 0. One-time setup

```bash
ollama list                     # pick a model name from here
ollama serve                    # skip if the Ollama app is already running
pip install -r requirements-dev.txt   # flask + pytest; the AI scripts need nothing extra
```

Tell the scripts which model to use (use the exact name from `ollama list`):

- macOS / Linux: `export OLLAMA_MODEL=llama3.2`
- Windows PowerShell: `$env:OLLAMA_MODEL="llama3.2"`
- Windows CMD: `set OLLAMA_MODEL=llama3.2`

Also edit `OLLAMA_MODEL` in the `Jenkinsfile`.

Quick check: `python -m pytest -q` should print `7 passed`.

## 1. Collect the numbers: BEFORE first, then AFTER

One switch controls the AI everywhere: `AI_ASSIST=0` (off) or `1` (on). The run scripts set it for you.

### Phase 1: BEFORE AI (Ollama not needed)

```bash
python run_before.py
```

1. **Manual diagnosis**: 6 failed build logs appear in random order and a stopwatch times how long it takes to find each root cause. Ideally a classmate does this without reading `bench/scenarios.py`. You planted the bugs, so your own times would be unfairly fast.
2. **Regex-only secret scan** on 12 test diffs (6 contain fake secrets).
3. **Naive Dockerfile**: image size, cold build, rebuild after a code change, start-up time, user. Keep Docker Desktop running.

Results go to `results/before/`, and `results/SUMMARY.md` shows the Before column. Screenshot it now.

### Phase 2: AFTER AI

```bash
python run_after.py
```

The same experiments run with the local LLM on: it writes `Dockerfile.ai`, checks the same 12 diffs, and diagnoses the same 6 failures. Results go to `results/after/`, and `results/SUMMARY.md` now shows **Before | After | Change** side by side. Also read `results/after/log_analysis_answers.md` and fix any auto-score the script got wrong.

Re-run one part only:

| Script | Phase |
|---|---|
| `bench/manual_timer.py` | before |
| `bench/secret_scan_bench.py --before` / without flag | before / after |
| `bench/docker_bench.py naive` / `ai` / `optimized` | before / after / after (fallback) |
| `bench/log_analysis_bench.py [--repeats 3]` | after |
| `ai/optimize_dockerfile.py` | after (creates Dockerfile.ai) |
| `bench/summarize.py` | rebuilds SUMMARY.md from whatever exists |

## 2. Git hooks (Module 2 demo)

```bash
git init
python hooks/install_hooks.py
```

- Commit a file containing `AKIAIOSFODNN7EXAMPLE` → commit is **blocked** and the output shows both the regex hit and the LLM's reason.
- `git add app.py && git commit` (no `-m`) → the editor opens with an **AI-written commit message**.

## 3. Jenkins pipeline (Module 3 demo)

1. Push this folder to a GitHub repo.
2. In Jenkins: **New Item → Pipeline → Pipeline script from SCM → Git**, paste the repo URL, Script Path `Jenkinsfile`.
3. **Build Now** → the build should be green.
4. Break something, e.g. change `(100 - percent)` to `(100 + percent)` in `app.py`, and push.
5. **Build with Parameters → untick AI_ASSIST** (before AI): the build goes red and you have to dig through the log yourself.
6. **Build with Parameters → tick AI_ASSIST** (after AI): same failure, but the **AI BUILD FAILURE ANALYSIS** box appears at the end of the Console Output.

`build.log` is archived with every build. The first build has no parameters yet; after it runs once, "Build with Parameters" appears.

Notes:

- The Jenkins agent needs `python` (or `python3`) and `docker` on its PATH. On Windows, Jenkins runs as a service user, so add Python to the **system** PATH, not just your user PATH.
- If Jenkins runs inside a Docker container, set `OLLAMA_URL = 'http://host.docker.internal:11434'` in the Jenkinsfile.
- If Ollama is down, the AI stage prints "Skipped" and never breaks the build on its own.

## 4. Suggested live demo flow (~5 min)

1. Show the architecture table above (30 s).
2. Git: the secret commit gets blocked, then an AI commit message is written (1 min).
3. Jenkins: push a bug, build with AI_ASSIST off (raw red log), then on (AI diagnosis) (2 min).
4. Show `results/SUMMARY.md`: Before | After | Change, plus where the AI got things wrong (1.5 min).

## Project layout

```
app.py, tests/            Flask app + 7 pytest tests
Jenkinsfile               Checkout -> Install -> Test -> Docker Build, AI on failure
Dockerfile.naive          "before AI" Dockerfile
Dockerfile.optimized      reviewed fallback if Dockerfile.ai doesn't build
ai/ollama_client.py       stdlib-only Ollama client (OLLAMA_URL, OLLAMA_MODEL)
ai/analyze_log.py         build-failure analyser
ai/commit_assist.py       secret scan + commit message (used by hooks)
ai/optimize_dockerfile.py writes Dockerfile.ai
ai/run_step.py            portable `tee` so Jenkins logs go to build.log
hooks/                    git hooks + installer
bench/                    benchmarks, seeded scenarios, summary
run_before.py             Phase 1: measure everything with AI off
run_after.py              Phase 2: same measurements with AI on
```
