import datetime
from mongoengine import connect, disconnect
from models import GateHistory

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def log(msg):
    print(msg)
    with open("qr_verify_log.txt", "a") as f:
        f.write(msg + "\n")

def verify_model():
    with open("qr_verify_log.txt", "w") as f:
        f.write("--- QR Fix Verification ---\n")
    log("Connecting...")
    connect(host=ATLAS_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    
    log("Attempting to save a GateHistory record with outing_time...")
    history = GateHistory(
        request_id="65d8f6b281a8b9f1a2b3c4d5",
        name="Test Verification",
        dept="DEBUG",
        year_sem_sec="N/A",
        outing_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    history.save()
    log(f"✓ SUCCESSFULLY SAVED record ID: {history.id}")
    
    # Clean up
    history.delete()
    log("✓ Cleanup successful.")

if __name__ == "__main__":
    try:
        verify_model()
    except Exception as e:
        print(f"✗ FAILED: {e}")
    finally:
        disconnect()
