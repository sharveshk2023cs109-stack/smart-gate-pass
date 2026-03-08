import os
import datetime
from mongoengine import connect, disconnect, Document, StringField, ReferenceField, CASCADE
from mongoengine.errors import DoesNotExist

# Mock models if needed or import them
# Since I'm on the same system, I can try importing from the local directory
import sys
sys.path.append(os.getcwd())

from models import User, Request

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def clean_dict(obj):
    if isinstance(obj, dict):
        return {k: clean_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [clean_dict(x) for x in obj]
    if hasattr(obj, 'to_mongo'):
        data = obj.to_mongo().to_dict()
        # This is the problematic part
        if isinstance(obj, Request) and obj.student:
            data['student'] = {
                'id': str(obj.student.id),
                'photo': obj.student.photo
            }
        return clean_dict(data)
    return obj

def reproduce():
    print("Connecting...")
    connect(host=ATLAS_URI, tlsAllowInvalidCertificates=True)
    
    email = "temp_reproduce@example.com"
    User.objects(email=email).delete()
    
    print("Creating user...")
    user = User(name="Temp User", email=email, password="password", role="student").save()
    
    print("Creating request...")
    req = Request(
        student=user,
        student_name=user.name,
        student_email=user.email,
        reason="Test",
        from_date="2026-01-01",
        to_date="2026-01-01",
        days=1
    ).save()
    
    print("Deleting user (simulating broken reference)...")
    user.delete()
    
    # Reload request from DB to ensure it's not cached in memory in a way that bypasses lazy loading
    req = Request.objects(id=req.id).first()
    
    print("Calling clean_dict...")
    try:
        clean_dict(req)
        print("Success? (Should have failed)")
    except DoesNotExist as e:
        print(f"Caught expected error: {e}")
    except Exception as e:
        print(f"Caught unexpected error: {type(e).__name__}: {e}")
    finally:
        req.delete()
        disconnect()

if __name__ == "__main__":
    reproduce()
