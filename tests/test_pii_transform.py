"""
Unit tests for pii_transform.py module.
"""

import unittest
import json
import os
import sqlite3
from unittest.mock import patch, MagicMock
import sys
import tempfile

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pii_transform import (
    get_replacement,
    generate_placeholder,
    detect_and_transform,
    transform_with_presidio,
    transform_json,
    restore_original_values,
    restore_json_values,
    get_db_connection_pii,
    _static_placeholder_generation
)


class TestPIITransform(unittest.TestCase):
    """Test cases for PII transformation functions."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary database for testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.original_db_path = 'data/mapping_store.db'
        
        # Patch the DB_PATH to use our temporary database
        self.db_path_patcher = patch('pii_transform.DB_PATH', self.temp_db_path)
        self.db_path_mock = self.db_path_patcher.start()
        
        # Initialize the test database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mappings (
            original TEXT PRIMARY KEY,
            replacement TEXT NOT NULL,
            entity_type TEXT,
            created_at TEXT,
            last_used TEXT,
            is_encrypted INTEGER DEFAULT 0
        )
        ''')
        conn.commit()
        conn.close()
        
        # Add some test mappings
        self.test_mappings = {
            'test@example.com': '__EMAIL_12345678__',
            '192.168.1.1': '__IP_87654321__',
            'api-key-12345': '__API_KEY_abcdef12__'
        }
        
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        for original, replacement in self.test_mappings.items():
            entity_type = 'EMAIL' if '@' in original else 'IP_ADDRESS' if '.' in original else 'API_KEY'
            cursor.execute(
                "INSERT INTO mappings VALUES (?, ?, ?, ?, ?, ?)",
                (original, replacement, entity_type, '2023-01-01T00:00:00', '2023-01-01T00:00:00', 0)
            )
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up after tests."""
        self.db_path_patcher.stop()
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)

    def test_get_replacement_existing(self):
        """Test retrieving an existing replacement."""
        for original, expected in self.test_mappings.items():
            result = get_replacement(original)
            self.assertEqual(result, expected)

    def test_get_replacement_new(self):
        """Test creating a new replacement."""
        new_email = 'new_user@example.com'
        result = get_replacement(new_email, 'EMAIL')
        self.assertTrue(result.startswith('__EMAIL_'))
        self.assertTrue(result.endswith('__'))
        
        # Verify it was stored in the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT replacement FROM mappings WHERE original = ?", (new_email,))
        db_result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(db_result)
        self.assertEqual(db_result[0], result)

    def test_get_replacement_with_entity_type(self):
        """Test creating replacements with different entity types."""
        test_cases = [
            ('john.doe@company.com', 'EMAIL'),
            ('10.0.0.1', 'IP_ADDRESS'),
            ('sk_test_12345abcdef', 'API_KEY'),
            ('John Smith', 'PERSON'),
            ('New York', 'LOCATION'),
            ('example.com', 'DOMAIN')
        ]
        
        for value, entity_type in test_cases:
            result = get_replacement(value, entity_type)
            self.assertTrue(f"__{entity_type}_" in result or f"__{entity_type[:3]}_" in result)

    @patch('pii_transform.db_encryption.encryption_enabled', False)
    def test_get_replacement_without_encryption(self):
        """Test creating a replacement without encryption."""
        value = 'unencrypted_data'
        result = get_replacement(value, 'GENERIC')
        
        # Verify it was stored unencrypted
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT original, is_encrypted FROM mappings WHERE replacement = ?", (result,))
        db_result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(db_result)
        self.assertEqual(db_result[0], value)  # Original value stored as-is
        self.assertEqual(db_result[1], 0)      # Not encrypted

    def test_generate_placeholder(self):
        """Test generating consistent placeholders."""
        # Test organization placeholder
        org_name = "Example Corp"
        org_placeholder = generate_placeholder("ORGANIZATION", org_name)
        self.assertIsNotNone(org_placeholder)
        
        # Test domain placeholder
        domain = "example.com"
        domain_placeholder = generate_placeholder("DOMAIN", domain)
        self.assertIsNotNone(domain_placeholder)
        self.assertTrue(domain_placeholder.endswith('.example.com'))
        
        # Test consistency - should get same placeholder for same input
        org_placeholder2 = generate_placeholder("ORGANIZATION", org_name)
        self.assertEqual(org_placeholder, org_placeholder2)

    def test_static_placeholder_generation(self):
        """Test static placeholder generation for different entity types."""
        # Test organization placeholder
        org_name = "Microsoft"
        org_placeholder = _static_placeholder_generation("ORGANIZATION", org_name)
        self.assertEqual(org_placeholder, "TechShield")
        
        # Test domain placeholder
        domain = "example.com"
        domain_placeholder = _static_placeholder_generation("DOMAIN", domain)
        self.assertTrue(domain_placeholder.startswith('domain-'))
        self.assertTrue(domain_placeholder.endswith('.example.com'))
        
        # Test person placeholder
        person_name = "John Smith"
        person_placeholder = _static_placeholder_generation("PERSON", person_name)
        self.assertTrue(len(person_placeholder.split()) == 2)  # Should be first and last name

    @patch('pii_transform.PRESIDIO_AVAILABLE', False)
    def test_detect_and_transform_regex_only(self):
        """Test detect_and_transform with regex only (no Presidio)."""
        test_text = "Contact john@example.com or call 555-123-4567"
        transformed = detect_and_transform(test_text)
        
        # Email should be transformed
        self.assertNotIn("john@example.com", transformed)
        # Phone number should be transformed
        self.assertNotIn("555-123-4567", transformed)

    @patch('pii_transform.USE_PRESIDIO', True)
    @patch('pii_transform.analyzer')
    @patch('pii_transform.anonymizer')
    def test_transform_with_presidio(self, mock_anonymizer, mock_analyzer):
        """Test transformation using Presidio."""
        # Mock analyzer to return some recognized entities
        mock_results = [
            MagicMock(entity_type="EMAIL", start=8, end=24, score=0.85),
            MagicMock(entity_type="PHONE_NUMBER", start=33, end=45, score=0.9)
        ]
        mock_analyzer.analyze.return_value = mock_results
        
        # Mock anonymizer to return a transformed text
        mock_anonymizer.anonymize.return_value = MagicMock(text="Contact __EMAIL_1__ or call __PHONE_1__")
        
        test_text = "Contact john@example.com or call 555-123-4567"
        result = transform_with_presidio(test_text)
        
        self.assertEqual(result, "Contact __EMAIL_1__ or call __PHONE_1__")
        mock_analyzer.analyze.assert_called_once()
        mock_anonymizer.anonymize.assert_called_once()

    def test_transform_json(self):
        """Test transforming sensitive data in JSON."""
        test_json = {
            "user": {
                "email": "test@example.com",
                "address": {
                    "city": "New York",
                    "ip": "192.168.1.1"
                }
            },
            "api_key": "api-key-12345"
        }
        
        transformed_json = transform_json(test_json)
        
        # Check that sensitive fields were transformed
        self.assertNotEqual(transformed_json["user"]["email"], "test@example.com")
        self.assertNotEqual(transformed_json["user"]["address"]["ip"], "192.168.1.1")
        self.assertNotEqual(transformed_json["api_key"], "api-key-12345")
        
        # Check that non-sensitive fields were preserved
        self.assertEqual(transformed_json["user"]["address"]["city"], "New York")

    def test_restore_original_values(self):
        """Test restoring original values from placeholders."""
        # Create a text with our test placeholders
        transformed_text = f"Contact {self.test_mappings['test@example.com']} from IP {self.test_mappings['192.168.1.1']}"
        
        # Restore original values
        restored_text = restore_original_values(transformed_text)
        
        # Check that placeholders were replaced with original values
        self.assertIn("test@example.com", restored_text)
        self.assertIn("192.168.1.1", restored_text)
        self.assertNotIn(self.test_mappings['test@example.com'], restored_text)
        self.assertNotIn(self.test_mappings['192.168.1.1'], restored_text)

    def test_restore_json_values(self):
        """Test restoring original values in JSON data."""
        # Create a JSON with our test placeholders
        transformed_json = {
            "user": {
                "email": self.test_mappings['test@example.com'],
                "address": {
                    "ip": self.test_mappings['192.168.1.1']
                }
            },
            "api_key": self.test_mappings['api-key-12345']
        }
        
        # Restore original values
        restored_json = restore_json_values(transformed_json)
        
        # Check that placeholders were replaced with original values
        self.assertEqual(restored_json["user"]["email"], "test@example.com")
        self.assertEqual(restored_json["user"]["address"]["ip"], "192.168.1.1")
        self.assertEqual(restored_json["api_key"], "api-key-12345")

    def test_get_db_connection_pii(self):
        """Test database connection function."""
        conn = get_db_connection_pii()
        self.assertIsNotNone(conn)
        
        # Test that we can execute a query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        self.assertEqual(result[0], 1)


if __name__ == '__main__':
    unittest.main()