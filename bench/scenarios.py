"""Seeded build-failure scenarios shared by the manual timer and the AI benchmark.

Each scenario injects one realistic bug into a temp copy of the project, runs the
test suite, and captures the failing log. `keywords`: if the AI's ROOT CAUSE/FIX
mentions any of these, the diagnosis is auto-scored correct (verify by hand too).
"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCENARIOS = [
    {
        "id": "S1_logic_bug",
        "desc": "Discount formula adds instead of subtracts",
        "file": "app.py",
        "old": "(100 - percent)",
        "new": "(100 + percent)",
        "truth": "apply_discount uses (100 + percent) instead of (100 - percent)",
        "keywords": ["100 + percent", "+ percent", "100 - percent", "subtract", "minus"],
    },
    {
        "id": "S2_syntax_error",
        "desc": "Missing colon after function definition",
        "file": "app.py",
        "old": "def get_port():",
        "new": "def get_port()",
        "truth": "SyntaxError: missing ':' after def get_port()",
        "keywords": ["colon", "':'", "\":\"", "missing :"],
    },
    {
        "id": "S3_missing_dependency",
        "desc": "New import not added to requirements",
        "file": "app.py",
        "old": "from flask import Flask, jsonify, request",
        "new": "from flask import Flask, jsonify, request\nfrom flask_cors import CORS",
        "truth": "flask_cors (Flask-Cors) imported but not installed / not in requirements.txt",
        "keywords": ["flask_cors", "flask-cors", "flask cors"],
    },
    {
        "id": "S4_key_typo",
        "desc": "Typo in dictionary key causes 500 error",
        "file": "app.py",
        "old": 'name=product["name"]',
        "new": 'name=product["nmae"]',
        "truth": "KeyError: 'nmae' typo in get_product, should be 'name'",
        "keywords": ["nmae"],
    },
    {
        "id": "S5_config_typo",
        "desc": "Default PORT '50OO' uses letter O instead of zero",
        "file": "app.py",
        "old": 'os.environ.get("PORT", "5000")',
        "new": 'os.environ.get("PORT", "50OO")',
        "truth": "Default port string '50OO' contains letter O, int() fails",
        "keywords": ["letter o", "capital o", "letter \"o\"", "letter 'o'", "letters o", "'o'", "zero"],
    },
    {
        "id": "S6_wrong_status",
        "desc": "Missing product returns 200 instead of 404",
        "file": "app.py",
        "old": 'return jsonify(error="product not found"), 404\n    return jsonify(id=pid, name',
        "new": 'return jsonify(error="product not found"), 200\n    return jsonify(id=pid, name',
        "truth": "get_product returns status 200 instead of 404 for a missing product",
        "keywords": ["404"],
    },
]

# Set B: six NEW bugs of the same kinds, used for the 3-level comparison
# (self / chatbot / full AI) so the person timing hasn't seen them before.
SCENARIOS_B = [
    {
        "id": "B1_logic_bug",
        "desc": "Discount divides by 10 instead of 100",
        "file": "app.py",
        "old": "(100 - percent) / 100",
        "new": "(100 - percent) / 10",
        "truth": "apply_discount divides by 10 instead of 100",
        "keywords": ["/ 10 ", "/10 ", "by 10 ", "by 10,", "by 10.", "10 instead"],
    },
    {
        "id": "B2_syntax_error",
        "desc": "Unclosed parenthesis in health route",
        "file": "app.py",
        "old": 'return jsonify(status="ok")',
        "new": 'return jsonify(status="ok"',
        "truth": "SyntaxError: '(' never closed in health() - add the closing parenthesis",
        "keywords": ["parenthes", "never closed", "bracket", "')'", "closing"],
    },
    {
        "id": "B3_bad_import",
        "desc": "Imports 'requests' from flask instead of 'request'",
        "file": "app.py",
        "old": "from flask import Flask, jsonify, request",
        "new": "from flask import Flask, jsonify, requests",
        "truth": "ImportError: flask has no 'requests' - should be 'request'",
        "keywords": ["requests"],
    },
    {
        "id": "B4_name_typo",
        "desc": "Variable name typo 'precent'",
        "file": "app.py",
        "old": 'apply_discount(product["price"], percent)',
        "new": 'apply_discount(product["price"], precent)',
        "truth": "NameError: 'precent' typo in get_price, should be 'percent'",
        "keywords": ["precent"],
    },
    {
        "id": "B5_type_error",
        "desc": "Query parameter not converted to a number",
        "file": "app.py",
        "old": 'percent = float(request.args.get("discount", 0))',
        "new": 'percent = request.args.get("discount", 0)',
        "truth": "discount query param stays a string; wrap it in float()",
        "keywords": ["float(", "float()", "convert", "cast", "string to", "str to"],
    },
    {
        "id": "B6_wrong_route",
        "desc": "Health route renamed to /healthz",
        "file": "app.py",
        "old": '@app.get("/health")',
        "new": '@app.get("/healthz")',
        "truth": "Route is /healthz but the test calls /health - rename it back",
        "keywords": ["healthz"],
    },
]

SETS = {"A": SCENARIOS, "B": SCENARIOS_B}


def build_failure_log(scenario):
    """Copy project to a temp dir, inject the bug, run pytest, return the log text."""
    tmp = tempfile.mkdtemp(prefix="devops_ai_")
    try:
        for name in ("app.py", "requirements.txt", "requirements-dev.txt"):
            shutil.copy(os.path.join(ROOT, name), tmp)
        shutil.copytree(os.path.join(ROOT, "tests"), os.path.join(tmp, "tests"),
                        ignore=shutil.ignore_patterns("__pycache__"))
        path = os.path.join(tmp, scenario["file"])
        with open(path, encoding="utf-8") as f:
            src = f.read()
        if scenario["old"] not in src:
            raise RuntimeError(f"{scenario['id']}: pattern not found in {scenario['file']}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src.replace(scenario["old"], scenario["new"], 1))

        cmd = [sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider"]
        proc = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True)
        log = f"$ python -m pytest -v\n{proc.stdout}{proc.stderr}"
        # Hide the temp folder path so logs look like a normal CI workspace
        return log.replace(tmp, "/var/jenkins_home/workspace/devops-ai-lab"), proc.returncode
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def score(answer, scenario):
    a = answer.lower()
    return any(k.lower() in a for k in scenario["keywords"])
