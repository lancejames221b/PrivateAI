"""
Private AI 🕵️ - AI Format Response Adapters

This module provides response format adaptation functionality for AI service responses.
It converts standardized OpenAI-compatible responses back to their original formats.

Author: Lance James @ Unit 221B
"""

import json
import re
from typing import Dict, List, Any
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("ai-response-adapters", "logs/ai_response_adapters.log")

class AIResponseAdapters:
    """Class for adapting OpenAI response format to various AI service formats"""
    
    def adapt_to_openai(self, response_data: Dict) -> Dict:
        """
        Identity function - response is already in OpenAI format
        """
        return response_data
    
    def adapt_to_anthropic(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Anthropic format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "completion": text,
            "model": response_data.get('model', 'claude-3-opus'),
            "stop_reason": "stop_sequence"
        }
    
    def adapt_to_github_copilot(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to GitHub Copilot format
        """
        completion = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                
                # Extract code completion from content
                # Look for code blocks or the most relevant part
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    completion = code_blocks[0]
                else:
                    # Use the first non-empty line as the completion
                    lines = [line for line in content.split('\n') if line.strip()]
                    if lines:
                        completion = lines[0]
                        
        # Format for Copilot
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "completions": [
                    {
                        "text": completion
                    }
                ]
            }
        }
    
    def adapt_to_cursor(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Cursor AI format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "response": text,
            "status": "success"
        }
    
    def adapt_to_jetbrains(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to JetBrains AI format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "result": {
                "text": text,
                "status": "complete"
            }
        }
    
    def adapt_to_vscode(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to VS Code format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "response": text,
            "success": True
        }
    
    def adapt_to_chatgpt_desktop(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to ChatGPT desktop app format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "message": text,
            "model": response_data.get('model', 'gpt-4'),
            "messageId": response_data.get('id', ''),
            "conversationId": response_data.get('id', '')
        }
    
    def adapt_to_claude_desktop(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Claude desktop app format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "completion": text,
            "model": response_data.get('model', 'claude-3-opus'),
            "stop_reason": "stop_sequence",
            "messageId": response_data.get('id', '')
        }
    
    def adapt_to_codeium(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Codeium format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                
                # Extract code from content
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    text = code_blocks[0]
                else:
                    # Use the first paragraph as a fallback
                    paragraphs = content.split('\n\n')
                    if paragraphs:
                        text = paragraphs[0]
                
        return {
            "completions": [
                {
                    "text": text,
                    "score": 0.95
                }
            ]
        }
    
    def adapt_to_tabnine(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to TabNine format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                
                # Extract code from content
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    text = code_blocks[0]
                else:
                    # Use the first line as a fallback
                    lines = content.split('\n')
                    if lines:
                        text = lines[0]
                
        return {
            "results": [
                {
                    "completions": [
                        {
                            "text": text,
                            "score": 1.0
                        }
                    ],
                    "is_locked": False
                }
            ]
        }
    
    def adapt_to_sourcegraph_cody(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Sourcegraph Cody format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "response": text,
            "error": None
        }
    
    def adapt_to_amazon_codewhisperer(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Amazon CodeWhisperer format
        """
        completions = []
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                
                # Extract code from content - try to get multiple suggestions
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    for block in code_blocks:
                        completions.append({
                            "content": block,
                            "confidence": "HIGH"
                        })
                else:
                    # Use the paragraphs as different completions
                    paragraphs = [p for p in content.split('\n\n') if p.strip()]
                    for para in paragraphs[:3]:  # Limit to 3 completions
                        completions.append({
                            "content": para,
                            "confidence": "MEDIUM"
                        })
                
        # If no completions, add an empty one
        if not completions:
            completions.append({
                "content": "",
                "confidence": "LOW"
            })
                
        return {
            "completions": completions,
            "status": "SUCCESS"
        }
    
    def adapt_to_replit(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Replit format
        """
        text = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                text = choice['message']['content']
                
        return {
            "answer": text,
            "success": True,
            "requestId": response_data.get('id', ''),
            "displayFormat": "markdown"
        }
    
    def adapt_to_kite(self, response_data: Dict) -> Dict:
        """
        Adapt OpenAI format to Kite format
        """
        completion = ""
        if 'choices' in response_data and response_data['choices']:
            choice = response_data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                content = choice['message']['content']
                
                # Extract code from content
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    completion = code_blocks[0]
                else:
                    # Use the first line as a fallback
                    lines = [line for line in content.split('\n') if line.strip()]
                    if lines:
                        completion = lines[0]
                
        return {
            "completions": [
                {
                    "text": completion,
                    "display": completion,
                    "score": 1.0
                }
            ]
        }