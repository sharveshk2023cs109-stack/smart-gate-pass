import os
import sys
import datetime
from mongoengine import connect, disconnect

# Add current directory to path to import models
sys.path.append(os.getcwd())
from models import User

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def verify_parent_mobile():
    print("Connecting to MongoDB...")
    connect(host=ATLAS_URI, tlsAllowInvalidCertificates=True)
    
    test_email = "test_parent_mobile@example.com"
    User.objects(email=test_email).delete()
    
    print(f"Creating test user with parent_mobile...")
    mobile = "+919876543210"
    user = User(
        name="Test Student",
        email=test_email,
        password="password",
        role="student",
        dept="CSE",
        year="3",
        semester="6",
        section="A",
        parent_mobile=mobile
    )
    user.hash_password()
    user.save()
    
    # Reload and verify
    reloaded_user = User.objects(email=test_email).first()
    print(f"Verifying parent_mobile for {reloaded_user.email}...")
    
    if reloaded_user.parent_mobile == mobile:
        print(f"✓ SUCCESS: parent_mobile stored correctly: {reloaded_user.parent_mobile}")
    else:
        print(f"✗ FAILED: parent_mobile mismatch. Expected {mobile}, got {reloaded_user.parent_mobile}")
    
    # Test update
    new_mobile = "+910123456789"
    print(f"Updating parent_mobile to {new_mobile}...")
    reloaded_user.parent_mobile = new_mobile
    reloaded_user.save()
    
    updated_user = User.objects(email=test_email).first()
    if updated_user.parent_mobile == new_mobile:
        print(f"✓ SUCCESS: parent_mobile updated correctly: {updated_user.parent_mobile}")
    else:
        print(f"✗ FAILED: parent_mobile update mismatch. Expected {new_mobile}, got {updated_user.parent_mobile}")

    print("\nCleaning up...")
    # updated_user.delete()
    disconnect()

if __name__ == "__main__":
    verify_parent_mobile()
