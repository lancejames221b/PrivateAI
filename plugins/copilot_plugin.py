#!/usr/bin/env python3
"""
Private AI 🕵️ - GitHub Copilot Plugin

This plugin handles GitHub Copilot requests and responses, applying PII protection
and ensuring proper authentication and certificate handling.

Author: Lance James @ Unit 221B
"""

import os
import json
import re
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from mitmproxy import http

from proxy_base import ProxyPlugin
from logger import get_logger, log_exception
from pii_transform import PIITransformer

# Initialize logger
logger = get_logger("copilot-plugin", "logs/copilot_plugin.log")

# Initialize PII transformer
pii_transformer = PIITransformer()

class CopilotPlugin(ProxyPlugin):
    """Plugin for handling GitHub Copilot requests and responses"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize the plugin
        
        Args:
            config: Plugin configuration (optional)
        """
        super().__init__(config)
        
        # Set priority (lower runs first)
        self.priority = 10  # High priority for Copilot
        
        # Copilot domains
        self.domains = self.config.get("domains", [
            "api.github.com",
            "github.com",
            "api.githubcopilot.com",
            "copilot-proxy.githubusercontent.com",
            "githubcopilot.com",
            "default.exp-tas.com"
        ])
        
        # Copilot endpoints
        self.endpoints = self.config.get("endpoints", [
            "/copilot",
            "/v1/engines",
            "/v1/completions",
            "/v1/chat/completions",
            "/github/copilot",
            "/v1/engines/copilot-codex",
            "/v1/engines/copilot-codex/completions"
        ])
        
        # Request tracking
        self.request_map = {}
        
        logger.info(f"Copilot plugin initialized with {len(self.domains)} domains and {len(self.endpoints)} endpoints")
    
    def should_process_request(self, flow: http.HTTPFlow) -> bool:
        """
        Determine if this plugin should process the request
        
        Args:
            flow: The HTTP flow to check
            
        Returns:
            bool: True if this plugin should process the request, False otherwise
        """
        # Check if there's a request body
        if not flow.request.content:
            return False
        
        # Check if it's a Copilot domain
        host = flow.request.host
        if any(domain in host for domain in self.domains):
            return True
        
        # Check if it's a Copilot endpoint
        path = flow.request.path
        if any(endpoint in path for endpoint in self.endpoints):
            return True
        
        # Check for Copilot-specific headers
        headers = flow.request.headers
        if "github-copilot" in str(headers).lower() or "copilot" in str(headers).lower():
            return True
        
        return False
    
    def process_request(self, flow: http.HTTPFlow) -> None:
        """
        Process a Copilot request
        
        Args:
            flow: The HTTP flow to process
        """
        try:
            # Generate a unique request ID for tracking
            request_id = str(uuid.uuid4())
            flow.request.id = request_id
            
            logger.info(f"Processing Copilot request to {flow.request.host}{flow.request.path} (ID: {request_id})")
            
            # Try to parse the request as JSON
            try:
                content = flow.request.content.decode('utf-8', errors='ignore')
                request_data = json.loads(content)
                
                # Store original request for response handling
                self.request_map[request_id] = {
                    "original": request_data,
                    "host": flow.request.host,
                    "path": flow.request.path
                }
                
                # Apply PII transformation to the request
                transformed_data = self._transform_request(request_data)
                
                # Convert back to JSON and update the request
                flow.request.content = json.dumps(transformed_data).encode('utf-8')
                flow.request.headers["content-length"] = str(len(flow.request.content))
                
                logger.info(f"Successfully transformed Copilot request (ID: {request_id})")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Non-JSON request or encoding error: {str(e)} (ID: {request_id})")
        except Exception as e:
            log_exception(logger, e, "process_request")
    
    def should_process_response(self, flow: http.HTTPFlow) -> bool:
        """
        Determine if this plugin should process the response
        
        Args:
            flow: The HTTP flow to check
            
        Returns:
            bool: True if this plugin should process the response, False otherwise
        """
        # Check if we tracked this request
        request_id = getattr(flow.request, 'id', None)
        return request_id is not None and request_id in self.request_map
    
    def process_response(self, flow: http.HTTPFlow) -> None:
        """
        Process a Copilot response
        
        Args:
            flow: The HTTP flow to process
        """
        try:
            # Get the request ID
            request_id = getattr(flow.request, 'id', None)
            if not request_id or request_id not in self.request_map:
                return
            
            # Get the original request
            request_info = self.request_map.pop(request_id)
            
            logger.info(f"Processing Copilot response for request {request_id}")
            
            # Try to parse the response as JSON
            try:
                content = flow.response.content.decode('utf-8', errors='ignore')
                response_data = json.loads(content)
                
                # Apply PII transformation to the response
                transformed_data = self._transform_response(response_data)
                
                # Convert back to JSON and update the response
                flow.response.content = json.dumps(transformed_data).encode('utf-8')
                flow.response.headers["content-length"] = str(len(flow.response.content))
                
                logger.info(f"Successfully transformed Copilot response (ID: {request_id})")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Non-JSON response or encoding error: {str(e)} (ID: {request_id})")
        except Exception as e:
            log_exception(logger, e, "process_response")
    
    def _transform_request(self, request_data: Dict) -> Dict:
        """
        Apply PII transformation to the request data
        
        Args:
            request_data: The request data to transform
            
        Returns:
            dict: The transformed request data
        """
        # Handle Copilot-specific request formats
        
        # Handle completions request
        if 'prompt' in request_data and isinstance(request_data['prompt'], str):
            request_data['prompt'] = pii_transformer.transform_text(request_data['prompt'])
        
        # Handle chat completions request
        if 'messages' in request_data and isinstance(request_data['messages'], list):
            for message in request_data['messages']:
                if 'content' in message and isinstance(message['content'], str):
                    message['content'] = pii_transformer.transform_text(message['content'])
        
        # Handle Copilot code context
        if 'source' in request_data and isinstance(request_data['source'], str):
            request_data['source'] = pii_transformer.transform_text(request_data['source'])
        
        # Handle Copilot document context
        if 'document' in request_data:
            if isinstance(request_data['document'], str):
                request_data['document'] = pii_transformer.transform_text(request_data['document'])
            elif isinstance(request_data['document'], dict) and 'content' in request_data['document']:
                if isinstance(request_data['document']['content'], str):
                    request_data['document']['content'] = pii_transformer.transform_text(request_data['document']['content'])
        
        # Handle prefix/suffix format
        if 'prefix' in request_data and isinstance(request_data['prefix'], str):
            request_data['prefix'] = pii_transformer.transform_text(request_data['prefix'])
        if 'suffix' in request_data and isinstance(request_data['suffix'], str):
            request_data['suffix'] = pii_transformer.transform_text(request_data['suffix'])
        
        return request_data
    
    def _transform_response(self, response_data: Dict) -> Dict:
        """
        Apply PII transformation to the response data
        
        Args:
            response_data: The response data to transform
            
        Returns:
            dict: The transformed response data
        """
        # Handle Copilot-specific response formats
        
        # Handle completions response
        if 'choices' in response_data and isinstance(response_data['choices'], list):
            for choice in response_data['choices']:
                if 'text' in choice and isinstance(choice['text'], str):
                    choice['text'] = pii_transformer.transform_text(choice['text'])
                if 'message' in choice and 'content' in choice['message']:
                    if isinstance(choice['message']['content'], str):
                        choice['message']['content'] = pii_transformer.transform_text(choice['message']['content'])
        
        # Handle Copilot completions response
        if 'completions' in response_data and isinstance(response_data['completions'], list):
            for completion in response_data['completions']:
                if 'text' in completion and isinstance(completion['text'], str):
                    completion['text'] = pii_transformer.transform_text(completion['text'])
        
        # Handle direct text response
        if 'text' in response_data and isinstance(response_data['text'], str):
            response_data['text'] = pii_transformer.transform_text(response_data['text'])
        
        return response_data