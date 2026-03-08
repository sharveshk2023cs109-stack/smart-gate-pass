from mongoengine import connect, disconnect
from models import Request

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def log(msg):
    print(msg)
    with open("debug_log.txt", "a") as f:
        f.write(msg + "\n")

def count_requests():
    with open("debug_log.txt", "w") as f:
        f.write("--- Debug Log ---\n")
    log("Connecting...")
    connect(host=ATLAS_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    count = Request.objects.count()
    log(f"Total Requests in DB: {count}")
    
    # Peek at the last one
    last = Request.objects.order_by('-created_at').first()
    if last:
        log(f"Latest Request Status: {last.status}")
        log(f"Latest Request Dept: '{last.dept}'")
        log(f"Latest Request YearSemSec: '{last.year_sem_sec}'")

if __name__ == "__main__":
    try:
        count_requests()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        disconnect()
