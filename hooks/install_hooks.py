"""Copy the AI git hooks into .git/hooks (works on Windows, macOS, Linux)."""
import os
import shutil
import stat

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dest = os.path.join(root, ".git", "hooks")
if not os.path.isdir(dest):
    raise SystemExit("No .git folder found. Run `git init` in the project folder first.")
for name in ("pre-commit", "prepare-commit-msg"):
    target = os.path.join(dest, name)
    shutil.copyfile(os.path.join(root, "hooks", name), target)
    os.chmod(target, os.stat(target).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print("installed", target)
