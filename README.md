# 🤖 Telegram Interview Scheduling Bot

A comprehensive Telegram bot for managing interview scheduling between students and mentors. Built with Python and the `python-telegram-bot` library.

## ✨ Features

### 🎯 Core Functionality
- **Smart Booking System**: Students can book interviews with their assigned mentors
- **Company Information**: Collects company name during booking process
- **Duration Selection**: Support for 1-hour and 1.5-2 hour interview slots
- **Automatic Reminders**: 1-hour advance notifications for scheduled interviews
- **Mentor Assignment**: Permanent mentor system with unlimited changes
- **Real-time Availability**: Dynamic time slot management

### 🔔 Notifications
- **Student → Mentor**: Notifications when students book interviews
- **Mentor → Student**: Notifications when mentors cancel interviews
- **Admin Channel**: All booking activities logged to private channel
- **Automatic Reminders**: Scheduled notifications before interviews

### 👥 User Management
- **Role-based Views**: Different interfaces for students and mentors
- **Profile System**: User statistics and booking history
- **Mentor Detection**: Automatic role recognition for mentors
- **Statistics Tracking**: Total bookings, upcoming, and cancelled interviews

### 📱 User Interface
- **Outline Buttons**: "Мои собеседования" and "Профиль" for easy navigation
- **Inline Keyboards**: Interactive booking and management interface
- **Command Suggestions**: Auto-complete when typing "/"
- **Responsive Design**: Works on all Telegram clients



## 🛠️ Technical Stack

- **Language**: Python 3.8+
- **Telegram API**: python-telegram-bot
- **Scheduler**: APScheduler with Moscow timezone
- **Database**: JSON-based storage (users.json, bookings.json, mentors.json)
- **Notifications**: Custom notification system

## 📋 Requirements

```bash
pip install -r requirements.txt
```

### Key Dependencies
- `python-telegram-bot==13.7`
- `APScheduler==3.9.1`
- `pytz==2021.3`

## ⚙️ Configuration

### 1. Bot Token Setup
Create a `keys.py` file with your Telegram bot token:
```python
BOT_TOKEN = "your_bot_token_here"
ADMIN_CHANNEL_ID = "@your_channel_username"
```

### 2. Mentor Configuration
Configure mentors in `interview_bot.py`:
```python
MENTORS = {
    "mentor_1": {
        "name": "Илья",
        "username": "@yashonflame",
        "user_id": 780202036,
        "max_students": 5,
        "specialization": "Full Stack Development"
    }
}
```

### 3. Time Slots
Customize available time slots:
```python
TIME_SLOTS = [
    "09:00 - 10:00",
    "10:00 - 11:00",
    "11:00 - 12:00",
    # ... add more slots
]
```

## 🚀 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/lapurryt/prost_test.git
   cd prost_test
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your bot**:
   - Create `keys.py` with your bot token
   - Update mentor configurations
   - Set up admin channel

4. **Run the bot**:
   ```bash
   python interview_bot.py
   ```

## 📊 Database Structure

### Users Database (`users.json`)
```json
{
  "user_id": {
    "user_id": 123456789,
    "username": "@username",
    "first_name": "Name",
    "registration_date": "2025-08-04 20:30:00",
    "total_bookings_made": 5
  }
}
```

### Bookings Database (`bookings.json`)
```json
{
  "date_mentor_id_slot": {
    "user_id": 123456789,
    "date": "2025-08-05",
    "time": "09:00 - 10:00",
    "mentor_id": "mentor_1",
    "duration": "1h",
    "company": "Company Name",
    "booked_at": "2025-08-04 20:30:00"
  }
}
```

### Mentors Database (`mentors.json`)
```json
{
  "user_id": {
    "permanent_mentor": "mentor_1"
  }
}
```

## 🎮 Usage

### For Students
1. **Start the bot**: `/start`
2. **Choose mentor**: Select your permanent mentor
3. **Book interview**: Pick date, time, and duration
4. **Manage bookings**: Use "Мои собеседования" button
5. **View profile**: Check statistics and change mentor

### For Mentors
1. **View interviews**: "Мои собеседования" shows waiting students
2. **Cancel interviews**: Remove bookings with student notifications
3. **Receive notifications**: Get alerts when students book

### Commands
- `/start` - Start booking process
- `/profile` - View user profile and statistics
- `/mybookings` - View current bookings
- `/help` - Show help information
- `/all <text>` - Send broadcast message to all users (admin only)



## 🔧 Customization

### Adding New Mentors
1. Update `MENTORS` dictionary in `interview_bot.py`
2. Add mentor information and user_id
3. Restart the bot

### Modifying Time Slots
1. Edit `TIME_SLOTS` array in `interview_bot.py`
2. Adjust available hours as needed
3. Restart the bot

### Changing Timezone
1. Update timezone in scheduler initialization
2. Modify `pytz.timezone('Europe/Moscow')` to your timezone

## 🛡️ Security Features

- **Token Protection**: Bot tokens stored in separate `keys.py` file
- **User Validation**: All user inputs validated and sanitized
- **Role-based Access**: Different permissions for students and mentors
- **Database Backup**: JSON files can be easily backed up

## 📈 Statistics System

The bot tracks comprehensive statistics:
- **Total Bookings**: All bookings ever made (never decreases)
- **Upcoming Interviews**: Current active bookings
- **Cancelled Interviews**: Calculated as total - upcoming

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

For issues and questions:
- Create an issue on GitHub
- Check the logs for error details
- Ensure all dependencies are installed

## 🔄 Recent Updates

- ✅ **Broadcast System**: Added `/all` command for admin to send messages to all users
- ✅ **Company Information Collection**: Added company name collection during booking process
- ✅ **Simple Chronological Sorting**: All interviews sorted by date and time in ascending order
- ✅ Fixed statistics calculation
- ✅ Added outline buttons for navigation
- ✅ Implemented mentor notifications
- ✅ Added 2-hour booking support
- ✅ Enhanced user experience with better UI

---

**Built with ❤️ for efficient interview scheduling** 