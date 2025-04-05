#!/bin/bash

# Kill any existing VS Code instances
pkill "Visual Studio Code" || true
pkill "Electron" || true

# Kill any existing proxy instances
pkill -f mitmdump || true

# Start a simple proxy
echo "Starting proxy..."
mitmdump --set confdir=~/.mitmproxy-fresh --set ssl_insecure=true -p 8080 --listen-host 127.0.0.1 &
PROXY_PID=$!

# Wait for proxy to start
sleep 2

# Set environment variables
export NODE_EXTRA_CA_CERTS="$PWD/copilot-cert.pem"
export HTTP_PROXY="http://127.0.0.1:8080"
export HTTPS_PROXY="http://127.0.0.1:8080"
export NODE_TLS_REJECT_UNAUTHORIZED="0"  # Only for testing - removes certificate validation

# Launch VS Code
echo "Launching VS Code with certificate: $NODE_EXTRA_CA_CERTS"
echo "Proxy settings: $HTTP_PROXY"
/Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron

# Clean up proxy when VS Code exits
kill $PROXY_PID 