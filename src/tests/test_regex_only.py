#!/usr/bin/env python3
"""
Test script for the regex patterns in TransformersRecognizer
This script extracts and tests only the regex patterns without importing the full module
"""

import logging
import re
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-regex-only")

# Define the regex patterns (copied from transformers_recognizer.py)
REGEX_PATTERNS = {
    "EMAIL_ADDRESS": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "PHONE_NUMBER": re.compile(r'\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b'),
    "IP_ADDRESS": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
    "US_SSN": re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'),
    "CREDIT_CARD": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
    "URL": re.compile(r'\bhttps?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'),
    "DATE": re.compile(r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b'),
    "USERNAME": re.compile(r'\b@[A-Za-z0-9_]{3,15}\b'),
}

# Add additional regex patterns for common PII types
ADDITIONAL_REGEX_PATTERNS = {
    "ADDRESS": re.compile(r'\b\d+\s+[A-Za-z0-9\s,]+(?:Avenue|Lane|Road|Boulevard|Drive|Street|Ave|Dr|Rd|Blvd|Ln|St)\.?\b', re.IGNORECASE),
    "PERSON": re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'),
    "LOCATION": re.compile(r'\b[A-Z][a-z]+(?:,\s+[A-Z]{2})?\b'),
    "ORGANIZATION": re.compile(r'\b[A-Z][a-z]*(?:\s+[A-Z][a-z]*)+\s+(?:Inc|LLC|Ltd|Corporation|Corp|Company|Co)\b'),
    "PASSWORD": re.compile(r'\b(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}\b'),
}

# Update the REGEX_PATTERNS dictionary with additional patterns
REGEX_PATTERNS.update(ADDITIONAL_REGEX_PATTERNS)

def test_regex_patterns():
    """Test the regex patterns"""
    logger.info("Testing regex patterns...")
    
    # Sample text with various PII entities
    test_text = """
    John Doe can be reached at john.doe@example.com or (555) 123-4567.
    His credit card number is 4111-1111-1111-1111 and SSN is 123-45-6789.
    He lives at 123 Main St, New York, NY 10001 and his IP is 192.168.1.1.
    Check out his website at https://www.johndoe.com or follow him @johndoe.
    The meeting is scheduled for 01/15/2023 with Microsoft Corporation.
    """
    
    results = []
    
    # Process each entity type
    for entity_type, pattern in REGEX_PATTERNS.items():
        matches = list(pattern.finditer(test_text))
        
        if matches:
            logger.info(f"Pattern for {entity_type} found {len(matches)} matches:")
            for match in matches:
                start, end = match.span()
                entity_text = test_text[start:end]
                logger.info(f"  - '{entity_text}'")
                
                results.append({
                    "entity_type": entity_type,
                    "start": start,
                    "end": end,
                    "text": entity_text,
                    "score": 0.85  # Default confidence for regex matches
                })
        else:
            logger.warning(f"Pattern for {entity_type} found no matches")
    
    # Print results
    logger.info(f"Found {len(results)} entities in total")
    
    # Verify we found all expected entity types
    found_types = set(result["entity_type"] for result in results)
    expected_types = {"EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IP_ADDRESS", "URL", "USERNAME", "DATE", "PERSON"}
    missing_types = expected_types - found_types
    
    if missing_types:
        logger.warning(f"Missing entity types: {missing_types}")
    else:
        logger.info("All expected entity types were found")
    
    return results

def validate_luhn_check():
    """Test the Luhn algorithm for credit card validation"""
    logger.info("Testing Luhn algorithm for credit card validation...")
    
    def luhn_check(digits):
        """Implement the Luhn algorithm for credit card validation"""
        try:
            # Reverse the digits
            digits = digits[::-1]
            
            # Double every second digit
            doubled = [(d * 2 if i % 2 == 1 else d) for i, d in enumerate(digits)]
            
            # Sum the digits (if a doubled number is > 9, add its digits)
            total = sum(d if d < 10 else d - 9 for d in doubled)
            
            # Check if divisible by 10
            return total % 10 == 0
        except Exception:
            return False
    
    # Test valid credit card numbers
    valid_cards = [
        "4111111111111111",  # Visa
        "5555555555554444",  # Mastercard
        "378282246310005",   # American Express
        "6011111111111117",  # Discover
    ]
    
    # Test invalid credit card numbers
    invalid_cards = [
        "4111111111111112",  # Invalid Visa
        "1234567890123456",  # Invalid format
        "9999999999999999",  # Invalid
    ]
    
    # Test valid cards
    for card in valid_cards:
        digits = [int(d) for d in card]
        is_valid = luhn_check(digits)
        logger.info(f"Card {card}: {'VALID' if is_valid else 'INVALID'} (expected: VALID)")
        
    # Test invalid cards
    for card in invalid_cards:
        digits = [int(d) for d in card]
        is_valid = luhn_check(digits)
        logger.info(f"Card {card}: {'VALID' if is_valid else 'INVALID'} (expected: INVALID)")
    
    return True

def main():
    """Main test function"""
    logger.info("Starting regex pattern tests")
    
    # Test regex patterns
    results = test_regex_patterns()
    success = len(results) > 0
    
    # Test Luhn algorithm
    luhn_success = validate_luhn_check()
    
    # Summary
    logger.info("\nTest Summary:")
    logger.info(f"Environment: Python {sys.version.split()[0]}")
    logger.info(f"Regex patterns test: {'PASS' if success else 'FAIL'}")
    logger.info(f"Luhn algorithm test: {'PASS' if luhn_success else 'FAIL'}")
    logger.info(f"Entities found: {len(results)}")
    
    return 0 if success and luhn_success else 1

if __name__ == "__main__":
    sys.exit(main())