from telegram import Bot
from datetime import datetime
import keys

def test_notification():
    """Test the notification system"""
    try:
        bot = Bot(token=keys.token)
        
        # Simulate a booking notification
        user_info = {
            'id': 123456789,
            'username': 'testuser',
            'first_name': 'Test User',
            'last_name': 'Test'
        }
        
        selected_date = "2025-08-05"
        selected_time = "10:00 - 11:00"
        
        # Format the notification message
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = f"{date_obj.strftime('%d.%m')} {day_names[date_obj.weekday()]}"
        
        # Get username or first name
        username = user_info.get('username', '')
        first_name = user_info.get('first_name', 'Unknown')
        
        if username:
            user_display = f"@{username}"
        else:
            user_display = first_name
        
        notification_text = (
            f"📅 **New Interview Booking**\n\n"
            f"👤 **User:** {user_display}\n"
            f"📅 **Date:** {formatted_date}\n"
            f"⏰ **Time:** {selected_time}\n"
            f"🆔 **User ID:** {user_info.get('id', 'Unknown')}\n"
            f"📝 **Booked at:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        # Send the notification
        result = bot.send_message(
            chat_id="@ddd999dd999",
            text=notification_text,
            parse_mode='Markdown'
        )
        
        print("✅ SUCCESS! Notification sent to channel!")
        print(f"Message ID: {result.message_id}")
        print(f"Channel: @ddd999dd999")
        print("\n📋 Notification sent:")
        print(notification_text)
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("Testing notification system...")
    test_notification() 