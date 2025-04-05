#!/usr/bin/env python3
"""
Real AI API Demo with Privacy Proxy

This script demonstrates using the Privacy Assistant with an actual OpenAI API call
going through our privacy-protecting proxy.
"""

import os
import json
import logging
import requests
import argparse
from datetime import datetime
from privacy_assistant import process_input, process_output, get_privacy_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("real-ai-demo")

def make_openai_api_call(prompt, api_key=None, proxy_url=None):
    """
    Make a real API call to OpenAI through our proxy
    
    Args:
        prompt: The sanitized prompt to send
        api_key: OpenAI API key (will use env var if not provided)
        proxy_url: URL of the proxy (default: http://localhost:8080)
    
    Returns:
        The API response text
    """
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it as an argument.")
    
    # Set up proxy if provided
    proxies = None
    if proxy_url:
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
            proxies=proxies
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

def run_demo(prompt=None, api_key=None, proxy_url="http://localhost:8080"):
    """Run the complete private AI integration demo with a real API call"""
    print("\n=== PRIVATE AI REAL API DEMONSTRATION ===\n")
    
    # Use default prompt if none provided
    if not prompt:
        prompt = """
I need assistance with setting up a new development environment.

Here are my details:
- Name: Alex Johnson
- Email: alex.johnson@acmecorp.com
- API Key: sk_live_51MbGLjHR4KmVQkGj3KHUiB7ct8PJu48UA5cE2
- Credit Card: 4111-3456-7890-1234
- Internal project: PROMETHEUS
- Server details: IP 10.142.56.78 with SSH access (password: P@ssw0rd123!)

Please advise on best practices for setting up this environment securely.
"""
    
    print("ORIGINAL PROMPT (with sensitive information):")
    print(prompt)
    print("\n" + "-"*80)
    
    # Step 1: Process the input to remove sensitive information
    sanitized_prompt, metrics, transformations = process_input(prompt)
    
    print("\nPRIVACY METRICS:")
    print(f"  - High sensitivity items: {metrics['sensitivity_high']}")
    print(f"  - Medium sensitivity items: {metrics['sensitivity_medium']}")
    print(f"  - Low sensitivity items: {metrics['sensitivity_low']}")
    
    print("\nSANITIZED PROMPT (sent to AI model):")
    print(sanitized_prompt)
    print("\n" + "-"*80)
    
    # Log the transformations (in a real scenario, keep this private!)
    print("\nTRANSFORMATIONS (for demonstration only - would be kept private):")
    for t in transformations:
        print(f"  - '{t['original']}' → '{t['replacement']}' ({t['entity_type']} - {t['sensitivity']})")
    print("\n" + "-"*80)
    
    # Step 2: Make the real API call through our proxy with sanitized data
    print(f"\nMaking API call through proxy at {proxy_url}...")
    api_response = make_openai_api_call(sanitized_prompt, api_key, proxy_url)
    
    print("\nRAW AI RESPONSE (may contain placeholders):")
    print(api_response)
    print("\n" + "-"*80)
    
    # Step 3: Process the output to restore original sensitive information where appropriate
    restored_response = process_output(api_response)
    
    print("\nRESTORED RESPONSE (returned to user):")
    print(restored_response)
    print("\n" + "-"*80)
    
    # Display overall privacy metrics
    overall_metrics = get_privacy_metrics()
    print("\nOVERALL PRIVACY METRICS:")
    print(f"Total requests processed: {overall_metrics['total_requests']}")
    print(f"Total sensitive items detected: {overall_metrics['total_detected']}")
    print(f"Total sensitive items transformed: {overall_metrics['total_transformed']}")
    print(f"Last activity: {overall_metrics['last_activity']}")
    
    print("\n=== DEMONSTRATION COMPLETE ===")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a real OpenAI API call through the privacy proxy")
    parser.add_argument("--prompt", help="Custom prompt to use (default: use built-in example)")
    parser.add_argument("--api-key", help="OpenAI API key (default: use OPENAI_API_KEY env var)")
    parser.add_argument("--proxy", default="http://localhost:8080", help="Proxy URL (default: http://localhost:8080)")
    
    args = parser.parse_args()
    
    # Run the demo
    run_demo(args.prompt, args.api_key, args.proxy) 