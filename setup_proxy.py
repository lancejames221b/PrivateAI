#!/usr/bin/env python3
"""
Private AI 🕵️ - System-wide Proxy Configuration

This module provides utilities to configure system-wide proxy settings across
different platforms (macOS, Windows, Linux). It ensures that all applications,
including IDE-based AI assistants, respect the proxy settings.

Author: Lance James @ Unit 221B
"""

import os
import sys
import subprocess
import platform
import tempfile
import shutil
from pathlib import Path
import logging
import re
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("proxy-config", "logs/proxy_config.log")

# Default proxy settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8080
DEFAULT_PROXY_URL = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"

def configure_proxy_macos(host=DEFAULT_HOST, port=DEFAULT_PORT, enable=True):
    """Configure proxy settings on macOS"""
    try:
        logger.info(f"Configuring macOS proxy settings: {'enable' if enable else 'disable'}")
        
        # Get list of network services
        result = subprocess.run(
            ["networksetup", "-listallnetworkservices"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the output to get network service names
        services = result.stdout.strip().split('\n')
        # Skip the first line which is a header
        services = services[1:]
        
        success = False
        
        for service in services:
            try:
                if enable:
                    # Configure HTTP proxy
                    subprocess.run(
                        ["networksetup", "-setwebproxy", service, host, str(port)],
                        check=True
                    )
                    
                    # Configure HTTPS proxy
                    subprocess.run(
                        ["networksetup", "-setsecurewebproxy", service, host, str(port)],
                        check=True
                    )
                    
                    # Configure SOCKS proxy
                    subprocess.run(
                        ["networksetup", "-setsocksfirewallproxy", service, host, str(port)],
                        check=True
                    )
                    
                    # Enable proxies
                    subprocess.run(
                        ["networksetup", "-setwebproxystate", service, "on"],
                        check=True
                    )
                    subprocess.run(
                        ["networksetup", "-setsecurewebproxystate", service, "on"],
                        check=True
                    )
                    subprocess.run(
                        ["networksetup", "-setsocksfirewallproxystate", service, "on"],
                        check=True
                    )
                else:
                    # Disable proxies
                    subprocess.run(
                        ["networksetup", "-setwebproxystate", service, "off"],
                        check=True
                    )
                    subprocess.run(
                        ["networksetup", "-setsecurewebproxystate", service, "off"],
                        check=True
                    )
                    subprocess.run(
                        ["networksetup", "-setsocksfirewallproxystate", service, "off"],
                        check=True
                    )
                
                logger.info(f"Successfully configured proxy for service: {service}")
                success = True
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to configure proxy for service {service}: {str(e)}")
        
        if success:
            logger.info("macOS proxy configuration completed successfully")
            return True
        else:
            logger.error("Failed to configure proxy for any network service")
            return False
    except Exception as e:
        log_exception(logger, e, "configure_proxy_macos")
        return False

def configure_proxy_windows(host=DEFAULT_HOST, port=DEFAULT_PORT, enable=True):
    """Configure proxy settings on Windows"""
    try:
        logger.info(f"Configuring Windows proxy settings: {'enable' if enable else 'disable'}")
        
        # Create a temporary PowerShell script to configure the proxy
        ps_script = tempfile.NamedTemporaryFile(suffix='.ps1', delete=False)
        
        if enable:
            ps_script.write(f"""
            # Set proxy settings
            $regKey = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
            
            # Enable proxy
            Set-ItemProperty -Path $regKey -Name ProxyEnable -Value 1
            
            # Set proxy server
            Set-ItemProperty -Path $regKey -Name ProxyServer -Value "{host}:{port}"
            
            # Set bypass list (localhost and 127.0.0.1)
            Set-ItemProperty -Path $regKey -Name ProxyOverride -Value "localhost;127.0.0.1;<local>"
            
            # Configure WinHTTP proxy (for applications that use WinHTTP)
            netsh winhttp set proxy "{host}:{port}"
            
            # Configure environment variables
            [Environment]::SetEnvironmentVariable("HTTP_PROXY", "http://{host}:{port}", "User")
            [Environment]::SetEnvironmentVariable("HTTPS_PROXY", "http://{host}:{port}", "User")
            [Environment]::SetEnvironmentVariable("NO_PROXY", "localhost,127.0.0.1", "User")
            
            Write-Host "Proxy enabled successfully"
            """.encode())
        else:
            ps_script.write(f"""
            # Disable proxy settings
            $regKey = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"
            
            # Disable proxy
            Set-ItemProperty -Path $regKey -Name ProxyEnable -Value 0
            
            # Reset WinHTTP proxy
            netsh winhttp reset proxy
            
            # Remove environment variables
            [Environment]::SetEnvironmentVariable("HTTP_PROXY", $null, "User")
            [Environment]::SetEnvironmentVariable("HTTPS_PROXY", $null, "User")
            [Environment]::SetEnvironmentVariable("NO_PROXY", $null, "User")
            
            Write-Host "Proxy disabled successfully"
            """.encode())
            
        ps_script.close()
        
        # Run the PowerShell script with elevated privileges
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script.name
        ], capture_output=True, text=True)
        
        # Clean up the temporary script
        os.unlink(ps_script.name)
        
        if result.returncode != 0:
            logger.error(f"Failed to configure Windows proxy: {result.stderr}")
            return False
            
        logger.info(f"Windows proxy configuration completed successfully: {'enabled' if enable else 'disabled'}")
        return True
    except Exception as e:
        log_exception(logger, e, "configure_proxy_windows")
        return False

def configure_proxy_linux(host=DEFAULT_HOST, port=DEFAULT_PORT, enable=True):
    """Configure proxy settings on Linux"""
    try:
        logger.info(f"Configuring Linux proxy settings: {'enable' if enable else 'disable'}")
        
        # Determine desktop environment
        desktop_env = os.environ.get('XDG_CURRENT_DESKTOP', '').upper()
        
        # Configure GNOME settings if available
        if 'GNOME' in desktop_env:
            try:
                if enable:
                    # Configure GNOME proxy settings
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy", "mode", "manual"
                    ], check=True)
                    
                    # HTTP proxy
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.http", "host", host
                    ], check=True)
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.http", "port", str(port)
                    ], check=True)
                    
                    # HTTPS proxy
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.https", "host", host
                    ], check=True)
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.https", "port", str(port)
                    ], check=True)
                    
                    # FTP proxy
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.ftp", "host", host
                    ], check=True)
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.ftp", "port", str(port)
                    ], check=True)
                    
                    # SOCKS proxy
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.socks", "host", host
                    ], check=True)
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy.socks", "port", str(port)
                    ], check=True)
                    
                    # Set bypass list
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy", "ignore-hosts", 
                        "['localhost', '127.0.0.0/8', '::1']"
                    ], check=True)
                else:
                    # Disable GNOME proxy
                    subprocess.run([
                        "gsettings", "set", "org.gnome.system.proxy", "mode", "none"
                    ], check=True)
                    
                logger.info("GNOME proxy settings configured successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to configure GNOME proxy settings: {str(e)}")
        
        # Configure KDE settings if available
        elif 'KDE' in desktop_env:
            try:
                # KDE uses kwriteconfig5 to modify settings
                if enable:
                    # Configure KDE proxy settings
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "ProxyType", "1"
                    ], check=True)
                    
                    # HTTP proxy
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "httpProxy", f"{host} {port}"
                    ], check=True)
                    
                    # HTTPS proxy
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "httpsProxy", f"{host} {port}"
                    ], check=True)
                    
                    # FTP proxy
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "ftpProxy", f"{host} {port}"
                    ], check=True)
                    
                    # SOCKS proxy
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "socksProxy", f"{host} {port}"
                    ], check=True)
                    
                    # No proxy list
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "NoProxyFor", "localhost,127.0.0.1"
                    ], check=True)
                else:
                    # Disable KDE proxy
                    subprocess.run([
                        "kwriteconfig5", "--file", "kioslaverc", "--group", "Proxy Settings",
                        "--key", "ProxyType", "0"
                    ], check=True)
                    
                # Reload KDE settings
                subprocess.run(["dbus-send", "--session", "--type=signal", "/KIO/Scheduler", 
                               "org.kde.KIO.Scheduler.reparseSlaveConfiguration", "string:''"], check=True)
                
                logger.info("KDE proxy settings configured successfully")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to configure KDE proxy settings: {str(e)}")
        
        # Configure environment variables in shell configuration files
        shell_config_files = []
        
        # Determine which shell configuration files to modify
        shell = os.environ.get('SHELL', '')
        home = os.path.expanduser('~')
        
        if 'bash' in shell:
            shell_config_files.append(os.path.join(home, '.bashrc'))
        elif 'zsh' in shell:
            shell_config_files.append(os.path.join(home, '.zshrc'))
        else:
            # Default to both
            shell_config_files.append(os.path.join(home, '.bashrc'))
            shell_config_files.append(os.path.join(home, '.zshrc'))
            
        # Also add .profile for login shells
        shell_config_files.append(os.path.join(home, '.profile'))
        
        for config_file in shell_config_files:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r') as f:
                        content = f.read()
                        
                    # Remove existing proxy settings
                    content = re.sub(r'# Private AI Proxy Settings.*?# End Private AI Proxy Settings\n', 
                                    '', content, flags=re.DOTALL)
                    
                    if enable:
                        # Add new proxy settings
                        proxy_settings = f"""
# Private AI Proxy Settings
export http_proxy="{DEFAULT_PROXY_URL}"
export https_proxy="{DEFAULT_PROXY_URL}"
export HTTP_PROXY="{DEFAULT_PROXY_URL}"
export HTTPS_PROXY="{DEFAULT_PROXY_URL}"
export no_proxy="localhost,127.0.0.1"
export NO_PROXY="localhost,127.0.0.1"
# End Private AI Proxy Settings
"""
                        content += proxy_settings
                        
                    with open(config_file, 'w') as f:
                        f.write(content)
                        
                    logger.info(f"Updated shell configuration file: {config_file}")
                except Exception as e:
                    logger.warning(f"Failed to update shell configuration file {config_file}: {str(e)}")
        
        # Configure apt proxy if available
        apt_conf_dir = '/etc/apt/apt.conf.d'
        if os.path.exists(apt_conf_dir):
            try:
                apt_conf_file = os.path.join(apt_conf_dir, '99privateai-proxy')
                
                if enable:
                    # Create apt proxy configuration
                    with open(apt_conf_file, 'w') as f:
                        f.write(f"""Acquire::http::Proxy "{DEFAULT_PROXY_URL}";
Acquire::https::Proxy "{DEFAULT_PROXY_URL}";
""")
                else:
                    # Remove apt proxy configuration
                    if os.path.exists(apt_conf_file):
                        os.remove(apt_conf_file)
                        
                logger.info(f"{'Configured' if enable else 'Removed'} apt proxy settings")
            except Exception as e:
                logger.warning(f"Failed to configure apt proxy: {str(e)}")
                
        logger.info(f"Linux proxy configuration completed")
        return True
    except Exception as e:
        log_exception(logger, e, "configure_proxy_linux")
        return False

def configure_ide_proxy(host=DEFAULT_HOST, port=DEFAULT_PORT, enable=True):
    """Configure proxy settings for common IDEs"""
    try:
        logger.info(f"Configuring IDE proxy settings: {'enable' if enable else 'disable'}")
        
        # VS Code settings
        vscode_settings = []
        
        if platform.system() == "Windows":
            vscode_settings.append(os.path.join(os.environ.get("APPDATA", ""), "Code/User/settings.json"))
        elif platform.system() == "Darwin":
            vscode_settings.append(os.path.expanduser("~/Library/Application Support/Code/User/settings.json"))
        elif platform.system() == "Linux":
            vscode_settings.append(os.path.expanduser("~/.config/Code/User/settings.json"))
            
        for settings_path in vscode_settings:
            if os.path.exists(os.path.dirname(settings_path)):
                try:
                    import json
                    
                    # Create settings file if it doesn't exist
                    if not os.path.exists(settings_path):
                        with open(settings_path, 'w') as f:
                            json.dump({}, f)
                    
                    # Read existing settings
                    with open(settings_path, 'r') as f:
                        try:
                            settings = json.load(f)
                        except json.JSONDecodeError:
                            settings = {}
                        
                    if enable:
                        # Update proxy settings
                        settings["http.proxy"] = f"http://{host}:{port}"
                        settings["http.proxyStrictSSL"] = False
                    else:
                        # Remove proxy settings
                        if "http.proxy" in settings:
                            del settings["http.proxy"]
                        if "http.proxyStrictSSL" in settings:
                            del settings["http.proxyStrictSSL"]
                    
                    # Write updated settings
                    with open(settings_path, 'w') as f:
                        json.dump(settings, f, indent=4)
                        
                    logger.info(f"VS Code settings updated at {settings_path}")
                except Exception as e:
                    logger.warning(f"Failed to update VS Code settings at {settings_path}: {str(e)}")
        
        # JetBrains IDEs
        # JetBrains IDEs store proxy settings in idea.properties or other IDE-specific properties files
        jetbrains_dirs = []
        
        if platform.system() == "Windows":
            jetbrains_base = os.path.join(os.environ.get("USERPROFILE", ""), ".IntelliJIdea")
            # Find all JetBrains config directories
            if os.path.exists(os.path.dirname(jetbrains_base)):
                for d in os.listdir(os.path.dirname(jetbrains_base)):
                    if d.startswith("."):
                        full_path = os.path.join(os.path.dirname(jetbrains_base), d)
                        if os.path.isdir(full_path):
                            jetbrains_dirs.append(full_path)
        elif platform.system() == "Darwin":
            jetbrains_base = os.path.expanduser("~/Library/Preferences/IntelliJIdea")
            # Find all JetBrains config directories
            if os.path.exists(os.path.dirname(jetbrains_base)):
                for d in os.listdir(os.path.dirname(jetbrains_base)):
                    full_path = os.path.join(os.path.dirname(jetbrains_base), d)
                    if os.path.isdir(full_path):
                        jetbrains_dirs.append(full_path)
        elif platform.system() == "Linux":
            jetbrains_base = os.path.expanduser("~/.IntelliJIdea")
            # Find all JetBrains config directories
            if os.path.exists(os.path.dirname(jetbrains_base)):
                for d in os.listdir(os.path.dirname(jetbrains_base)):
                    if d.startswith("."):
                        full_path = os.path.join(os.path.dirname(jetbrains_base), d)
                        if os.path.isdir(full_path):
                            jetbrains_dirs.append(full_path)
        
        for jetbrains_dir in jetbrains_dirs:
            try:
                # Look for idea.properties file
                properties_file = os.path.join(jetbrains_dir, "config", "idea.properties")
                if os.path.exists(properties_file):
                    with open(properties_file, 'r') as f:
                        content = f.read()
                        
                    # Remove existing proxy settings
                    content = re.sub(r'# Private AI Proxy Settings.*?# End Private AI Proxy Settings\n', 
                                    '', content, flags=re.DOTALL)
                    
                    if enable:
                        # Add new proxy settings
                        proxy_settings = f"""
# Private AI Proxy Settings
http.proxyHost={host}
http.proxyPort={port}
https.proxyHost={host}
https.proxyPort={port}
# End Private AI Proxy Settings
"""
                        content += proxy_settings
                        
                    with open(properties_file, 'w') as f:
                        f.write(content)
                        
                    logger.info(f"Updated JetBrains properties file: {properties_file}")
            except Exception as e:
                logger.warning(f"Failed to update JetBrains properties file: {str(e)}")
        
        # Cursor AI settings
        cursor_settings = []
        
        if platform.system() == "Windows":
            cursor_settings.append(os.path.join(os.environ.get("APPDATA", ""), "Cursor/User/settings.json"))
        elif platform.system() == "Darwin":
            cursor_settings.append(os.path.expanduser("~/Library/Application Support/Cursor/User/settings.json"))
        elif platform.system() == "Linux":
            cursor_settings.append(os.path.expanduser("~/.config/Cursor/User/settings.json"))
            
        for settings_path in cursor_settings:
            if os.path.exists(os.path.dirname(settings_path)):
                try:
                    import json
                    
                    # Create settings file if it doesn't exist
                    if not os.path.exists(settings_path):
                        with open(settings_path, 'w') as f:
                            json.dump({}, f)
                    
                    # Read existing settings
                    with open(settings_path, 'r') as f:
                        try:
                            settings = json.load(f)
                        except json.JSONDecodeError:
                            settings = {}
                        
                    if enable:
                        # Update proxy settings
                        settings["http.proxy"] = f"http://{host}:{port}"
                        settings["http.proxyStrictSSL"] = False
                    else:
                        # Remove proxy settings
                        if "http.proxy" in settings:
                            del settings["http.proxy"]
                        if "http.proxyStrictSSL" in settings:
                            del settings["http.proxyStrictSSL"]
                    
                    # Write updated settings
                    with open(settings_path, 'w') as f:
                        json.dump(settings, f, indent=4)
                        
                    logger.info(f"Cursor settings updated at {settings_path}")
                except Exception as e:
                    logger.warning(f"Failed to update Cursor settings at {settings_path}: {str(e)}")
        
        return True
    except Exception as e:
        log_exception(logger, e, "configure_ide_proxy")
        return False

def configure_proxy(host=DEFAULT_HOST, port=DEFAULT_PORT, enable=True):
    """Configure proxy settings based on the current platform"""
    system = platform.system()
    
    if system == "Darwin":
        return configure_proxy_macos(host, port, enable)
    elif system == "Windows":
        return configure_proxy_windows(host, port, enable)
    elif system == "Linux":
        return configure_proxy_linux(host, port, enable)
    else:
        logger.warning(f"Unsupported platform: {system}")
        return False

def print_proxy_instructions():
    """Print instructions for manual proxy configuration"""
    print("\n=== Proxy Configuration Instructions ===\n")
    print(f"Proxy URL: {DEFAULT_PROXY_URL}")
    
    if platform.system() == "Darwin":
        print("\nFor macOS:")
        print("1. Open System Preferences → Network")
        print("2. Select your active network connection")
        print("3. Click 'Advanced' → 'Proxies'")
        print("4. Check 'Web Proxy (HTTP)' and 'Secure Web Proxy (HTTPS)'")
        print(f"5. Enter '{DEFAULT_HOST}' for the server and '{DEFAULT_PORT}' for the port")
        print("6. Click 'OK' and then 'Apply'")
        
    elif platform.system() == "Linux":
        print("\nFor Linux (GNOME):")
        print("1. Open Settings → Network → Network Proxy")
        print("2. Select 'Manual'")
        print(f"3. Enter '{DEFAULT_HOST}' for HTTP and HTTPS Proxy")
        print(f"4. Enter '{DEFAULT_PORT}' for both ports")
        print("5. Click 'Apply'")
        
        print("\nFor Linux (KDE):")
        print("1. Open System Settings → Network → Proxy")
        print("2. Select 'Manual'")
        print(f"3. Enter '{DEFAULT_HOST}' for HTTP and HTTPS Proxy")
        print(f"4. Enter '{DEFAULT_PORT}' for both ports")
        print("5. Click 'Apply'")
        
    elif platform.system() == "Windows":
        print("\nFor Windows:")
        print("1. Open Settings → Network & Internet → Proxy")
        print("2. Enable 'Use a proxy server'")
        print(f"3. Enter '{DEFAULT_HOST}' for the Address")
        print(f"4. Enter '{DEFAULT_PORT}' for the Port")
        print("5. Click 'Save'")
        
    print("\nFor VS Code:")
    print("1. Open settings.json (File → Preferences → Settings → Edit in settings.json)")
    print('2. Add the following lines:')
    print(f'   "http.proxy": "{DEFAULT_PROXY_URL}",')
    print('   "http.proxyStrictSSL": false')
    
    print("\nFor JetBrains IDEs:")
    print("1. Open Settings → Appearance & Behavior → System Settings → HTTP Proxy")
    print("2. Select 'Manual proxy configuration'")
    print(f"3. Enter '{DEFAULT_HOST}' for the Host name")
    print(f"4. Enter '{DEFAULT_PORT}' for the Port number")
    print("5. Click 'Apply'")
    
    print("\nFor Cursor:")
    print("1. Open settings.json (File → Preferences → Settings → Edit in settings.json)")
    print('2. Add the following lines:')
    print(f'   "http.proxy": "{DEFAULT_PROXY_URL}",')
    print('   "http.proxyStrictSSL": false')
    
    print("\nFor environment variables (Linux/macOS):")
    print("Add the following to your shell configuration file (~/.bashrc, ~/.zshrc, etc.):")
    print(f'export http_proxy="{DEFAULT_PROXY_URL}"')
    print(f'export https_proxy="{DEFAULT_PROXY_URL}"')
    print(f'export HTTP_PROXY="{DEFAULT_PROXY_URL}"')
    print(f'export HTTPS_PROXY="{DEFAULT_PROXY_URL}"')
    print('export no_proxy="localhost,127.0.0.1"')
    print('export NO_PROXY="localhost,127.0.0.1"')
    
    print("\n=== End of Instructions ===\n")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Configure system-wide proxy settings for Private AI")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Proxy host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Proxy port (default: {DEFAULT_PORT})")
    parser.add_argument("--enable", action="store_true", help="Enable proxy settings")
    parser.add_argument("--disable", action="store_true", help="Disable proxy settings")
    parser.add_argument("--print-instructions", action="store_true", help="Print manual configuration instructions")
    parser.add_argument("--configure-ides", action="store_true", help="Configure IDE proxy settings only")
    
    args = parser.parse_args()
    
    if args.print_instructions:
        print_proxy_instructions()
    elif args.configure_ides:
        configure_ide_proxy(args.host, args.port, not args.disable)
    elif args.enable or args.disable:
        configure_proxy(args.host, args.port, args.enable)
    else:
        # Default to enable if no action specified
        configure_proxy(args.host, args.port, True)