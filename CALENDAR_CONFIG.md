# 📅 Calendar Configuration Guide

## 🕐 **How to Change Time Slots**

### **Current Time Slots (Lines 60-69 in interview_bot.py):**
```python
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
```

### **Example Changes:**

#### **1. Add More Time Slots:**
```python
TIME_SLOTS = [
    "08:00 - 09:00",    # Early morning
    "09:00 - 10:00",
    "10:00 - 11:00", 
    "11:00 - 12:00",
    "12:00 - 13:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00",
    "17:00 - 18:00",    # Evening slot
    "18:00 - 19:00"     # Late evening
]
```

#### **2. Change Working Hours:**
```python
TIME_SLOTS = [
    "10:00 - 11:00",    # Start later
    "11:00 - 12:00", 
    "12:00 - 13:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00",
    "17:00 - 18:00"     # End later
]
```

#### **3. Weekend Slots:**
```python
TIME_SLOTS = [
    "10:00 - 11:00",
    "11:00 - 12:00", 
    "12:00 - 13:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00"
]
```

## 📅 **How to Change Available Days**

### **Current Day Names (Line 72):**
```python
DAY_NAMES = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница']
```

### **Example Changes:**

#### **1. Add Weekend Days:**
```python
DAY_NAMES = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
```

#### **2. Change to Weekend Only:**
```python
DAY_NAMES = ['Суббота', 'Воскресенье']
```

## 👥 **How to Change Mentors**

### **Current Mentors (Lines 30-49):**
```python
MENTORS = {
    "mentor_1": {
        "name": "Илья",
        "username": "@yashonflame",
        "user_id": 780202036,
        "max_students": 5,
        "specialization": "Full Stack Development"
    },
    "mentor_2": {
        "name": "Андрей",
        "username": "@hxcnv",
        "user_id": 887557370,
        "max_students": 5,
        "specialization": "Backend Development"
    }
}
```

### **Example Changes:**

#### **1. Add New Mentor:**
```python
MENTORS = {
    "mentor_1": {
        "name": "Илья",
        "username": "@yashonflame",
        "user_id": 780202036,
        "max_students": 5,
        "specialization": "Full Stack Development"
    },
    "mentor_2": {
        "name": "Андрей",
        "username": "@hxcnv",
        "user_id": 887557370,
        "max_students": 5,
        "specialization": "Backend Development"
    },
    "mentor_3": {
        "name": "Мария",
        "username": "@maria_dev",
        "user_id": 123456789,
        "max_students": 3,
        "specialization": "Frontend Development"
    }
}
```

#### **2. Change Max Students:**
```python
"max_students": 10,  # Allow more students per mentor
```

## 🔄 **How to Deploy Changes**

### **Step 1: Make Changes Locally**
1. Edit `interview_bot.py`
2. Modify the settings you want
3. Test locally: `python interview_bot.py`

### **Step 2: Deploy to Server**

#### **Option A: Git + Docker (Recommended)**
```bash
# On your local machine
git add .
git commit -m "Updated time slots and mentors"
git push

# On your server
cd telegram-interview-bot
git pull
docker-compose up -d --build
```

#### **Option B: Direct File Edit**
```bash
# Connect to your server
ssh user@your-server-ip

# Edit the file directly
nano interview_bot.py

# Restart the bot
docker-compose restart telegram-bot
```

### **Step 3: Verify Changes**
```bash
# Check if bot is running
docker-compose ps

# View logs
docker-compose logs -f telegram-bot

# Test the bot
# Send /start to your bot on Telegram
```

## ⚠️ **Important Notes**

### **⚠️ Existing Bookings:**
- **Time slot changes** will affect **new bookings only**
- **Existing bookings** will remain unchanged
- **Mentor changes** will affect **new user assignments only**

### **⚠️ Database Impact:**
- **Adding time slots**: Safe, no impact on existing data
- **Removing time slots**: May cause issues with existing bookings
- **Changing mentor IDs**: Will break existing mentor assignments

### **⚠️ Best Practices:**
1. **Test changes locally** before deploying
2. **Backup your database** before major changes
3. **Deploy during low-usage hours**
4. **Notify users** about schedule changes

## 🛠️ **Quick Commands for Changes**

```bash
# View current bot status
docker-compose ps

# View recent logs
docker-compose logs --tail=50 telegram-bot

# Restart bot after changes
docker-compose restart telegram-bot

# Full rebuild (if major changes)
docker-compose up -d --build

# Backup database before changes
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz *.json

# Restore from backup (if needed)
tar -xzf backup_20241201_120000.tar.gz
```

## 📞 **Need Help?**

If you need help with specific changes:
1. **Backup your current settings**
2. **Make small changes first**
3. **Test thoroughly**
4. **Deploy during quiet hours**

---

**🎯 Remember: Always test changes locally before deploying to production!**
