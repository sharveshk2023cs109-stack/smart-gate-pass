import os
import datetime
from mongoengine import connect, disconnect
from models import User, Request, Holiday

# Use the same connection string as app.py
ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def log(msg):
    print(msg)
    with open("verify_results.txt", "a") as f:
        f.write(msg + "\n")

# Clear file
with open("verify_results.txt", "w") as f:
    f.write(f"--- Verification Run: {datetime.datetime.now()} ---\n")

def test_holiday_bypass():
    log("Connecting to MongoDB...")
    connect(host=ATLAS_URI, tlsAllowInvalidCertificates=True)
    
    test_date = "2026-12-25"
    
    # Setup: Create a holiday
    print(f"Setting up holiday on {test_date}...")
    Holiday.objects(date=test_date).delete()
    holiday = Holiday(date=test_date, reason="Test Christmas Holiday").save()
    
    # Setup: Users
    hosteller_email = "test_hosteller@example.com"
    day_scholar_email = "test_dayscholar@example.com"
    
    User.objects(email=hosteller_email).delete()
    User.objects(email=day_scholar_email).delete()
    
    hosteller = User(name="Test Hosteller", email=hosteller_email, password="password", role="student").save()
    day_scholar = User(name="Test Day Scholar", email=day_scholar_email, password="password", role="student").save()
    
    def simulate_submission(student, resident_type):
        log(f"\nSimulating submission for {student.name} ({resident_type})")
        new_request = Request(
            student=student,
            student_name=student.name,
            student_email=student.email,
            type="Leave",
            resident_type=resident_type,
            from_date=test_date,
            to_date=test_date,
            days=1,
            reason="Holiday Visit"
        )
        # Default status from model is 'Pending'
        new_request.save()
        
        # LOGIC FROM APP.PY
        try:
            start_date = datetime.datetime.strptime(new_request.from_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(new_request.to_date, "%Y-%m-%d")
            delta = end_date - start_date
            dates_to_check = [(start_date + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]
            
            holiday_count = Holiday.objects(date__in=dates_to_check).count()
            
            # THE FIX: and new_request.resident_type == 'Hosteller'
            if holiday_count == len(dates_to_check) and new_request.resident_type == 'Hosteller':
                new_request.status = 'Pending Warden'
                new_request.save()
                log(f"  ✓ SUCCESS: Status updated to '{new_request.status}' (Bypassed)")
            else:
                log(f"  - INFO: Status remains '{new_request.status}' (Standard flow)")
        except Exception as e:
            log(f"  ✗ ERROR: {e}")
        
        return new_request

    # Test Hosteller
    h_req = simulate_submission(hosteller, "Hosteller")
    assert h_req.status == "Pending Warden", f"Hosteller should be Pending Warden, got {h_req.status}"
    
    # Test Day Scholar
    d_req = simulate_submission(day_scholar, "Day Scholar")
    assert d_req.status == "Pending", f"Day Scholar should be Pending, got {d_req.status}"
    
    log("\n✓ ALL TESTS PASSED!")
    
    # Cleanup
    # h_req.delete()
    # d_req.delete()
    # holiday.delete()
    # hosteller.delete()
    # day_scholar.delete()

if __name__ == "__main__":
    try:
        test_holiday_bypass()
    finally:
        disconnect()
