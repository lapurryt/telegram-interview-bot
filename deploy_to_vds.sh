#!/bin/bash

# Telegram Bot Deployment Script for VDS
# This script will automatically deploy your bot to the VDS server

set -e

echo "🚀 Starting Telegram Bot Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Bot token
BOT_TOKEN="8186291228:AAFn_NZ3imH6Lpevm8JDSHJRWy8XqaWEmEg"

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing dependencies..."
apt install -y python3 python3-pip git curl wget nano

print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
else
    print_status "Docker already installed"
fi

print_status "Starting Docker service..."
systemctl start docker
systemctl enable docker

print_status "Cloning repository..."
if [ -d "telegram-interview-bot" ]; then
    print_warning "Repository already exists, pulling latest changes..."
    cd telegram-interview-bot
    git pull
else
    git clone https://github.com/lapurryt/telegram-interview-bot.git
    cd telegram-interview-bot
fi

print_status "Setting up bot token..."
cat > keys.py << EOF
token = "$BOT_TOKEN"
EOF

print_status "Verifying setup..."
echo "Bot token configured:"
cat keys.py
echo ""
echo "Data files:"
ls -la data/

print_status "Building and starting Docker containers..."
docker-compose down 2>/dev/null || true
docker-compose up -d --build

print_status "Waiting for bot to start..."
sleep 10

print_status "Checking bot status..."
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Bot deployed successfully!"
    print_status "📊 View logs: docker-compose logs -f telegram-bot"
    print_status "🛑 Stop bot: docker-compose down"
    print_status "🔄 Restart bot: docker-compose restart telegram-bot"
    
    echo ""
    print_status "📱 Your bot should now be running!"
    print_status "Test it by sending /start to your bot in Telegram"
    
    # Show recent logs
    echo ""
    print_status "Recent bot logs:"
    docker-compose logs --tail=20 telegram-bot
    
else
    print_error "❌ Bot failed to start!"
    print_status "Check logs: docker-compose logs telegram-bot"
    exit 1
fi
