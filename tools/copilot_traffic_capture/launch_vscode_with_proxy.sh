#!/bin/bash
# launch_vscode_with_proxy.sh
# Launch VS Code with mitmproxy for capturing GitHub Copilot traffic

# Configuration
PROXY_HOST="localhost"
PROXY_PORT="8080"
CERT_PATH="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
LOG_DIR="$HOME/copilot_logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Function to check if proxy is running
check_proxy_running() {
  if lsof -i:$PROXY_PORT > /dev/null 2>&1; then
    echo "Proxy already running on port $PROXY_PORT"
    return 0
  else
    return 1
  fi
}

# Function to start proxy
start_proxy() {
  echo "Starting mitmproxy on $PROXY_HOST:$PROXY_PORT..."
  mitmdump -p $PROXY_PORT --set ssl_insecure=true --flow-detail 3 --save-stream-file "$LOG_DIR/capture.mitm" &
  PROXY_PID=$!
  echo "Proxy started with PID $PROXY_PID"
  
  # Wait for proxy to start
  sleep 2
  
  # Check if proxy started successfully
  if ! check_proxy_running; then
    echo "Failed to start proxy"
    exit 1
  fi
}

# Function to stop proxy
stop_proxy() {
  echo "Stopping proxy..."
  if [ -n "$PROXY_PID" ]; then
    kill $PROXY_PID
  else
    pkill -f "mitmdump.*$PROXY_PORT"
  fi
}

# Set up trap to stop proxy on exit
trap stop_proxy EXIT

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
  
  echo "VS Code settings updated for proxy"
fi

# Launch VS Code
echo "Launching VS Code with proxy..."
/Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron

echo "VS Code closed. Cleaning up..."