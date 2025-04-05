"""
Unit tests for codename_generator.py module.
"""

import unittest
import json
import os
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import sys
import hashlib

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codename_generator import (
    initialize_db,
    detect_industry,
    generate_organization_codename,
    get_organization_codename,
    get_domain_codename,
    export_mappings,
    import_mappings,
    ADJECTIVES,
    TECH_NOUNS,
    INDUSTRY_PREFIXES
)


class TestCodenameGenerator(unittest.TestCase):
    """Test cases for codename generator functions."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary database for testing
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        self.original_db_path = 'data/codename_mappings.db'
        
        # Patch the DB_PATH to use our temporary database
        self.db_path_patcher = patch('codename_generator.DB_PATH', self.temp_db_path)
        self.db_path_mock = self.db_path_patcher.start()
        
        # Initialize the test database
        initialize_db()
        
        # Add some test mappings
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        # Add organization mappings
        cursor.execute('''
        INSERT INTO organization_mappings 
        (original, codename, industry, created_at, last_used)
        VALUES (?, ?, ?, ?, ?)
        ''', ('microsoft', 'TechShield', 'software', '2023-01-01T00:00:00', '2023-01-01T00:00:00'))
        
        cursor.execute('''
        INSERT INTO organization_mappings 
        (original, codename, industry, created_at, last_used)
        VALUES (?, ?, ?, ?, ?)
        ''', ('sentinelone', 'CyberGuardian', 'security', '2023-01-01T00:00:00', '2023-01-01T00:00:00'))
        
        # Add domain mappings
        cursor.execute('''
        INSERT INTO domain_mappings 
        (original, codename, organization_id, created_at, last_used)
        VALUES (?, ?, ?, ?, ?)
        ''', ('microsoft.com', 'techshield-123abc.example.com', 'microsoft', 
              '2023-01-01T00:00:00', '2023-01-01T00:00:00'))
        
        cursor.execute('''
        INSERT INTO domain_mappings 
        (original, codename, organization_id, created_at, last_used)
        VALUES (?, ?, ?, ?, ?)
        ''', ('sentinelone.net', 'cyberguardian-456def.example.com', 'sentinelone', 
              '2023-01-01T00:00:00', '2023-01-01T00:00:00'))
        
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up after tests."""
        self.db_path_patcher.stop()
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)

    def test_initialize_db(self):
        """Test database initialization."""
        # Create a new temporary database
        temp_fd, temp_path = tempfile.mkstemp()
        os.close(temp_fd)
        
        # Patch DB_PATH to use this new database
        with patch('codename_generator.DB_PATH', temp_path):
            initialize_db()
            
            # Verify tables were created
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            
            # Check organization_mappings table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organization_mappings'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check domain_mappings table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='domain_mappings'")
            self.assertIsNotNone(cursor.fetchone())
            
            conn.close()
        
        # Clean up
        os.unlink(temp_path)

    def test_detect_industry(self):
        """Test industry detection from organization names."""
        test_cases = [
            ('Microsoft Corporation', 'software'),
            ('SentinelOne, Inc.', 'security'),
            ('Google Cloud', 'cloud'),
            ('Amazon Web Services', 'cloud'),
            ('Apple Inc.', 'software'),  # Default to software if no specific match
            ('Bank of America', 'finance'),
            ('Healthcare Partners', 'healthcare'),
            ('Retail Solutions', 'retail'),
            ('Manufacturing Systems', 'manufacturing'),
            ('Telecom Services', 'telecom'),
            ('Energy Solutions', 'energy'),
            ('Transport Logistics', 'transportation'),
            ('Media Group', 'media'),
            ('Gaming Entertainment', 'gaming'),
            ('Unknown Company', 'software')  # Default to software
        ]
        
        for org_name, expected_industry in test_cases:
            detected = detect_industry(org_name)
            self.assertEqual(detected, expected_industry, f"Failed for {org_name}")

    def test_generate_organization_codename(self):
        """Test generating organization codenames."""
        # Test with specific industry
        org_name = "Test Security"
        industry = "security"
        
        # Use a fixed seed for deterministic testing
        with patch('random.seed') as mock_seed, \
             patch('random.choice') as mock_choice:
            
            # Mock random.choice to return predictable values
            mock_choice.side_effect = ["Cyber", "Shield"]
            
            codename = generate_organization_codename(org_name, industry)
            
            # Verify the result
            self.assertEqual(codename, "CyberShield")
            
            # Verify that random.seed was called with a hash of the org name
            mock_seed.assert_called()
            
            # Verify that random.choice was called with the security prefixes and tech nouns
            mock_choice.assert_any_call(INDUSTRY_PREFIXES["security"])
            mock_choice.assert_any_call(TECH_NOUNS)

    def test_generate_organization_codename_consistency(self):
        """Test that organization codenames are consistent for the same input."""
        org_name = "Consistent Organization"
        
        # Generate codename twice with the same input
        codename1 = generate_organization_codename(org_name)
        codename2 = generate_organization_codename(org_name)
        
        # Verify that both calls return the same codename
        self.assertEqual(codename1, codename2)
        
        # Test with a different organization name
        different_org = "Different Organization"
        different_codename = generate_organization_codename(different_org)
        
        # Verify that a different input produces a different output
        self.assertNotEqual(codename1, different_codename)

    def test_get_organization_codename_existing(self):
        """Test retrieving an existing organization codename."""
        # Test with an organization that's already in the database
        codename = get_organization_codename("microsoft")
        self.assertEqual(codename, "TechShield")
        
        codename = get_organization_codename("sentinelone")
        self.assertEqual(codename, "CyberGuardian")

    def test_get_organization_codename_new(self):
        """Test generating a new organization codename."""
        # Test with a new organization
        new_org = "New Company"
        
        # Mock generate_organization_codename to return a predictable value
        with patch('codename_generator.generate_organization_codename', return_value="TestCodename"):
            codename = get_organization_codename(new_org)
            self.assertEqual(codename, "TestCodename")
            
            # Verify it was stored in the database
            conn = sqlite3.connect(self.temp_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT codename FROM organization_mappings WHERE original = ?", (new_org.lower(),))
            result = cursor.fetchone()
            conn.close()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0], "TestCodename")

    def test_get_domain_codename_existing(self):
        """Test retrieving an existing domain codename."""
        # Test with a domain that's already in the database
        codename = get_domain_codename("microsoft.com")
        self.assertEqual(codename, "techshield-123abc.example.com")
        
        codename = get_domain_codename("sentinelone.net")
        self.assertEqual(codename, "cyberguardian-456def.example.com")

    def test_get_domain_codename_new_with_org(self):
        """Test generating a new domain codename with associated organization."""
        # Test with a new domain associated with an existing organization
        new_domain = "products.microsoft.com"
        
        codename = get_domain_codename(new_domain)
        
        # Verify the codename format
        self.assertTrue(codename.startswith("techshield-"))
        self.assertTrue(codename.endswith(".example.com"))
        
        # Verify it was stored in the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT codename, organization_id FROM domain_mappings WHERE original = ?", (new_domain,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], codename)
        self.assertEqual(result[1], "microsoft")  # Should be associated with Microsoft

    def test_get_domain_codename_new_without_org(self):
        """Test generating a new domain codename without associated organization."""
        # Test with a new domain not associated with any known organization
        new_domain = "example.org"
        
        codename = get_domain_codename(new_domain)
        
        # Verify the codename format
        self.assertTrue(codename.startswith("domain-"))
        self.assertTrue(codename.endswith(".example.com"))
        
        # Verify it was stored in the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT codename, organization_id FROM domain_mappings WHERE original = ?", (new_domain,))
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], codename)
        self.assertIsNone(result[1])  # Should not be associated with any organization

    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_export_mappings(self, mock_json_dump, mock_file):
        """Test exporting mappings to a JSON file."""
        output_file = 'test_export.json'
        
        result = export_mappings(output_file)
        
        # Verify the result
        self.assertEqual(result, output_file)
        
        # Verify that open was called with the correct file
        mock_file.assert_called_once_with(output_file, 'w')
        
        # Verify that json.dump was called
        mock_json_dump.assert_called_once()
        
        # Verify the structure of the exported data
        export_data = mock_json_dump.call_args[0][0]
        self.assertIn('organizations', export_data)
        self.assertIn('domains', export_data)
        self.assertIn('export_date', export_data)
        
        # Verify that our test mappings are included
        self.assertIn('microsoft', export_data['organizations'])
        self.assertEqual(export_data['organizations']['microsoft']['codename'], 'TechShield')
        self.assertIn('microsoft.com', export_data['domains'])
        self.assertEqual(export_data['domains']['microsoft.com']['codename'], 'techshield-123abc.example.com')

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=json.dumps({
        'organizations': {
            'test_org': {
                'codename': 'TestCodename',
                'industry': 'test',
                'created_at': '2023-01-01T00:00:00',
                'last_used': '2023-01-01T00:00:00'
            }
        },
        'domains': {
            'test.com': {
                'codename': 'test-domain.example.com',
                'organization_id': 'test_org',
                'created_at': '2023-01-01T00:00:00',
                'last_used': '2023-01-01T00:00:00'
            }
        }
    }))
    def test_import_mappings(self, mock_file, mock_exists):
        """Test importing mappings from a JSON file."""
        mock_exists.return_value = True
        input_file = 'test_import.json'
        
        success, message = import_mappings(input_file)
        
        # Verify the result
        self.assertTrue(success)
        self.assertIn("Successfully imported", message)
        
        # Verify that the mappings were imported into the database
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        
        # Check organization mapping
        cursor.execute("SELECT codename FROM organization_mappings WHERE original = ?", ('test_org',))
        org_result = cursor.fetchone()
        self.assertIsNotNone(org_result)
        self.assertEqual(org_result[0], 'TestCodename')
        
        # Check domain mapping
        cursor.execute("SELECT codename FROM domain_mappings WHERE original = ?", ('test.com',))
        domain_result = cursor.fetchone()
        self.assertIsNotNone(domain_result)
        self.assertEqual(domain_result[0], 'test-domain.example.com')
        
        conn.close()

    @patch('os.path.exists')
    def test_import_mappings_file_not_found(self, mock_exists):
        """Test importing mappings when file doesn't exist."""
        mock_exists.return_value = False
        input_file = 'nonexistent.json'
        
        success, message = import_mappings(input_file)
        
        # Verify the result
        self.assertFalse(success)
        self.assertIn("File not found", message)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"invalid": "format"}')
    def test_import_mappings_invalid_format(self, mock_file, mock_exists):
        """Test importing mappings with invalid format."""
        mock_exists.return_value = True
        input_file = 'invalid_format.json'
        
        success, message = import_mappings(input_file)
        
        # Verify the result
        self.assertFalse(success)
        self.assertIn("Invalid import file format", message)


if __name__ == '__main__':
    unittest.main()