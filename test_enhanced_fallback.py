#!/usr/bin/env python3
"""
Test script for the enhanced TransformersRecognizer with robust fallback mechanism
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-enhanced-fallback")

def test_direct_regex_patterns():
    """Test the regex patterns directly"""
    logger.info("Testing regex patterns directly...")
    
    # Import the regex patterns from the module
    try:
        # First try to import the module
        import transformers_recognizer
        
        # Get the regex patterns
        patterns = transformers_recognizer.REGEX_PATTERNS
        logger.info(f"Successfully imported {len(patterns)} regex patterns")
        
        # Sample text with various PII entities
        test_text = """
        John Doe can be reached at john.doe@example.com or (555) 123-4567.
        His credit card number is 4111-1111-1111-1111 and SSN is 123-45-6789.
        He lives at 123 Main St, New York, NY 10001 and his IP is 192.168.1.1.
        Check out his website at https://www.johndoe.com or follow him @johndoe.
        """
        
        # Test each pattern
        total_matches = 0
        for entity_type, pattern in patterns.items():
            matches = list(pattern.finditer(test_text))
            match_count = len(matches)
            total_matches += match_count
            
            if match_count > 0:
                logger.info(f"Pattern for {entity_type} found {match_count} matches:")
                for match in matches:
                    start, end = match.span()
                    logger.info(f"  - '{test_text[start:end]}'")
            else:
                logger.warning(f"Pattern for {entity_type} found no matches")
        
        logger.info(f"Total matches across all patterns: {total_matches}")
        return total_matches > 0
        
    except ImportError as e:
        logger.error(f"Error importing transformers_recognizer: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def test_fallback_mechanism():
    """Test the fallback mechanism in the TransformersRecognizer"""
    logger.info("Testing fallback mechanism...")
    
    try:
        # Import the module
        import transformers_recognizer
        
        # Check if imports are available
        if transformers_recognizer.IMPORTS_AVAILABLE:
            logger.info("Transformers imports are available - fallback not needed")
        else:
            logger.info("Transformers imports not available - fallback should be used")
            logger.info(f"Import error: {transformers_recognizer.TRANSFORMERS_IMPORT_ERROR}")
            
            if transformers_recognizer.NUMPY_COMPATIBILITY_ISSUE:
                logger.info("Numpy compatibility issue detected - this is expected")
        
        # Create mock classes if needed for testing
        if not transformers_recognizer.IMPORTS_AVAILABLE:
            logger.info("Creating mock classes for testing")
            
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
            transformers_recognizer.RecognizerResult = MockRecognizerResult
            transformers_recognizer.EntityRecognizer = MockEntityRecognizer
            transformers_recognizer.AnalysisExplanation = MockAnalysisExplanation
        
        # Try to create the recognizer
        try:
            recognizer = transformers_recognizer.TransformersRecognizer()
            logger.info("Successfully created TransformersRecognizer")
            
            # Check if using fallback
            if recognizer.using_regex_fallback:
                logger.info("Recognizer is using regex fallback as expected")
            else:
                logger.info("Recognizer is using transformer models")
            
            # Sample text with various PII entities
            test_text = """
            John Doe can be reached at john.doe@example.com or (555) 123-4567.
            His credit card number is 4111-1111-1111-1111 and SSN is 123-45-6789.
            He lives at 123 Main St, New York, NY 10001 and his IP is 192.168.1.1.
            Check out his website at https://www.johndoe.com or follow him @johndoe.
            """
            
            # Test the analyze method
            entities = ["EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "US_SSN", "IP_ADDRESS", "URL", "USERNAME"]
            results = recognizer.analyze(test_text, entities)
            
            logger.info(f"Found {len(results)} entities:")
            for result in results:
                entity_text = test_text[result.start:result.end]
                logger.info(f"{result.entity_type} ({result.score:.2f}): '{entity_text}'")
                
            return len(results) > 0
            
        except Exception as e:
            logger.error(f"Error creating or using recognizer: {str(e)}")
            return False
            
    except ImportError as e:
        logger.error(f"Error importing transformers_recognizer: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("Starting enhanced fallback tests")
    
    # Test regex patterns directly
    patterns_success = test_direct_regex_patterns()
    logger.info(f"Direct regex patterns test: {'PASS' if patterns_success else 'FAIL'}")
    
    # Test fallback mechanism
    fallback_success = test_fallback_mechanism()
    logger.info(f"Fallback mechanism test: {'PASS' if fallback_success else 'FAIL'}")
    
    # Summary
    logger.info("\nTest Summary:")
    logger.info(f"Environment: Python {sys.version.split()[0]}")
    logger.info(f"Direct regex patterns test: {'PASS' if patterns_success else 'FAIL'}")
    logger.info(f"Fallback mechanism test: {'PASS' if fallback_success else 'FAIL'}")
    
    return 0 if patterns_success else 1

if __name__ == "__main__":
    sys.exit(main())