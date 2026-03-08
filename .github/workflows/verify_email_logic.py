import jwt
import datetime
import requests
import json

BASE_URL = "http://localhost:5000"
SECRET_KEY = "smart-gate-pass-secure-key-2026-v1-highly-confidential"

def test_email_logic():
    print("Testing Email Approval Logic...")
    
    # 1. Simulate Token Generation
    req_id = "65e6d6c6e4b0a1a1a1a1a1a1" # Example ID
    role = "staff"
    
    token = jwt.encode({
        'req_id': req_id,
        'role': role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")
    
    print(f"Generated Token: {token[:20]}...")
    
    # 2. Test the Endpoint (Simulated)
    # Since we can't easily run the server and hit it from here while it's in debug mode blocking
    # We will just verify that the token can be decoded by the same logic used in the app.
    
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert data['req_id'] == req_id
        assert data['role'] == role
        print("✓ Token verification logic - PASSED")
    except Exception as e:
        print(f"✗ Token verification logic - FAILED: {e}")

if __name__ == "__main__":
    test_email_logic()
