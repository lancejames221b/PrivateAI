#!/bin/bash

# AI Security Proxy - Production Version
# =====================================

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
    echo "  -m, --mitm            Use mitmproxy instead of standalone proxy"
    echo "  -v, --verbose         Enable verbose logging"
    echo "  -p, --port PORT       Specify proxy port (default: 8080)"
    echo "  -h, --health-port PORT Specify health check port (default: 8081)"
    echo "  -l, --log-level LEVEL Set log level (debug, info, warn, error)"
    echo "  -r, --rate-limit      Enable rate limiting"
    echo "  -e, --env ENV         Set environment (development, production)"
    echo "  -b, --bind ADDR       Bind address (default: localhost for dev, 0.0.0.0 for prod)"
    echo "  --help                Show this help message"
    exit 1
}

# Default values
PROXY_TYPE="standalone"
VERBOSE=""
LOG_LEVEL="info"
ENVIRONMENT="development"
RATE_LIMIT="false"
BIND_ADDR=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--mitm)
            PROXY_TYPE="mitm"
            shift
            ;;
        -v|--verbose)
            VERBOSE="--set console_eventlog_verbosity=debug"
            export LOG_LEVEL="debug"
            shift
            ;;
        -p|--port)
            export PROXY_PORT="$2"
            shift 2
            ;;
        -h|--health-port)
            export HEALTH_PORT="$2"
            shift 2
            ;;
        -l|--log-level)
            export LOG_LEVEL="$2"
            shift 2
            ;;
        -r|--rate-limit)
            export ENABLE_RATE_LIMITING="true"
            shift
            ;;
        -e|--env)
            ENVIRONMENT="$2"
            export FLASK_ENV="$2"
            shift 2
            ;;
        -b|--bind)
            BIND_ADDR="$2"
            shift 2
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

# Set environment variables for configuration
export BLOCK_ALL_DOMAINS=${BLOCK_ALL_DOMAINS:-false}
export PROXY_PORT=${PROXY_PORT:-8080}
export HEALTH_PORT=${HEALTH_PORT:-8081}
export ENCRYPT_DATABASE=${ENCRYPT_DATABASE:-true}
export ENABLE_HEALTH_CHECK=${ENABLE_HEALTH_CHECK:-true}
export ENABLE_RATE_LIMITING=${ENABLE_RATE_LIMITING:-$RATE_LIMIT}
export FLASK_ENV=${FLASK_ENV:-$ENVIRONMENT}

# Set production-specific settings
if [ "$FLASK_ENV" = "production" ]; then
    echo "Running in PRODUCTION mode"
    export FLASK_DEBUG=0
    
    # Generate a secure random key if not already set
    if [ -z "$SECRET_KEY" ]; then
        export SECRET_KEY=$(openssl rand -hex 24)
    fi
    
    # Enable basic auth by default in production
    export BASIC_AUTH_ENABLED=${BASIC_AUTH_ENABLED:-true}
    
    # Set default bind address for production
    if [ -z "$BIND_ADDR" ]; then
        BIND_ADDR="0.0.0.0"
    fi
else
    echo "Running in DEVELOPMENT mode"
    export FLASK_DEBUG=1
    
    # Set default bind address for development
    if [ -z "$BIND_ADDR" ]; then
        BIND_ADDR="localhost"
    fi
fi

# Check if we need to download transformers models
if [ ! -d $HOME/.cache/huggingface ]; then
    echo "Downloading models (this will only happen once)..."
    echo "This may take a few minutes..."
fi

# Log configuration
echo "Starting AI Security Proxy with configuration:"
echo "- Proxy Port: ${PROXY_PORT}"
echo "- Health Port: ${HEALTH_PORT}"
echo "- Environment: ${FLASK_ENV}"
echo "- Bind Address: ${BIND_ADDR}"
echo "- Rate Limiting: ${ENABLE_RATE_LIMITING}"
echo "- Block All Domains: ${BLOCK_ALL_DOMAINS}"
echo "- Log Level: ${LOG_LEVEL}"
echo "- Proxy Type: ${PROXY_TYPE}"

# Write PID file for process management
echo $$ > logs/proxy.pid

# Run the appropriate proxy based on the selected type
if [ "$PROXY_TYPE" = "mitm" ]; then
    echo "Starting mitmproxy-based proxy..."
    exec mitmdump -s proxy_intercept.py --listen-host ${BIND_ADDR} --listen-port ${PROXY_PORT} --set block_global=false ${VERBOSE} --no-http2
else
    echo "Starting standalone proxy..."
    exec python3 ai_proxy.py
fi