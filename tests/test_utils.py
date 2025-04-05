"""
Unit tests for utils.py module.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import (
    initialize_presidio,
    initialize_anonymizer,
    DatabaseEncryption,
    get_domain_blocklist,
    get_custom_patterns,
    apply_regex_patterns,
    is_potentially_sensitive,
    safe_json_loads,
    transform_url_parameters,
    detect_and_adapt_ai_format
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a mock environment for testing
        self.env_patcher = patch.dict('os.environ', {
            'DB_ENCRYPTION_KEY': 'dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleT0=',  # Base64 encoded test key
            'BLOCK_ALL_DOMAINS': 'false'
        })
        self.env_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        self.temp_dir.cleanup()

    @patch('utils.SPACY_AVAILABLE', False)
    @patch('utils.PRESIDIO_AVAILABLE', False)
    def test_initialize_presidio_dependencies_not_available(self):
        """Test initialize_presidio when dependencies are not available."""
        result = initialize_presidio()
        self.assertIsNone(result)

    @patch('utils.SPACY_AVAILABLE', True)
    @patch('utils.PRESIDIO_AVAILABLE', True)
    @patch('utils.NlpEngineProvider')
    @patch('utils.RecognizerRegistry')
    @patch('utils.AnalyzerEngine')
    @patch('utils.PatternRecognizer')
    def test_initialize_presidio_success(self, mock_pattern_recognizer, mock_analyzer_engine, 
                                        mock_registry, mock_nlp_provider):
        """Test initialize_presidio successful initialization."""
        # Mock the NLP engine provider and analyzer
        mock_nlp_engine = MagicMock()
        mock_nlp_provider.return_value.create_engine.return_value = mock_nlp_engine
        mock_registry.return_value = MagicMock()
        mock_analyzer = MagicMock()
        mock_analyzer_engine.return_value = mock_analyzer
        
        # Call the function
        result = initialize_presidio()
        
        # Verify the result
        self.assertEqual(result, mock_analyzer)
        mock_nlp_provider.assert_called_once()
        mock_registry.assert_called_once()
        mock_analyzer_engine.assert_called_once_with(nlp_engine=mock_nlp_engine, registry=mock_registry.return_value)
        
        # Verify that custom recognizers were added
        self.assertTrue(mock_pattern_recognizer.called)
        self.assertTrue(mock_registry.return_value.add_recognizer.called)

    @patch('utils.PRESIDIO_AVAILABLE', False)
    def test_initialize_anonymizer_dependencies_not_available(self):
        """Test initialize_anonymizer when dependencies are not available."""
        result = initialize_anonymizer()
        self.assertIsNone(result)

    @patch('utils.PRESIDIO_AVAILABLE', True)
    @patch('utils.AnonymizerEngine')
    def test_initialize_anonymizer_success(self, mock_anonymizer_engine):
        """Test initialize_anonymizer successful initialization."""
        mock_anonymizer = MagicMock()
        mock_anonymizer_engine.return_value = mock_anonymizer
        
        result = initialize_anonymizer()
        
        self.assertEqual(result, mock_anonymizer)
        mock_anonymizer_engine.assert_called_once()

    def test_database_encryption_init_with_key(self):
        """Test DatabaseEncryption initialization with provided key."""
        db_encryption = DatabaseEncryption()
        self.assertIsNotNone(db_encryption.cipher)
        
        # Test with a specific key
        with patch.dict('os.environ', {'DB_ENCRYPTION_KEY': 'dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleT0='}):
            db_encryption = DatabaseEncryption()
            self.assertIsNotNone(db_encryption.cipher)
            self.assertEqual(db_encryption.key, b'testkeytesteykeytesteyk=')

    def test_database_encryption_encrypt_decrypt(self):
        """Test encryption and decryption of data."""
        db_encryption = DatabaseEncryption()
        
        # Test with a simple string
        original_text = "sensitive data"
        encrypted_text = db_encryption.encrypt(original_text)
        
        # Verify encryption changed the text
        self.assertNotEqual(original_text, encrypted_text)
        
        # Verify decryption restores the original
        decrypted_text = db_encryption.decrypt(encrypted_text)
        self.assertEqual(original_text, decrypted_text)
        
        # Test with empty string
        self.assertEqual(db_encryption.encrypt(""), "")
        self.assertEqual(db_encryption.decrypt(""), "")
        
        # Test with None
        self.assertIsNone(db_encryption.encrypt(None))
        self.assertIsNone(db_encryption.decrypt(None))

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data="example.com\n# Comment\nmalicious.com")
    def test_get_domain_blocklist(self, mock_file, mock_exists):
        """Test loading domain blocklist."""
        mock_exists.return_value = True
        
        blocklist = get_domain_blocklist()
        
        self.assertEqual(len(blocklist), 2)
        self.assertIn("example.com", blocklist)
        self.assertIn("malicious.com", blocklist)
        self.assertNotIn("# Comment", blocklist)
        
        # Test when file doesn't exist
        mock_exists.return_value = False
        blocklist = get_domain_blocklist()
        self.assertEqual(blocklist, [])

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test_pattern": {"pattern": "test\\\\d+", "is_active": true, "entity_type": "TEST"}}')
    def test_get_custom_patterns(self, mock_file, mock_exists):
        """Test loading custom patterns."""
        mock_exists.return_value = True
        
        patterns = get_custom_patterns()
        
        self.assertIn("TEST_test_pattern", patterns)
        self.assertEqual(patterns["TEST_test_pattern"], "test\\d+")
        
        # Test when file doesn't exist
        mock_exists.return_value = False
        patterns = get_custom_patterns()
        self.assertEqual(patterns, {})

    def test_apply_regex_patterns(self):
        """Test applying regex patterns to find sensitive information."""
        # Create a test text with sensitive information
        test_text = "Contact john@example.com or call 555-123-4567. API key: api-key-12345"
        
        # Mock the get_custom_patterns and get_domain_blocklist functions
        with patch('utils.get_custom_patterns', return_value={}), \
             patch('utils.get_domain_blocklist', return_value=[]):
            
            entities = apply_regex_patterns(test_text)
            
            # Verify that sensitive information was detected
            self.assertGreater(len(entities), 0)
            
            # Check for email detection
            email_entities = [e for e in entities if e['entity'] == 'EMAIL']
            self.assertEqual(len(email_entities), 1)
            self.assertEqual(email_entities[0]['word'], 'john@example.com')
            
            # Check for API key detection
            api_key_entities = [e for e in entities if e['entity'] == 'API_KEY']
            self.assertEqual(len(api_key_entities), 1)
            self.assertEqual(api_key_entities[0]['word'], 'api-key-12345')

    def test_is_potentially_sensitive(self):
        """Test checking if text might contain sensitive information."""
        # Test with sensitive terms
        sensitive_texts = [
            "Here is my api key: api-key-12345",
            "My password is secret123",
            "Internal project name: project-x",
            "SentinelOne agent ID: 12345-abcd-67890",
            "IP address: 192.168.1.1"
        ]
        
        for text in sensitive_texts:
            self.assertTrue(is_potentially_sensitive(text))
        
        # Test with non-sensitive text
        non_sensitive_text = "This is a regular message without sensitive information."
        
        # Mock domain blocklist to be empty for this test
        with patch('utils.get_domain_blocklist', return_value=[]):
            self.assertFalse(is_potentially_sensitive(non_sensitive_text))

    def test_safe_json_loads(self):
        """Test safely parsing JSON."""
        # Test with valid JSON
        valid_json = '{"key": "value", "number": 123}'
        result, success = safe_json_loads(valid_json)
        
        self.assertTrue(success)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["number"], 123)
        
        # Test with invalid JSON
        invalid_json = '{"key": "value", number: 123}'
        result, success = safe_json_loads(invalid_json)
        
        self.assertFalse(success)
        self.assertIsNone(result)
        
        # Test with non-string input
        result, success = safe_json_loads(None)
        self.assertFalse(success)
        self.assertIsNone(result)

    def test_transform_url_parameters(self):
        """Test transforming sensitive data in URL parameters."""
        # URL with sensitive parameters
        test_url = "https://api.example.com/v1/users?api_key=sk_test_12345&email=john@example.com&name=John"
        
        transformed_url = transform_url_parameters(test_url)
        
        # Verify that sensitive parameters were transformed
        self.assertIn("https://api.example.com/v1/users?", transformed_url)
        self.assertNotIn("sk_test_12345", transformed_url)
        self.assertNotIn("john@example.com", transformed_url)
        self.assertIn("name=John", transformed_url)  # Non-sensitive parameter should remain
        
        # Test URL without parameters
        url_without_params = "https://api.example.com/v1/users"
        self.assertEqual(transform_url_parameters(url_without_params), url_without_params)

    def test_detect_and_adapt_ai_format_openai(self):
        """Test detecting and adapting OpenAI format."""
        # OpenAI format request
        openai_request = {
            "model": "gpt-4",
            "messages": [
                {"role": "user", "content": "Hello, AI!"}
            ]
        }
        
        result, format_detected, adapted = detect_and_adapt_ai_format(openai_request)
        
        self.assertEqual(format_detected, "openai")
        self.assertFalse(adapted)
        self.assertEqual(result, openai_request)

    def test_detect_and_adapt_ai_format_anthropic(self):
        """Test detecting and adapting Anthropic format."""
        # Anthropic format request
        anthropic_request = {
            "model": "claude-2",
            "prompt": "\n\nHuman: Hello, Claude!\n\nAssistant:"
        }
        
        result, format_detected, adapted = detect_and_adapt_ai_format(anthropic_request)
        
        self.assertEqual(format_detected, "anthropic")
        self.assertTrue(adapted)
        self.assertIn("messages", result)
        self.assertEqual(result["messages"][0]["role"], "user")
        self.assertEqual(result["messages"][0]["content"], "Hello, Claude!")

    def test_detect_and_adapt_ai_format_unknown(self):
        """Test with unknown AI format."""
        # Unknown format request
        unknown_request = {
            "unknown_field": "value"
        }
        
        result, format_detected, adapted = detect_and_adapt_ai_format(unknown_request)
        
        self.assertEqual(format_detected, "unknown")
        self.assertFalse(adapted)
        self.assertEqual(result, unknown_request)


if __name__ == '__main__':
    unittest.main()