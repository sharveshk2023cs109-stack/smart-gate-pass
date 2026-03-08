import smtplib

def verify_smtp():
    server_addr = 'smtp.gmail.com'
    port = 587
    user = 'cibiraj.077@gmail.com'
    password = 'eome ywkt lbep zzsb'

    print(f"Connecting to {server_addr}:{port}...")
    try:
        server = smtplib.SMTP(server_addr, port, timeout=10)
        server.starttls()
        print("Attempting login...")
        server.login(user, password)
        print("✓ SMTP Authentication Successful!")
        server.quit()
        return True
    except Exception as e:
        print(f"✗ SMTP Authentication Failed: {e}")
        return False

if __name__ == "__main__":
    verify_smtp()
