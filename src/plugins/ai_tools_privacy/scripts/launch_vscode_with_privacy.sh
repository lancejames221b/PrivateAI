#!/bin/bash
# launch_vscode_with_privacy.sh
# Launch VS Code with Private AI proxy for GitHub Copilot privacy protection
# This script integrates GitHub Copilot traffic capturing with Private AI privacy features

# Get the plugin directory
PLUGIN_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
ROOT_DIR="$( cd "$PLUGIN_DIR/../.." && pwd )"

# Configuration
PROXY_HOST="localhost"
PROXY_PORT="8080"
CERT_PATH="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
LOG_DIR="$ROOT_DIR/proxy_logs"
SCRIPT_DIR="$PLUGIN_DIR/scripts"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   Private AI 🕵️ - GitHub Copilot Privacy Proxy                ║"
echo "║                                                               ║"
echo "║   This tool intercepts GitHub Copilot traffic and applies     ║"
echo "║   privacy protection to detect and transform PII.             ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if proxy is running
check_proxy_running() {
  if lsof -i:$PROXY_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Proxy already running on port $PROXY_PORT${NC}"
    return 0
  else
    return 1
  fi
}

# Function to start proxy
start_proxy() {
  echo -e "${YELLOW}Starting Private AI proxy on $PROXY_HOST:$PROXY_PORT...${NC}"
  
  # Create a timestamp for the log file
  TIMESTAMP=$(date +%s)
  LOG_FILE="$LOG_DIR/proxy_log_$TIMESTAMP.txt"
  
  # Start mitmdump with our proxy_base.py script
  cd "$ROOT_DIR"
  mitmdump -p $PROXY_PORT --set ssl_insecure=true -s "$ROOT_DIR/proxy_base.py" --save-stream-file "$LOG_DIR/capture_$TIMESTAMP.mitm" > "$LOG_FILE" 2>&1 &
  PROXY_PID=$!
  
  echo -e "${GREEN}✅ Proxy started with PID $PROXY_PID${NC}"
  echo -e "${GREEN}✅ Logs being saved to $LOG_FILE${NC}"
  echo -e "${GREEN}✅ Traffic being saved to $LOG_DIR/capture_$TIMESTAMP.mitm${NC}"
  
  # Wait for proxy to start
  sleep 2
  
  # Check if proxy started successfully
  if ! check_proxy_running; then
    echo -e "${RED}❌ Failed to start proxy${NC}"
    exit 1
  fi
}

# Function to stop proxy
stop_proxy() {
  echo -e "${YELLOW}Stopping proxy...${NC}"
  if [ -n "$PROXY_PID" ]; then
    kill $PROXY_PID
  else
    pkill -f "mitmdump.*$PROXY_PORT"
  fi
  echo -e "${GREEN}✅ Proxy stopped${NC}"
}

# Function to check and install certificate
check_and_install_certificate() {
  echo -e "${YELLOW}Checking mitmproxy certificate...${NC}"
  
  # Check if certificate exists
  if [ ! -f "$CERT_PATH" ]; then
    echo -e "${YELLOW}Certificate not found. Running mitmproxy to generate it...${NC}"
    mitmdump --no-server &
    TEMP_PID=$!
    sleep 2
    kill $TEMP_PID
    
    if [ ! -f "$CERT_PATH" ]; then
      echo -e "${RED}❌ Failed to generate certificate${NC}"
      exit 1
    fi
  fi
  
  echo -e "${GREEN}✅ Certificate found at $CERT_PATH${NC}"
  
  # Install certificate in VS Code certificates directory
  VSCODE_CERT_DIR="$HOME/Library/Application Support/Code/User/certificates"
  mkdir -p "$VSCODE_CERT_DIR"
  cp "$CERT_PATH" "$VSCODE_CERT_DIR/"
  
  echo -e "${GREEN}✅ Certificate installed in VS Code certificates directory${NC}"
}

# Set up trap to stop proxy on exit
trap stop_proxy EXIT

# Check and install certificate
check_and_install_certificate

# Start proxy if not already running
if ! check_proxy_running; then
  start_proxy
fi

# Set environment variables
export NODE_EXTRA_CA_CERTS="$CERT_PATH"
export HTTP_PROXY="http://$PROXY_HOST:$PROXY_PORT"
export HTTPS_PROXY="http://$PROXY_HOST:$PROXY_PORT"
export NO_PROXY="localhost,127.0.0.1"

# Update VS Code settings
VSCODE_SETTINGS_PATH="$HOME/Library/Application Support/Code/User/settings.json"
if [ -f "$VSCODE_SETTINGS_PATH" ]; then
  # Create a backup of the settings file
  cp "$VSCODE_SETTINGS_PATH" "${VSCODE_SETTINGS_PATH}.bak"
  
  # Update proxy settings
  cat > "${VSCODE_SETTINGS_PATH}.tmp" << EOF
{
  "http.proxy": "http://$PROXY_HOST:$PROXY_PORT",
  "http.proxyStrictSSL": false,
  "http.proxySupport": "override",
  "github.copilot.advanced": {
    "proxy": "http://$PROXY_HOST:$PROXY_PORT"
  }
}
EOF
  
  # Merge with existing settings
  jq -s '.[0] * .[1]' "$VSCODE_SETTINGS_PATH" "${VSCODE_SETTINGS_PATH}.tmp" > "${VSCODE_SETTINGS_PATH}.new"
  mv "${VSCODE_SETTINGS_PATH}.new" "$VSCODE_SETTINGS_PATH"
  rm "${VSCODE_SETTINGS_PATH}.tmp"
  
  echo -e "${GREEN}✅ VS Code settings updated for proxy${NC}"
fi

# Configure environment for Private AI
export AI_DOMAINS="openai.com,anthropic.com,api.github.com,copilot.github.com,api.githubcopilot.com,copilot-proxy.githubusercontent.com,githubcopilot.com,default.exp-tas.com"
export LOG_LEVEL="INFO"

echo -e "${YELLOW}Launching VS Code with privacy protection for GitHub Copilot...${NC}"
echo -e "${YELLOW}Any PII in your code will be automatically protected when sent to GitHub Copilot.${NC}"
echo -e "${YELLOW}Check the proxy logs for details on what was protected.${NC}"

# Launch VS Code
/Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron

echo -e "${YELLOW}VS Code closed. Cleaning up...${NC}"