#!/bin/bash
# Private AI 🕵️ - VS Code Launcher Script
# This script launches VS Code with the Private AI proxy integration
# Author: Lance James @ Unit 221B

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if mitmdump is installed
if ! command -v mitmdump &> /dev/null; then
    echo "Error: mitmdump is required but not installed."
    echo "Please install mitmproxy: https://mitmproxy.org/"
    exit 1
fi

# Check if required Python modules are installed
REQUIRED_MODULES=("mitmproxy" "json" "argparse")
MISSING_MODULES=()

for module in "${REQUIRED_MODULES[@]}"; do
    if ! python3 -c "import $module" &> /dev/null; then
        MISSING_MODULES+=("$module")
    fi
done

if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
    echo "Error: The following Python modules are required but not installed:"
    for module in "${MISSING_MODULES[@]}"; do
        echo "  - $module"
    done
    echo "Please install them using pip: pip install ${MISSING_MODULES[*]}"
    exit 1
fi

# Run the Python launcher script
echo "Launching VS Code with Private AI proxy integration..."
# Start the proxy if not already running
if ! lsof -i:8081 > /dev/null 2>&1; then
    echo "Starting proxy server..."
    mitmdump --set confdir=~/.private-ai --set ssl_insecure=true -p 8081 --listen-host 127.0.0.1 -s "$SCRIPT_DIR/simple_proxy.py" &
    PROXY_PID=$!
    sleep 2
else
    echo "Proxy already running on port 8081, using existing proxy"
fi

# Set environment variables
export NODE_EXTRA_CA_CERTS="$HOME/.private-ai/private-ai-ca-cert.pem"
export HTTP_PROXY="http://127.0.0.1:8081"
export HTTPS_PROXY="http://127.0.0.1:8081"
export NO_PROXY="localhost,127.0.0.1"

# Launch VS Code directly
echo "Launching VS Code with proxy integration..."
/Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron "$@"

# Check if the launcher exited with an error
if [ $? -ne 0 ]; then
    echo "Error: Failed to launch VS Code with proxy integration."
    echo "Check the logs for more information: $SCRIPT_DIR/logs/vscode_launcher.log"
    exit 1
fi

echo "VS Code launched successfully with proxy integration."
echo "Press Ctrl+C to stop the proxy and clean up."

# Wait for the Python script to exit
wait