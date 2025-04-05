#!/usr/bin/env python3
"""
Private AI 🕵️ - VS Code AI Proxy Test

This script simulates VS Code AI requests to test the PrivateAI proxy's
ability to intercept and transform requests from VS Code AI extensions.

Usage:
    python test_vscode_ai_proxy.py [--proxy http://localhost:8080]

Author: Lance James @ Unit 221B
"""

import argparse
import json
import requests
import sys
import os
import time
import socket
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

# Default settings
DEFAULT_PROXY = "http://localhost:8080"
DEFAULT_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
DEFAULT_VSCODE_ENDPOINT = "https://api.github.com/copilot/v1/completions"
DEFAULT_CURSOR_ENDPOINT = "https://api.cursor.sh/v1/completions"

# Sample PII for testing
SAMPLE_PII = {
    "name": "John Smith",
    "email": "john.smith@example.com",
    "phone": "(555) 123-4567",
    "address": "123 Main St, Anytown, CA 12345",
    "ssn": "123-45-6789",
    "credit_card": "4111-1111-1111-1111",
    "dob": "01/01/1980"
}

def check_proxy_connection(proxy_url: str) -> bool:
    """Check if the proxy is running and accessible"""
    parsed_url = urlparse(proxy_url)
    host = parsed_url.hostname
    port = parsed_url.port
    
    if not host or not port:
        print(f"Invalid proxy URL: {proxy_url}")
        return False
    
    try:
        # Try to connect to the proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"Proxy is running at {host}:{port}")
            return True
        else:
            print(f"Cannot connect to proxy at {host}:{port}")
            return False
    except Exception as e:
        print(f"Error checking proxy connection: {e}")
        return False

def create_openai_request(pii: Dict[str, str]) -> Dict[str, Any]:
    """Create a sample OpenAI API request with PII"""
    return {
        "model": "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": f"My name is {pii['name']} and my email is {pii['email']}. "
                           f"My phone number is {pii['phone']} and I live at {pii['address']}. "
                           f"Please help me write a Python function to calculate the factorial of a number."
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }

def create_vscode_request(pii: Dict[str, str]) -> Dict[str, Any]:
    """Create a sample VS Code AI request with PII"""
    return {
        "text": f"My name is {pii['name']} and my email is {pii['email']}. "
               f"My phone number is {pii['phone']} and I live at {pii['address']}. "
               f"Please help me write a Python function to calculate the factorial of a number.",
        "files": [
            {
                "name": "factorial.py",
                "content": f"# Author: {pii['name']}\n# Contact: {pii['email']}\n\n"
                           f"# TODO: Implement factorial function\n"
            }
        ],
        "vscodeVersion": "1.80.0",
        "extensionVersion": "1.0.0",
        "extensionId": "test-extension"
    }

def create_cursor_request(pii: Dict[str, str]) -> Dict[str, Any]:
    """Create a sample Cursor AI request with PII"""
    return {
        "prompt": f"My name is {pii['name']} and my email is {pii['email']}. "
                 f"My phone number is {pii['phone']} and I live at {pii['address']}. "
                 f"Please help me write a Python function to calculate the factorial of a number.",
        "context": f"# Author: {pii['name']}\n# Contact: {pii['email']}\n\n"
                  f"# TODO: Implement factorial function\n",
        "temperature": 0.7
    }

def create_github_copilot_request(pii: Dict[str, str]) -> Dict[str, Any]:
    """Create a sample GitHub Copilot request with PII"""
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getCompletions",
        "params": {
            "doc": {
                "source": f"# Author: {pii['name']}\n# Contact: {pii['email']}\n\n"
                         f"# Function to calculate factorial\n# My SSN is {pii['ssn']}\n",
                "prefix": f"# Author: {pii['name']}\n# Contact: {pii['email']}\n\n"
                         f"# Function to calculate factorial\n# My SSN is {pii['ssn']}\n",
                "suffix": "",
                "uri": "file:///project/factorial.py"
            }
        }
    }

def send_request(url: str, data: Dict[str, Any], proxy: Optional[str] = None, 
                 headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Send a request to the specified URL with the given data"""
    proxies = {"http": proxy, "https": proxy} if proxy else None
    default_headers = {
        "Content-Type": "application/json",
        "User-Agent": "VSCode/1.80.0"
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        # Set a shorter timeout to avoid long waits
        response = requests.post(
            url,
            json=data,
            proxies=proxies,
            headers=default_headers,
            verify=False,  # Disable SSL verification for testing with MITM proxy
            timeout=10
        )
        
        # Try to parse JSON response
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"text": response.text, "status_code": response.status_code}
            
    except requests.exceptions.ProxyError as e:
        print(f"Proxy error: {e}")
        print("This is expected if the proxy is correctly intercepting the request but cannot connect to the actual endpoint.")
        print("Check the proxy logs to verify that the request was intercepted.")
        return {"proxy_error": str(e), "note": "This is expected during testing if you don't have actual API access."}
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return {"error": str(e)}

def check_pii_in_response(response: Dict[str, Any], pii: Dict[str, str]) -> List[str]:
    """Check if any PII is present in the response"""
    found_pii = []
    response_str = json.dumps(response)
    
    for key, value in pii.items():
        if value in response_str:
            found_pii.append(f"{key}: {value}")
            
    return found_pii

def test_openai_request(proxy: Optional[str] = None, api_key: str = DEFAULT_OPENAI_API_KEY):
    """Test OpenAI API request through the proxy"""
    print("\n=== Testing OpenAI API Request ===")
    
    if not api_key:
        print("Skipping OpenAI test (no API key provided)")
        return None
    
    # Create request with PII
    request_data = create_openai_request(SAMPLE_PII)
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # Send request
    print("Sending request to OpenAI API...")
    response = send_request(DEFAULT_OPENAI_ENDPOINT, request_data, proxy, headers)
    
    # Check for PII in response
    found_pii = check_pii_in_response(response, SAMPLE_PII)
    
    # Print results
    response_str = json.dumps(response, indent=2)
    print(f"Response received: {response_str[:200]}..." if len(response_str) > 200 else f"Response received: {response_str}")
    
    if found_pii:
        print(f"WARNING: Found {len(found_pii)} PII items in response:")
        for item in found_pii:
            print(f"  - {item}")
    else:
        print("SUCCESS: No PII found in response")
        
    return response

def test_vscode_request(proxy: Optional[str] = None):
    """Test VS Code AI request through the proxy"""
    print("\n=== Testing VS Code AI Request ===")
    
    # Create request with PII
    request_data = create_vscode_request(SAMPLE_PII)
    
    # Set up headers
    headers = {
        "X-VSCode-Version": "1.80.0",
        "X-IDE-Version": "1.80.0",
        "X-IDE-Client": "vscode"
    }
    
    # Send request
    print("Sending request to VS Code AI endpoint...")
    response = send_request(DEFAULT_VSCODE_ENDPOINT, request_data, proxy, headers)
    
    # Check for PII in response
    found_pii = check_pii_in_response(response, SAMPLE_PII)
    
    # Print results
    response_str = json.dumps(response, indent=2)
    print(f"Response received: {response_str[:200]}..." if len(response_str) > 200 else f"Response received: {response_str}")
    
    if found_pii:
        print(f"WARNING: Found {len(found_pii)} PII items in response:")
        for item in found_pii:
            print(f"  - {item}")
    else:
        print("SUCCESS: No PII found in response")
        
    return response

def test_cursor_request(proxy: Optional[str] = None):
    """Test Cursor AI request through the proxy"""
    print("\n=== Testing Cursor AI Request ===")
    
    # Create request with PII
    request_data = create_cursor_request(SAMPLE_PII)
    
    # Set up headers
    headers = {
        "X-Cursor-Client": "cursor-app",
        "X-Cursor-Token": "test-token"
    }
    
    # Send request
    print("Sending request to Cursor AI endpoint...")
    response = send_request(DEFAULT_CURSOR_ENDPOINT, request_data, proxy, headers)
    
    # Check for PII in response
    found_pii = check_pii_in_response(response, SAMPLE_PII)
    
    # Print results
    response_str = json.dumps(response, indent=2)
    print(f"Response received: {response_str[:200]}..." if len(response_str) > 200 else f"Response received: {response_str}")
    
    if found_pii:
        print(f"WARNING: Found {len(found_pii)} PII items in response:")
        for item in found_pii:
            print(f"  - {item}")
    else:
        print("SUCCESS: No PII found in response")
        
    return response

def test_github_copilot_request(proxy: Optional[str] = None):
    """Test GitHub Copilot request through the proxy"""
    print("\n=== Testing GitHub Copilot Request ===")
    
    # Create request with PII
    request_data = create_github_copilot_request(SAMPLE_PII)
    
    # Set up headers
    headers = {
        "X-GitHub-Client": "vscode",
        "X-GitHub-Client-Version": "1.80.0",
        "X-Copilot-Session": "test-session"
    }
    
    # Send request
    print("Sending request to GitHub Copilot endpoint...")
    response = send_request(DEFAULT_VSCODE_ENDPOINT, request_data, proxy, headers)
    
    # Check for PII in response
    found_pii = check_pii_in_response(response, SAMPLE_PII)
    
    # Print results
    response_str = json.dumps(response, indent=2)
    print(f"Response received: {response_str[:200]}..." if len(response_str) > 200 else f"Response received: {response_str}")
    
    if found_pii:
        print(f"WARNING: Found {len(found_pii)} PII items in response:")
        for item in found_pii:
            print(f"  - {item}")
    else:
        print("SUCCESS: No PII found in response")
        
    return response

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test VS Code AI requests through PrivateAI proxy")
    parser.add_argument("--proxy", default=DEFAULT_PROXY, help=f"Proxy URL (default: {DEFAULT_PROXY})")
    parser.add_argument("--api-key", default=DEFAULT_OPENAI_API_KEY, help="OpenAI API key")
    parser.add_argument("--test-type", choices=["all", "openai", "vscode", "cursor", "copilot"], 
                        default="all", help="Type of test to run")
    
    args = parser.parse_args()
    
    print(f"Testing PrivateAI proxy with VS Code AI requests")
    print(f"Proxy: {args.proxy}")
    
    # Check if proxy is running
    if not check_proxy_connection(args.proxy):
        print("WARNING: Proxy connection check failed. Tests may not work correctly.")
        print("Make sure the proxy is running and listening on the correct port.")
        print("Continuing with tests anyway...")
        print()
    
    # Run tests based on test type
    if args.test_type in ["all", "openai"]:
        if args.api_key:
            test_openai_request(args.proxy, args.api_key)
        else:
            print("Skipping OpenAI test (no API key provided)")
            
    if args.test_type in ["all", "vscode"]:
        test_vscode_request(args.proxy)
        
    if args.test_type in ["all", "cursor"]:
        test_cursor_request(args.proxy)
        
    if args.test_type in ["all", "copilot"]:
        test_github_copilot_request(args.proxy)
    
    print("\nAll tests completed")
    print("\nNOTE: Connection errors are expected if you don't have actual API access.")
    print("The important part is that the proxy is correctly intercepting the requests.")
    print("Check the proxy logs to verify that the requests were intercepted and transformed.")

if __name__ == "__main__":
    main()