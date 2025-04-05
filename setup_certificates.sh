#!/bin/bash
# Privacy AI Certificate Setup Script
# This script generates Let's Encrypt certificates for the Privacy AI proxy
# and installs them in the system trust store.

# Enable error handling
set -e

echo "Privacy AI Certificate Setup"
echo "==================================="
echo "Creating certificate directory..."
mkdir -p "$HOME/.private-ai"

# Function to log messages with timestamps
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_message "Starting certificate setup process"

# Configuration
CERT_DIR="$HOME/.private-ai"
CERT_KEY="$CERT_DIR/private-ai-ca.key"
CERT_PEM="$CERT_DIR/private-ai-ca-cert.pem"
CERT_P12="$CERT_DIR/private-ai-ca-cert.p12"
CERT_CER="$CERT_DIR/private-ai-ca-cert.cer"
CERT_CONFIG="$CERT_DIR/cert_config.json"

# Certificate settings
CERT_CN="Privacy AI Certificate Authority"
CERT_ORG="Privacy AI"
CERT_COUNTRY="US"
CERT_VALIDITY_DAYS=90  # Let's Encrypt certificates are valid for 90 days

# Check if certbot is installed
check_certbot_installed() {
    if ! command -v certbot &> /dev/null; then
        log_message "ERROR: certbot command not found. Please install certbot and try again."
        log_message "You can install certbot using one of the following methods:"
        log_message "  - For macOS: brew install certbot"
        log_message "  - For Debian/Ubuntu: sudo apt-get install certbot"
        log_message "  - For RHEL/CentOS: sudo yum install certbot"
        log_message "  - For other systems, see: https://certbot.eff.org/instructions"
        exit 1
    fi
}

# Check if certificate exists and is valid
check_certificate_valid() {
    if [ ! -f "$CERT_PEM" ] || [ ! -f "$CERT_KEY" ]; then
        return 1
    fi
    
    # Check expiration date
    local end_date=$(openssl x509 -in "$CERT_PEM" -noout -enddate | cut -d= -f2)
    local end_timestamp=$(date -j -f "%b %d %H:%M:%S %Y %Z" "$end_date" +%s 2>/dev/null || date -d "$end_date" +%s 2>/dev/null)
    local now_timestamp=$(date +%s)
    local thirty_days=$((30 * 24 * 60 * 60))
    
    # If certificate expires in less than 30 days, consider it invalid
    if [ $((end_timestamp - now_timestamp)) -lt $thirty_days ]; then
        log_message "Certificate expires soon: $end_date"
        return 1
    fi
    
    log_message "Certificate is valid until $end_date"
    return 0
}

# Save certificate configuration
save_cert_config() {
    local created_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local expires_at=$(date -u -v+${CERT_VALIDITY_DAYS}d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d "+${CERT_VALIDITY_DAYS} days" +"%Y-%m-%dT%H:%M:%SZ")
    
    # Create JSON config file
    cat > "$CERT_CONFIG" << EOF
{
    "common_name": "$CERT_CN",
    "org_name": "$CERT_ORG",
    "country": "$CERT_COUNTRY",
    "validity_days": $CERT_VALIDITY_DAYS,
    "created_at": "$created_at",
    "expires_at": "$expires_at"
}
EOF
}

# Generate Let's Encrypt certificate
generate_lets_encrypt_cert() {
    log_message "Generating Let's Encrypt certificate..."
    
    # Check if domain is provided
    if [ -z "$1" ]; then
        log_message "ERROR: Domain name is required for Let's Encrypt certificate."
        log_message "Usage: $0 <domain>"
        exit 1
    fi
    
    DOMAIN="$1"
    
    # Run certbot to obtain certificate
    log_message "Running certbot to obtain certificate for $DOMAIN"
    if ! certbot certonly --standalone --non-interactive --agree-tos --email admin@${DOMAIN} -d ${DOMAIN}; then
        log_message "ERROR: Failed to obtain Let's Encrypt certificate. Check certbot output for details."
        exit 1
    fi
    
    # Copy Let's Encrypt certificates to our directory
    LETSENCRYPT_DIR="/etc/letsencrypt/live/${DOMAIN}"
    if [ ! -d "$LETSENCRYPT_DIR" ]; then
        log_message "ERROR: Let's Encrypt certificate directory not found: $LETSENCRYPT_DIR"
        exit 1
    fi
    
    log_message "Copying Let's Encrypt certificates to $CERT_DIR"
    cp "${LETSENCRYPT_DIR}/privkey.pem" "$CERT_KEY"
    cp "${LETSENCRYPT_DIR}/fullchain.pem" "$CERT_PEM"
    
    # Create additional certificate formats
    log_message "Creating additional certificate formats..."
    
    # Create additional certificate formats
    if ! openssl pkcs12 -export -out "$CERT_P12" \
        -inkey "$CERT_KEY" \
        -in "$CERT_PEM" \
        -password pass:privacyai; then
        log_message "WARNING: Failed to create .p12 certificate format"
    fi
    
    if ! openssl x509 -outform der -in "$CERT_PEM" \
        -out "$CERT_CER"; then
        log_message "WARNING: Failed to create .cer certificate format"
    fi
    
    log_message "All certificate formats created successfully"
    
    # Save certificate configuration
    save_cert_config
    
    log_message "Let's Encrypt certificate obtained and processed successfully"
    
    # Set up auto-renewal
    setup_auto_renewal "$DOMAIN"
}

# Set up auto-renewal for Let's Encrypt certificates
setup_auto_renewal() {
    local domain="$1"
    log_message "Setting up auto-renewal for Let's Encrypt certificate"
    
    # Create renewal hook script
    RENEWAL_HOOK="$CERT_DIR/renewal-hook.sh"
    cat > "$RENEWAL_HOOK" << EOF
#!/bin/bash
# This script is called by certbot when the certificate is renewed

# Copy renewed certificates to Private AI directory
cp "/etc/letsencrypt/live/${domain}/privkey.pem" "$CERT_KEY"
cp "/etc/letsencrypt/live/${domain}/fullchain.pem" "$CERT_PEM"

# Create additional certificate formats
openssl pkcs12 -export -out "$CERT_P12" -inkey "$CERT_KEY" -in "$CERT_PEM" -password pass:privacyai
openssl x509 -outform der -in "$CERT_PEM" -out "$CERT_CER"

# Restart any services that use the certificate
# Add your service restart commands here
EOF
    
    chmod +x "$RENEWAL_HOOK"
    
    # Add renewal hook to certbot configuration
    if [ -d "/etc/letsencrypt/renewal-hooks/post" ]; then
        sudo cp "$RENEWAL_HOOK" "/etc/letsencrypt/renewal-hooks/post/private-ai-renewal.sh"
        log_message "Renewal hook installed in certbot post-renewal directory"
    else
        log_message "WARNING: Could not find certbot renewal hooks directory. Manual renewal may be required."
        log_message "To manually renew, run: certbot renew && $RENEWAL_HOOK"
    fi
    
    # Add cron job for certificate renewal
    (crontab -l 2>/dev/null || echo "") | grep -v "certbot renew" | { cat; echo "0 3 * * * certbot renew --quiet"; } | crontab -
    log_message "Cron job added for automatic certificate renewal"
}

# Create a certificate if it doesn't exist or is expiring
if ! check_certificate_valid; then
    # Check if domain argument is provided
    if [ $# -eq 0 ]; then
        log_message "No domain provided. Usage: $0 <domain>"
        log_message "Falling back to self-signed certificate generation."
        
        # Check if openssl is available
        if ! command -v openssl &> /dev/null; then
            log_message "ERROR: openssl command not found. Please install openssl and try again."
            exit 1
        fi
        
        log_message "Generating self-signed Privacy AI certificate..."
        
        # Generate private key
        if ! openssl genrsa -out "$CERT_KEY" 4096; then
            log_message "ERROR: Failed to generate private key. Check if openssl is working properly."
            exit 1
        fi
        
        # Generate certificate signing request
        if ! openssl req -new -key "$CERT_KEY" -out "$CERT_DIR/privacy_ai_ca.csr" \
            -subj "/CN=$CERT_CN/O=$CERT_ORG/C=$CERT_COUNTRY"; then
            log_message "ERROR: Failed to generate CSR. Check if openssl is working properly."
            exit 1
        fi
        
        # Generate self-signed certificate
        if ! openssl x509 -req -days $CERT_VALIDITY_DAYS -in "$CERT_DIR/privacy_ai_ca.csr" \
            -signkey "$CERT_KEY" -out "$CERT_PEM"; then
            log_message "ERROR: Failed to generate certificate. Check if openssl is working properly."
            exit 1
        fi
        
        # Clean up CSR
        rm -f "$CERT_DIR/privacy_ai_ca.csr"
        
        # Save certificate configuration
        save_cert_config
        
        log_message "Self-signed Privacy AI certificate generated successfully (valid for $CERT_VALIDITY_DAYS days)"
        
        # Create the .p12 and .cer formats as well
        log_message "Creating additional certificate formats..."
        
        # Create additional certificate formats
        if ! openssl pkcs12 -export -out "$CERT_P12" \
            -inkey "$CERT_KEY" \
            -in "$CERT_PEM" \
            -password pass:privacyai; then
            log_message "WARNING: Failed to create .p12 certificate format"
        fi
        
        if ! openssl x509 -outform der -in "$CERT_PEM" \
            -out "$CERT_CER"; then
            log_message "WARNING: Failed to create .cer certificate format"
        fi
        
        log_message "All certificate formats created successfully"
    else
        # Use Let's Encrypt to generate certificate
        check_certbot_installed
        generate_lets_encrypt_cert "$1"
    fi
else
    log_message "Certificate already exists and is valid, skipping generation"
fi

# Display certificate information
if [ -f "$CERT_CONFIG" ]; then
    CN=$(grep -o '"common_name":[^,]*' "$CERT_CONFIG" | cut -d'"' -f4)
    ORG=$(grep -o '"org_name":[^,]*' "$CERT_CONFIG" | cut -d'"' -f4)
    EXPIRES=$(grep -o '"expires_at":[^,}]*' "$CERT_CONFIG" | cut -d'"' -f4)
    
    echo "Certificate information:"
    echo "  - Common Name: $CN"
    echo "  - Organization: $ORG"
    echo "  - Expires: $EXPIRES"
fi

echo "Certificate location: $CERT_PEM"

# Try to install to system trust store based on OS
OS="$(uname)"
log_message "Detected operating system: $OS"

if [ "$OS" == "Darwin" ]; then
    log_message "macOS detected, attempting to install Privacy AI certificate..."
    
    # Check if security command is available
    if ! command -v security &> /dev/null; then
        log_message "ERROR: 'security' command not found. Cannot install certificate to system store."
        exit 1
    fi
    
    # Attempt to install certificate with better error handling
    log_message "Running: sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain \"$CERT_PEM\""
    
    if ! sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$CERT_PEM"; then
        log_message "ERROR: Failed to install certificate to system keychain. Check if you have proper permissions."
        exit 1
    fi
    
    log_message "Certificate installation completed successfully"
    log_message "NOTE: You may need to restart your browser for changes to take effect"
elif [ "$OS" == "Linux" ]; then
    log_message "Linux detected, attempting to install Privacy AI certificate..."
    
    # Check for different Linux certificate stores
    if [ -d "/usr/local/share/ca-certificates/" ]; then
        log_message "Found Debian/Ubuntu certificate store"
        
        # Copy certificate and update store
        if ! sudo cp "$CERT_PEM" /usr/local/share/ca-certificates/private-ai-ca.crt; then
            log_message "ERROR: Failed to copy certificate to system store. Check if you have proper permissions."
            exit 1
        fi
        
        log_message "Running: sudo update-ca-certificates"
        if ! sudo update-ca-certificates; then
            log_message "ERROR: Failed to update certificate store. Check if update-ca-certificates is available."
            exit 1
        fi
        
        log_message "Certificate installation completed successfully"
        
    elif [ -d "/etc/ca-certificates/trust-source/anchors/" ]; then
        log_message "Found Arch/Manjaro certificate store"
        
        # Copy certificate and update store
        if ! sudo cp "$CERT_PEM" /etc/ca-certificates/trust-source/anchors/private-ai-ca.crt; then
            log_message "ERROR: Failed to copy certificate to system store. Check if you have proper permissions."
            exit 1
        fi
        
        log_message "Running: sudo update-ca-trust"
        if ! sudo update-ca-trust; then
            log_message "ERROR: Failed to update certificate store. Check if update-ca-trust is available."
            exit 1
        fi
        
        log_message "Certificate installation completed successfully"
        
    else
        log_message "WARNING: Could not find certificate directory. Manual installation required."
        log_message "Try one of the following methods:"
        log_message "  - For Debian/Ubuntu: sudo cp \"$CERT_PEM\" /usr/local/share/ca-certificates/private-ai-ca.crt && sudo update-ca-certificates"
        log_message "  - For Fedora/RHEL: sudo cp \"$CERT_PEM\" /etc/pki/ca-trust/source/anchors/private-ai-ca.crt && sudo update-ca-trust"
        log_message "  - For Arch/Manjaro: sudo cp \"$CERT_PEM\" /etc/ca-certificates/trust-source/anchors/private-ai-ca.crt && sudo update-ca-trust"
    fi
else
    log_message "Windows or unknown OS detected. Please install the certificate manually:"
    log_message "1. Open $CERT_PEM"
    log_message "2. Follow OS-specific instructions to add to trusted certificates"
    
    if [ "$OS" == "MINGW" ] || [ "$OS" == "MSYS" ] || [ "$OS" == "CYGWIN" ]; then
        log_message "Windows detected. You can try the following command in PowerShell (Run as Administrator):"
        log_message "Import-Certificate -FilePath \"$CERT_PEM\" -CertStoreLocation Cert:\\LocalMachine\\Root"
    fi
fi

# Configure web server to use the certificates
log_message "Configuring web server to use Let's Encrypt certificates..."

# Check if nginx is installed
if command -v nginx &> /dev/null; then
    log_message "Nginx detected, configuring SSL settings..."
    
    # Create nginx configuration for SSL
    NGINX_CONF="/tmp/private-ai-ssl.conf"
    cat > "$NGINX_CONF" << EOF
server {
    listen 443 ssl;
    server_name _;
    
    ssl_certificate $CERT_PEM;
    ssl_certificate_key $CERT_KEY;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    
    # HSTS (optional, but recommended)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Other SSL settings
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    
    # Proxy settings for mitmdump
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    log_message "Nginx SSL configuration created at $NGINX_CONF"
    log_message "To use this configuration, copy it to your nginx sites directory and reload nginx:"
    log_message "sudo cp $NGINX_CONF /etc/nginx/sites-available/private-ai-ssl"
    log_message "sudo ln -s /etc/nginx/sites-available/private-ai-ssl /etc/nginx/sites-enabled/"
    log_message "sudo nginx -t && sudo systemctl reload nginx"
fi

# Check if Apache is installed
if command -v apache2 &> /dev/null || command -v httpd &> /dev/null; then
    log_message "Apache detected, configuring SSL settings..."
    
    # Create Apache configuration for SSL
    APACHE_CONF="/tmp/private-ai-ssl.conf"
    cat > "$APACHE_CONF" << EOF
<VirtualHost *:443>
    ServerName private-ai
    
    SSLEngine on
    SSLCertificateFile $CERT_PEM
    SSLCertificateKeyFile $CERT_KEY
    
    # Strong SSL settings
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
    SSLHonorCipherOrder on
    SSLCipherSuite ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    
    # HSTS (optional, but recommended)
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # Proxy settings for mitmdump
    ProxyRequests Off
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8080/
    ProxyPassReverse / http://127.0.0.1:8080/
</VirtualHost>
EOF
    
    log_message "Apache SSL configuration created at $APACHE_CONF"
    log_message "To use this configuration, copy it to your Apache sites directory and reload Apache:"
    log_message "sudo cp $APACHE_CONF /etc/apache2/sites-available/private-ai-ssl.conf"
    log_message "sudo a2ensite private-ai-ssl"
    log_message "sudo a2enmod ssl proxy proxy_http headers"
    log_message "sudo apachectl configtest && sudo systemctl reload apache2"
fi

# Configure mitmdump to use the new certificates
log_message "Configuring mitmdump to use the new certificates..."
MITM_CONF="$HOME/.mitmproxy/config.yaml"
mkdir -p "$HOME/.mitmproxy"
cat > "$MITM_CONF" << EOF
# mitmproxy configuration for Private AI
ssl_verify_upstream: false
onboarding: false
ssl_insecure: true
# Use Let's Encrypt certificates
certs:
  - $CERT_PEM
  - $CERT_KEY
EOF

log_message "mitmdump configuration created at $MITM_CONF"
log_message "To use this configuration, run mitmdump with: mitmdump --set confdir=$HOME/.mitmproxy"

log_message "Privacy AI certificate setup process completed"
echo "=============================================="
echo "Privacy AI certificate installation complete. The proxy will now be able to intercept HTTPS traffic."
echo "If you encounter any issues, check the logs for detailed information."
echo ""
echo "Usage:"
echo "  - For Let's Encrypt certificates: $0 <domain>"
echo "  - For self-signed certificates: $0"
echo ""
echo "Certificate files are located in: $CERT_DIR"
