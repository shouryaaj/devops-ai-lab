"""Secret detection: regex hook (before AI) vs local LLM hook (after AI).

    python bench/secret_scan_bench.py --before   # regex only, Ollama not needed
    python bench/secret_scan_bench.py            # after: regex + LLM

All "secrets" below are fake. Results -> results/before|after/secret_scan.csv
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "ai"))
from commit_assist import ai_scan, regex_scan  # noqa: E402


def diff(path, *added):
    body = "\n".join("+" + a for a in added)
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1,0 +1,{len(added)} @@\n{body}"


# (id, has_real_secret, diff)
CASES = [
    ("L1_aws_key", True, diff("config.py", 'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"')),
    ("L2_password_literal", True, diff("settings.py", 'DB_PASSWORD = "Sup3rS3cret!2026"')),
    ("L3_private_key", True, diff("deploy/id_rsa", "-----BEGIN RSA PRIVATE KEY-----",
                                   "MIIEowIBAAKCAQEAu1SU1LfVLPHCozMxH2Mo4lgOEePzNm0tRgeLezV6ffAt0gun")),
    ("L4_conn_string", True, diff("app.py", 'DATABASE_URL = "postgresql://admin:Pr0dPass99@db.internal:5432/shop"')),
    ("L5_webhook_url", True, diff("notify.py",
                                  'SLACK_HOOK = "https://hooks.' + 'slack.com/services/T04ABCD12/B05EFGH34/q8Zk3nV1xYtR7mWp2LsJ9uHc"')),
    ("L6_token_in_yaml", True, diff(".github/config.yml", "deploy:", '  gh_pat: "gh' + 'p_8fK2mQ9vX4rT1nL7pW3sY6bZ0cD5hJ2aE9uR"')),
    ("C1_env_var_password", False, diff("settings.py", 'DB_PASSWORD = os.environ["DB_PASSWORD"]')),
    ("C2_token_from_header", False, diff("auth.py", 'token = request.headers.get("Authorization", "")')),
    ("C3_password_form_field", False, diff("templates/login.html", '<input type="password" name="password" required>')),
    ("C4_normal_code", False, diff("app.py", "def apply_tax(price, rate):", "    return round(price * (1 + rate), 2)")),
    ("C5_docs_mention", False, diff("README.md", "Set the `api_key: <your key>` value in your local .env file (never commit it).")),
    ("C6_secret_setting_name", False, diff("config.py", 'SECRET_KEY = os.getenv("SECRET_KEY")')),
]


def metrics(preds, truths):
    tp = sum(p and t for p, t in zip(preds, truths))
    fp = sum(p and not t for p, t in zip(preds, truths))
    fn = sum((not p) and t for p, t in zip(preds, truths))
    tn = sum((not p) and (not t) for p, t in zip(preds, truths))
    return {"caught": f"{tp}/{tp + fn}", "false_alarms": f"{fp}/{fp + tn}",
            "accuracy_pct": round(100 * (tp + tn) / len(truths), 1)}


def main():
    before = "--before" in sys.argv
    phase = "before" if before else "after"
    rows = []
    for cid, truth, d in CASES:
        rx = bool(regex_scan(d))
        row = {"case": cid, "real_secret": int(truth), "regex_flag": int(rx)}
        if before:
            print(f"{cid:24s} truth={int(truth)} regex={int(rx)}")
        else:
            r = ai_scan(d)
            row.update({"ai_flag": int(r["is_secret"]), "either_flag": int(rx or r["is_secret"]),
                        "both_flag": int(rx and r["is_secret"]), "ai_seconds": r["latency_s"],
                        "ai_reason": r["text"].replace("\n", " | ")[:200]})
            print(f"{cid:24s} truth={int(truth)} regex={int(rx)} ai={int(r['is_secret'])} ({r['latency_s']}s)")
        rows.append(row)

    out_dir = os.path.join(ROOT, "results", phase)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "secret_scan.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    truths = [bool(r["real_secret"]) for r in rows]
    print("\nMethod     caught   false alarms  accuracy")
    for m in (("regex",) if before else ("regex", "ai", "either", "both")):
        s = metrics([bool(r[m + "_flag"]) for r in rows], truths)
        print(f"{m:10s} {s['caught']:8s} {s['false_alarms']:13s} {s['accuracy_pct']}%")
    print(f"Saved results/{phase}/secret_scan.csv")


if __name__ == "__main__":
    main()
