"""
This is a test file containing sensitive data to verify PII detection and redaction
"""

# Personal Information
user_data = {
    "name": "John Michael Smith",
    "email": "john.smith@example.com",
    "phone": "(555) 123-4567",
    "ssn": "123-45-6789",
    "dob": "April 15, 1985",
    "address": "123 Main Street, Apt 4B, New York, NY 10001",
    "credit_card": "4111 1111 1111 1111",
    "expiration": "05/25",
    "cvv": "123"
}

# API Keys and Tokens
api_keys = {
    "openai_api_key": "sk-1234abcd5678efgh9012ijkl",
    "github_token": "ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890",
    "aws_access_key": "AKIAIOSFODNN7EXAMPLE",
    "aws_secret_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}

# Database Connection String
connection_string = "Server=myServerAddress;Database=myDataBase;User Id=myUsername;Password=myPassword;"

# Function that processes user information
def process_user_data(user):
    """Process user information and return formatted output"""
    print(f"Processing data for: {user['name']}")
    
    # Format address for display
    address_parts = user['address'].split(', ')
    formatted_address = "\n".join(address_parts)
    
    # Create a summary with sensitive information
    summary = f"""
User Summary:
------------
Name: {user['name']}
Contact: {user['email']} / {user['phone']}
SSN: {user['ssn']}
DOB: {user['dob']}
Address: {formatted_address}
Payment: Card ending in {user['credit_card'][-4:]} (Expires: {user['expiration']})
"""
    return summary

# Completion suggestion here: Create a function that 