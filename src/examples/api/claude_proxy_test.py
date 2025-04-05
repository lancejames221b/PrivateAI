#!/usr/bin/env python3
"""
Claude Proxy Test - This script tests how the Privacy AI Proxy handles sensitive information
when making requests to Claude Sonnet 3.7 API.
"""

import os
import sys
import argparse
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_PROXY = "http://localhost:8080"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-3-sonnet-20240229"
API_URL = "https://api.anthropic.com/v1/messages"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Test the Privacy AI Proxy with Claude Sonnet")
    parser.add_argument("--proxy", default=DEFAULT_PROXY,
                        help=f"HTTP proxy URL (default: {DEFAULT_PROXY})")
    parser.add_argument("--api-key", default=ANTHROPIC_API_KEY,
                        help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)")
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt to send to Claude (default: use built-in prompt with PII)")
    parser.add_argument("--model", default=CLAUDE_MODEL,
                        help=f"Claude model to use (default: {CLAUDE_MODEL})")
    parser.add_argument("--no-proxy", action="store_true",
                        help="Bypass the proxy and connect directly (for comparison)")
    parser.add_argument("--agentic", action="store_true",
                        help="Use a prompt that tests agentic capabilities")
    return parser.parse_args()

def get_test_prompt_with_pii():
    """
    Create a test prompt with various types of sensitive information embedded in it
    """
    return """
    Hello Claude, I'm testing a privacy protection proxy. I want you to analyze this message and identify what sensitive information it contains, but don't repeat the sensitive information in your response.
    
    My name is John Smith and I live at 123 Main Street, New York, NY 10001. 
    My phone number is 212-555-1234 and my email is john.smith@example.com.
    My credit card number is 4111-1111-1111-1111 with expiration 12/25 and CVV 123.
    My social security number is 123-45-6789.
    My API key is sk_live_51NZw66BLxRpYtGHkqtBsgDfEPXI2v3olWjcf9bAFATAP9NCr.
    My database password is Sup3rS3cr3t!2023.
    
    Please analyze what happened to this information as it passed through the proxy, and explain what types of sensitive data you can identify in what I sent, without repeating the actual sensitive values.
    """

def get_agentic_test_prompt():
    """
    Create a test prompt that triggers agentic capabilities, including file manipulation
    """
    return """
    Hello Claude, create a Python script that does the following:
    
    1. Creates a simple web server that listens on port 8000
    2. Accepts POST requests with JSON data
    3. The JSON should contain a "name" field and an "email" field
    4. Stores the data in a SQLite database
    5. Returns the stored data when accessed via GET
    
    My name is Sarah Johnson and my email is sarah.j@example.com.
    If you need to use example data, please use this information above.
    
    Additionally, my AWS access key is AKIAIOSFODNN7EXAMPLE and my secret key is wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY.
    
    Can you also explain how you would deploy this application to AWS using these credentials?
    """

def send_claude_request(prompt, api_key, model, proxy_url=None):
    """
    Send a request to Claude through the specified proxy
    """
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": model,
        "max_tokens": 2000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    proxies = None
    if proxy_url:
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        print(f"Using proxy: {proxy_url}")
    else:
        print("Connecting directly (no proxy)")
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data,
            proxies=proxies,
            verify=True
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Error sending request: {str(e)}")
        return None

def main():
    args = parse_arguments()
    
    if not args.api_key:
        print("Error: No Anthropic API key provided.")
        print("Set the ANTHROPIC_API_KEY environment variable or use the --api-key option.")
        sys.exit(1)
    
    # Determine which prompt to use
    if args.prompt:
        prompt = args.prompt
        print("Using custom prompt")
    elif args.agentic:
        prompt = get_agentic_test_prompt()
        print("Using agentic test prompt")
    else:
        prompt = get_test_prompt_with_pii()
        print("Using default PII test prompt")
    
    # Configure proxy
    proxy_url = None if args.no_proxy else args.proxy
    
    # Send request
    print(f"Sending request to Claude {args.model}...")
    response = send_claude_request(prompt, args.api_key, args.model, proxy_url)
    
    if response:
        print("\n" + "="*50)
        print("CLAUDE RESPONSE:")
        print("="*50)
        
        content = response["content"][0]["text"]
        print(content)
        
        print("\n" + "="*50)
        print("RESPONSE METADATA:")
        print("="*50)
        print(f"Model: {response.get('model')}")
        print(f"Usage: {json.dumps(response.get('usage', {}), indent=2)}")
        
        # Save the response to a file for analysis
        with open("claude_response.json", "w") as f:
            json.dump(response, f, indent=2)
        print(f"Full response saved to claude_response.json")

if __name__ == "__main__":
    main() 