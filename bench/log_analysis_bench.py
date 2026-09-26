"""AFTER-AI: local LLM diagnoses each seeded build failure.

    python bench/log_analysis_bench.py              # set A (pilot)
    python bench/log_analysis_bench.py --set B      # set B (3-level comparison)
    python bench/log_analysis_bench.py --repeats 3  # checks consistency

Results -> results/after/log_analysis[_B].csv and log_analysis_answers[_B].md
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "ai"))
from analyze_log import analyze  # noqa: E402
from scenarios import ROOT, SETS, build_failure_log, score  # noqa: E402

OUT_DIR = os.path.join(ROOT, "results", "after")
LOG_DIR = os.path.join(ROOT, "results", "logs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--set", choices=list(SETS), default="A", dest="set_")
    args = ap.parse_args()
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    rows, answers = [], []
    suffix = "" if args.set_ == "A" else f"_{args.set_}"
    for s in SETS[args.set_]:
        log, rc = build_failure_log(s)
        if rc == 0:
            print(f"[{s['id']}] tests passed on this machine (bug not triggered) - skipped")
            continue
        with open(os.path.join(LOG_DIR, s["id"] + ".log"), "w", encoding="utf-8") as f:
            f.write(log)
        for run in range(1, args.repeats + 1):
            print(f"[{s['id']}] run {run}/{args.repeats} ...", end=" ", flush=True)
            r = analyze(log)
            ok = score(r["text"], s)
            print(f"{r['latency_s']}s  {'CORRECT' if ok else 'check manually'}")
            rows.append({
                "scenario": s["id"], "run": run, "model": r["model"],
                "log_lines": r["log_lines"], "answer_lines": r["answer_lines"],
                "ai_seconds": r["latency_s"], "tokens_per_s": r["tokens_per_s"],
                "ai_correct_auto": int(ok),
            })
            answers.append((s, run, r, ok))

    with open(os.path.join(OUT_DIR, f"log_analysis{suffix}.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    with open(os.path.join(OUT_DIR, f"log_analysis_answers{suffix}.md"), "w", encoding="utf-8") as f:
        f.write("# AI diagnoses of seeded build failures\n\n")
        f.write("Auto-score = the answer mentions the real cause. Read each one and correct the score by hand if needed.\n\n")
        for s, run, r, ok in answers:
            f.write(f"## {s['id']} (run {run}): {s['desc']}\n\n")
            f.write(f"**Actual cause:** {s['truth']}  \n**Auto-score:** {'correct' if ok else 'NOT matched'}"
                    f"  \n**Time:** {r['latency_s']}s  \n\n```\n{r['text']}\n```\n\n")

    n = len(rows)
    correct = sum(r["ai_correct_auto"] for r in rows)
    avg = sum(r["ai_seconds"] for r in rows) / n
    print(f"\nAI correct (auto): {correct}/{n}   avg time: {avg:.1f}s")
    print(f"Saved results/after/log_analysis{suffix}.csv and results/after/log_analysis_answers{suffix}.md")


if __name__ == "__main__":
    main()
