# 🚀 Deployment Guide for Telegram Interview Bot

## 📋 Prerequisites

- Git installed
- Docker and Docker Compose installed
- Telegram Bot Token from @BotFather
- Server with Linux/Windows support

## 🔧 Local Setup

### 1. Initialize Git Repository

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Telegram Interview Bot"

# Add remote repository (replace with your repo URL)
git remote add origin https://github.com/yourusername/telegram-interview-bot.git
git push -u origin main
```

### 2. Environment Configuration

Create a `.env` file in the root directory:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot locally
python interview_bot.py
```

## 🌐 Russian Hosting Providers

### 🥇 **Top Recommendations**

#### 1. **VDS.ru** (Русский хостинг)
- **Цена**: от 299₽/месяц
- **Преимущества**: 
  - Российские серверы
  - Техподдержка на русском
  - Простая панель управления
  - Docker поддержка
- **Сайт**: https://vds.ru

#### 2. **Timeweb** 
- **Цена**: от 199₽/месяц
- **Преимущества**:
  - Надежная инфраструктура
  - Автоматические бэкапы
  - SSL сертификаты
  - Docker контейнеры
- **Сайт**: https://timeweb.com

#### 3. **Jino** (Джино)
- **Цена**: от 150₽/месяц
- **Преимущества**:
  - Российские дата-центры
  - Быстрая техподдержка
  - Простое управление
- **Сайт**: https://jino.ru

#### 4. **Beget**
- **Цена**: от 119₽/месяц
- **Преимущества**:
  - Стабильная работа
  - Хорошая техподдержка
  - Простая настройка
- **Сайт**: https://beget.com

#### 5. **Reg.ru**
- **Цена**: от 199₽/месяц
- **Преимущества**:
  - Российский провайдер
  - Надежность
  - Docker поддержка
- **Сайт**: https://reg.ru

### 🏆 **Enterprise Solutions**

#### 1. **Yandex Cloud**
- **Цена**: от 500₽/месяц
- **Преимущества**:
  - Облачная инфраструктура
  - Автомасштабирование
  - Высокая надежность
  - Kubernetes поддержка

#### 2. **VK Cloud** (Mail.ru)
- **Цена**: от 400₽/месяц
- **Преимущества**:
  - Российское облако
  - Безопасность данных
  - Техподдержка 24/7

## 🚀 Deployment Steps

### Option 1: Docker Deployment (Recommended)

#### 1. Server Setup

```bash
# Connect to your server
ssh user@your-server-ip

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

#### 2. Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/telegram-interview-bot.git
cd telegram-interview-bot

# Create environment file
echo "TELEGRAM_BOT_TOKEN=your_bot_token_here" > .env

# Deploy using script
chmod +x deploy.sh
./deploy.sh production
```

### Option 2: Manual Deployment

#### 1. Server Preparation

```bash
# Install Python 3.9
sudo apt update
sudo apt install python3.9 python3.9-pip python3.9-venv

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Application Setup

```bash
# Create keys.py file
cat > keys.py << EOF
token = "your_bot_token_here"
EOF

# Create systemd service
sudo tee /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Interview Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegram-interview-bot
Environment=PATH=/home/ubuntu/telegram-interview-bot/venv/bin
ExecStart=/home/ubuntu/telegram-interview-bot/venv/bin/python interview_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### Option 3: Cloud Deployment

#### Using Yandex Cloud

```bash
# Install Yandex Cloud CLI
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Initialize
yc init

# Create VM instance
yc compute instance create \
  --name telegram-bot \
  --hostname telegram-bot \
  --memory 2 \
  --cores 2 \
  --core-fraction 20 \
  --preemptible \
  --network-interface subnet-name=default-ru-central1-a,ipv4-address=auto \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2004-lts,size=10 \
  --ssh-key ~/.ssh/id_rsa.pub
```

## 📊 Monitoring & Maintenance

### 1. Log Monitoring

```bash
# View logs
docker-compose logs -f telegram-bot

# Or for systemd
sudo journalctl -u telegram-bot -f
```

### 2. Health Checks

```bash
# Check bot status
docker-compose ps

# Test bot response
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
```

### 3. Backup Strategy

```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/telegram-bot"

mkdir -p $BACKUP_DIR

# Backup database files
tar -czf $BACKUP_DIR/database_$DATE.tar.gz *.json

# Backup logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Add to crontab
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

## 🔒 Security Considerations

### 1. Firewall Setup

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. SSL Certificate (if using webhooks)

```bash
# Install Certbot
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com
```

### 3. Environment Security

```bash
# Secure environment file
chmod 600 .env

# Use secrets management
echo $TELEGRAM_BOT_TOKEN | docker secret create telegram_bot_token -
```

## 📈 Performance Optimization

### 1. Resource Limits

```yaml
# Add to docker-compose.yml
services:
  telegram-bot:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### 2. Database Optimization

```python
# Add to interview_bot.py
import gc

# Periodic garbage collection
def cleanup_memory():
    gc.collect()

# Schedule cleanup every hour
scheduler.add_job(cleanup_memory, 'interval', hours=1)
```

## 🆘 Troubleshooting

### Common Issues

1. **Bot not responding**
   ```bash
   # Check logs
   docker-compose logs telegram-bot
   
   # Verify token
   curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"
   ```

2. **Database corruption**
   ```bash
   # Restore from backup
   tar -xzf backup/database_20241201_120000.tar.gz
   ```

3. **Memory issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Restart container
   docker-compose restart telegram-bot
   ```

## 📞 Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Verify configuration: `docker-compose config`
- Test connectivity: `ping api.telegram.org`

## 💰 Cost Estimation

### Monthly Costs (Russian Providers)

| Provider | Plan | Price | Features |
|----------|------|-------|----------|
| VDS.ru | Basic | 299₽ | 1 CPU, 1GB RAM, 10GB SSD |
| Timeweb | Starter | 199₽ | 1 CPU, 1GB RAM, 20GB SSD |
| Jino | Standard | 150₽ | 1 CPU, 1GB RAM, 15GB SSD |
| Beget | Basic | 119₽ | 1 CPU, 1GB RAM, 10GB SSD |

### Recommended Configuration
- **CPU**: 1-2 cores
- **RAM**: 1-2 GB
- **Storage**: 20-50 GB SSD
- **Bandwidth**: Unlimited
- **Estimated Cost**: 150-500₽/month

---

**🎯 Ready to deploy? Choose your hosting provider and follow the deployment steps above!**
