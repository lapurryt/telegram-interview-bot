from notification_sender import send_cancellation_log

def test_cancellation():
    """Test the cancellation notification"""
    try:
        # Simulate a cancellation
        user_info = {
            'id': 123456789,
            'username': 'testuser',
            'first_name': 'Test User',
            'last_name': 'Test'
        }
        
        selected_date = "2025-08-05"
        selected_time = "10:00 - 11:00"
        
        # Send cancellation notification
        result = send_cancellation_log(user_info, selected_date, selected_time)
        
        if result:
            print("✅ Cancellation notification sent successfully!")
        else:
            print("❌ Failed to send cancellation notification")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing cancellation notification...")
    test_cancellation() 