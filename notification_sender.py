import logging
from datetime import datetime
from telegram import Bot
import asyncio
import keys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your private channel ID - updated to the new channel
CHANNEL_ID = "@ddd999dd999"

class NotificationSender:
    def __init__(self, bot_token):
        self.bot = Bot(token=bot_token)
        self.channel_id = CHANNEL_ID
    
    def format_date_for_display(self, date_str):
        """Format date as DD.MM day_name"""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{date_obj.strftime('%d.%m')} {day_names[date_obj.weekday()]}"
    
    def send_booking_notification(self, user_info, selected_date, selected_time):
        """Send booking notification to the private channel"""
        try:
            # Format the notification message
            formatted_date = self.format_date_for_display(selected_date)
            
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
            self.bot.send_message(
                chat_id=self.channel_id,
                text=notification_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"Booking notification sent to channel for user {user_display}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to channel: {e}")
            return False
    
    def send_test_message(self):
        """Send a test message to verify the channel connection"""
        try:
            test_message = (
                f"🤖 **Bot Notification Test**\n\n"
                f"✅ Interview Scheduling Bot is now connected to this channel!\n"
                f"📅 All new bookings will be logged here.\n"
                f"🕐 Connected at: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            
            self.bot.send_message(
                chat_id=self.channel_id,
                text=test_message,
                parse_mode='Markdown'
            )
            
            logger.info("Test message sent to channel successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False

# Create a global instance
notification_sender = NotificationSender(keys.token)

def send_booking_log(user_info, selected_date, selected_time):
    """Function to send booking notification (synchronous wrapper)"""
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create a new bot instance for this call
        bot = Bot(token=keys.token)
        
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
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=notification_text,
            parse_mode='Markdown'
        )
        
        logger.info(f"Booking notification sent to channel {CHANNEL_ID} for user {user_display}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending notification to channel: {e}")
        return False
    finally:
        if loop:
            loop.close()

def test_channel_connection():
    """Test the channel connection"""
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create a new bot instance for this call
        bot = Bot(token=keys.token)
        
        test_message = (
            f"🤖 **Bot Notification Test**\n\n"
            f"✅ Interview Scheduling Bot is now connected to this channel!\n"
            f"📅 All new bookings will be logged here.\n"
            f"🕐 Connected at: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        
        # Send the test message
        bot.send_message(
            chat_id=CHANNEL_ID,
            text=test_message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Test message sent to channel {CHANNEL_ID} successfully")
        print(f"✅ Successfully connected to channel: {CHANNEL_ID}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending test message: {e}")
        return False
    finally:
        if loop:
            loop.close()

if __name__ == "__main__":
    # Test the channel connection
    print("Testing channel connection...")
    if test_channel_connection():
        print("✅ Channel connection successful!")
    else:
        print("❌ Channel connection failed!")
        print("\nTo fix this:")
        print("1. Make sure your bot is added to the channel as an admin")
        print("2. The bot needs 'Send Messages' permission")
        print("3. Try using the channel ID instead of username") 