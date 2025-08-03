# 🤖 Telegram Interview Scheduling Bot

A fully functional Telegram bot for scheduling interviews with automatic notifications to a private channel.

## ✨ Features

- 📅 **Smart Date Selection**: Automatically shows next 5 weekdays
- ⏰ **Time Slot Booking**: 6 available time slots (9:00 AM - 5:00 PM)
- 📱 **Interactive Interface**: Inline keyboards for easy navigation
- 🔔 **Channel Notifications**: Automatic notifications to private channel
- 📋 **Booking Management**: View and manage existing bookings
- 🛡️ **Error Handling**: Robust error handling and logging
- 📊 **Detailed Logging**: Comprehensive logging for debugging

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.7+
- Telegram Bot Token (get from [@BotFather](https://t.me/BotFather))
- A private Telegram channel for notifications

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd prost_test

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

1. **Set up your bot token:**
   ```bash
   # Copy the template
   cp keys_template.py keys.py
   
   # Edit keys.py and add your bot token
   # Replace 'YOUR_BOT_TOKEN_HERE' with your actual token
   ```

2. **Configure your notification channel:**
   - Edit `notification_sender.py`
   - Change `CHANNEL_ID = "@ddd999dd999"` to your channel
   - Add your bot as admin to the channel with "Send Messages" permission

### 4. Run the Bot

```bash
python interview_bot.py
```

## 📁 Project Structure

```
prost_test/
├── interview_bot.py          # Main bot application
├── notification_sender.py    # Channel notification system
├── keys.py                   # Bot token (create from template)
├── keys_template.py          # Template for bot token
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── .gitignore               # Git ignore rules
├── test_channel.py          # Channel connection test
└── test_notification.py     # Notification system test
```

## 🎯 Bot Commands

- `/start` - Start the interview scheduling process
- `/help` - Show help information
- `/mybookings` - View your current bookings

## 📱 User Flow

1. **User sends `/start`**
2. **Bot shows 5 available weekdays** (Monday-Friday)
3. **User selects a date**
4. **Bot shows 6 time slots** (9:00-17:00 with lunch break)
5. **User selects a time**
6. **Bot shows booking confirmation**
7. **User confirms booking**
8. **Bot stores booking and sends notification to channel**

## 🔔 Channel Notifications

When a booking is made, the bot sends a notification to your configured channel:

```
📅 **New Interview Booking**

👤 **User:** @username
📅 **Date:** 05.08 Tuesday
⏰ **Time:** 10:00 - 11:00
🆔 **User ID:** 123456789
📝 **Booked at:** 04.08.2025 00:25:26
```

## 🛠️ Development

### Testing

```bash
# Test channel connection
python test_channel.py

# Test notification system
python test_notification.py

# Test notification sender
python notification_sender.py
```

### Logging

The bot uses detailed logging with DEBUG level. Check the console output for:
- User interactions
- Booking confirmations
- Channel notifications
- Error messages

## 🔧 Configuration Options

### Time Slots
Edit the `time_slots` list in `interview_bot.py`:
```python
time_slots = [
    "09:00 - 10:00",
    "10:00 - 11:00", 
    "11:00 - 12:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00"
]
```

### Available Days
The bot automatically shows the next 5 weekdays. This is calculated in the `get_available_dates()` function.

### Channel ID
Change the channel ID in `notification_sender.py`:
```python
CHANNEL_ID = "@your_channel_username"
```

## 🚨 Security Notes

- **Never commit `keys.py`** - it contains your bot token
- **Use `.gitignore`** - it's configured to exclude sensitive files
- **Keep your bot token private** - anyone with the token can control your bot

## 📝 Dependencies

- `python-telegram-bot==13.3` - Telegram Bot API wrapper
- `asyncio` - Asynchronous programming support
- `datetime` - Date and time handling
- `logging` - Logging system

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues:

1. Check the console logs for error messages
2. Verify your bot token is correct
3. Ensure your bot is added to the channel as admin
4. Test the channel connection with `python test_channel.py`

## 🎉 Success!

Your interview scheduling bot is now ready to help students book interviews efficiently! 🚀 