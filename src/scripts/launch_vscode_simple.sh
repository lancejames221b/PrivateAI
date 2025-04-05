#!/bin/bash
# Simple VS Code Launcher with Proxy
# This script launches VS Code with proxy environment variables

# Configuration
PROXY_HOST="127.0.0.1"
PROXY_PORT="8081"
CERT_PATH="$HOME/.private-ai/private-ai-ca-cert.pem"

# Set environment variables
export NODE_EXTRA_CA_CERTS="$CERT_PATH"
export ELECTRON_EXTRA_LAUNCH_ARGS="--ignore-certificate-errors"
export HTTP_PROXY="http://$PROXY_HOST:$PROXY_PORT"
export HTTPS_PROXY="http://$PROXY_HOST:$PROXY_PORT"
export NO_PROXY="localhost,127.0.0.1"

# Launch VS Code with certificate trust
echo "Launching VS Code with proxy environment variables..."
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

echo "VS Code closed."