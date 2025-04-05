#!/bin/bash
# install_mitmproxy_cert.sh
# Install mitmproxy certificate in system trust store and VS Code

# Configuration
MITMPROXY_CERT="$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
VSCODE_CERT_DIR="$HOME/Library/Application Support/Code/User/certificates"

# Check if mitmproxy certificate exists
if [ ! -f "$MITMPROXY_CERT" ]; then
  echo "mitmproxy certificate not found at $MITMPROXY_CERT"
  echo "Please run mitmproxy at least once to generate the certificate"
  exit 1
fi

# Function to install certificate in macOS system keychain
install_macos_cert() {
  echo "Installing certificate in macOS system keychain..."
  
  # Copy certificate to Downloads for easy access
  cp "$MITMPROXY_CERT" "$HOME/Downloads/mitmproxy-ca-cert.pem"
  echo "Certificate copied to $HOME/Downloads/mitmproxy-ca-cert.pem"
  
  # Install in system keychain
  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$MITMPROXY_CERT"
  
  if [ $? -eq 0 ]; then
    echo "Certificate installed in system keychain successfully"
  else
    echo "Failed to install certificate in system keychain"
    echo "Please install manually:"
    echo "1. Open Keychain Access"
    echo "2. Drag $HOME/Downloads/mitmproxy-ca-cert.pem to System keychain"
    echo "3. Double-click the certificate"
    echo "4. Expand 'Trust' section"
    echo "5. Set 'When using this certificate' to 'Always Trust'"
  fi
}

# Function to install certificate in Linux system trust store
install_linux_cert() {
  echo "Installing certificate in Linux system trust store..."
  
  # Copy certificate to system trust store
  sudo cp "$MITMPROXY_CERT" /usr/local/share/ca-certificates/mitmproxy-ca-cert.crt
  
  # Update CA certificates
  sudo update-ca-certificates
  
  if [ $? -eq 0 ]; then
    echo "Certificate installed in system trust store successfully"
  else
    echo "Failed to install certificate in system trust store"
  fi
}

# Function to install certificate in Windows system trust store
install_windows_cert() {
  echo "Installing certificate in Windows system trust store..."
  echo "Please run the following command in an Administrator PowerShell:"
  echo "Import-Certificate -FilePath \"$MITMPROXY_CERT\" -CertStoreLocation Cert:\\LocalMachine\\Root"
}

# Function to install certificate in VS Code
install_vscode_cert() {
  echo "Installing certificate in VS Code..."
  
  # Create VS Code certificates directory if it doesn't exist
  mkdir -p "$VSCODE_CERT_DIR"
  
  # Copy certificate to VS Code certificates directory
  cp "$MITMPROXY_CERT" "$VSCODE_CERT_DIR/"
  
  if [ $? -eq 0 ]; then
    echo "Certificate installed in VS Code successfully"
  else
    echo "Failed to install certificate in VS Code"
  fi
}

# Install certificate based on platform
case "$(uname -s)" in
  Darwin*)
    install_macos_cert
    ;;
  Linux*)
    install_linux_cert
    ;;
  CYGWIN*|MINGW*|MSYS*)
    install_windows_cert
    ;;
  *)
    echo "Unsupported platform: $(uname -s)"
    exit 1
    ;;
esac

# Install certificate in VS Code
install_vscode_cert

echo ""
echo "Certificate installation complete."
echo "To use the certificate with VS Code, set the following environment variable:"
echo "  export NODE_EXTRA_CA_CERTS=\"$MITMPROXY_CERT\""
echo ""
echo "Or use the launch_vscode_with_proxy.sh script to launch VS Code with the proxy."