"""
Private AI 🕵️ - MITM Proxy Interceptor

This module provides a mitmproxy script for intercepting AI service requests,
applying PII protection to the content, and forwarding them to the original
destination. It now features enhanced detection and format adaptation for
IDE-based AI assistants like GitHub Copilot, Cursor, VS Code AI, and others.

Author: Lance James @ Unit 221B
"""

import json
import re
import os
import base64
import uuid
import sys
import sqlite3
from typing import Dict, List, Union, Optional, Any, Tuple
from urllib.parse import urlparse

# Import mitmproxy
from mitmproxy import http, ctx
from mitmproxy.script import concurrent

# Import our modules
from pii_transform import PIITransformer
from logger import get_logger, log_exception
from ai_format_adapter import AIFormatAdapter

# Initialize logger
logger = get_logger("mitm-intercept", "logs/mitm_intercept.log")

# Initialize the PII transformer
pii_transformer = PIITransformer()

# Initialize the AI format adapter
format_adapter = AIFormatAdapter()

# Configuration - load from environment if available
AI_DOMAINS = os.environ.get("AI_DOMAINS", "openai.com,anthropic.com,api.github.com,copilot.github.com").split(",")
ADDITIONAL_DOMAINS = os.environ.get("ADDITIONAL_DOMAINS", "").split(",") if os.environ.get("ADDITIONAL_DOMAINS") else []
EXCLUDED_DOMAINS = os.environ.get("EXCLUDED_DOMAINS", "").split(",") if os.environ.get("EXCLUDED_DOMAINS") else []
ALL_DOMAINS = list(set(AI_DOMAINS + ADDITIONAL_DOMAINS))

# AI endpoint patterns that might be found in requests
AI_ENDPOINT_PATTERNS = [
    r"/v\d+/chat/completions",
    r"/v\d+/completions",
    r"/v\d+/messages",
    r"/v\d+/generate",
    r"/v\d+/engines/.+/completions",
    r"copilot",
    r"github\.com/api/v\d+/copilot",
    r"/api/ai/",
    r"/api/chat",
    r"/api/completion",
    r"/api/assistant",
    r"/api/generate",
    r"/codeCompletion",
    r"/codeAssistant",
    r"/suggest",
    r"/complete",
    r"/chat",
    r"/ai/",
    r"/ml/",
    r"/lsp/",
    r"/assistant/",
]

# AI content type patterns
AI_CONTENT_TYPE_PATTERNS = [
    r"application/json",
    r"text/plain",
]

# Heuristic keywords for AI request detection
AI_REQUEST_KEYWORDS = [
    "prompt", "message", "query", "input", "text", "completion", "content",
    "model", "temperature", "top_p", "max_tokens", "frequency_penalty", "presence_penalty",
    "gpt", "claude", "davinci", "ada", "curie", "babbage", "llama", "language", "token",
    "context", "conversation", "dialog", "system", "user", "assistant", "api_key",
    "code", "code_context", "file_content", "completion", "suggestion"
]

class AIRequestInterceptor:
    """Main interceptor class for the MITM proxy"""
    
    def __init__(self):
        """Initialize the interceptor"""
        self.transformer = pii_transformer
        self.adapter = format_adapter
        self.request_map = {}  # Map to track request formats
    
    def is_ai_domain(self, flow: http.HTTPFlow) -> bool:
        """Check if the domain in the flow is an AI service domain"""
        host = flow.request.host
        
        # Check against excluded domains first
        if any(domain in host for domain in EXCLUDED_DOMAINS if domain):
            return False
            
        # Check against known AI domains
        if any(domain in host for domain in ALL_DOMAINS if domain):
            return True
            
        # Check path against AI endpoint patterns
        path = flow.request.path
        if any(re.search(pattern, path, re.IGNORECASE) for pattern in AI_ENDPOINT_PATTERNS):
            return True
            
        return False
    
    def is_ai_request_heuristic(self, flow: http.HTTPFlow) -> bool:
        """
        Use heuristics to detect if a request is to an AI service,
        even if the domain is not in our known list
        """
        # Check content type
        content_type = flow.request.headers.get("content-type", "")
        if not any(re.search(pattern, content_type, re.IGNORECASE) for pattern in AI_CONTENT_TYPE_PATTERNS):
            return False
            
        # If it's JSON, check for AI-specific fields or keywords
        if "application/json" in content_type.lower():
            try:
                content = flow.request.content.decode('utf-8', errors='ignore')
                data = json.loads(content)
                
                # Check for common AI request fields
                field_count = 0
                for keyword in AI_REQUEST_KEYWORDS:
                    if isinstance(data, dict) and keyword in data:
                        field_count += 1
                
                # If multiple AI-related fields are found, it's likely an AI request
                if field_count >= 3:
                    return True
                    
                # Additional checks for IDE-based AI assistants
                # If these fields are present, it's very likely an IDE AI assistant request
                ide_indicators = [
                    "editor", "cursor", "selection", "document", "position",
                    "filepath", "language", "prefix", "suffix", "completion",
                    "before", "after", "code", "jsonrpc", "context"
                ]
                
                for indicator in ide_indicators:
                    if isinstance(data, dict) and indicator in data:
                        field_count += 1
                
                # If enough IDE indicators are found, detect as AI
                if field_count >= 2:
                    return True
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
                
        return False
    
    def should_intercept(self, flow: http.HTTPFlow) -> bool:
        """Determine if the request should be intercepted"""
        # Check if there's a request body
        if not flow.request.content:
            return False
            
        # Check if it's an AI domain
        is_ai_domain = self.is_ai_domain(flow)
        
        # If not a known AI domain, use heuristics
        if not is_ai_domain:
            return self.is_ai_request_heuristic(flow)
            
        return is_ai_domain
    
    @concurrent
    def request(self, flow: http.HTTPFlow) -> None:
        """Process an HTTP request"""
        try:
            if not self.should_intercept(flow):
                return
                
            # Generate a unique request ID for tracking
            request_id = str(uuid.uuid4())
            flow.request.id = request_id
            
            logger.info(f"Intercepted request to {flow.request.host}{flow.request.path} (ID: {request_id})")
            
            # Try to parse the request as JSON
            try:
                content = flow.request.content.decode('utf-8', errors='ignore')
                request_data = json.loads(content)
                
                # Extract headers as a dictionary
                headers = dict(flow.request.headers.items())
                
                # Use our format adapter to detect and adapt format if needed
                adapted_data, format_detected, adaptation_needed = self.adapter.detect_and_adapt_format(request_data, headers)
                
                if adaptation_needed:
                    logger.info(f"Adapted request format from {format_detected} to OpenAI format (ID: {request_id})")
                else:
                    logger.info(f"Request is already in {format_detected} format (ID: {request_id})")
                
                # Store the detected format for use in response handling
                self.request_map[request_id] = format_detected
                
                # Apply PII transformation to the adapted request
                if format_detected != 'unknown':
                    transformed_data = self.transform_request(adapted_data, format_detected)
                    
                    # Convert back to JSON and update the request
                    flow.request.content = json.dumps(transformed_data).encode('utf-8')
                    flow.request.headers["content-length"] = str(len(flow.request.content))
                    
                    logger.info(f"Successfully transformed request (ID: {request_id})")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Non-JSON request or encoding error: {str(e)} (ID: {request_id})")
        except Exception as e:
            log_exception(logger, e, "request")
    
    @concurrent
    def response(self, flow: http.HTTPFlow) -> None:
        """Process an HTTP response"""
        try:
            # Check if we tracked this request
            request_id = getattr(flow.request, 'id', None)
            if not request_id or request_id not in self.request_map:
                return
                
            # Get the original format
            original_format = self.request_map.pop(request_id)
            
            logger.info(f"Processing response for request {request_id} (original format: {original_format})")
            
            # Try to parse the response as JSON
            try:
                content = flow.response.content.decode('utf-8', errors='ignore')
                response_data = json.loads(content)
                
                # Apply PII transformation to the response data
                transformed_data = self.transform_response(response_data)
                
                # If needed, adapt the response back to the original format
                if original_format != 'unknown' and original_format != 'openai':
                    adapted_response = self.adapter.adapt_response(transformed_data, original_format)
                    logger.info(f"Adapted response from OpenAI format back to {original_format} format (ID: {request_id})")
                    
                    # Convert back to JSON and update the response
                    flow.response.content = json.dumps(adapted_response).encode('utf-8')
                else:
                    # Just update with the transformed data
                    flow.response.content = json.dumps(transformed_data).encode('utf-8')
                    
                flow.response.headers["content-length"] = str(len(flow.response.content))
                logger.info(f"Successfully processed response (ID: {request_id})")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Non-JSON response or encoding error: {str(e)} (ID: {request_id})")
        except Exception as e:
            log_exception(logger, e, "response")
    
    def transform_request(self, request_data: Dict, format_detected: str) -> Dict:
        """
        Apply PII transformation to the request data
        
        Args:
            request_data (dict): The request data to transform
            format_detected (str): The detected format
            
        Returns:
            dict: The transformed request data
        """
        if format_detected == 'openai':
            # Transform OpenAI-style messages
            if 'messages' in request_data:
                for message in request_data['messages']:
                    if 'content' in message and isinstance(message['content'], str):
                        message['content'] = self.transformer.transform_text(message['content'])
            
            # Transform prompt field if present
            if 'prompt' in request_data and isinstance(request_data['prompt'], str):
                request_data['prompt'] = self.transformer.transform_text(request_data['prompt'])
                
            # Handle streaming
            if 'stream' in request_data:
                # Some services don't handle streaming well with transformed content
                # Consider setting to False for more reliable operation
                # request_data['stream'] = False
                pass
        
        return request_data
    
    def transform_response(self, response_data: Dict) -> Dict:
        """
        Apply PII transformation to the response data
        
        Args:
            response_data (dict): The response data to transform
            
        Returns:
            dict: The transformed response data
        """
        # Transform OpenAI-style responses
        if 'choices' in response_data and isinstance(response_data['choices'], list):
            for choice in response_data['choices']:
                if 'message' in choice and 'content' in choice['message']:
                    if isinstance(choice['message']['content'], str):
                        choice['message']['content'] = self.transformer.transform_text(choice['message']['content'])
                elif 'text' in choice:
                    if isinstance(choice['text'], str):
                        choice['text'] = self.transformer.transform_text(choice['text'])
        
        # Transform Anthropic-style responses
        if 'completion' in response_data and isinstance(response_data['completion'], str):
            response_data['completion'] = self.transformer.transform_text(response_data['completion'])
            
        # Transform raw text responses
        if 'text' in response_data and isinstance(response_data['text'], str):
            response_data['text'] = self.transformer.transform_text(response_data['text'])
            
        # Transform content field if present
        if 'content' in response_data and isinstance(response_data['content'], str):
            response_data['content'] = self.transformer.transform_text(response_data['content'])
        
        return response_data

# Create a global instance of the interceptor for mitmproxy
interceptor = AIRequestInterceptor()

# Functions for mitmproxy to call
def request(flow: http.HTTPFlow) -> None:
    """mitmproxy request hook"""
    interceptor.request(flow)

def response(flow: http.HTTPFlow) -> None:
    """mitmproxy response hook"""
    interceptor.response(flow)