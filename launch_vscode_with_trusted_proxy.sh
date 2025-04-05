#!/bin/bash
# Launch VS Code with Trusted Proxy
# This script launches VS Code with a trusted proxy that handles certificate verification

# Configuration
PROXY_HOST="127.0.0.1"
PROXY_PORT="8081"
CERT_PATH="$HOME/.private-ai/private-ai-ca-cert.pem"
PROXY_SCRIPT="/Volumes/SeXternal 1/Dev/Private AI/trusted_proxy.py"

# Check if certificate exists
if [ ! -f "$CERT_PATH" ]; then
  echo "Certificate not found at $CERT_PATH"
  exit 1
fi

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
  echo "Starting trusted proxy on $PROXY_HOST:$PROXY_PORT..."
  mitmdump --set confdir=~/.private-ai --set ssl_insecure=true -p $PROXY_PORT --listen-host $PROXY_HOST -s $PROXY_SCRIPT &
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
export ELECTRON_EXTRA_LAUNCH_ARGS="--ignore-certificate-errors"
export HTTP_PROXY="http://$PROXY_HOST:$PROXY_PORT"
export HTTPS_PROXY="http://$PROXY_HOST:$PROXY_PORT"
export NO_PROXY="localhost,127.0.0.1"

# Launch VS Code with certificate trust
echo "Launching VS Code with trusted proxy..."
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  ELECTRON_ARGS="--js-flags=--expose-gc --ignore-certificate-errors"
  VSCODE_PATH="/Applications/Visual Studio Code.app/Contents/MacOS/Electron"
  
  # Launch VS Code with our arguments
  "$VSCODE_PATH" $ELECTRON_ARGS "$@"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  ELECTRON_ARGS="--js-flags=--expose-gc --ignore-certificate-errors"
  VSCODE_PATH="$(which code)"
  
  # Launch VS Code with our arguments
  "$VSCODE_PATH" $ELECTRON_ARGS "$@"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32" ]]; then
  # Windows
  ELECTRON_ARGS="--js-flags=--expose-gc --ignore-certificate-errors"
  VSCODE_PATH="C:/Program Files/Microsoft VS Code/Code.exe"
  
  # Launch VS Code with our arguments
  "$VSCODE_PATH" $ELECTRON_ARGS "$@"
else
  echo "Unsupported OS: $OSTYPE"
  exit 1
fi

echo "VS Code closed. Cleaning up..."