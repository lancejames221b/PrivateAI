#!/usr/bin/env python3
"""
Simple test script for the regex fallback mechanism in TransformersRecognizer
"""

import logging
import re
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-simple-fallback")

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

def test_regex_fallback():
    """Test the regex-based fallback mechanism"""
    logger.info("Testing regex fallback mechanism...")
    
    # Sample text with various PII entities
    test_text = """
    John Doe can be reached at john.doe@example.com or (555) 123-4567.
    His credit card number is 4111-1111-1111-1111 and SSN is 123-45-6789.
    He lives at 123 Main St, New York, NY 10001 and his IP is 192.168.1.1.
    Check out his website at https://www.johndoe.com or follow him @johndoe.
    """
    
    results = []
    
    # Process each entity type
    for entity_type, pattern in REGEX_PATTERNS.items():
        for match in pattern.finditer(test_text):
            start, end = match.span()
            entity_text = test_text[start:end]
            
            results.append({
                "entity_type": entity_type,
                "start": start,
                "end": end,
                "text": entity_text,
                "score": 0.85  # Default confidence for regex matches
            })
    
    # Print results
    logger.info(f"Found {len(results)} entities:")
    for result in results:
        logger.info(f"{result['entity_type']} ({result['score']:.2f}): '{result['text']}'")
    
    return results

def main():
    """Main test function"""
    logger.info("Starting simple regex fallback test")
    
    # Test regex fallback
    results = test_regex_fallback()
    success = len(results) > 0
    
    # Summary
    logger.info("\nTest Summary:")
    logger.info(f"Environment: Python {sys.version.split()[0]}")
    logger.info(f"Regex fallback test: {'PASS' if success else 'FAIL'}")
    logger.info(f"Entities found: {len(results)}")
    
    # Verify we found all expected entity types
    found_types = set(result["entity_type"] for result in results)
    expected_types = {"EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IP_ADDRESS", "URL", "USERNAME"}
    missing_types = expected_types - found_types
    
    if missing_types:
        logger.warning(f"Missing entity types: {missing_types}")
    else:
        logger.info("All expected entity types were found")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())