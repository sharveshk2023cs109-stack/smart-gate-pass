import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add current directory to path to import app
sys.path.append(os.getcwd())

class TestNotifications(unittest.TestCase):
    @patch('app.Client')
    def test_send_whatsapp_notification(self, mock_client):
        from app import app, send_whatsapp_notification
        
        # Setup mock credentials
        app.config['TWILIO_SID'] = 'ACtest'
        app.config['TWILIO_TOKEN'] = 'test_token'
        app.config['TWILIO_PHONE'] = '+14155238886'
        
        # Mock the Twilio client and messages.create
        mock_instance = mock_client.return_value
        mock_instance.messages.create.return_value.sid = 'SMtest'
        
        # Call the helper
        send_whatsapp_notification('+919876543210', 'John Doe', '2026-03-04 19:30:00')
        
        # Verify Twilio was called correctly
        mock_instance.messages.create.assert_called_once_with(
            from_='whatsapp:+14155238886',
            body='Smart Gate Pass: Your child John Doe has left the campus at 2026-03-04 19:30:00.',
            to='whatsapp:+919876543210'
        )
        print("✓ Test passed: Twilio notification logic is correct.")

if __name__ == '__main__':
    unittest.main()
