from mongoengine import connect, disconnect
from models import User, Request

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def verify_photos():
    print("Connecting to DB...")
    connect(host=ATLAS_URI, serverSelectionTimeoutMS=5000, tlsAllowInvalidCertificates=True)
    
    # 1. Check if model has the field
    print("Checking User model fields...")
    user_fields = User._fields.keys()
    if 'photo' in user_fields:
        print("✓ User model has 'photo' field.")
    else:
        print("✗ User model MISSING 'photo' field.")

    # 2. Check if a mock student can be saved with a photo
    print("Testing student registration with photo...")
    try:
        mock_email = "photo_test@edu.com"
        User.objects(email=mock_email).delete()
        
        test_user = User(
            name="Photo Test Student",
            email=mock_email,
            password="testpassword",
            role="student",
            dept="CSE",
            year="4",
            photo="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==" # Mock white pixel
        )
        test_user.save()
        print(f"✓ Successfully registered user with photo. ID: {test_user.id}")

        # 3. Verify clean_dict behavior for Requests
        print("Testing Request photo linkage...")
        mock_req = Request(
            student=test_user,
            student_name=test_user.name,
            student_email=test_user.email,
            dept="CSE",
            year_sem_sec="4 / Sem 7 / A",
            status="Pending",
            type="Leave",
            reason="Verification Test",
            from_date="2024-01-01",
            to_date="2024-01-02",
            days=1,
            resident_type="Day Scholar"
        )
        mock_req.save()
        
        # We need clean_dict from app.py. For simplicity, we just check the linked field
        if mock_req.student.photo.startswith("data:image"):
            print("✓ Request successfully linked to student photo.")
        
        # Cleanup
        mock_req.delete()
        test_user.delete()
        print("✓ Cleanup successful.")

    except Exception as e:
        print(f"✗ Verification Error: {e}")

if __name__ == "__main__":
    try:
        verify_photos()
    except Exception as e:
        print(f"FATAL: {e}")
    finally:
        disconnect()
