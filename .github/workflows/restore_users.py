from mongoengine import connect
from models import User
import certifi

# MongoDB Connection String from app.py
ATLAS_URI = "mongodb+srv://cibiraj077_db_user:Cibiraj.001122@cluster0.pe7tmzj.mongodb.net/smart_gate_pass?retryWrites=true&w=majority&appName=Cluster0"

def restore_users():
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB Atlas...")
        connect(host=ATLAS_URI)
        print("✓ Connected successfully.")

        # Default users to restore
        defaults = [
            {'name': 'System Admin', 'email': 'admin@portal.edu', 'password': 'adminportal123', 'role': 'admin'},
            {'name': 'Gate Security', 'email': 'gate@portal.edu', 'password': 'gateportal123', 'role': 'gate'}
        ]

        for def_user in defaults:
            user = User.objects(email=def_user['email']).first()
            if not user:
                print(f"Restoring {def_user['role']} ({def_user['email']})...")
                user = User(
                    name=def_user['name'],
                    email=def_user['email'],
                    password=def_user['password'],
                    role=def_user['role']
                )
                user.hash_password()
                user.save()
                print(f"✓ {def_user['role'].capitalize()} restored successfully.")
            else:
                print(f"ℹ {def_user['role'].capitalize()} already exists.")

    except Exception as e:
        print(f"✗ ERROR: {e}")

if __name__ == "__main__":
    restore_users()
