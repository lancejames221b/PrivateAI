# GitHub Copilot Traffic Capturing Guide

This guide explains how to intercept and analyze the HTTPS traffic between VS Code and GitHub Copilot servers using mitmproxy.

## Problem

GitHub Copilot in VS Code communicates with several API endpoints which we want to intercept and analyze. However, the traffic is encrypted with TLS, making it difficult to inspect.

## Solution Overview

We use mitmproxy to intercept the HTTPS traffic between VS Code and GitHub Copilot servers. The key challenges are:

1. Configuring mitmproxy correctly
2. Getting VS Code (Electron app) to trust the proxy's certificates
3. Setting up proper logging

## Prerequisites

- mitmproxy installed (`brew install mitmproxy` on macOS)
- VS Code with GitHub Copilot extension installed
- Administrative access (for certificate installation)

## Step-by-Step Solution

### 1. Fix mitmproxy configuration

The initial error is often due to an invalid certificate configuration in `~/.mitmproxy/config.yaml`. Reset the configuration:

```bash
mv ~/.mitmproxy/config.yaml ~/.mitmproxy/config.yaml.bak
echo "# Default mitmproxy config" > ~/.mitmproxy/config.yaml
```

### 2. Install mitmproxy certificate in system trust store

Copy the mitmproxy certificate to make it accessible:

```bash
cp ~/.mitmproxy/mitmproxy-ca-cert.pem ~/Downloads/mitmproxy-ca-cert.pem
```

Then add it to the macOS Keychain Access:
- Double-click on the certificate file
- Add it to the System keychain
- Set "When using this certificate" to "Always Trust"

For automated installation, use:

```bash
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem
```

### 3. Make Electron (VS Code) trust the certificate

Since VS Code is an Electron app, it doesn't automatically use the system's certificate store. Set an environment variable to include the mitmproxy certificate:

```bash
export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
/Applications/Visual\ Studio\ Code.app/Contents/MacOS/Electron
```

Alternatively, install the certificate directly in VS Code's trusted certificates:

```bash
mkdir -p ~/Library/Application\ Support/Code/User/certificates
cp ~/.mitmproxy/mitmproxy-ca-cert.pem ~/Library/Application\ Support/Code/User/certificates/
```

### 4. Configure VS Code proxy settings

In VS Code settings:
- Set HTTP proxy to "http://localhost:8080"
- Disable "Proxy Strict SSL" setting

You can do this by adding the following to your VS Code `settings.json`:

```json
{
  "http.proxy": "http://localhost:8080",
  "http.proxyStrictSSL": false,
  "http.proxySupport": "override",
  "github.copilot.advanced": {
    "proxy": "http://localhost:8080"
  }
}
```

### 5. Start mitmproxy to capture traffic

Create a logs directory:
```bash
mkdir -p copilot_logs/analysis
```

Start mitmproxy on port 8080:
```bash
mitmdump -p 8080
```

For more detailed logging:
```bash
mitmdump -p 8080 --set ssl_insecure=true --flow-detail 3 --save-stream-file copilot_logs/capture.mitm
```

### 6. Using VS Code with GitHub Copilot

After launching VS Code with the environment variable set:
1. Open a new file in a supported language (like Python)
2. Trigger Copilot completions by typing code
3. Use Copilot Chat
4. Observe traffic being captured by mitmproxy

## Captured Traffic Types

Successfully intercepted:
- Authentication: `api.github.com/copilot_internal/v2/token`
- Models: `api.business.githubcopilot.com/models`
- Completions: `api.business.githubcopilot.com/chat/completions`
- Telemetry: `telemetry.business.githubcopilot.com` and `copilot-telemetry.githubusercontent.com`

## Automation Scripts

### Launch VS Code with Proxy

```bash
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
```

### Reset VS Code to Direct Connection

```bash
#!/bin/bash
# reset_vscode_direct.sh
# Reset VS Code to connect directly without proxy

echo "Resetting VS Code to connect directly without proxy..."

# Kill any running proxy processes
echo "Stopping any running proxy processes..."
pkill -f "mitmdump"

# Reset VS Code settings
echo "Resetting VS Code settings..."
VSCODE_SETTINGS_PATH="$HOME/Library/Application Support/Code/User/settings.json"

if [ -f "$VSCODE_SETTINGS_PATH" ]; then
  # Create a backup of the settings file
  cp "$VSCODE_SETTINGS_PATH" "${VSCODE_SETTINGS_PATH}.bak"
  
  # Remove proxy settings using temporary file
  jq 'del(.["http.proxy"]) | del(.["http.proxyStrictSSL"]) | del(.["http.proxySupport"]) | del(.["github.copilot.advanced"]["proxy"])' "$VSCODE_SETTINGS_PATH" > "${VSCODE_SETTINGS_PATH}.tmp"
  
  # Check if jq command was successful
  if [ $? -eq 0 ]; then
    mv "${VSCODE_SETTINGS_PATH}.tmp" "$VSCODE_SETTINGS_PATH"
    echo "VS Code settings updated successfully"
  else
    echo "Failed to update VS Code settings with jq, using manual approach"
    # If jq fails, try a simpler approach with sed
    sed -i '' -e '/"http.proxy"/d' -e '/"http.proxyStrictSSL"/d' -e '/"http.proxySupport"/d' -e '/"github.copilot.advanced".*"proxy"/d' "$VSCODE_SETTINGS_PATH"
  fi
else
  echo "VS Code settings file not found at $VSCODE_SETTINGS_PATH"
fi

# Clear environment variables
unset HTTP_PROXY
unset HTTPS_PROXY
unset NO_PROXY
unset NODE_EXTRA_CA_CERTS

echo "VS Code reset to connect directly without proxy."
```

## Troubleshooting

If you see "The client does not trust the proxy's certificate" errors, double-check:
1. Certificate is installed correctly in both system and VS Code
2. The environment variable is set
3. VS Code's Proxy Strict SSL setting is disabled

If port 8080 is already in use, try a different port:
```bash
mitmdump -p 8081
```
And update the VS Code proxy settings accordingly.

## Analysis

To analyze the captured traffic:

1. Use mitmproxy's built-in viewer:
   ```bash
   mitmproxy -r copilot_logs/capture.mitm
   ```

2. Export specific requests for further analysis:
   ```bash
   mitmdump -r copilot_logs/capture.mitm -w copilot_logs/completions.mitm "~u /completions"
   ```

3. Convert to HAR format for browser analysis:
   ```bash
   mitmdump -r copilot_logs/capture.mitm --save-stream-file copilot_logs/capture.har
   ```

## Conclusion

This approach allows you to successfully intercept and analyze the HTTPS traffic between VS Code and GitHub Copilot servers. The key is ensuring that VS Code trusts the mitmproxy certificate and is configured to use the proxy for all HTTP/HTTPS traffic.