#!/usr/bin/env python3
"""
Interview Scheduling Bot for Telegram
Allows students to book interview slots with automatic reminders and admin notifications.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import keys
from notification_sender import send_booking_log, send_cancellation_log, send_reminder_log
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
DATABASE_FILE = "bookings.json"  # JSON database file

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
        # Create bot instance for sending message
        updater = Updater(keys.token, use_context=True)
        bot = updater.bot
        
        # Format the reminder message
        date_obj = datetime.strptime(interview_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
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
        
        bot.send_message(
            chat_id=user_id,
            text=reminder_text,
            parse_mode='Markdown'
        )
        
        logger.info(f"Reminder sent to user {user_id} for interview on {interview_date} at {interview_time}")
        
        # Send notification to admin channel
        try:
            # Get user info from interview_bookings
            user_info = None
            for booking_key, booking_data in interview_bookings.items():
                if (booking_data['user_id'] == user_id and 
                    booking_data['date'] == interview_date and 
                    booking_data['time'] == interview_time):
                    user_info = booking_data['user_info']
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
        logger.error(f"Error sending reminder to user {user_id}: {e}")
        return False

def schedule_reminder(user_id, interview_date, interview_time):
    """Schedule a reminder for 1 hour before the interview"""
    try:
        # Parse the interview date and time
        date_obj = datetime.strptime(interview_date, '%Y-%m-%d')
        
        # Find the time slot index
        time_slot_index = None
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
        
        reminder_time = date_obj.replace(hour=reminder_hour, minute=0, second=0, microsecond=0)
        # Add Moscow timezone info
        reminder_time = pytz.timezone('Europe/Moscow').localize(reminder_time)
        
        # Schedule the reminder
        job_id = f"reminder_{user_id}_{interview_date}_{time_slot_index}"
        
        # Remove existing job if it exists
        try:
            scheduler.remove_job(job_id)
        except:
            pass
        
        # Add new job
        scheduler.add_job(
            func=send_reminder_to_user,
            trigger='date',
            run_date=reminder_time,
            args=[user_id, interview_date, interview_time],
            id=job_id,
            replace_existing=True
        )
        
        logger.info(f"Reminder scheduled for user {user_id} on {interview_date} at {reminder_time}")
        return True
        
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
            available_dates.append(current_date.strftime('%Y-%m-%d'))
            date_count += 1
        current_date += timedelta(days=1)
    
    return available_dates

def format_date_for_display(date):
    """Format date as DD.MM day_name"""
    return f"{date.strftime('%d.%m')} {DAY_NAMES[date.weekday()]}"

def format_date_for_callback(date):
    """Format date for callback data"""
    return date.strftime('%Y-%m-%d')

# ============================================================================
# BOOKING CONFLICT PREVENTION
# ============================================================================

def is_time_slot_available(selected_date, time_slot_index):
    """Check if a time slot is available for booking"""
    booking_key = f"{selected_date}_{time_slot_index}"
    return booking_key not in interview_bookings

def get_booked_slots_for_date(selected_date):
    """Get list of booked time slots for a specific date"""
    booked_slots = []
    for booking_key, booking_data in interview_bookings.items():
        if booking_data['date'] == selected_date:
            time_slot_index = booking_data['time_slot_index']
            booked_slots.append(time_slot_index)
    return booked_slots

# ============================================================================
# BOT COMMAND HANDLERS
# ============================================================================

def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    try:
        user = update.effective_user
        logger.info(f"Start command received from user {user.id} ({user.username})")
        
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
            formatted_date = format_date_for_display(date_obj)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(welcome_text, reply_markup=reply_markup)
        logger.info("Welcome message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

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
        logger.info(f"Date selection callback received: {callback_data}")
        
        # Get booked slots for this date
        booked_slots = get_booked_slots_for_date(selected_date)
        
        # Create time slot buttons
        keyboard = []
        for i, time_slot in enumerate(TIME_SLOTS):
            if i in booked_slots:
                # Slot is booked
                button_text = f"❌ {time_slot} (Занято)"
                callback_data = f"booked_slot_{selected_date}_{i}"
            else:
                # Slot is available
                button_text = f"✅ {time_slot}"
                callback_data = f"time_{selected_date}_{i}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add back button
        keyboard.append([InlineKeyboardButton("← Назад к датам", callback_data="back_to_dates")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format date for display
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
        response_text = f"📅 Выбрана дата: {formatted_date}\n\n⏰ Выберите удобное время:\n\n✅ - Доступно | ❌ - Занято"
        
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
        
        parts = callback_data.split('_')
        selected_date = parts[1]
        time_slot_index = int(parts[2])
        selected_time = TIME_SLOTS[time_slot_index]
        
        logger.info(f"Time selection callback received: {callback_data}")
        
        # Check if slot is still available
        if not is_time_slot_available(selected_date, time_slot_index):
            query.edit_message_text("❌ Это время уже занято. Пожалуйста, выберите другое время.")
            return
        
        # Format date for display
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
        # Create confirmation message
        confirmation_text = (
            f"📋 **Подтверждение записи**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {selected_time}\n\n"
            f"Пожалуйста, подтвердите вашу запись:"
        )
        
        # Create confirmation buttons
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{selected_date}_{time_slot_index}"),
                InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking")
            ],
            [InlineKeyboardButton("← Назад к времени", callback_data=f"date_{selected_date}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(text=confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
        logger.info("Confirmation sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_time_selection: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def handle_confirmation(update: Update, context: CallbackContext):
    """Handle booking confirmation"""
    try:
        query = update.callback_query
        query.answer()
        
        # Extract data from callback
        callback_data = query.data
        if not callback_data.startswith('confirm_'):
            return
        
        parts = callback_data.split('_')
        selected_date = parts[1]
        time_slot_index = int(parts[2])
        selected_time = TIME_SLOTS[time_slot_index]
        
        logger.info(f"Confirmation callback received: {callback_data}")
        
        # Check if slot is still available
        if not is_time_slot_available(selected_date, time_slot_index):
            query.edit_message_text("❌ Это время уже занято. Пожалуйста, выберите другое время.")
            return
        
        # Store the booking
        user = update.effective_user
        booking_key = f"{selected_date}_{time_slot_index}"
        
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
            'booked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Add to database
        add_booking_to_database(booking_key, booking_data)
        
        logger.info(f"Booking stored: {booking_key} for user {user.id}")
        
        # Schedule reminder
        schedule_reminder(user.id, selected_date, selected_time)
        logger.info(f"Reminder scheduled for user {user.id}")
        
        # Send notification to admin channel
        try:
            send_booking_log(
                interview_bookings[booking_key]['user_info'],
                selected_date,
                selected_time
            )
            logger.info("Notification sent to private channel successfully")
        except Exception as e:
            logger.error(f"Error sending notification to channel: {e}")
        
        # Send confirmation message
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
        success_text = (
            f"✅ **Запись подтверждена!**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {selected_time}\n\n"
            f"🔔 За 1 час до собеседования вы получите напоминание.\n\n"
            f"Используйте /mybookings для просмотра ваших записей.\n"
            f"Используйте /help для получения справки."
        )
        
        query.edit_message_text(text=success_text, parse_mode='Markdown')
        logger.info("Booking confirmation sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_confirmation: {e}")
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
        
        # Get available dates
        available_dates = get_available_dates()
        
        # Create inline keyboard with date buttons
        keyboard = []
        for date_str in available_dates:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj)
            callback_data = f"date_{format_date_for_callback(date_obj)}"
            keyboard.append([InlineKeyboardButton(formatted_date, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            f"📅 Выберите удобную дату для собеседования:"
        )
        
        query.edit_message_text(welcome_text, reply_markup=reply_markup)
        logger.info("Back to dates sent successfully")
        
    except Exception as e:
        logger.error(f"Error in handle_back_to_dates: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    try:
        help_text = (
            f"🤖 **Справка по боту**\n\n"
            f"**Доступные команды:**\n"
            f"• /start - Записаться на собеседование\n"
            f"• /mybookings - Посмотреть ваши записи\n"
            f"• /help - Показать эту справку\n"
            f"• /database - Просмотр базы данных (только для админа)\n\n"
            f"**Как записаться:**\n"
            f"1. Используйте /start\n"
            f"2. Выберите удобную дату\n"
            f"3. Выберите свободное время\n"
            f"4. Подтвердите запись\n\n"
            f"**Напоминания:**\n"
            f"За 1 час до собеседования вы получите автоматическое напоминание.\n\n"
            f"**Отмена записи:**\n"
            f"Используйте /mybookings для просмотра и отмены ваших записей."
        )
        
        update.message.reply_text(help_text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def my_bookings(update: Update, context: CallbackContext):
    """Handle /mybookings command"""
    try:
        user = update.effective_user
        
        # Find user's bookings
        user_bookings = []
        for booking_key, booking_data in interview_bookings.items():
            if booking_data['user_id'] == user.id:
                user_bookings.append((booking_key, booking_data))
        
        if not user_bookings:
            update.message.reply_text("У вас пока нет записей на собеседование.")
            return
        
        # Create message with user's bookings
        bookings_text = "📋 **Ваши записи на собеседование:**\n\n"
        
        keyboard = []
        for booking_key, booking_data in user_bookings:
            date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj)
            
            bookings_text += f"📅 {formatted_date} | ⏰ {booking_data['time']}\n"
            
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
        
        # Send confirmation message
        date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
        formatted_date = format_date_for_display(date_obj)
        
        cancellation_text = (
            f"❌ **Запись отменена**\n\n"
            f"📅 Дата: {formatted_date}\n"
            f"⏰ Время: {selected_time}\n\n"
            f"Запись успешно отменена.\n"
            f"Используйте /start для новой записи."
        )
        
        query.edit_message_text(text=cancellation_text, parse_mode='Markdown')
        logger.info(f"Booking cancelled: {booking_key}")
        
    except Exception as e:
        logger.error(f"Error in handle_cancellation: {e}")
        query.edit_message_text("Произошла ошибка. Попробуйте еще раз.")

def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

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
            user_info = booking_data['user_info']
            username = user_info.get('username', '')
            first_name = user_info.get('first_name', 'Unknown')
            
            if username:
                user_display = f"@{username}"
            else:
                user_display = first_name
            
            date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj)
            
            summary += f"🔑 {booking_key}\n"
            summary += f"👤 Пользователь: {user_display}\n"
            summary += f"📅 Дата: {formatted_date}\n"
            summary += f"⏰ Время: {booking_data['time']}\n"
            summary += f"📝 Забронировано: {booking_data['booked_at']}\n\n"
        
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
        logger.info("📊 Database loaded successfully!")
        
        logger.info("📱 Bot is now running. Send /start to your bot to test it!")
        logger.info("📢 Notifications will be sent to your private channel!")
        
        # Create updater and dispatcher
        updater = Updater(keys.token, use_context=True)
        dispatcher = updater.dispatcher
        
        # Add handlers
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("mybookings", my_bookings))
        dispatcher.add_handler(CommandHandler("database", view_database))
        
        # Add callback query handlers
        dispatcher.add_handler(CallbackQueryHandler(handle_date_selection, pattern='^date_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_time_selection, pattern='^time_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_confirmation, pattern='^confirm_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_booked_slot, pattern='^booked_slot_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_cancellation, pattern='^cancel_booking_'))
        dispatcher.add_handler(CallbackQueryHandler(handle_back_to_dates, pattern='^back_to_dates$'))
        
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

if __name__ == "__main__":
    main()