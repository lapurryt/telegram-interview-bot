# Interview Scheduling Bot for Telegram

A comprehensive Telegram bot for managing interview scheduling with automatic reminders and admin notifications.

## Features

- 📅 **Date Selection**: Choose from available weekdays (Monday-Friday)
- ⏰ **Time Slots**: 6 time slots per day (9:00-17:00 with lunch break)
- 🔔 **Automatic Reminders**: Get notified 1 hour before your interview
- 📢 **Admin Notifications**: All bookings sent to private admin channel
- ❌ **Booking Cancellation**: Cancel your bookings anytime
- 🚫 **Conflict Prevention**: No double bookings for the same time slot
- 🇷🇺 **Russian Interface**: Full Russian language support
- 🕐 **Moscow Timezone**: Configured for Moscow time (UTC+3)

## Files Structure

```
prost_test/
├── interview_bot.py          # Main bot application
├── notification_sender.py    # Admin channel notifications
├── keys.py                   # Bot token (not in git)
├── keys_template.py          # Template for keys.py
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .gitignore               # Git ignore rules
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Bot Token

1. Copy `keys_template.py` to `keys.py`
2. Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token from @BotFather

```python
# keys.py
token = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
```

### 3. Configure Admin Channel

1. Create a private Telegram channel
2. Add your bot as an admin with "Send Messages" permission
3. Update `CHANNEL_ID` in `notification_sender.py`:

```python
CHANNEL_ID = "@your_channel_username"
```

### 4. Run the Bot

```bash
python interview_bot.py
```

## Bot Commands

- `/start` - Start booking process
- `/help` - Show help information
- `/mybookings` - View and cancel your bookings

## How It Works

### For Students:
1. Send `/start` to begin booking
2. Select a date from available weekdays
3. Choose an available time slot
4. Confirm your booking
5. Receive reminder 1 hour before interview

### For Admins:
- All bookings are automatically logged to your private channel
- Cancellations are also notified
- Reminder notifications show when reminders are sent to students

## Time Slots

- **Morning**: 09:00-10:00, 10:00-11:00, 11:00-12:00
- **Afternoon**: 14:00-15:00, 15:00-16:00, 16:00-17:00

## Reminder System

- Reminders are sent 1 hour before the interview start time
- Uses Moscow timezone (UTC+3)
- Both student and admin receive notifications

## Booking Conflict Prevention

- Real-time availability checking
- Visual indicators for booked/available slots
- Prevents double bookings for the same time slot

## Dependencies

- `python-telegram-bot==13.3` - Telegram Bot API
- `APScheduler==3.6.3` - Background task scheduling
- `pytz` - Timezone handling

## Configuration

### Timezone
The bot is configured for Moscow time (UTC+3). To change timezone:

1. Update scheduler initialization in `interview_bot.py`:
```python
scheduler = BackgroundScheduler(timezone=pytz.timezone('Your/Timezone'))
```

2. Update reminder scheduling in `schedule_reminder()` function

### Time Slots
Modify `TIME_SLOTS` list in `interview_bot.py` to change available times.

### Channel Notifications
Update `CHANNEL_ID` in `notification_sender.py` to change admin channel.

## Troubleshooting

### Bot Not Responding
1. Check if bot token is correct in `keys.py`
2. Ensure bot is not blocked by users
3. Check logs for error messages

### Channel Notifications Not Working
1. Verify bot is admin in the channel
2. Check bot has "Send Messages" permission
3. Ensure channel ID is correct (include @ symbol)

### Reminders Not Sending
1. Check timezone configuration
2. Verify APScheduler is running
3. Check logs for scheduling errors

## Security Notes

- Never commit `keys.py` to version control
- Keep your bot token secure
- Regularly update dependencies

## Development

### Adding New Features
1. Create feature branch: `git checkout -b feature-name`
2. Implement changes
3. Test thoroughly
4. Create pull request

### Testing
- Test booking flow with multiple users
- Verify reminder scheduling
- Check admin notifications
- Test cancellation functionality

## License

This project is for educational and personal use.

## Support

For issues or questions, check the logs or review the code comments for debugging information. 