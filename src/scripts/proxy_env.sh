#!/bin/bash

# Path to mitmproxy certificate
CERT_PATH="$HOME/.mitmproxy-fresh/mitmproxy-ca-cert.pem"

# Configure Node.js to trust our certificate - Copilot specifically looks for this
export NODE_EXTRA_CA_CERTS="$CERT_PATH"

# Configure proxy for all HTTP/HTTPS requests
export HTTP_PROXY="http://127.0.0.1:8080"
export HTTPS_PROXY="http://127.0.0.1:8080"
export NO_PROXY="localhost,127.0.0.1"

# Kill any running VS Code processes
pkill -f "Visual Studio Code" || true

# Open VS Code settings before launch
open ~/.vscode/settings.json

echo "Now run VS Code with these environment variables:"
echo "/Applications/Visual\\ Studio\\ Code.app/Contents/MacOS/Electron"
echo ""
echo "Make sure your VS Code settings.json contains:"
echo '{
  "http.proxy": "http://127.0.0.1:8080",
  "http.proxyStrictSSL": false,
  "http.proxySupport": "override",
  "github.copilot.advanced": {
    "proxy": "http://127.0.0.1:8080"
  }
}' 