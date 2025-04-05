#!/usr/bin/env python3
"""
Private AI 🕵️ - Your AI Security Detective

This privacy-preserving middleware intercepts HTTP/HTTPS traffic to AI APIs
and redacts sensitive information in both requests and responses.
Like a detective on the case, it protects your private data while allowing AI systems to work.

Author: Lance James @ Unit 221B
"""

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import urllib.error
import ssl
import json
import os
import re
import logging
import sys
import time
import signal
import threading
import traceback
from datetime import datetime
from pii_transform import detect_and_transform, restore_original_values
from utils import PATTERNS, AI_INFERENCE_PATTERNS, SENTINEL_PATTERNS, get_domain_blocklist
import http.client
from socketserver import ThreadingMixIn, TCPServer
import socket

# Configure logging with rotation
try:
    from logging.handlers import RotatingFileHandler
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Get log level from environment variable or default to INFO
    log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    
    # Configure logging with rotation (10MB max size, keep 5 backup files)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                "logs/aiproxy.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            ),
            logging.StreamHandler(sys.stdout)
        ]
    )
except ImportError:
    # Fallback to basic logging if RotatingFileHandler is not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/aiproxy.log", mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

logger = logging.getLogger("ai-security-proxy")
logger.info("Starting AI Security Proxy - Log initialized")

# Combined regex patterns
REGEX_PATTERNS = {**PATTERNS, **AI_INFERENCE_PATTERNS, **SENTINEL_PATTERNS}

# Global statistics for monitoring
STATS = {
    "requests_processed": 0,
    "requests_transformed": 0,
    "responses_transformed": 0,
    "errors": 0,
    "start_time": time.time()
}

# Thread-safe lock for updating stats
stats_lock = threading.Lock()

# Enhanced threading HTTP server with better error handling and performance
class ThreadingHTTPServer(ThreadingMixIn, TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    request_queue_size = 100  # Increase request queue for high traffic
    timeout = 60  # Socket timeout in seconds
    
    def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
        """Initialize the server with enhanced error handling"""
        # Set a more permissive socket timeout
        self.socket_timeout = 60
        
        # Call parent constructor
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)
        
        # Track active connections for graceful shutdown
        self.active_connections = set()
        self.connections_lock = threading.Lock()
        
        logger.info(f"Server initialized with queue size {self.request_queue_size} and timeout {self.timeout}s")
    
    def get_request(self):
        """Get a request and set socket timeout"""
        socket, addr = super().get_request()
        socket.settimeout(self.socket_timeout)
        
        # Track this connection
        with self.connections_lock:
            self.active_connections.add(socket)
            
        return socket, addr
    
    def shutdown(self):
        """Enhanced shutdown that closes all active connections"""
        logger.info("Shutting down server gracefully...")
        
        # Close all active connections
        with self.connections_lock:
            for sock in self.active_connections:
                try:
                    sock.close()
                except Exception as e:
                    logger.debug(f"Error closing socket: {str(e)}")
            self.active_connections.clear()
        
        # Call parent shutdown
        super().shutdown()
        logger.info("Server shutdown complete")
    
    def handle_error(self, request, client_address):
        """Handle errors that occur during request processing"""
        with stats_lock:
            STATS["errors"] += 1
            
        logger.error(f"Error processing request from {client_address}:")
        logger.error(traceback.format_exc())

# List of AI API domains to focus on
AI_API_DOMAINS = [
    # OpenAI API endpoints
    "api.openai.com",              # Standard OpenAI API
    "oai.azure.com",               # Azure OpenAI
    "api.openai.azure.com",        # Alternative Azure OpenAI endpoint
    "api.o.openai.com",            # Specialized o1/o3 models endpoints
    "chat.openai.com",             # ChatGPT web interface
    "platform.openai.com",         # OpenAI platform
    "*.openai.com",                # All OpenAI subdomains
    
    # Anthropic API endpoints
    "api.anthropic.com",           # Standard Anthropic API
    "api.claude.ai",               # Claude direct API
    "claude.ai",                   # Claude web interface
    "api-staging.anthropic.com",   # Anthropic staging environment
    "api-experimental.anthropic.com", # Experimental models endpoint
    "*.anthropic.com",             # All Anthropic subdomains
    "*.claude.ai",                 # All Claude subdomains
    
    # Google AI endpoints
    "api.gemini.google.com",       # Gemini API
    "generativelanguage.googleapis.com", # PaLM/Gemini API
    "vertex.ai",                   # Vertex AI hosting
    "us-central1-aiplatform.googleapis.com", # Regional Vertex AI
    "europe-west4-aiplatform.googleapis.com", # EU Vertex AI
    "ai.googleapis.com",           # Google AI API
    
    # OpenRouter endpoints
    "openrouter.ai",               # Main OpenRouter domain
    "api.openrouter.ai",           # OpenRouter API
    "openrouter.dev",              # Development endpoint
    "*.openrouter.ai",             # All subdomains
    "openrouter.helicone.ai",      # Helicone integration
    
    # IDE AI Assistant domains
    "vscode-copilot.githubusercontent.com",  # VS Code Copilot
    "api.githubcopilot.com",       # GitHub Copilot API
    "api.cursor.sh",               # Cursor AI
    "cursor.sh",                   # Cursor platform
    "vscode.dev",                  # VS Code Web
    "insiders.vscode.dev",         # VS Code Insiders
    "online.visualstudio.com",     # Visual Studio Online
    "copilot.github.com",          # GitHub Copilot
    "copilot-proxy.githubusercontent.com", # GitHub Copilot proxy
    "plugins.jetbrains.com",       # JetBrains AI Assistant
    "api-inference.nvidia.com",    # NVIDIA AI-powered tools
    "model-api.tabnine.com",       # TabNine AI completions
    "api.kite.com",                # Kite AI Completions
    "api.sourcegraph.com",         # Sourcegraph Cody
    "completion.kite.com",         # Kite completions endpoint
    "api.replit.com",              # Replit AI features
    "api.codeium.com",             # Codeium AI completion
    "api.aws.codewhisperer.amazon.com", # Amazon CodeWhisperer
    "chat.aws.codewhisperer.amazon.com", # Amazon CodeWhisperer Chat
    "api.adrenaline.dev",          # Adrenaline AI
    "api.tabnine.com",             # TabNine AI
    
    # Other major providers
    "api.cohere.ai",               # Cohere
    "api.cohere.com",              # Alternative Cohere endpoint
    "api.sonnet.ai",               # Specialized Claude API
    "api.replicate.com",           # Replicate
    
    # Open model providers
    "huggingface.co",              # Hugging Face
    "api.huggingface.co",          # Hugging Face API
    "huggingface.inference.endpoints", # HF inference endpoints
    "api-inference.huggingface.io", # HF inference API
    
    # Emerging providers
    "api.mistral.ai",              # Mistral AI
    "api.together.xyz",            # Together AI
    "api.perplexity.ai",           # Perplexity AI
    "api.deepseek.com",            # DeepSeek
    "api.deepseek.ai",             # Alternative DeepSeek endpoint
    "api.groq.com",                # Groq
    "api.groq.dev",                # Groq development endpoint
    "api.minimax.chat",            # MiniMax
    "api-inference.minimax.ai",    # MiniMax inference API 
    "api.aleph-alpha.com",         # Aleph Alpha
    "api.fireworks.ai",            # Fireworks AI
    "api.anyscale.com",            # Anyscale
    "api.qwen.ai",                 # Qwen AI (Alibaba)
    "api.stability.ai",            # Stability AI
    "api.meta.ai",                 # Meta AI models
    "llama-api.meta.com",          # Meta's Llama API
    
    # Development testing
    "httpbin.org",                 # Testing endpoint
]

# Simple class to represent a proxy request for easier transformation
class ProxyRequest:
    """
    A simple class to represent an HTTP request for proxy transformation.
    This makes it easier to transform the request properties before sending.
    """
    def __init__(self, url, method, headers, body=None):
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body
        
    def __str__(self):
        return f"ProxyRequest(url={self.url}, method={self.method}, headers={len(self.headers)} items, body_size={len(self.body) if self.body else 0})"

def should_process_url(url, content_type=None):
    """Determine if we should process this URL based on domain or content type"""
    try:
        # Extract domain from URL
        parts = urllib.parse.urlparse(url)
        domain = parts.netloc
        
        # Always process any request to AI API domains
        for ai_domain in AI_API_DOMAINS:
            # Handle wildcard domains
            if ai_domain.startswith('*.') and domain.endswith(ai_domain[2:]):
                logger.info(f"Processing wildcard AI API domain: {domain}")
                return True
            elif ai_domain in domain:
                logger.info(f"Processing AI API domain: {domain}")
                return True
                
        # Process if URL path matches OpenRouter API patterns
        openrouter_patterns = [
            "/api/v1/chat/completions",
            "/api/v1/completions",
            "/api/generation",
            "/v1/chat/completions",
        ]
        
        if any(pattern in parts.path for pattern in openrouter_patterns):
            logger.info(f"Processing OpenRouter API path: {parts.path}")
            return True
                
        # Process if URL contains AI-related keywords
        if any(kw in url.lower() for kw in ["openai", "gpt", "claude", "anthropic", "gemini", "llm", "openrouter"]):
            logger.info(f"Processing AI-related URL: {url}")
            return True
            
        # Process any requests with JSON content
        if content_type and content_type.startswith("application/json"):
            logger.info(f"Processing JSON content request: {url}")
            return True
            
        logger.info(f"Skipping non-AI URL: {url}")
        return False
    except Exception as e:
        logger.error(f"Error in should_process_url: {str(e)}")
        return False

def transform_url_parameters(url):
    """Transform sensitive data in URL parameters"""
    try:
        if '?' not in url:
            return url
            
        logger.info(f"Processing URL parameters: {url}")
        base_url, query_string = url.split('?', 1)
        
        # Parse the query string
        parsed_query = urllib.parse.parse_qs(query_string)
        logger.info(f"Parsed query parameters: {parsed_query}")
        
        # Transform each parameter value
        transformed_query = {}
        transformed_count = 0
        
        # Check if we should block all domains
        block_all_domains = os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true'
        logger.info(f"Block all domains setting: {block_all_domains}")
        
        # Get domain blocklist
        domain_blocklist = get_domain_blocklist()
        logger.info(f"Domain blocklist contains {len(domain_blocklist)} entries")
        
        for key, values in parsed_query.items():
            transformed_query[key] = []
            for value in values:
                # Don't transform empty values
                if not value:
                    transformed_query[key].append(value)
                    continue
                    
                # Special handling for domain parameters
                if key.lower() in ['domain', 'site', 'url', 'website', 'hostname', 'host']:
                    # Check if this is a domain we should block
                    should_block = block_all_domains
                    
                    if not should_block and domain_blocklist:
                        # Check against blocklist
                        for blocked_domain in domain_blocklist:
                            if blocked_domain.lower() in value.lower():
                                should_block = True
                                logger.info(f"Domain {value} matched blocklist entry {blocked_domain}")
                                break
                    
                    if should_block:
                        transformed_value, log = detect_and_transform(value)
                        transformed_query[key].append(transformed_value)
                        transformed_count += 1
                        logger.info(f"Transformed domain parameter {key} from '{value}' to '{transformed_value}'")
                        continue
                
                # Check if this parameter value contains sensitive data
                has_sensitive_data = False
                matched_pattern = None
                
                # Check each regex pattern
                for pattern_name, pattern in REGEX_PATTERNS.items():
                    if re.search(pattern, value, re.IGNORECASE):
                        has_sensitive_data = True
                        matched_pattern = pattern_name
                        logger.info(f"Found sensitive data in URL param {key}: matched pattern {pattern_name}")
                        break
                        
                # If sensitive, transform the value
                if has_sensitive_data:
                    transformed_value, log = detect_and_transform(value)
                    transformed_query[key].append(transformed_value)
                    transformed_count += 1
                    logger.info(f"Transformed URL parameter {key} from '{value}' to '{transformed_value}' (matched {matched_pattern})")
                else:
                    transformed_query[key].append(value)
        
        # If any values were transformed, rebuild the URL
        if transformed_count > 0:
            new_query = []
            for key, values in transformed_query.items():
                for value in values:
                    new_query.append(f"{key}={urllib.parse.quote(value)}")
            
            # Rebuild the URL
            new_url = f"{base_url}?{'&'.join(new_query)}"
            logger.info(f"Processed URL parameters: transformed {transformed_count} values")
            logger.info(f"New URL: {new_url}")
            return new_url
        
        return url
    except Exception as e:
        logger.error(f"Error transforming URL parameters: {str(e)}")
        return url

def transform_openrouter_request(request):
    """
    Handle OpenRouter specific headers and parameters.
    This function processes the request to add necessary headers for OpenRouter and
    transforms any model-specific parameters.
    
    Args:
        request: The HTTP request to transform
        
    Returns:
        Modified request with appropriate OpenRouter headers and parameters
    """
    try:
        # Check if this is an OpenRouter request
        if "openrouter" not in request.url.lower():
            return request
            
        # Log OpenRouter request
        logger.info(f"Processing OpenRouter request: {request.url}")
        
        # Preserve original Authorization if present
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            logger.info("Authorization header is present")
        else:
            logger.warning("Authorization header missing for OpenRouter request")
            
        # Add required OpenRouter headers if missing
        openrouter_headers = {
            "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "ai-security-proxy"),
            "X-Title": os.environ.get("OPENROUTER_TITLE", "AI Security Proxy"),
        }
        
        for header, value in openrouter_headers.items():
            if header not in request.headers:
                request.headers[header] = value
                logger.info(f"Added OpenRouter header: {header}")
                
        # Process request body for model-specific parameters if it's JSON
        if request.headers.get("content-type", "").startswith("application/json") and request.body:
            try:
                body = json.loads(request.body)
                
                # Handle model-specific parameters for different model types
                if "model" in body:
                    model = body["model"].lower()
                    
                    # Add reasoning_effort parameter for supported models
                    if any(model_name in model for model_name in ["o3-mini", "o1", "o1-mini", "o1-pro"]) and "reasoning_effort" not in body:
                        body["reasoning_effort"] = os.environ.get("DEFAULT_REASONING_EFFORT", "medium")
                        logger.info(f"Added reasoning_effort={body['reasoning_effort']} for {model}")
                    
                    # Add output_parsing parameter for Claude models
                    if "claude" in model and "output_parsing" not in body:
                        output_format = body.get("response_format", {}).get("type")
                        if output_format == "json":
                            body["output_parsing"] = "json"
                            logger.info(f"Added output_parsing=json for {model}")
                    
                    # Add specific parameters for Claude 3.7 models
                    if "claude-3-7" in model:
                        # Set appropriate temperature if not specified
                        if "temperature" not in body:
                            body["temperature"] = 0.7
                            logger.info(f"Added temperature=0.7 for {model}")
                        
                        # Add top_p if not specified
                        if "top_p" not in body:
                            body["top_p"] = 0.9
                            logger.info(f"Added top_p=0.9 for {model}")
                    
                    # Add specific parameters for GPT-4.5 Preview
                    if "gpt-4.5" in model or "gpt-4-5" in model:
                        # Set appropriate temperature if not specified
                        if "temperature" not in body:
                            body["temperature"] = 0.7
                            logger.info(f"Added temperature=0.7 for {model}")
                        
                        # Add top_p if not specified
                        if "top_p" not in body:
                            body["top_p"] = 0.95
                            logger.info(f"Added top_p=0.95 for {model}")
                    
                    # Add specific parameters for GPT-4o
                    if "gpt-4o" in model:
                        # Set appropriate temperature if not specified
                        if "temperature" not in body:
                            body["temperature"] = 0.7
                            logger.info(f"Added temperature=0.7 for {model}")
                
                # Update the request body with the modified parameters
                request.body = json.dumps(body)
                
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON body for OpenRouter request")
                
        return request
        
    except Exception as e:
        logger.error(f"Error in transform_openrouter_request: {str(e)}")
        return request

class AIProxyHandler(BaseHTTPRequestHandler):
    """Enhanced HTTP request handler with better error handling, security, and performance"""
    
    # Set timeout for socket operations
    timeout = 60
    
    # Class-level cache for domain blocklist to avoid repeated disk reads
    _domain_blocklist_cache = None
    _domain_blocklist_timestamp = 0
    _domain_blocklist_lock = threading.Lock()
    
    # Class-level request counter
    request_count = 0
    request_count_lock = threading.Lock()
    
    def __init__(self, *args, **kwargs):
        # Initialize request timer
        self.start_time = time.time()
        self.request_id = None
        
        # Call parent constructor
        super().__init__(*args, **kwargs)
    
    def setup(self):
        """Set up the connection"""
        # Generate a unique request ID
        with AIProxyHandler.request_count_lock:
            AIProxyHandler.request_count += 1
            self.request_id = f"{int(time.time())}-{AIProxyHandler.request_count}"
        
        # Call parent setup
        super().setup()
    
    def log_message(self, format, *args):
        """Enhanced logging with request ID"""
        logger.info(f"[{self.request_id}] {format % args}")
    
    def log_error(self, format, *args):
        """Enhanced error logging with request ID"""
        logger.error(f"[{self.request_id}] {format % args}")
    
    @classmethod
    def get_domain_blocklist(cls):
        """Get domain blocklist with caching"""
        current_time = time.time()
        
        # Check if we need to refresh the cache (every 5 minutes)
        with cls._domain_blocklist_lock:
            if cls._domain_blocklist_cache is None or current_time - cls._domain_blocklist_timestamp > 300:
                cls._domain_blocklist_cache = get_domain_blocklist()
                cls._domain_blocklist_timestamp = current_time
                logger.debug(f"Refreshed domain blocklist cache: {len(cls._domain_blocklist_cache)} entries")
            
            return cls._domain_blocklist_cache
    
    def do_CONNECT(self):
        """Handle HTTPS CONNECT requests with enhanced error handling"""
        try:
            logger.info(f"CONNECT request: {self.path}")
            
            # Extract host and port from the path
            host, port = self.path.split(':')
            
            # Check if this is an AI API
            if not any(ai_domain in host for ai_domain in AI_API_DOMAINS):
                logger.info(f"Skipping non-AI CONNECT: {host}")
                self.send_response(200, 'Connection Established')
                self.end_headers()
                return
                
            logger.info(f"Processing AI API CONNECT: {host}")
            
            # We would need to implement MITM for HTTPS here
            # This requires generating certificates on the fly
            # For now, we'll just establish the tunnel
            
            self.send_response(200, 'Connection Established')
            self.end_headers()
            
            # This is where we would implement MITM for HTTPS
            # But that's beyond the scope of this simple proxy
            
        except Exception as e:
            logger.error(f"Error handling CONNECT: {str(e)}")
            self.send_error(500, f"Error handling CONNECT: {str(e)}")
    
    def do_GET(self):
        """Handle GET requests"""
        self._handle_request()
    
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request()
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_request()
    
    def _handle_request(self):
        """Common logic for handling HTTP requests with enhanced monitoring and error handling"""
        try:
            # Update request stats
            with stats_lock:
                STATS["requests_processed"] += 1
            
            # Start request timer
            request_start = time.time()
            
            # Log request details
            client_ip = self.client_address[0]
            logger.info(f"[{self.request_id}] {self.command} {self.path} from {client_ip}")
            
            # Add security headers to all responses
            self.protocol_version = 'HTTP/1.1'
            
            # Extract content type
            content_type = self.headers.get('Content-Type', '')
            
            # Check request size limits
            if 'Content-Length' in self.headers:
                content_length = int(self.headers['Content-Length'])
                max_size = int(os.environ.get('MAX_REQUEST_SIZE', 10 * 1024 * 1024))  # Default 10MB
                if content_length > max_size:
                    logger.warning(f"[{self.request_id}] Request too large: {content_length} bytes (max: {max_size})")
                    self.send_error(413, "Request entity too large")
                    return
            
            # Rate limiting (simple implementation)
            rate_limit_enabled = os.environ.get('ENABLE_RATE_LIMITING', 'false').lower() == 'true'
            if rate_limit_enabled and hasattr(self.server, 'rate_limiter'):
                if not self.server.rate_limiter.allow_request(client_ip):
                    logger.warning(f"[{self.request_id}] Rate limit exceeded for {client_ip}")
                    self.send_error(429, "Too many requests")
                    return
            
            # Determine if we should process this URL
            if not should_process_url(self.path, content_type):
                logger.debug(f"[{self.request_id}] Passing through request without processing")
                self._proxy_request(self.path)
                return
                
            # Process the request based on method and content type
            if self.command in ['POST', 'PUT'] and content_type.startswith('application/json'):
                logger.debug(f"[{self.request_id}] Handling as JSON request")
                self._handle_json_request()
            else:
                # For GET or non-JSON requests, just transform URL parameters
                transformed_url = transform_url_parameters(self.path)
                self._proxy_request(transformed_url)
                
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            self.send_error(500, f"Error handling request: {str(e)}")
    
    def _handle_json_request(self):
        """Handle JSON POST/PUT requests with PII detection"""
        try:
            # Read the request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            logger.info(f"Request body (first 100 chars): {body[:100]}...")
            
            # Transform sensitive data in the request body
            transformed_body, log = detect_and_transform(body)
            
            if log:
                logger.info(f"Transformed request body: {len(log)} items replaced")
            
            # Make the request with the transformed body
            self._proxy_request(self.path, transformed_body)
            
        except Exception as e:
            logger.error(f"Error handling JSON request: {str(e)}")
            self.send_error(500, f"Error handling JSON request: {str(e)}")
    
    def _proxy_request(self, url, body=None):
        """Proxy the request to the destination server and return the response"""
        try:
            # Prepare the method and headers
            method = self.command
            headers = {key: value for key, value in self.headers.items()}
            target_url = url

            # Check if we should process this URL
            if should_process_url(target_url, headers.get('content-type')):
                # Create a proxy request object for transformations
                proxy_request = ProxyRequest(
                    url=target_url,
                    method=method,
                    headers=headers,
                    body=body
                )
                
                # Apply OpenRouter-specific transformations if needed
                proxy_request = transform_openrouter_request(proxy_request)
                
                # Update variables with potentially transformed request
                target_url = proxy_request.url
                method = proxy_request.method
                headers = proxy_request.headers
                body = proxy_request.body
                
                # Process the request content (handle PII, sensitive data, etc.)
                if body:
                    # For JSON content, transform sensitive data
                    if headers.get('content-type', '').startswith('application/json'):
                        transformed_body, log = detect_and_transform(body)
                        body = transformed_body
                        logger.info(f"Transformed request body for {target_url}")
                    
                    # Process URL parameters if present
                    if '?' in target_url:
                        transformed_url = transform_url_parameters(target_url)
                        if transformed_url != target_url:
                            logger.info(f"Transformed URL parameters: {target_url} -> {transformed_url}")
                            target_url = transformed_url
            
            # Create the request
            parsed_url = urllib.parse.urlparse(target_url)
            conn = http.client.HTTPSConnection(parsed_url.netloc)
            
            # Send the request
            conn.request(method, parsed_url.path + '?' + parsed_url.query if parsed_url.query else parsed_url.path, 
                        body, headers)
            
            # Get the response
            response = conn.getresponse()
            
            # Read response data
            response_data = response.read()
            
            # Get response headers
            response_headers = {k.lower(): v for k, v in response.getheaders()}
            
            # Process response content if needed
            content_type = response_headers.get('content-type', '')
            if should_process_url(target_url, content_type) and 'application/json' in content_type:
                # First, restore any placeholders that were used in the request
                restored_data = restore_original_values(response_data.decode('utf-8', errors='replace'))
                
                # Then transform any new sensitive data that might be in the response
                transformed_data, log = detect_and_transform(restored_data)
                response_data = transformed_data.encode('utf-8')
            
            # Send headers to client
            self.send_response(response.status)
            for key, value in response.getheaders():
                self.send_header(key, value)
            self.end_headers()
            
            # Send body to client
            self.wfile.write(response_data)
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error proxying request to {url}: {str(e)}")
            self.send_error(500, message=str(e))

# Simple rate limiter class
class RateLimiter:
    """Simple rate limiter for production use"""
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
        self.lock = threading.Lock()
        
    def allow_request(self, client_ip):
        """Check if a request from this IP is allowed based on rate limits"""
        current_time = time.time()
        minute_ago = current_time - 60
        
        with self.lock:
            # Clean up old entries
            self.request_counts = {ip: [timestamp for timestamp in timestamps if timestamp > minute_ago]
                                 for ip, timestamps in self.request_counts.items()}
            
            # Get this client's request timestamps
            timestamps = self.request_counts.get(client_ip, [])
            
            # Check if rate limit exceeded
            if len(timestamps) >= self.requests_per_minute:
                return False
                
            # Add current timestamp
            timestamps.append(current_time)
            self.request_counts[client_ip] = timestamps
            
            return True

# Health check endpoint handler
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler for health check endpoint"""
    def do_GET(self):
        """Handle GET requests to health check endpoint"""
        if self.path == '/health':
            # Calculate uptime
            uptime = time.time() - STATS["start_time"]
            
            # Prepare health data
            health_data = {
                "status": "healthy",
                "uptime": uptime,
                "requests_processed": STATS["requests_processed"],
                "requests_transformed": STATS["requests_transformed"],
                "responses_transformed": STATS["responses_transformed"],
                "errors": STATS["errors"],
                "version": "1.0.0-production"
            }
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode('utf-8'))
        else:
            self.send_error(404)

def run_proxy(port=8080, health_port=8081):
    """Run the proxy server with enhanced production features"""
    # Create signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down gracefully...")
        if 'proxy_server' in globals():
            proxy_server.shutdown()
        if 'health_server' in globals():
            health_server.shutdown()
        
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create rate limiter if enabled
    rate_limit_enabled = os.environ.get('ENABLE_RATE_LIMITING', 'false').lower() == 'true'
    rate_limiter = None
    if rate_limit_enabled:
        requests_per_minute = int(os.environ.get('RATE_LIMIT_RPM', 60))
        rate_limiter = RateLimiter(requests_per_minute)
        logger.info(f"Rate limiting enabled: {requests_per_minute} requests per minute per IP")
    
    # Determine bind address (localhost for dev, 0.0.0.0 for production)
    bind_addr = '0.0.0.0' if os.environ.get('FLASK_ENV') == 'production' else 'localhost'
    
    # Create and configure the proxy server
    proxy_server = ThreadingHTTPServer((bind_addr, port), AIProxyHandler)
    if rate_limiter:
        proxy_server.rate_limiter = rate_limiter
    
    # Start health check server if enabled
    health_check_enabled = os.environ.get('ENABLE_HEALTH_CHECK', 'true').lower() == 'true'
    if health_check_enabled:
        try:
            health_server = ThreadingHTTPServer((bind_addr, health_port), HealthCheckHandler)
            health_thread = threading.Thread(target=health_server.serve_forever, daemon=True)
            health_thread.start()
            logger.info(f"Health check endpoint available at http://{bind_addr}:{health_port}/health")
        except Exception as e:
            logger.error(f"Failed to start health check server: {str(e)}")
    
    # Log startup information
    logger.info(f"Starting AI Security Proxy on {bind_addr}:{port}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info(f"Process ID: {os.getpid()}")
    logger.info("Press Ctrl+C to stop")
    
    try:
        # Run the server
        proxy_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in proxy server: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        # Ensure clean shutdown
        logger.info("Stopping AI Security Proxy")
        proxy_server.shutdown()
        
        # Log final stats
        uptime = time.time() - STATS["start_time"]
        logger.info(f"Server ran for {uptime:.2f} seconds")
        logger.info(f"Processed {STATS['requests_processed']} requests")
        logger.info(f"Transformed {STATS['requests_transformed']} requests and {STATS['responses_transformed']} responses")
        logger.info(f"Encountered {STATS['errors']} errors")

if __name__ == "__main__":
    try:
        # Create required directories
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Load environment variables from .env file if it exists
        if os.path.exists('.env'):
            logger.info("Loading environment variables from .env file")
            from dotenv import load_dotenv
            load_dotenv()
        
        # Get configuration from environment variables
        proxy_port = int(os.environ.get('PROXY_PORT', 8080))
        health_port = int(os.environ.get('HEALTH_PORT', 8081))
        
        # Log startup configuration
        logger.info("Starting AI Security Proxy with configuration:")
        logger.info(f"- Proxy Port: {proxy_port}")
        logger.info(f"- Health Port: {health_port}")
        logger.info(f"- Environment: {os.environ.get('FLASK_ENV', 'development')}")
        logger.info(f"- Rate Limiting: {os.environ.get('ENABLE_RATE_LIMITING', 'false')}")
        logger.info(f"- Block All Domains: {os.environ.get('BLOCK_ALL_DOMAINS', 'false')}")
        
        # Write PID file for process management
        with open('logs/proxy.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        # Run the proxy
        run_proxy(proxy_port, health_port)
    except Exception as e:
        logger.critical(f"Fatal error starting proxy: {str(e)}")
        logger.critical(traceback.format_exc())
        sys.exit(1)