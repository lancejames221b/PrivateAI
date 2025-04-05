#!/bin/bash

# Start Privacy Proxy Script
# This script starts the mitmproxy with our privacy-focused interceptor

# Terminal color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Privacy AI Proxy - Starting${NC}"
echo -e "${BLUE}=================================${NC}"

# Activate virtual environment if it exists
if [ -d "privacy_proxy_env" ]; then
    echo -e "${BLUE}Activating virtual environment${NC}"
    source privacy_proxy_env/bin/activate
else
    echo -e "${YELLOW}Warning: Virtual environment not found. Dependencies may not be available.${NC}"
fi

# Check if mitmproxy is installed
if ! command -v mitmdump &> /dev/null; then
    echo -e "${RED}Error: mitmproxy is not installed${NC}"
    echo "Please install it with: pip install mitmproxy"
    exit 1
fi

# Check if .env file exists and load it
if [ -f .env ]; then
    echo -e "${BLUE}Loading environment variables from .env file${NC}"
    source .env
fi

# Set default port if not set in environment
PROXY_PORT=${PROXY_PORT:-8080}
BLOCK_ALL_DOMAINS=${BLOCK_ALL_DOMAINS:-false}
LOG_LEVEL=${LOG_LEVEL:-info}
LOG_FILE=${LOG_FILE:-proxy.log}
PROXY_MODE=${PROXY_MODE:-mitmdump}

# Determine which interceptor script to use
INTERCEPT_SCRIPT="proxy_intercept.py"
if [ ! -f "$INTERCEPT_SCRIPT" ]; then
    echo -e "${RED}Error: $INTERCEPT_SCRIPT not found${NC}"
    exit 1
fi

# Determine which proxy mode to use
if [ "$PROXY_MODE" = "mitmweb" ]; then
    WEB_PORT=${WEB_PORT:-8081}
    CMD="mitmweb -s $INTERCEPT_SCRIPT --listen-port $PROXY_PORT --web-port $WEB_PORT --set block_global=false --no-http2"
    echo -e "${YELLOW}Starting mitmweb on port $PROXY_PORT (web interface on port $WEB_PORT)${NC}"
else
    CMD="mitmdump -s $INTERCEPT_SCRIPT --listen-port $PROXY_PORT --set block_global=false --no-http2"
    echo -e "${YELLOW}Starting mitmdump on port $PROXY_PORT${NC}"
fi

# Display settings
echo -e "${GREEN}Proxy Settings:${NC}"
echo -e "  ${YELLOW}Port:${NC}          $PROXY_PORT"
echo -e "  ${YELLOW}Mode:${NC}          $PROXY_MODE"
echo -e "  ${YELLOW}Script:${NC}        $INTERCEPT_SCRIPT"
echo -e "  ${YELLOW}Block domains:${NC} $BLOCK_ALL_DOMAINS"
echo -e "  ${YELLOW}Log level:${NC}     $LOG_LEVEL"
echo -e "  ${YELLOW}Log file:${NC}      $LOG_FILE"

echo -e "${BLUE}Starting proxy...${NC}"
echo -e "${YELLOW}To use this proxy with curl:${NC}"
echo -e "  curl -x http://localhost:$PROXY_PORT https://api.openai.com/v1/chat/completions"
echo -e "${YELLOW}To use this proxy with the API demo:${NC}"
echo -e "  python real_ai_demo.py --proxy http://localhost:$PROXY_PORT"
echo -e "${BLUE}Press Ctrl+C to stop${NC}"

# Run the proxy
$CMD

# Exit message
echo -e "${GREEN}Privacy Proxy stopped${NC}" 