#!/bin/bash
# This script enables the Private AI proxy for VS Code after GitHub Copilot authentication

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== Private AI Proxy Enabler =====${NC}"

# Step 1: Skip checking if VS Code is running since we're already in VS Code
echo -e "${YELLOW}Skipping VS Code check - continuing with proxy setup${NC}"
# if pgrep -f "Visual Studio Code" > /dev/null; then
#     echo -e "${YELLOW}VS Code is running. Please close all VS Code windows before continuing.${NC}"
#     read -p "Press Enter when VS Code is closed..."
# fi

# Step 2: Activate virtual environment and ensure the database is set up
echo -e "${BLUE}Activating virtual environment...${NC}"
source privacy_proxy_env/bin/activate

echo -e "${BLUE}Setting up the database...${NC}"
python db_setup.py

# Step 3: Kill any running proxy processes
echo -e "${BLUE}Stopping any running proxy processes...${NC}"
pkill -f mitmdump || true
pkill -f "python.*app.py" || true

# Step 4: Create .env file with proper GitHub exclusions
echo -e "${BLUE}Creating .env file with GitHub domain exclusions...${NC}"
cat > .env << EOF
# Private AI Proxy Configuration
FLASK_APP=app.py
FLASK_ENV=production
PROXY_PORT=8080
PROXY_HOST=localhost
LOG_LEVEL=INFO

# Model configuration
MODEL_NAME=dslim/bert-base-NER
TRANSFORMER_MODEL_NAME=dslim/bert-base-NER
USE_PRESIDIO=true
PRESIDIO_LOG_LEVEL=INFO
SPACY_MODEL=en_core_web_lg

# AI protection settings
ENABLE_PII_DETECTION=true
ENABLE_API_KEY_DETECTION=true
ENABLE_CREDIT_CARD_DETECTION=true
ENABLE_CODE_DETECTION=true
ENABLE_USERNAME_DETECTION=true

# Domain configuration
BLOCK_ALL_DOMAINS=false
EXCLUDED_DOMAINS=github.com,githubusercontent.com,copilot.github.com,api.github.com,githubcopilot.com,github.dev,gist.github.com,vscode.dev,visualstudio.com,login.microsoftonline.com,vsmarketplacebadge.apphb.com,marketplace.visualstudio.com,vscode-cdn.net,gallerycdn.vsassets.io,auth.gfx.ms,login.live.com,login.windows.net,microsoftonline.com,management.core.windows.net,aadcdn.msauth.net,aadcdn.msftauth.net

# Security
SECRET_KEY=86daa356aa826ee6000fbb470402bfa6
BASIC_AUTH_ENABLED=true
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=admin

# Transformer settings
TRANSFORMERS_MODEL=dslim/bert-base-NER
TRANSFORMERS_CONFIDENCE_THRESHOLD=0.8
TRANSFORMERS_OFFLINE_ONLY=1
EOF

echo -e "${GREEN}.env file created with GitHub domain exclusions${NC}"

# Step 5: Start the proxy
echo -e "${BLUE}Starting the Private AI proxy...${NC}"
mitmdump -p 8080 --set confdir=~/.mitmproxy --set block_global=false --set ssl_insecure=true -s proxy_intercept.py --set stream_large_bodies=100m --set connection_strategy=lazy --set websocket=true --set keep_host_header=true &
PROXY_PID=$!

# Wait for proxy to start
sleep 3
if ps -p $PROXY_PID > /dev/null; then
    echo -e "${GREEN}Proxy started successfully with PID $PROXY_PID${NC}"
else
    echo -e "${RED}Failed to start proxy!${NC}"
    exit 1
fi

# Step 6: Update VS Code settings to use proxy
echo -e "${BLUE}Updating VS Code settings to use Private AI proxy...${NC}"
VSCODE_SETTINGS_DIR="$HOME/Library/Application Support/Code/User"
SETTINGS_FILE="$VSCODE_SETTINGS_DIR/settings.json"

# Save original settings if not already saved
if [ -f "$SETTINGS_FILE" ] && [ ! -f "${SETTINGS_FILE}.bak" ]; then
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    echo -e "${YELLOW}Backed up original settings to ${SETTINGS_FILE}.bak${NC}"
fi

# Create or update VS Code settings
mkdir -p "$VSCODE_SETTINGS_DIR"
cat > "$SETTINGS_FILE" << EOF
{
    "http.proxy": "http://localhost:8080",
    "http.proxyStrictSSL": false,
    "http.proxySupport": "on",
    "github.copilot.advanced": {
        "debug.testOverrideProxyUrl": false,
        "debug.overrideProxyUrl": "",
        "debug.useDevCopilotLanguageServer": false,
        "debug.useGitHubRemoteUrlMetrics": true
    }
}
EOF

echo -e "${GREEN}VS Code settings updated to use Private AI proxy!${NC}"

# Step 7: Skip launching VS Code with the test project
echo -e "${BLUE}Skipping VS Code launch - you can open it manually later${NC}"
# cd simple-web-app
# code . || open -a "Visual Studio Code" .

echo -e "${YELLOW}Private AI Proxy is running with PID $PROXY_PID${NC}"
echo -e "${YELLOW}VS Code is configured to use the proxy.${NC}"
echo -e "${YELLOW}GitHub domains are excluded from interception.${NC}"
echo -e "${GREEN}You can now use GitHub Copilot while protecting your sensitive data!${NC}"
echo -e "${YELLOW}To stop the proxy, run: kill $PROXY_PID${NC}"

# Stay in the foreground so proxy keeps running
echo -e "${BLUE}Press Ctrl+C to stop the proxy and exit${NC}"
wait $PROXY_PID 