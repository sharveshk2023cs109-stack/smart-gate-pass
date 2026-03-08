import pymongo
import ssl
import sys
import certifi
import traceback

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def log(msg):
    print(msg)
    with open("results.txt", "a") as f:
        f.write(msg + "\n")

# Clear file
with open("results.txt", "w") as f:
    f.write(f"--- Test Run: {sys.version} ---\n")

log(f"Certifi path: {certifi.where()}")

try:
    log("Testing connection...")
    client = pymongo.MongoClient(
        ATLAS_URI, 
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where()
    )
    is_primary = client.is_primary
    log(f"Is primary: {is_primary}")
    log("✓ Successfully connected!")
except Exception as e:
    log(f"✗ Connection failed: {str(e)}")
    with open("results.txt", "a") as f:
        traceback.print_exc(file=f)
