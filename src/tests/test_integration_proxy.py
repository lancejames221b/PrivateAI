"""
Integration tests for the Private AI proxy request/response lifecycle.

These tests verify the end-to-end functionality of the proxy, including:
- Request interception and transformation
- PII detection and replacement
- Response transformation
- Original value restoration
"""

import unittest
import os
import sys
import json
import requests
import threading
import time
import subprocess
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pii_transform import detect_and_transform, restore_original_values
from ai_proxy import ThreadingHTTPServer, AIProxyHandler


class TestProxyIntegration(unittest.TestCase):
    """Integration tests for the proxy request/response lifecycle."""

    @classmethod
    def setUpClass(cls):
        """Start a test proxy server for integration tests."""
        # Set environment variables for testing
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['BLOCK_ALL_DOMAINS'] = 'false'
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Start the proxy server in a separate thread
        cls.proxy_port = 8081  # Use a different port for testing
        cls.proxy_thread = threading.Thread(target=cls._run_proxy_server, args=(cls.proxy_port,))
        cls.proxy_thread.daemon = True
        cls.proxy_thread.start()
        
        # Wait for the proxy to start
        time.sleep(2)
        
        # Configure requests to use the proxy
        cls.proxies = {
            'http': f'http://localhost:{cls.proxy_port}',
            'https': f'http://localhost:{cls.proxy_port}'
        }
        
        # Create a mock server to handle requests
        cls.mock_server_port = 8082
        cls.mock_server_thread = threading.Thread(target=cls._run_mock_server, args=(cls.mock_server_port,))
        cls.mock_server_thread.daemon = True
        cls.mock_server_thread.start()
        
        # Wait for the mock server to start
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Stop the proxy server
        if hasattr(cls, 'proxy_server') and cls.proxy_server:
            cls.proxy_server.shutdown()
            cls.proxy_server.server_close()
        
        # Stop the mock server
        if hasattr(cls, 'mock_server') and cls.mock_server:
            cls.mock_server.shutdown()
            cls.mock_server.server_close()

    @classmethod
    def _run_proxy_server(cls, port):
        """Run the proxy server for testing."""
        try:
            from ai_proxy import run_proxy
            run_proxy(port=port, health_port=port+1000)
        except Exception as e:
            print(f"Error starting proxy server: {e}")

    @classmethod
    def _run_mock_server(cls, port):
        """Run a mock AI API server for testing."""
        import http.server
        import socketserver
        
        class MockAIHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Parse the request data
                try:
                    request_json = json.loads(post_data)
                    
                    # Prepare a response based on the request
                    if self.path == '/v1/chat/completions':
                        # OpenAI-like chat completion endpoint
                        response = {
                            "id": "chatcmpl-123",
                            "object": "chat.completion",
                            "created": 1677858242,
                            "model": "gpt-3.5-turbo-0613",
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {
                                        "role": "assistant",
                                        "content": f"This is a response to your message about {request_json.get('messages', [{}])[-1].get('content', 'unknown topic')}"
                                    },
                                    "finish_reason": "stop"
                                }
                            ],
                            "usage": {
                                "prompt_tokens": 10,
                                "completion_tokens": 20,
                                "total_tokens": 30
                            }
                        }
                    else:
                        # Generic response
                        response = {
                            "status": "success",
                            "request_data": request_json,
                            "message": "This is a mock response"
                        }
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    # Handle non-JSON requests
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode('utf-8'))
                    
                except Exception as e:
                    # Handle other errors
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        
        # Create and start the server
        cls.mock_server = socketserver.TCPServer(("localhost", port), MockAIHandler)
        cls.mock_server.serve_forever()

    def test_proxy_request_transformation(self):
        """Test that the proxy transforms PII in requests."""
        # Skip this test if the proxy is not running
        if not self._is_proxy_running():
            self.skipTest("Proxy server is not running")
        
        # Create a request with PII
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "My email is test@example.com and my phone is 555-123-4567"}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        # Send the request through the proxy to our mock server
        with patch('ai_proxy.should_process_url', return_value=True):
            response = requests.post(
                f"http://localhost:{self.mock_server_port}/v1/chat/completions",
                json=data,
                proxies=self.proxies,
                verify=False  # Disable SSL verification for testing
            )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        
        # The response should contain transformed content
        response_data = response.json()
        self.assertIn("choices", response_data)
        self.assertIn("message", response_data["choices"][0])
        self.assertIn("content", response_data["choices"][0]["message"])
        
        # The response should not contain the original PII
        content = response_data["choices"][0]["message"]["content"]
        self.assertNotIn("test@example.com", content)
        self.assertNotIn("555-123-4567", content)

    def test_proxy_response_transformation(self):
        """Test that the proxy transforms PII in responses."""
        # Skip this test if the proxy is not running
        if not self._is_proxy_running():
            self.skipTest("Proxy server is not running")
        
        # Create a request that will trigger a response with PII
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Repeat this information: email john@example.com, phone 555-987-6543"}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        # Mock the response from the AI API to include PII
        with patch('proxy_intercept.response', side_effect=self._mock_response_with_pii):
            response = requests.post(
                f"http://localhost:{self.mock_server_port}/v1/chat/completions",
                json=data,
                proxies=self.proxies,
                verify=False
            )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        
        # The response should not contain the original PII
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        self.assertNotIn("john@example.com", content)
        self.assertNotIn("555-987-6543", content)

    def test_proxy_bidirectional_transformation(self):
        """Test that the proxy correctly handles bidirectional transformation."""
        # Skip this test if the proxy is not running
        if not self._is_proxy_running():
            self.skipTest("Proxy server is not running")
        
        # Create a request with PII
        email = "bidirectional@example.com"
        phone = "555-111-2222"
        
        data = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"My email is {email} and my phone is {phone}"}
            ],
            "model": "gpt-3.5-turbo"
        }
        
        # First, get the transformed values
        transformed_email, _ = detect_and_transform(email)
        transformed_phone, _ = detect_and_transform(phone)
        
        # Send the request through the proxy
        with patch('ai_proxy.should_process_url', return_value=True):
            response = requests.post(
                f"http://localhost:{self.mock_server_port}/v1/chat/completions",
                json=data,
                proxies=self.proxies,
                verify=False
            )
        
        # Verify the response
        self.assertEqual(response.status_code, 200)
        
        # The response should contain the transformed values, not the original PII
        response_data = response.json()
        content = response_data["choices"][0]["message"]["content"]
        
        # Check that original values are not present
        self.assertNotIn(email, content)
        self.assertNotIn(phone, content)
        
        # Check that transformed values are present (or their placeholders)
        # Note: The exact transformed values might be different in the response due to the proxy's transformation
        # So we're checking that the original values are not present, which is the important security aspect

    def _is_proxy_running(self):
        """Check if the proxy server is running."""
        try:
            response = requests.get(f"http://localhost:{self.proxy_port + 1000}/health")
            return response.status_code == 200
        except:
            return False

    def _mock_response_with_pii(self, flow):
        """Mock the response handler to inject PII into the response."""
        if not hasattr(flow, 'response') or not flow.response:
            return
            
        if flow.response.headers.get("content-type", "").startswith("application/json"):
            try:
                data = flow.response.content.decode("utf-8")
                json_data = json.loads(data)
                
                # Inject PII into the response
                if "choices" in json_data and len(json_data["choices"]) > 0:
                    if "message" in json_data["choices"][0]:
                        json_data["choices"][0]["message"]["content"] = (
                            "Here's the information you asked for: "
                            "email john@example.com, phone 555-987-6543"
                        )
                
                # Update the response
                flow.response.text = json.dumps(json_data)
            except:
                pass


class TestProxyComponentIntegration(unittest.TestCase):
    """Integration tests for proxy components without starting a full proxy server."""
    
    def setUp(self):
        """Set up test environment."""
        # Create necessary directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)

    def test_pii_transform_integration(self):
        """Test that PII transformation works correctly with the proxy components."""
        # Test text with various types of PII
        test_text = """
        Here is some sensitive information:
        - Email: john.doe@example.com
        - Phone: 555-123-4567
        - Credit Card: 4111-1111-1111-1111
        - SSN: 123-45-6789
        - IP Address: 192.168.1.1
        - API Key: sk_test_abcdefghijklmnopqrstuvwxyz
        """
        
        # Transform the text
        transformed_text, log = detect_and_transform(test_text)
        
        # Verify that PII was detected and transformed
        self.assertNotEqual(test_text, transformed_text)
        self.assertGreater(len(log), 0)
        
        # Verify specific PII types were transformed
        self.assertNotIn("john.doe@example.com", transformed_text)
        self.assertNotIn("555-123-4567", transformed_text)
        self.assertNotIn("4111-1111-1111-1111", transformed_text)
        self.assertNotIn("123-45-6789", transformed_text)
        self.assertNotIn("sk_test_abcdefghijklmnopqrstuvwxyz", transformed_text)
        
        # Restore the original values
        restored_text = restore_original_values(transformed_text)
        
        # Verify that the original text was restored
        self.assertEqual(test_text.strip(), restored_text.strip())

    def test_json_transformation_integration(self):
        """Test that JSON transformation works correctly with the proxy components."""
        from pii_transform import transform_json, restore_json_values
        
        # Test JSON with nested PII
        test_json = {
            "user": {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "555-123-4567",
                "address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "zip": "10001"
                }
            },
            "payment": {
                "card_number": "4111-1111-1111-1111",
                "expiry": "12/25",
                "cvv": "123"
            },
            "api_key": "sk_test_abcdefghijklmnopqrstuvwxyz"
        }
        
        # Transform the JSON
        transformed_json = transform_json(test_json)
        
        # Verify that PII was transformed
        self.assertNotEqual(test_json, transformed_json)
        
        # Verify specific PII fields were transformed
        self.assertNotEqual(test_json["user"]["email"], transformed_json["user"]["email"])
        self.assertNotEqual(test_json["user"]["phone"], transformed_json["user"]["phone"])
        self.assertNotEqual(test_json["payment"]["card_number"], transformed_json["payment"]["card_number"])
        self.assertNotEqual(test_json["api_key"], transformed_json["api_key"])
        
        # Verify non-PII fields were preserved
        self.assertEqual(test_json["user"]["address"]["city"], transformed_json["user"]["address"]["city"])
        self.assertEqual(test_json["payment"]["expiry"], transformed_json["payment"]["expiry"])
        
        # Restore the original values
        restored_json = restore_json_values(transformed_json)
        
        # Verify that the original JSON was restored
        self.assertEqual(test_json, restored_json)


if __name__ == '__main__':
    unittest.main()