"""Combine results/before and results/after into results/SUMMARY.md.
Works after the BEFORE phase alone too (after-columns show as "-").

    python bench/summarize.py
"""
import csv
import os
from statistics import mean

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def load(phase, name):
    p = os.path.join(RES, phase, name)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def change(before, after, lower_is_better=True):
    if before in (None, 0) or after is None:
        return "-"
    d = 100 * (after - before) / before
    good = (d < 0) == lower_is_better
    return f"{d:+.0f}% ({'better' if good else 'worse'})"


def fmt(x, nd=1):
    return "-" if x is None else f"{x:.{nd}f}"


def main():
    out = ["# Before AI vs After AI - measured results\n"]

    # ---------- 1. Build-failure diagnosis ----------
    def avg_t(rows, col):
        return mean(float(r[col]) for r in rows) if rows else None

    def acc(rows, col):
        return 100 * mean(int(r[col]) for r in rows) if rows else None

    three_level_sets = []
    for set_ in ("A", "B"):
        selfB = load("before", f"manual_self_{set_}.csv")
        chatB = load("before", "manual_times.csv" if set_ == "A" else "manual_chatbot_B.csv")
        aiB = load("after", "log_analysis.csv" if set_ == "A" else "log_analysis_B.csv")
        if not selfB:
            continue
        three_level_sets.append(set_)
        out.append(f"## 1. Build-failure diagnosis: 3 levels of AI use (6 bugs, set {set_})\n")
        out.append("- **Level 1 - Self:** developer reads the log and fixes it, no AI")
        out.append("- **Level 2 - Chatbot:** copy log -> paste into an LLM chat -> read reply -> type fix")
        out.append("- **Level 3 - Pipeline AI:** Jenkins sends the log to the local LLM automatically\n")
        sm = {r["scenario"]: r for r in (selfB or [])}
        cm = {r["scenario"]: r for r in (chatB or [])}
        am = {}
        for r in aiB or []:
            am.setdefault(r["scenario"], []).append(r)
        out.append("| Scenario | L1 Self (s) | L1 ok | L2 Chatbot (s) | L2 ok | L3 Pipeline AI (s) | L3 ok |")
        out.append("|---|---|---|---|---|---|---|")
        yn = lambda r: ("yes" if r["manual_correct"] == "1" else "no") if r else "-"
        for sid in sorted(set(sm) | set(cm) | set(am)):
            x, y, z = sm.get(sid), cm.get(sid), am.get(sid)
            out.append(f"| {sid} | {x['manual_seconds'] if x else '-'} | {yn(x)} | "
                       f"{y['manual_seconds'] if y else '-'} | {yn(y)} | "
                       f"{fmt(mean(float(q['ai_seconds']) for q in z)) if z else '-'} | "
                       f"{(str(sum(int(q['ai_correct_auto']) for q in z)) + '/' + str(len(z))) if z else '-'} |")
        t1, t2, t3 = avg_t(selfB, "manual_seconds"), avg_t(chatB, "manual_seconds"), avg_t(aiB, "ai_seconds")
        a1, a2, a3 = acc(selfB, "manual_correct"), acc(chatB, "manual_correct"), acc(aiB, "ai_correct_auto")
        out.append("\n| Metric | L1 Self | L2 Chatbot | L3 Pipeline AI | L3 vs L1 |\n|---|---|---|---|---|")
        out.append(f"| Avg time per failure (s) | {fmt(t1)} | {fmt(t2)} | {fmt(t3)} | {change(t1, t3)} |")
        out.append(f"| Correct (%) | {fmt(a1, 0)} | {fmt(a2, 0)} | {fmt(a3, 0)} | {change(a1, a3, False)} |")
        if aiB:
            logl, ansl = mean(int(r["log_lines"]) for r in aiB), mean(int(r["answer_lines"]) for r in aiB)
            out.append(f"| Lines a developer must read | {logl:.0f} | {logl:.0f} + chat reply | {ansl:.0f} | {change(logl, ansl)} |")
        out.append("")

    manual, ai = load("before", "manual_times.csv"), load("after", "log_analysis.csv")
    if (manual or ai) and "A" not in three_level_sets:
        title = "Pilot run: chatbot vs pipeline AI (set A)" if three_level_sets else "1. Build-failure diagnosis"
        out.append(f"## {title}\n")
        man = {r["scenario"]: r for r in (manual or [])}
        by_ai = {}
        for r in ai or []:
            by_ai.setdefault(r["scenario"], []).append(r)
        out.append("| Scenario | Before: manual time (s) | Before: correct | After: AI time (s) | After: AI correct |")
        out.append("|---|---|---|---|---|")
        for sid in sorted(set(man) | set(by_ai)):
            m, rs = man.get(sid), by_ai.get(sid)
            out.append(
                f"| {sid} | {m['manual_seconds'] if m else '-'} | "
                f"{('yes' if m['manual_correct'] == '1' else 'no') if m else '-'} | "
                f"{fmt(mean(float(x['ai_seconds']) for x in rs)) if rs else '-'} | "
                f"{(str(sum(int(x['ai_correct_auto']) for x in rs)) + '/' + str(len(rs))) if rs else '-'} |")
        m_t, a_t = avg_t(manual, "manual_seconds"), avg_t(ai, "ai_seconds")
        m_a, a_a = acc(manual, "manual_correct"), acc(ai, "ai_correct_auto")
        out.append("\n| Metric | Before AI | After AI | Change |\n|---|---|---|---|")
        out.append(f"| Avg time to find root cause (s) | {fmt(m_t)} | {fmt(a_t)} | {change(m_t, a_t)} |")
        out.append(f"| Diagnoses correct (%) | {fmt(m_a, 0)} | {fmt(a_a, 0)} | {change(m_a, a_a, False)} |")
        if ai:
            logl = mean(int(r["log_lines"]) for r in ai)
            ansl = mean(int(r["answer_lines"]) for r in ai)
            out.append(f"| Lines a developer must read | {logl:.0f} | {ansl:.0f} | {change(logl, ansl)} |")
    all_ai = (ai or []) + (load("after", "log_analysis_B.csv") or [])
    tps = [float(r["tokens_per_s"]) for r in all_ai if r.get("tokens_per_s")]
    if all_ai:
        out.append(f"\nModel: `{all_ai[0]['model']}`" + (f", ~{mean(tps):.0f} tokens/s on this laptop" if tps else ""))
    out.append("")

    # ---------- 2. Secret detection ----------
    sb, sa = load("before", "secret_scan.csv"), load("after", "secret_scan.csv")
    if sb or sa:
        out.append("## 2. Secret detection before commit (Git pre-commit hook)\n")
        out.append("| Method | Secrets caught | False alarms | Accuracy |\n|---|---|---|---|")

        def line(rows, col, label):
            t = [r["real_secret"] == "1" for r in rows]
            p = [r[col] == "1" for r in rows]
            tp = sum(a and b for a, b in zip(p, t))
            fp = sum(a and not b for a, b in zip(p, t))
            acc = 100 * sum(a == b for a, b in zip(p, t)) / len(t)
            out.append(f"| {label} | {tp}/{sum(t)} | {fp}/{len(t) - sum(t)} | {acc:.0f}% |")

        if sb:
            line(sb, "regex_flag", "**Before:** regex hook")
        if sa:
            line(sa, "ai_flag", "**After:** LLM only")
            line(sa, "either_flag", "**After:** regex OR LLM (hook default)")
            line(sa, "both_flag", "**After:** regex AND LLM")
            out.append(f"\nLLM check time per commit: ~{mean(float(r['ai_seconds']) for r in sa):.1f}s (regex: ~0s)")
        out.append("")

    # ---------- 3. Docker ----------
    db, da = load("before", "docker.csv"), load("after", "docker.csv")
    if db or da:
        out.append("## 3. Docker image (naive vs AI-optimised Dockerfile)\n")
        b, a = (db or [None])[0], (da or [None])[0]
        out.append("| Metric | Before AI (Dockerfile.naive) | After AI (Dockerfile." + (a["variant"] if a else "ai") + ") | Change |")
        out.append("|---|---|---|---|")
        for k, label in (("image_mb", "Image size (MB)"), ("layers", "Layers"), ("cold_build_s", "Cold build (s)"),
                         ("rebuild_after_code_change_s", "Rebuild after code change (s)"), ("startup_s", "Start-up (s)")):
            x = float(b[k]) if b and b[k] not in ("", "None") else None
            y = float(a[k]) if a and a[k] not in ("", "None") else None
            out.append(f"| {label} | {fmt(x)} | {fmt(y)} | {change(x, y)} |")
        out.append(f"| Runs as | {b['runs_as'] if b else '-'} | {a['runs_as'] if a else '-'} | |")
        out.append("")

    os.makedirs(RES, exist_ok=True)
    path = os.path.join(RES, "SUMMARY.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"Saved {path}")


if __name__ == "__main__":
    main()
