#!/bin/bash

# AI Security Proxy - mitmproxy Backend
# ======================================

# Terminal color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}AI Security Proxy - mitmproxy Backend${NC}"
echo -e "${BLUE}=================================${NC}"

# Function to print usage information
print_usage() {
    echo -e "${YELLOW}Usage:${NC} $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -p, --port PORT          Specify proxy port (default: 8080)"
    echo "  -s, --script SCRIPT      Specify the proxy script to use (default: proxy_intercept.py)"
    echo "  -m, --mode MODE          Proxy mode: mitmdump, mitmproxy, mitmweb (default: mitmdump)"
    echo "  -v, --verbose            Enable verbose output"
    echo "  -b, --block-domains      Block all domains in domain_blocklist.txt"
    echo "  -l, --log-level LEVEL    Set log level: debug, info, warning, error (default: info)"
    echo "  -f, --log-file FILE      Log to this file (default: proxy.log)"
    echo "  -w, --web-port PORT      Web interface port (for mitmweb mode) (default: 8081)"
    echo "  -c, --cert DIR           Custom certificate directory"
    echo "  -h, --help               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -p 8888                   # Run proxy on port 8888"
    echo "  $0 -m mitmweb -w 9090        # Run with web interface on port 9090"
    echo "  $0 -v -l debug               # Run with verbose debug logging"
    echo "  $0 -b                        # Run with domain blocking enabled"
    exit 1
}

# Set default values
PORT=8080
SCRIPT="proxy_intercept.py"
MODE="mitmdump"
VERBOSE=""
BLOCK_DOMAINS="false"
LOG_LEVEL="info"
LOG_FILE="proxy.log"
WEB_PORT=8081
CERT_DIR=""
EXTRA_ARGS=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -s|--script)
            SCRIPT="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE="--set console_eventlog_verbosity=debug"
            export LOG_LEVEL="debug"
            shift
            ;;
        -b|--block-domains)
            BLOCK_DOMAINS="true"
            shift
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -f|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -w|--web-port)
            WEB_PORT="$2"
            shift 2
            ;;
        -c|--cert)
            CERT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            ;;
        *)
            echo -e "${RED}Unknown option:${NC} $1"
            print_usage
            ;;
    esac
done

# Validate MODE
if [[ ! "$MODE" =~ ^(mitmdump|mitmproxy|mitmweb)$ ]]; then
    echo -e "${RED}Error:${NC} Invalid mode '$MODE'. Must be one of: mitmdump, mitmproxy, mitmweb"
    exit 1
fi

# Ensure the script exists
if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}Error:${NC} Script not found: $SCRIPT"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data
mkdir -p logs

# Set environment variables for configuration
export BLOCK_ALL_DOMAINS=${BLOCK_DOMAINS}
export PROXY_PORT=${PORT}
export LOG_LEVEL=${LOG_LEVEL}
export LOG_FILE=${LOG_FILE}

# Load environment variables if .env exists
if [ -f .env ]; then
    echo -e "${BLUE}Loading environment from .env file${NC}"
    source .env
fi

# Construct certificate args if specified
CERT_ARGS=""
if [ -n "$CERT_DIR" ]; then
    CERT_ARGS="--set confdir=$CERT_DIR"
    echo -e "${BLUE}Using custom certificate directory:${NC} $CERT_DIR"
fi

# Show configuration
echo -e "${GREEN}Starting AI Security Proxy with configuration:${NC}"
echo -e "  ${YELLOW}Mode:${NC}          $MODE"
echo -e "  ${YELLOW}Port:${NC}          $PORT"
echo -e "  ${YELLOW}Script:${NC}        $SCRIPT"
echo -e "  ${YELLOW}Block domains:${NC} $BLOCK_DOMAINS"
echo -e "  ${YELLOW}Log level:${NC}     $LOG_LEVEL"
echo -e "  ${YELLOW}Log file:${NC}      $LOG_FILE"

if [ "$MODE" = "mitmweb" ]; then
    echo -e "  ${YELLOW}Web port:${NC}      $WEB_PORT"
fi

# Construct the command based on the mode
if [ "$MODE" = "mitmdump" ]; then
    CMD="mitmdump -s $SCRIPT --listen-port $PORT --set block_global=false $VERBOSE $CERT_ARGS --no-http2"
elif [ "$MODE" = "mitmproxy" ]; then
    CMD="mitmproxy -s $SCRIPT --listen-port $PORT --set block_global=false $VERBOSE $CERT_ARGS --no-http2"
elif [ "$MODE" = "mitmweb" ]; then
    CMD="mitmweb -s $SCRIPT --listen-port $PORT --web-port $WEB_PORT --set block_global=false $VERBOSE $CERT_ARGS --no-http2"
fi

echo -e "${BLUE}Running command:${NC} $CMD"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"

# Execute the command
$CMD

# Exit gracefully
echo -e "${GREEN}AI Security Proxy stopped${NC}" 