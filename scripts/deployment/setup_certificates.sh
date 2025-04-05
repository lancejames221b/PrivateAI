#!/bin/bash

# Script to install mitmproxy CA certificate to system/browser trust store

echo "AI Security Proxy Certificate Setup"
echo "==================================="
echo "This script helps install the mitmproxy CA certificate to your system."
echo

# Check for certificate in both absolute and relative paths
CERT_PATH="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
ALT_CERT_PATH="./mitmproxy-ca-cert.pem"

if [ -f "$CERT_PATH" ]; then
  echo "Found mitmproxy certificate at $CERT_PATH"
  CERT_TO_USE="$CERT_PATH"
elif [ -f "$ALT_CERT_PATH" ]; then
  echo "Found mitmproxy certificate at $ALT_CERT_PATH"
  CERT_TO_USE="$ALT_CERT_PATH"
else
  echo "mitmproxy certificate not found. Generating a temporary certificate for demonstration."
  echo "In a real setup, you would need to run mitmproxy first to generate certificates."
  
  # Create a temporary self-signed certificate for demonstration
  mkdir -p "$HOME/.mitmproxy"
  openssl req -x509 -newkey rsa:4096 -keyout "$HOME/.mitmproxy/mitmproxy-ca.key" -out "$HOME/.mitmproxy/mitmproxy-ca-cert.pem" -days 365 -nodes -subj "/CN=Private AI Demo CA" 2>/dev/null
  
  if [ $? -eq 0 ]; then
    echo "Created temporary certificate for demonstration."
    CERT_TO_USE="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
  else
    echo "Failed to create temporary certificate. Please run mitmproxy once to generate certificates."
    echo "Run: mitmproxy"
    exit 1
  fi
fi

# Detect OS
OS="$(uname)"
if [ "$OS" == "Darwin" ]; then
  echo "macOS detected."
  echo "Installing certificate to system keychain..."
  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$CERT_TO_USE"
  echo "Certificate installed to system keychain."
  
  echo "Note: For Chrome and Edge, you may need to restart the browser."
  echo "For Firefox, you need to import the certificate manually:"
  echo "Settings > Privacy & Security > Certificates > View Certificates > Import"
elif [ "$OS" == "Linux" ]; then
  echo "Linux detected."
  
  # Check for common certificate directories
  if [ -d "/etc/ca-certificates/trust-source/anchors/" ]; then
    # Arch-based
    sudo cp "$CERT_TO_USE" /etc/ca-certificates/trust-source/anchors/mitmproxy-ca-cert.pem
    sudo update-ca-trust
  elif [ -d "/usr/local/share/ca-certificates/" ]; then
    # Debian/Ubuntu
    sudo cp "$CERT_TO_USE" /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
    sudo update-ca-certificates
  else
    echo "Could not detect certificate directory. Please install manually."
  fi
elif [[ "$OS" == MINGW* ]] || [[ "$OS" == MSYS* ]] || [[ "$OS" == CYGWIN* ]]; then
  echo "Windows detected."
  echo "Please install the certificate manually:"
  echo "1. Convert the PEM certificate to CRT:"
  echo "   openssl x509 -outform der -in \"$CERT_TO_USE\" -out mitmproxy-ca-cert.crt"
  echo "2. Double-click the .crt file"
  echo "3. Click 'Install Certificate'"
  echo "4. Choose 'Local Machine' and click Next"
  echo "5. Select 'Place all certificates in the following store'"
  echo "6. Click 'Browse' and select 'Trusted Root Certification Authorities'"
  echo "7. Click 'OK', 'Next', and 'Finish'"
else
  echo "Unknown operating system. Please install the certificate manually."
fi

echo
echo "Certificate setup complete. Please restart your browser."
echo "The proxy will run on localhost:8080"
echo "You can configure your system proxy settings to use this proxy."
echo "To run the proxy: mitmproxy -s proxy_intercept.py"
echo 