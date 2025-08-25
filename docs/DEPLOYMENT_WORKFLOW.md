# 🚀 Complete Deployment Workflow

## 🎯 **Step-by-Step Process**

### **Phase 1: Choose Your Hosting**

**🥇 Recommended: VDS.ru (from your image)**
- **Plan**: Облачные серверы VPS/VDS
- **Price**: 299₽/месяц
- **Why**: DDoS protection, application catalog, Russian servers

**Alternative Budget Options:**
- **Beget**: 119₽/месяц
- **Jino**: 150₽/месяц

### **Phase 2: Server Setup**

#### **1. Order VPS Server**
```bash
# You'll get these credentials:
# IP: 123.456.789.123
# Username: root
# Password: your_password
```

#### **2. Connect to Server**
```bash
# Windows (PowerShell)
ssh root@123.456.789.123

# Or use PuTTY on Windows
```

#### **3. Install Docker**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### **Phase 3: Deploy Your Bot**

#### **1. Upload Your Code**
```bash
# Clone your repository
git clone https://github.com/yourusername/telegram-interview-bot.git
cd telegram-interview-bot

# Or upload files manually via SFTP
```

#### **2. Configure Environment**
```bash
# Create environment file
echo "TELEGRAM_BOT_TOKEN=your_actual_bot_token_here" > .env

# Verify the file
cat .env
```

#### **3. Deploy**
```bash
# Make script executable
chmod +x deploy.sh

# Deploy to production
./deploy.sh production
```

### **Phase 4: Verify Deployment**

#### **1. Check Bot Status**
```bash
# Check if container is running
docker-compose ps

# Should show:
# interview-scheduling-bot    Up    telegram-bot
```

#### **2. Check Logs**
```bash
# View real-time logs
docker-compose logs -f telegram-bot

# Should show:
# INFO - Bot started successfully
# INFO - Scheduler started with Moscow timezone
```

#### **3. Test Bot**
- Open Telegram
- Find your bot
- Send `/start`
- Should respond with welcome message

## 🔄 **How Docker Works for Your Bot**

### **What Happens When You Deploy:**

1. **Docker Builds Container:**
   ```bash
   # This creates a package with your bot + all dependencies
   docker build -t telegram-bot .
   ```

2. **Docker Runs Container:**
   ```bash
   # This starts your bot in an isolated environment
   docker-compose up -d
   ```

3. **Auto-Restart:**
   ```bash
   # If bot crashes, Docker automatically restarts it
   restart: unless-stopped
   ```

4. **Persistent Data:**
   ```bash
   # Your database files are saved outside the container
   volumes:
     - ./data:/app/data
     - ./logs:/app/logs
   ```

### **Your Bot's Docker Architecture:**
```
┌─────────────────────────────────────┐
│           Your Server               │
├─────────────────────────────────────┤
│  ┌─────────────────────────────┐    │
│  │     Docker Container        │    │
│  │  ┌───────────────────────┐  │    │
│  │  │   Python 3.9          │  │    │
│  │  │   + Your Bot Code     │  │    │
│  │  │   + Dependencies      │  │    │
│  │  └───────────────────────┘  │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │     Host File System        │    │
│  │  • bookings.json            │    │
│  │  • users.json               │    │
│  │  • mentors.json             │    │
│  │  • logs/                    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

## 📅 **Making Calendar Changes**

### **Scenario 1: Add Evening Slots**

#### **Step 1: Edit Locally**
```python
# In interview_bot.py, change TIME_SLOTS:
TIME_SLOTS = [
    "09:00 - 10:00",
    "10:00 - 11:00", 
    "11:00 - 12:00",
    "12:00 - 13:00",
    "13:00 - 14:00",
    "14:00 - 15:00",
    "15:00 - 16:00",
    "16:00 - 17:00",
    "17:00 - 18:00",    # NEW: Evening slot
    "18:00 - 19:00"     # NEW: Late evening
]
```

#### **Step 2: Deploy Changes**
```bash
# On your local machine
git add .
git commit -m "Added evening time slots"
git push

# On your server
cd telegram-interview-bot
git pull
docker-compose up -d --build
```

#### **Step 3: Verify**
```bash
# Check logs
docker-compose logs -f telegram-bot

# Test bot
# Send /start and check if new slots appear
```

### **Scenario 2: Change Working Days**

#### **Step 1: Edit Locally**
```python
# In interview_bot.py, change DAY_NAMES:
DAY_NAMES = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
```

#### **Step 2: Deploy**
```bash
# Same process as above
git add .
git commit -m "Added Saturday to working days"
git push

# On server
git pull
docker-compose up -d --build
```

## 🛠️ **Daily Management Commands**

### **Check Bot Status:**
```bash
docker-compose ps
```

### **View Recent Logs:**
```bash
docker-compose logs --tail=20 telegram-bot
```

### **Restart Bot:**
```bash
docker-compose restart telegram-bot
```

### **Update Bot:**
```bash
git pull
docker-compose up -d --build
```

### **Backup Data:**
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz *.json
```

### **View Resource Usage:**
```bash
docker stats
```

## 🆘 **Troubleshooting**

### **Bot Not Responding:**
```bash
# Check if container is running
docker-compose ps

# Check logs for errors
docker-compose logs telegram-bot

# Restart if needed
docker-compose restart telegram-bot
```

### **Out of Memory:**
```bash
# Check memory usage
docker stats

# Restart container
docker-compose restart telegram-bot
```

### **Database Issues:**
```bash
# Backup current data
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz *.json

# Check file permissions
ls -la *.json
```

## 💰 **Cost Breakdown**

| Component | Monthly Cost |
|-----------|--------------|
| **VDS.ru Server** | 299₽ |
| **Domain (optional)** | 100₽/year |
| **SSL Certificate** | Free |
| **Total** | **299₽/month** |

## 🎯 **Next Steps**

1. **Choose VDS.ru** from the image you showed
2. **Order the basic VPS plan** (299₽/month)
3. **Follow the deployment steps** above
4. **Test your bot** thoroughly
5. **Start using it** with your students!

---

**🚀 Your bot will be running 24/7 with automatic restarts and easy management!**
