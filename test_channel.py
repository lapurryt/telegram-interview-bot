from telegram import Bot
import keys

def test_channel():
    """Simple test to check channel connection"""
    try:
        bot = Bot(token=keys.token)
        
        # Try to send a simple test message
        message = "🤖 Test message from Interview Bot"
        
        result = bot.send_message(
            chat_id="@ddd999dd999",
            text=message
        )
        
        print("✅ SUCCESS! Message sent to channel!")
        print(f"Message ID: {result.message_id}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n🔧 TO FIX THIS:")
        print("1. Add your bot to the channel @ddd999dd999")
        print("2. Make the bot an ADMIN of the channel")
        print("3. Give the bot 'Send Messages' permission")
        print("\n📋 STEPS:")
        print("1. Go to your channel @ddd999dd999")
        print("2. Click on channel name → Manage Channel")
        print("3. Click 'Administrators'")
        print("4. Click 'Add Admin'")
        print("5. Search for your bot username")
        print("6. Add it and enable 'Send Messages' permission")
        return False

if __name__ == "__main__":
    print("Testing channel connection...")
    test_channel() 