import subprocess
import sys
import os

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONIOENCODING"] = "utf-8"

CMD = [
    sys.executable, "-m", "nuitka",
    "--standalone",
    "--onefile",
    "--windows-console-mode=disable",
    "--enable-plugin=pyqt6",
    "--include-package=core",
    "--include-package=input",
    "--include-package=ui",
    "--include-data-files=config.json=config.json",
    "--output-filename=LectureZoom.exe",
    "--output-dir=dist",
    "main.py",
]

print("Building LectureZoom with Nuitka...")
print(f"Command: {' '.join(CMD)}")

env = os.environ.copy()
result = subprocess.run(
    CMD,
    env=env,
    encoding="utf-8",
    errors="replace",
)
sys.exit(result.returncode)
