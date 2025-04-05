#!/bin/bash
# PrivateAI - VS Code Testing Script (Fixed Version)
# This script sets up and tests the PrivateAI proxy with VS Code
# Uses a virtual environment with fixed dependencies to avoid compatibility issues

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
PROXY_PORT=8080
PROXY_HOST="localhost"
PROXY_URL="http://${PROXY_HOST}:${PROXY_PORT}"

# Fix environment variables with incorrect comments
export MODEL_NAME="dslim/bert-base-NER"
export TRANSFORMER_MODEL_NAME="iiiorg/piiranha-v1-detect-personal-information"

# Disable proxy for initial model download
export HTTP_PROXY=""
export HTTPS_PROXY=""
export NO_PROXY="localhost,127.0.0.1"

# Ensure Copilot domains and authentication domains are not blocked
export BLOCK_ALL_DOMAINS="false"
export EXCLUDED_DOMAINS="github.com,githubusercontent.com,copilot.github.com,api.github.com,githubcopilot.com,github.dev,gist.github.com,vscode.dev,visualstudio.com,login.microsoftonline.com,vsmarketplacebadge.apphb.com,marketplace.visualstudio.com,*.vscode-cdn.net,*.gallerycdn.vsassets.io,auth.gfx.ms,login.live.com,login.windows.net,microsoftonline.com,management.core.windows.net,aadcdn.msauth.net,aadcdn.msftauth.net"
LOG_LEVEL=${LOG_LEVEL:-INFO}
VSCODE_SETTINGS_DIR=""
PROXY_PID=""
PROXY_LOG_FILE="logs/proxy.log"
WAIT_TIME=5  # Seconds to wait for proxy to initialize
VENV_DIR="privacy_proxy_env"  # Virtual environment directory
REQUIREMENTS_FILE="requirements-fixed.txt"  # Fixed requirements file

# Create logs directory
mkdir -p logs

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

# Check if required tools are installed and set up virtual environment
check_requirements() {
    echo -e "${BLUE}Checking requirements...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is required but not found. Please install Python 3.${NC}"
        exit 1
    fi
    
    # Check if virtualenv is installed
    if ! command -v python3 -m venv &> /dev/null; then
        echo -e "${YELLOW}Python venv module not found. Installing...${NC}"
        python3 -m pip install --user virtualenv
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${BLUE}Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}Virtual environment created at $VENV_DIR${NC}"
    fi
    
    # Activate virtual environment
    echo -e "${BLUE}Activating virtual environment...${NC}"
    source "$VENV_DIR/bin/activate"
    
    # Install fixed dependencies
    echo -e "${BLUE}Installing fixed dependencies...${NC}"
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    
    # Check if mitmproxy is installed in the virtual environment
    if ! command -v mitmdump &> /dev/null; then
        echo -e "${RED}mitmproxy installation failed. Please check the requirements file.${NC}"
        exit 1
    fi
    
    # Check VS Code
    if ! command -v code &> /dev/null; then
        echo -e "${YELLOW}VS Code command-line tool not found. You may need to manually configure VS Code.${NC}"
    fi
    
    # Check if port is already in use
    check_port_in_use
    
    echo -e "${GREEN}All required tools are available.${NC}"
}

# Check if the proxy port is already in use
check_port_in_use() {
    if command -v lsof &> /dev/null; then
        if lsof -i:$PROXY_PORT &> /dev/null; then
            echo -e "${YELLOW}Port $PROXY_PORT is already in use. The proxy may not start correctly.${NC}"
            echo -e "You can check what's using the port with: lsof -i:$PROXY_PORT"
            
            # Try to kill existing mitmproxy processes
            if pgrep -f "mitmdump -s proxy_intercept.py" > /dev/null; then
                echo -e "Found existing mitmproxy process. Attempting to stop it..."
                pkill -f "mitmdump -s proxy_intercept.py"
                sleep 2
                
                # Check if it's still running
                if pgrep -f "mitmdump -s proxy_intercept.py" > /dev/null; then
                    echo -e "${RED}Failed to stop existing mitmproxy process. Please stop it manually.${NC}"
                    echo -e "You can use: pkill -f \"mitmdump -s proxy_intercept.py\""
                else
                    echo -e "${GREEN}Successfully stopped existing mitmproxy process.${NC}"
                fi
            fi
        fi
    fi
}

# Install certificates
install_certificates() {
    echo -e "${BLUE}Installing certificates...${NC}"
    
    # Create certificates directory if it doesn't exist
    mkdir -p ~/.mitmproxy
    
    # Use python from virtual environment
    python setup_certificates.py
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Certificate installation may have issues. Trying to print instructions...${NC}"
        python setup_certificates.py --print-instructions
        
        echo -e "${YELLOW}Additional certificate troubleshooting for Copilot:${NC}"
        echo -e "1. Ensure the mitmproxy certificate is installed in your system trust store"
        echo -e "2. The certificate should be in ~/.mitmproxy/mitmproxy-ca-cert.pem"
        echo -e "3. Restart VS Code after installing the certificate"
        echo -e "4. If using macOS, try: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem"
        echo -e "5. If using Windows, double-click the certificate and install it to the 'Trusted Root Certification Authorities' store"
        echo -e "6. If using Linux, follow your distribution's instructions for adding a trusted CA certificate"
    else
        echo -e "${GREEN}Certificates installed successfully.${NC}"
        
        # Additional steps for different operating systems
        case "$(uname -s)" in
            Darwin*)
                echo -e "${YELLOW}On macOS, you may need to manually trust the certificate:${NC}"
                echo -e "sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem"
                ;;
            Linux*)
                echo -e "${YELLOW}On Linux, you may need to manually trust the certificate. Check your distribution's documentation.${NC}"
                ;;
            CYGWIN*|MINGW*|MSYS*)
                echo -e "${YELLOW}On Windows, you may need to manually trust the certificate:${NC}"
                echo -e "1. Navigate to ~/.mitmproxy/"
                echo -e "2. Double-click mitmproxy-ca-cert.pem"
                echo -e "3. Install it to the 'Trusted Root Certification Authorities' store"
                ;;
        esac
    fi
}

# Configure VS Code settings
configure_vscode() {
    echo -e "${BLUE}Configuring VS Code settings...${NC}"
    
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

# Update proxy settings
settings['http.proxy'] = '$PROXY_URL'
settings['http.proxyStrictSSL'] = False

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

# Configure system-wide proxy
configure_system_proxy() {
    echo -e "${BLUE}Configuring system-wide proxy...${NC}"
    python setup_proxy.py --enable --host $PROXY_HOST --port $PROXY_PORT
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}System proxy configuration may have issues. You may need to configure it manually.${NC}"
    else
        echo -e "${GREEN}System proxy configured successfully.${NC}"
    fi
}

# Start the proxy
start_proxy() {
    echo -e "${BLUE}Starting PrivateAI proxy...${NC}"
    
    # Check if proxy is already running
    if pgrep -f "mitmdump -s proxy_intercept.py" > /dev/null; then
        echo -e "${YELLOW}Proxy already running. Stopping it first...${NC}"
        pkill -f "mitmdump -s proxy_intercept.py"
        sleep 2
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p logs
    
    # Start proxy in background with logging to file
    echo -e "${BLUE}Starting proxy in background with logging to file.${NC}"
    echo -e "${YELLOW}In a separate terminal, you can run VS Code and test the proxy.${NC}"
    echo -e "${GREEN}Proxy will be listening on $PROXY_URL${NC}"
    
    # Use mitmdump with quiet output, redirecting to log file
    echo -e "${BLUE}Proxy logs will be written to $PROXY_LOG_FILE${NC}"
    
    # Set environment variables to ensure GitHub Copilot traffic passes through
    # We're completely disabling interception for this test to ensure authentication works
    export AI_DOMAINS=""
    export ADDITIONAL_DOMAINS=""
    
    echo -e "${YELLOW}Disabling all interception to ensure authentication works properly...${NC}"
    
    # Create a temporary ignore file for authentication domains
    TEMP_IGNORE_FILE=$(mktemp)
    echo ".*github\.com.*" > $TEMP_IGNORE_FILE
    echo ".*githubusercontent\.com.*" >> $TEMP_IGNORE_FILE
    echo ".*visualstudio\.com.*" >> $TEMP_IGNORE_FILE
    echo ".*vscode.*" >> $TEMP_IGNORE_FILE
    echo ".*microsoft.*" >> $TEMP_IGNORE_FILE
    echo ".*live\.com.*" >> $TEMP_IGNORE_FILE
    echo ".*windows\.net.*" >> $TEMP_IGNORE_FILE
    
    # Use a more permissive configuration for the proxy
    LOG_LEVEL=$LOG_LEVEL mitmdump -s proxy_intercept.py \
        --set confdir=~/.mitmproxy \
        --set ssl_insecure=true \
        --listen-host $PROXY_HOST \
        --listen-port $PROXY_PORT \
        --set block_global=false \
        --set flow_detail=0 \
        --set stream_large_bodies=100m \
        --set connection_strategy=lazy \
        --set websocket=true \
        --set keep_host_header=true \
        --set upstream_cert=true \
        --ignore-hosts "$(cat $TEMP_IGNORE_FILE | tr '\n' ',')" > $PROXY_LOG_FILE 2>&1 &
        
    # Clean up the temporary file
    rm $TEMP_IGNORE_FILE
    
    # Save the PID of the proxy process
    PROXY_PID=$!
    echo -e "${GREEN}Proxy started with PID: $PROXY_PID${NC}"
    
    # Wait for proxy to initialize
    echo -e "${BLUE}Waiting for proxy to initialize...${NC}"
    sleep $WAIT_TIME
}

# Verify proxy connection
verify_proxy_connection() {
    echo -e "${BLUE}Verifying proxy connection...${NC}"
    
    # Try to connect to the proxy using curl
    if command -v curl &> /dev/null; then
        echo "Testing connection to proxy with curl..."
        if curl -s -x $PROXY_URL -o /dev/null -w "%{http_code}" https://example.com > /dev/null; then
            echo -e "${GREEN}Successfully connected to proxy!${NC}"
            
            # Test GitHub domains specifically
            echo "Testing connection to GitHub domains..."
            if curl -s -x $PROXY_URL -o /dev/null -w "%{http_code}" https://github.com > /dev/null; then
                echo -e "${GREEN}Successfully connected to github.com!${NC}"
            else
                echo -e "${RED}Failed to connect to github.com.${NC}"
                echo -e "This may cause issues with GitHub Copilot."
            fi
            
            if curl -s -x $PROXY_URL -o /dev/null -w "%{http_code}" https://api.github.com > /dev/null; then
                echo -e "${GREEN}Successfully connected to api.github.com!${NC}"
            else
                echo -e "${RED}Failed to connect to api.github.com.${NC}"
                echo -e "This may cause issues with GitHub Copilot."
            fi
        else
            echo -e "${RED}Failed to connect to proxy with curl.${NC}"
            echo -e "This may indicate a problem with the proxy configuration."
            echo -e "Check $PROXY_LOG_FILE for details."
        fi
    else
        echo -e "${YELLOW}curl not found. Skipping proxy connection verification.${NC}"
    fi
}

# Run automated tests
run_tests() {
    echo -e "${BLUE}Running automated tests...${NC}"
    
    # Run the test script with error handling (using python from virtual environment)
    python test_vscode_ai_proxy.py --proxy $PROXY_URL --test-type vscode
    VSCODE_TEST_RESULT=$?
    
    python test_vscode_ai_proxy.py --proxy $PROXY_URL --test-type copilot
    COPILOT_TEST_RESULT=$?
    
    # Check if any tests failed
    if [ $VSCODE_TEST_RESULT -ne 0 ] || [ $COPILOT_TEST_RESULT -ne 0 ]; then
        echo -e "${RED}Some tests failed. Check the output above for details.${NC}"
        echo -e "${YELLOW}This may be expected if you don't have access to the actual API endpoints.${NC}"
        echo -e "The important part is that the proxy is running and correctly configured."
    else
        echo -e "${GREEN}Tests completed successfully.${NC}"
    fi
    
    echo -e "${YELLOW}Note: Connection errors in the tests are expected if you don't have actual API access.${NC}"
    echo -e "The important part is that the proxy is correctly intercepting the requests."
}

# Print manual testing instructions
print_instructions() {
    echo -e "\n${BLUE}=== Manual Testing Instructions ===${NC}"
    echo -e "${GREEN}The proxy is now running and VS Code is configured to use it.${NC}"
    echo -e "To manually test with VS Code:"
    echo -e "1. Open VS Code"
    echo -e "2. Create a new file with some PII (e.g., names, emails, etc.)"
    echo -e "3. Use GitHub Copilot or another AI extension to generate code"
    echo -e "4. Check the proxy logs to verify interception and transformation"
    echo -e "\nTo view the proxy logs in real-time:"
    echo -e "  tail -f $PROXY_LOG_FILE"
    echo -e "\nTo stop the proxy when done:"
    echo -e "  pkill -f \"mitmdump -s proxy_intercept.py\""
    echo -e "  source $VENV_DIR/bin/activate && python setup_proxy.py --disable"
    echo -e "\nFor more detailed instructions, see docs/vscode_testing_guide.md"
    
    echo -e "\n${BLUE}=== GitHub Copilot Troubleshooting ===${NC}"
    echo -e "If you experience 'Failed to fetch' errors with GitHub Copilot:"
    echo -e "1. Ensure the mitmproxy certificate is installed in your system trust store"
    echo -e "2. Restart VS Code after installing the certificate"
    echo -e "3. Check the proxy logs for any errors related to GitHub domains"
    echo -e "4. If you see authentication dialogs, try the 'device code' option"
    echo -e "5. If authentication fails, try signing out of GitHub in VS Code and signing in again"
    echo -e "6. If issues persist, try temporarily disabling the proxy to test if Copilot works without it"
    echo -e "7. For detailed troubleshooting, see the 'fetchfailure.txt' file"
    
    echo -e "\n${YELLOW}Note: This script is now configured to completely bypass interception${NC}"
    echo -e "${YELLOW}for GitHub and authentication-related domains to ensure proper functionality.${NC}"
    
    echo -e "\n${RED}IMPORTANT: If you continue to experience issues with GitHub Copilot,${NC}"
    echo -e "${RED}try using the test_without_proxy.sh script to test without the proxy:${NC}"
    echo -e "${YELLOW}./test_without_proxy.sh${NC}"
}

# Cleanup function
cleanup() {
    echo -e "\n${BLUE}Cleaning up...${NC}"
    
    # Stop the proxy if it's still running
    if [ -n "$PROXY_PID" ] && ps -p $PROXY_PID > /dev/null; then
        echo "Stopping proxy process..."
        kill $PROXY_PID 2>/dev/null || true
        wait $PROXY_PID 2>/dev/null || true
    fi
    
    # Disable system proxy (using python from virtual environment)
    echo "Disabling system proxy..."
    source "$VENV_DIR/bin/activate" && python setup_proxy.py --disable >/dev/null 2>&1 || true
    
    # Deactivate virtual environment if it was activated
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "Deactivating virtual environment..."
        deactivate 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Cleanup completed.${NC}"
}

# Main function
main() {
    echo -e "${BLUE}=== PrivateAI VS Code Testing (with Virtual Environment) ===${NC}"
    
    # Setup trap for cleanup on exit
    trap cleanup EXIT
    
    # Run setup steps
    detect_os
    check_requirements
    install_certificates
    configure_vscode
    configure_system_proxy
    
    # Start proxy in background
    start_proxy
    
    # Verify proxy connection
    verify_proxy_connection
    
    # Run automated tests
    run_tests
    
    # Print manual testing instructions
    print_instructions
    
    # Wait for user input to stop the proxy
    echo -e "${YELLOW}Press Enter to stop the proxy and clean up...${NC}"
    read
    
    # Stop the proxy
    if [ -n "$PROXY_PID" ]; then
        echo -e "${BLUE}Stopping proxy (PID: $PROXY_PID)...${NC}"
        kill $PROXY_PID 2>/dev/null || true
        wait $PROXY_PID 2>/dev/null || true
        echo -e "${GREEN}Proxy stopped.${NC}"
    fi
}

# Run the main function
main
