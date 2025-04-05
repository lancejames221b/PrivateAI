#!/bin/bash

# AI Security Proxy - One Page Admin Interface Production Script
# ============================================================

# Exit on error
set -e

# Function to handle errors
handle_error() {
    echo "Error occurred at line $1"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Install certificates function
setup_certificates() {
    echo "Setting up mitmproxy certificates..."
    
    # Run certificate setup script
    if [ -f "./setup_certificates.sh" ]; then
        chmod +x ./setup_certificates.sh
        ./setup_certificates.sh
    else
        echo "Certificate setup script not found."
        echo "Please run mitmproxy once to generate certificates, then run setup_certificates.sh"
    fi
}

# Function to display usage
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -p, --production    Run in production mode (default)"
    echo "  -d, --development   Run in development mode"
    echo "  --port PORT         Specify port (default: 5002)"
    echo "  --host HOST         Specify host (default: 0.0.0.0)"
    echo "  --workers N         Number of workers for production (default: 4)"
    echo "  --threads N         Number of threads per worker (default: 2)"
    echo "  --timeout SEC       Worker timeout in seconds (default: 120)"
    echo "  --daemon            Run in daemon mode (background)"
    echo "  --no-cert           Skip certificate installation"
    echo "  -h, --help          Show this help message"
    exit 1
}

# Default values
MODE="production"
PORT=5002
HOST="0.0.0.0"
WORKERS=4
THREADS=2
TIMEOUT=120
DAEMON=false
SKIP_CERT=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--production)
            MODE="production"
            shift
            ;;
        -d|--development)
            MODE="development"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --threads)
            THREADS="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --daemon)
            DAEMON=true
            shift
            ;;
        --no-cert)
            SKIP_CERT=true
            shift
            ;;
        -h|--help)
            print_usage
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            ;;
    esac
done

# Create required directories
mkdir -p data logs

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    source .env
fi

# Install certificates if needed
if [ "$SKIP_CERT" = false ] && [ ! -f "$HOME/.mitmproxy/mitmproxy-ca-cert.pem" ]; then
    setup_certificates
fi

# Initialize domains file if it doesn't exist
if [ ! -f "data/ai_domains.json" ]; then
    echo "Initializing AI domains configuration..."
    cp data/ai_domains.json.example data/ai_domains.json 2>/dev/null || echo '{"openai": ["api.openai.com"], "anthropic": ["api.anthropic.com"], "google": ["generativelanguage.googleapis.com"], "mistral": ["api.mistral.ai"], "ide": ["vscode-copilot.githubusercontent.com", "api.githubcopilot.com"], "azure": ["api.cognitive.microsoft.com"]}' > data/ai_domains.json
fi

# Set environment variables for configuration
export FLASK_APP=run_app.py
export FLASK_ENV=$MODE
export PYTHONUNBUFFERED=1
export PORT=$PORT
export HOST=$HOST
export WORKERS=$WORKERS
export THREADS=$THREADS
export TIMEOUT=$TIMEOUT
export ENABLE_DOMAIN_MANAGEMENT=true

# Log configuration
echo "Starting AI Security Proxy Admin Interface with configuration:"
echo "- Mode: ${MODE}"
echo "- Host: ${HOST}"
echo "- Port: ${PORT}"
echo "- Workers: ${WORKERS}"
echo "- Threads: ${THREADS}"
echo "- Timeout: ${TIMEOUT}"
echo "- Domain Management: Enabled"

# Write PID file for process management
echo $$ > logs/admin.pid

# Run in daemon mode if requested
if [ "$DAEMON" = true ]; then
    echo "Starting in daemon mode..."
    
    # Redirect output to log files
    if [ "$MODE" = "production" ]; then
        nohup waitress-serve --port=$PORT --host=$HOST --threads=$THREADS --connection-limit=1000 --url-scheme=http run_app:app > logs/admin.out 2> logs/admin.err &
    else
        nohup python run_app.py > logs/admin.out 2> logs/admin.err &
    fi
    
    echo "Admin interface started in background. PID: $!"
    echo "Check logs/admin.out and logs/admin.err for output"
    exit 0
fi

# Run in foreground based on mode
if [ "$MODE" = "production" ]; then
    echo "Starting in production mode with Waitress..."
    exec waitress-serve --port=$PORT --host=$HOST --threads=$THREADS --connection-limit=1000 --url-scheme=http run_app:app
else
    echo "Starting in development mode with Flask..."
    exec python run_app.py
fi