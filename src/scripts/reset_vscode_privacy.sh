#!/bin/bash
# reset_vscode_privacy.sh
# Reset VS Code to connect directly without the privacy proxy

echo "Resetting VS Code to connect directly without privacy proxy..."

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

echo "VS Code reset to connect directly without privacy proxy."
