#!/usr/bin/env python3
"""
Private AI 🕵️ - Certificate Management

This module handles certificate generation and installation for the Private AI proxy.
It provides automated certificate installation across different platforms and
ensures that IDE tools trust the proxy's certificates.

Author: Lance James @ Unit 221B
"""

import os
import sys
import subprocess
import platform
import shutil
import tempfile
from pathlib import Path
import logging
import datetime
import json
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("certificate-manager", "logs/certificate_manager.log")

# Certificate paths
CERT_DIR = os.path.expanduser("~/.private-ai")
CERT_PEM = os.path.join(CERT_DIR, "private-ai-ca-cert.pem")
CERT_KEY = os.path.join(CERT_DIR, "private-ai-ca.key")
CERT_P12 = os.path.join(CERT_DIR, "private-ai-ca-cert.p12")
CERT_CER = os.path.join(CERT_DIR, "private-ai-ca-cert.cer")
CERT_CONFIG = os.path.join(CERT_DIR, "cert_config.json")

# Default certificate configuration
DEFAULT_CERT_CONFIG = {
    "common_name": "Privacy AI Certificate Authority",
    "org_name": "Privacy AI",
    "country": "US",
    "validity_days": 90,  # Let's Encrypt certificates are valid for 90 days
    "created_at": None,
    "expires_at": None
}

def ensure_cert_directory():
    """Ensure the certificate directory exists with proper permissions"""
    try:
        os.makedirs(CERT_DIR, mode=0o700, exist_ok=True)
        logger.info(f"Certificate directory ensured at {CERT_DIR}")
        return True
    except Exception as e:
        log_exception(logger, e, "ensure_cert_directory")
        return False

def load_cert_config():
    """Load certificate configuration from file"""
    if os.path.exists(CERT_CONFIG):
        try:
            import json
            with open(CERT_CONFIG, 'r') as f:
                return json.load(f)
        except Exception as e:
            log_exception(logger, e, "load_cert_config")
    
    # Return default configuration if file doesn't exist or can't be read
    return DEFAULT_CERT_CONFIG.copy()

def save_cert_config(config):
    """Save certificate configuration to file"""
    try:
        import json
        with open(CERT_CONFIG, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        log_exception(logger, e, "save_cert_config")
        return False

def check_certificate_exists():
    """Check if the certificate already exists"""
    return os.path.exists(CERT_PEM) and os.path.exists(CERT_KEY)

def check_certificate_valid():
    """Check if the existing certificate is still valid"""
    if not check_certificate_exists():
        return False
        
    try:
        # Get certificate expiration date
        result = subprocess.run(
            ["openssl", "x509", "-in", CERT_PEM, "-noout", "-enddate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Parse expiration date
        import datetime
        end_date_str = result.stdout.strip().split('=')[1]
        end_date = datetime.datetime.strptime(end_date_str, "%b %d %H:%M:%S %Y %Z")
        
        # Check if certificate is still valid (with 30 days buffer)
        now = datetime.datetime.now()
        thirty_days = datetime.timedelta(days=30)
        
        if end_date - now > thirty_days:
            logger.info(f"Certificate is valid until {end_date}")
            return True
        else:
            logger.warning(f"Certificate expires soon: {end_date}")
            return False
    except Exception as e:
        log_exception(logger, e, "check_certificate_valid")
        return False

def check_certbot_installed():
    """Check if certbot is installed"""
    try:
        subprocess.run(
            ["certbot", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("certbot is not installed. Please install certbot to use Let's Encrypt certificates.")
        logger.error("Installation instructions: https://certbot.eff.org/instructions")
        return False

def generate_self_signed_certificate():
    """Generate a self-signed certificate for Privacy AI"""
    # Load certificate configuration
    config = load_cert_config()
    
    try:
        logger.info("Generating new self-signed Privacy AI certificate...")
        
        # Create certificate directory if it doesn't exist
        ensure_cert_directory()
        
        # Generate private key
        subprocess.run([
            "openssl", "genrsa",
            "-out", CERT_KEY,
            "4096"
        ], check=True)
        
        # Generate certificate signing request
        csr_path = os.path.join(CERT_DIR, "privacy_ai_ca.csr")
        subprocess.run([
            "openssl", "req",
            "-new",
            "-key", CERT_KEY,
            "-out", csr_path,
            "-subj", f"/CN={config['common_name']}/O={config['org_name']}/C={config['country']}"
        ], check=True)
        
        # Generate self-signed certificate
        subprocess.run([
            "openssl", "x509",
            "-req",
            "-days", str(config['validity_days']),
            "-in", csr_path,
            "-signkey", CERT_KEY,
            "-out", CERT_PEM
        ], check=True)
        
        # Clean up CSR file
        if os.path.exists(csr_path):
            os.remove(csr_path)
            
        # Update config with creation and expiration dates
        now = datetime.datetime.now()
        config['created_at'] = now.isoformat()
        expiry = now + datetime.timedelta(days=config['validity_days'])
        config['expires_at'] = expiry.isoformat()
        config['cert_type'] = "self-signed"
        save_cert_config(config)
        
        logger.info(f"Self-signed Privacy AI certificate generated successfully (valid for {config['validity_days']} days)")
        
        # Create additional certificate formats
        create_additional_formats()
        
        return True
    except Exception as e:
        log_exception(logger, e, "generate_self_signed_certificate")
        return False

def generate_certificate(domain=None):
    """Generate a certificate for Privacy AI (Let's Encrypt or self-signed)"""
    # Load certificate configuration
    config = load_cert_config()
    
    # Check if certificate exists and is valid
    if check_certificate_exists() and check_certificate_valid():
        logger.info("Valid Privacy AI certificate already exists, skipping generation")
        return True
        
def generate_lets_encrypt_certificate(domain):
    """Generate a Let's Encrypt certificate for the specified domain"""
    if not check_certbot_installed():
        return False
        
    try:
        logger.info(f"Generating Let's Encrypt certificate for domain: {domain}")
        
        # Create certificate directory if it doesn't exist
        ensure_cert_directory()
        
        # Run certbot to obtain certificate
        subprocess.run([
            "certbot", "certonly", "--standalone", "--non-interactive",
            "--agree-tos", "--email", f"admin@{domain}", "-d", domain
        ], check=True)
        
        # Copy Let's Encrypt certificates to our directory
        letsencrypt_dir = f"/etc/letsencrypt/live/{domain}"
        if not os.path.exists(letsencrypt_dir):
            logger.error(f"Let's Encrypt certificate directory not found: {letsencrypt_dir}")
            return False
            
        # Copy certificates
        shutil.copy(os.path.join(letsencrypt_dir, "privkey.pem"), CERT_KEY)
        shutil.copy(os.path.join(letsencrypt_dir, "fullchain.pem"), CERT_PEM)
        
        # Create additional certificate formats
        create_additional_formats()
        
        # Update config with creation and expiration dates
        config = load_cert_config()
        now = datetime.datetime.now()
        config['created_at'] = now.isoformat()
        expiry = now + datetime.timedelta(days=90)  # Let's Encrypt certificates are valid for 90 days
        config['expires_at'] = expiry.isoformat()
        config['domain'] = domain
        config['cert_type'] = "letsencrypt"
        save_cert_config(config)
        
        # Set up auto-renewal
        setup_auto_renewal(domain)
        
        logger.info(f"Let's Encrypt certificate obtained successfully for {domain}")
        return True
    except Exception as e:
        log_exception(logger, e, "generate_lets_encrypt_certificate")
        return False

def setup_auto_renewal(domain):
    """Set up auto-renewal for Let's Encrypt certificates"""
    try:
        logger.info(f"Setting up auto-renewal for Let's Encrypt certificate for {domain}")
        
        # Create renewal hook script
        renewal_hook = os.path.join(CERT_DIR, "renewal-hook.sh")
        with open(renewal_hook, 'w') as f:
            f.write(f"""#!/bin/bash
# This script is called by certbot when the certificate is renewed

# Copy renewed certificates to Private AI directory
cp \"/etc/letsencrypt/live/{domain}/privkey.pem\" \"{CERT_KEY}\"
cp \"/etc/letsencrypt/live/{domain}/fullchain.pem\" \"{CERT_PEM}\"

# Create additional certificate formats
openssl pkcs12 -export -out \"{CERT_P12}\" -inkey \"{CERT_KEY}\" -in \"{CERT_PEM}\" -password pass:privacyai
openssl x509 -outform der -in \"{CERT_PEM}\" -out \"{CERT_CER}\"

# Restart any services that use the certificate
# Add your service restart commands here
""")
        
        # Make the script executable
        os.chmod(renewal_hook, 0o755)
        
        # Add renewal hook to certbot configuration
        renewal_hooks_dir = "/etc/letsencrypt/renewal-hooks/post"
        if os.path.exists(renewal_hooks_dir):
            try:
                dest_hook = os.path.join(renewal_hooks_dir, "private-ai-renewal.sh")
                subprocess.run(["sudo", "cp", renewal_hook, dest_hook], check=True)
                subprocess.run(["sudo", "chmod", "+x", dest_hook], check=True)
                logger.info("Renewal hook installed in certbot post-renewal directory")
            except subprocess.SubprocessError:
                logger.warning("Failed to install renewal hook in certbot directory. Manual renewal may be required.")
        else:
            logger.warning("Certbot renewal hooks directory not found. Manual renewal may be required.")
            
        logger.info("Auto-renewal setup completed")
        return True
    except Exception as e:
        log_exception(logger, e, "setup_auto_renewal")
        return False
    # Generate certificate based on whether a domain is provided
    if domain:
        return generate_lets_encrypt_certificate(domain)
    else:
        return generate_self_signed_certificate()

def create_additional_formats():
    """Create additional certificate formats (P12, CER) for different platforms"""
    try:
        if not os.path.exists(CERT_PEM):
            logger.error("Cannot create additional formats: PEM certificate not found")
            return False
            
        # Create P12 format (for Windows and macOS)
        subprocess.run([
            "openssl", "pkcs12", "-export",
            "-out", CERT_P12,
            "-inkey", CERT_KEY,
            "-in", CERT_PEM,
            "-password", "pass:privacyai"
        ], check=True)
        
        # Create CER format (for Windows)
        subprocess.run([
            "openssl", "x509", 
            "-outform", "der", 
            "-in", CERT_PEM,
            "-out", CERT_CER
        ], check=True)
        
        logger.info("Additional certificate formats created successfully")
        return True
    except Exception as e:
        log_exception(logger, e, "create_additional_formats")
        return False

def install_certificate_macos():
    """Install the certificate in the macOS system keychain"""
    try:
        if not os.path.exists(CERT_PEM):
            logger.error("Cannot install certificate: PEM certificate not found")
            return False
            
        logger.info("Installing certificate in macOS system keychain...")
        
        # First try with sudo
        try:
            result = subprocess.run([
                "sudo", "security", "add-trusted-cert", 
                "-d", "-r", "trustRoot",
                "-k", "/Library/Keychains/System.keychain",
                CERT_PEM
            ], check=True)
            logger.info("Certificate installed in system keychain successfully")
        except subprocess.CalledProcessError:
            # If sudo fails, try without sudo for user keychain
            logger.warning("Failed to install in system keychain, trying user keychain...")
            result = subprocess.run([
                "security", "add-trusted-cert", 
                "-d", "-r", "trustRoot",
                "-k", os.path.expanduser("~/Library/Keychains/login.keychain"),
                CERT_PEM
            ], check=True)
            logger.info("Certificate installed in user keychain successfully")
            
        return True
    except Exception as e:
        log_exception(logger, e, "install_certificate_macos")
        return False

def install_certificate_linux():
    """Install the certificate in the Linux system trust store"""
    try:
        if not os.path.exists(CERT_PEM):
            logger.error("Cannot install certificate: PEM certificate not found")
            return False
            
        logger.info("Installing certificate in Linux system trust store...")
        
        # Detect the Linux distribution and use the appropriate method
        if os.path.exists("/usr/local/share/ca-certificates/"):
            # Debian/Ubuntu
            cert_dest = "/usr/local/share/ca-certificates/private-ai-ca.crt"
            try:
                subprocess.run(["sudo", "cp", CERT_PEM, cert_dest], check=True)
                subprocess.run(["sudo", "update-ca-certificates"], check=True)
                logger.info("Certificate installed successfully (Debian/Ubuntu)")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install certificate: {str(e)}")
                return False
                
        elif os.path.exists("/etc/ca-certificates/trust-source/anchors/"):
            # Arch Linux
            cert_dest = "/etc/ca-certificates/trust-source/anchors/private-ai-ca.crt"
            try:
                subprocess.run(["sudo", "cp", CERT_PEM, cert_dest], check=True)
                subprocess.run(["sudo", "update-ca-trust"], check=True)
                logger.info("Certificate installed successfully (Arch)")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install certificate: {str(e)}")
                return False
                
        elif os.path.exists("/etc/pki/ca-trust/source/anchors/"):
            # RHEL/CentOS/Fedora
            cert_dest = "/etc/pki/ca-trust/source/anchors/private-ai-ca.crt"
            try:
                subprocess.run(["sudo", "cp", CERT_PEM, cert_dest], check=True)
                subprocess.run(["sudo", "update-ca-trust", "extract"], check=True)
                logger.info("Certificate installed successfully (RHEL/CentOS/Fedora)")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install certificate: {str(e)}")
                return False
        
        # Fallback for other distributions - try to install in user's browser directories
        logger.warning("Could not detect Linux distribution, trying browser-specific installation")
        return install_certificate_browsers()
    except Exception as e:
        log_exception(logger, e, "install_certificate_linux")
        return False

def install_certificate_windows():
    """Install the certificate in the Windows certificate store"""
    try:
        if not os.path.exists(CERT_CER):
            logger.error("Cannot install certificate: CER certificate not found")
            return False
            
        logger.info("Installing certificate in Windows certificate store...")
        
        # Create a temporary PowerShell script to import the certificate
        ps_script = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False)
        ps_script.write(f"""
        $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2("{CERT_CER}")
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "LocalMachine")
        $store.Open("ReadWrite")
        $store.Add($cert)
        $store.Close()
        Write-Host "Certificate installed successfully"
        """.encode())
        ps_script.close()
        
        # Run the PowerShell script with elevated privileges
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script.name
        ], check=True)
        
        # Clean up the temporary script
        os.unlink(ps_script.name)
        
        logger.info("Certificate installed in Windows certificate store successfully")
        return True
    except Exception as e:
        log_exception(logger, e, "install_certificate_windows")
        return False

def install_certificate_browsers():
    """Install the certificate in browser-specific certificate stores"""
    success = False
    
    # Chrome/Chromium
    try:
        chrome_dirs = []
        
        if platform.system() == "Linux":
            # Linux Chrome/Chromium
            chrome_dirs = [
                os.path.expanduser("~/.pki/nssdb"),  # Chrome/Chromium
                os.path.expanduser("~/.config/chromium/Default/Network"),  # Chromium
                os.path.expanduser("~/.config/google-chrome/Default/Network")  # Chrome
            ]
        elif platform.system() == "Darwin":
            # macOS Chrome/Chromium
            chrome_dirs = [
                os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Network"),
                os.path.expanduser("~/Library/Application Support/Chromium/Default/Network")
            ]
        elif platform.system() == "Windows":
            # Windows Chrome/Chromium
            chrome_dirs = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google/Chrome/User Data/Default/Network"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Chromium/User Data/Default/Network")
            ]
            
        for chrome_dir in chrome_dirs:
            if os.path.exists(chrome_dir):
                try:
                    # Use certutil to install the certificate
                    subprocess.run([
                        "certutil", "-d", "sql:" + chrome_dir,
                        "-A", "-t", "C,,", "-n", "private-ai",
                        "-i", CERT_PEM
                    ], check=True)
                    logger.info(f"Certificate installed in Chrome/Chromium directory: {chrome_dir}")
                    success = True
                except Exception as e:
                    logger.warning(f"Failed to install certificate in {chrome_dir}: {str(e)}")
    except Exception as e:
        logger.warning(f"Error installing certificate in Chrome/Chromium: {str(e)}")
    
    # Firefox
    try:
        firefox_dirs = []
        
        if platform.system() == "Linux":
            # Find Firefox profiles
            firefox_profile_dir = os.path.expanduser("~/.mozilla/firefox")
            if os.path.exists(firefox_profile_dir):
                for profile in os.listdir(firefox_profile_dir):
                    if profile.endswith(".default") or "default" in profile:
                        firefox_dirs.append(os.path.join(firefox_profile_dir, profile))
        elif platform.system() == "Darwin":
            # macOS Firefox
            firefox_profile_dir = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
            if os.path.exists(firefox_profile_dir):
                for profile in os.listdir(firefox_profile_dir):
                    if profile.endswith(".default") or "default" in profile:
                        firefox_dirs.append(os.path.join(firefox_profile_dir, profile))
        elif platform.system() == "Windows":
            # Windows Firefox
            firefox_profile_dir = os.path.join(os.environ.get("APPDATA", ""), "Mozilla/Firefox/Profiles")
            if os.path.exists(firefox_profile_dir):
                for profile in os.listdir(firefox_profile_dir):
                    if profile.endswith(".default") or "default" in profile:
                        firefox_dirs.append(os.path.join(firefox_profile_dir, profile))
                        
        for firefox_dir in firefox_dirs:
            if os.path.exists(firefox_dir):
                try:
                    # Create cert9.db if it doesn't exist
                    cert_db = os.path.join(firefox_dir, "cert9.db")
                    if not os.path.exists(cert_db):
                        subprocess.run([
                            "certutil", "-d", "sql:" + firefox_dir,
                            "-N", "--empty-password"
                        ], check=True)
                    
                    # Use certutil to install the certificate
                    subprocess.run([
                        "certutil", "-d", "sql:" + firefox_dir,
                        "-A", "-t", "C,,", "-n", "private-ai",
                        "-i", CERT_PEM
                    ], check=True)
                    logger.info(f"Certificate installed in Firefox directory: {firefox_dir}")
                    success = True
                except Exception as e:
                    logger.warning(f"Failed to install certificate in {firefox_dir}: {str(e)}")
    except Exception as e:
        logger.warning(f"Error installing certificate in Firefox: {str(e)}")
def configure_web_server():
    """Configure web server to use the certificates"""
    try:
        logger.info("Configuring web server to use Let's Encrypt certificates...")
        
        # Check if nginx is installed
        nginx_installed = False
        try:
            subprocess.run(["nginx", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            nginx_installed = True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        if nginx_installed:
            logger.info("Nginx detected, configuring SSL settings...")
            
            # Create nginx configuration for SSL
            nginx_conf = "/tmp/private-ai-ssl.conf"
            with open(nginx_conf, 'w') as f:
                f.write(f"""server {{
    listen 443 ssl;
    server_name _;
    
    ssl_certificate {CERT_PEM};
    ssl_certificate_key {CERT_KEY};
    
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
    location / {{
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}""")
            
            logger.info(f"Nginx SSL configuration created at {nginx_conf}")
            logger.info("To use this configuration, copy it to your nginx sites directory and reload nginx:")
            logger.info(f"sudo cp {nginx_conf} /etc/nginx/sites-available/private-ai-ssl")
            logger.info("sudo ln -s /etc/nginx/sites-available/private-ai-ssl /etc/nginx/sites-enabled/")
            logger.info("sudo nginx -t && sudo systemctl reload nginx")
            
        # Check if Apache is installed
        apache_installed = False
        try:
            subprocess.run(["apache2", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            apache_installed = True
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                subprocess.run(["httpd", "-v"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                apache_installed = True
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
                
        if apache_installed:
            logger.info("Apache detected, configuring SSL settings...")
            
            # Create Apache configuration for SSL
            apache_conf = "/tmp/private-ai-ssl.conf"
            with open(apache_conf, 'w') as f:
                f.write(f"""<VirtualHost *:443>
    ServerName private-ai
    
    SSLEngine on
    SSLCertificateFile {CERT_PEM}
    SSLCertificateKeyFile {CERT_KEY}
    
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
</VirtualHost>""")
            
            logger.info(f"Apache SSL configuration created at {apache_conf}")
            logger.info("To use this configuration, copy it to your Apache sites directory and reload Apache:")
            logger.info(f"sudo cp {apache_conf} /etc/apache2/sites-available/private-ai-ssl.conf")
            logger.info("sudo a2ensite private-ai-ssl")
            logger.info("sudo a2enmod ssl proxy proxy_http headers")
            logger.info("sudo apachectl configtest && sudo systemctl reload apache2")
            
        # Configure mitmdump to use the new certificates
        mitm_conf = os.path.expanduser("~/.mitmproxy/config.yaml")
        os.makedirs(os.path.dirname(mitm_conf), exist_ok=True)
        with open(mitm_conf, 'w') as f:
            f.write(f"""# mitmproxy configuration for Private AI
ssl_verify_upstream: false
onboarding: false
ssl_insecure: true
# Use Let's Encrypt certificates
certs:
  - {CERT_PEM}
  - {CERT_KEY}
""")
        
        logger.info(f"mitmdump configuration created at {mitm_conf}")
        logger.info("To use this configuration, run mitmdump with: mitmdump --set confdir=~/.mitmproxy")
        
        return True
    except Exception as e:
        log_exception(logger, e, "configure_web_server")
        return False
    
    return False

def configure_ide_certificates():
    """Configure IDE-specific certificate settings"""
    try:
        # VS Code configuration
        vscode_settings = []
        
        if platform.system() == "Windows":
            vscode_settings.append(os.path.join(os.environ.get("APPDATA", ""), "Code/User/settings.json"))
        elif platform.system() == "Darwin":
            vscode_settings.append(os.path.expanduser("~/Library/Application Support/Code/User/settings.json"))
        elif platform.system() == "Linux":
            vscode_settings.append(os.path.expanduser("~/.config/Code/User/settings.json"))
            
        for settings_path in vscode_settings:
            if os.path.exists(settings_path):
                try:
                    import json
                    
                    # Read existing settings
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                        
                    # Update proxy settings
                    settings["http.proxy"] = "http://localhost:8080"
                    settings["http.proxyStrictSSL"] = False
                    
                    # Write updated settings
                    with open(settings_path, 'w') as f:
                        json.dump(settings, f, indent=4)
                        
                    logger.info(f"VS Code settings updated at {settings_path}")
                except Exception as e:
                    logger.warning(f"Failed to update VS Code settings at {settings_path}: {str(e)}")
                    
        # JetBrains IDEs
        # Note: JetBrains IDEs require manual certificate import
        # We'll just log instructions for the user
        logger.info("For JetBrains IDEs, manually import the certificate in Settings → Tools → Server Certificates")
        
        return True
    except Exception as e:
        log_exception(logger, e, "configure_ide_certificates")
        return False

def setup_certificates(domain=None):
    """Main function to set up certificates for the proxy"""
    logger.info("Starting Privacy AI certificate setup...")
    
    # Ensure certificate directory exists
    ensure_cert_directory()
    
    # Generate certificate if it doesn't exist or is expiring
    if not check_certificate_exists() or not check_certificate_valid():
        if not generate_certificate(domain):
            logger.error("Failed to generate Privacy AI certificate")
            return False
    else:
        # Create additional formats if they don't exist
        if not os.path.exists(CERT_P12) or not os.path.exists(CERT_CER):
            create_additional_formats()
            
        # Load and display certificate info
        config = load_cert_config()
        logger.info(f"Using existing Privacy AI certificate:")
        logger.info(f"  - Common Name: {config.get('common_name', 'Privacy AI Certificate Authority')}")
        logger.info(f"  - Organization: {config.get('org_name', 'Privacy AI')}")
        if config.get('expires_at'):
            logger.info(f"  - Expires: {config.get('expires_at')}")
        if config.get('domain'):
            logger.info(f"  - Domain: {config.get('domain')}")
        if config.get('cert_type'):
            logger.info(f"  - Certificate Type: {config.get('cert_type')}")
    
    # Install certificate based on platform
    system = platform.system()
    if system == "Darwin":
        install_certificate_macos()
    elif system == "Linux":
        install_certificate_linux()
    elif system == "Windows":
        install_certificate_windows()
    else:
        logger.warning(f"Unsupported platform: {system}")
        
    # Configure IDE certificates
    configure_ide_certificates()
    
    # Configure web server
    configure_web_server()
    
    logger.info("Certificate setup completed")
    return True

def print_certificate_instructions():
    """Print instructions for manual certificate installation"""
    print("\n=== Privacy AI Certificate Installation Instructions ===\n")
    print(f"Certificate location: {CERT_PEM}")
    
    if platform.system() == "Darwin":
        print("\nFor macOS:")
        print("1. Open Keychain Access")
        print("2. Select System keychain")
        print("3. File → Import Items → Select the certificate")
        print("4. Double-click the imported certificate")
        print("5. Expand 'Trust' and set 'When using this certificate' to 'Always Trust'")
        
    elif platform.system() == "Linux":
        print("\nFor Linux:")
        print("1. Copy the certificate to the system certificate directory:")
        print(f"   sudo cp {CERT_PEM} /usr/local/share/ca-certificates/private-ai-ca.crt")
        print("2. Update the certificate store:")
        print("   sudo update-ca-certificates")
        
    elif platform.system() == "Windows":
        print("\nFor Windows:")
        print("1. Double-click the certificate file")
        print("2. Select 'Install Certificate'")
        print("3. Select 'Local Machine' and click Next")
        print("4. Select 'Place all certificates in the following store'")
        print("5. Click 'Browse' and select 'Trusted Root Certification Authorities'")
        print("6. Click 'Next' and then 'Finish'")
        
    print("\nFor VS Code:")
    print("1. Open settings.json (File → Preferences → Settings → Edit in settings.json)")
    print('2. Add the following lines:')
    print('   "http.proxy": "http://localhost:8080",')
    print('   "http.proxyStrictSSL": false')
    
    print("\nFor JetBrains IDEs:")
    print("1. Open Settings → Tools → Server Certificates")
    print("2. Click 'Import' and select the certificate file")
    
    print("\nFor Firefox:")
    print("1. Open Firefox and go to about:preferences#privacy")
    print("2. Scroll down to 'Certificates' and click 'View Certificates'")
    print("3. Go to 'Authorities' tab and click 'Import'")
    print("4. Select the certificate file and check 'Trust this CA to identify websites'")
    
    print("\n=== End of Instructions ===\n")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Set up certificates for Private AI proxy")
    parser.add_argument("--print-instructions", action="store_true", help="Print manual installation instructions")
    parser.add_argument("--generate-only", action="store_true", help="Only generate certificates, don't install")
    parser.add_argument("--install", action="store_true", help="Install certificates")
    parser.add_argument("--configure-ides", action="store_true", help="Configure IDE certificate settings")
    parser.add_argument("--domain", help="Domain name for Let's Encrypt certificate")
    
    args = parser.parse_args()
    
    if args.print_instructions:
        print_certificate_instructions()
    elif args.generate_only:
        ensure_cert_directory()
        generate_certificate(args.domain)
    elif args.install:
        system = platform.system()
        if system == "Darwin":
            install_certificate_macos()
        elif system == "Linux":
            install_certificate_linux()
        elif system == "Windows":
            install_certificate_windows()
        else:
            logger.warning(f"Unsupported platform: {system}")
    elif args.configure_ides:
        configure_ide_certificates()
    else:
        # Run the full setup
        setup_certificates(args.domain)
