# 🆕 Adding New Calendar Features

## 🎯 **How to Add New Features to Your Bot**

### **Step 1: Identify What You Want to Add**

Common new features you might want:
- **Event Descriptions** - Users can add notes to their bookings
- **Recurring Events** - Weekly/monthly interviews
- **Calendar View** - Visual calendar interface
- **Event Categories** - Different types of interviews
- **Reminder Settings** - Custom reminder times
- **Group Bookings** - Multiple students in one slot

### **Step 2: Plan Your Changes**

#### **Example: Adding Event Descriptions**

**Current Flow:**
1. User selects date
2. User selects time
3. User confirms booking

**New Flow with Descriptions:**
1. User selects date
2. User selects time
3. **NEW: Bot asks for description**
4. User enters description
5. User confirms booking

### **Step 3: Modify the Code**

#### **1. Update Database Structure**

```python
# In interview_bot.py, modify the booking data structure:
booking_data = {
    'user_id': user.id,
    'date': selected_date,
    'time': selected_time,
    'mentor_id': mentor_id,
    'description': description,  # NEW FIELD
    'booked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}
```

#### **2. Add New Handler for Description**

```python
# Add this new function to interview_bot.py:
def handle_description_input(update: Update, context: CallbackContext):
    """Handle user input for event description"""
    try:
        user_message = update.message.text
        user = update.effective_user
        
        # Store description in context
        if 'pending_booking' in context.user_data:
            context.user_data['pending_booking']['description'] = user_message
        
        # Show confirmation with description
        show_booking_confirmation(update, context)
        
    except Exception as e:
        logger.error(f"Error handling description: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def show_booking_confirmation(update: Update, context: CallbackContext):
    """Show final booking confirmation with description"""
    try:
        pending_booking = context.user_data['pending_booking']
        description = pending_booking.get('description', 'Не указано')
        
        confirmation_text = (
            f"📋 **Подтверждение записи**\n\n"
            f"📅 Дата: {pending_booking['formatted_date']}\n"
            f"⏰ Время: {pending_booking['time_range']}\n"
            f"⏱️ Длительность: {pending_booking['duration_text']}\n"
            f"📝 Описание: {description}\n\n"
            f"Подтвердите запись:"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_with_description"),
                InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(confirmation_text, reply_markup=reply_markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error showing confirmation: {e}")
```

#### **3. Modify Existing Handlers**

```python
# In handle_duration_selection, add description prompt:
def handle_duration_selection(update: Update, context: CallbackContext):
    # ... existing code ...
    
    # After storing booking details, ask for description
    description_text = (
        f"📝 **Добавьте описание к собеседованию**\n\n"
        f"Например:\n"
        f"• Тема: JavaScript разработка\n"
        f"• Вопросы по React\n"
        f"• Подготовка к собеседованию\n\n"
        f"Или просто нажмите 'Пропустить'"
    )
    
    keyboard = [
        [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_description")],
        [InlineKeyboardButton("← Назад", callback_data=f"date_{selected_date}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text=description_text, reply_markup=reply_markup, parse_mode='Markdown')
```

#### **4. Add New Callback Handlers**

```python
# Add these to your main() function:
def main():
    # ... existing handlers ...
    
    # Add new handlers
    updater.dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, 
        handle_description_input
    ))
    
    # Add callback handlers
    updater.dispatcher.add_handler(CallbackQueryHandler(
        handle_skip_description, 
        pattern='^skip_description$'
    ))
    
    updater.dispatcher.add_handler(CallbackQueryHandler(
        handle_confirm_with_description, 
        pattern='^confirm_with_description$'
    ))

def handle_skip_description(update: Update, context: CallbackContext):
    """Handle skipping description"""
    try:
        query = update.callback_query
        query.answer()
        
        # Set default description
        if 'pending_booking' in context.user_data:
            context.user_data['pending_booking']['description'] = 'Не указано'
        
        show_booking_confirmation(update, context)
        
    except Exception as e:
        logger.error(f"Error handling skip description: {e}")

def handle_confirm_with_description(update: Update, context: CallbackContext):
    """Handle confirmation with description"""
    try:
        query = update.callback_query
        query.answer()
        
        # Use existing confirmation logic but with description
        handle_confirmation(update, context)
        
    except Exception as e:
        logger.error(f"Error handling confirm with description: {e}")
```

### **Step 4: Test Your Changes**

```bash
# Test locally first
python interview_bot.py

# Test the new flow:
# 1. Send /start
# 2. Select date and time
# 3. Check if description prompt appears
# 4. Test with and without description
```

### **Step 5: Deploy Changes**

```bash
# Commit your changes
git add .
git commit -m "feat: added event descriptions to calendar"

# Push to repository
git push

# On server, pull and rebuild
ssh user@your-server-ip
cd telegram-interview-bot
git pull
docker-compose up -d --build
```

## 🎯 **Other Feature Examples**

### **Example 2: Add Recurring Events**

```python
# Add to booking data:
booking_data = {
    # ... existing fields ...
    'recurring': {
        'type': 'weekly',  # weekly, monthly, none
        'end_date': '2024-12-31',
        'interval': 1  # every 1 week
    }
}

# Add recurring logic:
def schedule_recurring_reminders(booking_data):
    """Schedule reminders for recurring events"""
    if booking_data.get('recurring', {}).get('type') != 'none':
        # Schedule multiple reminders
        start_date = datetime.strptime(booking_data['date'], '%Y-%m-%d')
        end_date = datetime.strptime(booking_data['recurring']['end_date'], '%Y-%m-%d')
        
        current_date = start_date
        while current_date <= end_date:
            schedule_reminder(
                booking_data['user_id'],
                current_date.strftime('%Y-%m-%d'),
                booking_data['time']
            )
            current_date += timedelta(weeks=booking_data['recurring']['interval'])
```

### **Example 3: Add Calendar View**

```python
def show_calendar_view(update: Update, context: CallbackContext):
    """Show visual calendar for the month"""
    try:
        # Create calendar grid
        calendar_text = "📅 **Календарь на месяц**\n\n"
        calendar_text += "Пн  Вт  Ср  Чт  Пт  Сб  Вс\n"
        
        # Add calendar logic here
        # This would show available/occupied dates
        
        keyboard = [
            [InlineKeyboardButton("📅 Выбрать дату", callback_data="select_date_from_calendar")],
            [InlineKeyboardButton("← Назад", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.callback_query.edit_message_text(
            text=calendar_text, 
            reply_markup=reply_markup, 
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error showing calendar: {e}")
```

## 🛠️ **Development Workflow**

### **1. Plan Your Feature**
- What should it do?
- How will users interact with it?
- What data needs to be stored?

### **2. Modify Code Locally**
- Add new functions
- Update existing handlers
- Test thoroughly

### **3. Update Database Structure**
- Add new fields to JSON files
- Handle data migration if needed

### **4. Deploy and Test**
- Deploy to server
- Test with real users
- Monitor for issues

## 📞 **Need Help with Specific Features?**

If you want to add a specific feature, tell me:
1. **What feature** you want to add
2. **How it should work**
3. **What data** it needs to store

I'll help you implement it step by step!

---

**🎯 Remember: Always test new features locally before deploying!**
