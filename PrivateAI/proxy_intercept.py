"""
Private AI 🕵️ - mitmproxy Interceptor

This detective module intercepts and transforms AI API requests and responses,
investigating for sensitive information and protecting privacy across all major AI systems.

Author: Lance James @ Unit 221B
"""

from mitmproxy import http

# Force disable transformers to avoid numpy incompatibility
import os
os.environ['DISABLE_TRANSFORMERS'] = 'true'

try:
    from pii_transform import detect_and_transform, restore_original_values
    PII_TRANSFORM_AVAILABLE = True
except ImportError:
    PII_TRANSFORM_AVAILABLE = False
    import logging
    logging.warning("pii_transform module not available. Proxy will only forward requests without transformation.")
    
    # Define stub functions for detect_and_transform and restore_original_values
    def detect_and_transform(text):
        return text, []
    
    def restore_original_values(text):
        return text

from utils import transform_url_parameters, logger, PATTERNS, AI_INFERENCE_PATTERNS, SENTINEL_PATTERNS
from utils import detect_and_adapt_ai_format, adapt_ai_response
import urllib.parse
import re
import os
import sys
import argparse
import logging
import json

# Configure logging based on environment variables or defaults
def setup_logging():
    """
    Configure the logging system based on environment variables.
    """
    log_level_str = os.environ.get('LOG_LEVEL', 'info').upper()
    log_levels = {
        'DEBUG': logging.DEBUG, 
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = log_levels.get(log_level_str, logging.INFO)
    
    log_file = os.environ.get('LOG_FILE', 'proxy.log')
    
    # Configure logging handlers
    handlers = [
        logging.StreamHandler(sys.stdout)
    ]
    
    # Add file handler if a log file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        handlers.append(logging.FileHandler(log_file))
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Update logger with new settings
    logger.setLevel(log_level)
    logger.info(f"Logging initialized at level: {log_level_str}")
    logger.info(f"Log file: {log_file if log_file else 'None'}")

# Call setup_logging at module load time
setup_logging()

# Print startup banner
logger.info("=" * 50)
logger.info("AI Security Proxy - mitmproxy interceptor starting")
logger.info(f"Block all domains: {os.environ.get('BLOCK_ALL_DOMAINS', 'false')}")
logger.info(f"PII transform available: {PII_TRANSFORM_AVAILABLE}")
logger.info("=" * 50)

# Combined regex patterns
REGEX_PATTERNS = {**PATTERNS, **AI_INFERENCE_PATTERNS, **SENTINEL_PATTERNS}

# List of AI API domains to focus on - now loaded from JSON config
AI_API_DOMAINS = []

# Load custom domain list from environment if available
def load_custom_domains():
    """Load any custom domains from environment variables"""
    custom_domains_str = os.environ.get('CUSTOM_AI_DOMAINS', '')
    if custom_domains_str:
        custom_domains = [d.strip() for d in custom_domains_str.split(',')]
        logger.info(f"Loaded {len(custom_domains)} custom domains from environment")
        return custom_domains
    return []

# Add any custom domains from environment
AI_API_DOMAINS.extend(load_custom_domains())

# Add domains from the blocklist
from utils import get_domain_blocklist
domain_blocklist = get_domain_blocklist()
logger.info(f"Loaded {len(domain_blocklist)} domains from blocklist")

# Global variable to store request format information for response adaptation
request_formats = {}

def should_process_request(flow: http.HTTPFlow) -> bool:
    """Determine if we should process this request based on domain and content"""
    try:
        # Extract domain from host header or URL
        host = flow.request.host
        logger.info(f"Checking host: {host}")
        
        # Always process any request to AI API domains
        for ai_domain in AI_API_DOMAINS:
            # Handle wildcard domains
            if ai_domain.startswith('*') and host.endswith(ai_domain[2:]):
                logger.info(f"Processing wildcard AI API domain: {host}")
                return True
            elif ai_domain in host:
                logger.info(f"Processing AI API request: {host}")
                return True
                
        # Process if URL contains AI-related keywords
        ai_keywords = [
            # OpenAI models
            "openai", "gpt", "chatgpt", "davinci", "o1", "o3", "sora", "dall-e",
            # Anthropic models
            "claude", "anthropic", "sonnet", "opus", "haiku",
            # Google models
            "gemini", "palm", "vertex", "bard",
            # Other major models
            "llm", "llama", "mistral", "falcon", "mixtral",
            # IDE AI integration keywords
            "copilot", "cursor", "codeium", "tabnine", "kite", "cody", "github-copilot", 
            "sourcegraph", "replit", "codewhisperer", "adrenaline", "jetbrains",
            # Common IDE API endpoints
            "completions", "chat/completions", "suggestions", "inline-suggestions", 
            "code-completion", "agent.js", "extension.js", "models",
            # Self-descriptive URL parameters
            "model=", "prompt=", "message=", "completion=", "embedding="
        ]
        
        url_lower = flow.request.url.lower()
        if any(kw in url_lower for kw in ai_keywords):
            matching_keywords = [kw for kw in ai_keywords if kw in url_lower]
            logger.info(f"Processing AI-related request: {flow.request.url} (matched: {', '.join(matching_keywords)})")
            return True
            
        # Process any requests with JSON content
        if flow.request and flow.request.headers.get("content-type", "").startswith("application/json"):
            logger.info(f"Processing JSON request: {flow.request.url}")
            return True
        
        # Check for IDE-specific protocol headers
        ide_protocol_headers = [
            # GitHub Copilot headers
            "x-github-token", "x-github-client-id", "x-github-client-name", "x-copilot-session", "github-copilot",
            # Cursor headers
            "x-cursor-token", "x-cursor-client",
            # VS Code headers
            "x-vscode", "x-ide-version", "x-ide-client", "x-plugin-type",
            # Other IDE headers
            "x-sourcegraph-client", "x-tabnine-client", "x-codeium-token"
        ]
        
        for header in ide_protocol_headers:
            if header in flow.request.headers:
                logger.info(f"Processing request with IDE protocol header: {header}")
                return True
                
        # Check for JSONRPC protocol (used by GitHub Copilot and others)
        if flow.request.content and flow.request.headers.get("content-type", "").startswith("application/json"):
            try:
                content = flow.request.content.decode('utf-8')
                if '"jsonrpc":' in content or '"method":' in content:
                    logger.info(f"Processing JSON-RPC request: {flow.request.url}")
                    return True
            except Exception as e:
                logger.error(f"Error parsing JSON content: {str(e)}")
            
        logger.info(f"Skipping non-AI request: {flow.request.url}")
        return False
    except Exception as e:
        logger.error(f"Error in should_process_request: {str(e)}")
        return False

def request(flow: http.HTTPFlow) -> None:
    """
    Intercept and transform requests. This will:
    1. Detect and transform PII in the request content
    2. Detect and transform PII in URL parameters
    3. Adapt different AI API formats to a standardized format
    
    Author: Lance James @ Unit 221B
    """
    try:
        logger.info(f"Received request: {flow.request.url}")
        
        # Only process if it's to an AI API or if we should process it
        if not should_process_request(flow):
            return
        
        # Log request details
        logger.info(f"Request method: {flow.request.method}")
        
        # Process JSON content if available
        if flow.request and flow.request.headers.get("content-type", "").startswith("application/json"):
            try:
                # Get the original JSON data
                data = flow.request.content.decode("utf-8")
                logger.info(f"Request data (first 100 chars): {data[:100]}...")
                
                # Parse JSON
                try:
                    json_data = json.loads(data)
                    
                    # Detect and adapt the AI format
                    adapted_data, format_detected, adaptation_needed = detect_and_adapt_ai_format(
                        json_data, 
                        {k: v for k, v in flow.request.headers.items()}
                    )
                    
                    # Save the format for response handling
                    request_id = flow.request.url + str(id(flow))
                    request_formats[request_id] = format_detected
                    
                    if adaptation_needed:
                        logger.info(f"Adapted request format from {format_detected} to OpenAI format")
                        # Use the adapted data
                        data = json.dumps(adapted_data)
                
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON data for format adaptation")
                
                # Transform sensitive data in the request body
                transformed, log = detect_and_transform(data)
                flow.request.text = transformed
                
                if log:
                    logger.info(f"Processed JSON request: {flow.request.url} - Replaced {len(log)} items")
                else:
                    logger.info(f"No sensitive data found in request JSON")
            except Exception as e:
                logger.error(f"Error processing JSON request: {str(e)}")
        
        # Process URL parameters
        try:
            url = flow.request.url
            transformed_url = transform_url_parameters(url)
            if transformed_url != url:
                logger.info(f"Transformed URL parameters: {url} -> {transformed_url}")
                flow.request.url = transformed_url
        except Exception as e:
            logger.error(f"Error processing URL parameters: {str(e)}")
                
        # Log request details
        logger.debug(f"Final request URL: {flow.request.url}")
        logger.debug(f"Final request method: {flow.request.method}")

        # Check if there's a matching server configuration
        server_config = get_server_config(flow.request.url)
        if server_config:
            # Apply authentication and custom headers from the configuration
            apply_server_auth(flow, server_config)
            
            # Set the provider type in flow.metadata for later use in response handling
            flow.metadata = flow.metadata or {}
            flow.metadata['ai_provider'] = server_config.get('provider', 'openai')
            logger.info(f"Set AI provider type: {server_config.get('provider', 'openai')}")
    except Exception as e:
        logger.error(f"Error in request handler: {str(e)}")

def response(flow: http.HTTPFlow) -> None:
    """
    Intercept and transform responses. This will:
    1. Detect and transform PII in the response content
    2. Restore original values where placeholders were used in the request
    3. Adapt the response format to match the original request format
    
    Author: Lance James @ Unit 221B
    """
    try:
        logger.info(f"Received response: {flow.request.url}")
        
        # Only process if it's from an AI API or if we should process it
        if not should_process_request(flow):
            return
            
        # Process content based on type
        if flow.response and flow.response.headers.get("content-type", "").startswith("application/json"):
            try:
                data = flow.response.content.decode("utf-8")
                logger.info(f"Response data (first 100 chars): {data[:100]}...")
                
                # First restore any placeholders from the request
                restored_data = restore_original_values(data)
                
                # Then detect and transform sensitive information in the response
                transformed, log = detect_and_transform(restored_data)
                
                # Adapt the response format if needed
                try:
                    # Get the original request format
                    request_id = flow.request.url + str(id(flow))
                    original_format = request_formats.pop(request_id, 'openai')
                    
                    # Parse JSON
                    json_data = json.loads(transformed)
                    
                    # Adapt the response format if needed
                    if original_format != 'openai':
                        adapted_response = adapt_ai_response(json_data, original_format)
                        logger.info(f"Adapted response from OpenAI format to {original_format} format")
                        transformed = json.dumps(adapted_response)
                except Exception as format_error:
                    logger.error(f"Error adapting response format: {str(format_error)}")
                
                # Update response with transformed content
                flow.response.text = transformed
                
                if log:
                    logger.info(f"Processed JSON response: {flow.request.url} - Replaced {len(log)} items")
                else:
                    logger.info(f"No sensitive data found in response")
            except Exception as e:
                logger.error(f"Error processing JSON response: {str(e)}")
        else:
            logger.info(f"Skipping non-JSON response: {flow.response.headers.get('content-type', 'unknown')}")
    except Exception as e:
        logger.error(f"Error in response handler: {str(e)}")

# Add a command-line entrypoint for testing the script directly
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Security Proxy - mitmproxy interceptor")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-l", "--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"],
                      help="Set the logging level")
    parser.add_argument("-f", "--log-file", default="proxy.log", help="Log file location")
    parser.add_argument("-b", "--block-all-domains", action="store_true", help="Block all domains")
    parser.add_argument("--supports-all-ai", action="store_true", help="Enable support for all AI APIs", default=True)
    
    args = parser.parse_args()
    
    # Set environment variables based on args
    if args.verbose:
        os.environ["LOG_LEVEL"] = "debug"
    else:
        os.environ["LOG_LEVEL"] = args.log_level
        
    os.environ["LOG_FILE"] = args.log_file
    os.environ["BLOCK_ALL_DOMAINS"] = "true" if args.block_all_domains else "false"
    os.environ["SUPPORTS_ALL_AI"] = "true" if args.supports_all_ai else "false"
    
    # Re-initialize logging with new settings
    setup_logging()
    
    # Print information about how to run with mitmproxy
    logger.info("This script is designed to be used with mitmproxy.")
    logger.info("Run with: mitmdump -s proxy_intercept.py [mitmproxy options]")
    logger.info("Script settings:")
    logger.info(f"  Log level: {os.environ.get('LOG_LEVEL', 'info')}")
    logger.info(f"  Log file: {os.environ.get('LOG_FILE', 'proxy.log')}")
    logger.info(f"  Block all domains: {os.environ.get('BLOCK_ALL_DOMAINS', 'false')}")
    logger.info(f"  Support all AI formats: {os.environ.get('SUPPORTS_ALL_AI', 'true')}")
    logger.info(f"  PII transform available: {PII_TRANSFORM_AVAILABLE}") 

# Modified load_ai_servers function to also handle domain definitions
def load_ai_servers():
    """Load AI server configurations and domain definitions from JSON file"""
    servers_file = os.path.join('data', 'ai_servers.json')
    domains_file = os.path.join('data', 'ai_domains.json')
    
    domains_loaded = False
    servers_loaded = False
    
    # First load domains if available
    if os.path.exists(domains_file):
        try:
            with open(domains_file, 'r') as f:
                domains_data = json.load(f)
                global AI_API_DOMAINS
                AI_API_DOMAINS = domains_data.get('domains', [])
                logger.info(f"Loaded {len(AI_API_DOMAINS)} AI API domains from configuration")
                domains_loaded = True
        except Exception as e:
            logger.error(f"Error loading AI domains: {str(e)}")
    
    # Then load server configurations
    if not os.path.exists(servers_file):
        logger.warning(f"AI servers configuration file not found at {servers_file}")
        # Create default domain configuration if needed
        if not domains_loaded:
            create_default_domain_config()
        return []
    
    try:
        with open(servers_file, 'r') as f:
            servers = json.load(f)
            # Only return active servers
            active_servers = [s for s in servers if s.get('is_active', True)]
            logger.info(f"Loaded {len(active_servers)} active AI server configurations")
            servers_loaded = True
            
            # Extract domains from server configurations
            for server in active_servers:
                base_url = server.get('base_url', '')
                if base_url:
                    try:
                        # Extract domain from URL
                        from urllib.parse import urlparse
                        domain = urlparse(base_url).netloc
                        if domain and domain not in AI_API_DOMAINS:
                            AI_API_DOMAINS.append(domain)
                            logger.info(f"Added domain from AI server config: {domain}")
                    except Exception as e:
                        logger.error(f"Error parsing domain from {base_url}: {str(e)}")
            
            return active_servers
    except Exception as e:
        logger.error(f"Error loading AI servers: {str(e)}")
        return []
    
    # If no configurations were loaded, create defaults
    if not domains_loaded and not servers_loaded:
        create_default_domain_config()
        
    return []

def create_default_domain_config():
    """Create a default domain configuration file with common AI API domains"""
    domains_file = os.path.join('data', 'ai_domains.json')
    
    # Define default domains - moved from the hardcoded list
    default_domains = {
        "domains": [
            # OpenAI API endpoints
            "api.openai.com",              # Standard OpenAI API
            "oai.azure.com",               # Azure OpenAI
            "api.openai.azure.com",        # Alternative Azure OpenAI endpoint
            "api.o.openai.com",            # Specialized o1/o3 models endpoints
            
            # Anthropic API endpoints
            "api.anthropic.com",           # Standard Anthropic API
            "api.claude.ai",               # Claude direct API
            "api-staging.anthropic.com",   # Anthropic staging environment
            "api-experimental.anthropic.com", # Experimental models endpoint
            
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
            "httpbin.org"                  # Testing endpoint
        ],
        "categories": {
            "openai": [
                "api.openai.com",
                "oai.azure.com",
                "api.openai.azure.com",
                "api.o.openai.com"
            ],
            "anthropic": [
                "api.anthropic.com",
                "api.claude.ai",
                "api-staging.anthropic.com",
                "api-experimental.anthropic.com"
            ],
            "google": [
                "api.gemini.google.com",
                "generativelanguage.googleapis.com",
                "vertex.ai",
                "us-central1-aiplatform.googleapis.com",
                "europe-west4-aiplatform.googleapis.com",
                "ai.googleapis.com"
            ],
            "ide": [
                "vscode-copilot.githubusercontent.com",
                "api.githubcopilot.com",
                "api.cursor.sh",
                "cursor.sh",
                "vscode.dev",
                "insiders.vscode.dev",
                "online.visualstudio.com",
                "copilot.github.com",
                "copilot-proxy.githubusercontent.com",
                "plugins.jetbrains.com",
                "api-inference.nvidia.com",
                "model-api.tabnine.com",
                "api.kite.com",
                "api.sourcegraph.com",
                "completion.kite.com",
                "api.replit.com",
                "api.codeium.com",
                "api.aws.codewhisperer.amazon.com",
                "chat.aws.codewhisperer.amazon.com",
                "api.adrenaline.dev",
                "api.tabnine.com"
            ],
            "openrouter": [
                "openrouter.ai",
                "api.openrouter.ai",
                "openrouter.dev",
                "*.openrouter.ai",
                "openrouter.helicone.ai"
            ],
            "open": [
                "huggingface.co",
                "api.huggingface.co",
                "huggingface.inference.endpoints",
                "api-inference.huggingface.io"
            ],
            "emerging": [
                "api.mistral.ai",
                "api.together.xyz",
                "api.perplexity.ai",
                "api.deepseek.com",
                "api.deepseek.ai",
                "api.groq.com",
                "api.groq.dev",
                "api.minimax.chat",
                "api-inference.minimax.ai",
                "api.aleph-alpha.com",
                "api.fireworks.ai",
                "api.anyscale.com",
                "api.qwen.ai",
                "api.stability.ai",
                "api.meta.ai",
                "llama-api.meta.com"
            ],
            "testing": [
                "httpbin.org"
            ]
        }
    }
    
    try:
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(domains_file), exist_ok=True)
        
        # Write the default domains to the file
        with open(domains_file, 'w') as f:
            json.dump(default_domains, f, indent=2)
            
        logger.info(f"Created default domain configuration with {len(default_domains['domains'])} domains")
        
        # Update the global variable
        global AI_API_DOMAINS
        AI_API_DOMAINS = default_domains['domains']
        
    except Exception as e:
        logger.error(f"Error creating default domain configuration: {str(e)}")
    
def save_ai_domains(domains_data):
    """Save AI domain configurations to JSON file"""
    domains_file = os.path.join('data', 'ai_domains.json')
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(domains_file), exist_ok=True)
    
    try:
        with open(domains_file, 'w') as f:
            json.dump(domains_data, f, indent=2)
        logger.info(f"Saved {len(domains_data.get('domains', []))} AI domains to configuration")
        return True
    except Exception as e:
        logger.error(f"Error saving AI domains: {str(e)}")
        return False

# Load domains from AI server configurations 
# This section is now handled by the updated load_ai_servers function

# Add to request function to handle configured authentication
def apply_server_auth(flow, server_config):
    """Apply authentication from server configuration to the request"""
    auth_type = server_config.get('auth_type')
    auth_key = server_config.get('auth_key', '')
    auth_value = server_config.get('auth_value', '')
    
    if not auth_type or auth_type == 'none':
        return
        
    if auth_type == 'bearer' and auth_key and auth_value:
        # Add Bearer token
        flow.request.headers[auth_key] = f"Bearer {auth_value}"
        logger.info(f"Added Bearer token authentication to request")
        
    elif auth_type == 'api_key' and auth_key and auth_value:
        # Add API key header
        flow.request.headers[auth_key] = auth_value
        logger.info(f"Added API key authentication to request")
        
    elif auth_type == 'basic' and auth_key and auth_value:
        # Add Basic authentication
        import base64
        auth_string = f"{auth_key}:{auth_value}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        flow.request.headers['Authorization'] = f"Basic {encoded}"
        logger.info(f"Added Basic authentication to request")
        
    # Add any custom headers
    try:
        custom_headers = server_config.get('custom_headers', '')
        if custom_headers:
            headers = json.loads(custom_headers)
            for key, value in headers.items():
                flow.request.headers[key] = value
                logger.info(f"Added custom header: {key}")
    except Exception as e:
        logger.error(f"Error adding custom headers: {str(e)}")

# Add this to the request function after checking should_process_request
# Find matching server configuration for this request
def get_server_config(url):
    """Find a matching server configuration for the given URL"""
    if not url:
        return None
        
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        # Load AI server configurations
        servers = load_ai_servers()
        
        for server in servers:
            if not server.get('is_active', True):
                continue
                
            base_url = server.get('base_url', '')
            if not base_url:
                continue
                
            server_domain = urlparse(base_url).netloc
            
            if domain == server_domain:
                logger.info(f"Found matching server configuration for {domain}: {server.get('name')}")
                return server
                
    except Exception as e:
        logger.error(f"Error finding server configuration: {str(e)}")
        
    return None 