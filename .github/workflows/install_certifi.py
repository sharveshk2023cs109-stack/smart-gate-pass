import subprocess
import sys
import os

def log(msg):
    with open("install_log.txt", "a") as f:
        f.write(msg + "\n")

with open("install_log.txt", "w") as f:
    f.write(f"Python: {sys.executable}\n")
    f.write(f"Path: {sys.path}\n")

try:
    log("Running: " + sys.executable + " -m pip install certifi")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "certifi"], capture_output=True, text=True)
    log("STDOUT: " + result.stdout)
    log("STDERR: " + result.stderr)
    
    log("Testing import...")
    import certifi
    log("Success! Certifi located at: " + certifi.where())
except Exception as e:
    log("Error: " + str(e))
