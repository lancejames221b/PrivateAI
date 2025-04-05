import os
from logger import get_logger, log_exception

# Initialize logger
logger = get_logger("pii-transform", "logs/pii_transform.log")

try:
    # Check if transformers are explicitly disabled
    if os.environ.get('DISABLE_TRANSFORMERS', 'false').lower() == 'true':
        TRANSFORMERS_AVAILABLE = False
        logger.warning("transformers module disabled by environment variable.")
    else:
        from transformers import pipeline
        TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers module not available. Using regex-only transformations.")

import re
import json
import os
import uuid
import base64
from datetime import datetime
import hashlib
import sqlite3
# Simple encryption replacement
import base64
# Create a simple in-memory database replacement
# Simple encryption function using base64
def simple_encrypt(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    return base64.b64encode(text).decode('utf-8')

def simple_decrypt(text):
    if isinstance(text, str):
        text = text.encode('utf-8')
    return base64.b64decode(text).decode('utf-8')

class DatabaseEncryption:
    def __init__(self, db_path=None, encryption_key=None):
        self.mappings = {}
        self.encrypted = True
        self.encryption_enabled = False
        
    def encrypt_database(self):
        # No-op for in-memory implementation
        return True
        
    def decrypt_database(self):
        # No-op for in-memory implementation
        return True
        
    def store_mapping(self, original, replacement):
        self.mappings[original] = replacement
        return True
        
    def get_mapping(self, original):
        return self.mappings.get(original)
        
    def get_all_mappings(self):
        return self.mappings.items()

# Import the codename generator if available
try:
    from codename_generator import get_organization_codename, get_domain_codename
    CODENAME_GENERATOR_AVAILABLE = True
except ImportError:
    CODENAME_GENERATOR_AVAILABLE = False
    logger.warning("codename_generator module not available. Using basic placeholder generation.")
try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import RecognizerResult, OperatorConfig
    # Try to import our custom Transformers recognizer
    try:
        from transformers_recognizer import TransformersRecognizer, register_with_presidio
        TRANSFORMERS_RECOGNIZER_AVAILABLE = True
    except ImportError:
        TRANSFORMERS_RECOGNIZER_AVAILABLE = False
        logger.warning("Custom TransformersRecognizer not available. Using standard Presidio recognizers.")
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    TRANSFORMERS_RECOGNIZER_AVAILABLE = False
    logger.warning("presidio modules not available. Using regex-only transformations.")

# Suppress specific transformers warnings about unused weights
from transformers import logging as transformers_logging
transformers_logging.set_verbosity_error()

# Constants
USE_PRESIDIO = os.environ.get('USE_PRESIDIO', 'true').lower() == 'true' and PRESIDIO_AVAILABLE
BLOCK_ALL_DOMAINS = os.environ.get('BLOCK_ALL_DOMAINS', 'false').lower() == 'true'

# Initialize NER model if transformers is available
ner_model = None
if TRANSFORMERS_AVAILABLE:
    try:
        MODEL_NAME = os.environ.get('MODEL_NAME', 'dslim/bert-base-NER')
        # Try to load the model with a timeout to avoid hanging
        try:
            # Use a simpler pipeline configuration to avoid compatibility issues
            try:
                # First try with simple configuration
                ner_model = pipeline("ner", model=MODEL_NAME)
                logger.info(f"NER model loaded with basic configuration: {MODEL_NAME}")
            except Exception as config_error:
                if "remove_duplicate" in str(config_error):
                    # Handle the specific torch/transformers incompatibility
                    logger.warning("Detected torch/transformers version incompatibility. Using regex-only transformations.")
                    raise config_error
                else:
                    # Try without aggregation_strategy which can cause issues
                    ner_model = pipeline("ner", model=MODEL_NAME, aggregation_strategy=None)
                    logger.info(f"NER model loaded with fallback configuration: {MODEL_NAME}")
        except Exception as model_error:
            # If there's a proxy error or connection issue, log it and continue without the model
            if any(err in str(model_error) for err in ["ProxyError", "ConnectionError", "HTTPSConnectionPool", "remove_duplicate"]):
                logger.warning(f"Error loading NER model, continuing with regex-only: {str(model_error)}")
            else:
                # For other errors, re-raise
                raise model_error
    except Exception as e:
        logger.error(f"Error loading NER model: {str(e)}")
        logger.warning("Falling back to regex-only transformations")
        TRANSFORMERS_AVAILABLE = False

# Dictionary to store placeholder mappings
placeholder_mappings = {}

# Placeholder patterns for better regex matching
PLACEHOLDER_PATTERNS = [
    # Match domain codenames like "cyberguardian-123abc.example.com"
    r'([a-zA-Z0-9]+-[a-f0-9]+\.example\.com)',
    # Match organization codenames
    r'(Organization-[a-f0-9]+)',
    # Match CyberGuardian, TechShield, etc.
    r'(CyberGuardian|TechShield|SearchSphere|CloudPeak|FruitTech|CogniVerse|EthosAI|FalconDefend|VirtualPlatform|RelationCloud|DataKeeper|BlueCore|NetConnect|ShieldWare|GuardCore|FireWall|FlameShield|ThreatHunter|DarkGuard|WebShield|AccessGate|LogVault|TrendGuard|PathSec|FortBar|GateKeep|ShapeDefend|BitGuard|SoPhase)',
    # Match URL patterns
    r'(https://[a-zA-Z0-9-]+\.example\.com(?:/[^"\'\s<>()]*)?)',
    # Match SentinelOne specific patterns
    r'(agent-[a-f0-9]+-xxxx-xxxx-xxxx|group-[a-f0-9]+|S1-[A-Z]+-[a-f0-9]+)',
    # Match API keys
    r'(api-key-XXXX\.\.\.XXXX[a-f0-9]+|sk_[a-zA-Z0-9_]+-XXXX\.\.\.XXXX[a-f0-9]+)',
    # Match email placeholders
    r'(redacted\.email[a-f0-9]+@example\.com)',
    # Match IP address placeholders
    r'(192\.0\.2\.[0-9]+)',
    # Match IPv6 address placeholders
    r'(2001:db8:[a-f0-9:]+)',
    # Match other redacted content
    r'(REDACTED-[A-Z_]+-[a-f0-9]+)',
    # Match Presidio-style placeholders
    r'(<[A-Z_]+>)'
]

# Initialize Presidio if available
analyzer = None
anonymizer = None
if USE_PRESIDIO:
    try:
        # Create NLP engine based on spaCy - handle different Presidio API versions
        try:
            # For Presidio 2.2+
            provider = NlpEngineProvider(nlp_engine_name="spacy")
            nlp_engine = provider.create_engine()
        except TypeError:
            # For newer Presidio versions with changed API
            from presidio_analyzer.nlp_engine import SpacyNlpEngine
            nlp_engine = SpacyNlpEngine()
        
        # Create analyzer with standard recognizers and custom ones
        analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        anonymizer = AnonymizerEngine()
        
        # Register our custom transformer recognizer if available
        if TRANSFORMERS_RECOGNIZER_AVAILABLE:
            try:
                # Initialize with Piiranha or fallback to default model from .env
                model_name = os.environ.get('TRANSFORMER_MODEL_NAME', 'iiiorg/piiranha-v1-detect-personal-information')
                if model_name != 'iiiorg/piiranha-v1-detect-personal-information':
                    logger.info(f"Using custom transformer model: {model_name}")
                else:
                    logger.info("Using Piiranha v1 model for enhanced PII detection")
                
                # Create and register the recognizer
                transformers_recognizer = TransformersRecognizer(model_name=model_name)
                analyzer.registry.add_recognizer(transformers_recognizer)
                logger.info("TransformersRecognizer registered successfully with Presidio")
            except Exception as e:
                logger.error(f"Error registering TransformersRecognizer: {str(e)}")
                logger.warning("Continuing with standard Presidio recognizers only")
        
        logger.info("Presidio analyzer initialized successfully")
        logger.info("Presidio anonymizer initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Presidio: {str(e)}")
        USE_PRESIDIO = False

# Initialize database encryption with enhanced security
db_encryption = DatabaseEncryption()

# Database path - use a local path instead of Docker container path
DB_PATH = 'data/mapping_store.db'

# Global variables for connection and cursor
conn = None
cursor = None

def initialize_db_connection():
    """Initialize the database connection and cursor."""
    global conn, cursor
    if conn is None:
        try:
            # Ensure the database directory exists and has proper permissions
            data_dir = os.path.dirname(DB_PATH)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, mode=0o700)  # Secure permissions
            elif os.path.isdir(data_dir):
                # Try to secure existing directory
                os.chmod(data_dir, 0o700)

            # Connect to SQLite database for persistent storage
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row # Optional: Fetch rows as dict-like objects
            cursor = conn.cursor()
            logger.info(f"Database connection established to {DB_PATH}")

            # Create table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS mappings (
                original TEXT PRIMARY KEY,
                replacement TEXT NOT NULL,
                entity_type TEXT,
                created_at TEXT,
                last_used TEXT,
                is_encrypted INTEGER DEFAULT 0
            )
            ''')
            conn.commit()
            logger.info("'mappings' table ensured.")

            # Check if the is_encrypted column exists, add it if missing
            try:
                cursor.execute("SELECT is_encrypted FROM mappings LIMIT 1")
            except sqlite3.OperationalError:
                # Column doesn't exist, add it
                cursor.execute("ALTER TABLE mappings ADD COLUMN is_encrypted INTEGER DEFAULT 0")
                conn.commit()
                logger.info("Added is_encrypted column to mappings table")

        except Exception as e:
            log_exception(logger, e, "initialize_db_connection")
            conn = None # Ensure conn is None if initialization fails
            cursor = None

def get_db_connection_pii():
    """Returns the global connection and cursor for pii_transform module."""
    initialize_db_connection() # Ensure connection is initialized
    return conn, cursor

def get_replacement(word, entity_type=None):
    """Retrieve or generate a replacement for a sensitive word."""
    conn, cursor = get_db_connection_pii()
    if not conn or not cursor:
        logger.error("Database connection not available in get_replacement")
        # Fallback to basic placeholder generation if DB fails
        return generate_placeholder(entity_type or "UNKNOWN", word)

    # Validate input to prevent SQL injection
    if not word or not isinstance(word, str):
        logger.warning("Invalid input to get_replacement")
        return f"__INVALID_INPUT_{str(uuid.uuid4())[:8]}__"
        
    # Sanitize entity_type
    if entity_type and not re.match(r'^[A-Z_]+$', entity_type):
        logger.warning(f"Invalid entity type format: {entity_type}")
        entity_type = "UNKNOWN"
    
    try:
        # Check if the mapping exists
        cursor.execute("SELECT replacement, is_encrypted FROM mappings WHERE original = ? OR original = ?", 
                      (word, db_encryption.encrypt(word)))
        result = cursor.fetchone()
        
        if result:
            replacement, is_encrypted = result
            
            # Update last used time
            cursor.execute("UPDATE mappings SET last_used = ? WHERE original = ? OR original = ?", 
                          (datetime.now().isoformat(),
                           word, db_encryption.encrypt(word)))
            conn.commit()
            
            return replacement
        else:
            # Create a more informative replacement based on entity type
            prefix = "REDACTED"
            if entity_type:
                # Use a short prefix based on entity type
                if entity_type == "DOMAIN":
                    prefix = "DOMAIN"
                elif entity_type == "EMAIL":
                    prefix = "EMAIL"
                elif entity_type == "API_KEY":
                    prefix = "API_KEY"
                elif entity_type == "CREDENTIAL":
                    prefix = "CRED"
                elif entity_type.startswith("SENTINEL"):
                    prefix = "S1"
                elif entity_type == "IP_ADDRESS":
                    prefix = "IP"
                elif entity_type == "INTERNAL_IP_RANGE":
                    prefix = "INTERNAL_IP"
                elif entity_type == "PERSON":
                    prefix = "PERSON"
                elif entity_type == "LOCATION":
                    prefix = "LOC"
                elif entity_type == "PHONE_NUMBER":
                    prefix = "PHONE"
                elif entity_type == "NRP":
                    prefix = "NRP"  # National Registration Pattern
                elif entity_type == "CLOUD_RESOURCE":
                    prefix = "CLOUD"
                elif entity_type == "US_BANK_NUMBER":
                    prefix = "BANK"
                elif entity_type == "INTERNAL_PROJECT_NAME":
                    prefix = "PROJECT"
                elif entity_type == "SERVER_PATH":
                    prefix = "PATH"
                elif entity_type == "ENV_VARIABLE":
                    prefix = "ENV"
                else:
                    # Use first 3 chars of entity type
                    prefix = entity_type[:3] if len(entity_type) >= 3 else entity_type
            
            replacement = f"__{prefix}_{str(uuid.uuid4())[:8]}__"
            
            # If encryption is enabled, encrypt the original value
            encrypted_word = db_encryption.encrypt(word)
            is_encrypted = 1 if db_encryption.encryption_enabled else 0
            
            # Store the encrypted value if encryption is enabled, otherwise store plaintext
            storage_word = encrypted_word if db_encryption.encryption_enabled else word
            
            # Use parameterized query to prevent SQL injection
            cursor.execute(
                "INSERT INTO mappings VALUES (?, ?, ?, ?, ?, ?)",
                (storage_word, replacement, entity_type,
                 datetime.now().isoformat(),
                 datetime.now().isoformat(),
                 is_encrypted)
            )
            conn.commit()
            
            # Audit log for sensitive operations
            logger.info(f"Created new mapping for entity type: {entity_type}")
            return replacement
    except Exception as e:
        log_exception(logger, e, "get_replacement")
        # Return a fallback replacement in case of error
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Using fallback replacement with error ID: {error_id}")
        return f"__ERROR_{error_id}__"

def generate_placeholder(entity_type, value=None):
    """Generate a consistent placeholder for an entity"""
    placeholder_key = f"{entity_type}:{value}" if value else f"{entity_type}:{uuid.uuid4()}"
    
    if placeholder_key in placeholder_mappings:
        return placeholder_mappings[placeholder_key]
    
    # Use the dynamic codename generator if available
    if CODENAME_GENERATOR_AVAILABLE:
        if entity_type == "ORGANIZATION" or entity_type == "PERSON":
            if value:
                placeholder = get_organization_codename(value)
            else:
                placeholder = f"Organization-{uuid.uuid4().hex[:6]}"
        
        elif entity_type == "DOMAIN":
            if value:
                placeholder = get_domain_codename(value)
            else:
                placeholder = f"domain-{uuid.uuid4().hex[:6]}.example.com"
        
        elif entity_type == "URL":
            if value:
                try:
                    from urllib.parse import urlparse, urlunparse
                    parsed = urlparse(value)
                    
                    # Create domain replacement using generate_placeholder
                    domain_placeholder = generate_placeholder("DOMAIN", parsed.netloc)
                    
                    # Reconstruct the URL with the placeholder domain
                    # Keep scheme, path, params, query, fragment
                    placeholder = urlunparse((
                        parsed.scheme,
                        domain_placeholder, 
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment
                    ))
                except Exception as parse_error:
                    logger.warning(f"Failed to parse URL '{value}': {parse_error}. Falling back to generic placeholder.")
                    # Fallback to a simple hash if parsing fails
                    placeholder = f"https://redacted-url-{hashlib.md5(value.encode()).hexdigest()[:8]}.com"
            else:
                placeholder = f"https://redacted-url-{uuid.uuid4().hex[:8]}.com"
        
        # For other entity types, fall back to the static approach
        else:
            placeholder = _static_placeholder_generation(entity_type, value)
    else:
        # Fall back to static mappings if codename generator is not available
        placeholder = _static_placeholder_generation(entity_type, value)
    
    # Store the mapping in both directions for bidirectional transformation
    placeholder_mappings[placeholder_key] = placeholder
    reverse_key = f"REVERSE:{placeholder}"
    placeholder_mappings[reverse_key] = value if value else f"UNKNOWN_{entity_type}"
    
    return placeholder

def _static_placeholder_generation(entity_type, value=None):
    """Static placeholder generation as fallback"""
    # Organization mapping table for consistent codenames
    if entity_type == "ORGANIZATION":
        org_mappings = {
            "sentinelone": "CyberGuardian",
            "sentinel one": "CyberGuardian",
            "sentinel-one": "CyberGuardian",
            "s1": "CyberGuardian",
            "microsoft": "TechShield",
            "google": "SearchSphere",
            "amazon": "CloudPeak",
            "apple": "FruitTech",
            "openai": "CogniVerse",
            "anthropic": "EthosAI",
            "crowdstrike": "FalconDefend",
            "vmware": "VirtualPlatform",
            "salesforce": "RelationCloud",
            "oracle": "DataKeeper",
            "ibm": "BlueCore",
            "cisco": "NetConnect",
            "symantec": "ShieldWare",
            "mcafee": "GuardCore",
            "palo alto": "FireWall",
            "palo alto networks": "FireWall",
            "fireeye": "FlameShield",
            "mandiant": "ThreatHunter",
            "carbon black": "DarkGuard",
            "cloudflare": "WebShield",
            "okta": "AccessGate",
            "splunk": "LogVault",
            "trend micro": "TrendGuard",
            "juniper": "PathSec",
            "fortinet": "FortBar",
            "checkpoint": "GateKeep", 
            "cylance": "ShapeDefend",
            "bitdefender": "BitGuard",
            "sophos": "SoPhase"
        }
        
        # If we have a value, check if it matches any known organization
        if value:
            value_lower = value.lower().strip()
            
            # Check for exact matches
            if value_lower in org_mappings:
                placeholder = org_mappings[value_lower]
            else:
                # Check for partial matches (for organization names in text)
                for org_name, org_code in org_mappings.items():
                    if org_name in value_lower or value_lower in org_name:
                        placeholder = org_code
                        break
                else:
                    # No match found, generate a consistent hash-based name
                    hash_id = hashlib.md5(value.encode()).hexdigest()[:6]
                    placeholder = f"Organization-{hash_id}"
        else:
            # No value provided, use a generic placeholder
            placeholder = f"Organization-{uuid.uuid4().hex[:6]}"
    
    elif entity_type == "PERSON":
        if value:
            # Generate a realistic-looking fake name
            try:
                # Check if it's a full name (first and last)
                parts = value.split()
                if len(parts) >= 2:
                    # First name options
                    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery",
                                  "Quinn", "Skyler", "Dakota", "Reese", "Finley", "Rowan", "Jamie"]
                    
                    # Last name options
                    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis",
                                 "Garcia", "Rodriguez", "Wilson", "Martinez", "Anderson", "Taylor", "Thomas"]
                    
                    # Use hash of original name to select consistent fake name
                    first_hash = int(hashlib.md5(parts[0].encode()).hexdigest(), 16)
                    last_hash = int(hashlib.md5(parts[-1].encode()).hexdigest(), 16)
                    
                    fake_first = first_names[first_hash % len(first_names)]
                    fake_last = last_names[last_hash % len(last_names)]
                    
                    # Handle middle names/initials if present
                    if len(parts) > 2:
                        middle_parts = parts[1:-1]
                        fake_middle_parts = []
                        for part in middle_parts:
                            if len(part) == 1 or part.endswith('.'):  # Initial
                                middle_hash = int(hashlib.md5(part.encode()).hexdigest(), 16)
                                fake_middle = chr(65 + (middle_hash % 26)) + "."
                            else:  # Middle name
                                middle_hash = int(hashlib.md5(part.encode()).hexdigest(), 16)
                                fake_middle = first_names[middle_hash % len(first_names)]
                            fake_middle_parts.append(fake_middle)
                        
                        placeholder = f"{fake_first} {' '.join(fake_middle_parts)} {fake_last}"
                    else:
                        placeholder = f"{fake_first} {fake_last}"
                else:
                    # Single name, treat as first name
                    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery",
                                  "Quinn", "Skyler", "Dakota", "Reese", "Finley", "Rowan", "Jamie"]
                    name_hash = int(hashlib.md5(value.encode()).hexdigest(), 16)
                    placeholder = first_names[name_hash % len(first_names)]
            except Exception as e:
                logger.warning(f"Failed to generate fake name for '{value}': {e}. Using generic placeholder.")
                placeholder = f"Person-{hashlib.md5(value.encode()).hexdigest()[:6]}"
        else:
            # No value provided, use a generic placeholder
            placeholder = f"Person-{uuid.uuid4().hex[:6]}"
    
    # Domain mapping for better readability
    elif entity_type == "DOMAIN":
        # Create deterministic but anonymous domain replacements
        if value:
            # Check for known domains
            if "sentinelone.net" in value.lower() or "s1" in value.lower():
                domain_hash = hashlib.md5(value.encode()).hexdigest()[:6]
                placeholder = f"cyberguardian-{domain_hash}.example.com"
            else:
                domain_hash = hashlib.md5(value.encode()).hexdigest()[:6]
                placeholder = f"domain-{domain_hash}.example.com"
        else:
            placeholder = f"redacted-domain-{uuid.uuid4().hex[:8]}.com"
    
    # URL mapping to maintain context
    elif entity_type == "URL":
        if value:
            # Parse the URL to maintain some structure
            try:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(value)
                
                # Create domain replacement using generate_placeholder
                domain_placeholder = generate_placeholder("DOMAIN", parsed.netloc)
                
                # Reconstruct the URL with the placeholder domain
                # Keep scheme, path, params, query, fragment
                placeholder = urlunparse((
                    parsed.scheme,
                    domain_placeholder, 
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
            except Exception as parse_error:
                logger.warning(f"Failed to parse URL '{value}': {parse_error}. Falling back to generic placeholder.")
                # Fallback to a simple hash if parsing fails
                placeholder = f"https://redacted-url-{hashlib.md5(value.encode()).hexdigest()[:8]}.com"
        else:
            placeholder = f"https://redacted-url-{uuid.uuid4().hex[:8]}.com"
            
    elif entity_type == "API_KEY":
        if value and len(value) > 12:
            # Try to preserve the format but mask the content
            parts = value.split('_')
            if len(parts) > 1 and parts[0].lower() in ['sk', 'pk', 'api']:
                # Keep the prefix pattern but mask the rest
                prefix = '_'.join(parts[:2])
                placeholder = f"{prefix}_XXXX...XXXX{hashlib.md5(value.encode()).hexdigest()[:4]}"
            else:
                placeholder = f"api-key-XXXX...XXXX{hashlib.md5(value.encode()).hexdigest()[:4]}"
        else:
            placeholder = f"sk-REDACTED-API-KEY-{uuid.uuid4().hex[:8]}"
    
    elif entity_type == "EMAIL":
        if value:
            try:
                # Parse the email to maintain structure
                username, domain = value.split('@')
                
                # Generate consistent fake username based on original
                if '.' in username:
                    # Handle firstname.lastname pattern
                    parts = username.split('.')
                    fake_username = []
                    for part in parts:
                        # Create a deterministic fake name with same length
                        hash_val = hashlib.md5(part.encode()).hexdigest()[:6]
                        fake_part = ''.join([chr(97 + (ord(c) + int(hash_val[i % 6], 16)) % 26) for i, c in enumerate(part) if c.isalpha()])
                        if not fake_part:  # Fallback if no letters
                            fake_part = f"user{hash_val[:4]}"
                        fake_username.append(fake_part)
                    fake_username = '.'.join(fake_username)
                else:
                    # Handle single username
                    hash_val = hashlib.md5(username.encode()).hexdigest()[:6]
                    fake_username = ''.join([chr(97 + (ord(c) + int(hash_val[i % 6], 16)) % 26) for i, c in enumerate(username) if c.isalpha()])
                    if not fake_username:  # Fallback if no letters
                        fake_username = f"user{hash_val[:4]}"
                
                # Generate fake domain that looks realistic
                domain_parts = domain.split('.')
                tld = domain_parts[-1]  # Preserve the TLD (.com, .org, etc.)
                
                # Create a fake domain name
                domain_hash = hashlib.md5(domain.encode()).hexdigest()[:6]
                fake_domains = ["example", "sample", "private", "secure", "mail", "inbox"]
                fake_domain = fake_domains[int(domain_hash, 16) % len(fake_domains)]
                
                placeholder = f"{fake_username}@{fake_domain}.{tld}"
            except Exception as e:
                # Fallback if parsing fails
                logger.warning(f"Failed to parse email '{value}': {e}. Using generic placeholder.")
                placeholder = f"user{hashlib.md5(value.encode()).hexdigest()[:5]}@example.com"
        else:
            placeholder = f"user{uuid.uuid4().hex[:5]}@example.com"
    
    elif entity_type == "IP_ADDRESS":
        # Use a deterministic hash for consistent IP address transformation
        if value:
            # Create a hash of the original IP to ensure consistent transformation
            ip_hash = int(hashlib.md5(value.encode()).hexdigest()[:4], 16) % 254 + 1
            placeholder = f"192.0.2.{ip_hash}"
        else:
            # Fallback for when no value is provided
            placeholder = f"192.0.2.{uuid.uuid4().hex[:2]}"
    
    elif entity_type == "IPV6_ADDRESS":
        # Use a deterministic hash for consistent IPv6 address transformation
        if value:
            # Create a hash of the original IPv6 to ensure consistent transformation
            ip_hash = hashlib.md5(value.encode()).hexdigest()[:16]
            # Use RFC 3849 documentation prefix (2001:db8::/32)
            placeholder = f"2001:db8:{ip_hash[:4]}:{ip_hash[4:8]}:{ip_hash[8:12]}:{ip_hash[12:16]}"
        else:
            # Fallback for when no value is provided
            random_hex = uuid.uuid4().hex[:16]
            placeholder = f"2001:db8:{random_hex[:4]}:{random_hex[4:8]}:{random_hex[8:12]}:{random_hex[12:16]}"
    
    elif entity_type == "CREDIT_CARD":
        placeholder = "XXXX-XXXX-XXXX-XXXX"
    
    elif entity_type == "PASSWORD":
        placeholder = "********"
    
    # Handle SentinelOne specific entities
    elif entity_type.startswith("SENTINEL"):
        if "AGENT_ID" in entity_type and value:
            id_hash = hashlib.md5(value.encode()).hexdigest()[:8]
            placeholder = f"agent-{id_hash}-xxxx-xxxx-xxxx"
        elif "GROUP_ID" in entity_type or "SITE_ID" in entity_type:
            id_hash = hashlib.md5(value.encode()).hexdigest()[:6] if value else uuid.uuid4().hex[:6]
            placeholder = f"group-{id_hash}"
        else:
            type_abbr = ''.join(word[0] for word in entity_type.split('_') if word)
            placeholder = f"S1-{type_abbr}-{uuid.uuid4().hex[:6]}"
    
    else:
        placeholder = f"REDACTED-{entity_type}-{uuid.uuid4().hex[:8]}"
    
    return placeholder

def detect_and_transform(text):
    """
    Detect sensitive information in text and replace with placeholders.
    
    Args:
        text (str): The text to process
        
    Returns:
        tuple: (transformed_text, transformations_log)
    """
    if not text:
        return text, []
    
    transformations_log = []
    original_text = text
    
    try:
        # Try to parse as JSON if it looks like JSON
        if (text.strip().startswith('{') and text.strip().endswith('}')) or \
           (text.strip().startswith('[') and text.strip().endswith(']')):
            try:
                json_data = json.loads(text)
                transformed_json, log = transform_json(json_data)
                if log:  # Only convert back to string if changes were made
                    transformations_log.extend(log)
                    return json.dumps(transformed_json), transformations_log
            except json.JSONDecodeError:
                pass  # Not valid JSON, continue with regular text processing
        
        # Process with Presidio if available
        if USE_PRESIDIO:
            return transform_with_presidio(text)
            
        # Process using regex and NER if Presidio is not available
        transformed_text = original_text
        
        # Check for specific URLs first (more precise matching)
        if "https://console.sentinelone.net" in transformed_text:
            transformed_text = transformed_text.replace("https://console.sentinelone.net", "<URL-CONSOLE>")
            transformations_log.append({
                "entity_type": "URL",
                "start": transformed_text.find("<URL-CONSOLE>"),
                "end": transformed_text.find("<URL-CONSOLE>") + len("<URL-CONSOLE>"),
                "original_length": len("https://console.sentinelone.net")
            })
            
        if "https://usea1-purple.sentinelone.net/api/v2/" in transformed_text:
            transformed_text = transformed_text.replace("https://usea1-purple.sentinelone.net/api/v2/", "<URL-API>")
            transformations_log.append({
                "entity_type": "URL",
                "start": transformed_text.find("<URL-API>"),
                "end": transformed_text.find("<URL-API>") + len("<URL-API>"),
                "original_length": len("https://usea1-purple.sentinelone.net/api/v2/")
            })
        
        # Apply regex transformations
        for pattern_name, pattern in PATTERNS.items():
            matches = re.finditer(pattern, transformed_text, re.IGNORECASE)
            offset = 0
            
            for match in matches:
                entity_type = pattern_name
                value = match.group(0)
                placeholder = generate_placeholder(entity_type, value)
                
                start = match.start() + offset
                end = match.end() + offset
                
                before = transformed_text[:start]
                after = transformed_text[end:]
                transformed_text = before + placeholder + after
                
                # Adjust offset for future replacements
                offset += len(placeholder) - len(value)
                
                # Log the transformation
                transformations_log.append({
                    "entity_type": entity_type,
                    "start": start,
                    "end": start + len(placeholder),
                    "original_length": len(value)
                })
        
        # Apply NER-based transformations if available
        if TRANSFORMERS_AVAILABLE and ner_model:
            ner_results = ner_model(transformed_text)
            
            # Sort entities by start position in reverse to avoid offset issues
            ner_results.sort(key=lambda x: x['start'], reverse=True)
            
            for entity in ner_results:
                entity_type = entity['entity_group']
                value = entity['word']
                confidence = entity['score']
                
                # Skip low confidence predictions
                if confidence < 0.8:
                    continue
                
                start = entity['start']
                end = entity['end']
                
                placeholder = generate_placeholder(entity_type, value)
                
                before = transformed_text[:start]
                after = transformed_text[end:]
                transformed_text = before + placeholder + after
                
                # Log the transformation
                transformations_log.append({
                    "entity_type": entity_type,
                    "start": start,
                    "end": start + len(placeholder),
                    "original_length": end - start,
                    "confidence": confidence
                })
        
        return transformed_text, transformations_log
        
    except Exception as e:
        logger.error(f"Error in detect_and_transform: {str(e)}")
        return original_text, []

def transform_with_presidio(text):
    """Transform text using Presidio analyzer and anonymizer with custom logic"""
    try:
        # Get analysis results from Presidio
        results = analyzer.analyze(text=text, language="en")
        
        # Define custom anonymizer functions using our generate_placeholder logic
        operators = {}
        for entity_type in set(res.entity_type for res in results):
            if entity_type == "ORGANIZATION":
                operators[entity_type] = OperatorConfig(
                    "custom", 
                    {"lambda": lambda x: generate_placeholder(entity_type, x)}
                )
            elif entity_type == "DOMAIN":
                operators[entity_type] = OperatorConfig(
                    "custom", 
                    {"lambda": lambda x: generate_placeholder(entity_type, x)}
                )
            elif entity_type == "URL":
                operators[entity_type] = OperatorConfig(
                    "custom", 
                    {"lambda": lambda x: generate_placeholder(entity_type, x)}
                )
            else:
                # For other entities, use the default replacement or a custom one if needed
                operators[entity_type] = OperatorConfig(
                    "custom", 
                    {"lambda": lambda x: generate_placeholder(entity_type, x)}
                )
        
        # Anonymize using Presidio with our custom operators
        anonymized_response = anonymizer.anonymize(
            text=text, 
            analyzer_results=results,
            operators=operators
        )
        
        anonymized_text = anonymized_response.text
        
        # Create log of transformations
        transformations_log = [{
            "entity_type": result.entity_type,
            "start": result.start,
            "end": result.end,
            "confidence": result.score,
            "original": text[result.start:result.end],
            "placeholder": anonymized_text[item.start:item.end] if item else None # Get placeholder from response item
        } for result, item in zip(results, anonymized_response.items)]
        
        return anonymized_text, transformations_log
    except Exception as e:
        logger.error(f"Error in Presidio transformation: {str(e)}")
        return text, []

def transform_json(json_data):
    """
    Recursively process JSON data to detect and transform sensitive information.
    
    Args:
        json_data: The parsed JSON data (dict or list)
        
    Returns:
        tuple: (transformed_json, transformations_log)
    """
    transformations_log = []
    
    if isinstance(json_data, dict):
        result = {}
        for key, value in json_data.items():
            # Check for specific sensitive fields based on key name
            transformed_value = value
            special_handling = False
            
            # Special handling for known fields
            if key == "apiEndpoint" and isinstance(value, str):
                if "console.sentinelone.net" in value:
                    transformed_value = "<URL-CONSOLE>"
                    special_handling = True
                    transformations_log.append({
                        "entity_type": "URL",
                        "field": key,
                        "original_length": len(value)
                    })
                elif "usea1-purple.sentinelone.net/api/v2/" in value:
                    transformed_value = "<URL-API>"
                    special_handling = True
                    transformations_log.append({
                        "entity_type": "URL",
                        "field": key,
                        "original_length": len(value)
                    })
            
            # Standard processing if no special handling was done
            key_transformed = key
            if not special_handling:
                # Check if key contains sensitive info
                key_transformed, key_log = detect_and_transform(key)
                transformations_log.extend(key_log)
                
                # Process the value
                if isinstance(value, (dict, list)):
                    transformed_value, value_log = transform_json(value)
                    transformations_log.extend(value_log)
                elif isinstance(value, str):
                    transformed_value, value_log = detect_and_transform(value)
                    transformations_log.extend(value_log)
            
            result[key_transformed] = transformed_value
        return result, transformations_log
        
    elif isinstance(json_data, list):
        result = []
        for item in json_data:
            if isinstance(item, (dict, list)):
                transformed_item, item_log = transform_json(item)
                transformations_log.extend(item_log)
            elif isinstance(item, str):
                transformed_item, item_log = detect_and_transform(item)
                transformations_log.extend(item_log)
            else:
                transformed_item = item
                
            result.append(transformed_item)
        return result, transformations_log
        
    return json_data, transformations_log

def restore_original_values(text):
    """
    Restores original values from placeholders, prioritizing specific codenames.
    """
    if not text:
        return text
    
    processed_text = text
    logger.debug(f"Starting restoration for text: {processed_text[:100]}...")
    
    # Create a sorted list of placeholders found in the text based on start position
    found_placeholders = []
    for pattern in PLACEHOLDER_PATTERNS:
        try:
            for match in re.finditer(pattern, processed_text):
                found_placeholders.append({
                    "placeholder": match.group(1),
                    "start": match.start(),
                    "end": match.end()
                })
        except re.error as e:
            logger.warning(f"Regex error with pattern '{pattern}': {e}")
    
    # Sort placeholders by start position in reverse order to avoid offset issues
    found_placeholders.sort(key=lambda x: x['start'], reverse=True)
    
    # Iterate through found placeholders and attempt restoration
    restored_count = 0
    conn, cursor = get_db_connection_pii()
    if not conn or not cursor:
        logger.error("Database connection not available in restore_original_values")
        return text # Return original text if DB fails

    for item in found_placeholders:
        placeholder = item['placeholder']
        start = item['start']
        end = item['end']
        
        reverse_key = f"REVERSE:{placeholder}"
        
        # Check if we have a direct mapping for this placeholder
        if reverse_key in placeholder_mappings:
            original = placeholder_mappings[reverse_key]
            
            # Only replace if we have a valid original value
            if original and not original.startswith("UNKNOWN_"):
                logger.debug(f"Restoring '{placeholder}' with '{original}'")
                processed_text = processed_text[:start] + original + processed_text[end:]
                restored_count += 1
                continue  # Move to the next placeholder

        # Fallback: Handle generic Presidio placeholders if no direct match found
        if placeholder.startswith("<") and placeholder.endswith(">"):
            entity_type = placeholder[1:-1]  # Extract entity type like EMAIL_ADDRESS
            entity_key_prefix = f"{entity_type}:"
            
            # Find the *most specific* matching original value from mappings
            # This tries to find the value associated with this generic type
            possible_originals = []
            for key, value in placeholder_mappings.items():
                if key.startswith(entity_key_prefix):
                     # Check if the value corresponding to this key is a plausible original
                     reverse_lookup_key = f"REVERSE:{placeholder_mappings[key]}"
                     if reverse_lookup_key in placeholder_mappings and placeholder_mappings[reverse_lookup_key] == key.split(":", 1)[1]:
                          possible_originals.append(key.split(":", 1)[1])

            if possible_originals:
                # Simple strategy: use the first plausible original found
                # More sophisticated logic could be added here (e.g., context matching)
                original_value = possible_originals[0] 
                logger.debug(f"Restoring generic placeholder '{placeholder}' with inferred '{original_value}'")
                processed_text = processed_text[:start] + original_value + processed_text[end:]
                restored_count += 1
            else:
                 logger.warning(f"Could not find original value for generic placeholder: {placeholder}")
        else:
             logger.debug(f"No reverse mapping found for: {placeholder}")

    logger.info(f"Restored {restored_count} placeholders.")
    return processed_text

def restore_json_values(json_data):
    """
    Recursively restore original values in JSON data.
    
    Args:
        json_data: The JSON data (dict or list)
        
    Returns:
        The JSON data with original values restored
    """
    if isinstance(json_data, dict):
        result = {}
        for key, value in json_data.items():
            # Restore key if it's a placeholder
            restored_key = key
            
            # Process each potential placeholder in the key
            import re
            
            # Handle Presidio-style placeholders in keys
            for entity_type in ["ORGANIZATION", "PERSON", "LOCATION", "DATE_TIME", "NRP", "PHONE_NUMBER", 
                              "EMAIL_ADDRESS", "URL", "US_DRIVER_LICENSE", "US_PASSPORT", 
                              "US_SSN", "UK_NHS", "IP_ADDRESS", "CREDIT_CARD"]:
                placeholder = f"<{entity_type}>"
                if placeholder in restored_key:
                    # Try to find the original value in our mappings
                    entity_key = f"{entity_type}:"
                    possible_keys = [k for k in placeholder_mappings.keys() if k.startswith(entity_key)]
                    if possible_keys:
                        # Use the first one we find as a reasonable guess
                        original_key = possible_keys[0]
                        if ":" in original_key:
                            original_value = original_key.split(":", 1)[1]
                            if original_value:
                                restored_key = restored_key.replace(placeholder, original_value)
            
            # Process standard placeholders
            for pattern in PLACEHOLDER_PATTERNS:
                matches = re.finditer(pattern, restored_key)
                for match in matches:
                    placeholder = match.group(1)
                    reverse_key = f"REVERSE:{placeholder}"
                    if reverse_key in placeholder_mappings:
                        original = placeholder_mappings[reverse_key]
                        if original and not original.startswith("UNKNOWN_"):
                            restored_key = restored_key.replace(placeholder, original)
            
            # Special case for partially transformed keys
            if "<ORGANIZATION>ne" in restored_key:
                restored_key = restored_key.replace("<ORGANIZATION>ne", "SentinelOne")
            elif "SentinelOnene" in restored_key:
                restored_key = restored_key.replace("SentinelOnene", "SentinelOne")
            
            # Process the value
            if isinstance(value, (dict, list)):
                restored_value = restore_json_values(value)
            elif isinstance(value, str):
                restored_value = restore_original_values(value)  # Reuse the text restoration function
            else:
                restored_value = value
                
            result[restored_key] = restored_value
        return result
        
    elif isinstance(json_data, list):
        result = []
        for item in json_data:
            if isinstance(item, (dict, list)):
                restored_item = restore_json_values(item)
            elif isinstance(item, str):
                restored_item = restore_original_values(item)  # Reuse the text restoration function
            else:
                restored_item = item
                
            result.append(restored_item)
        return result
        
    return json_data
# PIITransformer class to wrap the functionality
class PIITransformer:
    """
    PIITransformer class for transforming PII in text and JSON data.
    This class wraps the existing functionality in pii_transform.py.
    """
    
    def __init__(self):
        """Initialize the PIITransformer"""
        # Nothing to initialize as all state is module-level
        pass
    
    def transform_text(self, text):
        """Transform text to protect PII"""
        return detect_and_transform(text)
    
    def transform_json(self, json_data):
        """Transform JSON data to protect PII"""
        return transform_json(json_data)
    
    def restore_original_values(self, text):
        """Restore original values in transformed text"""
        return restore_original_values(text)
    
    def restore_json_values(self, json_data):
        """Restore original values in transformed JSON data"""
        return restore_json_values(json_data)

# Basic pattern definitions - these will be extended
PATTERNS = {
    # Add IPv6 address transformation pattern
    "API_KEY": r'(sk|pk)_(test|live|proj|or-v1|ant-api\d+)_[0-9a-zA-Z_-]{24,}|api[_-]?key[=: "\']+[0-9a-zA-Z\-_]{20,}',
    "OPENAI_API_KEY": r'sk[-_](?:proj|test|live)[-_][0-9a-zA-Z-_]{48,}',
    "OPENROUTER_API_KEY": r'sk[-_]or[-_]v1[-_][0-9a-zA-Z-_]{48,}',
    "ANTHROPIC_API_KEY": r'sk[-_]ant[-_]api\d+[-_][0-9a-zA-Z_-]{48,}',
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "IP_ADDRESS": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    "CREDIT_CARD": r'\b(?:\d{4}[- ]?){3}\d{4}\b',
    "PASSWORD": r'password[=: "\']+[^ ]{8,}',
    "DOMAIN": r'\b(?:(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9])\b',
    "PHONE_NUMBER": r'\+?\d{1,3}[- ]?\(?\d{3}\)?[- ]?\d{3,4}[- ]?\d{4}',
}

# Initialize domain blocklist
domain_blocklist = []

def load_domain_blocklist():
    """Load domain blocklist from file"""
    global domain_blocklist
    blocklist_file = "data/domain_blocklist.txt"
    
    try:
        if os.path.exists(blocklist_file):
            with open(blocklist_file, 'r') as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                domain_blocklist = domains
                logger.info(f"Loaded {len(domains)} domains from blocklist")
        else:
            logger.warning(f"Domain blocklist file not found: {blocklist_file}")
    except Exception as e:
        logger.error(f"Error loading domain blocklist: {str(e)}")

# Load domain blocklist at module initialization
load_domain_blocklist()

# Function to migrate existing database to encrypted format
def migrate_to_encrypted_database():
    """
    Migrate existing plaintext mappings to encrypted format
    """
    if not db_encryption.encryption_enabled:
        print("Encryption is disabled. Skipping migration.")
        return
    
    try:
        # Get all unencrypted mappings
        cursor.execute("SELECT original, replacement, entity_type, created_at, last_used FROM mappings WHERE is_encrypted = 0")
        unencrypted_mappings = cursor.fetchall()
        
        if not unencrypted_mappings:
            print("No unencrypted mappings found. Database is already encrypted or empty.")
            return
        
        print(f"Migrating {len(unencrypted_mappings)} mappings to encrypted format...")
        
        # Encrypt each mapping
        for original, replacement, entity_type, created_at, last_used in unencrypted_mappings:
            encrypted_original = db_encryption.encrypt(original)
            
            # Update the record
            cursor.execute("""
                UPDATE mappings 
                SET original = ?, is_encrypted = 1 
                WHERE original = ? AND is_encrypted = 0
            """, (encrypted_original, original))
        
        conn.commit()
        print("Database migration completed successfully.")
    except Exception as e:
        print(f"Error during database migration: {str(e)}")
        conn.rollback()

# Run migration if encryption is enabled
try:
    if db_encryption.encryption_enabled:
        migrate_to_encrypted_database()
except Exception as e:
    logger.error(f"Error during database migration: {str(e)}")
    logger.info("Continuing without migration - this is normal for first run") 