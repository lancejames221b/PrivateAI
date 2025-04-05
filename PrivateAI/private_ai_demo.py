#!/usr/bin/env python3
"""
Private AI Demo Script

This script demonstrates how to use the Privacy Assistant to protect sensitive 
information in API calls to AI models like OpenAI's GPT models.

It shows a complete example of:
1. Processing input prompt to remove sensitive information
2. Making API calls with sanitized data
3. Restoring sensitive information in the response
"""

import os
import json
import logging
import requests
from datetime import datetime
from privacy_assistant import process_input, process_output, get_privacy_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("private-ai-demo")

# Mock OpenAI API call function (in a real scenario, this would use the actual API)
def mock_openai_api_call(prompt, model="gpt-4"):
    """
    Simulate an OpenAI API call to demonstrate the privacy protection.
    In a real implementation, this would use the actual API.
    """
    logger.info(f"Making API call to {model}")
    
    # In a real scenario, this would be:
    # headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}"}
    # response = requests.post(
    #     "https://api.openai.com/v1/chat/completions",
    #     headers=headers,
    #     json={
    #         "model": model,
    #         "messages": [{"role": "user", "content": prompt}],
    #         "temperature": 0.7
    #     }
    # )
    # return response.json()["choices"][0]["message"]["content"]
    
    # For demonstration, we'll simulate a response that mentions elements from the prompt
    # This demonstrates how the privacy assistant handles placeholders in both directions
    lines = prompt.strip().split('\n')
    keywords = []
    
    # Extract key tokens from the prompt to simulate a contextual response
    for line in lines:
        if ':' in line:
            parts = line.split(':')
            if len(parts) >= 2:
                keywords.append(parts[1].strip())
    
    # Extract values for the response
    keyword_value = keywords[0] if keywords else 'your project'
    last_keyword = keywords[-1] if keywords else 'your project'
    
    # Get server IP if present
    server_value = "your specified address"
    if 'IP' in prompt:
        try:
            server_value = prompt.split('IP')[1].split(' ')[1]
        except:
            pass
            
    # Get email if present
    email_value = "the email you provided"
    if 'Email:' in prompt:
        try:
            email_value = prompt.split('Email:')[1].split('\n')[0].strip()
        except:
            pass
    
    # Create a response that references back to input elements (simulating how an
    # AI might repeat sensitive information back in its response)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Use string formatting without f-strings
    response = """
Based on your request at {}, I've analyzed the information provided.

Your credentials have been verified, and I can see you're working on a project 
that requires access to specific resources. The information for {} 
has been analyzed.

Here are some recommendations:
1. For secure access, continue using your provided API key
2. The server at {} should be configured 
   with additional security measures
3. Your contact information ({}) 
   has been registered for further updates

Let me know if you need further assistance with {}.
""".format(current_time, keyword_value, server_value, email_value, last_keyword)
    return response

def run_demo():
    """Run the complete privacy-preserving AI interaction demo"""
    print("\n=== PRIVATE AI DEMONSTRATION ===\n")
    
    # Original prompt with sensitive information
    original_prompt = """
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
    print(original_prompt)
    print("\n" + "-"*80)
    
    # Step 1: Process the input to remove sensitive information
    sanitized_prompt, metrics, transformations = process_input(original_prompt)
    
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
    
    # Step 2: Make the API call with sanitized data
    print("\nMaking API call with sanitized data...")
    api_response = mock_openai_api_call(sanitized_prompt)
    
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
    run_demo() 