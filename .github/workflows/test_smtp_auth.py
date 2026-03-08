import smtplib
import socket

def test_smtp():
    server_addr = 'smtp.gmail.com'
    port = 587
    user = 'cibiraj.077@gmail.com'
    password = 'Cibiraj.0012' # Provided by user

    print(f"Connecting to {server_addr}:{port}...")
    try:
        server = smtplib.SMTP(server_addr, port, timeout=10)
        server.set_debuglevel(1)
        server.starttls()
        print("Attempting login...")
        server.login(user, password)
        print("✓ Login successful!")
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"✗ Authentication Failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_smtp()
