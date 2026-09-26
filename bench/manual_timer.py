"""BEFORE-AI baselines: time a human fixing each failed build log.

    python bench/manual_timer.py --mode self    --set B   # level 1: read the log yourself
    python bench/manual_timer.py --mode chatbot --set B   # level 2: copy log -> ask a chatbot -> type fix

Level 3 (full AI in the pipeline) is bench/log_analysis_bench.py --set B.
Do NOT open bench/scenarios.py first - it contains the answers.

Results -> results/before/manual_<mode>_<set>.csv
(Running with no arguments reproduces the original pilot run: chatbot on set A.)
"""
import argparse
import csv
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scenarios import ROOT, SETS, build_failure_log  # noqa: E402

OUT_DIR = os.path.join(ROOT, "results", "before")
LOG_DIR = os.path.join(ROOT, "results", "logs")

INSTRUCTIONS = {
    "self": "Read each log YOURSELF (no AI, no Google) and type the root cause + fix.",
    "chatbot": "For each log: copy the error, paste it into a chatbot, read the reply, then type the fix here.",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["self", "chatbot"], default="chatbot")
    ap.add_argument("--set", choices=list(SETS), default="A", dest="set_")
    args = ap.parse_args()

    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    order = SETS[args.set_][:]
    random.shuffle(order)
    rows = []
    print(f"MODE: {args.mode.upper()}   SET: {args.set_}")
    print(INSTRUCTIONS[args.mode])
    input("Press Enter to start...")
    for i, s in enumerate(order, 1):
        log, rc = build_failure_log(s)
        if rc == 0:
            continue
        with open(os.path.join(LOG_DIR, s["id"] + ".log"), "w", encoding="utf-8") as f:
            f.write(log)
        print("\n" * 3 + "=" * 70 + f"\nLOG {i}/{len(order)}   ({args.mode})\n" + "=" * 70)
        print(log)
        start = time.perf_counter()
        answer = input("\n>>> Type the root cause + fix, then Enter: ")
        secs = round(time.perf_counter() - start, 1)
        print(f"\nActual cause: {s['truth']}")
        correct = input("Were you correct? (y/n): ").strip().lower().startswith("y")
        rows.append({"scenario": s["id"], "manual_seconds": secs,
                     "manual_correct": int(correct), "manual_answer": answer})
        print(f"Time: {secs}s")

    rows.sort(key=lambda r: r["scenario"])
    # Original pilot run (chatbot, set A) keeps its old file name
    name = "manual_times.csv" if (args.mode, args.set_) == ("chatbot", "A") else f"manual_{args.mode}_{args.set_}.csv"
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    total = sum(r["manual_seconds"] for r in rows)
    print(f"\nSaved {path}\nTotal {total:.0f}s, correct {sum(r['manual_correct'] for r in rows)}/{len(rows)}")


if __name__ == "__main__":
    main()
