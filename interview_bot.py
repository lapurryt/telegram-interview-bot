#!/usr/bin/env python3
"""
Interview Scheduling Bot for Telegram
Allows students to book interview slots with automatic reminders and admin notifications.
"""

import logging
import json
import os
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
from telegram import BotCommand
import keys
from notification_sender import send_booking_log, send_cancellation_log, send_reminder_log, send_mentor_booking_log
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global variables
interview_bookings = {}  # Store interview bookings (in production, use a database)
DATABASE_FILE = "data/bookings.json"  # JSON database file
USERS_DATABASE_FILE = "data/users.json"  # JSON database file for user registrations
MENTORS_DATABASE_FILE = "data/mentors.json"  # JSON database file for mentor assignments
users_database = {}  # Store user registration data
mentors_database = {}  # Store mentor assignments and availability

# Mentor configuration
MENTORS = {
    "mentor_1": {
        "name": "Илья",
        "username": "@yashonflame",
        "user_id": 780202036,  # yashonflame's user ID
        "max_students": 5,
        "specialization": "Full Stack Development"
    },
    "mentor_2": {
        "name": "Андрей",
        "username": "@hxcnv",
        "user_id": 887557370,  # hxcnv's user ID
        "max_students": 5,
        "specialization": "Backend Development"
    }
}

# Default mentor assignments (you can modify this)
DEFAULT_MENTOR_ASSIGNMENTS = {
    "780202036": "mentor_1",  # yashonflame -> Илья
    "432182242": "mentor_2",  # hey_cami -> Андрей
    "7900814468": "mentor_1", # GolubovNAi -> Илья
    "887557370": "mentor_2",  # hxcnv -> Андрей
}

# Time slots configuration
TIME_SLOTS = [
    "09:00 - 10:00",
    "10:00 - 11:00", 
    "11:00 - 12:00",
    "12:00 - 13:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00"
]

# Day names for display
DAY_NAMES = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']

# Initialize scheduler for reminders (Moscow time)
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Moscow'))
scheduler.start()
logger.info("Scheduler started with Moscow timezone")

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def load_users_from_database():
    """Load users from JSON database"""
    global users_database
    try:
        if os.path.exists(USERS_DATABASE_FILE):
            with open(USERS_DATABASE_FILE, 'r', encoding='utf-8') as file:
                users_database = json.load(file)
                logger.info(f"Loaded {len(users_database)} users from database")
        else:
            users_database = {}
            logger.info("No existing users database found, starting with empty users")
    except Exception as e:
        logger.error(f"Error loading users database: {e}")
        users_database = {}

def save_users_to_database():
    """Save users to JSON database"""
    try:
        with open(USERS_DATABASE_FILE, 'w', encoding='utf-8') as file:
            json.dump(users_database, file, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(users_database)} users to database")
    except Exception as e:
        logger.error(f"Error saving users database: {e}")

def register_user_if_new(user):
    """Register a new user if they don't exist in database"""
    user_id = str(user.id)
    if user_id not in users_database:
        users_database[user_id] = {
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'first_interaction': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_bookings_made': 0
        }
        save_users_to_database()
        logger.info(f"Registered new user: {user.id} ({user.username})")
        return True
    return False

def get_user_registration_date(user_id):
    """Get user registration date"""
    user_id_str = str(user_id)
    if user_id_str in users_database:
        return users_database[user_id_str].get('registration_date', 'Неизвестно')
    return 'Неизвестно'

def increment_user_total_bookings(user_id):
    """Increment user's total bookings count"""
    user_id_str = str(user_id)
    if user_id_str in users_database:
        if 'total_bookings_made' not in users_database[user_id_str]:
            users_database[user_id_str]['total_bookings_made'] = 0
        users_database[user_id_str]['total_bookings_made'] += 1
        save_users_to_database()
        logger.info(f"Incremented total bookings for user {user_id} to {users_database[user_id_str]['total_bookings_made']}")

def get_user_total_bookings(user_id):
    """Get user's total bookings count"""
    user_id_str = str(user_id)
    if user_id_str in users_database:
        return users_database[user_id_str].get('total_bookings_made', 0)
    return 0

# ============================================================================
# MENTOR MANAGEMENT FUNCTIONS
# ============================================================================

def load_mentors_from_database():
    """Load mentors from JSON database"""
    global mentors_database
    try:
        if os.path.exists(MENTORS_DATABASE_FILE):
            with open(MENTORS_DATABASE_FILE, 'r', encoding='utf-8') as file:
                mentors_database = json.load(file)
                logger.info(f"Loaded {len(mentors_database)} mentor assignments from database")
        else:
            mentors_database = {}
            logger.info("No existing mentors database found, starting with empty mentors")
    except Exception as e:
        logger.error(f"Error loading mentors database: {e}")
        mentors_database = {}

def save_mentors_to_database():
    """Save mentors to JSON database"""
    try:
        with open(MENTORS_DATABASE_FILE, 'w', encoding='utf-8') as file:
            json.dump(mentors_database, file, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(mentors_database)} mentor assignments to database")
    except Exception as e:
        logger.error(f"Error saving mentors database: {e}")

def get_user_permanent_mentor(user_id):
    """Get user's permanent mentor"""
    user_id_str = str(user_id)
    if user_id_str in mentors_database:
        return mentors_database[user_id_str].get('permanent_mentor')
    return None

def is_user_mentor(user_id):
    """Check if user is a mentor"""
    logger.info(f"Checking if user {user_id} is a mentor")
    for mentor_id, mentor_info in MENTORS.items():
        mentor_user_id = mentor_info.get('user_id')
        logger.info(f"Comparing {user_id} with mentor {mentor_id} user_id: {mentor_user_id}")
        if mentor_user_id == user_id:
            logger.info(f"User {user_id} is confirmed as mentor {mentor_id}")
            return True
    logger.info(f"User {user_id} is not a mentor")
    return False

def get_mentor_id_by_user_id(user_id):
    """Get mentor_id for a user if they are a mentor"""
    for mentor_id, mentor_info in MENTORS.items():
        if mentor_info.get('user_id') == user_id:
            return mentor_id
    return None

def has_used_one_time_change(user_id):
    """Check if user has used their one-time mentor change (deprecated - now unlimited)"""
    return False

def set_user_permanent_mentor(user_id, mentor_id):
    """Set user's permanent mentor"""
    user_id_str = str(user_id)
    if user_id_str not in mentors_database:
        mentors_database[user_id_str] = {}
    mentors_database[user_id_str]['permanent_mentor'] = mentor_id
    save_mentors_to_database()
    logger.info(f"Set permanent mentor {mentor_id} for user {user_id}")

def mark_one_time_change_used(user_id):
    """Mark that user has used their one-time mentor change (deprecated - now unlimited)"""
    pass

def get_mentor_availability(mentor_id, selected_date):
    """Get mentor's availability for a specific date"""
    mentor_bookings = 0
    for booking_key, booking_data in interview_bookings.items():
        if (booking_data.get('mentor_id') == mentor_id and 
            booking_data['date'] == selected_date):
            mentor_bookings += 1
    
    max_students = MENTORS[mentor_id]['max_students']
    return max_students - mentor_bookings

def get_available_mentors_for_date(selected_date, user_id):
    """Get available mentors for a specific date and user"""
    available_mentors = []
    permanent_mentor = get_user_permanent_mentor(user_id)
    
    # If user has a permanent mentor, only show that mentor
    if permanent_mentor:
        permanent_availability = get_mentor_availability(permanent_mentor, selected_date)
        if permanent_availability > 0:
            available_mentors.append({
                'mentor_id': permanent_mentor,
                'name': MENTORS[permanent_mentor]['name'],
                'availability': permanent_availability,
                'is_permanent': True
            })
    else:
        # User doesn't have a permanent mentor, show all available mentors
        for mentor_id, mentor_info in MENTORS.items():
            availability = get_mentor_availability(mentor_id, selected_date)
            if availability > 0:
                available_mentors.append({
                    'mentor_id': mentor_id,
                    'name': mentor_info['name'],
                    'availability': availability,
                    'is_permanent': False
                })
    
    return available_mentors

def load_bookings_from_database():
    """Load bookings from JSON database"""
    global interview_bookings
    try:
        if os.path.exists(DATABASE_FILE):
            with open(DATABASE_FILE, 'r', encoding='utf-8') as file:
                interview_bookings = json.load(file)
                logger.info(f"Loaded {len(interview_bookings)} bookings from database")
        else:
            interview_bookings = {}
            logger.info("No existing database found, starting with empty bookings")
    except Exception as e:
        logger.error(f"Error loading database: {e}")
interview_bookings = {}

def save_bookings_to_database():
    """Save bookings to JSON database"""
    try:
        with open(DATABASE_FILE, 'w', encoding='utf-8') as file:
            json.dump(interview_bookings, file, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(interview_bookings)} bookings to database")
    except Exception as e:
        logger.error(f"Error saving database: {e}")

def add_booking_to_database(booking_key, booking_data):
    """Add a new booking to database"""
    interview_bookings[booking_key] = booking_data
    save_bookings_to_database()
    logger.info(f"Added booking {booking_key} to database")

def remove_booking_from_database(booking_key):
    """Remove a booking from database"""
    if booking_key in interview_bookings:
        del interview_bookings[booking_key]
        save_bookings_to_database()
        logger.info(f"Removed booking {booking_key} from database")
        return True
    return False

# ============================================================================
# REMINDER SYSTEM FUNCTIONS
# ============================================================================

def send_reminder_to_user(user_id, interview_date, interview_time):
    """Send reminder to user about upcoming interview"""
    try:
        # Use the global bot instance instead of creating a new one
        from telegram import Bot
        bot = Bot(token=keys.token)
        
        # Format the reminder message
        date_obj = datetime.strptime(interview_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj, False)
        
        reminder_text = (
            f"🔔 **Напоминание о собеседовании!**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {interview_time}\n\n"
            f"⚠️ **Через 1 час у вас собеседование!**\n\n"
            f"Пожалуйста, не забудьте:\n"
            f"• Прийти за 15 минут до начала\n"
            f"• Быть готовым к интервью\n\n"
            f"Удачи! 🍀"
        )
        
        # Send message with better error handling
        try:
            bot.send_message(
                chat_id=user_id,
                text=reminder_text,
                parse_mode='Markdown'
            )
            logger.info(f"Reminder sent to user {user_id} for interview on {interview_date} at {interview_time}")
        except Exception as send_error:
            logger.error(f"Failed to send reminder to user {user_id}: {send_error}")
            # Try to send without markdown if markdown fails
            try:
                bot.send_message(
                    chat_id=user_id,
                    text=reminder_text.replace('**', '').replace('*', '')
                )
                logger.info(f"Reminder sent to user {user_id} without markdown")
            except Exception as fallback_error:
                logger.error(f"Failed to send reminder to user {user_id} even without markdown: {fallback_error}")
                return False
        
        # Send notification to admin channel
        try:
            # Get user info from interview_bookings with better search
            user_info = None
            for booking_key, booking_data in interview_bookings.items():
                if (booking_data.get('user_id') == user_id and 
                    booking_data.get('date') == interview_date and 
                    booking_data.get('time') == interview_time):
                    user_info = booking_data.get('user_info', {})
                    break
            
            if user_info:
                send_reminder_log(user_info, interview_date, interview_time)
                logger.info(f"Reminder notification sent to admin channel for user {user_id}")
            else:
                logger.warning(f"Could not find user info for reminder notification to admin channel for user {user_id}")
        except Exception as e:
            logger.error(f"Error sending reminder notification to admin channel: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in send_reminder_to_user for user {user_id}: {e}")
        return False

def schedule_reminder(user_id, interview_date, interview_time):
    """Schedule a reminder for 1 hour before the interview"""
    try:
        # Parse the interview date and time
        date_obj = datetime.strptime(interview_date, '%Y-%m-%d')
        
        # Find the time slot index
        time_slot_index = None
        
        # Handle 2-hour bookings (e.g., "13:00 - 15:00")
        if " - " in interview_time and len(interview_time.split(" - ")) == 2:
            start_time = interview_time.split(" - ")[0]
            # Find the first slot that matches the start time
            for i, slot in enumerate(TIME_SLOTS):
                if slot.startswith(start_time):
                    time_slot_index = i
                    break
        else:
            # Handle 1-hour bookings (e.g., "13:00 - 14:00")
            for i, slot in enumerate(TIME_SLOTS):
                if slot == interview_time:
                    time_slot_index = i
                    break
        
        if time_slot_index is None:
            logger.error(f"Could not find time slot index for {interview_time}")
            return False
        
        # Calculate reminder time (1 hour before interview start)
        if time_slot_index < 3:  # Morning slots (09:00, 10:00, 11:00)
            reminder_hour = 8 + time_slot_index  # 08:00, 09:00, 10:00
        elif time_slot_index == 3:  # Lunch slot (12:00)
            reminder_hour = 11  # 11:00
        elif time_slot_index == 4:  # After lunch slot (13:00)
            reminder_hour = 12  # 12:00
        else:  # Afternoon slots (14:00, 15:00, 16:00)
            reminder_hour = 13 + (time_slot_index - 5)  # 13:00, 14:00, 15:00
        
        # Create reminder time with proper timezone handling
        reminder_time = date_obj.replace(hour=reminder_hour, minute=0, second=0, microsecond=0)
        
        # Check if reminder time is in the past
        current_time = datetime.now()
        if reminder_time <= current_time:
            logger.warning(f"Reminder time {reminder_time} is in the past for user {user_id}, skipping")
            return False
        
        # Add Moscow timezone info
        moscow_tz = pytz.timezone('Europe/Moscow')
        reminder_time = moscow_tz.localize(reminder_time)
        
        # Schedule the reminder
        job_id = f"reminder_{user_id}_{interview_date}_{time_slot_index}"
        
        # Remove existing job if it exists
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Removed existing reminder job {job_id}")
        except Exception as remove_error:
            logger.debug(f"No existing job to remove for {job_id}: {remove_error}")
        
        # Add new job with better error handling
        try:
            scheduler.add_job(
                func=send_reminder_to_user,
                trigger='date',
                run_date=reminder_time,
                args=[user_id, interview_date, interview_time],
                id=job_id,
                replace_existing=True,
                misfire_grace_time=None  # Don't skip if missed
            )
            
            logger.info(f"Reminder scheduled for user {user_id} on {interview_date} at {reminder_time} (job_id: {job_id})")
            return True
            
        except Exception as add_error:
            logger.error(f"Failed to add reminder job for user {user_id}: {add_error}")
            return False
        
    except Exception as e:
        logger.error(f"Error scheduling reminder for user {user_id}: {e}")
        return False

def cancel_reminder(user_id, interview_date, time_slot_index):
    """Cancel a scheduled reminder"""
    try:
        job_id = f"reminder_{user_id}_{interview_date}_{time_slot_index}"
        scheduler.remove_job(job_id)
        logger.info(f"Reminder cancelled for user {user_id} on {interview_date}")
        return True
    except Exception as e:
        logger.error(f"Error cancelling reminder for user {user_id}: {e}")
        return False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_available_dates():
    """Get available dates starting from today (weekdays only)"""
    available_dates = []
    current_date = datetime.now()
    
    # Start from today and find the next 5 weekdays
    date_count = 0
    while date_count < 5:
        # Check if current date is a weekday (Monday = 0, Sunday = 6)
        if current_date.weekday() < 5:  # Monday to Friday
            # Only add today if there are still available time slots
            if current_date.date() == datetime.now().date():
                # Check if there are any available time slots for today
                has_available_slots = False
                for i in range(len(TIME_SLOTS)):
                    if not is_time_slot_in_past(current_date.strftime('%Y-%m-%d'), i):
                        has_available_slots = True
                        break
                if has_available_slots:
                    available_dates.append(current_date.strftime('%Y-%m-%d'))
                    date_count += 1
            else:
                available_dates.append(current_date.strftime('%Y-%m-%d'))
                date_count += 1
        current_date += timedelta(days=1)
    
    return available_dates

def get_next_week_dates():
    """Get next week's dates (Thursday, Friday, Monday, Tuesday, Wednesday)"""
    next_week_dates = []
    
    # Find next Thursday
    current_date = datetime.now()
    days_until_thursday = (3 - current_date.weekday()) % 7  # Thursday is weekday 3
    if days_until_thursday == 0:  # If today is Thursday, get next Thursday
        days_until_thursday = 7
    
    next_thursday = current_date + timedelta(days=days_until_thursday)
    
    # Add next week's dates in order: Thursday, Friday, Monday, Tuesday, Wednesday
    next_week_dates.append(next_thursday.strftime('%Y-%m-%d'))  # Thursday
    next_week_dates.append((next_thursday + timedelta(days=1)).strftime('%Y-%m-%d'))  # Friday
    next_week_dates.append((next_thursday + timedelta(days=4)).strftime('%Y-%m-%d'))  # Monday
    next_week_dates.append((next_thursday + timedelta(days=5)).strftime('%Y-%m-%d'))  # Tuesday
    next_week_dates.append((next_thursday + timedelta(days=6)).strftime('%Y-%m-%d'))  # Wednesday
    
    return next_week_dates

def get_next_week_2_dates():
    """Get the week after next week's dates (Thursday, Friday, Monday, Tuesday, Wednesday)"""
    next_week_2_dates = []
    
    # Find next Thursday
    current_date = datetime.now()
    days_until_thursday = (3 - current_date.weekday()) % 7  # Thursday is weekday 3
    if days_until_thursday == 0:  # If today is Thursday, get next Thursday
        days_until_thursday = 7
    
    next_thursday = current_date + timedelta(days=days_until_thursday)
    
    # Add the week after next week's dates (7 days later)
    next_week_2_dates.append((next_thursday + timedelta(days=7)).strftime('%Y-%m-%d'))  # Thursday
    next_week_2_dates.append((next_thursday + timedelta(days=8)).strftime('%Y-%m-%d'))  # Friday
    next_week_2_dates.append((next_thursday + timedelta(days=11)).strftime('%Y-%m-%d'))  # Monday
    next_week_2_dates.append((next_thursday + timedelta(days=12)).strftime('%Y-%m-%d'))  # Tuesday
    next_week_2_dates.append((next_thursday + timedelta(days=13)).strftime('%Y-%m-%d'))  # Wednesday
    
    return next_week_2_dates

def format_date_for_display(date, include_availability=True, mentor_id=None):
    """Format date as DD.MM day_name with optional availability status"""
    base_format = f"{date.strftime('%d.%m')} {DAY_NAMES[date.weekday()]}"
    
    if include_availability and mentor_id:
        date_str = date.strftime('%Y-%m-%d')
        availability = get_date_availability_status(date_str, mentor_id)
        return f"{base_format} ({availability})"
    else:
        return base_format

def format_date_for_callback(date):
    """Format date for callback data"""
    return date.strftime('%Y-%m-%d')

def get_russian_plural_form(number, one_form, few_form, many_form):
    """Get correct Russian plural form based on number"""
    if number % 10 == 1 and number % 100 != 11:
        return one_form
    elif 2 <= number % 10 <= 4 and (number % 100 < 10 or number % 100 >= 20):
        return few_form
    else:
        return many_form

def get_date_availability_status(selected_date, mentor_id=None):
    """Get availability status for a specific date and mentor"""
    try:
        # Count total slots for this date
        total_slots = len(TIME_SLOTS)
        available_slots = 0
        booked_slots = 0
        
        # Check each time slot
        for i in range(total_slots):
            # Check if slot is in the past
            if is_time_slot_in_past(selected_date, i):
                continue  # Skip past slots
            
            # Check if slot is booked for the specific mentor
            mentor_slot_key = f"{selected_date}_{mentor_id}_{i}"
            booking_key_2h = f"{selected_date}_{mentor_id}_{i}_2h"
            
            # Check if slot is blocked by a 2-hour booking from previous slot
            is_blocked_by_2h = False
            if i > 0:  # Check if previous slot has a 2-hour booking that extends to this slot
                prev_booking_key_2h = f"{selected_date}_{mentor_id}_{i-1}_2h"
                if prev_booking_key_2h in interview_bookings:
                    is_blocked_by_2h = True
            
            if mentor_slot_key in interview_bookings or booking_key_2h in interview_bookings or is_blocked_by_2h:
                booked_slots += 1
            else:
                available_slots += 1
        
        # Determine status with correct Russian plural forms
        if available_slots == 0:
            return "все места заняты"
        elif booked_slots == 0:
            return "все места свободны"
        else:
            # Use correct plural form for "место"
            place_form = get_russian_plural_form(available_slots, "место", "места", "мест")
            return f"{available_slots} {place_form} есть"
            
    except Exception as e:
        logger.error(f"Error calculating availability for {selected_date} mentor {mentor_id}: {e}")
        return "ошибка"

# ============================================================================
# BOOKING CONFLICT PREVENTION
# ============================================================================

def is_time_slot_available(selected_date, time_slot_index):
    """Check if a time slot is available for booking"""
    # Check if time slot is in the past
    if is_time_slot_in_past(selected_date, time_slot_index):
        return False
    
    # Check if already booked
    booking_key = f"{selected_date}_{time_slot_index}"
    return booking_key not in interview_bookings

def is_time_slot_in_past(selected_date, time_slot_index):
    """Check if a time slot is in the past"""
    try:
        # Parse the selected date
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        
        # Get current date and time
        current_datetime = datetime.now()
        
        # If the date is in the past, the time slot is unavailable
        if date_obj.date() < current_datetime.date():
            return True
        
        # If it's today, check the specific time
        if date_obj.date() == current_datetime.date():
            # Get the start time of the time slot
            time_slot = TIME_SLOTS[time_slot_index]
            start_time_str = time_slot.split(' - ')[0]  # Get "09:00" from "09:00 - 10:00"
            
            # Parse the start time
            slot_start_time = datetime.strptime(f"{selected_date} {start_time_str}", '%Y-%m-%d %H:%M')
            
            # If current time is past the slot start time, it's unavailable
            if current_datetime > slot_start_time:
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking if time slot is in past: {e}")
        return True  # If there's an error, assume it's unavailable

def get_booked_slots_for_date(selected_date):
    """Get list of booked time slots for a specific date"""
    booked_slots = []
    for booking_key, booking_data in interview_bookings.items():
        if booking_data['date'] == selected_date:
            time_slot_index = booking_data['time_slot_index']
            booked_slots.append(time_slot_index)
    return booked_slots



# ============================================================================
# BOT COMMANDS AND HANDLERS
# ============================================================================

def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    try:
        user = update.effective_user
        logger.info(f"Start command received from user {user.id} ({user.username})")
        
        # Register user if new
        is_new_user = register_user_if_new(user)
        
        # Check if user has a permanent mentor
        permanent_mentor = get_user_permanent_mentor(user.id)
        
        if permanent_mentor is None:
            # User needs to choose a permanent mentor first
            welcome_text = (
                f"Привет, {user.first_name}! 👋\n\n"
                f"Добро пожаловать в систему записи на собеседование!\n\n"
                f"🎯 Сначала выберите вашего основного ментора:\n"
                f"Этот ментор будет вашим постоянным наставником."
            )
            
            # Create mentor selection buttons
            keyboard = []
            for mentor_id, mentor_info in MENTORS.items():
                button_text = f"👤 {mentor_info['name']} {mentor_info['username']}"
                callback_data = f"choose_mentor_{mentor_id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(welcome_text, reply_markup=reply_markup)
            logger.info("Mentor selection request sent to new user")
            return
        
        # User has a permanent mentor, show normal welcome
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            f"Добро пожаловать в систему записи на собеседование!\n\n"
            f"📅 Выберите удобную дату для собеседования:"
        )
    
        # Get available dates
        available_dates = get_available_dates()
    
                # Create inline keyboard with date buttons
        keyboard = []
        for date_str in available_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Get user's permanent mentor for availability display
            user = update.effective_user
            permanent_mentor = get_user_permanent_mentor(user.id)
            formatted_date = format_date_for_display(date_obj, True, permanent_mentor)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        # Add "Следующая неделя→" button
        keyboard.append([InlineKeyboardButton("Следующая неделя→", callback_data="next_week")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Create outline keyboard with main buttons
        outline_keyboard = [
            ["Мои собеседования"],
            ["Профиль"]
        ]
        outline_markup = ReplyKeyboardMarkup(outline_keyboard, resize_keyboard=True, one_time_keyboard=False)
    
        # Create outline keyboard with main buttons
        outline_keyboard = [
            ["Мои собеседования"],
            ["Профиль"]
        ]
        outline_markup = ReplyKeyboardMarkup(outline_keyboard, resize_keyboard=True, one_time_keyboard=False)
        
        # Send message with both inline and outline keyboards
        update.message.reply_text(welcome_text, reply_markup=reply_markup)
        
        # Send outline keyboard in a separate message
        update.message.reply_text("Используйте кнопки ниже для навигации:", reply_markup=outline_markup)
        
        logger.info("Welcome message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def handle_next_week(update: Update, context: CallbackContext):
    """Handle next week button click"""
    try:
        query = update.callback_query
        query.answer()
        
        # Get next week's dates
        next_week_dates = get_next_week_dates()
        
        # Create message text
        message_text = "📅 **Следующая неделя:**\n\nВыберите удобную дату:"
        
        # Create inline keyboard with next week's date buttons
        keyboard = []
        for date_str in next_week_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Get user's permanent mentor for availability display
            user = update.effective_user
            permanent_mentor = get_user_permanent_mentor(user.id)
            formatted_date = format_date_for_display(date_obj, True, permanent_mentor)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        # Add navigation buttons
        keyboard.append([
            InlineKeyboardButton("← Назад", callback_data="back_to_dates"),
            InlineKeyboardButton("→ Следующая", callback_data="next_week_2")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        logger.info("Next week dates displayed successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_next_week: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_next_week_2(update: Update, context: CallbackContext):
    """Handle next week 2 button click"""
    try:
        query = update.callback_query
        query.answer()
        
        # Get the week after next week's dates
        next_week_2_dates = get_next_week_2_dates()
        
        # Create message text
        message_text = "📅 **Через неделю:**\n\nВыберите удобную дату:"
        
        # Create inline keyboard with next week 2's date buttons
        keyboard = []
        for date_str in next_week_2_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Get user's permanent mentor for availability display
            user = update.effective_user
            permanent_mentor = get_user_permanent_mentor(user.id)
            formatted_date = format_date_for_display(date_obj, True, permanent_mentor)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        # Add back button only (no more weeks after this)
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="next_week")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        logger.info("Next week 2 dates displayed successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_next_week_2: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_mentor_choice(update: Update, context: CallbackContext):
    """Handle mentor choice for new users"""
    try:
        query = update.callback_query
        query.answer()
        
        # Extract mentor ID from callback data
        callback_data = query.data
        if not callback_data.startswith('choose_mentor_'):
            return
        
        mentor_id = callback_data.replace('choose_mentor_', '')
        user = update.effective_user
        
        logger.info(f"Mentor choice callback received: {callback_data} from user {user.id}")
        
        # Set the user's permanent mentor
        set_user_permanent_mentor(user.id, mentor_id)
        
        # Get mentor info for display
        mentor_info = MENTORS[mentor_id]
        
        # Show confirmation and then the normal welcome
        confirmation_text = (
            f"✅ Отлично! Ваш основной ментор:\n"
            f"👤 {mentor_info['name']} {mentor_info['username']}\n\n"
            f"Теперь вы можете записываться на собеседования!"
        )
        
        # Get available dates
        available_dates = get_available_dates()
        
        # Create inline keyboard with date buttons
        keyboard = []
        for date_str in available_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj, True, mentor_id)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        # Add profile button
        keyboard.append([InlineKeyboardButton("👤 Мой профиль", callback_data="profile")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text=confirmation_text, reply_markup=reply_markup)
        
        # Send outline keyboard
        outline_keyboard = [
            ["Мои собеседования"],
            ["Профиль"]
        ]
        outline_markup = ReplyKeyboardMarkup(outline_keyboard, resize_keyboard=True, one_time_keyboard=False)
        query.message.reply_text("Используйте кнопки ниже для навигации:", reply_markup=outline_markup)
        
        logger.info(f"Mentor {mentor_id} assigned to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in handle_mentor_choice: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_date_selection(update: Update, context: CallbackContext):
    """Handle date selection callback"""
    try:
        query = update.callback_query
        query.answer()
    
        # Extract date from callback data
        callback_data = query.data
        if not callback_data.startswith('date_'):
            return
        
        selected_date = callback_data.replace('date_', '')
        user = update.effective_user
        logger.info(f"Date selection callback received: {callback_data} from user {user.id}")
        
        # Get user's permanent mentor
        permanent_mentor = get_user_permanent_mentor(user.id)
        
        if not permanent_mentor:
            # User doesn't have a permanent mentor
            response_text = (
                f"📅 Выбрана дата: {format_date_for_display(datetime.strptime(selected_date, '%Y-%m-%d'), False)}\n\n"
                f"❌ У вас не выбран основной ментор.\n\n"
                f"Сначала выберите основного ментора в профиле."
            )
            keyboard = [[InlineKeyboardButton("👤 Мой профиль", callback_data="profile")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=response_text, reply_markup=reply_markup)
            return
        
        # Check if mentor is available for this date
        mentor_availability = get_mentor_availability(permanent_mentor, selected_date)
        if mentor_availability <= 0:
            response_text = (
                f"📅 Выбрана дата: {format_date_for_display(datetime.strptime(selected_date, '%Y-%m-%d'), False)}\n\n"
                f"❌ Ваш ментор недоступен на эту дату.\n\n"
                f"Попробуйте выбрать другую дату."
            )
            keyboard = [[InlineKeyboardButton("← Назад к датам", callback_data="back_to_dates")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=response_text, reply_markup=reply_markup)
            return
        
        # Get available time slots for this mentor and date
        available_slots = []
        for i, time_slot in enumerate(TIME_SLOTS):
            # Check if this time slot is available for this mentor
            mentor_slot_key = f"{selected_date}_{permanent_mentor}_{i}"
            booking_key_2h = f"{selected_date}_{permanent_mentor}_{i}_2h"
            
            # Check if slot is blocked by a 2-hour booking
            is_blocked_by_2h = False
            if i > 0:  # Check if previous slot has a 2-hour booking that extends to this slot
                prev_booking_key_2h = f"{selected_date}_{permanent_mentor}_{i-1}_2h"
                if prev_booking_key_2h in interview_bookings:
                    is_blocked_by_2h = True
            
            # Check if slot is available for 1-hour booking
            is_available_1h = (mentor_slot_key not in interview_bookings and 
                             booking_key_2h not in interview_bookings and 
                             not is_blocked_by_2h and 
                             not is_time_slot_in_past(selected_date, i))
            
            # Check if slot is available for 2-hour booking (need current + next slot)
            is_available_2h = False
            if i < len(TIME_SLOTS) - 1:  # Not the last slot
                next_mentor_slot_key = f"{selected_date}_{permanent_mentor}_{i + 1}"
                next_booking_key_2h = f"{selected_date}_{permanent_mentor}_{i + 1}_2h"
                is_available_2h = (mentor_slot_key not in interview_bookings and 
                                 next_mentor_slot_key not in interview_bookings and
                                 booking_key_2h not in interview_bookings and
                                 next_booking_key_2h not in interview_bookings and
                                 not is_blocked_by_2h and
                                 not is_time_slot_in_past(selected_date, i) and
                                 not is_time_slot_in_past(selected_date, i + 1))
            
            # Show slot if available for either 1h or 2h booking
            if is_available_1h or is_available_2h:
                available_slots.append((i, time_slot))
        
        if not available_slots:
            response_text = (
                f"📅 Выбрана дата: {format_date_for_display(datetime.strptime(selected_date, '%Y-%m-%d'), False)}\n\n"
                f"❌ У вашего ментора нет свободного времени на эту дату.\n\n"
                f"Попробуйте выбрать другую дату."
            )
            keyboard = [[InlineKeyboardButton("← Назад к датам", callback_data="back_to_dates")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(text=response_text, reply_markup=reply_markup)
            return
        
        # Create time slot buttons
        keyboard = []
        for i, time_slot in available_slots:
            button_text = f"✅ {time_slot}"
            callback_data = f"time_{selected_date}_{permanent_mentor}_{i}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("← Назад к датам", callback_data="back_to_dates")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format date for display
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
        # Get mentor info for display
        mentor_info = MENTORS[permanent_mentor]
        
        response_text = (
            f"📅 Дата: {formatted_date}\n"
            f"👤 Ментор: {mentor_info['name']} {mentor_info['username']}\n\n"
            f"⏰ Выберите удобное время:"
        )
        
        query.edit_message_text(text=response_text, reply_markup=reply_markup)
        logger.info("Time slots sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_date_selection: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")



def handle_time_selection(update: Update, context: CallbackContext):
    """Handle time selection callback"""
    try:
        query = update.callback_query
        query.answer()
    
        # Extract data from callback
        callback_data = query.data
        if not callback_data.startswith('time_'):
            return
        
        # Handle mentor IDs that contain underscores (e.g., mentor_1, mentor_2)
        parts = callback_data.split('_')
        if len(parts) < 5:  # Need at least: time, date, mentor, id, time_slot_index
            return
        
        selected_date = parts[1]
        # Reconstruct mentor_id from parts
        mentor_id = f"{parts[2]}_{parts[3]}"
        time_slot_index = int(parts[4])
        selected_time = TIME_SLOTS[time_slot_index]
        user = update.effective_user
        
        logger.info(f"Time selection callback received: {callback_data} from user {user.id}")
        
        # Check if time slot is in the past
        if is_time_slot_in_past(selected_date, time_slot_index):
            query.edit_message_text("❌ Это время уже прошло. Пожалуйста, выберите другое время.")
            return
        
        # Check if slot is still available
        mentor_slot_key = f"{selected_date}_{mentor_id}_{time_slot_index}"
        if mentor_slot_key in interview_bookings:
            query.edit_message_text("❌ Это время уже занято. Пожалуйста, выберите другое время.")
            return
        
        # Format date for display
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
            
        # Get mentor info
        mentor_info = MENTORS[mentor_id]
        
        # Create duration selection message
        duration_text = (
            f"📋 **Выбор длительности собеседования**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {selected_time}\n"
            f"👤 Ментор: {mentor_info['name']} {mentor_info['username']}\n\n"
            f"Выберите длительность собеседования:"
        )
        
        # Create duration selection buttons
        keyboard = [
            [
                InlineKeyboardButton("⏰ 1 час", callback_data=f"duration_1h_{selected_date}_{mentor_id}_{time_slot_index}"),
                InlineKeyboardButton("⏰ 1.5-2 часа", callback_data=f"duration_2h_{selected_date}_{mentor_id}_{time_slot_index}")
            ],
            [InlineKeyboardButton("← Назад к времени", callback_data=f"date_{selected_date}")]
        ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=duration_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info("Duration selection sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_time_selection: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_duration_selection(update: Update, context: CallbackContext):
    """Handle duration selection callback"""
    try:
        query = update.callback_query
        query.answer()
    
        # Extract data from callback
        callback_data = query.data
        if not callback_data.startswith('duration_'):
            return
    
        # Handle mentor IDs that contain underscores (e.g., mentor_1, mentor_2)
        parts = callback_data.split('_')
        if len(parts) < 6:  # Need at least: duration, 1h/2h, date, mentor, id, time_slot_index
            return
    
        duration = parts[1]  # 1h or 2h
        selected_date = parts[2]
        # Reconstruct mentor_id from parts
        mentor_id = f"{parts[3]}_{parts[4]}"
        time_slot_index = int(parts[5])
        selected_time = TIME_SLOTS[time_slot_index]
        user = update.effective_user
        
        logger.info(f"Duration selection callback received: {callback_data} from user {user.id}")
        
        # Check if time slot is in the past
        if is_time_slot_in_past(selected_date, time_slot_index):
            query.edit_message_text("❌ Это время уже прошло. Пожалуйста, выберите другое время.")
            return
    
        # Check if slot is still available
        mentor_slot_key = f"{selected_date}_{mentor_id}_{time_slot_index}"
        if mentor_slot_key in interview_bookings:
            query.edit_message_text("❌ Это время уже занято. Пожалуйста, выберите другое время.")
            return
    
        # For 2-hour bookings, check if next slot is available
        if duration == "2h":
            next_time_slot_index = time_slot_index + 1
            if next_time_slot_index >= len(TIME_SLOTS):
                query.edit_message_text("❌ Недостаточно времени для 2-часового собеседования. Выберите более раннее время.")
                return
            
            next_mentor_slot_key = f"{selected_date}_{mentor_id}_{next_time_slot_index}"
            if next_mentor_slot_key in interview_bookings:
                query.edit_message_text("❌ Следующий час уже занят. Выберите 1 час или другое время.")
                return
    
        # Format date for display
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
            
        # Get mentor info
        mentor_info = MENTORS[mentor_id]
        permanent_mentor = get_user_permanent_mentor(user.id)
        is_one_time_change = mentor_id != permanent_mentor
    
        # Create confirmation message
        mentor_type = "🔄 Временная замена" if is_one_time_change else "👤 Постоянный ментор"
    
        if duration == "1h":
            duration_text = "1 час"
            time_range = selected_time
        else:  # 2h
            next_time = TIME_SLOTS[time_slot_index + 1]
            duration_text = "1.5-2 часа"
            time_range = f"{selected_time.split(' - ')[0]} - {next_time.split(' - ')[1]}"
    
        # Store booking details in context for company question
        context.user_data['pending_booking'] = {
            'date': selected_date,
            'mentor_id': mentor_id,
            'time_slot_index': time_slot_index,
            'duration': duration,
            'time_range': time_range,
            'duration_text': duration_text,
            'mentor_type': mentor_type,
            'formatted_date': formatted_date
        }
        
        company_text = (
            f"📋 **Информация о собеседовании**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {time_range}\n"
            f"⏱️ Длительность: {duration_text}\n"
            f"👤 Ментор: {mentor_info['name']} {mentor_info['username']}\n"
            f"📋 Тип: {mentor_type}\n\n"
            f"🏢 **Укажите вашу компанию:**"
        )
        
        # Create back button
        keyboard = [
            [InlineKeyboardButton("← Назад", callback_data=f"date_{selected_date}")]
        ]
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=company_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info("Company question sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_duration_selection: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_confirmation(update: Update, context: CallbackContext):
    """Handle booking confirmation"""
    try:
        query = update.callback_query
        query.answer()
    
        # Extract data from callback
        callback_data = query.data
        user = update.effective_user
        
        # Check if this is a confirmation with company
        if callback_data == "confirm_with_company":
            if 'pending_booking' not in context.user_data:
                query.edit_message_text("❌ Ошибка: данные бронирования не найдены. Попробуйте еще раз.")
                return
            
            pending_booking = context.user_data['pending_booking']
            selected_date = pending_booking['date']
            mentor_id = pending_booking['mentor_id']
            time_slot_index = pending_booking['time_slot_index']
            duration = pending_booking['duration']
            selected_time = TIME_SLOTS[time_slot_index]
            company_name = pending_booking.get('company', 'Не указана')
        else:
            # Handle old confirmation format (for backward compatibility)
            if not callback_data.startswith('confirm_'):
                return
            
            # Handle mentor IDs that contain underscores (e.g., mentor_1, mentor_2)
            parts = callback_data.split('_')
            if len(parts) < 6:  # Need at least: confirm, date, mentor, id, time_slot_index, duration
                return
            
            selected_date = parts[1]
            # Reconstruct mentor_id from parts
            mentor_id = f"{parts[2]}_{parts[3]}"
            time_slot_index = int(parts[4])
            duration = parts[5]  # 1h or 2h
            selected_time = TIME_SLOTS[time_slot_index]
            company_name = 'Не указана'  # Default for old format
        
        logger.info(f"Confirmation callback received: {callback_data} from user {user.id}")
        
        # Check if slot is still available
        mentor_slot_key = f"{selected_date}_{mentor_id}_{time_slot_index}"
        if mentor_slot_key in interview_bookings:
            query.edit_message_text("❌ Это время уже занято. Пожалуйста, выберите другое время.")
            return
        
        # For 2-hour bookings, check if next slot is still available
        if duration == "2h":
            next_time_slot_index = time_slot_index + 1
            if next_time_slot_index >= len(TIME_SLOTS):
                query.edit_message_text("❌ Недостаточно времени для 2-часового собеседования. Выберите более раннее время.")
                return
            
            next_mentor_slot_key = f"{selected_date}_{mentor_id}_{next_time_slot_index}"
            if next_mentor_slot_key in interview_bookings:
                query.edit_message_text("❌ Следующий час уже занят. Выберите 1 час или другое время.")
                return
        
        # Get mentor info
        mentor_info = MENTORS[mentor_id]
        
        if duration == "1h":
            duration_text = "1 час"
            time_range = selected_time
            booking_data = {
                'user_id': user.id,
                'user_info': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name
                },
                'date': selected_date,
                'time': selected_time,
                'time_slot_index': time_slot_index,
                'mentor_id': mentor_id,
                'mentor_name': mentor_info['name'],
                'duration': '1h',
                'company': company_name,
                'booked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            # Store 1-hour booking
            add_booking_to_database(mentor_slot_key, booking_data)
            booking_keys = [mentor_slot_key]
        else:  # 2h
            next_time = TIME_SLOTS[time_slot_index + 1]
            duration_text = "1.5-2 часа"
            time_range = f"{selected_time.split(' - ')[0]} - {next_time.split(' - ')[1]}"
            
            # Create special 2-hour booking key
            booking_key_2h = f"{selected_date}_{mentor_id}_{time_slot_index}_2h"
            
            booking_data = {
                'user_id': user.id,
                'user_info': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name
                },
                'date': selected_date,
                'time': time_range,
                'time_slot_index': time_slot_index,
                'mentor_id': mentor_id,
                'mentor_name': mentor_info['name'],
                'duration': '2h',
                'company': company_name,
                'booked_slots': [time_slot_index, time_slot_index + 1],
                'booked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            # Store 2-hour booking with special key
            add_booking_to_database(booking_key_2h, booking_data)
            booking_keys = [booking_key_2h]
        
        logger.info(f"Booking stored: {booking_keys} for user {user.id}")
        
        # Increment user's total bookings count
        increment_user_total_bookings(user.id)
        
        # Schedule reminder
        schedule_reminder(user.id, selected_date, time_range)
        logger.info(f"Reminder scheduled for user {user.id}")
        
        # Send notification to admin channel
        try:
            send_mentor_booking_log(
                booking_data['user_info'],
                selected_date,
                time_range,
                mentor_info['name'],
                company_name
            )
            logger.info("Mentor booking notification sent to private channel successfully")
        except Exception as e:
            logger.error(f"Error sending mentor booking notification to channel: {e}")
        
        # Send notification to mentor
        try:
            mentor_user_id = mentor_info.get('user_id')
            if mentor_user_id:
                # Format date for display
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj)
                
                # Get student info
                student_name = user.first_name
                student_username = user.username
                student_text = f"{student_name}"
                if student_username:
                    student_text += f" @{student_username}"
                
                # Create notification message for mentor
                mentor_notification = (
                    f"📅 **Новое собеседование**\n\n"
                    f"Студент {student_text} записался на собеседование:\n\n"
                    f"📅 Дата: {formatted_date}\n"
                    f"⏰ Время: {time_range}\n"
                    f"⏱️ Длительность: {duration_text}\n"
                    f"🏢 Компания: {company_name}\n\n"
                    f"Используйте кнопку 'Мои собеседования' для просмотра всех записей."
                )
                
                # Send notification to mentor
                context.bot.send_message(
                    chat_id=mentor_user_id,
                    text=mentor_notification,
                    parse_mode='Markdown'
                )
                logger.info(f"Student booking notification sent to mentor {mentor_user_id}")
                
        except Exception as e:
            logger.error(f"Error sending student booking notification to mentor: {e}")
        
        # Send confirmation message
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
        success_text = (
            f"✅ **Запись подтверждена!**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {time_range}\n"
            f"⏱️ Длительность: {duration_text}\n"
            f"🏢 Компания: {company_name}\n\n"
            f"🔔 За 1 час до собеседования вы получите напоминание.\n\n"
            f"Используйте /mybookings для просмотра ваших записей.\n"
            f"Используйте /help для получения справки."
        )
        
        # Clean up pending booking data
        if 'pending_booking' in context.user_data:
            del context.user_data['pending_booking']
        
        query.edit_message_text(text=success_text, parse_mode='Markdown')
        logger.info("Booking confirmation sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_confirmation: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_cancel_company(update: Update, context: CallbackContext):
    """Handle cancellation of company input"""
    try:
        query = update.callback_query
        query.answer()
        
        # Clean up pending booking data
        if 'pending_booking' in context.user_data:
            del context.user_data['pending_booking']
        
        query.edit_message_text("❌ Запись отменена.")
        logger.info("Company input cancelled")
        
    except Exception as e:
        logger.error(f"Error in handle_cancel_company: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_booked_slot(update: Update, context: CallbackContext):
    """Handle clicks on booked slots"""
    try:
        query = update.callback_query
        query.answer()
        
        query.edit_message_text("❌ Это время уже занято. Пожалуйста, выберите другое время.")
        
    except Exception as e:
        logger.error(f"Error in handle_booked_slot: {e}")

def handle_back_to_dates(update: Update, context: CallbackContext):
    """Handle back to dates button"""
    try:
        query = update.callback_query
        query.answer()
        
        # Get user's permanent mentor
        user = update.effective_user
        permanent_mentor = get_user_permanent_mentor(user.id)
        
        # Get available dates
        available_dates = get_available_dates()
        
        # Create inline keyboard with date buttons
        keyboard = []
        for date_str in available_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj, True, permanent_mentor)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        # Add "Следующая неделя→" button
        keyboard.append([InlineKeyboardButton("Следующая неделя→", callback_data="next_week")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"📅 Выберите удобную дату для собеседования:"
        )
        
        query.edit_message_text(welcome_text, reply_markup=reply_markup)
        
        # Send outline buttons message
        outline_keyboard = [
            ["Мои собеседования"],
            ["Профиль"]
        ]
        outline_markup = ReplyKeyboardMarkup(outline_keyboard, resize_keyboard=True, one_time_keyboard=False)
        query.message.reply_text("", reply_markup=outline_markup)
        
        logger.info("Back to dates sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_back_to_dates: {e}")

def handle_profile_callback(update: Update, context: CallbackContext):
    """Handle profile button callback"""
    try:
        query = update.callback_query
        query.answer()
        
        user = update.effective_user
        
        # Get user's booking statistics
        user_bookings = []
        upcoming_interviews = 0
        
        # Get total bookings made by user (from user database)
        total_bookings_made = get_user_total_bookings(user.id)
        
        for booking_key, booking_data in interview_bookings.items():
            if booking_data['user_id'] == user.id:
                # Check if interview is in the past (both date and time)
                interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                current_date = datetime.now().date()
                
                # Check if the interview time has passed
                is_past = False
                if interview_date.date() < current_date:
                    is_past = True
                elif interview_date.date() == current_date:
                    # Check if the specific time slot has passed
                    time_slot_index = booking_data.get('time_slot_index', 0)
                    if is_time_slot_in_past(booking_data['date'], time_slot_index):
                        is_past = True
                
                # Only add upcoming interviews to the list
                if not is_past:
                    upcoming_interviews += 1
                    user_bookings.append(booking_data)
        
        # Create profile text
        profile_text = f"👤 **Профиль пользователя**\n\n"
        profile_text += f"**Основная информация:**\n"
        profile_text += f"• Имя: {user.first_name}\n"
        if user.username:
            profile_text += f"• Username: @{user.username}\n"
        profile_text += f"• ID: {user.id}\n"
        profile_text += f"• Дата регистрации: {get_user_registration_date(user.id)}\n"
        
        # Add mentor information
        permanent_mentor = get_user_permanent_mentor(user.id)
        if permanent_mentor:
            permanent_mentor_info = MENTORS[permanent_mentor]
            profile_text += f"• Постоянный ментор: {permanent_mentor_info['name']} {permanent_mentor_info['username']}\n"
        else:
            profile_text += f"• Постоянный ментор: ❌ Не выбран\n"
        
        profile_text += f"\n**Статистика собеседований:**\n"
        profile_text += f"• Всего записей: {total_bookings_made}\n"
        profile_text += f"• Предстоящих: {upcoming_interviews}\n"
        profile_text += f"• Отмененных: {total_bookings_made - upcoming_interviews}\n\n"
        
        if upcoming_interviews > 0:
            profile_text += f"**Ближайшие собеседования:**\n"
            for booking in user_bookings:
                formatted_date = format_date_for_display(datetime.strptime(booking['date'], '%Y-%m-%d'))
                profile_text += f"• {formatted_date} в {booking['time']}\n"
        
        # Add navigation buttons
        keyboard = [
            [InlineKeyboardButton("📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton("📅 Записаться", callback_data="back_to_dates")]
        ]
        
        # Add change mentor button for all users
        keyboard.append([InlineKeyboardButton("🔄 Сменить основного ментора", callback_data="change_mentor")])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="close_profile")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=profile_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info("Profile displayed successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_profile_callback: {e}")
        query.edit_message_text("Произошла ошибка при загрузке профиля.")

def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    try:
        user = update.effective_user
        
        help_text = (
            f"🤖 **Справка по боту**\n\n"
            f"**📋 Доступные команды:**\n"
            f"• `/start` - Записаться на собеседование\n"
            f"• `/profile` - Посмотреть ваш профиль и статистику\n"
            f"• `/mybookings` - Посмотреть ваши записи\n"
            f"• `/help` - Показать эту справку\n"
            f"• `/database` - Просмотр базы данных (только для админа)\n"
        )
        
        # Add admin commands for @yashonflame
        if user.id == 780202036:  # @yashonflame's user ID
            help_text += f"• `/all <текст>` - Отправить сообщение всем пользователям\n"
        
        help_text += (
            f"\n"
            f"**🔘 Кнопки навигации:**\n"
            f"• **Мои собеседования** - Посмотреть предстоящие собеседования с менторами\n"
            f"• **Профиль** - Посмотреть ваш профиль и статистику\n\n"
            f"**📅 Как записаться на собеседование:**\n"
            f"1. Нажмите `/start` или кнопку **Мои собеседования**\n"
            f"2. Выберите удобную дату\n"
            f"3. Выберите свободное время\n"
            f"4. Подтвердите запись\n\n"
            f"**👤 Ментор:**\n"
            f"• У каждого студента есть постоянный ментор\n"
            f"• Ментора можно сменить в профиле\n"
            f"• При записи автоматически используется ваш постоянный ментор\n\n"
            f"**⏰ Напоминания:**\n"
            f"За 1 час до собеседования вы получите автоматическое напоминание.\n\n"
            f"**❌ Отмена записи:**\n"
            f"• Нажмите кнопку **Мои собеседования**\n"
            f"• Выберите собеседование для отмены\n"
            f"• Нажмите кнопку **Отменить**\n\n"
            f"**💡 Подсказка:**\n"
            f"Используйте кнопки **Мои собеседования** и **Профиль** для быстрой навигации!"
        )
        
        update.message.reply_text(help_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in help_command: {e}")

def profile_command(update: Update, context: CallbackContext):
    """Handle /profile command"""
    try:
        user = update.effective_user
        logger.info(f"Profile command received from user {user.id} ({user.username})")
        
        # Get user's booking statistics
        user_bookings = []
        upcoming_interviews = 0
        
        # Get total bookings made by user (from user database)
        total_bookings_made = get_user_total_bookings(user.id)
        
        for booking_key, booking_data in interview_bookings.items():
            if booking_data['user_id'] == user.id:
                # Check if interview is in the past (both date and time)
                interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                current_date = datetime.now().date()
                
                # Check if the interview time has passed
                is_past = False
                if interview_date.date() < current_date:
                    is_past = True
                elif interview_date.date() == current_date:
                    # Check if the specific time slot has passed
                    time_slot_index = booking_data.get('time_slot_index', 0)
                    if is_time_slot_in_past(booking_data['date'], time_slot_index):
                        is_past = True
                
                # Only add upcoming interviews to the list
                if not is_past:
                    upcoming_interviews += 1
                    user_bookings.append(booking_data)
        
        # Create profile text
        profile_text = f"👤 **Профиль пользователя**\n\n"
        profile_text += f"**Основная информация:**\n"
        profile_text += f"• Имя: {user.first_name}\n"
        if user.username:
            profile_text += f"• Username: @{user.username}\n"
        profile_text += f"• ID: {user.id}\n"
        profile_text += f"• Дата регистрации: {get_user_registration_date(user.id)}\n"
        
        # Add mentor information
        permanent_mentor = get_user_permanent_mentor(user.id)
        if permanent_mentor:
            permanent_mentor_info = MENTORS[permanent_mentor]
            profile_text += f"• Постоянный ментор: {permanent_mentor_info['name']} {permanent_mentor_info['username']}\n"
            profile_text += f"• Смена ментора: {'❌ Использована' if has_used_one_time_change(user.id) else '✅ Доступна'}\n\n"
        else:
            profile_text += f"• Постоянный ментор: ❌ Не выбран\n"
            profile_text += f"• Смена ментора: ❌ Недоступно\n\n"
        
        profile_text += f"**Статистика собеседований:**\n"
        profile_text += f"• Всего записей: {total_bookings_made}\n"
        profile_text += f"• Предстоящих: {upcoming_interviews}\n"
        profile_text += f"• Отмененных: {total_bookings_made - upcoming_interviews}\n\n"
        
        if upcoming_interviews > 0:
            profile_text += f"**Ближайшие собеседования:**\n"
            for booking in user_bookings:
                formatted_date = format_date_for_display(datetime.strptime(booking['date'], '%Y-%m-%d'))
                profile_text += f"• {formatted_date} в {booking['time']}\n"
        
        # Add navigation buttons
        keyboard = [
            [InlineKeyboardButton("📋 Мои записи", callback_data="my_bookings")],
            [InlineKeyboardButton("📅 Записаться", callback_data="back_to_dates")]
        ]
        
        # Add change mentor button if user has a permanent mentor
        if permanent_mentor:
            keyboard.append([InlineKeyboardButton("🔄 Сменить основного ментора", callback_data="change_mentor")])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="close_profile")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in profile_command: {e}")
        update.message.reply_text("Произошла ошибка при загрузке профиля.")

def my_bookings(update: Update, context: CallbackContext):
    """Handle /mybookings command"""
    try:
        user = update.effective_user
    
        # Find user's bookings (only upcoming ones)
        user_bookings = []
        seen_bookings = set()  # To avoid duplicates
        
        for booking_key, booking_data in interview_bookings.items():
            if booking_data['user_id'] == user.id:
                # Check if the interview time has passed
                interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                current_date = datetime.now().date()
                
                is_past = False
                if interview_date.date() < current_date:
                    is_past = True
                elif interview_date.date() == current_date:
                    # Check if the specific time slot has passed
                    time_slot_index = booking_data.get('time_slot_index', 0)
                    if is_time_slot_in_past(booking_data['date'], time_slot_index):
                        is_past = True
                
                if not is_past:
                    # Create a unique identifier for the booking to avoid duplicates
                    booking_id = f"{booking_data['date']}_{booking_data['time']}_{booking_data.get('duration', '1h')}"
                    if booking_id not in seen_bookings:
                        seen_bookings.add(booking_id)
                        user_bookings.append((booking_key, booking_data))
    
        if not user_bookings:
            update.message.reply_text("У вас пока нет предстоящих записей на собеседование.")
            return
        
        # Create message with user's bookings
        bookings_text = "📋 **Ваши записи на собеседование:**\n\n"
        
        keyboard = []
        for booking_key, booking_data in user_bookings:
            date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj)
            
            # Add mentor information
            mentor_info = ""
            if 'mentor_id' in booking_data:
                mentor_id = booking_data['mentor_id']
                if mentor_id in MENTORS:
                    mentor_name = MENTORS[mentor_id]['name']
                    mentor_username = MENTORS[mentor_id]['username']
                    mentor_info = f" | 👤 {mentor_name} {mentor_username}"
            
            # Add duration information
            duration_info = ""
            if 'duration' in booking_data:
                if booking_data['duration'] == '1h':
                    duration_info = " | ⏱️ 1 час"
                elif booking_data['duration'] == '2h':
                    duration_info = " | ⏱️ 1.5-2 часа"
            
            bookings_text += f"📅 {formatted_date} | ⏰ {booking_data['time']}{mentor_info}{duration_info}\n"
            
            # Add cancel button for each booking
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ Отменить {formatted_date} {booking_data['time']}", 
                    callback_data=f"cancel_booking_{booking_key}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(bookings_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in my_bookings: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def handle_cancellation(update: Update, context: CallbackContext):
    """Handle booking cancellation"""
    try:
        query = update.callback_query
        query.answer()
        
        # Extract booking key from callback data
        callback_data = query.data
        if not callback_data.startswith('cancel_booking_'):
            return
        
        booking_key = callback_data.replace('cancel_booking_', '')
        
        if booking_key not in interview_bookings:
            query.edit_message_text("❌ Запись не найдена.")
            return
    
        # Get booking data
        booking_data = interview_bookings[booking_key]
        user_id = booking_data['user_id']
        selected_date = booking_data['date']
        selected_time = booking_data['time']
        time_slot_index = booking_data['time_slot_index']
        
        # Cancel the reminder
        cancel_reminder(user_id, selected_date, time_slot_index)
        
        # Remove the booking from database
        remove_booking_from_database(booking_key)
        
        # If this is a 2-hour booking, remove the special 2-hour booking key
        if booking_data.get('duration') == '2h':
            # The booking is already removed above, no need to remove additional slots
            # since 2-hour bookings now use a single special key
            logger.info(f"Removed 2-hour booking: {booking_key}")
        
        # Check if the person cancelling is a mentor
        cancelling_user = update.effective_user
        is_mentor_cancelling = is_user_mentor(cancelling_user.id)
        
        # Send notification to admin channel
        try:
            send_cancellation_log(
                booking_data['user_info'],
                selected_date,
                selected_time
            )
            logger.info("Cancellation notification sent to private channel successfully")
        except Exception as e:
            logger.error(f"Error sending cancellation notification to channel: {e}")
        
        # If mentor is cancelling, send notification to student
        if is_mentor_cancelling:
            try:
                mentor_info = MENTORS[get_mentor_id_by_user_id(cancelling_user.id)]
                mentor_name = mentor_info['name']
                mentor_username = mentor_info['username']
                
                # Format date for display
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj)
                
                # Create notification message for student
                student_notification = (
                    f"❌ **Собеседование отменено**\n\n"
                    f"Ментор {mentor_name} {mentor_username} отменил собеседование:\n\n"
                    f"📅 Дата: {formatted_date}\n"
                    f"⏰ Время: {selected_time}\n\n"
                    f"Пожалуйста, запишитесь на другое время."
                )
                
                # Send notification to student
                context.bot.send_message(
                    chat_id=user_id,
                    text=student_notification,
                    parse_mode='Markdown'
                )
                logger.info(f"Mentor cancellation notification sent to student {user_id}")
                
            except Exception as e:
                logger.error(f"Error sending mentor cancellation notification to student: {e}")
        
        # Send confirmation message
        query.edit_message_text("✅ Успешно удалено")
        logger.info(f"Booking cancelled: {booking_key}")
        
    except Exception as e:
        logger.error(f"Error in handle_cancellation: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_change_mentor(update: Update, context: CallbackContext):
    """Handle mentor change request"""
    try:
        query = update.callback_query
        query.answer()
        
        user = update.effective_user
        
        # Create mentor selection buttons
        keyboard = []
        for mentor_id, mentor_info in MENTORS.items():
            button_text = f"👤 {mentor_info['name']} {mentor_info['username']}"
            callback_data = f"change_to_mentor_{mentor_id}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("← Назад к профилю", callback_data="profile")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        change_text = (
            f"🔄 **Смена основного ментора**\n\n"
            f"Выберите нового основного ментора:"
        )
        
        query.edit_message_text(text=change_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in handle_change_mentor: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_change_to_mentor(update: Update, context: CallbackContext):
    """Handle mentor change confirmation"""
    try:
        query = update.callback_query
        query.answer()
        
        # Extract mentor ID from callback data
        callback_data = query.data
        if not callback_data.startswith('change_to_mentor_'):
            return
        
        mentor_id = callback_data.replace('change_to_mentor_', '')
        user = update.effective_user
        
        logger.info(f"Mentor change callback received: {callback_data} from user {user.id}")
        
        # Set the user's new permanent mentor
        set_user_permanent_mentor(user.id, mentor_id)
        
        # Get mentor info for display
        mentor_info = MENTORS[mentor_id]
        
        # Show confirmation
        confirmation_text = (
            f"✅ **Ментор успешно изменен!**\n\n"
            f"Ваш новый основной ментор:\n"
            f"👤 {mentor_info['name']} {mentor_info['username']}\n\n"
            f"Теперь вы можете записываться на собеседования с новым ментором."
        )
        
        # Add back to profile button
        keyboard = [[InlineKeyboardButton("👤 Назад к профилю", callback_data="profile")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text=confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info(f"Mentor changed to {mentor_id} for user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in handle_change_to_mentor: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_profile_navigation(update: Update, context: CallbackContext):
    """Handle profile navigation callbacks"""
    try:
        query = update.callback_query
        query.answer()
        
        callback_data = query.data
        
        if callback_data == "my_bookings":
            # Show user's bookings (same as "Мои собеседования")
            user = update.effective_user
            user_bookings = []
            seen_bookings = set()  # To avoid duplicates
            
            for booking_key, booking_data in interview_bookings.items():
                if booking_data['user_id'] == user.id:
                    # Check if interview is in the past (both date and time)
                    interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                    current_date = datetime.now().date()
                    
                    # Check if the interview time has passed
                    is_past = False
                    if interview_date.date() < current_date:
                        is_past = True
                    elif interview_date.date() == current_date:
                        # Check if the specific time slot has passed
                        time_slot_index = booking_data.get('time_slot_index', 0)
                        if is_time_slot_in_past(booking_data['date'], time_slot_index):
                            is_past = True
                    
                    # Only add if not past
                    if not is_past:
                        # Create a unique identifier for the booking to avoid duplicates
                        booking_id = f"{booking_data['date']}_{booking_data['time']}_{booking_data.get('duration', '1h')}"
                        if booking_id not in seen_bookings:
                            seen_bookings.add(booking_id)
                            user_bookings.append((booking_key, booking_data))
            
            if not user_bookings:
                response_text = (
                    "📅 **Мои собеседования**\n\n"
                    "У вас пока нет запланированных собеседований.\n\n"
                    "Используйте /start для записи на собеседование!"
                )
                query.edit_message_text(response_text, parse_mode='Markdown')
                return
            
            # Create response text with upcoming interviews
            response_text = "📅 **Мои собеседования**\n\n"
            
            for booking_key, booking_data in user_bookings:
                date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj)
                
                # Get mentor info (handle missing mentor_id)
                mentor_id = booking_data.get('mentor_id')
                if mentor_id and mentor_id in MENTORS:
                    mentor_info = MENTORS[mentor_id]
                    mentor_text = f"{mentor_info['name']} {mentor_info['username']}"
                else:
                    mentor_text = "Не указан"
                
                # Add duration information
                duration_text = ""
                if 'duration' in booking_data:
                    if booking_data['duration'] == '1h':
                        duration_text = " | ⏱️ 1 час"
                    elif booking_data['duration'] == '2h':
                        duration_text = " | ⏱️ 1.5-2 часа"
                
                response_text += (
                    f"📅 **{formatted_date}**\n"
                    f"⏰ Время: {booking_data['time']}{duration_text}\n"
                    f"👤 Ментор: {mentor_text}\n\n"
                )
            
            # Add cancel buttons for each booking
            keyboard = []
            for booking_key, booking_data in user_bookings:
                button_text = f"❌ Отменить {format_date_for_display(datetime.strptime(booking_data['date'], '%Y-%m-%d'), False)} {booking_data['time']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"cancel_booking_{booking_key}")])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("← Назад", callback_data="profile_outline")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif callback_data == "close_profile":
            # Close profile and return to main menu
            welcome_text = (
                f"Привет, {update.effective_user.first_name}! 👋\n\n"
                f"Добро пожаловать в систему записи на собеседование!\n\n"
                f"📅 Выберите удобную дату для собеседования:"
            )
            
            # Get available dates
            available_dates = get_available_dates()
            
            # Create inline keyboard with date buttons
            keyboard = []
            for date_str in available_dates:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                # Get user's permanent mentor for availability display
                user = update.effective_user
                permanent_mentor = get_user_permanent_mentor(user.id)
                formatted_date = format_date_for_display(date_obj, True, permanent_mentor)
                callback_data = f"date_{format_date_for_callback(date_obj)}"
                keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
            
            # Add profile button
            keyboard.append([InlineKeyboardButton("👤 Мой профиль", callback_data="profile")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(welcome_text, reply_markup=reply_markup)
            
    except Exception as e:
        logger.error(f"Error in handle_profile_navigation: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_my_interviews(update: Update, context: CallbackContext):
    """Handle 'Мои собеседования' outline button with filtering options"""
    try:
        user = update.effective_user
        
        # Check if user is a mentor
        is_mentor = is_user_mentor(user.id)
        
        # Get all upcoming bookings for the user with better validation
        all_bookings = []
        seen_bookings = set()  # To avoid duplicates
        
        if is_mentor:
            # For mentors: get all upcoming interviews assigned to them
            mentor_id = get_mentor_id_by_user_id(user.id)
            
            if not mentor_id:
                update.message.reply_text("❌ Ошибка: не удалось определить ваш ID ментора.")
                return
            
            for booking_key, booking_data in interview_bookings.items():
                try:
                    # Validate booking data
                    if not all(key in booking_data for key in ['date', 'time', 'mentor_id']):
                        logger.warning(f"Invalid booking data for key {booking_key}: missing required fields")
                        continue
                    
                    if booking_data.get('mentor_id') == mentor_id:
                        # Check if interview is in the past (both date and time)
                        interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                        current_date = datetime.now().date()
                        
                        # Check if the interview time has passed
                        is_past = False
                        if interview_date.date() < current_date:
                            is_past = True
                        elif interview_date.date() == current_date:
                            # Check if the specific time slot has passed
                            time_slot_index = booking_data.get('time_slot_index', 0)
                            if is_time_slot_in_past(booking_data['date'], time_slot_index):
                                is_past = True
                        
                        # Only add if not past
                        if not is_past:
                            # Create a unique identifier for the booking to avoid duplicates
                            booking_id = f"{booking_data['date']}_{booking_data['time']}_{booking_data.get('duration', '1h')}"
                            if booking_id not in seen_bookings:
                                seen_bookings.add(booking_id)
                                all_bookings.append((booking_key, booking_data))
                except Exception as booking_error:
                    logger.error(f"Error processing booking {booking_key}: {booking_error}")
                    continue
        else:
            # For students: get their own upcoming bookings
            for booking_key, booking_data in interview_bookings.items():
                try:
                    # Validate booking data
                    if not all(key in booking_data for key in ['date', 'time', 'user_id']):
                        logger.warning(f"Invalid booking data for key {booking_key}: missing required fields")
                        continue
                    
                    if booking_data['user_id'] == user.id:
                        # Check if interview is in the past (both date and time)
                        interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                        current_date = datetime.now().date()
                        
                        # Check if the interview time has passed
                        is_past = False
                        if interview_date.date() < current_date:
                            is_past = True
                        elif interview_date.date() == current_date:
                            # Check if the specific time slot has passed
                            time_slot_index = booking_data.get('time_slot_index', 0)
                            if is_time_slot_in_past(booking_data['date'], time_slot_index):
                                is_past = True
                        
                        # Only add if not past
                        if not is_past:
                            # Create a unique identifier for the booking to avoid duplicates
                            booking_id = f"{booking_data['date']}_{booking_data['time']}_{booking_data.get('duration', '1h')}"
                            if booking_id not in seen_bookings:
                                seen_bookings.add(booking_id)
                                all_bookings.append((booking_key, booking_data))
                except Exception as booking_error:
                    logger.error(f"Error processing booking {booking_key}: {booking_error}")
                    continue
        
        if not all_bookings:
            response_text = (
                "📅 **Мои собеседования"
            )
            if is_mentor:
                response_text += " (Ментор)"
            response_text += "**\n\n"
            
            if is_mentor:
                response_text += "У вас пока нет запланированных собеседований.\n\nСтуденты еще не записались на собеседования."
            else:
                response_text += "У вас пока нет запланированных собеседований.\n\nИспользуйте /start для записи на собеседование!"
            
            update.message.reply_text(response_text, parse_mode='Markdown')
            return
        
        # Sort bookings by date and time in ascending order
        all_bookings = sort_bookings_by_time(all_bookings)
        
        # Format and display
        response_text = "📅 **Мои собеседования"
        if is_mentor:
            response_text += " (Ментор)"
        response_text += "**\n\n"
        
        for booking_key, booking_data in all_bookings:
            try:
                date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj, False)
                
                # Duration information
                duration_text = ""
                if 'duration' in booking_data:
                    if booking_data['duration'] == '1h':
                        duration_text = " | ⏱️ 1 час"
                    elif booking_data['duration'] == '2h':
                        duration_text = " | ⏱️ 1.5-2 часа"
                
                if is_mentor:
                    # For mentors: show student info
                    student_info = booking_data.get('user_info', {})
                    student_name = student_info.get('first_name', 'Неизвестно')
                    student_username = student_info.get('username', '')
                    student_text = f"{student_name}"
                    if student_username:
                        student_text += f" @{student_username}"
                    
                    # Get company information
                    company_info = booking_data.get('company', 'Не указана')
                    
                    response_text += (
                        f"📅 **{formatted_date}**\n"
                        f"⏰ Время: {booking_data['time']}{duration_text}\n"
                        f"👤 Студент: {student_text}\n"
                        f"🏢 Компания: {company_info}\n\n"
                    )
                else:
                    # For students: show mentor info
                    mentor_id = booking_data.get('mentor_id')
                    if mentor_id and mentor_id in MENTORS:
                        mentor_info = MENTORS[mentor_id]
                        mentor_text = f"{mentor_info['name']} {mentor_info['username']}"
                    else:
                        mentor_text = "Не указан"
                    
                    response_text += (
                        f"📅 **{formatted_date}**\n"
                        f"⏰ Время: {booking_data['time']}{duration_text}\n"
                        f"👤 Ментор: {mentor_text}\n\n"
                    )
            except Exception as format_error:
                logger.error(f"Error formatting booking {booking_key}: {format_error}")
                continue
        
        # Add cancel buttons for each booking
        keyboard = []
        for booking_key, booking_data in all_bookings:
            try:
                button_text = f"❌ Отменить {format_date_for_display(datetime.strptime(booking_data['date'], '%Y-%m-%d'), False)} {booking_data['time']}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"cancel_booking_{booking_key}")])
            except Exception as button_error:
                logger.error(f"Error creating cancel button for booking {booking_key}: {button_error}")
                continue
        
        # Add back button - should go back to profile, not to date selection
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="profile_outline")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(response_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        logger.info(f"Successfully displayed {len(all_bookings)} interviews for user {user.id} (mentor: {is_mentor})")
        
    except Exception as e:
        logger.error(f"Error in handle_my_interviews: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def handle_start_menu(update: Update, context: CallbackContext):
    """Handle 'start_menu' callback to return to main menu"""
    try:
        query = update.callback_query
        query.answer()
        
        # Get user info
        user = update.effective_user
        
        # Register user if new
        register_user_if_new(user)
        
        # Get user's permanent mentor
        permanent_mentor = get_user_permanent_mentor(user.id)
        
        # Get available dates
        available_dates = get_available_dates()
        
        # Create inline keyboard with date buttons
        keyboard = []
        for date_str in available_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj, True, permanent_mentor)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        # Add "Следующая неделя→" button
        keyboard.append([InlineKeyboardButton("Следующая неделя→", callback_data="next_week")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"👋 Привет, {user.first_name}!\n\n"
            f"📅 Выберите удобную дату для собеседования:"
        )
        
        # Edit the current message to show the main menu
        query.edit_message_text(welcome_text, reply_markup=reply_markup)
        
        # Send outline buttons message
        outline_keyboard = [
            ["Мои собеседования"],
            ["Профиль"]
        ]
        outline_markup = ReplyKeyboardMarkup(outline_keyboard, resize_keyboard=True, one_time_keyboard=False)
        query.message.reply_text("Используйте кнопки ниже для навигации:", reply_markup=outline_markup)
        
        logger.info(f"User {user.id} returned to main menu")
        
    except Exception as e:
        logger.error(f"Error in handle_start_menu: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_profile_outline(update: Update, context: CallbackContext):
    """Handle 'Профиль' outline button and callback"""
    try:
        # Check if this is a callback query or a message
        is_callback = hasattr(update, 'callback_query') and update.callback_query is not None
        
        if is_callback:
            query = update.callback_query
            query.answer()
            user = query.from_user
        else:
            user = update.effective_user
        
        # Get user's booking statistics
        user_bookings = []
        upcoming_interviews = 0
        
        # Get total bookings made by user (from user database)
        total_bookings_made = get_user_total_bookings(user.id)
        
        for booking_key, booking_data in interview_bookings.items():
            if booking_data['user_id'] == user.id:
                # Check if interview is in the past (both date and time)
                interview_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
                current_date = datetime.now().date()
                
                # Check if the interview time has passed
                is_past = False
                if interview_date.date() < current_date:
                    is_past = True
                elif interview_date.date() == current_date:
                    # Check if the specific time slot has passed
                    time_slot_index = booking_data.get('time_slot_index', 0)
                    if is_time_slot_in_past(booking_data['date'], time_slot_index):
                        is_past = True
                
                # Only add upcoming interviews to the list
                if not is_past:
                    upcoming_interviews += 1
                    user_bookings.append(booking_data)
        
        # Create profile text
        profile_text = f"👤 **Профиль пользователя**\n\n"
        profile_text += f"**Основная информация:**\n"
        profile_text += f"• Имя: {user.first_name}\n"
        if user.username:
            profile_text += f"• Username: @{user.username}\n"
        profile_text += f"• ID: {user.id}\n"
        profile_text += f"• Дата регистрации: {get_user_registration_date(user.id)}\n"
        
        # Add mentor information
        permanent_mentor = get_user_permanent_mentor(user.id)
        if permanent_mentor:
            permanent_mentor_info = MENTORS[permanent_mentor]
            profile_text += f"• Постоянный ментор: {permanent_mentor_info['name']} {permanent_mentor_info['username']}\n"
        else:
            profile_text += f"• Постоянный ментор: ❌ Не выбран\n"
        
        profile_text += f"\n**Статистика собеседований:**\n"
        profile_text += f"• Всего записей: {total_bookings_made}\n"
        profile_text += f"• Предстоящих: {upcoming_interviews}\n"
        profile_text += f"• Завершенных: {total_bookings_made - upcoming_interviews}\n\n"
        

        
        # Add navigation buttons
        keyboard = []
        keyboard.append([InlineKeyboardButton("📅 Мои записи", callback_data="my_bookings")])
        keyboard.append([InlineKeyboardButton("🔄 Сменить ментора", callback_data="change_mentor")])
        keyboard.append([InlineKeyboardButton("← Назад", callback_data="start_menu")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if is_callback:
            # Edit the current message for callback queries
            query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            # Send new message for outline button clicks
            update.message.reply_text(profile_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in handle_profile_outline: {e}")
        if is_callback:
            query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")
        else:
            update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def handle_message(update: Update, context: CallbackContext):
    """Handle text messages for outline buttons and company input"""
    try:
        text = update.message.text
        
        # Check if user is waiting for company input
        if 'pending_booking' in context.user_data:
            # User is providing company name
            company_name = text.strip()
            if not company_name:
                update.message.reply_text("❌ Пожалуйста, укажите название компании.")
                return
            
            # Get pending booking details
            pending_booking = context.user_data['pending_booking']
            
            # Create confirmation message with company
            confirmation_text = (
                f"📋 **Подтверждение записи**\n\n"
                f"📅 Дата: {pending_booking['formatted_date']}\n"
                f"⏰ Время: {pending_booking['time_range']}\n"
                f"⏱️ Длительность: {pending_booking['duration_text']}\n"
                f"👤 Ментор: {MENTORS[pending_booking['mentor_id']]['name']} {MENTORS[pending_booking['mentor_id']]['username']}\n"
                f"📋 Тип: {pending_booking['mentor_type']}\n"
                f"🏢 Компания: {company_name}\n\n"
                f"Подтвердите запись на собеседование?"
            )
            
            # Store company name in context
            context.user_data['pending_booking']['company'] = company_name
            
            # Create confirmation buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_with_company"),
                    InlineKeyboardButton("❌ Отменить", callback_data="cancel_company")
                ]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(text=confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
            return
        
        # Check for broadcast command
        if text.startswith('/all '):
            handle_broadcast_command(update, context)
            return
        
        if text == "Мои собеседования":
            handle_my_interviews(update, context)
        elif text == "Профиль":
            handle_profile_outline(update, context)
        elif text == "/" or text == "/help":
            # Show help when user types just "/" or "/help"
            help_command(update, context)
        else:
            # Unknown text, ignore
            pass
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")

def handle_broadcast_command(update: Update, context: CallbackContext):
    """Handle broadcast command to send message to all users"""
    try:
        user = update.effective_user
        
        # Check if user is @yashonflame (mentor_1)
        if user.id != 780202036:  # @yashonflame's user ID
            update.message.reply_text("❌ У вас нет прав для отправки сообщений всем пользователям.")
            return
        
        # Extract the message from the command
        message_text = update.message.text[5:].strip()  # Remove '/all ' prefix
        
        if not message_text:
            update.message.reply_text("❌ Пожалуйста, укажите текст сообщения.\n\nПример: /all Привет всем!")
            return
        
        # Load users from database
        load_users_from_database()
        
        # Get all user IDs
        user_ids = list(users_database.keys())
        
        if not user_ids:
            update.message.reply_text("❌ Нет пользователей для отправки сообщения.")
            return
        
        # Send message to all users
        success_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                context.bot.send_message(
                    chat_id=int(user_id),
                    text=f"📢 **Сообщение от администратора:**\n\n{message_text}",
                    parse_mode='Markdown'
                )
                success_count += 1
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Failed to send broadcast message to user {user_id}: {e}")
                failed_count += 1
        
        # Send confirmation to admin
        confirmation_text = (
            f"✅ **Сообщение отправлено!**\n\n"
            f"📤 Успешно отправлено: {success_count}\n"
            f"❌ Ошибок отправки: {failed_count}\n"
            f"📊 Всего пользователей: {len(user_ids)}\n\n"
            f"📝 **Текст сообщения:**\n{message_text}"
        )
        
        update.message.reply_text(confirmation_text, parse_mode='Markdown')
        logger.info(f"Broadcast message sent by {user.username} ({user.id}) to {success_count} users")
        
    except Exception as e:
        logger.error(f"Error in handle_broadcast_command: {e}")
        update.message.reply_text("❌ Произошла ошибка при отправке сообщения.")

def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def validate_database_command(update: Update, context: CallbackContext):
    """Command to manually validate and clean the database"""
    try:
        user = update.effective_user
        
        # Only allow admin users to run this command
        if user.id != 780202036:  # Replace with actual admin user ID
            update.message.reply_text("❌ У вас нет прав для выполнения этой команды.")
            return
        
        update.message.reply_text("🔍 Начинаю проверку базы данных...")
        
        # Run validation
        is_valid = validate_and_clean_bookings_database()
        
        if is_valid:
            update.message.reply_text("✅ База данных проверена и очищена. Все записи корректны.")
        else:
            update.message.reply_text("⚠️ База данных проверена и очищена. Были найдены и исправлены ошибки.")
            
    except Exception as e:
        logger.error(f"Error in validate_database_command: {e}")
        update.message.reply_text("❌ Произошла ошибка при проверке базы данных.")

def view_database(update: Update, context: CallbackContext):
    """Admin command to view database contents"""
    try:
        user = update.effective_user
        
        # Check if user is admin (you can modify this check)
        if user.id != 780202036:  # Replace with your admin user ID
            update.message.reply_text("❌ У вас нет прав для просмотра базы данных.")
            return
        
        if not interview_bookings:
            update.message.reply_text("📊 База данных пуста.")
            return
        
        # Create database summary
        summary = "📊 Содержимое базы данных:\n\n"
        
        for booking_key, booking_data in interview_bookings.items():
            user_info = booking_data.get('user_info', {})
            username = user_info.get('username', '')
            first_name = user_info.get('first_name', 'Unknown')
            
            if username:
                user_display = f"@{username}"
            else:
                user_display = first_name
            
            date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj, False)
            
            summary += f"🔑 {booking_key}\n"
            summary += f"👤 Пользователь: {user_display}\n"
            summary += f"📅 Дата: {formatted_date}\n"
            summary += f"⏰ Время: {booking_data['time']}\n"
            summary += f"📝 Забронировано: {booking_data.get('booked_at', 'Не указано')}\n\n"
        
        update.message.reply_text(summary)
        
    except Exception as e:
        logger.error(f"Error in view_database: {e}")
        update.message.reply_text("Произошла ошибка при просмотре базы данных.")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to start the bot"""
    try:
        logger.info("Starting Interview Scheduling Bot...")
        logger.info("🤖 Interview Scheduling Bot is starting...")
        logger.info("📝 Bot token is configured!")
        
        # Load existing bookings from database
        load_bookings_from_database()
        logger.info("📊 Bookings database loaded successfully!")
        
        # Load existing users from database
        load_users_from_database()
        logger.info("👥 Users database loaded successfully!")
        
        # Load existing mentors from database
        load_mentors_from_database()
        logger.info("👨‍🏫 Mentors database loaded successfully!")
        
        # Validate and clean database on startup
        logger.info("🔍 Validating database on startup...")
        validate_and_clean_bookings_database()
        
        logger.info("📱 Bot is now running. Send /start to your bot to test it!")
        logger.info("📢 Notifications will be sent to your private channel!")
        
        # Create updater and dispatcher
        updater = Updater(keys.token, use_context=True)
        dispatcher = updater.dispatcher
        
        # Set up bot commands
        setup_bot_commands(updater)
    
    # Add handlers
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("profile", profile_command))
        dispatcher.add_handler(CommandHandler("mybookings", my_bookings))
        dispatcher.add_handler(CommandHandler("database", view_database))
        dispatcher.add_handler(CommandHandler("validate_db", validate_database_command))
        dispatcher.add_handler(MessageHandler(Filters.text, handle_message)) # Add message handler for outline buttons
    
    # Add callback query handlers
        dispatcher.add_handler(CallbackQueryHandler(handle_mentor_choice, pattern='^choose_mentor_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_date_selection, pattern='^date_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_time_selection, pattern='^time_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_duration_selection, pattern='^duration_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_confirmation, pattern='^confirm_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_cancel_company, pattern='^cancel_company$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_booked_slot, pattern='^booked_slot_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_cancellation, pattern='^cancel_booking_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_back_to_dates, pattern='^back_to_dates$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_next_week, pattern='^next_week$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_next_week_2, pattern='^next_week_2$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_profile_callback, pattern='^profile$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_profile_navigation, pattern='^(my_bookings|close_profile)$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_change_mentor, pattern='^change_mentor$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_change_to_mentor, pattern='^change_to_mentor_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_my_interviews, pattern='^my_interviews$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_profile_outline, pattern='^profile_outline$'))
        dispatcher.add_handler(CallbackQueryHandler(handle_start_menu, pattern='^start_menu$'))
        

        
        # Add error handler
        dispatcher.add_error_handler(error_handler)
        
        # Start polling
        updater.start_polling()
        logger.info("Polling started successfully!")
        logger.info("Bot is now idle and waiting for messages...")
        
        # Keep the bot running
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

def setup_bot_commands(updater):
    """Set up bot commands that appear when user types /"""
    commands = [
        BotCommand("start", "Записаться на собеседование"),
        BotCommand("profile", "Посмотреть профиль и статистику"),
        BotCommand("mybookings", "Посмотреть ваши записи"),
        BotCommand("help", "Показать справку по боту"),
        BotCommand("database", "Просмотр базы данных (админ)"),
        BotCommand("validate_db", "Проверить и очистить базу данных (админ)")
    ]
    
    try:
        updater.bot.set_my_commands(commands)
        logger.info("Bot commands set up successfully")
    except Exception as e:
        logger.error(f"Error setting up bot commands: {e}")

# ============================================================================
# SORTING FUNCTION
# ============================================================================

def sort_bookings_by_time(bookings):
    """Sort bookings by date and time in ascending order"""
    return sorted(bookings, key=lambda x: (
        datetime.strptime(x[1]['date'], '%Y-%m-%d'),
        x[1]['time']
    ))

def validate_and_clean_bookings_database():
    """Validate and clean up the bookings database to prevent missing interviews"""
    global interview_bookings
    
    try:
        logger.info("Starting database validation and cleanup...")
        
        # Track issues found
        issues_found = []
        cleaned_bookings = {}
        
        for booking_key, booking_data in interview_bookings.items():
            try:
                # Check for required fields
                required_fields = ['user_id', 'date', 'time', 'mentor_id']
                missing_fields = [field for field in required_fields if field not in booking_data]
                
                if missing_fields:
                    issues_found.append(f"Booking {booking_key}: Missing fields {missing_fields}")
                    continue
                
                # Validate date format
                try:
                    datetime.strptime(booking_data['date'], '%Y-%m-%d')
                except ValueError:
                    issues_found.append(f"Booking {booking_key}: Invalid date format {booking_data['date']}")
                    continue
                
                # Validate time format
                if ' - ' not in booking_data['time']:
                    issues_found.append(f"Booking {booking_key}: Invalid time format {booking_data['time']}")
                    continue
                
                # Validate user_id is integer
                try:
                    int(booking_data['user_id'])
                except (ValueError, TypeError):
                    issues_found.append(f"Booking {booking_key}: Invalid user_id {booking_data['user_id']}")
                    continue
                
                # Validate mentor_id exists in MENTORS
                if booking_data['mentor_id'] not in MENTORS:
                    issues_found.append(f"Booking {booking_key}: Invalid mentor_id {booking_data['mentor_id']}")
                    continue
                
                # If all validations pass, keep the booking
                cleaned_bookings[booking_key] = booking_data
                
            except Exception as e:
                issues_found.append(f"Booking {booking_key}: Error during validation - {e}")
                continue
        
        # Report issues
        if issues_found:
            logger.warning(f"Found {len(issues_found)} issues in bookings database:")
            for issue in issues_found:
                logger.warning(issue)
        
        # Update the global variable with cleaned data
        interview_bookings = cleaned_bookings
        
        # Save cleaned data to file
        save_bookings_to_database()
        
        logger.info(f"Database cleanup complete. Kept {len(cleaned_bookings)} valid bookings out of {len(interview_bookings) + len(issues_found)} total.")
        
        return len(issues_found) == 0
        
    except Exception as e:
        logger.error(f"Error during database validation: {e}")
        return False

if __name__ == "__main__":
    main()