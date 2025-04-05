#!/bin/bash

# Start the proxy if not already running
pgrep -f "mitmdump.*simple_copilot_proxy.py" > /dev/null
if [ $? -ne 0 ]; then
  echo "Starting mitmdump proxy..."
  mitmdump --set confdir=~/.mitmproxy-fresh --set ssl_insecure=true --set block_global=false -p 8080 --listen-host 127.0.0.1 -s simple_copilot_proxy.py &
  sleep 2  # Give the proxy time to start
else
  echo "Proxy already running"
fi

# Update VS Code settings
echo "Updating VS Code settings..."
mkdir -p ~/.vscode
cp vscode_settings.json ~/.vscode/settings.json
echo "VS Code settings updated"

# Kill any existing VS Code processes
echo "Closing any running VS Code instances..."
pkill "Visual Studio Code"
pkill "Electron"
sleep 2  # Give the processes time to terminate

# Set environment variables and launch VS Code
echo "Launching VS Code with proxy settings..."
VSCODE="/Applications/Visual Studio Code.app/Contents/MacOS/Electron"

# These environment variables are crucial for certificate bypass
export NODE_TLS_REJECT_UNAUTHORIZED=0
export NODE_EXTRA_CA_CERTS=~/.mitmproxy-fresh/mitmproxy-ca-cert.pem
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080

# Launch VS Code
$VSCODE &

echo "VS Code launched with proxy settings. Copilot should now work with the proxy."
echo "If Copilot still shows as offline, try restarting VS Code from within VS Code using the Command Palette."
echo "You can also try reinstalling the GitHub Copilot extensions if needed." 