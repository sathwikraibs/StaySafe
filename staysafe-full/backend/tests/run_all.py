"""
Run every backend test file and fail if any test fails.
Used by the GitHub check on every change, and locally:  python tests/run_all.py
Each file runs on its own (some set up fakes for outside services before their tests).
"""
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)


def main() -> int:
    bad, total = [], 0
    for path in sorted(glob.glob(os.path.join(HERE, "test_*.py"))):
        name = os.path.basename(path)
        run = subprocess.run([sys.executable, path], cwd=BACKEND, capture_output=True, text=True, timeout=900,
                             env=dict(os.environ, PYTHONUNBUFFERED="1"))
        out = run.stdout + run.stderr
        fails = [line for line in out.splitlines() if line.startswith("FAIL")]
        m = re.search(r"(\d+)/(\d+) tests passed", out)
        passed = m and m.group(1) == m.group(2) and not fails and run.returncode == 0
        total += int(m.group(2)) if m else 0
        print(f"{'ok  ' if passed else 'FAIL'}  {name}  {m.group(0) if m else '(no summary)'}")
        if not passed:
            bad.append(name)
            print(out[-3000:])
            if os.environ.get("GITHUB_ACTIONS"):
                # shown on the run's summary page, so a failure can be read without the full log
                detail = "\n".join(fails[:15]) + "\n---\n" + out[-1800:]
                print(f"::error title={name}::" + detail.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
    print(f"\n{total} tests in {len(glob.glob(os.path.join(HERE, 'test_*.py')))} files; "
          + ("all passed" if not bad else f"failed: {', '.join(bad)}"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
