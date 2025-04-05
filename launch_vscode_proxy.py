#!/usr/bin/env python3
"""
Private AI 🕵️ - VS Code Proxy Launcher

This script provides a unified way to launch VS Code with the Private AI proxy.
It handles certificate management, proxy configuration, and environment setup
across different platforms.

Author: Lance James @ Unit 221B
"""

import os
import sys
import subprocess
import platform
import argparse
import json
import time
import signal
import atexit
from typing import Dict, List, Optional, Tuple

# Import our modules
from certificate_manager import certificate_manager, setup_certificates
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("vscode-launcher", "logs/vscode_launcher.log")

class VSCodeLauncher:
    """Launcher for VS Code with proxy integration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the launcher
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "vscode_launcher_config.json")
        self.config = self._load_config()
        
        # Set platform-specific variables
        self.platform = platform.system()
        self._set_platform_variables()
        
        # Proxy process
        self.proxy_process = None
        
        # Register cleanup handler
        atexit.register(self.cleanup)
    
    def _load_config(self) -> Dict:
        """
        Load configuration from file
        
        Returns:
            dict: Configuration
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log_exception(logger, e, "load_config")
        
        # Return default configuration if file doesn't exist or can't be read
        return {
            "proxy": {
                "port": 8081,
                "host": "127.0.0.1",
                "script": "simple_proxy.py"
            },
            "vscode": {
                "settings": {
                    "http.proxy": "http://127.0.0.1:8080",
                    "http.proxyStrictSSL": False,
                    "http.proxySupport": "override",
                    "github.copilot.advanced": {
                        "proxy": "http://127.0.0.1:8080"
                    }
                }
            },
            "certificates": {
                "auto_install": True,
                "force_regenerate": False
            }
        }
    
    def _save_config(self) -> bool:
        """
        Save configuration to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            log_exception(logger, e, "save_config")
            return False
    
    def _set_platform_variables(self) -> None:
        """Set platform-specific variables"""
        if self.platform == "Darwin":  # macOS
            self.vscode_path = "/Applications/Visual Studio Code.app/Contents/MacOS/Electron"
            self.vscode_settings_dir = os.path.expanduser("~/Library/Application Support/Code/User")
        elif self.platform == "Linux":
            self.vscode_path = "/usr/bin/code"
            self.vscode_settings_dir = os.path.expanduser("~/.config/Code/User")
        elif self.platform == "Windows":
            self.vscode_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs\\Microsoft VS Code\\Code.exe")
            self.vscode_settings_dir = os.path.join(os.environ.get("APPDATA", ""), "Code\\User")
        else:
            logger.error(f"Unsupported platform: {self.platform}")
            self.vscode_path = None
            self.vscode_settings_dir = None
    
    def setup_certificates(self) -> bool:
        """
        Set up certificates for the proxy
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Set up certificates
            force = self.config.get("certificates", {}).get("force_regenerate", False)
            result = setup_certificates(domain=None, force=force)
            
            if not result:
                logger.error("Failed to set up certificates")
                return False
            
            logger.info("Certificates set up successfully")
            return True
        except Exception as e:
            log_exception(logger, e, "setup_certificates")
            return False
    
    def update_vscode_settings(self) -> bool:
        """
        Update VS Code settings for proxy integration
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create settings directory if it doesn't exist
            os.makedirs(self.vscode_settings_dir, exist_ok=True)
            
            # Settings file path
            settings_path = os.path.join(self.vscode_settings_dir, "settings.json")
            
            # Load existing settings if they exist
            settings = {}
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, 'r') as f:
                        settings = json.load(f)
                except:
                    pass
            
            # Update settings with proxy configuration
            vscode_settings = self.config.get("vscode", {}).get("settings", {})
            settings.update(vscode_settings)
            
            # Save settings
            with open(settings_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            logger.info(f"VS Code settings updated at {settings_path}")
            return True
        except Exception as e:
            log_exception(logger, e, "update_vscode_settings")
            return False
    
    def is_port_in_use(self, port: int) -> bool:
        """
        Check if a port is already in use
        
        Args:
            port: Port to check
            
        Returns:
            bool: True if port is in use, False otherwise
        """
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def start_proxy(self) -> bool:
        """
        Start the proxy server
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if proxy is already running
            proxy_port = self.config.get("proxy", {}).get("port", 8080)
            if self.is_port_in_use(proxy_port):
                logger.info(f"Proxy already running on port {proxy_port}, using existing proxy")
                return True
                
            # Kill any existing proxy instances that might be in a bad state
            self._kill_existing_proxy()
            
            # Get proxy configuration
            proxy_config = self.config.get("proxy", {})
            port = proxy_config.get("port", 8080)
            host = proxy_config.get("host", "127.0.0.1")
            script = proxy_config.get("script", "proxy_base.py")
            
            # Get certificate path
            cert_dir = certificate_manager.cert_dir
            
            # Build command
            cmd = [
                "mitmdump",
                "--set", f"confdir={cert_dir}",
                "--set", "ssl_insecure=true",
                "-p", str(port),
                "--listen-host", host,
                "-s", script
            ]
            
            # Start proxy
            logger.info(f"Starting proxy: {' '.join(cmd)}")
            self.proxy_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for proxy to start
            time.sleep(2)
            
            # Check if proxy is running
            if self.proxy_process.poll() is not None:
                stderr = self.proxy_process.stderr.read()
                logger.error(f"Proxy failed to start: {stderr}")
                return False
            
            logger.info(f"Proxy started on {host}:{port}")
            return True
        except Exception as e:
            log_exception(logger, e, "start_proxy")
            return False
    
    def _kill_existing_proxy(self) -> None:
        """Kill any existing proxy instances"""
        try:
            if self.platform == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "mitmdump.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.run(["pkill", "-f", "mitmdump"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            pass
    
    def _kill_existing_vscode(self) -> None:
        """Kill any existing VS Code instances"""
        try:
            if self.platform == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "Code.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif self.platform == "Darwin":
                subprocess.run(["pkill", "-f", "Visual Studio Code"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.run(["pkill", "-f", "code"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            pass
    
    def launch_vscode(self, workspace_path: str = None, kill_existing: bool = True) -> bool:
        """
        Launch VS Code with proxy integration
        
        Args:
            workspace_path: Path to workspace to open (optional)
            kill_existing: Whether to kill existing VS Code instances (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Kill existing VS Code instances if requested
            if kill_existing:
                self._kill_existing_vscode()
            
            # Get certificate path
            cert_path = certificate_manager.cert_pem
            
            # Set environment variables
            env = os.environ.copy()
            env["NODE_EXTRA_CA_CERTS"] = cert_path
            env["HTTP_PROXY"] = f"http://{self.config['proxy']['host']}:{self.config['proxy']['port']}"
            env["HTTPS_PROXY"] = f"http://{self.config['proxy']['host']}:{self.config['proxy']['port']}"
            env["NO_PROXY"] = "localhost,127.0.0.1"
            
            # Build command
            cmd = [self.vscode_path]
            if workspace_path:
                cmd.append(workspace_path)
            
            # Launch VS Code
            logger.info(f"Launching VS Code: {' '.join(cmd)}")
            logger.info(f"Environment variables: NODE_EXTRA_CA_CERTS={env['NODE_EXTRA_CA_CERTS']}, HTTP_PROXY={env['HTTP_PROXY']}")
            
            vscode_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for VS Code to start
            time.sleep(2)
            
            # Check if VS Code is running
            if vscode_process.poll() is not None:
                stderr = vscode_process.stderr.read()
                logger.error(f"VS Code failed to start: {stderr}")
                return False
            
            logger.info("VS Code launched successfully")
            return True
        except Exception as e:
            log_exception(logger, e, "launch_vscode")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources"""
        # Stop proxy
        if self.proxy_process:
            try:
                self.proxy_process.terminate()
                self.proxy_process.wait(timeout=5)
            except:
                if self.proxy_process.poll() is None:
                    self.proxy_process.kill()
            
            logger.info("Proxy stopped")
    
    def run(self, workspace_path: str = None, kill_existing: bool = True) -> bool:
        """
        Run the launcher
        
        Args:
            workspace_path: Path to workspace to open (optional)
            kill_existing: Whether to kill existing VS Code instances (default: True)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Set up certificates
        if self.config.get("certificates", {}).get("auto_install", True):
            if not self.setup_certificates():
                return False
        
        # Update VS Code settings
        if not self.update_vscode_settings():
            return False
        
        # Start proxy
        if not self.start_proxy():
            return False
        
        # Launch VS Code
        if not self.launch_vscode(workspace_path, kill_existing):
            self.cleanup()
            return False
        
        return True

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Launch VS Code with Private AI proxy integration")
    parser.add_argument("--workspace", "-w", help="Path to workspace to open")
    parser.add_argument("--keep-running", "-k", action="store_true", help="Keep existing VS Code instances running")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    args = parser.parse_args()
    
    # Create launcher
    launcher = VSCodeLauncher(args.config)
    
    # Run launcher
    result = launcher.run(
        workspace_path=args.workspace,
        kill_existing=not args.keep_running
    )
    
    if not result:
        logger.error("Failed to launch VS Code with proxy integration")
        sys.exit(1)
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        launcher.cleanup()

if __name__ == "__main__":
    main()