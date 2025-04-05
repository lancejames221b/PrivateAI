#!/bin/bash
# This script starts VS Code with proper settings for GitHub Copilot

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===== VS Code with GitHub Copilot Setup =====${NC}"

# Step 1: Create a new simple test directory
echo -e "${BLUE}Creating test directory...${NC}"
TEST_DIR="simple-web-app"
mkdir -p $TEST_DIR

# Step 2: Stop any running proxy
echo -e "${BLUE}Stopping any running proxy processes...${NC}"
pkill -f mitmdump || true
pkill -f "python.*app.py" || true

# Step 3: Clear proxy environment variables
echo -e "${BLUE}Clearing proxy environment variables...${NC}"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# Step 4: Initialize the test project
echo -e "${BLUE}Initializing test project...${NC}"
cd $TEST_DIR

# Create a simple HTML file
cat > index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Web App</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <h1>Welcome</h1>
    <script src="script.js"></script>
</body>
</html>
EOF

# Create a simple CSS file
cat > styles.css << EOF
/* Styles for our app */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
}
EOF

# Create a simple JS file
cat > script.js << EOF
// JavaScript for our app
console.log('Script loaded!');

// TODO: Add more functionality here
EOF

# Create a Python test file with sensitive data
cat > test.py << EOF
# This is a test file with sensitive information for Copilot to detect

# Personal data
user = {
    "name": "John Smith",
    "email": "john.smith@example.com",
    "ssn": "123-45-6789",
    "credit_card": "4111-1111-1111-1111",
    "address": "123 Main St, Anytown, CA 12345"
}

# API key (for testing)
api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"

# Function to process user data
def process_user_data():
    print(f"Processing data for {user['name']}")
    # Use Copilot to complete this function...
EOF

echo -e "${GREEN}Test project created!${NC}"

# Step 5: Update VS Code settings for this session only
echo -e "${BLUE}Updating VS Code settings...${NC}"
VSCODE_SETTINGS_DIR="$HOME/Library/Application Support/Code/User"
SETTINGS_FILE="$VSCODE_SETTINGS_DIR/settings.json"

# Save original settings
if [ -f "$SETTINGS_FILE" ]; then
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    echo -e "${YELLOW}Backed up original settings to ${SETTINGS_FILE}.bak${NC}"
fi

# Create or update VS Code settings
mkdir -p "$VSCODE_SETTINGS_DIR"
cat > "$SETTINGS_FILE" << EOF
{
    "http.proxy": "",
    "http.proxyStrictSSL": true,
    "http.proxySupport": "off",
    "github.copilot.advanced": {
        "debug.testOverrideProxyUrl": false,
        "debug.overrideProxyUrl": "",
        "debug.useDevCopilotLanguageServer": false,
        "debug.useGitHubRemoteUrlMetrics": true
    }
}
EOF

echo -e "${GREEN}VS Code settings updated to use direct connection!${NC}"

# Step 6: Find and Launch VS Code
echo -e "${BLUE}Finding VS Code...${NC}"

# Check common VS Code locations
VSCODE_PATHS=(
  "/Applications/Visual Studio Code.app/Contents/MacOS/Electron"
  "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
  "/usr/local/bin/code"
  "$HOME/Applications/Visual Studio Code.app/Contents/MacOS/Electron"
)

VSCODE_FOUND=false
for path in "${VSCODE_PATHS[@]}"; do
  if [ -f "$path" ]; then
    echo -e "${GREEN}Found VS Code at: $path${NC}"
    echo -e "${BLUE}Launching VS Code...${NC}"
    
    # Use the appropriate method based on which path was found
    if [[ "$path" == *"/bin/code" ]]; then
      "$path" .
    else
      "$path" "$(pwd)"
    fi
    
    VSCODE_FOUND=true
    break
  fi
done

if [ "$VSCODE_FOUND" = false ]; then
  echo -e "${RED}Could not find VS Code in standard locations.${NC}"
  echo -e "${YELLOW}Attempting fallback methods...${NC}"
  
  # Try standard command line tools as fallback
  if command -v code &> /dev/null; then
    echo -e "${GREEN}Using 'code' command...${NC}"
    code .
  elif [ -d "/Applications/Visual Studio Code.app" ]; then
    echo -e "${GREEN}Using 'open' command with VS Code...${NC}"
    open -a "Visual Studio Code" .
  else
    echo -e "${RED}Failed to launch VS Code. Please install VS Code or launch it manually.${NC}"
    echo -e "${YELLOW}Then open the '${TEST_DIR}' directory.${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}VS Code launched with test project!${NC}"
echo -e "${YELLOW}Try testing GitHub Copilot now. It should use a direct connection.${NC}"
echo -e "${YELLOW}To restore your original settings, run:${NC}"
echo -e "${BLUE}cp \"${SETTINGS_FILE}.bak\" \"${SETTINGS_FILE}\"${NC}"

cd .. 