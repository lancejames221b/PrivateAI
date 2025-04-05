#!/bin/bash
# PrivateAI - VS Code Testing Script (No Proxy Version)
# This script sets up VS Code without using the proxy to test if GitHub Copilot works directly

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
VSCODE_SETTINGS_DIR=""
VENV_DIR="privacy_proxy_env"  # Virtual environment directory

# Determine OS and set VS Code settings path
detect_os() {
    echo -e "${BLUE}Detecting operating system...${NC}"
    case "$(uname -s)" in
        Darwin*)
            echo "macOS detected"
            VSCODE_SETTINGS_DIR="$HOME/Library/Application Support/Code/User"
            ;;
        Linux*)
            echo "Linux detected"
            VSCODE_SETTINGS_DIR="$HOME/.config/Code/User"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "Windows detected"
            VSCODE_SETTINGS_DIR="$APPDATA/Code/User"
            ;;
        *)
            echo -e "${YELLOW}Unknown OS. You'll need to manually configure VS Code settings.${NC}"
            ;;
    esac
    
    if [ -n "$VSCODE_SETTINGS_DIR" ]; then
        echo -e "${GREEN}VS Code settings directory: $VSCODE_SETTINGS_DIR${NC}"
    fi
}

# Configure VS Code to not use a proxy
configure_vscode_no_proxy() {
    echo -e "${BLUE}Configuring VS Code to not use a proxy...${NC}"
    
    if [ -z "$VSCODE_SETTINGS_DIR" ]; then
        echo -e "${YELLOW}VS Code settings directory not detected. Skipping automatic configuration.${NC}"
        return
    fi
    
    SETTINGS_FILE="$VSCODE_SETTINGS_DIR/settings.json"
    
    # Create settings directory if it doesn't exist
    mkdir -p "$VSCODE_SETTINGS_DIR"
    
    # Create or update settings.json
    if [ ! -f "$SETTINGS_FILE" ]; then
        echo "{}" > "$SETTINGS_FILE"
    fi
    
    # Use Python to update the JSON file
    python3 -c "
import json
import sys

try:
    with open('$SETTINGS_FILE', 'r') as f:
        settings = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    settings = {}

# Remove proxy settings if they exist
if 'http.proxy' in settings:
    del settings['http.proxy']
    
if 'http.proxyStrictSSL' in settings:
    del settings['http.proxyStrictSSL']

# Write updated settings
with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=4)
    
print('VS Code settings updated successfully')
"
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to update VS Code settings. You may need to configure them manually.${NC}"
    else
        echo -e "${GREEN}VS Code settings updated successfully.${NC}"
    fi
}

# Disable system-wide proxy
disable_system_proxy() {
    echo -e "${BLUE}Disabling system-wide proxy...${NC}"
    
    # Activate virtual environment if it exists
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Disable proxy if setup_proxy.py exists
    if [ -f "setup_proxy.py" ]; then
        python setup_proxy.py --disable
        
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}System proxy disabling may have issues. You may need to disable it manually.${NC}"
        else
            echo -e "${GREEN}System proxy disabled successfully.${NC}"
        fi
    else
        echo -e "${YELLOW}setup_proxy.py not found. You may need to disable the system proxy manually.${NC}"
    fi
    
    # Deactivate virtual environment if it was activated
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
}

# Print instructions for testing GitHub Copilot
print_instructions() {
    echo -e "\n${BLUE}=== GitHub Copilot Testing Instructions ===${NC}"
    echo -e "${GREEN}VS Code is now configured to NOT use a proxy.${NC}"
    echo -e "To test GitHub Copilot:"
    echo -e "1. Close all instances of VS Code"
    echo -e "2. Open VS Code again"
    echo -e "3. Sign in to GitHub Copilot (if not already signed in)"
    echo -e "4. Create a new file and test Copilot functionality"
    echo -e "\n${YELLOW}If Copilot works without the proxy but not with it, the issue is with the proxy configuration.${NC}"
    echo -e "${YELLOW}If Copilot still doesn't work, the issue might be with your Copilot account or VS Code installation.${NC}"
    
    echo -e "\n${BLUE}=== GitHub Copilot Troubleshooting ===${NC}"
    echo -e "1. Try signing out of GitHub in VS Code and signing in again"
    echo -e "2. Check if your Copilot subscription is active"
    echo -e "3. Try reinstalling the GitHub Copilot extension"
    echo -e "4. Check VS Code logs for any errors (Help > Toggle Developer Tools)"
}

# Main function
main() {
    echo -e "${BLUE}=== Testing GitHub Copilot Without Proxy ===${NC}"
    
    # Run setup steps
    detect_os
    disable_system_proxy
    configure_vscode_no_proxy
    
    # Print instructions
    print_instructions
    
    echo -e "\n${GREEN}Setup complete. Please follow the instructions above to test GitHub Copilot.${NC}"
}

# Run the main function
main