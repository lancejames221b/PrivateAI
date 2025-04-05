#!/usr/bin/env python3
"""
Private AI 🕵️ - Enhanced Certificate Management

This module provides a unified, cross-platform approach to certificate management
for the Private AI proxy. It handles certificate generation, installation, and validation
across different operating systems and browsers.

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
import time
from typing import Dict, Optional, List, Tuple, Any, Union

# Initialize logger
from logger import get_logger, log_exception
logger = get_logger("certificate-manager", "logs/certificate_manager.log")

class CertificateManager:
    """Unified certificate management across platforms"""
    
    def __init__(self, cert_dir: str = None, config: Dict = None):
        """
        Initialize the certificate manager
        
        Args:
            cert_dir: Directory to store certificates (default: ~/.private-ai)
            config: Certificate configuration (optional)
        """
        # Set certificate directory
        self.cert_dir = cert_dir or os.path.expanduser("~/.private-ai")
        
        # Certificate paths
        self.cert_pem = os.path.join(self.cert_dir, "private-ai-ca-cert.pem")
        self.cert_key = os.path.join(self.cert_dir, "private-ai-ca.key")
        self.cert_p12 = os.path.join(self.cert_dir, "private-ai-ca-cert.p12")
        self.cert_cer = os.path.join(self.cert_dir, "private-ai-ca-cert.cer")
        self.cert_config_path = os.path.join(self.cert_dir, "cert_config.json")
        
        # Default certificate configuration
        self.default_config = {
            "common_name": "Privacy AI Certificate Authority",
            "org_name": "Privacy AI",
            "country": "US",
            "validity_days": 90,
            "created_at": None,
            "expires_at": None,
            "cert_type": "self-signed"
        }
        
        # Load or set configuration
        self.config = config or self.load_config()
        
        # Detect platform
        self.platform = platform.system()
        
    def load_config(self) -> Dict:
        """Load certificate configuration from file"""
        if os.path.exists(self.cert_config_path):
            try:
                with open(self.cert_config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log_exception(logger, e, "load_config")
        
        # Return default configuration if file doesn't exist or can't be read
        return self.default_config.copy()
    
    def save_config(self) -> bool:
        """Save certificate configuration to file"""
        try:
            with open(self.cert_config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            log_exception(logger, e, "save_config")
            return False
    
    def ensure_cert_directory(self) -> bool:
        """Ensure the certificate directory exists with proper permissions"""
        try:
            os.makedirs(self.cert_dir, mode=0o700, exist_ok=True)
            logger.info(f"Certificate directory ensured at {self.cert_dir}")
            return True
        except Exception as e:
            log_exception(logger, e, "ensure_cert_directory")
            return False
    
    def check_certificate_exists(self) -> bool:
        """Check if the certificate already exists"""
        return os.path.exists(self.cert_pem) and os.path.exists(self.cert_key)
    
    def check_certificate_valid(self) -> bool:
        """Check if the existing certificate is still valid"""
        if not self.check_certificate_exists():
            return False
            
        try:
            # Get certificate expiration date
            result = subprocess.run(
                ["openssl", "x509", "-in", self.cert_pem, "-noout", "-enddate"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Parse expiration date
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
    
    def generate_certificate(self, domain: str = None, force: bool = False) -> bool:
        """
        Generate a certificate (Let's Encrypt or self-signed)
        
        Args:
            domain: Domain for Let's Encrypt certificate (optional)
            force: Force certificate regeneration even if valid (default: False)
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if certificate exists and is valid
        if not force and self.check_certificate_exists() and self.check_certificate_valid():
            logger.info("Valid certificate already exists, skipping generation")
            return True
            
        # Generate certificate based on whether a domain is provided
        if domain:
            return self.generate_lets_encrypt_certificate(domain)
        else:
            return self.generate_self_signed_certificate()
    
    def generate_self_signed_certificate(self) -> bool:
        """Generate a self-signed certificate"""
        try:
            logger.info("Generating new self-signed certificate...")
            
            # Create certificate directory if it doesn't exist
            self.ensure_cert_directory()
            
            # Generate private key
            subprocess.run([
                "openssl", "genrsa",
                "-out", self.cert_key,
                "4096"
            ], check=True)
            
            # Generate certificate signing request
            csr_path = os.path.join(self.cert_dir, "privacy_ai_ca.csr")
            subprocess.run([
                "openssl", "req",
                "-new",
                "-key", self.cert_key,
                "-out", csr_path,
                "-subj", f"/CN={self.config['common_name']}/O={self.config['org_name']}/C={self.config['country']}"
            ], check=True)
            
            # Generate self-signed certificate
            subprocess.run([
                "openssl", "x509",
                "-req",
                "-days", str(self.config['validity_days']),
                "-in", csr_path,
                "-signkey", self.cert_key,
                "-out", self.cert_pem
            ], check=True)
            
            # Clean up CSR file
            if os.path.exists(csr_path):
                os.remove(csr_path)
                
            # Update config with creation and expiration dates
            now = datetime.datetime.now()
            self.config['created_at'] = now.isoformat()
            expiry = now + datetime.timedelta(days=self.config['validity_days'])
            self.config['expires_at'] = expiry.isoformat()
            self.config['cert_type'] = "self-signed"
            self.save_config()
            
            logger.info(f"Self-signed certificate generated successfully (valid for {self.config['validity_days']} days)")
            
            # Create additional certificate formats
            self.create_additional_formats()
            
            return True
        except Exception as e:
            log_exception(logger, e, "generate_self_signed_certificate")
            return False
    
    def generate_lets_encrypt_certificate(self, domain: str) -> bool:
        """
        Generate a Let's Encrypt certificate for the specified domain
        
        Args:
            domain: Domain for Let's Encrypt certificate
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if certbot is installed
        try:
            subprocess.run(
                ["certbot", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.error("certbot is not installed. Please install certbot to use Let's Encrypt certificates.")
            logger.error("Installation instructions: https://certbot.eff.org/instructions")
            return False
            
        try:
            logger.info(f"Generating Let's Encrypt certificate for domain: {domain}")
            
            # Create certificate directory if it doesn't exist
            self.ensure_cert_directory()
            
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
            shutil.copy(os.path.join(letsencrypt_dir, "privkey.pem"), self.cert_key)
            shutil.copy(os.path.join(letsencrypt_dir, "fullchain.pem"), self.cert_pem)
            
            # Create additional certificate formats
            self.create_additional_formats()
            
            # Update config with creation and expiration dates
            now = datetime.datetime.now()
            self.config['created_at'] = now.isoformat()
            expiry = now + datetime.timedelta(days=90)  # Let's Encrypt certificates are valid for 90 days
            self.config['expires_at'] = expiry.isoformat()
            self.config['domain'] = domain
            self.config['cert_type'] = "letsencrypt"
            self.save_config()
            
            # Set up auto-renewal
            self.setup_auto_renewal(domain)
            
            logger.info(f"Let's Encrypt certificate obtained successfully for {domain}")
            return True
        except Exception as e:
            log_exception(logger, e, "generate_lets_encrypt_certificate")
            return False
    
    def create_additional_formats(self) -> bool:
        """Create additional certificate formats (P12, CER) for different platforms"""
        try:
            if not os.path.exists(self.cert_pem):
                logger.error("Cannot create additional formats: PEM certificate not found")
                return False
                
            # Create P12 format (for Windows and macOS)
            subprocess.run([
                "openssl", "pkcs12", "-export",
                "-out", self.cert_p12,
                "-inkey", self.cert_key,
                "-in", self.cert_pem,
                "-password", "pass:privacyai"
            ], check=True)
            
            # Create CER format (for Windows)
            subprocess.run([
                "openssl", "x509", 
                "-outform", "der", 
                "-in", self.cert_pem,
                "-out", self.cert_cer
            ], check=True)
            
            logger.info("Additional certificate formats created successfully")
            return True
        except Exception as e:
            log_exception(logger, e, "create_additional_formats")
            return False
    
    def setup_auto_renewal(self, domain: str) -> bool:
        """Set up auto-renewal for Let's Encrypt certificates"""
        try:
            logger.info(f"Setting up auto-renewal for Let's Encrypt certificate for {domain}")
            
            # Create renewal hook script
            renewal_hook = os.path.join(self.cert_dir, "renewal-hook.sh")
            with open(renewal_hook, 'w') as f:
                f.write(f"""#!/bin/bash
# This script is called by certbot when the certificate is renewed

# Copy renewed certificates to Private AI directory
cp "/etc/letsencrypt/live/{domain}/privkey.pem" "{self.cert_key}"
cp "/etc/letsencrypt/live/{domain}/fullchain.pem" "{self.cert_pem}"

# Create additional certificate formats
openssl pkcs12 -export -out "{self.cert_p12}" -inkey "{self.cert_key}" -in "{self.cert_pem}" -password pass:privacyai
openssl x509 -outform der -in "{self.cert_pem}" -out "{self.cert_cer}"

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
    
    def install_certificate(self) -> bool:
        """Install the certificate in the system trust store based on platform"""
        if self.platform == "Darwin":
            return self.install_certificate_macos()
        elif self.platform == "Linux":
            return self.install_certificate_linux()
        elif self.platform == "Windows":
            return self.install_certificate_windows()
        else:
            logger.error(f"Unsupported platform: {self.platform}")
            return False
    
    def install_certificate_macos(self) -> bool:
        """Install the certificate in the macOS system keychain"""
        try:
            if not os.path.exists(self.cert_pem):
                logger.error("Cannot install certificate: PEM certificate not found")
                return False
                
            logger.info("Installing certificate in macOS system keychain...")
            
            # First try with sudo
            try:
                result = subprocess.run([
                    "sudo", "security", "add-trusted-cert", 
                    "-d", "-r", "trustRoot",
                    "-k", "/Library/Keychains/System.keychain",
                    self.cert_pem
                ], check=True)
                logger.info("Certificate installed in system keychain successfully")
            except subprocess.CalledProcessError:
                # If sudo fails, try without sudo for user keychain
                logger.warning("Failed to install in system keychain, trying user keychain...")
                result = subprocess.run([
                    "security", "add-trusted-cert", 
                    "-d", "-r", "trustRoot",
                    "-k", os.path.expanduser("~/Library/Keychains/login.keychain"),
                    self.cert_pem
                ], check=True)
                logger.info("Certificate installed in user keychain successfully")
                
            return True
        except Exception as e:
            log_exception(logger, e, "install_certificate_macos")
            return False
    
    def install_certificate_linux(self) -> bool:
        """Install the certificate in the Linux system trust store"""
        try:
            if not os.path.exists(self.cert_pem):
                logger.error("Cannot install certificate: PEM certificate not found")
                return False
                
            logger.info("Installing certificate in Linux system trust store...")
            
            # Detect the Linux distribution and use the appropriate method
            if os.path.exists("/usr/local/share/ca-certificates/"):
                # Debian/Ubuntu
                cert_dest = "/usr/local/share/ca-certificates/private-ai-ca.crt"
                try:
                    subprocess.run(["sudo", "cp", self.cert_pem, cert_dest], check=True)
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
                    subprocess.run(["sudo", "cp", self.cert_pem, cert_dest], check=True)
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
                    subprocess.run(["sudo", "cp", self.cert_pem, cert_dest], check=True)
                    subprocess.run(["sudo", "update-ca-trust", "extract"], check=True)
                    logger.info("Certificate installed successfully (RHEL/CentOS/Fedora)")
                    return True
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to install certificate: {str(e)}")
                    return False
            
            # Fallback for other distributions - try to install in user's browser directories
            logger.warning("Could not detect Linux distribution, trying browser-specific installation")
            return self.install_certificate_browsers()
        except Exception as e:
            log_exception(logger, e, "install_certificate_linux")
            return False
    
    def install_certificate_windows(self) -> bool:
        """Install the certificate in the Windows certificate store"""
        try:
            if not os.path.exists(self.cert_cer):
                logger.error("Cannot install certificate: CER certificate not found")
                return False
                
            logger.info("Installing certificate in Windows certificate store...")
            
            # Create a temporary PowerShell script to import the certificate
            ps_script = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False)
            ps_script.write(f"""
            $cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2("{self.cert_cer}")
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
    
    def install_certificate_browsers(self) -> bool:
        """Install the certificate in browser-specific certificate stores"""
        success = False
        
        # Chrome/Chromium
        try:
            chrome_dirs = []
            
            if self.platform == "Linux":
                # Linux Chrome/Chromium
                chrome_dirs = [
                    os.path.expanduser("~/.pki/nssdb"),  # Chrome/Chromium
                    os.path.expanduser("~/.config/chromium/Default/Network"),  # Chromium
                    os.path.expanduser("~/.config/google-chrome/Default/Network")  # Chrome
                ]
            elif self.platform == "Darwin":
                # macOS Chrome/Chromium
                chrome_dirs = [
                    os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Network"),
                    os.path.expanduser("~/Library/Application Support/Chromium/Default/Network")
                ]
            elif self.platform == "Windows":
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
                            "-i", self.cert_pem
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
            
            if self.platform == "Linux":
                # Linux Firefox
                firefox_profile_dir = os.path.expanduser("~/.mozilla/firefox")
                if os.path.exists(firefox_profile_dir):
                    for profile in os.listdir(firefox_profile_dir):
                        if profile.endswith(".default") or "default" in profile:
                            firefox_dirs.append(os.path.join(firefox_profile_dir, profile))
            elif self.platform == "Darwin":
                # macOS Firefox
                firefox_profile_dir = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
                if os.path.exists(firefox_profile_dir):
                    for profile in os.listdir(firefox_profile_dir):
                        if profile.endswith(".default") or "default" in profile:
                            firefox_dirs.append(os.path.join(firefox_profile_dir, profile))
            elif self.platform == "Windows":
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
                        
                        # Install certificate
                        subprocess.run([
                            "certutil", "-d", "sql:" + firefox_dir,
                            "-A", "-t", "C,,", "-n", "private-ai",
                            "-i", self.cert_pem
                        ], check=True)
                        logger.info(f"Certificate installed in Firefox directory: {firefox_dir}")
                        success = True
                    except Exception as e:
                        logger.warning(f"Failed to install certificate in {firefox_dir}: {str(e)}")
        except Exception as e:
            logger.warning(f"Error installing certificate in Firefox: {str(e)}")
        
        return success
    
    def configure_ide_certificates(self) -> bool:
        """Configure certificates for IDEs (VS Code, etc.)"""
        try:
            logger.info("Configuring certificates for IDEs...")
            
            # VS Code settings
            vscode_settings_dir = os.path.expanduser("~/.vscode")
            os.makedirs(vscode_settings_dir, exist_ok=True)
            
            vscode_settings_path = os.path.join(vscode_settings_dir, "settings.json")
            vscode_settings = {}
            
            # Load existing settings if they exist
            if os.path.exists(vscode_settings_path):
                try:
                    with open(vscode_settings_path, 'r') as f:
                        vscode_settings = json.load(f)
                except:
                    pass
            
            # Update settings
            vscode_settings.update({
                "http.proxy": "http://127.0.0.1:8080",
                "http.proxyStrictSSL": False,
                "http.proxySupport": "override",
                "github.copilot.advanced": {
                    "proxy": "http://127.0.0.1:8080"
                }
            })
            
            # Save settings
            with open(vscode_settings_path, 'w') as f:
                json.dump(vscode_settings, f, indent=2)
            
            logger.info(f"VS Code settings updated at {vscode_settings_path}")
            
            # Create environment variables script
            env_script_path = os.path.join(self.cert_dir, "ide_proxy_env.sh")
            with open(env_script_path, 'w') as f:
                f.write(f"""#!/bin/bash

# Path to Private AI certificate
CERT_PATH="{self.cert_pem}"

# Configure Node.js to trust our certificate - Copilot specifically looks for this
export NODE_EXTRA_CA_CERTS="$CERT_PATH"

# Configure proxy for all HTTP/HTTPS requests
export HTTP_PROXY="http://127.0.0.1:8080"
export HTTPS_PROXY="http://127.0.0.1:8080"
export NO_PROXY="localhost,127.0.0.1"

echo "Environment variables set for IDE proxy integration"
echo "NODE_EXTRA_CA_CERTS=$NODE_EXTRA_CA_CERTS"
echo "HTTP_PROXY=$HTTP_PROXY"
echo "HTTPS_PROXY=$HTTPS_PROXY"
""")
            
            # Make script executable
            os.chmod(env_script_path, 0o755)
            
            logger.info(f"IDE environment script created at {env_script_path}")
            return True
        except Exception as e:
            log_exception(logger, e, "configure_ide_certificates")
            return False
    
    def print_certificate_info(self) -> Dict:
        """Print certificate information and return as a dictionary"""
        info = {
            "exists": self.check_certificate_exists(),
            "valid": False,
            "path": self.cert_pem,
            "config": self.config,
            "expires_at": None,
            "created_at": None,
            "days_remaining": None
        }
        
        if info["exists"]:
            try:
                # Get certificate information
                result = subprocess.run(
                    ["openssl", "x509", "-in", self.cert_pem, "-noout", "-text"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                
                # Get expiration date
                end_date_result = subprocess.run(
                    ["openssl", "x509", "-in", self.cert_pem, "-noout", "-enddate"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True
                )
                
                # Parse expiration date
                end_date_str = end_date_result.stdout.strip().split('=')[1]
                end_date = datetime.datetime.strptime(end_date_str, "%b %d %H:%M:%S %Y %Z")
                
                # Calculate days remaining
                now = datetime.datetime.now()
                days_remaining = (end_date - now).days
                
                info["valid"] = days_remaining > 0
                info["expires_at"] = end_date.isoformat()
                info["days_remaining"] = days_remaining
                info["created_at"] = self.config.get("created_at")
                info["details"] = result.stdout
                
                logger.info(f"Certificate information retrieved: valid={info['valid']}, days_remaining={days_remaining}")
            except Exception as e:
                log_exception(logger, e, "print_certificate_info")
        
        return info

# Singleton instance for easy access
certificate_manager = CertificateManager()

def setup_certificates(domain: str = None, force: bool = False) -> bool:
    """
    Set up certificates for the Private AI proxy
    
    Args:
        domain: Domain for Let's Encrypt certificate (optional)
        force: Force certificate regeneration even if valid (default: False)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize certificate manager
        cert_manager = certificate_manager
        
        # Generate certificate
        if not cert_manager.generate_certificate(domain, force):
            logger.error("Failed to generate certificate")
            return False
        
        # Install certificate
        if not cert_manager.install_certificate():
            logger.warning("Failed to install certificate in system trust store")
            # Continue anyway, as we'll configure IDE certificates
        
        # Configure IDE certificates
        if not cert_manager.configure_ide_certificates():
            logger.warning("Failed to configure IDE certificates")
            # Continue anyway, as we've already generated the certificate
        
        logger.info("Certificate setup completed successfully")
        return True
    except Exception as e:
        log_exception(logger, e, "setup_certificates")
        return False
