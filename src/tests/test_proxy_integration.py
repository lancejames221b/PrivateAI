#!/usr/bin/env python3
"""
Private AI 🕵️ - Proxy Integration Test

This script tests the integration between VS Code, GitHub Copilot, and the
Private AI proxy. It verifies that the proxy is correctly intercepting and
transforming requests and responses.

Author: Lance James @ Unit 221B
"""

import os
import sys
import json
import argparse
import subprocess
import time
import requests
from typing import Dict, List, Any, Optional, Tuple

# Import our modules
from enhanced_logger import get_logger, log_exception

# Initialize logger
logger = get_logger("proxy-test", "logs/proxy_test.log")

class ProxyTester:
    """Tester for proxy integration"""
    
    def __init__(self, proxy_url: str = "http://127.0.0.1:8080"):
        """
        Initialize the tester
        
        Args:
            proxy_url: Proxy URL (default: http://127.0.0.1:8080)
        """
        self.proxy_url = proxy_url
        self.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # Certificate path
        self.cert_path = os.path.expanduser("~/.private-ai/private-ai-ca-cert.pem")
        
        logger.info(f"Proxy tester initialized with proxy URL: {proxy_url}")
    
    def test_proxy_connection(self) -> bool:
        """
        Test proxy connection
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Test connection to proxy
            response = requests.get(
                "http://example.com",
                proxies=self.proxies,
                verify=False  # Disable SSL verification for testing
            )
            
            # Check if proxy headers are present
            proxy_headers = [h for h in response.headers if "proxy" in h.lower()]
            
            if proxy_headers:
                logger.info(f"Proxy connection successful: {proxy_headers}")
                return True
            else:
                logger.info("Proxy connection successful, but no proxy headers found")
                return True
        except Exception as e:
            log_exception(logger, e, "test_proxy_connection")
            return False
    
    def test_copilot_request(self) -> bool:
        """
        Test GitHub Copilot request
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Mock Copilot request
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer mock_token",
                "GitHub-Authentication-Bearer": "mock_token",
                "User-Agent": "GitHub-Copilot/1.0"
            }
            
            data = {
                "prompt": "def calculate_sum(a, b):",
                "max_tokens": 100,
                "temperature": 0.7,
                "top_p": 1.0,
                "n": 1,
                "stream": False,
                "logprobs": None,
                "stop": ["\n\n"]
            }
            
            # Send request through proxy
            response = requests.post(
                "https://api.githubcopilot.com/v1/engines/copilot-codex/completions",
                json=data,
                headers=headers,
                proxies=self.proxies,
                verify=False  # Disable SSL verification for testing
            )
            
            # Check response
            logger.info(f"Copilot request status: {response.status_code}")
            
            # Note: This will likely fail with a 401 or 404 since we're using mock credentials
            # But it should still go through the proxy
            return response.status_code < 500
        except Exception as e:
            log_exception(logger, e, "test_copilot_request")
            return False
    
    def test_certificate_installation(self) -> bool:
        """
        Test certificate installation
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if certificate file exists
            if not os.path.exists(self.cert_path):
                logger.error(f"Certificate file not found: {self.cert_path}")
                return False
            
            # Check certificate validity
            result = subprocess.run(
                ["openssl", "x509", "-in", self.cert_path, "-noout", "-text"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # Check if certificate is valid
            if "Private AI" in result.stdout:
                logger.info("Certificate is valid")
                return True
            else:
                logger.warning("Certificate exists but may not be valid")
                return False
        except Exception as e:
            log_exception(logger, e, "test_certificate_installation")
            return False
    
    def test_vscode_settings(self) -> bool:
        """
        Test VS Code settings
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine settings path based on platform
            if sys.platform == "darwin":  # macOS
                settings_path = os.path.expanduser("~/Library/Application Support/Code/User/settings.json")
            elif sys.platform == "linux":
                settings_path = os.path.expanduser("~/.config/Code/User/settings.json")
            elif sys.platform == "win32":
                settings_path = os.path.join(os.environ.get("APPDATA", ""), "Code\\User\\settings.json")
            else:
                logger.error(f"Unsupported platform: {sys.platform}")
                return False
            
            # Check if settings file exists
            if not os.path.exists(settings_path):
                logger.error(f"VS Code settings file not found: {settings_path}")
                return False
            
            # Load settings
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            
            # Check proxy settings
            if "http.proxy" in settings and "github.copilot.advanced" in settings:
                logger.info("VS Code settings are configured for proxy")
                return True
            else:
                logger.warning("VS Code settings may not be properly configured for proxy")
                return False
        except Exception as e:
            log_exception(logger, e, "test_vscode_settings")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        Run all tests
        
        Returns:
            dict: Test results
        """
        results = {
            "proxy_connection": self.test_proxy_connection(),
            "certificate_installation": self.test_certificate_installation(),
            "vscode_settings": self.test_vscode_settings(),
            "copilot_request": self.test_copilot_request()
        }
        
        # Log results
        logger.info(f"Test results: {json.dumps(results, indent=2)}")
        
        return results

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test proxy integration")
    parser.add_argument("--proxy", "-p", default="http://127.0.0.1:8080", help="Proxy URL")
    args = parser.parse_args()
    
    # Create tester
    tester = ProxyTester(args.proxy)
    
    # Run tests
    results = tester.run_all_tests()
    
    # Print results
    print("\nProxy Integration Test Results:")
    print("==============================")
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test}: {status}")
    
    # Exit with success if all tests passed
    if all(results.values()):
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed. Check the logs for more information.")
        sys.exit(1)

if __name__ == "__main__":
    main()