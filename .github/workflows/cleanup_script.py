import os
import shutil

items_to_delete = [
    "__pycache__",
    "tmp",
    "check_env.py",
    "count_requests.py",
    "debug_requests.py",
    "debug_v3.py",
    "diagnose.py",
    "install_certifi.py",
    "restore_users.py",
    "test_conn.py",
    "test_duplicate_fix.py",
    "verify_email_logic.py",
    "verify_fix.py",
    "verify_holidays.py",
    "verify_photo_feature.py",
    "verify_qr_fix.py",
    "verify_users.py"
]

base_dir = r"d:\gate form management system"

for item in items_to_delete:
    path = os.path.join(base_dir, item)
    if os.path.exists(path):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Deleted directory: {item}")
            else:
                os.remove(path)
                print(f"Deleted file: {item}")
        except Exception as e:
            print(f"Error deleting {item}: {e}")
    else:
        print(f"Item not found: {item}")
