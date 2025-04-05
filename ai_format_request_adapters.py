"""
Private AI 🕵️ - AI Format Request Adapters

This module provides request format adaptation functionality for AI service requests.
It standardizes diverse request formats to a common OpenAI-compatible format.

Author: Lance James @ Unit 221B
"""

import json
import re
from typing import Dict, Optional, List, Any
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("ai-format-adapters", "logs/ai_format_adapters.log")

class AIRequestAdapters:
    """Class for adapting various AI request formats to a standard OpenAI format"""
    
    def adapt_to_openai_format(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Identity function - data is already in OpenAI format
        """
        return request_data
    
    def adapt_from_anthropic(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Anthropic format to OpenAI format
        """
        # Handle Claude API v1 format (prompt string)
        if 'prompt' in request_data and isinstance(request_data.get('prompt'), str):
            prompt = request_data['prompt']
            messages = []
            
            # Parse the Anthropic-style conversation format
            chunks = prompt.split('\n\n')
            for chunk in chunks:
                if chunk.startswith('Human:'):
                    messages.append({
                        'role': 'user',
                        'content': chunk[6:].strip()
                    })
                elif chunk.startswith('Assistant:'):
                    messages.append({
                        'role': 'assistant',
                        'content': chunk[10:].strip()
                    })
            
            # Create OpenAI-compatible request
            adapted_data = {
                'model': request_data.get('model', 'gpt-4'),
                'messages': messages,
                'temperature': request_data.get('temperature', 0.7),
                'max_tokens': request_data.get('max_tokens', 1024),
                'stream': request_data.get('stream', False)
            }
            
            # Copy other parameters
            for key in ['top_p', 'frequency_penalty', 'presence_penalty', 'stop']:
                if key in request_data:
                    adapted_data[key] = request_data[key]
                    
            return adapted_data
            
        # Handle Claude API v2 format (messages array)
        elif 'messages' in request_data:
            messages = []
            
            # Convert Claude message roles to OpenAI roles
            role_mapping = {
                'human': 'user',
                'assistant': 'assistant',
                'system': 'system'
            }
            
            for message in request_data.get('messages', []):
                role = message.get('role', '')
                content = message.get('content', '')
                
                if role in role_mapping:
                    messages.append({
                        'role': role_mapping[role],
                        'content': content
                    })
            
            # Create OpenAI-compatible request
            adapted_data = {
                'model': request_data.get('model', 'gpt-4'),
                'messages': messages,
                'temperature': request_data.get('temperature', 0.7),
                'max_tokens': request_data.get('max_tokens', 1024),
                'stream': request_data.get('stream', False)
            }
            
            # Copy other parameters
            for key in ['top_p', 'frequency_penalty', 'presence_penalty', 'stop']:
                if key in request_data:
                    adapted_data[key] = request_data[key]
                    
            return adapted_data
            
        # Fallback - return original data
        return request_data
    
    def adapt_from_github_copilot(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt GitHub Copilot format to OpenAI format
        """
        # Handle different Copilot methods
        if 'method' in request_data:
            method = request_data['method']
            params = request_data.get('params', {})
            
            if method == 'getCompletions':
                doc_context = params.get('doc', {}).get('source', '')
                prefix = params.get('doc', {}).get('prefix', '')
                suffix = params.get('doc', {}).get('suffix', '')
                
                # Get language from file path if available
                language = ''
                if 'uri' in params.get('doc', {}):
                    uri = params['doc']['uri']
                    if '.' in uri:
                        ext = uri.split('.')[-1].lower()
                        language_map = {
                            'py': 'python',
                            'js': 'javascript',
                            'ts': 'typescript',
                            'jsx': 'javascript',
                            'tsx': 'typescript',
                            'html': 'html',
                            'css': 'css',
                            'java': 'java',
                            'c': 'c',
                            'cpp': 'cpp',
                            'cs': 'csharp',
                            'go': 'go',
                            'rb': 'ruby',
                            'php': 'php',
                            'rs': 'rust',
                            'swift': 'swift',
                            'kt': 'kotlin'
                        }
                        language = language_map.get(ext, '')
                
                # Convert to OpenAI format
                adapted_data = {
                    'model': 'gpt-4',  # Default to GPT-4 for code completions
                    'messages': [
                        {
                            'role': 'system',
                            'content': f'You are GitHub Copilot, an AI programming assistant. ' + 
                                     f'You are helping with {language} code.' if language else 
                                     'You are GitHub Copilot, an AI programming assistant.'
                        },
                        {
                            'role': 'user',
                            'content': f"Complete the following code:\n\n```{language if language else ''}\n{prefix}[CURSOR HERE]{suffix}\n```\n\nContext:\n```{language if language else ''}\n{doc_context}\n```"
                        }
                    ],
                    'temperature': 0.2,  # Lower temperature for code completion
                    'max_tokens': 512,
                    'stream': True
                }
                return adapted_data
                
            elif method in ['getCompletionsCycling', 'provideInlineCompletions']:
                # Similar to getCompletions but with different parameters
                doc = params.get('doc', {})
                if not doc and 'documents' in params:
                    doc = params.get('documents', [{}])[0]
                
                # Extract code context
                prefix = doc.get('prefix', '')
                suffix = doc.get('suffix', '')
                source = doc.get('source', '')
                
                # Convert to OpenAI format
                adapted_data = {
                    'model': 'gpt-4',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are GitHub Copilot, an AI programming assistant.'
                        },
                        {
                            'role': 'user',
                            'content': f"Complete the following code inline:\n\n```\n{prefix}[CURSOR HERE]{suffix}\n```\n\nContext:\n```\n{source}\n```"
                        }
                    ],
                    'temperature': 0.2,
                    'max_tokens': 100,
                    'stream': True
                }
                return adapted_data
                
            # For other methods, return a minimal OpenAI request
            return {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are GitHub Copilot, an AI programming assistant.'
                    },
                    {
                        'role': 'user',
                        'content': f"Method: {method}, Params: {json.dumps(params)}"
                    }
                ],
                'temperature': 0.2,
                'max_tokens': 100
            }
        
        # Fallback - return original data
        return request_data
    
    def adapt_from_cursor(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Cursor AI format to OpenAI format
        """
        # Extract what we can from the Cursor request
        prompt = request_data.get('prompt', '')
        context = request_data.get('context', '')
        
        if not prompt and 'messages' in request_data:
            # Already has messages array, might be using OpenAI-like format
            return request_data
            
        # Convert to OpenAI format
        adapted_data = {
            'model': request_data.get('model', 'gpt-4'),
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an AI programming assistant integrated in Cursor code editor.'
                }
            ],
            'temperature': request_data.get('temperature', 0.7),
            'max_tokens': request_data.get('max_tokens', 1024),
            'stream': request_data.get('stream', False)
        }
        
        # Add context as system message if available
        if context:
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"Context: {context}"
            })
            
        # Add prompt as user message
        if prompt:
            adapted_data['messages'].append({
                'role': 'user',
                'content': prompt
            })
            
        return adapted_data
    
    def adapt_from_jetbrains(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt JetBrains AI format to OpenAI format
        """
        # Extract what we can from the JetBrains request
        prompt = request_data.get('query', '') or request_data.get('prompt', '')
        context = request_data.get('context', '')
        code_snippet = request_data.get('code', '')
        
        # Combine available context
        full_prompt = prompt
        if code_snippet:
            full_prompt = f"{full_prompt}\n\nCode:\n```\n{code_snippet}\n```"
        if context:
            full_prompt = f"{full_prompt}\n\nContext: {context}"
            
        # Convert to OpenAI format
        adapted_data = {
            'model': request_data.get('model', 'gpt-4'),
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an AI programming assistant integrated in a JetBrains IDE.'
                },
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ],
            'temperature': request_data.get('temperature', 0.7),
            'max_tokens': request_data.get('max_tokens', 1024),
            'stream': request_data.get('stream', False)
        }
        return adapted_data
    
    def adapt_from_vscode(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt VS Code extension format to OpenAI format
        """
        # Similar conversion to OpenAI format
        prompt = request_data.get('text', '') or request_data.get('prompt', '')
        
        # Handle potential array of files/context
        files = request_data.get('files', [])
        context = ""
        
        if files:
            for file in files:
                filename = file.get('name', 'unnamed')
                content = file.get('content', '')
                if content:
                    context += f"\nFile: {filename}\n```\n{content}\n```\n"
        
        # Convert to OpenAI format
        adapted_data = {
            'model': request_data.get('model', 'gpt-4'),
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an AI programming assistant integrated in VS Code.'
                }
            ],
            'temperature': request_data.get('temperature', 0.7),
            'max_tokens': request_data.get('max_tokens', 1024),
            'stream': request_data.get('stream', False)
        }
        
        # Add context as system message if available
        if context:
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"Context: {context}"
            })
            
        # Add prompt as user message
        if prompt:
            adapted_data['messages'].append({
                'role': 'user',
                'content': prompt
            })
        return adapted_data
    
    def adapt_from_chatgpt_desktop(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt ChatGPT desktop app format to OpenAI format
        """
        # Extract what we can from the ChatGPT desktop request
        prompt = request_data.get('prompt', '')
        context = request_data.get('context', '')
        
        if not prompt and 'messages' in request_data:
            # Already has messages array, might be using OpenAI-like format
            return request_data
            
        # Convert to OpenAI format
        adapted_data = {
            'model': request_data.get('model', 'gpt-4'),
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are ChatGPT, a large language model trained by OpenAI.'
                }
            ],
            'temperature': request_data.get('temperature', 0.7),
            'max_tokens': request_data.get('max_tokens', 2048),
            'stream': request_data.get('stream', True)
        }
        
        # Add context as system message if available
        if context:
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"Context: {context}"
            })
            
        # Add prompt as user message
        if prompt:
            adapted_data['messages'].append({
                'role': 'user',
                'content': prompt
            })
        return adapted_data
    
    def adapt_from_claude_desktop(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Claude desktop app format to OpenAI format
        """
        # Extract what we can from the Claude desktop request
        prompt = request_data.get('prompt', '')
        context = request_data.get('context', '')
        
        if not prompt and 'messages' in request_data:
            # Already has messages array, might be using OpenAI-like format
            return request_data
            
        # Convert to OpenAI format
        adapted_data = {
            'model': request_data.get('model', 'claude-3-opus'),
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are Claude, an AI assistant by Anthropic.'
                }
            ],
            'temperature': request_data.get('temperature', 0.7),
            'max_tokens': request_data.get('max_tokens', 2048),
            'stream': request_data.get('stream', True)
        }
        
        # Add context as system message if available
        if context:
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"Context: {context}"
            })
            
        # Add prompt as user message
        if prompt:
            adapted_data['messages'].append({
                'role': 'user',
                'content': prompt
            })
        return adapted_data
    
    def adapt_from_codeium(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Codeium format to OpenAI format
        """
        # Extract context from document 
        document = request_data.get('document', {})
        position = request_data.get('position', {})
        language = request_data.get('language', '')
        
        # Extract code context
        content = document.get('content', '')
        if content and position:
            line = position.get('line', 0)
            character = position.get('character', 0)
            
            # Split content into lines
            lines = content.split('\n')
            
            # Get context before and after cursor
            before_lines = lines[:line]
            current_line = lines[line] if line < len(lines) else ""
            after_lines = lines[line+1:] if line < len(lines) else []
            
            # Get prefix and suffix
            prefix = '\n'.join(before_lines) + '\n' + current_line[:character]
            suffix = current_line[character:] + '\n' + '\n'.join(after_lines)
            
            # Convert to OpenAI format
            adapted_data = {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are Codeium, an AI code completion assistant for {language}.' if language else 'You are Codeium, an AI code completion assistant.'
                    },
                    {
                        'role': 'user',
                        'content': f"Complete the code at the cursor position:\n\n```{language}\n{prefix}[CURSOR]{suffix}\n```"
                    }
                ],
                'temperature': 0.2,
                'max_tokens': 256,
                'stream': True
            }
            return adapted_data
        
        # Fallback for unknown format
        return request_data
    
    def adapt_from_tabnine(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt TabNine format to OpenAI format
        """
        # Extract content before and after cursor
        before = request_data.get('before', '')
        after = request_data.get('after', '')
        language = request_data.get('language', '')
        
        if before is not None:
            # Convert to OpenAI format
            adapted_data = {
                'model': 'gpt-4',
                'messages': [
                    {
                        'role': 'system',
                        'content': f'You are TabNine, an AI code completion assistant for {language}.' if language else 'You are TabNine, an AI code completion assistant.'
                    },
                    {
                        'role': 'user',
                        'content': f"Complete the code at the cursor position:\n\n```{language}\n{before}[CURSOR]{after}\n```"
                    }
                ],
                'temperature': 0.2,
                'max_tokens': 64,
                'stream': False
            }
            return adapted_data
            
        # Fallback for unknown format
        return request_data
    
    def adapt_from_sourcegraph_cody(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Sourcegraph Cody format to OpenAI format
        """
        query = request_data.get('query', '')
        codebase = request_data.get('codebase', '')
        files = request_data.get('files', [])
        
        # Build context from files
        context = ""
        if files:
            for file in files:
                filename = file.get('path', 'unnamed')
                content = file.get('content', '')
                if content:
                    context += f"\nFile: {filename}\n```\n{content}\n```\n"
        
        # Convert to OpenAI format
        adapted_data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': f'You are Cody, an AI programming assistant from Sourcegraph. You have access to the {codebase} codebase.' if codebase else 'You are Cody, an AI programming assistant from Sourcegraph.'
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1024,
            'stream': False
        }
        
        # Add context as system message if available
        if context:
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"Context: {context}"
            })
            
        # Add query as user message
        if query:
            adapted_data['messages'].append({
                'role': 'user',
                'content': query
            })
            
        return adapted_data
    
    def adapt_from_amazon_codewhisperer(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Amazon CodeWhisperer format to OpenAI format
        """
        file_context = request_data.get('fileContext', '')
        code_reference = request_data.get('codeReference', '')
        language = request_data.get('language', '')
        prompt = request_data.get('query', '') or request_data.get('prompt', '')
        
        # Build context
        full_context = ""
        if file_context:
            full_context += f"File Context:\n```{language}\n{file_context}\n```\n\n"
        if code_reference:
            full_context += f"Code Reference:\n```{language}\n{code_reference}\n```\n\n"
            
        # Convert to OpenAI format
        adapted_data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': f'You are Amazon CodeWhisperer, an AI coding assistant specialized in {language}.' if language else 'You are Amazon CodeWhisperer, an AI coding assistant.'
                }
            ],
            'temperature': 0.2,
            'max_tokens': 512,
            'stream': False
        }
        
        # Add context if available
        if full_context:
            adapted_data['messages'].append({
                'role': 'system',
                'content': full_context
            })
            
        # Add prompt if available
        if prompt:
            adapted_data['messages'].append({
                'role': 'user',
                'content': prompt
            })
        else:
            # Default prompt
            adapted_data['messages'].append({
                'role': 'user',
                'content': "Provide code completion based on the context."
            })
            
        return adapted_data
    
    def adapt_from_replit(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Replit format to OpenAI format
        """
        code = request_data.get('code', '')
        language = request_data.get('language', '')
        prompt = request_data.get('prompt', '')
        
        # Convert to OpenAI format
        adapted_data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': f'You are an AI programming assistant integrated in Replit, specialized in {language}.' if language else 'You are an AI programming assistant integrated in Replit.'
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1024,
            'stream': False
        }
        
        # Add code context if available
        if code:
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"Code context:\n```{language}\n{code}\n```"
            })
            
        # Add prompt if available
        if prompt:
            adapted_data['messages'].append({
                'role': 'user',
                'content': prompt
            })
        else:
            # Default prompt
            adapted_data['messages'].append({
                'role': 'user',
                'content': "Provide assistance with this code."
            })
            
        return adapted_data
    
    def adapt_from_kite(self, request_data: Dict, headers: Optional[Dict] = None) -> Dict:
        """
        Adapt Kite format to OpenAI format
        """
        editor = request_data.get('editor', '')
        filename = request_data.get('filename', '')
        buffer = request_data.get('buffer', '')
        cursor = request_data.get('cursor', {})
        line = cursor.get('line', 0) if cursor else 0
        column = cursor.get('column', 0) if cursor else 0
        
        # Convert to OpenAI format
        adapted_data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': f'You are Kite, an AI programming assistant integrated in {editor}.' if editor else 'You are Kite, an AI programming assistant.'
                }
            ],
            'temperature': 0.2,
            'max_tokens': 64,
            'stream': False
        }
        
        # Add code context if available
        if buffer:
            # Get language from filename
            language = ''
            if filename and '.' in filename:
                ext = filename.split('.')[-1].lower()
                language_map = {
                    'py': 'python',
                    'js': 'javascript',
                    'ts': 'typescript',
                    'jsx': 'javascript',
                    'tsx': 'typescript',
                    'html': 'html',
                    'css': 'css',
                    'java': 'java',
                    'c': 'c',
                    'cpp': 'cpp',
                    'cs': 'csharp',
                    'go': 'go',
                    'rb': 'ruby',
                    'php': 'php',
                    'rs': 'rust'
                }
                language = language_map.get(ext, '')
                
            # Split buffer into lines
            lines = buffer.split('\n')
            
            # Add cursor position indicator
            if 0 <= line < len(lines) and 0 <= column <= len(lines[line]):
                before = lines[line][:column]
                after = lines[line][column:]
                lines[line] = before + "[CURSOR]" + after
                
            # Join lines back together
            buffer_with_cursor = '\n'.join(lines)
                
            adapted_data['messages'].append({
                'role': 'system',
                'content': f"File: {filename}\n\nCode:\n```{language}\n{buffer_with_cursor}\n```"
            })
            
        # Add a user message requesting completion
        adapted_data['messages'].append({
            'role': 'user',
            'content': "Please provide code completion at the cursor position."
        })
            
        return adapted_data