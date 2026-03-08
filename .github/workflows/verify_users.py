from mongoengine import connect
from models import User
import certifi

ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def verify_users():
    try:
        connect(host=ATLAS_URI, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
        print("Checking users...")
        
        admin = User.objects(role='admin').first()
        gate = User.objects(role='gate').first()
        
        if admin:
            print(f"✓ Admin exists: {admin.email}")
        else:
            print("✗ Admin NOT found")
            
        if gate:
            print(f"✓ Gate exists: {gate.email}")
        else:
            print("✗ Gate NOT found")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_users()
