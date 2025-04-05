"""
Integration tests for the Private AI proxy API endpoints.

These tests verify the functionality of the API endpoints in app.py, including:
- Configuration management endpoints
- PII transformation endpoints
- Proxy control endpoints
- Domain and pattern management endpoints
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import BytesIO

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Flask app and create a test client
from app import app


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for the API endpoints."""

    def setUp(self):
        """Set up test environment."""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['BASIC_AUTH_FORCE'] = False  # Disable basic auth for testing
        
        # Create a test client
        self.client = app.test_client()
        
        # Create temporary directories for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.temp_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Patch the database path to use our temporary directory
        self.db_path_patcher = patch('app.get_db_connection', self._get_test_db_connection)
        self.db_path_mock = self.db_path_patcher.start()
        
        # Initialize test database
        self._initialize_test_db()
        
        # Create test patterns file
        self._create_test_patterns_file()
        
        # Create test domain blocklist file
        self._create_test_domain_blocklist()
        
        # Create test AI servers file
        self._create_test_ai_servers_file()
        
        # Create test AI domains file
        self._create_test_ai_domains_file()

    def tearDown(self):
        """Clean up after tests."""
        # Stop patchers
        self.db_path_patcher.stop()
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)

    def _get_test_db_connection(self):
        """Get a connection to the test database."""
        import sqlite3
        conn = sqlite3.connect(os.path.join(self.data_dir, 'mapping_store.db'))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_test_db(self):
        """Initialize the test database with sample data."""
        import sqlite3
        conn = sqlite3.connect(os.path.join(self.data_dir, 'mapping_store.db'))
        cursor = conn.cursor()
        
        # Create mappings table
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
        
        # Add some test mappings
        test_mappings = [
            ('test@example.com', '__EMAIL_12345678__', 'EMAIL', '2023-01-01T00:00:00', '2023-01-01T00:00:00', 0),
            ('192.168.1.1', '__IP_87654321__', 'IP_ADDRESS', '2023-01-01T00:00:00', '2023-01-01T00:00:00', 0),
            ('api-key-12345', '__API_KEY_abcdef12__', 'API_KEY', '2023-01-01T00:00:00', '2023-01-01T00:00:00', 0)
        ]
        
        for mapping in test_mappings:
            cursor.execute(
                "INSERT OR REPLACE INTO mappings VALUES (?, ?, ?, ?, ?, ?)",
                mapping
            )
        
        conn.commit()
        conn.close()

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

    def test_api_stats_endpoint(self):
        """Test the /api/stats endpoint."""
        # Mock the is_proxy_running function to return True
        with patch('app.is_proxy_running', return_value=True):
            response = self.client.get('/api/stats')
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Check that the response contains the expected fields
            self.assertIn('proxy_status', data)
            self.assertEqual(data['proxy_status'], 'running')
            self.assertIn('uptime', data)
            self.assertIn('requests_processed', data)
            self.assertIn('mappings_count', data)

    def test_process_text_endpoint(self):
        """Test the /api/process-text endpoint."""
        # Create test data with PII
        test_data = {
            "text": "My email is test@example.com and my phone is 555-123-4567",
            "action": "transform"
        }
        
        # Test transformation
        response = self.client.post(
            '/api/process-text',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check that the text was transformed
        self.assertIn('transformed_text', data)
        self.assertNotIn('test@example.com', data['transformed_text'])
        
        # Test restoration
        test_data["action"] = "restore"
        test_data["text"] = data['transformed_text']
        
        response = self.client.post(
            '/api/process-text',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check that the text was restored
        self.assertIn('restored_text', data)
        self.assertIn('test@example.com', data['restored_text'])

    def test_connection_settings_endpoint(self):
        """Test the /api/connection-settings endpoint."""
        # Mock the is_proxy_running function to return True
        with patch('app.is_proxy_running', return_value=True):
            response = self.client.get('/api/connection-settings')
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Check that the response contains the expected fields
            self.assertIn('proxy_status', data)
            self.assertEqual(data['proxy_status'], 'running')
            self.assertIn('proxy_url', data)
            self.assertIn('proxy_port', data)

    def test_update_privacy_settings_endpoint(self):
        """Test the /api/update_privacy_settings endpoint."""
        # Create test settings
        test_settings = {
            "BLOCK_ALL_DOMAINS": "true",
            "USE_PRESIDIO": "true",
            "ENCRYPT_DATABASE": "true",
            "ENABLE_AI_INFERENCE_PROTECTION": "true",
            "INFERENCE_PROTECTION_LEVEL": "high"
        }
        
        # Test updating settings
        with patch('app.update_env_setting') as mock_update_env:
            response = self.client.post(
                '/api/update_privacy_settings',
                data=json.dumps(test_settings),
                content_type='application/json'
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Check that the settings were updated
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'success')
            
            # Check that update_env_setting was called for each setting
            self.assertEqual(mock_update_env.call_count, len(test_settings))

    def test_ai_servers_endpoints(self):
        """Test the AI servers management endpoints."""
        # Test listing AI servers
        response = self.client.get('/ai_servers')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test OpenAI', response.data)
        self.assertIn(b'Test Anthropic', response.data)
        
        # Test adding a new AI server
        with patch('app.save_ai_servers') as mock_save:
            new_server_data = {
                "name": "Test Google",
                "provider": "google",
                "base_url": "https://api.gemini.google.com",
                "auth_type": "api_key",
                "auth_key": "x-goog-api-key",
                "auth_value": "test_key_12345",
                "is_active": "y"  # Form checkbox value
            }
            
            response = self.client.post(
                '/ai_servers/add',
                data=new_server_data,
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_ai_servers was called
            mock_save.assert_called_once()
        
        # Test editing an AI server
        with patch('app.save_ai_servers') as mock_save:
            edit_server_data = {
                "name": "Test OpenAI",
                "provider": "openai",
                "base_url": "https://api.openai.com/v2",  # Changed URL
                "auth_type": "api_key",
                "auth_key": "Authorization",
                "auth_value": "Bearer sk_test_updated",  # Changed value
                "is_active": "y"
            }
            
            response = self.client.post(
                '/ai_servers/edit/Test OpenAI',
                data=edit_server_data,
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_ai_servers was called
            mock_save.assert_called_once()
        
        # Test deleting an AI server
        with patch('app.save_ai_servers') as mock_save:
            response = self.client.post(
                '/ai_servers/delete/Test Anthropic',
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_ai_servers was called
            mock_save.assert_called_once()

    def test_ai_domains_endpoints(self):
        """Test the AI domains management endpoints."""
        # Test listing AI domains
        response = self.client.get('/ai_domains')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'api.openai.com', response.data)
        self.assertIn(b'api.anthropic.com', response.data)
        
        # Test adding a new AI domain
        with patch('app.save_ai_domains') as mock_save:
            new_domain_data = {
                "domain": "api.mistral.ai",
                "category": "emerging",
                "description": "Mistral AI API"
            }
            
            response = self.client.post(
                '/ai_domains/add',
                data=new_domain_data,
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_ai_domains was called
            mock_save.assert_called_once()
        
        # Test deleting an AI domain
        with patch('app.save_ai_domains') as mock_save:
            response = self.client.post(
                '/ai_domains/delete/api.openai.com',
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_ai_domains was called
            mock_save.assert_called_once()
        
        # Test viewing domains by category
        response = self.client.get('/ai_domains/category/openai')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'api.openai.com', response.data)

    def test_patterns_endpoints(self):
        """Test the patterns management endpoints."""
        # Test listing patterns
        response = self.client.get('/patterns')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test_pattern', response.data)
        
        # Test adding a new pattern
        with patch('app.save_custom_patterns') as mock_save:
            new_pattern_data = {
                "name": "credit_card_pattern",
                "entity_type": "CREDIT_CARD",
                "pattern": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
                "description": "Credit card number pattern",
                "is_active": "y",
                "priority": "1"
            }
            
            response = self.client.post(
                '/add_pattern',
                data=new_pattern_data,
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_custom_patterns was called
            mock_save.assert_called_once()
        
        # Test toggling a pattern
        with patch('app.save_custom_patterns') as mock_save:
            response = self.client.get(
                '/toggle_pattern/test_pattern',
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_custom_patterns was called
            mock_save.assert_called_once()
        
        # Test deleting a pattern
        with patch('app.save_custom_patterns') as mock_save:
            response = self.client.get(
                '/delete_pattern/test_pattern',
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_custom_patterns was called
            mock_save.assert_called_once()

    def test_domains_endpoints(self):
        """Test the domains management endpoints."""
        # Test listing domains
        response = self.client.get('/domains')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'example.com', response.data)
        
        # Test adding a new domain
        with patch('app.save_domain_blocklist') as mock_save:
            new_domain_data = {
                "domain": "new-blocked-domain.com"
            }
            
            response = self.client.post(
                '/add_domain',
                data=new_domain_data,
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_domain_blocklist was called
            mock_save.assert_called_once()
        
        # Test removing a domain
        with patch('app.save_domain_blocklist') as mock_save:
            response = self.client.get(
                '/remove_domain/example.com',
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that save_domain_blocklist was called
            mock_save.assert_called_once()
        
        # Test toggling block all domains
        with patch('app.update_env_setting') as mock_update:
            response = self.client.post(
                '/toggle_block_all_domains',
                follow_redirects=True
            )
            
            # Verify the response
            self.assertEqual(response.status_code, 200)
            
            # Check that update_env_setting was called
            mock_update.assert_called_once()

    def test_mappings_endpoint(self):
        """Test the mappings management endpoint."""
        # Test listing mappings
        response = self.client.get('/mappings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test@example.com', response.data)
        self.assertIn(b'__EMAIL_12345678__', response.data)
        
        # Test deleting a mapping
        with patch('sqlite3.Connection.execute') as mock_execute:
            with patch('sqlite3.Connection.commit') as mock_commit:
                response = self.client.get(
                    '/delete_mapping/test@example.com',
                    follow_redirects=True
                )
                
                # Verify the response
                self.assertEqual(response.status_code, 200)
                
                # Check that the database operations were called
                mock_execute.assert_called_once()
                mock_commit.assert_called_once()


if __name__ == '__main__':
    unittest.main()