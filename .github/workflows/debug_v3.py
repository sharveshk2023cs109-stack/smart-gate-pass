import sys
import datetime
from mongoengine import connect, disconnect
from models import User, Request

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def run_debug():
    log_file = "debug_v3.txt"
    def log(msg):
        print(msg)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"--- Debug Run {datetime.datetime.now()} ---\n")

    try:
        log("Connecting...")
        connect(host=ATLAS_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
        log("Connected successfully.")

        # 1. Total Requests
        total = Request.objects.count()
        log(f"Total Requests: {total}")

        # 2. Status counts
        pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        status_counts = list(Request.objects.aggregate(pipeline))
        log(f"Status Counts: {status_counts}")

        # 3. Sample of Pending requests
        pending = Request.objects(status="Pending").limit(5)
        log("\nPending Requests Samples:")
        for r in pending:
            log(f"ID: {r.id} | Dept: '{r.dept}' | YSS: '{r.year_sem_sec}' | Student: {r.student_name}")

        # 4. Check for Staff users
        staff_count = User.objects(role="staff").count()
        log(f"\nTotal Staff: {staff_count}")
        for s in User.objects(role="staff")[:5]:
            log(f"Staff: {s.name} | Dept: '{s.dept}' | Year: '{s.year}' | Sec: '{s.section}'")

    except Exception as e:
        log(f"FATAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    run_debug()
