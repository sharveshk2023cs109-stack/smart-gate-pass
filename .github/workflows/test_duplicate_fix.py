import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api"

def test_duplicate_blocking():
    # 1. Login as Gate Security
    login_data = {
        "email": "gate@portal.edu",
        "password": "gateportal123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print("Login failed. Make sure the server is running.")
        return
    
    token = response.json().get("token")
    headers = {"Authorization": token}
    
    # 2. Prepare test data
    test_id = "65d8f6b281a8b9f1a2b3c4d5" # Mocking a 24-char ObjectID
    scan_data = {
        "id": test_id,
        "name": "Test Student",
        "dept": "CSE",
        "year_sem_sec": "Year 3 / Sem 6 / Sec A"
    }
    
    # 3. First scan
    print("Attempting first scan...")
    r1 = requests.post(f"{BASE_URL}/gate/record", json=scan_data, headers=headers)
    print(f"R1: {r1.json()}")
    
    # 4. Immediate second scan (duplicate)
    print("\nAttempting immediate second scan...")
    r2 = requests.post(f"{BASE_URL}/gate/record", json=scan_data, headers=headers)
    print(f"R2: {r2.json()}")
    
    if r2.json().get("message") == "Duplicate scan ignored":
        print("\nSUCCESS: Duplicate entry was blocked by the backend.")
    else:
        print("\nFAILURE: Duplicate entry may have been allowed.")

if __name__ == "__main__":
    test_duplicate_blocking()
