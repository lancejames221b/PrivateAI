#!/usr/bin/env python3
"""
Test file with sensitive data to check if the PrivateAI proxy detects and transforms it.
"""

# Personal Information
NAME = "John Smith"
EMAIL = "john.smith@example.com"
PHONE = "(555) 123-4567"
ADDRESS = "123 Main St, Anytown, CA 12345"
SSN = "123-45-6789"
CREDIT_CARD = "4111-1111-1111-1111"
DOB = "01/01/1980"

def get_user_info():
    """Return user information as a dictionary"""
    return {
        "name": NAME,
        "email": EMAIL,
        "phone": PHONE,
        "address": ADDRESS,
        "ssn": SSN,
        "credit_card": CREDIT_CARD,
        "dob": DOB
    }

def main():
    """Main function"""
    print(f"User: {NAME}")
    print(f"Email: {EMAIL}")
    print(f"Phone: {PHONE}")
    print(f"Address: {ADDRESS}")
    print(f"SSN: {SSN}")
    print(f"Credit Card: {CREDIT_CARD}")
    print(f"DOB: {DOB}")

if __name__ == "__main__":
    main()

# TODO: Implement a function to process user data
# This comment is intended to trigger AI code completion with sensitive data
# The function should take the user's name, email, and address and format it for display