"""One command to prepare an isolated environment and run the app or tests."""

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", action="store_true", help="Install test dependencies and run pytest")
    parser.add_argument("--export", action="store_true", help="Write summary and CSV reports to exports/")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        raise SystemExit("Please use Python 3.11, 3.12 or 3.13.")
    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not python.exists():
        print("Creating .venv", flush=True)
        venv.create(environment, with_pip=True)
    requirements = ROOT / ("requirements-dev.txt" if args.test else "requirements.txt")
    digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = environment / (".test-requirements" if args.test else ".app-requirements")
    if not stamp.exists() or stamp.read_text() != digest:
        # uv-created environments may not include pip.
        if subprocess.run([str(python), "-m", "pip", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            subprocess.check_call([str(python), "-m", "ensurepip", "--upgrade"])
        subprocess.check_call([str(python), "-m", "pip", "install", "-r", str(requirements)])
        stamp.write_text(digest)
    if args.test:
        command = [str(python), "-m", "pytest", "-q"]
    elif args.export:
        command = [str(python), "scripts/export_report.py"]
    else:
        command = [str(python), "-m", "streamlit", "run", "app.py", "--server.port", str(args.port),
                   "--server.address", "127.0.0.1"]
    try:
        return subprocess.call(command, cwd=ROOT)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
