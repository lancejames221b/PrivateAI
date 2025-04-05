#!/bin/bash

# AI Security Proxy - Production Deployment Script
# ===============================================

# Exit on error
set -e

# Function to handle errors
handle_error() {
    echo "Error occurred at line $1"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Function to display usage
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -p, --port PORT       Specify proxy port (default: 8080)"
    echo "  -h, --health-port PORT Specify health check port (default: 8081)"
    echo "  -w, --workers N       Number of worker processes (for mitm mode)"
    echo "  -b, --bind ADDR       Bind address (default: 0.0.0.0)"
    echo "  -r, --rate-limit RPM  Enable rate limiting with requests per minute"
    echo "  -l, --log-level LEVEL Set log level (debug, info, warn, error)"
    echo "  -m, --mitm            Use mitmproxy instead of standalone proxy"
    echo "  -d, --daemon          Run in daemon mode (background)"
    echo "  --help                Show this help message"
    exit 1
}

# Default values for production
PROXY_TYPE="standalone"
LOG_LEVEL="info"
BIND_ADDR="0.0.0.0"
DAEMON_MODE=false
RATE_LIMIT_RPM=60

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            export PROXY_PORT="$2"
            shift 2
            ;;
        -h|--health-port)
            export HEALTH_PORT="$2"
            shift 2
            ;;
        -w|--workers)
            export WORKERS="$2"
            shift 2
            ;;
        -b|--bind)
            BIND_ADDR="$2"
            shift 2
            ;;
        -r|--rate-limit)
            export ENABLE_RATE_LIMITING="true"
            export RATE_LIMIT_RPM="$2"
            shift 2
            ;;
        -l|--log-level)
            export LOG_LEVEL="$2"
            shift 2
            ;;
        -m|--mitm)
            PROXY_TYPE="mitm"
            shift
            ;;
        -d|--daemon)
            DAEMON_MODE=true
            shift
            ;;
        --help)
            print_usage
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            ;;
    esac
done

# Create required directories
mkdir -p data
mkdir -p logs

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    source .env
fi

# Set production environment variables
export FLASK_ENV="production"
export FLASK_DEBUG=0
export PROXY_PORT=${PROXY_PORT:-8080}
export HEALTH_PORT=${HEALTH_PORT:-8081}
export ENABLE_HEALTH_CHECK=${ENABLE_HEALTH_CHECK:-true}
export ENABLE_RATE_LIMITING=${ENABLE_RATE_LIMITING:-true}
export RATE_LIMIT_RPM=${RATE_LIMIT_RPM:-60}
export BASIC_AUTH_ENABLED=${BASIC_AUTH_ENABLED:-true}
export MAX_REQUEST_SIZE=${MAX_REQUEST_SIZE:-10485760}  # 10MB

# Generate a secure random key if not already set
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(openssl rand -hex 24)
fi

# Set up log rotation
if command -v logrotate &> /dev/null; then
    # Create logrotate config if it doesn't exist
    if [ ! -f logs/logrotate.conf ]; then
        cat > logs/logrotate.conf << EOF
logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        [ -f logs/proxy.pid ] && kill -USR1 \$(cat logs/proxy.pid) 2>/dev/null || true
    endscript
}
EOF
    fi
    
    # Set up cron job for log rotation if not already set up
    if ! crontab -l 2>/dev/null | grep -q "logrotate.*logs/logrotate.conf"; then
        (crontab -l 2>/dev/null; echo "0 0 * * * logrotate -s logs/logrotate.status logs/logrotate.conf") | crontab -
        echo "Set up log rotation cron job"
    fi
fi

# Log configuration
echo "Starting AI Security Proxy in PRODUCTION mode with configuration:"
echo "- Proxy Port: ${PROXY_PORT}"
echo "- Health Port: ${HEALTH_PORT}"
echo "- Bind Address: ${BIND_ADDR}"
echo "- Rate Limiting: ${ENABLE_RATE_LIMITING} (${RATE_LIMIT_RPM} RPM)"
echo "- Log Level: ${LOG_LEVEL}"
echo "- Proxy Type: ${PROXY_TYPE}"

# Write PID file for process management
echo $$ > logs/proxy.pid

# Run in daemon mode if requested
if [ "$DAEMON_MODE" = true ]; then
    echo "Starting in daemon mode..."
    
    # Redirect output to log files
    if [ "$PROXY_TYPE" = "mitm" ]; then
        nohup mitmdump -s proxy_intercept.py --listen-host ${BIND_ADDR} --listen-port ${PROXY_PORT} --set block_global=false --no-http2 > logs/proxy.out 2> logs/proxy.err &
    else
        nohup python3 ai_proxy.py > logs/proxy.out 2> logs/proxy.err &
    fi
    
    echo "Proxy started in background. PID: $!"
    echo "Check logs/proxy.out and logs/proxy.err for output"
    exit 0
else
    # Run in foreground
    if [ "$PROXY_TYPE" = "mitm" ]; then
        echo "Starting mitmproxy-based proxy..."
        exec mitmdump -s proxy_intercept.py --listen-host ${BIND_ADDR} --listen-port ${PROXY_PORT} --set block_global=false --no-http2
    else
        echo "Starting standalone proxy..."
        exec python3 ai_proxy.py
    fi
fi