#!/usr/bin/env python3
"""
Test script to verify reminder notifications are sent to admin channel
"""

import logging
from datetime import datetime, timedelta
from telegram import Bot
import keys
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import time
from notification_sender import send_reminder_log

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize scheduler with Moscow timezone
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
scheduler.start()

def send_test_reminder_with_notification(user_id, interview_date, interview_time):
    """Send test reminder to user and notification to admin channel"""
    try:
        # Create bot instance
        bot = Bot(token=keys.token)
        
        # Get current Moscow time
        moscow_time = datetime.now(pytz.timezone('Europe/Moscow'))
        
        # Format the reminder message
        reminder_text = (
            f"🔔 **ТЕСТОВОЕ НАПОМИНАНИЕ!**\n\n"
            f"📅 Дата: {interview_date}\n"
            f"⏰ Время: {interview_time}\n\n"
            f"⚠️ **Это тестовое напоминание!**\n\n"
            f"Система напоминаний работает корректно! ✅\n\n"
            f"Текущее время в Москве: {moscow_time.strftime('%H:%M:%S')}\n\n"
            f"В реальном режиме вы получите напоминание за 1 час до собеседования."
        )
        
        # Send reminder to user
        bot.send_message(
            chat_id=user_id,
            text=reminder_text,
            parse_mode='Markdown'
        )
        
        logger.info(f"Test reminder sent to user {user_id}")
        print(f"✅ Test reminder sent to user {user_id}")
        
        # Send notification to admin channel
        user_info = {
            'id': user_id,
            'username': 'test_user',
            'first_name': 'Test User'
        }
        
        success = send_reminder_log(user_info, interview_date, interview_time)
        if success:
            print(f"✅ Reminder notification sent to admin channel")
            logger.info(f"Reminder notification sent to admin channel for user {user_id}")
        else:
            print(f"❌ Failed to send reminder notification to admin channel")
            logger.error(f"Failed to send reminder notification to admin channel for user {user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending test reminder to user {user_id}: {e}")
        print(f"❌ Error sending test reminder: {e}")
        return False

def schedule_test_reminder_with_notification(user_id, interview_date, interview_time, minutes_from_now=2):
    """Schedule a test reminder for X minutes from now using Moscow time"""
    try:
        # Calculate reminder time (X minutes from now) in Moscow time
        moscow_tz = pytz.timezone('Europe/Moscow')
        reminder_time = datetime.now(moscow_tz) + timedelta(minutes=minutes_from_now)
        
        # Schedule the reminder
        job_id = f"test_reminder_notification_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        scheduler.add_job(
            func=send_test_reminder_with_notification,
            trigger='date',
            run_date=reminder_time,
            args=[user_id, interview_date, interview_time],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"Test reminder with notification scheduled for user {user_id} at {reminder_time}")
        print(f"✅ Test reminder with notification scheduled for {reminder_time.strftime('%H:%M:%S')} Moscow time (in {minutes_from_now} minutes)")
        return True
        
    except Exception as e:
        logger.error(f"Error scheduling test reminder for user {user_id}: {e}")
        print(f"❌ Error scheduling test reminder: {e}")
        return False

def test_reminder_notification():
    """Test the reminder system with admin channel notification"""
    print("🧪 Testing Reminder System with Admin Notifications")
    print("=" * 60)
    
    # Get current Moscow time
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_moscow = datetime.now(moscow_tz)
    print(f"🕐 Current Moscow time: {current_moscow.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Replace with your actual user ID from the logs
    user_id = 780202036  # This is the user ID from your logs
    
    print(f"👤 Testing with user ID: {user_id}")
    print(f"⏰ Will send reminder in 2 minutes (Moscow time)...")
    print(f"📢 Admin notification will be sent to channel @ddd999dd999")
    
    # Schedule test reminder
    success = schedule_test_reminder_with_notification(
        user_id=user_id,
        interview_date="2025-08-04",
        interview_time="12:00 - 13:00",  # Testing the new lunch time slot
        minutes_from_now=2
    )
    
    if success:
        print("\n📱 Please check your Telegram bot in 2 minutes!")
        print("You should receive a test reminder message.")
        print("\n📢 Please check your admin channel @ddd999dd999!")
        print("You should receive a reminder notification there too.")
        
        # Wait for the reminder to be sent
        print(f"\n⏰ Waiting {2 + 1} minutes for reminder to be sent...")
        time.sleep((2 + 1) * 60)  # Wait 3 minutes total
        
        print("\n✅ Test completed!")
        print("If you received both the reminder and the admin notification, the system is working correctly!")
        
    else:
        print("❌ Failed to schedule test reminder")

if __name__ == "__main__":
    test_reminder_notification()
    
    # Keep scheduler running
    print("\n⏰ Keeping scheduler running...")
    time.sleep(10)
    
    # Shutdown scheduler
    scheduler.shutdown()
    print("✅ Scheduler shutdown complete") 