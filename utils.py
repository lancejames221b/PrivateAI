"""
Private AI 🕵️ - Detective Utilities

This module provides detective utility functions for the Private AI system,
investigating formats and adapting between different AI systems while protecting sensitive information.

Author: Lance James @ Unit 221B
"""

import re
import json
import os
from typing import Dict, List, Tuple, Any, Optional
from cryptography.fernet import Fernet, InvalidToken
from logger import get_logger, log_exception

# Get logger for this module
logger = get_logger("ai-security-proxy", "logs/proxy.log")

# Try to import optional dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy module not available. Using regex-only transformations.")

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import RecognizerResult, OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logger.warning("Presidio modules not available. Using regex-only transformations.")

# Regular expression patterns for detecting sensitive information
PATTERNS = {
    "API_KEY": r'(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}|api[_-]?key[=: "\']+[0-9a-zA-Z\-_]{20,}',
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "IP_ADDRESS": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    "IPV6_ADDRESS": r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
    "AWS_KEY": r'AKIA[0-9A-Z]{16}',
    "PASSWORD": r'password[=: "\']+[^ ]{8,}',
    "LICENSE_KEY": r'license[_-]?key[=: "\']+[0-9a-zA-Z\-]{5,}',
    "GITHUB_TOKEN": r'gh[pousr]_[0-9a-zA-Z]{36}',
    "PRIVATE_KEY": r'-----BEGIN( RSA)? PRIVATE KEY-----',
    "MAC_ADDRESS": r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b',
    "DOMAIN": r'\b(?:(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9])\b',
    "URL": r'https?://[^\s/$.?#].[^\s]*',
    "GEO_COORDINATES": r'\b-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+\b',
    "PHONE_NUMBER": r'\+?\d{1,3}[- ]?\(?\d{3}\)?[- ]?\d{3,4}[- ]?\d{4}',
    "PASSPORT_NUMBER": r'\b[A-Z]{1,2}\d{6,9}\b',
}

# AI Inference prevention patterns - to detect information that could be used to infer sensitive details
AI_INFERENCE_PATTERNS = {
    "INTERNAL_PROJECT_NAME": r'project[: "\'=]+([A-Za-z0-9_-]{3,})',
    "API_ENDPOINT": r'api\.internal\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}',
    "INTERNAL_IP_RANGE": r'10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}',
    "SERVER_PATH": r'/var/www/[a-zA-Z0-9_/.-]+|/home/[a-zA-Z0-9_/.-]+|/srv/[a-zA-Z0-9_/.-]+',
    "DB_CONNECTION_STRING": r'(jdbc|mongodb|mysql|postgresql):.*?://.+?\.[a-zA-Z]{2,}(:\d+)?/[a-zA-Z0-9_-]+',
    "CLOUD_RESOURCE": r'arn:aws:[a-zA-Z0-9-]+:[a-zA-Z0-9-]*:\d{12}:[a-zA-Z0-9-/]+',
    "SESSION_IDENTIFIER": r'sess-[a-zA-Z0-9]{16}|token-[a-zA-Z0-9]{16}',
    "CI_CD_CONFIG": r'\.github/workflows/[a-zA-Z0-9_.-]+\.yml|\.gitlab-ci\.yml',
    "ENV_VARIABLE": r'[A-Z][A-Z0-9_]{2,}=[a-zA-Z0-9_/+.-]+',
}

# SentinelOne specific patterns
SENTINEL_PATTERNS = {
    "SENTINEL_AGENT_ID": r'([0-9a-fA-F]{8}[-]?[0-9a-fA-F]{4}[-]?[0-9a-fA-F]{4}[-]?[0-9a-fA-F]{4}[-]?[0-9a-fA-F]{12})',
    "SENTINEL_API_TOKEN": r'[0-9a-zA-Z]{40,80}',
    "SENTINEL_CONSOLE_URL": r'(https?://[a-zA-Z0-9][-a-zA-Z0-9.]*[-a-zA-Z0-9]\.[a-zA-Z0-9][-a-zA-Z0-9.]*[-a-zA-Z0-9]\.?(?:\.sentinelone\.net|\.s1-eu\.com|\.s1-apac\.com|\.s1-us\.com))',
    "SENTINEL_GROUP_ID": r'([0-9]{5,})',
    "SENTINEL_SITE_ID": r'([0-9]{5,})',
}

# Initialize Presidio NLP engine and analyzer
def initialize_presidio():
    if not SPACY_AVAILABLE or not PRESIDIO_AVAILABLE:
        logger.warning("Cannot initialize Presidio: required dependencies not available")
        return None
    
    try:
        # Set up the NLP engine with spaCy
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
        }
        
        # Download spaCy model if not already downloaded
        try:
            spacy.load("en_core_web_lg")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_lg"], 
                         check=True)
        
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        # Set up the analyzer with built-in recognizers
        registry = RecognizerRegistry()
        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
        
        # Add custom recognizers for our patterns
        for name, pattern in {**PATTERNS, **SENTINEL_PATTERNS, **AI_INFERENCE_PATTERNS}.items():
            # Create pattern recognizer
            custom_recognizer = PatternRecognizer(
                supported_entity=name.upper(),
                name=f"{name}_recognizer",
                patterns=[{"name": name, "regex": pattern, "score": 0.85}]
            )
            registry.add_recognizer(custom_recognizer)
        
        logger.info("Presidio analyzer initialized successfully")
        return analyzer
    except Exception as e:
        log_exception(logger, e, "initialize_presidio")
        logger.info("Falling back to regex-based detection")
        return None

# Initialize Presidio anonymizer
def initialize_anonymizer():
    if not PRESIDIO_AVAILABLE:
        logger.warning("Cannot initialize Presidio anonymizer: required dependencies not available")
        return None
    
    try:
        anonymizer = AnonymizerEngine()
        logger.info("Presidio anonymizer initialized successfully")
        return anonymizer
    except Exception as e:
        log_exception(logger, e, "initialize_anonymizer")
        return None

# Database encryption class for secure storage
class DatabaseEncryption:
    def __init__(self):
        """Initialize database encryption with a key"""
        try:
            # Try to load key from environment or generate a new one
            key_str = os.environ.get('DB_ENCRYPTION_KEY')
            if key_str:
                # Use provided key
                self.key = key_str.encode()
            else:
                # Generate a new key if none exists
                self.key = Fernet.generate_key()
                logger.info("Generated new database encryption key")
            
            self.cipher = Fernet(self.key)
            logger.info("Database encryption initialized successfully")
        except Exception as e:
            log_exception(logger, e, "DatabaseEncryption initialization")
            # Fallback to a dummy cipher that doesn't actually encrypt
            self.cipher = None
    
    def encrypt(self, text):
        """Encrypt a string value"""
        if not text or not self.cipher:
            return text
        
        try:
            return self.cipher.encrypt(text.encode()).decode()
        except Exception as e:
            log_exception(logger, e, "DatabaseEncryption.encrypt")
            logger.warning(f"Returning unencrypted text due to encryption failure")
            return text
    
    def decrypt(self, encrypted_text):
        """Decrypt an encrypted string value"""
        if not encrypted_text or not self.cipher:
            return encrypted_text
        
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except InvalidToken:
            logger.warning("Invalid token during decryption, returning original")
            return encrypted_text
        except Exception as e:
            log_exception(logger, e, "DatabaseEncryption.decrypt")
            logger.warning(f"Returning original text due to decryption failure")
            return encrypted_text

# Global variables for Presidio engines
presidio_analyzer = initialize_presidio()
presidio_anonymizer = initialize_anonymizer()
presidio_anonymizer = initialize_anonymizer()

def get_domain_blocklist():
    """
    Load domain blocklist from the data file
    Returns a list of domains to block
    """
    blocklist = []
    try:
        blocklist_file = os.path.join(os.path.dirname(__file__), 'data', 'domain_blocklist.txt')
        if os.path.exists(blocklist_file):
            with open(blocklist_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        blocklist.append(line)
            logger.info(f"Loaded {len(blocklist)} domains from blocklist")
        else:
            logger.warning(f"Domain blocklist file not found at {blocklist_file}")
    except Exception as e:
        log_exception(logger, e, "get_domain_blocklist")
        logger.error("Using empty domain blocklist due to loading error")
    
    return blocklist

def get_custom_patterns():
    """
    Load custom patterns from the admin panel configuration
    """
    try:
        if os.path.exists('data/custom_patterns.json'):
            with open('data/custom_patterns.json', 'r') as f:
                custom_patterns = json.load(f)
                
                # Convert to format used by the detection system
                patterns = {}
                for name, pattern_data in custom_patterns.items():
                    if pattern_data.get('is_active', True):
                        # Add entity type to the pattern name for better tracking
                        entity_type = pattern_data.get('entity_type', 'GENERIC')
                        pattern_key = f"{entity_type.lower()}_{name}"
                        patterns[pattern_key] = pattern_data['pattern']
                
                return patterns
    except Exception as e:
        log_exception(logger, e, "get_custom_patterns")
        logger.error("Using empty custom patterns due to loading error")
    
    return {}

def apply_regex_patterns(text: str) -> List[Dict]:
    """
    Apply regex patterns to find potentially sensitive information.
    Returns a list of entities with their positions in the text.
    """
    entities = []
    
    # Combine built-in and custom patterns
    patterns = REGEX_PATTERNS.copy()
    custom_patterns = get_custom_patterns()
    
    # Get domain blocklist
    domain_blocklist = get_domain_blocklist()
    
    # Check if we should block all domains
    block_all_domains = os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true'
    
    # Add custom patterns, prioritized by their priority setting
    for name, pattern_data in custom_patterns.items():
        if pattern_data.get('is_active', True):
            pattern = pattern_data.get('pattern')
            entity_type = pattern_data.get('entity_type', 'CUSTOM')
            priority = int(pattern_data.get('priority', 2))  # Default to medium priority
            
            if pattern:
                patterns.append({
                    'name': name,
                    'pattern': pattern,
                    'entity_type': entity_type,
                    'priority': priority
                })
    
    # Sort patterns by priority (1=high, 2=medium, 3=low)
    patterns.sort(key=lambda x: x.get('priority', 2))
    
    # Apply each pattern
    for pattern_data in patterns:
        pattern_string = pattern_data['pattern']
        entity_type = pattern_data['entity_type']
        
        try:
            pattern = re.compile(pattern_string, re.IGNORECASE)
            for match in pattern.finditer(text):
                match_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Special handling for domains
                if entity_type == 'DOMAIN':
                    # If block_all_domains is true, match all domains
                    # Otherwise, only match domains in the blocklist
                    domain_in_blocklist = False
                    
                    # Check if the matched domain is in the blocklist
                    for domain in domain_blocklist:
                        if domain.lower() in match_text.lower():
                            domain_in_blocklist = True
                            break
                    
                    # Skip if we're not blocking all domains and this domain isn't in the blocklist
                    if not block_all_domains and not domain_in_blocklist:
                        continue
                
                # Only add entities that don't overlap with existing ones
                overlap = False
                for entity in entities:
                    if (start_pos <= entity['end'] and end_pos >= entity['start']):
                        overlap = True
                        # If new match is longer, replace the existing one
                        if (end_pos - start_pos) > (entity['end'] - entity['start']):
                            entity['start'] = start_pos
                            entity['end'] = end_pos
                            entity['word'] = match_text
                            entity['entity'] = entity_type
                        break
                
                if not overlap:
                    entities.append({
                        'start': start_pos,
                        'end': end_pos,
                        'word': match_text,
                        'entity': entity_type,
                        'score': 1.0
                    })
        except re.error as regex_err:
            logger.error(f"Invalid regex pattern '{pattern_string}': {str(regex_err)}")
            continue
        except Exception as e:
            log_exception(logger, e, f"apply_regex_patterns for pattern '{pattern_string}'")
            continue
    
    return entities

def is_potentially_sensitive(text: str) -> bool:
    """
    Quick check if text might contain sensitive information
    """
    # Always check all messages when domain blocklisting is enabled
    if get_domain_blocklist():
        return True
    
    # Check if text contains any of the key terms that might indicate sensitive data
    sensitive_terms = ['api', 'key', 'secret', 'token', 'password', 'credential', 
                      'access', 'private', 'confidential', 'restricted',
                      'sentinelone', 'sentinel', 'agent', 'console', 'site',
                      'internal', 'project', 'server', 'database', 'endpoint',
                      'session', 'vpc', 'subnet', 'azure', 'aws', 'gcp']
    
    for term in sensitive_terms:
        if term.lower() in text.lower():
            return True
    
    # Check if any regex pattern matches (including custom patterns)
    all_patterns = {}
    all_patterns.update(PATTERNS)
    all_patterns.update(SENTINEL_PATTERNS)
    all_patterns.update(AI_INFERENCE_PATTERNS)
    all_patterns.update(get_custom_patterns())
    
    for pattern in all_patterns.values():
        try:
            if re.search(pattern, text):
                return True
        except:
            # Skip invalid patterns
            continue
            
    return False

def safe_json_loads(text: str) -> Tuple[Optional[Dict], bool]:
    """
    Safely attempt to parse JSON, return (result, success)
    """
    try:
        return json.loads(text), True
    except (json.JSONDecodeError, TypeError):
        return None, False

def log_transformation(original: str, transformed: str, entities: List[Dict]) -> None:
    """
    Log transformation details for audit purposes
    """
    if not entities:
        return
        
    logger.info(f"Transformed {len(entities)} entities")
    
    # Group entities by type for cleaner logs
    entity_types = {}
    for entity in entities:
        entity_type = entity.get('entity', 'UNKNOWN')
        if entity_type not in entity_types:
            entity_types[entity_type] = 0
        entity_types[entity_type] += 1
    
    # Log summary by entity type
    for entity_type, count in entity_types.items():
        logger.info(f"  {entity_type}: {count} entities")
    
    # Log details at debug level
    for entity in entities:
        entity_type = entity.get('entity', 'UNKNOWN')
        score = entity.get('score', 0.0)
        word = entity.get('word', '')
        # Don't log full value for security, just length and preview
        word_preview = word[:3] + '...' + word[-3:] if len(word) > 10 else word
        logger.debug(f"Entity: {entity_type}, Length: {len(word)}, Preview: {word_preview}, Score: {score}")
        
    # Log character count difference for monitoring
    logger.debug(f"Original length: {len(original)}, Transformed length: {len(transformed)}")

def transform_url_parameters(url):
    """Transform sensitive data in URL parameters"""
    if '?' not in url:
        return url
        
    base_url, query_string = url.split('?', 1)
    params = query_string.split('&')
    transformed_params = []
    
    for param in params:
        if '=' not in param:
            transformed_params.append(param)
            continue
            
        key, value = param.split('=', 1)
        
        # Check if this parameter contains sensitive info
        should_transform = False
        for pattern_name, pattern in PATTERNS.items():
            if re.search(pattern, value, re.IGNORECASE):
                should_transform = True
                logger.info(f"Found sensitive data in URL param {key}")
                break
                
        # Check if it's a domain and we're blocking all domains
        if not should_transform and key.lower() in ('domain', 'site', 'url', 'website', 'host'):
            block_all = os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true'
            if block_all:
                should_transform = True
                logger.info(f"Blocking domain in URL param {key} (BLOCK_ALL_DOMAINS=true)")
        
        if should_transform:
            # Replace the value with a placeholder
            new_value = f"REDACTED_{key.upper()}_{os.urandom(4).hex()}"
            transformed_params.append(f"{key}={new_value}")
        else:
            transformed_params.append(param)
    
    return f"{base_url}?{'&'.join(transformed_params)}"

def detect_and_adapt_ai_format(request_data, headers=None):
    """
    Detect the AI API format of the request and convert it to a standard format if needed.
    This function is used to support multiple AI API formats including IDE-specific ones.
    
    Args:
        request_data (dict): The request data as a Python dictionary
        headers (dict, optional): The request headers
        
    Returns:
        tuple: (adapted_data, format_detected, adaptation_needed)
            - adapted_data: The adapted request data, or original if no adaptation needed
            - format_detected: String identifying the detected format (e.g. 'openai', 'github-copilot', 'cursor')
            - adaptation_needed: Boolean indicating whether adaptation was performed
    """
    if not request_data:
        return request_data, 'unknown', False
        
    adaptation_needed = False
    format_detected = 'unknown'
    adapted_data = request_data
    # Wrap the entire function body in a try-except block
    try:
        # Check for standard OpenAI format
        # Check for standard OpenAI format
        if 'model' in request_data and ('messages' in request_data or 'prompt' in request_data):
            format_detected = 'openai'
            # This is already in OpenAI format, no adaptation needed
            return request_data, format_detected, False
            
        # Check for Anthropic format
        if 'model' in request_data and 'prompt' in request_data and isinstance(request_data.get('prompt'), str) and \
           request_data.get('prompt', '').startswith('\n\nHuman:'):
            format_detected = 'anthropic'
            # Convert Anthropic format to OpenAI format
            messages = []
            prompt = request_data['prompt']
            
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
            
            adapted_data = {
                'model': request_data['model'],
                'messages': messages,
                'temperature': request_data.get('temperature', 0.7),
                'max_tokens': request_data.get('max_tokens', 1024),
                'stream': request_data.get('stream', False)
            }
            adaptation_needed = True
        
        # Check for GitHub Copilot format
        elif 'jsonrpc' in request_data and 'method' in request_data:
            format_detected = 'github-copilot'
            
            # Handle different Copilot methods
            if request_data['method'] == 'getCompletions':
                params = request_data.get('params', {})
                doc_context = params.get('doc', {}).get('source', '')
                prefix = params.get('doc', {}).get('prefix', '')
                suffix = params.get('doc', {}).get('suffix', '')
                
                # Convert to OpenAI format
                adapted_data = {
                    'model': 'gpt-4',  # Default to GPT-4 for code completions
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an AI programming assistant. Provide code completions based on the given context.'
                        },
                        {
                            'role': 'user',
                            'content': f"Complete the following code:\n\n```\n{prefix}[CURSOR HERE]{suffix}\n```\n\nContext:\n```\n{doc_context}\n```"
                        }
                    ],
                    'temperature': 0.2,  # Lower temperature for code completion
                    'max_tokens': 512,
                    'stream': True
                }
                adaptation_needed = True
            
            # Handle other Copilot methods like 'getCompletionsCycling' or 'provideInlineCompletions'
            elif request_data['method'] in ['getCompletionsCycling', 'provideInlineCompletions']:
                params = request_data.get('params', {})
                
                # Try to extract relevant information
                doc = params.get('doc', {})
                if not doc and 'documents' in params:
                    doc = params.get('documents', [{}])[0]
                
                # Extract code context
                prefix = doc.get('prefix', '')
                suffix = doc.get('suffix', '')
                source = doc.get('source', '')
                
                # Convert to OpenAI format similar to getCompletions
                adapted_data = {
                    'model': 'gpt-4',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are an AI programming assistant. Provide inline code completions.'
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
                adaptation_needed = True
                
        # Check for Cursor AI format
        elif headers and any(header.lower().startswith('x-cursor') for header in headers):
            format_detected = 'cursor'
            
            # Extract what we can from the Cursor request
            prompt = request_data.get('prompt', '')
            context = request_data.get('context', '')
            
            if not prompt and 'messages' in request_data:
                # Already has messages array, might be using OpenAI-like format
                return request_data, format_detected, False
                
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
            adaptation_needed = True
            
        # JetBrains AI format
        elif headers and any(header.lower().startswith('x-jetbrains') for header in headers):
            format_detected = 'jetbrains'
            
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
            adaptation_needed = True
            
        # VS Code extension format
        elif headers and any(header.lower().startswith('x-vscode') for header in headers):
            format_detected = 'vscode'
            
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
            adaptation_needed = True
            
        # Check for ChatGPT desktop app format
        elif headers and any(header.lower().startswith('x-chatgpt') for header in headers):
            format_detected = 'chatgpt-desktop'
            
            # Extract what we can from the ChatGPT desktop request
            prompt = request_data.get('prompt', '')
            context = request_data.get('context', '')
            
            if not prompt and 'messages' in request_data:
                # Already has messages array, might be using OpenAI-like format
                return request_data, format_detected, False
                
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
            adaptation_needed = True
            
        # Check for Claude desktop app format
        elif headers and any(header.lower().startswith('x-claude') for header in headers):
            format_detected = 'claude-desktop'
            
            # Extract what we can from the Claude desktop request
            prompt = request_data.get('prompt', '')
            context = request_data.get('context', '')
            
            if not prompt and 'messages' in request_data:
                # Already has messages array, might be using OpenAI-like format
                return request_data, format_detected, False
                
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
            adaptation_needed = True
            
        # Add more format detections here as needed
        
    except Exception as e:
        logger.error(f"Error in format detection: {str(e)}")
        return request_data, 'unknown', False
        
    return adapted_data, format_detected, adaptation_needed

# Function to adapt responses back to the original format
def adapt_ai_response(response_data, original_format):
    """
    Adapt the response back to the original request format
    
    Args:
        response_data (dict): The response data in OpenAI format
        original_format (str): The original format to convert back to
        
    Returns:
        dict: The adapted response data
    """
    try:
        # If format is already OpenAI, no need to adapt
        if original_format == 'openai':
            return response_data
            
        # Handle conversion to GitHub Copilot format
        if original_format == 'github-copilot':
            completion = ""
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                    
                    # Extract code completion from content
                    # Look for code blocks or the most relevant part
                    import re
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
            
        # Handle conversion to Cursor AI format
        elif original_format == 'cursor':
            text = ""
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    text = choice['message']['content']
                    
            return {
                "response": text,
                "status": "success"
            }
            
        # Handle conversion to JetBrains AI format
        elif original_format == 'jetbrains':
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
            
        # Handle conversion to VS Code format
        elif original_format == 'vscode':
            text = ""
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    text = choice['message']['content']
                    
            return {
                "response": text,
                "success": True
            }
            
        # Handle conversion to Anthropic format
        elif original_format == 'anthropic':
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
            
        # Add more format adaptations here as needed
            
        # If no specific format matched, return the original response
        return response_data
        
    except Exception as e:
        logger.error(f"Error adapting response format: {str(e)}")
        # Return original data in case of error
        return response_data


class DatabaseEncryption:
    """Class to handle database encryption"""
    
    def __init__(self):
        """Initialize the encryption key"""
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        self.encryption_enabled = True
        logger.info("Database encryption initialized successfully")
    
    def _get_or_create_key(self):
        """Get or create an encryption key"""
        key_file = "data/encryption.key"
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        try:
            if os.path.exists(key_file):
                with open(key_file, "rb") as f:
                    key = f.read()
                    # Validate the key
                    if len(key) != 44:  # Fernet keys are 44 bytes
                        raise ValueError("Invalid key format")
                    return key
            else:
                # Generate a new key
                key = Fernet.generate_key()
                with open(key_file, "wb") as f:
                    f.write(key)
                logger.info("Generated new database encryption key")
                return key
        except Exception as e:
            # Fallback to a hardcoded key (not ideal for production)
            logger.error(f"Error accessing encryption key file: {str(e)}")
            return Fernet.generate_key()
    
    def encrypt(self, data):
        """Encrypt data"""
        if not data:
            return data
        try:
            if isinstance(data, str):
                return self.cipher.encrypt(data.encode()).decode()
            else:
                return self.cipher.encrypt(str(data).encode()).decode()
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            return data
    
    def decrypt(self, data):
        """Decrypt data"""
        if not data:
            return data
        try:
            if isinstance(data, str):
                return self.cipher.decrypt(data.encode()).decode()
            else:
                return self.cipher.decrypt(str(data).encode()).decode()
        except InvalidToken:
            logger.warning("Invalid token during decryption")
            return data
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            return data
