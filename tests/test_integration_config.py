"""
Integration tests for the Private AI proxy configuration functionality.

These tests verify the configuration loading and saving functionality, including:
- Environment settings management
- AI server configurations
- Domain blocklists
- Custom pattern configurations
- Database encryption settings
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
import sqlite3
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from utils import DatabaseEncryption


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for configuration loading and saving."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Save original environment variables
        self.original_env = os.environ.copy()
        
        # Set test environment variables
        os.environ['BLOCK_ALL_DOMAINS'] = 'false'
        os.environ['USE_PRESIDIO'] = 'true'
        os.environ['ENCRYPT_DATABASE'] = 'true'
        os.environ['ENABLE_AI_INFERENCE_PROTECTION'] = 'true'
        os.environ['INFERENCE_PROTECTION_LEVEL'] = 'medium'
        
        # Create test configuration files
        self._create_test_patterns_file()
        self._create_test_domain_blocklist()
        self._create_test_ai_servers_file()
        self._create_test_ai_domains_file()

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def _create_test_patterns_file(self):
        """Create a test patterns file."""
        patterns = {
            "test_pattern": {
                "name": "test_pattern",
                "entity_type": "EMAIL",
                "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                "description": "Test email pattern",
                "is_active": True,
                "priority": "2",
                "created_at": "2023-01-01T00:00:00"
            },
            "credit_card_pattern": {
                "name": "credit_card_pattern",
                "entity_type": "CREDIT_CARD",
                "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
                "description": "Credit card number pattern",
                "is_active": True,
                "priority": "1",
                "created_at": "2023-01-01T00:00:00"
            }
        }
        
        os.makedirs(os.path.join(self.data_dir), exist_ok=True)
        with open(os.path.join(self.data_dir, 'custom_patterns.json'), 'w') as f:
            json.dump(patterns, f)

    def _create_test_domain_blocklist(self):
        """Create a test domain blocklist file."""
        domains = ["example.com", "test-domain.com", "sensitive-site.org"]
        
        with open(os.path.join(self.data_dir, 'domain_blocklist.txt'), 'w') as f:
            for domain in domains:
                f.write(f"{domain}\n")

    def _create_test_ai_servers_file(self):
        """Create a test AI servers configuration file."""
        servers = [
            {
                "name": "Test OpenAI",
                "provider": "openai",
                "base_url": "https://api.openai.com",
                "auth_type": "api_key",
                "auth_key": "Authorization",
                "auth_value": "Bearer sk_test_12345",
                "custom_headers": "{}",
                "is_active": True
            },
            {
                "name": "Test Anthropic",
                "provider": "anthropic",
                "base_url": "https://api.anthropic.com",
                "auth_type": "api_key",
                "auth_key": "x-api-key",
                "auth_value": "sk_ant_test12345",
                "custom_headers": "{}",
                "is_active": True
            }
        ]
        
        with open(os.path.join(self.data_dir, 'ai_servers.json'), 'w') as f:
            json.dump(servers, f)

    def _create_test_ai_domains_file(self):
        """Create a test AI domains configuration file."""
        domains_data = {
            "domains": [
                "api.openai.com",
                "api.anthropic.com",
                "api.gemini.google.com"
            ],
            "categories": {
                "openai": ["api.openai.com"],
                "anthropic": ["api.anthropic.com"],
                "google": ["api.gemini.google.com"]
            }
        }
        
        with open(os.path.join(self.data_dir, 'ai_domains.json'), 'w') as f:
            json.dump(domains_data, f)

    def test_env_settings_management(self):
        """Test environment settings management."""
        # Import the function to test
        from app import update_env_setting
        
        # Test updating an environment setting
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Call the function
            update_env_setting('TEST_SETTING', 'test_value')
            
            # Check that the environment variable was updated
            self.assertEqual(os.environ.get('TEST_SETTING'), 'test_value')
            
            # Check that the .env file was updated
            mock_open.assert_called()
            mock_file.write.assert_called()

    def test_custom_patterns_loading(self):
        """Test loading custom patterns from configuration file."""
        # Import the function to test
        from app import get_custom_patterns
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'custom_patterns.json')):
            # Call the function
            patterns = get_custom_patterns()
            
            # Check that the patterns were loaded correctly
            self.assertIn('test_pattern', patterns)
            self.assertIn('credit_card_pattern', patterns)
            self.assertEqual(patterns['test_pattern']['entity_type'], 'EMAIL')
            self.assertEqual(patterns['credit_card_pattern']['entity_type'], 'CREDIT_CARD')

    def test_custom_patterns_saving(self):
        """Test saving custom patterns to configuration file."""
        # Import the function to test
        from app import save_custom_patterns
        
        # Create modified patterns
        modified_patterns = {
            "test_pattern": {
                "name": "test_pattern",
                "entity_type": "EMAIL",
                "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                "description": "Modified description",  # Changed
                "is_active": False,  # Changed
                "priority": "3",  # Changed
                "created_at": "2023-01-01T00:00:00"
            },
            "new_pattern": {  # New pattern
                "name": "new_pattern",
                "entity_type": "PHONE_NUMBER",
                "pattern": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                "description": "Phone number pattern",
                "is_active": True,
                "priority": "2",
                "created_at": "2023-02-01T00:00:00"
            }
        }
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'custom_patterns.json')):
            # Call the function
            save_custom_patterns(modified_patterns)
            
            # Read the file to verify changes
            with open(os.path.join(self.data_dir, 'custom_patterns.json'), 'r') as f:
                saved_patterns = json.load(f)
            
            # Check that the patterns were saved correctly
            self.assertIn('test_pattern', saved_patterns)
            self.assertIn('new_pattern', saved_patterns)
            self.assertEqual(saved_patterns['test_pattern']['description'], 'Modified description')
            self.assertEqual(saved_patterns['test_pattern']['is_active'], False)
            self.assertEqual(saved_patterns['test_pattern']['priority'], '3')
            self.assertEqual(saved_patterns['new_pattern']['entity_type'], 'PHONE_NUMBER')

    def test_domain_blocklist_loading(self):
        """Test loading domain blocklist from configuration file."""
        # Import the function to test
        from utils import get_domain_blocklist
        
        # Patch the file path to use our test file
        with patch('utils.os.path.join', return_value=os.path.join(self.data_dir, 'domain_blocklist.txt')):
            # Call the function
            domains = get_domain_blocklist()
            
            # Check that the domains were loaded correctly
            self.assertIn('example.com', domains)
            self.assertIn('test-domain.com', domains)
            self.assertIn('sensitive-site.org', domains)

    def test_domain_blocklist_saving(self):
        """Test saving domain blocklist to configuration file."""
        # Import the function to test
        from app import save_domain_blocklist
        
        # Create modified domains list
        modified_domains = [
            "example.com",
            "new-domain.com",  # Added
            "another-domain.org"  # Added
        ]
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'domain_blocklist.txt')):
            # Call the function
            save_domain_blocklist(modified_domains)
            
            # Read the file to verify changes
            with open(os.path.join(self.data_dir, 'domain_blocklist.txt'), 'r') as f:
                saved_domains = [line.strip() for line in f if line.strip()]
            
            # Check that the domains were saved correctly
            self.assertIn('example.com', saved_domains)
            self.assertIn('new-domain.com', saved_domains)
            self.assertIn('another-domain.org', saved_domains)
            self.assertNotIn('test-domain.com', saved_domains)  # Removed
            self.assertNotIn('sensitive-site.org', saved_domains)  # Removed

    def test_ai_servers_loading(self):
        """Test loading AI server configurations from file."""
        # Import the function to test
        from app import load_ai_servers
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'ai_servers.json')):
            # Call the function
            servers = load_ai_servers()
            
            # Check that the servers were loaded correctly
            self.assertEqual(len(servers), 2)
            self.assertEqual(servers[0]['name'], 'Test OpenAI')
            self.assertEqual(servers[1]['name'], 'Test Anthropic')
            self.assertEqual(servers[0]['provider'], 'openai')
            self.assertEqual(servers[1]['provider'], 'anthropic')

    def test_ai_servers_saving(self):
        """Test saving AI server configurations to file."""
        # Import the function to test
        from app import save_ai_servers
        
        # Create modified servers list
        modified_servers = [
            {
                "name": "Test OpenAI",
                "provider": "openai",
                "base_url": "https://api.openai.com/v2",  # Changed
                "auth_type": "api_key",
                "auth_key": "Authorization",
                "auth_value": "Bearer sk_test_updated",  # Changed
                "custom_headers": "{}",
                "is_active": True
            },
            {
                "name": "Test Google",  # New server
                "provider": "google",
                "base_url": "https://api.gemini.google.com",
                "auth_type": "api_key",
                "auth_key": "x-goog-api-key",
                "auth_value": "test_key_12345",
                "custom_headers": "{}",
                "is_active": True
            }
        ]
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'ai_servers.json')):
            # Call the function
            save_ai_servers(modified_servers)
            
            # Read the file to verify changes
            with open(os.path.join(self.data_dir, 'ai_servers.json'), 'r') as f:
                saved_servers = json.load(f)
            
            # Check that the servers were saved correctly
            self.assertEqual(len(saved_servers), 2)
            self.assertEqual(saved_servers[0]['name'], 'Test OpenAI')
            self.assertEqual(saved_servers[0]['base_url'], 'https://api.openai.com/v2')
            self.assertEqual(saved_servers[0]['auth_value'], 'Bearer sk_test_updated')
            self.assertEqual(saved_servers[1]['name'], 'Test Google')
            self.assertEqual(saved_servers[1]['provider'], 'google')

    def test_ai_domains_loading(self):
        """Test loading AI domains from configuration file."""
        # Import the function to test
        from app import load_ai_domains
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'ai_domains.json')):
            # Call the function
            domains_data = load_ai_domains()
            
            # Check that the domains were loaded correctly
            self.assertIn('domains', domains_data)
            self.assertIn('categories', domains_data)
            self.assertEqual(len(domains_data['domains']), 3)
            self.assertIn('api.openai.com', domains_data['domains'])
            self.assertIn('api.anthropic.com', domains_data['domains'])
            self.assertIn('api.gemini.google.com', domains_data['domains'])
            self.assertEqual(len(domains_data['categories']), 3)
            self.assertIn('openai', domains_data['categories'])
            self.assertIn('anthropic', domains_data['categories'])
            self.assertIn('google', domains_data['categories'])

    def test_ai_domains_saving(self):
        """Test saving AI domains to configuration file."""
        # Import the function to test
        from app import save_ai_domains
        
        # Create modified domains data
        modified_domains_data = {
            "domains": [
                "api.openai.com",
                "api.mistral.ai",  # Added
                "api.together.xyz"  # Added
            ],
            "categories": {
                "openai": ["api.openai.com"],
                "emerging": ["api.mistral.ai", "api.together.xyz"]  # Added
            }
        }
        
        # Patch the file path to use our test file
        with patch('app.os.path.join', return_value=os.path.join(self.data_dir, 'ai_domains.json')):
            # Call the function
            save_ai_domains(modified_domains_data)
            
            # Read the file to verify changes
            with open(os.path.join(self.data_dir, 'ai_domains.json'), 'r') as f:
                saved_domains_data = json.load(f)
            
            # Check that the domains were saved correctly
            self.assertIn('domains', saved_domains_data)
            self.assertIn('categories', saved_domains_data)
            self.assertEqual(len(saved_domains_data['domains']), 3)
            self.assertIn('api.openai.com', saved_domains_data['domains'])
            self.assertIn('api.mistral.ai', saved_domains_data['domains'])
            self.assertIn('api.together.xyz', saved_domains_data['domains'])
            self.assertNotIn('api.anthropic.com', saved_domains_data['domains'])  # Removed
            self.assertNotIn('api.gemini.google.com', saved_domains_data['domains'])  # Removed
            self.assertIn('openai', saved_domains_data['categories'])
            self.assertIn('emerging', saved_domains_data['categories'])
            self.assertNotIn('anthropic', saved_domains_data['categories'])  # Removed
            self.assertNotIn('google', saved_domains_data['categories'])  # Removed

    def test_database_encryption(self):
        """Test database encryption functionality."""
        # Create a test database
        db_path = os.path.join(self.data_dir, 'test_encryption.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create a table
        cursor.execute('''
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            sensitive_data TEXT
        )
        ''')
        
        # Insert some test data
        cursor.execute("INSERT INTO test_table VALUES (1, 'sensitive information')")
        conn.commit()
        conn.close()
        
        # Create a DatabaseEncryption instance
        db_encryption = DatabaseEncryption()
        
        # Test encryption
        sensitive_data = "This is sensitive information"
        encrypted_data = db_encryption.encrypt(sensitive_data)
        
        # Verify that the data was encrypted
        self.assertNotEqual(sensitive_data, encrypted_data)
        
        # Test decryption
        decrypted_data = db_encryption.decrypt(encrypted_data)
        
        # Verify that the data was correctly decrypted
        self.assertEqual(sensitive_data, decrypted_data)
        
        # Test with different encryption key
        different_key = Fernet.generate_key()
        with patch.object(db_encryption, '_encryption_key', different_key):
            # Attempt to decrypt with a different key should fail
            with self.assertRaises(Exception):
                db_encryption.decrypt(encrypted_data)


class TestConfigLoadingOrder(unittest.TestCase):
    """Tests for configuration loading order and precedence."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directories for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Save original environment variables
        self.original_env = os.environ.copy()
        
        # Create a test .env file
        self.env_file = os.path.join(self.temp_dir, '.env')
        with open(self.env_file, 'w') as f:
            f.write("TEST_SETTING=env_file_value\n")
            f.write("OVERRIDE_SETTING=env_file_value\n")

    def tearDown(self):
        """Clean up after tests."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def test_config_loading_precedence(self):
        """Test that configuration loading respects precedence order."""
        # Set an environment variable that should override the .env file
        os.environ['OVERRIDE_SETTING'] = 'environment_value'
        
        # Import the app module with patched .env file path
        with patch('dotenv.find_dotenv', return_value=self.env_file):
            with patch('dotenv.load_dotenv'):
                # Force reload of app module to apply patched .env
                if 'app' in sys.modules:
                    del sys.modules['app']
                import app
                
                # Check that the .env file value was loaded
                self.assertEqual(os.environ.get('TEST_SETTING'), 'env_file_value')
                
                # Check that the environment variable overrides the .env file
                self.assertEqual(os.environ.get('OVERRIDE_SETTING'), 'environment_value')

    def test_default_settings_fallback(self):
        """Test that default settings are used when not specified elsewhere."""
        # Import the app module with patched .env file path
        with patch('dotenv.find_dotenv', return_value=self.env_file):
            with patch('dotenv.load_dotenv'):
                # Force reload of app module to apply patched .env
                if 'app' in sys.modules:
                    del sys.modules['app']
                
                # Patch the default privacy settings
                test_defaults = {
                    'DEFAULT_SETTING': 'default_value',
                    'TEST_SETTING': 'default_value_should_not_be_used'  # Should be overridden by .env
                }
                
                with patch('app.default_privacy_settings', test_defaults):
                    import app
                    
                    # Check that the default value was used for the unspecified setting
                    self.assertEqual(os.environ.get('DEFAULT_SETTING'), 'default_value')
                    
                    # Check that the .env file value overrides the default
                    self.assertEqual(os.environ.get('TEST_SETTING'), 'env_file_value')


if __name__ == '__main__':
    unittest.main()