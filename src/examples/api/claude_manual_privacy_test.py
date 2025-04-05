#!/usr/bin/env python3
"""
Claude Manual Privacy Test - This script manually applies privacy transformations
before sending data to Claude 3.7 Sonnet, simulating the Privacy AI Proxy functionality.
"""

import os
import sys
import argparse
import json
import requests
import re
import hashlib
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default configuration
DEFAULT_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-3-sonnet-20240229"  # Using Claude 3 Sonnet
API_URL = "https://api.anthropic.com/v1/messages"

# Sensitivity levels
SENSITIVITY_HIGH = "HIGH"
SENSITIVITY_MEDIUM = "MEDIUM"
SENSITIVITY_LOW = "LOW"

# Regular expression patterns for detecting sensitive information
PATTERNS = {
    "API_KEY": (r'(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}|api[_-]?key[=: "\']+[0-9a-zA-Z\-_]{20,}', SENSITIVITY_HIGH),
    "EMAIL": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', SENSITIVITY_HIGH),
    "IP_ADDRESS": (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', SENSITIVITY_MEDIUM),
    "CREDIT_CARD": (r'\b(?:\d{4}[- ]?){3}\d{4}\b', SENSITIVITY_HIGH),
    "SSN": (r'\b\d{3}-\d{2}-\d{4}\b', SENSITIVITY_HIGH),
    "AWS_KEY": (r'AKIA[0-9A-Z]{16}', SENSITIVITY_HIGH),
    "PASSWORD": (r'password[=: "\']+[^ ]{8,}|[Pp]assword is [^ ]{8,}', SENSITIVITY_HIGH),
    "PHONE_NUMBER": (r'\+?\d{1,3}[- ]?\(?\d{3}\)?[- ]?\d{3,4}[- ]?\d{4}', SENSITIVITY_MEDIUM),
    "NAME": (r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)?\s?[A-Z][a-z]+ [A-Z][a-z]+\b', SENSITIVITY_LOW),
}

def parse_arguments():
    parser = argparse.ArgumentParser(description="Test manual privacy transformations with Claude 3.7 Sonnet")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY,
                        help="Anthropic API key (defaults to ANTHROPIC_API_KEY env var)")
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt to send to Claude (default: use built-in prompt with PII)")
    parser.add_argument("--model", default=CLAUDE_MODEL,
                        help=f"Claude model to use (default: {CLAUDE_MODEL})")
    parser.add_argument("--extended-thinking", action="store_true", 
                        help="Use Claude 3.7's extended thinking mode for complex reasoning")
    parser.add_argument("--skip-privacy", action="store_true",
                        help="Skip privacy transformations (for comparison)")
    return parser.parse_args()

def get_test_prompt_with_pii():
    """
    Create a test prompt with various types of sensitive information embedded in it
    """
    return """
    Hello Claude, I'm testing a privacy protection system that transforms sensitive data.
    
    My name is John Smith and I live at 123 Main Street, New York, NY 10001. 
    My phone number is 212-555-1234 and my email is john.smith@example.com.
    My credit card number is 4111-1111-1111-1111 with expiration 12/25 and CVV 123.
    My social security number is 123-45-6789.
    My API key is sk_live_51NZw66BLxRpYtGHkqtBsgDfEPXI2v3olWjcf9bAFATAP9NCr.
    My database password is Sup3rS3cr3t!2023.
    
    Please analyze what happened to this information. What types of sensitive data can you identify in what I sent? 
    Don't repeat any actual sensitive values, but do explain what kinds of data were present and how they 
    might have been transformed. Also, describe how Claude 3.7 Sonnet's capabilities are helpful in privacy-focused applications.
    """

def get_agentic_test_prompt():
    """
    Create a test prompt that triggers agentic capabilities, including file manipulation
    """
    return """
    Hello Claude, I need your help to create a Python script that implements a privacy transformation system for sensitive data.
    
    The system should:
    1. Detect various types of sensitive information (PII) in text
    2. Replace the sensitive information with placeholders
    3. Store the mapping between placeholders and original values securely
    4. Be able to restore the original values when needed
    
    My name is Sarah Johnson and my email is sarah.j@example.com.
    If you need to use example data, please use this information above.
    
    Additionally, my AWS access key is AKIAIOSFODNN7EXAMPLE and my secret key is wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY.
    
    Please provide a complete Python implementation with proper error handling, comments, and a brief explanation of
    how your solution works. Focus on security best practices for handling sensitive data.
    """

def apply_privacy_transformations(text):
    """
    Apply privacy transformations to the input text
    Returns:
        - Transformed text
        - Dictionary of transformations
        - Metrics
    """
    transformations = {}
    metrics = {
        'detected_entities': 0,
        'transformed_entities': 0,
        'sensitivity_high': 0,
        'sensitivity_medium': 0,
        'sensitivity_low': 0
    }
    
    transformed_text = text
    
    # Find and replace sensitive information
    for entity_type, (pattern, sensitivity) in PATTERNS.items():
        matches = re.finditer(pattern, transformed_text)
        for match in matches:
            original = match.group(0)
            if original not in transformations:
                # Generate a placeholder with type, sensitivity and hash
                hash_suffix = hashlib.md5(original.encode()).hexdigest()[:8]
                sensitivity_code = sensitivity[0]
                placeholder = f"__{entity_type}_{sensitivity_code}_{hash_suffix}__"
                
                # Store the transformation
                transformations[original] = {
                    'placeholder': placeholder,
                    'entity_type': entity_type,
                    'sensitivity': sensitivity
                }
                
                # Update metrics
                metrics['detected_entities'] += 1
                metrics['transformed_entities'] += 1
                if sensitivity == SENSITIVITY_HIGH:
                    metrics['sensitivity_high'] += 1
                elif sensitivity == SENSITIVITY_MEDIUM:
                    metrics['sensitivity_medium'] += 1
                else:
                    metrics['sensitivity_low'] += 1
    
    # Apply transformations to the text
    for original, info in transformations.items():
        transformed_text = transformed_text.replace(original, info['placeholder'])
    
    return transformed_text, transformations, metrics

def send_claude_request(prompt, api_key, model, extended_thinking=False):
    """
    Send a request to Claude 3.7 Sonnet
    """
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": model,
        "max_tokens": 4000,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    # Enable extended thinking mode for Claude 3.7 Sonnet
    if extended_thinking:
        data["system"] = "Use your extended thinking mode to provide a carefully reasoned response."
    
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json=data
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

def restore_original_values(text, transformations):
    """
    Restore original values from the transformed text
    """
    restored_text = text
    
    # Replace placeholders with original values
    for original, info in transformations.items():
        restored_text = restored_text.replace(info['placeholder'], original)
    
    return restored_text

def main():
    args = parse_arguments()
    
    if not args.api_key:
        print("Error: No Anthropic API key provided.")
        print("Set the ANTHROPIC_API_KEY environment variable or use the --api-key option.")
        sys.exit(1)
    
    # Determine which prompt to use
    if args.prompt:
        original_prompt = args.prompt
        print("Using custom prompt")
    else:
        original_prompt = get_agentic_test_prompt()
        print("Using agentic test prompt with PII")
    
    # Apply privacy transformations
    if args.skip_privacy:
        print("Skipping privacy transformations (sending original prompt)")
        transformed_prompt = original_prompt
        transformations = {}
        metrics = {'detected_entities': 0, 'transformed_entities': 0}
    else:
        transformed_prompt, transformations, metrics = apply_privacy_transformations(original_prompt)
        
        print("\n" + "="*50)
        print("PRIVACY METRICS:")
        print("="*50)
        print(f"Detected entities: {metrics['detected_entities']}")
        print(f"Transformed entities: {metrics['transformed_entities']}")
        print(f"High sensitivity items: {metrics['sensitivity_high']}")
        print(f"Medium sensitivity items: {metrics['sensitivity_medium']}")
        print(f"Low sensitivity items: {metrics['sensitivity_low']}")
        
        print("\n" + "="*50)
        print("TRANSFORMATIONS:")
        print("="*50)
        for original, info in transformations.items():
            print(f"• {original} → {info['placeholder']} ({info['entity_type']} - {info['sensitivity']})")
    
    # Send request to Claude
    print(f"\nSending request to {args.model}...")
    if args.extended_thinking:
        print("Using extended thinking mode")
    
    response = send_claude_request(transformed_prompt, args.api_key, args.model, args.extended_thinking)
    
    if response:
        print("\n" + "="*50)
        print("CLAUDE RESPONSE (with transformations):")
        print("="*50)
        
        content = response["content"][0]["text"]
        print(content)
        
        # Restore original values if needed
        if not args.skip_privacy and transformations:
            restored_content = restore_original_values(content, transformations)
            
            print("\n" + "="*50)
            print("RESTORED RESPONSE:")
            print("="*50)
            print(restored_content)
        
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