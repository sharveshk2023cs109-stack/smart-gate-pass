import sys
import os
import subprocess

print("-" * 30)
print("DIAGNOSTIC REPORT")
print("-" * 30)
print(f"Python Executable: {sys.executable}")
print(f"Python Version: {sys.version}")

print("\nChecking for certifi...")
try:
    import certifi
    print(f"✓ certifi is installed at: {certifi.where()}")
except ImportError:
    print("✗ certifi is NOT installed")

print("\nChecking for pymongo and mongoengine...")
try:
    import pymongo
    import mongoengine
    print(f"✓ pymongo version: {pymongo.version}")
    print(f"✓ mongoengine version: {mongoengine.__version__}")
except ImportError as e:
    print(f"✗ Library missing: {e}")

print("\nTesting DNS resolution for Atlas...")
try:
    import socket
    host = "cluster0.pe7tmzj.mongodb.net"
    ip = socket.gethostbyname(host)
    print(f"✓ Resolved {host} to {ip}")
except Exception as e:
    print(f"✗ DNS Resolution failed: {e}")

print("\nRecommended Fix Command:")
print(f"{sys.executable} -m pip install certifi --user")
print("-" * 30)
