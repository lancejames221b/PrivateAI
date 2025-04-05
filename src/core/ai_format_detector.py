"""
Private AI 🕵️ - AI Format Detector

This module provides format detection functionality for AI service requests.
It can identify various AI API formats based on request data and headers.

Author: Lance James @ Unit 221B
"""

import json
import re
from typing import Dict, Optional, List, Any
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("ai-format-detector", "logs/ai_format_detector.log")

class AIFormatDetector:
    """Class to detect AI API formats from request data and headers"""
    
    def __init__(self):
        """Initialize the format detector"""
        # Dictionary mapping format names to detector methods
        self.detectors = {
            'openai': self._detect_openai_format,
            'anthropic': self._detect_anthropic_format,
            'github-copilot': self._detect_github_copilot_format,
            'cursor': self._detect_cursor_format,
            'jetbrains': self._detect_jetbrains_format,
            'vscode': self._detect_vscode_format,
            'chatgpt-desktop': self._detect_chatgpt_desktop_format,
            'claude-desktop': self._detect_claude_desktop_format,
            'codeium': self._detect_codeium_format,
            'tabnine': self._detect_tabnine_format,
            'sourcegraph-cody': self._detect_sourcegraph_cody_format,
            'amazon-codewhisperer': self._detect_codewhisperer_format,
            'replit': self._detect_replit_format,
            'kite': self._detect_kite_format,
        }
    
    def detect_format(self, request_data: Dict, headers: Optional[Dict] = None) -> str:
        """
        Detect the format of the request data
        
        Args:
            request_data (dict): The request data
            headers (dict, optional): The request headers
            
        Returns:
            str: The detected format
        """
        # Try each detector in order
        for format_name, detector in self.detectors.items():
            try:
                if detector(request_data, headers):
                    logger.info(f"Detected {format_name} format")
                    return format_name
            except Exception as e:
                log_exception(logger, e, f"_detect_{format_name}_format")
                
        # If no format detected, return unknown
        return 'unknown'
    
    def _detect_openai_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect OpenAI API format"""
        return ('model' in request_data and 
                ('messages' in request_data or 'prompt' in request_data))
    
    def _detect_anthropic_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Anthropic API format"""
        # Check for Claude API format
        if 'model' in request_data and 'prompt' in request_data:
            if isinstance(request_data.get('prompt'), str):
                # Check for Claude-style prompt format
                if request_data.get('prompt', '').startswith('\n\nHuman:'):
                    return True
                    
        # Check for Claude API v2 format (messages array)
        if 'model' in request_data and 'messages' in request_data:
            # Check if any message has role 'human' or 'assistant'
            for message in request_data.get('messages', []):
                if message.get('role') in ['human', 'assistant']:
                    return True
                    
        # Check for Anthropic headers
        if headers:
            for header_name in headers:
                if 'anthropic' in header_name.lower() or 'claude' in header_name.lower():
                    return True
                    
        return False
    
    def _detect_github_copilot_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect GitHub Copilot format"""
        # Check for JSONRPC format used by Copilot
        if 'jsonrpc' in request_data and 'method' in request_data:
            # Check for Copilot-specific methods
            copilot_methods = [
                'getCompletions', 
                'getCompletionsCycling', 
                'provideInlineCompletions',
                'notifyAccepted',
                'notifyRejected',
                'notifyShown'
            ]
            if request_data.get('method') in copilot_methods:
                return True
                
        # Check for Copilot headers
        if headers:
            copilot_headers = [
                'x-github-token', 
                'x-github-client-id', 
                'x-github-client-name', 
                'x-copilot-session', 
                'github-copilot'
            ]
            for header in copilot_headers:
                if any(header.lower() in h.lower() for h in headers):
                    return True
                    
        return False
    
    def _detect_cursor_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Cursor AI format"""
        # Check for Cursor headers
        if headers:
            cursor_headers = ['x-cursor-token', 'x-cursor-client']
            for header in cursor_headers:
                if any(header.lower() in h.lower() for h in headers):
                    return True
                    
        # Check for Cursor-specific request format
        if 'prompt' in request_data and 'context' in request_data:
            return True
                
        return False
    
    def _detect_jetbrains_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect JetBrains AI format"""
        # Check for JetBrains headers
        if headers:
            for header_name in headers:
                if 'jetbrains' in header_name.lower():
                    return True
                    
        # Check for JetBrains-specific request format
        if ('query' in request_data or 'prompt' in request_data) and 'context' in request_data:
            return True
                
        return False
    
    def _detect_vscode_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect VS Code extension format"""
        # Check for VS Code headers
        if headers:
            vscode_headers = ['x-vscode', 'x-ide-version', 'x-ide-client', 'x-plugin-type']
            for header in vscode_headers:
                if any(header.lower() in h.lower() for h in headers):
                    return True
                    
        # Check for VS Code-specific request format
        if 'text' in request_data or 'files' in request_data:
            return True
                
        return False
    
    def _detect_chatgpt_desktop_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect ChatGPT desktop app format"""
        # Check for ChatGPT headers
        if headers:
            for header_name in headers:
                if 'chatgpt' in header_name.lower():
                    return True
                    
        # Check for ChatGPT-specific request format
        if 'prompt' in request_data and 'context' in request_data:
            # Check if not Cursor format (which also has prompt and context)
            if not self._detect_cursor_format(request_data, headers):
                return True
                
        return False
    
    def _detect_claude_desktop_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Claude desktop app format"""
        # Check for Claude headers
        if headers:
            for header_name in headers:
                if 'claude' in header_name.lower() and 'anthropic' not in header_name.lower():
                    return True
                    
        # Check for Claude-specific request format
        if 'prompt' in request_data and not self._detect_anthropic_format(request_data, headers):
            # Look for Claude-specific fields
            claude_fields = ['claudeVersion', 'appVersion']
            for field in claude_fields:
                if field in request_data:
                    return True
                
        return False
    
    def _detect_codeium_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Codeium format"""
        # Check for Codeium headers
        if headers:
            codeium_headers = ['x-codeium-token', 'x-codeium-client']
            for header in codeium_headers:
                if any(header.lower() in h.lower() for h in headers):
                    return True
                    
        # Check for Codeium-specific request format
        if 'document' in request_data and 'position' in request_data:
            return True
                
        return False
    
    def _detect_tabnine_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect TabNine format"""
        # Check for TabNine headers
        if headers:
            tabnine_headers = ['x-tabnine-client', 'x-tabnine-token']
            for header in tabnine_headers:
                if any(header.lower() in h.lower() for h in headers):
                    return True
                    
        # Check for TabNine-specific request format
        if 'before' in request_data and 'after' in request_data:
            return True
                
        return False
    
    def _detect_sourcegraph_cody_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Sourcegraph Cody format"""
        # Check for Sourcegraph headers
        if headers:
            sourcegraph_headers = ['x-sourcegraph-client', 'x-cody-token']
            for header in sourcegraph_headers:
                if any(header.lower() in h.lower() for h in headers):
                    return True
                    
        # Check for Cody-specific request format
        if 'query' in request_data and 'codebase' in request_data:
            return True
                
        return False
    
    def _detect_codewhisperer_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Amazon CodeWhisperer format"""
        # Check for CodeWhisperer headers
        if headers:
            for header_name in headers:
                if 'codewhisperer' in header_name.lower() or 'aws-codewhisperer' in header_name.lower():
                    return True
                    
        # Check for CodeWhisperer-specific request format
        if 'codeReference' in request_data or 'fileContext' in request_data:
            return True
                
        return False
    
    def _detect_replit_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Replit format"""
        # Check for Replit headers
        if headers:
            for header_name in headers:
                if 'replit' in header_name.lower():
                    return True
                    
        # Check for Replit-specific request format
        if 'code' in request_data and 'language' in request_data:
            return True
                
        return False
    
    def _detect_kite_format(self, request_data: Dict, headers: Optional[Dict] = None) -> bool:
        """Detect Kite format"""
        # Check for Kite headers
        if headers:
            for header_name in headers:
                if 'kite' in header_name.lower():
                    return True
                    
        # Check for Kite-specific request format
        if 'editor' in request_data and 'filename' in request_data:
            return True
                
        return False