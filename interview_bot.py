import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import keys
import urllib3
from notification_sender import send_booking_log

# Configure detailed logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # Changed to DEBUG for more detailed logs
)
logger = logging.getLogger(__name__)

# Store interview bookings (in a real app, use a database)
interview_bookings = {}

def get_available_dates():
    """Get 5 available weekdays starting from today"""
    logger.debug("Getting available dates...")
    available_dates = []
    current_date = datetime.now()
    
    # Start from today
    next_date = current_date
    
    # Find 5 weekdays (Monday to Friday)
    count = 0
    while count < 5:
        if next_date.weekday() < 5:  # Monday = 0, Friday = 4
            available_dates.append(next_date)
            count += 1
        next_date += timedelta(days=1)
    
    logger.debug(f"Available dates: {available_dates}")
    return available_dates

def format_date_for_display(date):
    """Format date as DD.MM day_name"""
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    return f"{date.strftime('%d.%m')} {day_names[date.weekday()]}"

def format_date_for_callback(date):
    """Format date for callback data"""
    return date.strftime('%Y-%m-%d')

def start_command(update: Update, context: CallbackContext):
    """Send welcome message and show available dates"""
    logger.info(f"Start command received from user {update.effective_user.id} ({update.effective_user.first_name})")
    
    try:
        user = update.effective_user
        welcome_text = f"Hello {user.first_name}! 👋\n\nI'm your interview scheduling bot. Let me show you available interview dates."
        
        # Get available dates
        available_dates = get_available_dates()
        
        # Create inline keyboard with available dates
        keyboard = []
        for date in available_dates:
            display_text = format_date_for_display(date)
            callback_data = f"date_{format_date_for_callback(date)}"
            keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        logger.debug(f"Sending welcome message with {len(keyboard)} date options")
        update.message.reply_text(
            welcome_text + "\n\n📅 On which date would you like to schedule your interview?",
            reply_markup=reply_markup
        )
        logger.info("Welcome message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        update.message.reply_text("Sorry, something went wrong. Please try again.")

def handle_date_selection(update: Update, context: CallbackContext):
    """Handle date selection and show available time slots"""
    logger.info(f"Date selection callback received: {update.callback_query.data}")
    
    try:
        query = update.callback_query
        query.answer()
        
        # Extract date from callback data
        callback_data = query.data
        if callback_data.startswith("date_"):
            selected_date = callback_data[5:]  # Remove "date_" prefix
            logger.debug(f"Selected date: {selected_date}")
            
            # Parse the date
            try:
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj)
                
                # Show available time slots
                time_slots = [
                    "09:00 - 10:00",
                    "10:00 - 11:00", 
                    "11:00 - 12:00",
                    "14:00 - 15:00",
                    "15:00 - 16:00",
                    "16:00 - 17:00"
                ]
                
                keyboard = []
                for i, time_slot in enumerate(time_slots):
                    callback_data = f"time_{selected_date}_{i}"
                    keyboard.append([InlineKeyboardButton(time_slot, callback_data=callback_data)])
                
                # Add back button
                keyboard.append([InlineKeyboardButton("← Back to dates", callback_data="back_to_dates")])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                logger.debug(f"Sending time slots for date {formatted_date}")
                query.edit_message_text(
                    f"📅 Selected date: {formatted_date}\n\n⏰ Choose your preferred time slot:",
                    reply_markup=reply_markup
                )
                logger.info("Time slots sent successfully")
                
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")
                query.edit_message_text("❌ Invalid date format. Please try again.")
        
        elif callback_data == "back_to_dates":
            logger.debug("Going back to date selection")
            # Go back to date selection
            available_dates = get_available_dates()
            
            keyboard = []
            for date in available_dates:
                display_text = format_date_for_display(date)
                callback_data = f"date_{format_date_for_callback(date)}"
                keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                "📅 On which date would you like to schedule your interview?",
                reply_markup=reply_markup
            )
            logger.info("Back to dates sent successfully")
            
    except Exception as e:
        logger.error(f"Error in handle_date_selection: {e}")
        try:
            update.callback_query.edit_message_text("Sorry, something went wrong. Please try again.")
        except:
            pass

def handle_time_selection(update: Update, context: CallbackContext):
    """Handle time slot selection and confirm booking"""
    logger.info(f"Time selection callback received: {update.callback_query.data}")
    
    try:
        query = update.callback_query
        query.answer()
        
        callback_data = query.data
        if callback_data.startswith("time_"):
            # Extract date and time slot
            parts = callback_data.split("_")
            if len(parts) == 3:
                selected_date = parts[1]
                time_slot_index = int(parts[2])
                logger.debug(f"Selected time: date={selected_date}, slot={time_slot_index}")
                
                time_slots = [
                    "09:00 - 10:00",
                    "10:00 - 11:00", 
                    "11:00 - 12:00",
                    "14:00 - 15:00",
                    "15:00 - 16:00",
                    "16:00 - 17:00"
                ]
                
                selected_time = time_slots[time_slot_index]
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj)
                
                # Create confirmation keyboard
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{selected_date}_{time_slot_index}"),
                        InlineKeyboardButton("❌ Cancel", callback_data="cancel_booking")
                    ],
                    [InlineKeyboardButton("← Back to times", callback_data=f"date_{selected_date}")]
                ]
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                logger.debug(f"Sending confirmation for {formatted_date} at {selected_time}")
                query.edit_message_text(
                    f"📋 Booking Summary:\n\n"
                    f"📅 Date: {formatted_date}\n"
                    f"⏰ Time: {selected_time}\n\n"
                    f"Please confirm your interview booking:",
                    reply_markup=reply_markup
                )
                logger.info("Confirmation sent successfully")
                
    except Exception as e:
        logger.error(f"Error in handle_time_selection: {e}")
        try:
            update.callback_query.edit_message_text("Sorry, something went wrong. Please try again.")
        except:
            pass

def handle_confirmation(update: Update, context: CallbackContext):
    """Handle booking confirmation"""
    logger.info(f"Confirmation callback received: {update.callback_query.data}")
    
    try:
        query = update.callback_query
        query.answer()
        
        callback_data = query.data
        
        if callback_data.startswith("confirm_"):
            # Extract booking details
            parts = callback_data.split("_")
            if len(parts) == 3:
                selected_date = parts[1]
                time_slot_index = int(parts[2])
                logger.debug(f"Confirming booking: date={selected_date}, slot={time_slot_index}")
                
                time_slots = [
                    "09:00 - 10:00",
                    "10:00 - 11:00", 
                    "11:00 - 12:00",
                    "14:00 - 15:00",
                    "15:00 - 16:00",
                    "16:00 - 17:00"
                ]
                
                selected_time = time_slots[time_slot_index]
                date_obj = datetime.strptime(selected_date, '%Y-%m-%d')
                formatted_date = format_date_for_display(date_obj)
                
                # Store the booking (in a real app, save to database)
                user_id = update.effective_user.id
                booking_key = f"{selected_date}_{time_slot_index}"
                interview_bookings[booking_key] = {
                    'user_id': user_id,
                    'date': selected_date,
                    'time': selected_time,
                    'user_name': update.effective_user.first_name
                }
                
                logger.info(f"Booking stored: {booking_key} for user {user_id}")
                
                # Send notification to private channel
                try:
                    user_info = {
                        'id': update.effective_user.id,
                        'username': update.effective_user.username,
                        'first_name': update.effective_user.first_name,
                        'last_name': update.effective_user.last_name
                    }
                    
                    # Send notification to your private channel
                    notification_sent = send_booking_log(user_info, selected_date, selected_time)
                    if notification_sent:
                        logger.info("Notification sent to private channel successfully")
                    else:
                        logger.warning("Failed to send notification to private channel")
                        
                except Exception as e:
                    logger.error(f"Error sending notification: {e}")
                
                # Create keyboard to start over
                keyboard = [[InlineKeyboardButton("📅 Schedule Another Interview", callback_data="new_booking")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                query.edit_message_text(
                    f"✅ Interview booked successfully!\n\n"
                    f"📅 Date: {formatted_date}\n"
                    f"⏰ Time: {selected_time}\n\n"
                    f"Please arrive 5 minutes before your scheduled time.\n"
                    f"We'll send you a reminder 1 hour before the interview.",
                    reply_markup=reply_markup
                )
                logger.info("Booking confirmation sent successfully")
        
        elif callback_data == "cancel_booking":
            logger.debug("Booking cancelled, going back to date selection")
            # Go back to date selection
            available_dates = get_available_dates()
            
            keyboard = []
            for date in available_dates:
                display_text = format_date_for_display(date)
                callback_data = f"date_{format_date_for_callback(date)}"
                keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                "📅 On which date would you like to schedule your interview?",
                reply_markup=reply_markup
            )
            logger.info("Back to dates after cancellation sent successfully")
        
        elif callback_data == "new_booking":
            logger.debug("Starting new booking process")
            # Start new booking process
            available_dates = get_available_dates()
            
            keyboard = []
            for date in available_dates:
                display_text = format_date_for_display(date)
                callback_data = f"date_{format_date_for_callback(date)}"
                keyboard.append([InlineKeyboardButton(display_text, callback_data=callback_data)])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                "📅 On which date would you like to schedule your interview?",
                reply_markup=reply_markup
            )
            logger.info("New booking process started successfully")
            
    except Exception as e:
        logger.error(f"Error in handle_confirmation: {e}")
        try:
            update.callback_query.edit_message_text("Sorry, something went wrong. Please try again.")
        except:
            pass

def help_command(update: Update, context: CallbackContext):
    """Send help message"""
    logger.info(f"Help command received from user {update.effective_user.id}")
    
    try:
        help_text = """
🤖 Interview Scheduling Bot Help

Commands:
/start - Start the interview scheduling process
/help - Show this help message
/mybookings - View your current bookings

How to use:
1. Click /start to begin
2. Select an available date
3. Choose your preferred time slot
4. Confirm your booking

Available times: 9:00 AM - 5:00 PM (with lunch break)
"""
        update.message.reply_text(help_text)
        logger.info("Help message sent successfully")
        
    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        update.message.reply_text("Sorry, something went wrong. Please try again.")

def my_bookings(update: Update, context: CallbackContext):
    """Show user's current bookings"""
    logger.info(f"My bookings command received from user {update.effective_user.id}")
    
    try:
        user_id = update.effective_user.id
        
        # Find user's bookings
        user_bookings = []
        for booking_key, booking_data in interview_bookings.items():
            if booking_data['user_id'] == user_id:
                user_bookings.append(booking_data)
        
        logger.debug(f"Found {len(user_bookings)} bookings for user {user_id}")
        
        if not user_bookings:
            update.message.reply_text("📋 You don't have any scheduled interviews yet.\n\nUse /start to schedule one!")
            logger.info("No bookings found message sent")
            return
        
        bookings_text = "📋 Your scheduled interviews:\n\n"
        for i, booking in enumerate(user_bookings, 1):
            date_obj = datetime.strptime(booking['date'], '%Y-%m-%d')
            formatted_date = format_date_for_display(date_obj)
            bookings_text += f"{i}. 📅 {formatted_date} at {booking['time']}\n"
        
        update.message.reply_text(bookings_text)
        logger.info("Bookings list sent successfully")
        
    except Exception as e:
        logger.error(f"Error in my_bookings: {e}")
        update.message.reply_text("Sorry, something went wrong. Please try again.")

def error_handler(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.error(f'Update {update} caused error {context.error}')

def main():
    """Main function to run the bot"""
    logger.info('Starting Interview Scheduling Bot...')
    
    try:
        # Create updater
        logger.debug(f"Creating updater with token: {keys.token[:10]}...")
        updater = Updater(keys.token, use_context=True)
        
        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher
        
        # Commands
        logger.debug("Registering command handlers...")
        dispatcher.add_handler(CommandHandler('start', start_command))
        dispatcher.add_handler(CommandHandler('help', help_command))
        dispatcher.add_handler(CommandHandler('mybookings', my_bookings))
        
        # Callback query handlers
        logger.debug("Registering callback query handlers...")
        dispatcher.add_handler(CallbackQueryHandler(handle_date_selection, pattern="^date_"))
        dispatcher.add_handler(CallbackQueryHandler(handle_time_selection, pattern="^time_"))
        dispatcher.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^(confirm_|cancel_booking|new_booking)"))
        
        # Error handler
        dispatcher.add_error_handler(error_handler)
        
        # Run bot
        logger.info("🤖 Interview Scheduling Bot is starting...")
        logger.info("📝 Bot token is configured!")
        logger.info("📱 Bot is now running. Send /start to your bot to test it!")
        logger.info("📢 Notifications will be sent to your private channel!")
        
        # Start the bot
        logger.debug("Starting polling...")
        updater.start_polling()
        logger.info("Polling started successfully!")
        
        logger.info("Bot is now idle and waiting for messages...")
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == '__main__':
    main()