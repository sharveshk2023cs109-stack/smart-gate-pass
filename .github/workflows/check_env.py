import subprocess
import sys

with open("env_check.txt", "w") as f:
    f.write(f"Python: {sys.executable}\n")
    f.write(f"Version: {sys.version}\n")
    f.write("Installed packages:\n")
    subprocess.run([sys.executable, "-m", "pip", "list"], stdout=f, stderr=f)
