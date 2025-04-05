"""
Private AI 🕵️ - AI Format Adapter

This module provides enhanced format detection and adaptation for AI service requests,
with a focus on IDE-based AI assistants. It standardizes diverse payload formats
to enable consistent PII protection across different AI services.

Author: Lance James @ Unit 221B
"""

import json
import re
import os
from typing import Dict, List, Tuple, Any, Optional, Union
from logger import get_logger, log_exception

# Import specialized modules
from ai_format_detector import AIFormatDetector
from ai_format_request_adapters import AIRequestAdapters
from ai_format_response_adapters import AIResponseAdapters

# Initialize logger
logger = get_logger("ai-format-adapter", "logs/ai_format_adapter.log")

class AIFormatAdapter:
    """
    Class to handle detection and adaptation of AI API formats.
    This provides a more structured approach to format standardization.
    """
    
    def __init__(self):
        """Initialize the format adapter with detectors and adapters"""
        self.detector = AIFormatDetector()
        self.request_adapters = AIRequestAdapters()
        self.response_adapters = AIResponseAdapters()
    
    def detect_and_adapt_format(self, request_data: Dict, headers: Optional[Dict] = None) -> Tuple[Dict, str, bool]:
        """
        Detect the AI API format of the request and convert it to a standard format if needed.
        
        Args:
            request_data (dict): The request data as a Python dictionary
            headers (dict, optional): The request headers
            
        Returns:
            tuple: (adapted_data, format_detected, adaptation_needed)
                - adapted_data: The adapted request data, or original if no adaptation needed
                - format_detected: String identifying the detected format
                - adaptation_needed: Boolean indicating whether adaptation was performed
        """
        if not request_data:
            return request_data, 'unknown', False
            
        # Try to detect the format
        format_detected = self.detector.detect_format(request_data, headers)
        
        if format_detected == 'openai':
            # Already in OpenAI format, no adaptation needed
            return request_data, format_detected, False
            
        # Adapt to OpenAI format if needed
        try:
            adapter_method = getattr(self.request_adapters, f"adapt_from_{format_detected}", None)
            if adapter_method:
                adapted_data = adapter_method(request_data, headers)
                return adapted_data, format_detected, True
            else:
                logger.warning(f"No adapter available for format {format_detected}")
                return request_data, format_detected, False
        except Exception as e:
            log_exception(logger, e, f"adapt_from_{format_detected}_format")
            logger.warning(f"Failed to adapt {format_detected} format, returning original")
            return request_data, format_detected, False
    
    def adapt_response(self, response_data: Dict, original_format: str) -> Dict:
        """
        Adapt the response back to the original request format
        
        Args:
            response_data (dict): The response data in OpenAI format
            original_format (str): The original format to convert back to
            
        Returns:
            dict: The adapted response data
        """
        if original_format == 'openai' or original_format == 'unknown':
            return response_data
        
        try:    
            adapter_method = getattr(self.response_adapters, f"adapt_to_{original_format}", None)
            if adapter_method:
                return adapter_method(response_data)
            else:
                logger.warning(f"No response adapter available for format {original_format}")
                return response_data
        except Exception as e:
            log_exception(logger, e, f"adapt_response_to_{original_format}_format")
            logger.warning(f"Failed to adapt response to {original_format} format, returning original")
                
        return response_data
