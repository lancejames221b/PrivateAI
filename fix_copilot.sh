#!/bin/bash

# This script patches the GitHub Copilot extension to disable certificate validation
# Mac specific paths - modify for other OS

# Find Copilot extension directories
VSCODEDIR="$HOME/.vscode/extensions"
COPILOTDIR=$(ls "${VSCODEDIR}" | grep -E "github.copilot-[0-9].*" | sort -V | tail -n1)
COPILOTCHATDIR=$(ls "${VSCODEDIR}" | grep -E "github.copilot-chat-[0-9].*" | sort -V | tail -n1)

# Define extension file paths
EXTENSIONFILEPATH="${VSCODEDIR}/${COPILOTDIR}/dist/extension.js"
CHATEXTENSIONFILEPATH="${VSCODEDIR}/${COPILOTCHATDIR}/dist/extension.js"

echo "Looking for GitHub Copilot extensions in: ${VSCODEDIR}"
echo "Found Copilot: ${COPILOTDIR}"
echo "Found Copilot Chat: ${COPILOTCHATDIR}"

# Patch regular Copilot extension
if [[ -f "$EXTENSIONFILEPATH" ]]; then
    echo "Found Copilot Extension, backing up and applying patches to '$EXTENSIONFILEPATH'..."
    cp "${EXTENSIONFILEPATH}" "${EXTENSIONFILEPATH}.bak"
    
    # Apply patches to disable certificate validation
    perl -pi -e 's/,rejectUnauthorized:[a-z]}(?!})/,rejectUnauthorized:false}/g' "${EXTENSIONFILEPATH}"
    perl -pi -e 's/d=\{\.\.\.l,/d={...l,rejectUnauthorized:false,/g' "${EXTENSIONFILEPATH}"
    
    # Search for other patterns that might need to be replaced
    echo "Looking for other certificate validation patterns..."
    HTTPSPATTERNS=$(grep -n "https.request\|rejectUnauthorized\|NODE_TLS_REJECT_UNAUTHORIZED" "${EXTENSIONFILEPATH}" | head -n 10)
    if [[ -n "$HTTPSPATTERNS" ]]; then
        echo "Found additional HTTPS patterns that might need manual inspection:"
        echo "$HTTPSPATTERNS"
    fi
    
    echo "Patching complete! Restart VS Code completely for changes to take effect."
else
    echo "Couldn't find the extension.js file for Copilot (${EXTENSIONFILEPATH})"
    echo "Please verify the extension is installed."
fi

# Patch Copilot Chat extension if found
if [[ -f "$CHATEXTENSIONFILEPATH" ]]; then
    echo "Found Copilot Chat Extension, backing up and applying patches to '$CHATEXTENSIONFILEPATH'..."
    cp "${CHATEXTENSIONFILEPATH}" "${CHATEXTENSIONFILEPATH}.bak"
    
    # Apply patches to disable certificate validation
    perl -pi -e 's/,rejectUnauthorized:[a-z]}(?!})/,rejectUnauthorized:false}/g' "${CHATEXTENSIONFILEPATH}"
    perl -pi -e 's/d=\{\.\.\.l,/d={...l,rejectUnauthorized:false,/g' "${CHATEXTENSIONFILEPATH}"
    
    echo "Copilot Chat extension patched!"
fi

echo ""
echo "Next steps:"
echo "1. Make sure you have the mitmproxy certificate installed in the System keychain"
echo "2. Set environment variable before starting VS Code:"
echo "   export NODE_EXTRA_CA_CERTS=~/.mitmproxy-fresh/mitmproxy-ca-cert.pem"
echo "3. Completely quit VS Code (Cmd+Q) and restart it" 