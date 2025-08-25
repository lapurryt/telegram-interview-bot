# Telegram Bot Deployment Script for Windows
# Usage: .\deploy.ps1 [production|staging]

param(
    [string]$Environment = "production"
)

Write-Host "🚀 Deploying Telegram Bot to $Environment environment..." -ForegroundColor Green

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Error ".env file not found! Please create it with your bot token:"
    Write-Host "TELEGRAM_BOT_TOKEN=your_bot_token_here"
    exit 1
}

# Load environment variables
Get-Content .env | ForEach-Object {
    if ($_ -match "^([^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Check if bot token is set
if (-not $env:TELEGRAM_BOT_TOKEN) {
    Write-Error "TELEGRAM_BOT_TOKEN not set in .env file!"
    exit 1
}

Write-Status "Environment variables loaded successfully"

# Create necessary directories
New-Item -ItemType Directory -Force -Path "data", "logs", "monitoring" | Out-Null

# Create monitoring configuration if it doesn't exist
if (-not (Test-Path "monitoring/prometheus.yml")) {
    Write-Status "Creating Prometheus configuration..."
    @"
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'telegram-bot'
    static_configs:
      - targets: ['telegram-bot:8080']
"@ | Out-File -FilePath "monitoring/prometheus.yml" -Encoding UTF8
}

# Stop existing containers
Write-Status "Stopping existing containers..."
docker-compose down 2>$null

# Build and start services
Write-Status "Building and starting services..."
if ($Environment -eq "production") {
    docker-compose up -d --build telegram-bot
    Write-Warning "Production mode: Only bot service started"
    Write-Warning "To start monitoring, run: docker-compose up -d"
} else {
    docker-compose up -d --build
    Write-Status "Staging mode: All services started including monitoring"
}

# Wait for bot to start
Write-Status "Waiting for bot to start..."
Start-Sleep -Seconds 10

# Check if bot is running
if (docker-compose ps | Select-String "Up") {
    Write-Status "✅ Bot deployed successfully!"
    Write-Status "📊 Logs: docker-compose logs -f telegram-bot"
    Write-Status "🛑 Stop: docker-compose down"
    Write-Status "🔄 Restart: docker-compose restart telegram-bot"
    
    if ($Environment -eq "staging") {
        Write-Status "📈 Monitoring available at:"
        Write-Status "   - Prometheus: http://localhost:9090"
        Write-Status "   - Grafana: http://localhost:3000 (admin/admin)"
    }
} else {
    Write-Error "❌ Bot failed to start!"
    Write-Status "Check logs: docker-compose logs telegram-bot"
    exit 1
}
