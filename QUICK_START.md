# 🚀 Quick Start Guide - Telegram Interview Bot

## ⚡ 5-Minute Deployment

### 1. Choose Your Hosting (Russian Providers)

**🥇 Recommended for Budget:**
- **Beget** - 119₽/месяц - https://beget.com
- **Jino** - 150₽/месяц - https://jino.ru

**🏆 Recommended for Reliability:**
- **Timeweb** - 199₽/месяц - https://timeweb.com
- **VDS.ru** - 299₽/месяц - https://vds.ru

### 2. Server Setup (Ubuntu/Debian)

```bash
# Connect to your server
ssh root@your-server-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Deploy Your Bot

```bash
# Clone your repository
git clone https://github.com/yourusername/telegram-interview-bot.git
cd telegram-interview-bot

# Create environment file
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env

# Deploy
chmod +x deploy.sh
./deploy.sh production
```

### 4. Verify Deployment

```bash
# Check if bot is running
docker-compose ps

# View logs
docker-compose logs -f telegram-bot

# Test bot
# Send /start to your bot on Telegram
```

## 📋 What You Get

✅ **Fully Functional Bot** with:
- Interview scheduling system
- Mentor assignment
- Automatic reminders
- Admin notifications
- User management
- Booking statistics

✅ **Production Ready** with:
- Docker containerization
- Auto-restart on failure
- Log monitoring
- Backup system
- Security configurations

✅ **Monitoring** with:
- Prometheus metrics
- Grafana dashboards
- Health checks
- Performance monitoring

## 💰 Cost Breakdown

| Component | Monthly Cost |
|-----------|--------------|
| **Server (Beget/Jino)** | 119-150₽ |
| **Domain (optional)** | 100₽/year |
| **SSL Certificate** | Free (Let's Encrypt) |
| **Total** | **119-150₽/month** |

## 🔧 Management Commands

```bash
# Start bot
docker-compose up -d

# Stop bot
docker-compose down

# View logs
docker-compose logs -f telegram-bot

# Restart bot
docker-compose restart telegram-bot

# Update bot
git pull && docker-compose up -d --build

# Backup data
tar -czf backup_$(date +%Y%m%d).tar.gz *.json
```

## 🆘 Common Issues

**Bot not responding?**
```bash
# Check logs
docker-compose logs telegram-bot

# Verify token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
```

**Server out of memory?**
```bash
# Check usage
docker stats

# Restart container
docker-compose restart telegram-bot
```

## 📞 Support

- **Hosting Issues**: Contact your provider's support
- **Bot Issues**: Check logs and Telegram API status
- **Code Issues**: Review GitHub repository

---

**🎯 Your bot is ready to serve students and mentors!**
