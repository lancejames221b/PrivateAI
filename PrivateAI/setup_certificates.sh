#!/bin/bash

# Script to install mitmproxy CA certificate to system/browser trust store

echo "AI Security Proxy Certificate Setup"
echo "==================================="
echo "This script helps install the mitmproxy CA certificate to your system."
echo

if [ ! -f "~/.mitmproxy/mitmproxy-ca-cert.pem" ]; then
  echo "mitmproxy certificate not found. Please run mitmproxy once to generate certificates."
  echo "Run: mitmproxy"
  exit 1
fi

# Detect OS
OS="$(uname)"
if [ "$OS" == "Darwin" ]; then
  echo "macOS detected."
  echo "Installing certificate to system keychain..."
  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem
  echo "Certificate installed to system keychain."
  
  echo "Note: For Chrome and Edge, you may need to restart the browser."
  echo "For Firefox, you need to import the certificate manually:"
  echo "Settings > Privacy & Security > Certificates > View Certificates > Import"
elif [ "$OS" == "Linux" ]; then
  echo "Linux detected."
  
  # Check for common certificate directories
  if [ -d "/etc/ca-certificates/trust-source/anchors/" ]; then
    # Arch-based
    sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /etc/ca-certificates/trust-source/anchors/mitmproxy-ca-cert.pem
    sudo update-ca-trust
  elif [ -d "/usr/local/share/ca-certificates/" ]; then
    # Debian/Ubuntu
    sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
    sudo update-ca-certificates
  else
    echo "Could not detect certificate directory. Please install manually."
  fi
elif [[ "$OS" == MINGW* ]] || [[ "$OS" == MSYS* ]] || [[ "$OS" == CYGWIN* ]]; then
  echo "Windows detected."
  echo "Please install the certificate manually:"
  echo "1. Convert the PEM certificate to CRT:"
  echo "   openssl x509 -outform der -in ~/.mitmproxy/mitmproxy-ca-cert.pem -out mitmproxy-ca-cert.crt"
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