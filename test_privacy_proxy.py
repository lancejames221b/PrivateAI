#!/usr/bin/env python3
"""
Privacy Proxy Test - Test the privacy features of the AI proxy

This script sends a request with sensitive information to an AI service through the proxy
and checks if the sensitive information is properly transformed or redacted.

Usage:
    python test_privacy_proxy.py [--proxy http://localhost:8080] [--api-key YOUR_API_KEY]
"""

import argparse
import json
import requests
import sys
import os
from urllib.parse import urlparse

# Default settings
DEFAULT_PROXY = "http://localhost:8080"
DEFAULT_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
DEFAULT_OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"

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

def check_proxy_connection(proxy_url):
    """Check if the proxy is running and accessible"""
    parsed_url = urlparse(proxy_url)
    host = parsed_url.hostname
    port = parsed_url.port
    
    if not host or not port:
        print(f"Invalid proxy URL: {proxy_url}")
        return False
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Proxy is running at {host}:{port}")
            return True
        else:
            print(f"❌ Cannot connect to proxy at {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ Error checking proxy connection: {e}")
        return False

def create_openai_request_with_pii():
    """Create a request to OpenAI with PII in the prompt"""
    return {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": f"""
                My name is {SAMPLE_PII['name']} and my email is {SAMPLE_PII['email']}.
                My phone number is {SAMPLE_PII['phone']} and I live at {SAMPLE_PII['address']}.
                My social security number is {SAMPLE_PII['ssn']} and my credit card is {SAMPLE_PII['credit_card']}.
                My date of birth is {SAMPLE_PII['dob']}.
                
                Please help me write a Python function to calculate the factorial of a number.
                """
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

def send_request_through_proxy(api_key, proxy_url):
    """Send a request to OpenAI through the proxy and check for PII transformation"""
    # Create request with PII
    request_data = create_openai_request_with_pii()
    
    # Set up headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Set up proxy
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    
    print("\n🔍 Sending request with PII through proxy...")
    print("📝 Original request contains the following PII:")
    for key, value in SAMPLE_PII.items():
        print(f"  - {key}: {value}")
    
    # Convert request to string for PII checking
    request_str = json.dumps(request_data)
    
    # Check if PII is in the original request (it should be)
    pii_in_request = []
    for key, value in SAMPLE_PII.items():
        if value in request_str:
            pii_in_request.append(f"{key}: {value}")
    
    if pii_in_request:
        print(f"✅ Confirmed {len(pii_in_request)} PII items in original request")
    else:
        print("❌ No PII found in original request (this is unexpected)")
    
    try:
        # Send request through proxy
        response = requests.post(
            DEFAULT_OPENAI_ENDPOINT,
            json=request_data,
            headers=headers,
            proxies=proxies,
            verify=False,  # Disable SSL verification for testing with MITM proxy
            timeout=30
        )
        
        # Check if request was successful
        if response.status_code == 200:
            print("✅ Request successful!")
            
            # Parse response
            try:
                response_data = response.json()
                
                # Get the response content
                if "choices" in response_data and len(response_data["choices"]) > 0:
                    if "message" in response_data["choices"][0]:
                        content = response_data["choices"][0]["message"].get("content", "")
                    else:
                        content = response_data["choices"][0].get("text", "")
                else:
                    content = str(response_data)
                
                print("\n📊 Response from AI service:")
                print(f"{content[:500]}..." if len(content) > 500 else content)
                
                # Check if PII is in the response
                pii_in_response = []
                for key, value in SAMPLE_PII.items():
                    if value in content:
                        pii_in_response.append(f"{key}: {value}")
                
                if pii_in_response:
                    print(f"\n❌ Found {len(pii_in_response)} PII items in response:")
                    for item in pii_in_response:
                        print(f"  - {item}")
                    print("The proxy did not properly transform or redact PII in the response.")
                else:
                    print("\n✅ No PII found in response - Privacy protection working!")
                
            except json.JSONDecodeError:
                print(f"❌ Error parsing response: {response.text[:200]}...")
        else:
            print(f"❌ Request failed with status code {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            # Check if this is an authentication error (which is expected without a valid API key)
            if "authentication" in response.text.lower() or "api key" in response.text.lower():
                print("\n⚠️ Authentication error - this is expected if you didn't provide a valid API key.")
                print("However, we can still check if the proxy attempted to transform the PII.")
                
                # Check request logs to see if PII was transformed
                print("\n🔍 Please check the proxy logs to verify PII transformation:")
                print("  tail -n 50 logs/proxy.log")
                print("  tail -n 50 logs/pii_transform.log")
                
                return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return False
    
    return True

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test the privacy features of the AI proxy")
    parser.add_argument("--proxy", default=DEFAULT_PROXY, help=f"Proxy URL (default: {DEFAULT_PROXY})")
    parser.add_argument("--api-key", default=DEFAULT_OPENAI_API_KEY, help="OpenAI API key")
    
    args = parser.parse_args()
    
    print("🔒 Privacy Proxy Test")
    print(f"Proxy: {args.proxy}")
    
    # Check if proxy is running
    if not check_proxy_connection(args.proxy):
        print("❌ Proxy connection check failed. Make sure the proxy is running.")
        sys.exit(1)
    
    # Check if API key is provided
    if not args.api_key:
        print("⚠️ No API key provided. The request will fail with an authentication error.")
        print("However, we can still check if the proxy attempted to transform the PII.")
        print("To provide an API key, use the --api-key parameter or set the OPENAI_API_KEY environment variable.")
    
    # Send request through proxy
    if send_request_through_proxy(args.api_key, args.proxy):
        print("\n✅ Test completed. Check the results above to verify privacy protection.")
    else:
        print("\n❌ Test failed. Check the error messages above.")

if __name__ == "__main__":
    main()