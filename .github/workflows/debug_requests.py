from mongoengine import connect, disconnect
from models import User, Request, Holiday
import json

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def debug_visibility():
    print("Attempting to connect to MongoDB...")
    connect(host=ATLAS_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    print("Connected!")
    
    print("--- RECENT REQUESTS ---")
    requests = Request.objects().order_by('-created_at')[:10]
    for r in requests:
        print(f"ID: {r.id}")
        print(f"  Student: {r.student_name} ({r.student_email})")
        print(f"  Dept: '{r.dept}'")
        print(f"  Resident: {r.resident_type}")
        print(f"  Status: {r.status}")
        print(f"  Year/Sem/Sec: '{r.year_sem_sec}'")
        print("-" * 20)

    print("\n--- STAFF USERS ---")
    staff = User.objects(role='staff')
    for s in staff:
        print(f"Staff: {s.name} ({s.email})")
        print(f"  Dept: '{s.dept}'")
        print(f"  Year: '{s.year}'")
        print(f"  Section: '{s.section}'")
    
    print("\n--- HOD USERS ---")
    hods = User.objects(role='hod')
    for h in hods:
        print(f"HOD: {h.name} ({h.email})")
        print(f"  Dept: '{h.dept}'")

if __name__ == "__main__":
    try:
        debug_visibility()
    finally:
        disconnect()
