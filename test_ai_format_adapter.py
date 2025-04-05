"""
Private AI 🕵️ - AI Format Adapter Tests

This module provides tests for the AI format detection and adaptation functionality.
It verifies the correct detection and transformation of various IDE-based AI assistant
request and response formats.

Author: Lance James @ Unit 221B
"""

import json
import unittest
import os
import sys
from typing import Dict, Optional

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_format_adapter import AIFormatAdapter
from ai_format_detector import AIFormatDetector
from ai_format_request_adapters import AIRequestAdapters
from ai_format_response_adapters import AIResponseAdapters

class TestAIFormatAdapter(unittest.TestCase):
    """Test case for AI format adapter"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.adapter = AIFormatAdapter()
        self.detector = AIFormatDetector()
        self.request_adapters = AIRequestAdapters()
        self.response_adapters = AIResponseAdapters()
    
    def test_openai_format_detection(self):
        """Test detection of OpenAI format"""
        openai_request = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, world!"}
            ],
            "temperature": 0.7
        }
        
        format_detected = self.detector.detect_format(openai_request)
        self.assertEqual(format_detected, "openai")
    
    def test_anthropic_format_detection(self):
        """Test detection of Anthropic format"""
        anthropic_request = {
            "model": "claude-3-opus",
            "prompt": "\n\nHuman: Hello, Claude!\n\nAssistant: ",
            "max_tokens": 1024
        }
        
        format_detected = self.detector.detect_format(anthropic_request)
        self.assertEqual(format_detected, "anthropic")
        
        # Test Anthropic with messages array
        anthropic_messages_request = {
            "model": "claude-3-opus",
            "messages": [
                {"role": "human", "content": "Hello, Claude!"}
            ],
            "max_tokens": 1024
        }
        
        format_detected = self.detector.detect_format(anthropic_messages_request)
        self.assertEqual(format_detected, "anthropic")
    
    def test_github_copilot_format_detection(self):
        """Test detection of GitHub Copilot format"""
        copilot_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getCompletions",
            "params": {
                "doc": {
                    "source": "function hello() {\n    return 'Hello,'\n}",
                    "prefix": "function hello() {\n    return 'Hello,",
                    "suffix": "'\n}",
                    "position": {
                        "line": 1,
                        "character": 24
                    },
                    "uri": "file:///project/test.js"
                }
            }
        }
        
        format_detected = self.detector.detect_format(copilot_request)
        self.assertEqual(format_detected, "github-copilot")
    
    def test_cursor_format_detection(self):
        """Test detection of Cursor AI format"""
        cursor_request = {
            "prompt": "How do I implement a binary search tree in Python?",
            "context": "class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None",
            "temperature": 0.7
        }
        
        format_detected = self.detector.detect_format(cursor_request)
        self.assertEqual(format_detected, "cursor")
    
    def test_jetbrains_format_detection(self):
        """Test detection of JetBrains AI format"""
        jetbrains_request = {
            "query": "How do I implement a binary search tree in Java?",
            "context": "class Node {\n    int value;\n    Node left;\n    Node right;\n    \n    Node(int value) {\n        this.value = value;\n        this.left = null;\n        this.right = null;\n    }\n}",
            "intellijPlugin": "true"
        }
        
        format_detected = self.detector.detect_format(jetbrains_request)
        self.assertEqual(format_detected, "jetbrains")
    
    def test_vscode_format_detection(self):
        """Test detection of VS Code format"""
        vscode_request = {
            "text": "How do I implement a binary search tree in TypeScript?",
            "files": [
                {
                    "name": "bst.ts",
                    "content": "class Node {\n    value: number;\n    left: Node | null;\n    right: Node | null;\n    \n    constructor(value: number) {\n        this.value = value;\n        this.left = null;\n        this.right = null;\n    }\n}"
                }
            ]
        }
        
        format_detected = self.detector.detect_format(vscode_request)
        self.assertEqual(format_detected, "vscode")
    
    def test_anthropic_format_adaptation(self):
        """Test adaptation of Anthropic format to OpenAI"""
        anthropic_request = {
            "model": "claude-3-opus",
            "prompt": "\n\nHuman: Hello, Claude!\n\nAssistant: ",
            "max_tokens": 1024
        }
        
        adapted_data = self.request_adapters.adapt_from_anthropic(anthropic_request)
        
        # Check that the adaptation created a valid OpenAI format
        self.assertIn("messages", adapted_data)
        self.assertEqual(len(adapted_data["messages"]), 1)
        self.assertEqual(adapted_data["messages"][0]["role"], "user")
        self.assertEqual(adapted_data["messages"][0]["content"], "Hello, Claude!")
    
    def test_github_copilot_format_adaptation(self):
        """Test adaptation of GitHub Copilot format to OpenAI"""
        copilot_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getCompletions",
            "params": {
                "doc": {
                    "source": "function hello() {\n    return 'Hello,'\n}",
                    "prefix": "function hello() {\n    return 'Hello,",
                    "suffix": "'\n}",
                    "uri": "file:///project/test.js"
                }
            }
        }
        
        adapted_data = self.request_adapters.adapt_from_github_copilot(copilot_request)
        
        # Check that the adaptation created a valid OpenAI format
        self.assertIn("messages", adapted_data)
        self.assertIn("model", adapted_data)
        self.assertEqual(len(adapted_data["messages"]), 2)
        self.assertEqual(adapted_data["messages"][0]["role"], "system")
        self.assertEqual(adapted_data["messages"][1]["role"], "user")
    
    def test_cursor_format_adaptation(self):
        """Test adaptation of Cursor AI format to OpenAI"""
        cursor_request = {
            "prompt": "How do I implement a binary search tree in Python?",
            "context": "class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None",
            "temperature": 0.7
        }
        
        adapted_data = self.request_adapters.adapt_from_cursor(cursor_request)
        
        # Check that the adaptation created a valid OpenAI format
        self.assertIn("messages", adapted_data)
        self.assertIn("model", adapted_data)
        self.assertGreaterEqual(len(adapted_data["messages"]), 2)
        self.assertEqual(adapted_data["messages"][0]["role"], "system")
        self.assertIn("content", adapted_data["messages"][-1])
    
    def test_openai_response_adaptation_to_github_copilot(self):
        """Test adaptation of OpenAI response to GitHub Copilot format"""
        openai_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "gpt-4",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "```javascript\nfunction hello() {\n    return 'Hello, World!';\n}\n```"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
        
        adapted_response = self.response_adapters.adapt_to_github_copilot(openai_response)
        
        # Check that the adaptation created a valid GitHub Copilot response
        self.assertIn("jsonrpc", adapted_response)
        self.assertIn("result", adapted_response)
        self.assertIn("completions", adapted_response["result"])
        self.assertEqual(len(adapted_response["result"]["completions"]), 1)
        self.assertIn("text", adapted_response["result"]["completions"][0])
    
    def test_openai_response_adaptation_to_cursor(self):
        """Test adaptation of OpenAI response to Cursor format"""
        openai_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "gpt-4",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Here's a binary search tree implementation in Python:\n\n```python\nclass Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n\nclass BinarySearchTree:\n    def __init__(self):\n        self.root = None\n```"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
        
        adapted_response = self.response_adapters.adapt_to_cursor(openai_response)
        
        # Check that the adaptation created a valid Cursor response
        self.assertIn("response", adapted_response)
        self.assertIn("status", adapted_response)
        self.assertEqual(adapted_response["status"], "success")
    
    def test_format_detection_and_adaptation_pipeline(self):
        """Test the entire format detection and adaptation pipeline"""
        # Test with GitHub Copilot format
        copilot_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getCompletions",
            "params": {
                "doc": {
                    "source": "function hello() {\n    return 'Hello,'\n}",
                    "prefix": "function hello() {\n    return 'Hello,",
                    "suffix": "'\n}",
                    "uri": "file:///project/test.js"
                }
            }
        }
        
        # Use the format adapter to detect and adapt the format
        adapted_data, format_detected, adaptation_needed = self.adapter.detect_and_adapt_format(copilot_request)
        
        # Verify detection and adaptation
        self.assertEqual(format_detected, "github-copilot")
        self.assertTrue(adaptation_needed)
        self.assertIn("messages", adapted_data)
        self.assertIn("model", adapted_data)
        
        # Create an OpenAI-style response
        openai_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "gpt-4",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "```javascript\nfunction hello() {\n    return 'Hello, World!';\n}\n```"
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
        
        # Adapt the response back to the original format
        adapted_response = self.adapter.adapt_response(openai_response, format_detected)
        
        # Verify the response adaptation
        self.assertIn("jsonrpc", adapted_response)
        self.assertIn("result", adapted_response)
        self.assertIn("completions", adapted_response["result"])
    
    def test_header_based_detection(self):
        """Test detection based on headers"""
        # Simple request with copilot-specific headers
        request_data = {"dummy": "data"}
        headers = {
            "X-GitHub-Client": "vscode",
            "X-Copilot-Session": "abc123"
        }
        
        format_detected = self.detector.detect_format(request_data, headers)
        self.assertEqual(format_detected, "github-copilot")
        
        # Simple request with cursor-specific headers
        request_data = {"dummy": "data"}
        headers = {
            "X-Cursor-Client": "vscode",
            "X-Cursor-Token": "xyz789"
        }
        
        format_detected = self.detector.detect_format(request_data, headers)
        self.assertEqual(format_detected, "cursor")
    
    def test_unknown_format_handling(self):
        """Test handling of unknown formats"""
        # Request that doesn't match any known format
        unknown_request = {
            "unknown_field": "some_value",
            "another_field": 123
        }
        
        format_detected = self.detector.detect_format(unknown_request)
        self.assertEqual(format_detected, "unknown")
        
        # Trying to adapt an unknown format should return the original data
        adapted_data, format_detected, adaptation_needed = self.adapter.detect_and_adapt_format(unknown_request)
        self.assertEqual(format_detected, "unknown")
        self.assertFalse(adaptation_needed)
        self.assertEqual(adapted_data, unknown_request)
        
        # Trying to adapt a response to an unknown format should return the original data
        openai_response = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Hello!"
                    }
                }
            ]
        }
        
        adapted_response = self.adapter.adapt_response(openai_response, "unknown")
        self.assertEqual(adapted_response, openai_response)

if __name__ == "__main__":
    unittest.main()