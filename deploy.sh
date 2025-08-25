#!/bin/bash

# Telegram Bot Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
echo "🚀 Deploying Telegram Bot to $ENVIRONMENT environment..."

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

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found! Please create it with your bot token:"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    exit 1
fi

# Load environment variables
source .env

# Check if bot token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    print_error "TELEGRAM_BOT_TOKEN not set in .env file!"
    exit 1
fi

print_status "Environment variables loaded successfully"

# Create necessary directories
mkdir -p data logs monitoring

# Create monitoring configuration if it doesn't exist
if [ ! -f monitoring/prometheus.yml ]; then
    print_status "Creating Prometheus configuration..."
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'telegram-bot'
    static_configs:
      - targets: ['telegram-bot:8080']
EOF
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Build and start services
print_status "Building and starting services..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose up -d --build telegram-bot
    print_warning "Production mode: Only bot service started"
    print_warning "To start monitoring, run: docker-compose up -d"
else
    docker-compose up -d --build
    print_status "Staging mode: All services started including monitoring"
fi

# Wait for bot to start
print_status "Waiting for bot to start..."
sleep 10

# Check if bot is running
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Bot deployed successfully!"
    print_status "📊 Logs: docker-compose logs -f telegram-bot"
    print_status "🛑 Stop: docker-compose down"
    print_status "🔄 Restart: docker-compose restart telegram-bot"
    
    if [ "$ENVIRONMENT" = "staging" ]; then
        print_status "📈 Monitoring available at:"
        print_status "   - Prometheus: http://localhost:9090"
        print_status "   - Grafana: http://localhost:3000 (admin/admin)"
    fi
else
    print_error "❌ Bot failed to start!"
    print_status "Check logs: docker-compose logs telegram-bot"
    exit 1
fi
