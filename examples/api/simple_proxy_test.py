#!/usr/bin/env python3
"""
Simple Proxy Test Script

This script tests the AI Security Proxy by making a direct request to the OpenAI API
through the proxy. It doesn't depend on spaCy or other complex dependencies.
"""

import os
import sys
import argparse
import json
import requests
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simple-proxy-test")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Test the AI Security Proxy")
    parser.add_argument("--api-key", default=os.environ.get('OPENAI_API_KEY', ''),
                        help="OpenAI API key (defaults to OPENAI_API_KEY env var)")
    parser.add_argument("--proxy", default="http://localhost:8080",
                        help="Proxy URL (default: http://localhost:8080)")
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt to send to OpenAI (default: use built-in prompt with PII)")
    return parser.parse_args()

def get_test_prompt_with_pii():
    """Create a test prompt with various types of sensitive information embedded in it"""
    return """
    Hello! I need assistance with setting up a new development environment.

    Here are my details:
    - Name: Alex Johnson
    - Email: alex.johnson@acmecorp.com
    - API Key: sk_live_51MbGLjHR4KmVQkGj3KHUiB7ct8PJu48UA5cE2
    - Credit Card: 4111-3456-7890-1234
    - Internal project: PROMETHEUS
    - Server details: IP 10.142.56.78 with SSH access (password: P@ssw0rd123!)

    Please advise on best practices for setting up this environment securely.
    """

def make_openai_api_call(prompt, api_key, proxy_url):
    """
    Make a real API call to OpenAI through the proxy
    
    Args:
        prompt: The prompt to send
        api_key: OpenAI API key 
        proxy_url: URL of the proxy
    
    Returns:
        The API response text
    """
    if not api_key:
        logger.error("OpenAI API key is required.")
        sys.exit(1)
    
    # Set up proxy
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
    logger.info(f"Using proxy: {proxy_url}")
    
    # Set up API call
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # OpenAI API request data
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        # Make the API call through the proxy
        logger.info("Making API call to OpenAI...")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            proxies=proxies,
            verify=False  # Skip SSL verification for testing
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"API call failed with status {response.status_code}: {response.text}")
            return f"Error: API call failed with status {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error making API call: {str(e)}")
        return f"Error: {str(e)}"

def main():
    args = parse_arguments()
    
    # Use default prompt if none provided
    prompt = args.prompt if args.prompt else get_test_prompt_with_pii()
    
    print("\n" + "="*80)
    print("SIMPLE PROXY TEST")
    print("="*80)
    
    print("\nORIGINAL PROMPT (with sensitive information):")
    print(prompt)
    print("\n" + "-"*80)
    
    # Make the API call through the proxy
    print(f"\nMaking API call through proxy at {args.proxy}...")
    api_response = make_openai_api_call(prompt, args.api_key, args.proxy)
    
    print("\nAPI RESPONSE:")
    print(api_response)
    print("\n" + "-"*80)
    
    print("\nTest complete!")

if __name__ == "__main__":
    # Disable SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main() 