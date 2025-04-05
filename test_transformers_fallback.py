#!/usr/bin/env python3
"""
Test script for the TransformersRecognizer with fallback mechanisms
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-transformers-fallback")

# Import the transformers recognizer module
import transformers_recognizer

def test_environment_compatibility():
    """Test the environment compatibility check function"""
    logger.info("Testing environment compatibility check...")
    env_info = transformers_recognizer.check_environment_compatibility()
    
    for key, value in env_info.items():
        logger.info(f"{key}: {value}")
    
    return env_info

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
    
    # Create a mock analyzer class if presidio is not available
    if not transformers_recognizer.IMPORTS_AVAILABLE:
        logger.info("Presidio not available, creating mock classes for testing")
        
        class MockAnalysisExplanation:
            def __init__(self, recognizer, original_score, pattern_name, pattern, validation_result):
                self.recognizer = recognizer
                self.original_score = original_score
                self.pattern_name = pattern_name
                self.pattern = pattern
                self.validation_result = validation_result
                
        class MockRecognizerResult:
            def __init__(self, entity_type, start, end, score, analysis_explanation):
                self.entity_type = entity_type
                self.start = start
                self.end = end
                self.score = score
                self.analysis_explanation = analysis_explanation
                
            def __str__(self):
                return f"{self.entity_type} ({self.score:.2f}): {self.start}-{self.end}"
                
        class MockEntityRecognizer:
            def __init__(self, supported_entities, supported_language, name):
                self.supported_entities = supported_entities
                self.supported_language = supported_language
                self.name = name
                
        # Monkey patch the imports
        transformers_recognizer.AnalysisExplanation = MockAnalysisExplanation
        transformers_recognizer.RecognizerResult = MockRecognizerResult
        transformers_recognizer.EntityRecognizer = MockEntityRecognizer
    
    # Create the recognizer with regex fallback
    try:
        recognizer = transformers_recognizer.TransformersRecognizer()
        logger.info("Successfully created TransformersRecognizer")
        
        # Test the analyze method
        entities = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IP_ADDRESS", "URL", "USERNAME"]
        results = recognizer.analyze(test_text, entities)
        
        logger.info(f"Found {len(results)} entities:")
        for result in results:
            entity_text = test_text[result.start:result.end]
            logger.info(f"{result.entity_type} ({result.score:.2f}): '{entity_text}'")
            
        return len(results) > 0
    except Exception as e:
        logger.error(f"Error testing regex fallback: {str(e)}")
        return False

def test_transformers_model():
    """Test the transformers model if available"""
    if not transformers_recognizer.IMPORTS_AVAILABLE:
        logger.info("Transformers not available, skipping model test")
        return None
    
    logger.info("Testing transformers model...")
    
    try:
        # Create the recognizer
        recognizer = transformers_recognizer.TransformersRecognizer()
        
        # Check if model loaded successfully
        if recognizer.model:
            logger.info(f"Model loaded successfully: {recognizer.model_name}")
            return True
        else:
            logger.warning("Model not loaded")
            return False
    except Exception as e:
        logger.error(f"Error testing transformers model: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("Starting transformers recognizer tests")
    
    # Test environment compatibility
    env_info = test_environment_compatibility()
    
    # Test regex fallback
    regex_success = test_regex_fallback()
    logger.info(f"Regex fallback test {'successful' if regex_success else 'failed'}")
    
    # Test transformers model
    model_success = test_transformers_model()
    if model_success is None:
        logger.info("Transformers model test skipped")
    else:
        logger.info(f"Transformers model test {'successful' if model_success else 'failed'}")
    
    # Summary
    logger.info("\nTest Summary:")
    logger.info(f"Environment: Python {sys.version.split()[0]}")
    logger.info(f"Transformers available: {transformers_recognizer.IMPORTS_AVAILABLE}")
    logger.info(f"Numpy compatibility issue: {transformers_recognizer.NUMPY_COMPATIBILITY_ISSUE}")
    logger.info(f"Regex fallback test: {'PASS' if regex_success else 'FAIL'}")
    
    if model_success is not None:
        logger.info(f"Transformers model test: {'PASS' if model_success else 'FAIL'}")
    else:
        logger.info("Transformers model test: SKIPPED")
    
    return 0 if regex_success else 1

if __name__ == "__main__":
    sys.exit(main())