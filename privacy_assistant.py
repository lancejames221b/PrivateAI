#!/usr/bin/env python3
"""
Privacy Assistant for AI Model Interactions

This module provides functions to detect, classify, and transform sensitive information
in token streams to and from AI models. It focuses on protecting PII and other sensitive
information while maintaining utility of the interactions.
"""

import re
import json
import logging
import os
import uuid
import hashlib
from typing import Dict, List, Tuple, Any, Optional, Set
import sqlite3
from datetime import datetime
import base64

# Import encryption module
try:
    from cryptography.fernet import Fernet, InvalidToken
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logging.warning("cryptography module not available. Database encryption will be disabled.")

# Import NLP components if available
try:
    import spacy
    from transformers import pipeline
    NLP_ADVANCED = True
except ImportError:
    NLP_ADVANCED = False
    logging.warning("Advanced NLP modules not available. Using regex-only detection.")

# Import Presidio components if available
try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer
    from presidio_analyzer.nlp_engine import NlpEngineProvider
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import RecognizerResult, OperatorConfig
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    logging.warning("presidio modules not available. Using regex-only transformations.")

# Configure logging
logger = logging.getLogger("privacy-assistant")

# Initialize database
os.makedirs('data', exist_ok=True)

# ===============================================================
# Constants and Configuration
# ===============================================================

# Privacy sensitivity levels for classification
SENSITIVITY_HIGH = "HIGH"       # Direct personal or security information
SENSITIVITY_MEDIUM = "MEDIUM"   # Indirect or inferrable sensitive details
SENSITIVITY_LOW = "LOW"         # Potentially sensitive context

# Regular expression patterns for detecting sensitive information
PATTERNS = {
    "API_KEY": (r'(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}|api[_-]?key[=: "\']+[0-9a-zA-Z\-_]{20,}', SENSITIVITY_HIGH),
    "EMAIL": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', SENSITIVITY_HIGH),
    "IP_ADDRESS": (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', SENSITIVITY_MEDIUM),
    "IPV6_ADDRESS": (r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b', SENSITIVITY_MEDIUM),
    "CREDIT_CARD": (r'\b(?:\d{4}[- ]?){3}\d{4}\b', SENSITIVITY_HIGH),
    "SSN": (r'\b\d{3}-\d{2}-\d{4}\b', SENSITIVITY_HIGH),
    "AWS_KEY": (r'AKIA[0-9A-Z]{16}', SENSITIVITY_HIGH),
    "PASSWORD": (r'password[=: "\']+[^ ]{8,}', SENSITIVITY_HIGH),
    "LICENSE_KEY": (r'license[_-]?key[=: "\']+[0-9a-zA-Z\-]{5,}', SENSITIVITY_HIGH),
    "GITHUB_TOKEN": (r'gh[pousr]_[0-9a-zA-Z]{36}', SENSITIVITY_HIGH),
    "PRIVATE_KEY": (r'-----BEGIN( RSA)? PRIVATE KEY-----', SENSITIVITY_HIGH),
    "MAC_ADDRESS": (r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b', SENSITIVITY_MEDIUM),
    "DOMAIN": (r'\b(?:(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9])\b', SENSITIVITY_LOW),
    "URL": (r'https?://[^\s/$.?#].[^\s]*', SENSITIVITY_MEDIUM),
    "GEO_COORDINATES": (r'\b-?\d{1,3}\.\d+,\s*-?\d{1,3}\.\d+\b', SENSITIVITY_HIGH),
    "PHONE_NUMBER": (r'\+?\d{1,3}[- ]?\(?\d{3}\)?[- ]?\d{3,4}[- ]?\d{4}', SENSITIVITY_HIGH),
    "PASSPORT_NUMBER": (r'\b[A-Z]{1,2}\d{6,9}\b', SENSITIVITY_HIGH),
}

# AI Inference prevention patterns - to detect information that could be used to infer sensitive details
AI_INFERENCE_PATTERNS = {
    "INTERNAL_PROJECT_NAME": (r'project[: "\'=]+([A-Za-z0-9_-]{3,})', SENSITIVITY_MEDIUM),
    "API_ENDPOINT": (r'api\.internal\.[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', SENSITIVITY_HIGH),
    "INTERNAL_IP_RANGE": (r'10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}', SENSITIVITY_MEDIUM),
    "SERVER_PATH": (r'/var/www/[a-zA-Z0-9_/.-]+|/home/[a-zA-Z0-9_/.-]+|/srv/[a-zA-Z0-9_/.-]+', SENSITIVITY_MEDIUM),
    "DB_CONNECTION_STRING": (r'(jdbc|mongodb|mysql|postgresql):.*?://.+?\.[a-zA-Z]{2,}(:\d+)?/[a-zA-Z0-9_-]+', SENSITIVITY_HIGH),
    "CLOUD_RESOURCE": (r'arn:aws:[a-zA-Z0-9-]+:[a-zA-Z0-9-]*:\d{12}:[a-zA-Z0-9-/]+', SENSITIVITY_HIGH),
    "SESSION_IDENTIFIER": (r'sess-[a-zA-Z0-9]{16}|token-[a-zA-Z0-9]{16}', SENSITIVITY_HIGH),
    "CI_CD_CONFIG": (r'\.github/workflows/[a-zA-Z0-9_.-]+\.yml|\.gitlab-ci\.yml', SENSITIVITY_MEDIUM),
    "ENV_VARIABLE": (r'[A-Z][A-Z0-9_]{2,}=[a-zA-Z0-9_/+.-]+', SENSITIVITY_MEDIUM),
}

# Combined patterns
ALL_PATTERNS = {**PATTERNS, **AI_INFERENCE_PATTERNS}

# ===============================================================
# Database and Encryption
# ===============================================================

class DatabaseManager:
    """Manages storage and encryption of sensitive data mappings"""
    
    def __init__(self):
        self.db_path = 'data/privacy_mappings.db'
        self.encryption_enabled = ENCRYPTION_AVAILABLE and os.environ.get('ENCRYPT_DATABASE', 'true').lower() == 'true'
        self.fernet = None
        
        # Initialize encryption if enabled
        if self.encryption_enabled:
            self._initialize_encryption()
        
        # Set up the database connection
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create table if it doesn't exist
        self._create_tables()
    
    def _initialize_encryption(self):
        """Initialize encryption with existing or new key"""
        try:
            # Check for environment variable key
            env_key = os.environ.get('ENCRYPTION_KEY')
            key_file = os.path.join('data', '.privacy_key')
            
            if env_key:
                key = base64.b64decode(env_key)
                if len(key) != 32:
                    raise ValueError("Encryption key must be 32 bytes")
                self.fernet = Fernet(base64.b64encode(key))
                logger.info("Using encryption key from environment")
            elif os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
                self.fernet = Fernet(key)
                logger.info("Using existing encryption key from file")
            else:
                # Generate a new key
                key = Fernet.generate_key()
                self.fernet = Fernet(key)
                
                # Save the key
                with open(key_file, 'wb') as f:
                    f.write(key)
                os.chmod(key_file, 0o600)  # Restrict permissions
                logger.info(f"Generated new encryption key and saved to {key_file}")
        except Exception as e:
            logger.error(f"Error initializing encryption: {str(e)}")
            self.encryption_enabled = False
    
    def _create_tables(self):
        """Create necessary database tables"""
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original TEXT NOT NULL,
            replacement TEXT NOT NULL,
            entity_type TEXT,
            sensitivity TEXT,
            created_at TEXT,
            last_used TEXT,
            is_encrypted INTEGER DEFAULT 0
        )
        ''')
        
        # Create index for faster lookups
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_original ON mappings(original)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_replacement ON mappings(replacement)')
        
        # Create metrics table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            request_type TEXT,
            detected_entities INTEGER,
            transformed_entities INTEGER,
            sensitivity_high INTEGER,
            sensitivity_medium INTEGER,
            sensitivity_low INTEGER
        )
        ''')
        
        self.conn.commit()
    
    def encrypt(self, data):
        """Encrypt data if encryption is enabled"""
        if not self.encryption_enabled or data is None:
            return data
        
        try:
            if isinstance(data, str):
                return self.fernet.encrypt(data.encode()).decode()
            return data
        except Exception as e:
            logger.error(f"Encryption error: {str(e)}")
            return data
    
    def decrypt(self, data):
        """Decrypt data if encryption is enabled"""
        if not self.encryption_enabled or data is None:
            return data
        
        try:
            if isinstance(data, str):
                return self.fernet.decrypt(data.encode()).decode()
            return data
        except InvalidToken:
            logger.warning("Invalid token during decryption - data may not be encrypted")
            return data
        except Exception as e:
            logger.error(f"Decryption error: {str(e)}")
            return data
    
    def store_mapping(self, original, replacement, entity_type, sensitivity):
        """Store a mapping between original and replacement values"""
        now = datetime.now().isoformat()
        
        # Check if mapping already exists
        self.cursor.execute("SELECT id FROM mappings WHERE original = ?", (original,))
        result = self.cursor.fetchone()
        
        if result:
            # Update existing mapping
            self.cursor.execute(
                "UPDATE mappings SET last_used = ? WHERE id = ?",
                (now, result[0])
            )
        else:
            # Create new mapping
            is_encrypted = 1 if self.encryption_enabled else 0
            encrypted_original = self.encrypt(original) if self.encryption_enabled else original
            
            self.cursor.execute(
                "INSERT INTO mappings (original, replacement, entity_type, sensitivity, created_at, last_used, is_encrypted) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (encrypted_original, replacement, entity_type, sensitivity, now, now, is_encrypted)
            )
        
        self.conn.commit()
    
    def get_mapping(self, original):
        """Get replacement for an original value"""
        self.cursor.execute("SELECT replacement, is_encrypted FROM mappings WHERE original = ?", (original,))
        result = self.cursor.fetchone()
        
        if result:
            replacement, is_encrypted = result
            # Update last used time
            now = datetime.now().isoformat()
            self.cursor.execute("UPDATE mappings SET last_used = ? WHERE original = ?", (now, original))
            self.conn.commit()
            return replacement
        
        return None
    
    def get_original(self, replacement):
        """Get original value for a replacement"""
        self.cursor.execute("SELECT original, is_encrypted FROM mappings WHERE replacement = ?", (replacement,))
        result = self.cursor.fetchone()
        
        if result:
            original, is_encrypted = result
            if is_encrypted:
                return self.decrypt(original)
            return original
        
        return None
    
    def log_metrics(self, request_type, metrics):
        """Log privacy metrics for a request"""
        now = datetime.now().isoformat()
        
        self.cursor.execute(
            "INSERT INTO metrics (timestamp, request_type, detected_entities, transformed_entities, sensitivity_high, sensitivity_medium, sensitivity_low) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                now, 
                request_type, 
                metrics.get('detected_entities', 0),
                metrics.get('transformed_entities', 0),
                metrics.get('sensitivity_high', 0),
                metrics.get('sensitivity_medium', 0),
                metrics.get('sensitivity_low', 0)
            )
        )
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

# Global database manager instance
db_manager = DatabaseManager()

# ===============================================================
# Detection and Transformation
# ===============================================================

def _generate_placeholder(entity_type, sensitivity=None):
    """Generate a consistent placeholder for an entity"""
    prefix = "REDACTED"
    
    if entity_type:
        if entity_type == "EMAIL":
            prefix = "EMAIL"
        elif entity_type == "API_KEY":
            prefix = "API_KEY" 
        elif entity_type == "CREDENTIAL":
            prefix = "CRED"
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
        elif entity_type == "CLOUD_RESOURCE":
            prefix = "CLOUD"
        elif entity_type == "INTERNAL_PROJECT_NAME":
            prefix = "PROJECT"
        elif entity_type == "SERVER_PATH":
            prefix = "PATH"
        elif entity_type == "ENV_VARIABLE":
            prefix = "ENV"
        else:
            # Use first 3 chars of entity type
            prefix = entity_type[:3] if len(entity_type) >= 3 else entity_type
    
    # Add sensitivity level to the prefix
    if sensitivity:
        prefix = f"{prefix}_{sensitivity[:1]}"
        
    # Generate a random identifier
    random_id = str(uuid.uuid4())[:8]
    return f"__{prefix}_{random_id}__"

def detect_entities_regex(text):
    """
    Detect sensitive entities using regex patterns
    Returns a list of detected entities with positions
    """
    entities = []
    
    # Apply each pattern
    for entity_type, (pattern, sensitivity) in ALL_PATTERNS.items():
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            for match in regex.finditer(text):
                match_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Only add entities that don't overlap with existing ones
                overlap = False
                for entity in entities:
                    if (start_pos <= entity['end'] and end_pos >= entity['start']):
                        overlap = True
                        # If new match is longer or higher sensitivity, replace the existing one
                        if ((end_pos - start_pos) > (entity['end'] - entity['start']) or 
                            sensitivity_rank(sensitivity) > sensitivity_rank(entity['sensitivity'])):
                            entity['start'] = start_pos
                            entity['end'] = end_pos
                            entity['text'] = match_text
                            entity['entity_type'] = entity_type
                            entity['sensitivity'] = sensitivity
                        break
                
                if not overlap:
                    entities.append({
                        'start': start_pos,
                        'end': end_pos,
                        'text': match_text,
                        'entity_type': entity_type,
                        'sensitivity': sensitivity
                    })
        except Exception as e:
            logger.error(f"Error applying pattern {entity_type}: {str(e)}")
    
    # Sort entities by start position
    entities.sort(key=lambda x: x['start'])
    return entities

def sensitivity_rank(sensitivity):
    """Convert sensitivity label to numeric rank for comparison"""
    if sensitivity == SENSITIVITY_HIGH:
        return 3
    elif sensitivity == SENSITIVITY_MEDIUM:
        return 2
    else:  # SENSITIVITY_LOW
        return 1

def transform_text(text, entities=None):
    """
    Transform detected entities in text with privacy-preserving replacements
    Returns transformed text and transformation log
    """
    if not text:
        return text, []
        
    # Detect entities if not provided
    if entities is None:
        entities = detect_entities_regex(text)
    
    if not entities:
        return text, []
    
    # Transform text from end to beginning to maintain offsets
    entities.sort(key=lambda x: x['start'], reverse=True)
    transformed_text = text
    transformations = []
    
    metrics = {
        'detected_entities': len(entities),
        'transformed_entities': 0,
        'sensitivity_high': 0,
        'sensitivity_medium': 0,
        'sensitivity_low': 0
    }
    
    for entity in entities:
        original = entity['text']
        entity_type = entity['entity_type']
        sensitivity = entity['sensitivity']
        start = entity['start']
        end = entity['end']
        
        # Check if we already have a mapping for this value
        replacement = db_manager.get_mapping(original)
        
        # If not, create a new replacement
        if not replacement:
            replacement = _generate_placeholder(entity_type, sensitivity)
            db_manager.store_mapping(original, replacement, entity_type, sensitivity)
        
        # Replace in the text
        transformed_text = transformed_text[:start] + replacement + transformed_text[end:]
        
        # Track the transformation
        transformations.append({
            'original': original,
            'replacement': replacement,
            'entity_type': entity_type,
            'sensitivity': sensitivity
        })
        
        # Update metrics
        metrics['transformed_entities'] += 1
        if sensitivity == SENSITIVITY_HIGH:
            metrics['sensitivity_high'] += 1
        elif sensitivity == SENSITIVITY_MEDIUM:
            metrics['sensitivity_medium'] += 1
        else:
            metrics['sensitivity_low'] += 1
    
    # Log metrics
    db_manager.log_metrics('transform', metrics)
    
    return transformed_text, transformations

def restore_text(text):
    """
    Restore original values from redacted placeholders
    Returns restored text and count of restorations
    """
    if not text:
        return text, 0
    
    # Find all placeholder patterns
    placeholder_pattern = r'__([A-Z_]+)_([A-Z0-9]{1})_([a-zA-Z0-9-]{8})__'
    matches = re.finditer(placeholder_pattern, text)
    
    restored_text = text
    count = 0
    
    # Collect all matches first to handle overlapping replacements
    replacements = []
    for match in matches:
        placeholder = match.group(0)
        original = db_manager.get_original(placeholder)
        
        if original:
            replacements.append((match.start(), match.end(), original))
            count += 1
    
    # Apply replacements in reverse order to maintain offsets
    for start, end, original in sorted(replacements, key=lambda x: x[0], reverse=True):
        restored_text = restored_text[:start] + original + restored_text[end:]
    
    return restored_text, count

def transform_json(json_data):
    """
    Transform sensitive data in a JSON object
    Handles nested structures recursively
    """
    if isinstance(json_data, dict):
        result = {}
        for key, value in json_data.items():
            # Skip transformation for specific keys
            skip_keys = ['id', 'user_id', 'created_at', 'updated_at']
            if key in skip_keys:
                result[key] = value
            else:
                result[key] = transform_json(value)
        return result
    elif isinstance(json_data, list):
        return [transform_json(item) for item in json_data]
    elif isinstance(json_data, str):
        transformed, _ = transform_text(json_data)
        return transformed
    else:
        # For other types (int, float, bool, None)
        return json_data

def restore_json(json_data):
    """
    Restore original values in a JSON object
    Handles nested structures recursively
    """
    if isinstance(json_data, dict):
        result = {}
        for key, value in json_data.items():
            result[key] = restore_json(value)
        return result
    elif isinstance(json_data, list):
        return [restore_json(item) for item in json_data]
    elif isinstance(json_data, str):
        restored, _ = restore_text(json_data)
        return restored
    else:
        # For other types (int, float, bool, None)
        return json_data

# ===============================================================
# Public API
# ===============================================================

def process_input(text, content_type=None):
    """
    Process input to an AI model, detecting and transforming sensitive information
    Returns:
        - Transformed text/data
        - Privacy metrics
        - Log of transformations
    """
    metrics = {
        'detected_entities': 0,
        'transformed_entities': 0,
        'sensitivity_high': 0,
        'sensitivity_medium': 0,
        'sensitivity_low': 0
    }
    
    # Handle different content types
    if content_type and 'json' in content_type:
        try:
            data = json.loads(text)
            transformed_data = transform_json(data)
            return json.dumps(transformed_data), metrics, []
        except json.JSONDecodeError:
            logger.warning("Invalid JSON content despite content type")
    
    # Default to plain text processing
    transformed, transformations = transform_text(text)
    
    # Update metrics
    metrics['detected_entities'] = len(transformations)
    metrics['transformed_entities'] = len(transformations)
    
    for t in transformations:
        sensitivity = t.get('sensitivity', SENSITIVITY_LOW)
        if sensitivity == SENSITIVITY_HIGH:
            metrics['sensitivity_high'] += 1
        elif sensitivity == SENSITIVITY_MEDIUM:
            metrics['sensitivity_medium'] += 1
        else:
            metrics['sensitivity_low'] += 1
    
    return transformed, metrics, transformations

def process_output(text, content_type=None):
    """
    Process output from an AI model, restoring original values where needed
    while still protecting sensitive information
    """
    # Handle different content types
    if content_type and 'json' in content_type:
        try:
            data = json.loads(text)
            restored_data = restore_json(data)
            return json.dumps(restored_data)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON content despite content type")
    
    # Default to plain text processing
    restored, count = restore_text(text)
    return restored

def get_privacy_metrics():
    """Get aggregated privacy metrics from the database"""
    try:
        db_manager.cursor.execute("""
            SELECT 
                COUNT(*) as total_requests,
                SUM(detected_entities) as total_detected,
                SUM(transformed_entities) as total_transformed,
                SUM(sensitivity_high) as total_high,
                SUM(sensitivity_medium) as total_medium,
                SUM(sensitivity_low) as total_low,
                MAX(timestamp) as last_activity
            FROM metrics
        """)
        
        result = db_manager.cursor.fetchone()
        
        if result:
            return {
                'total_requests': result[0],
                'total_detected': result[1] or 0,
                'total_transformed': result[2] or 0,
                'sensitivity_high': result[3] or 0,
                'sensitivity_medium': result[4] or 0,
                'sensitivity_low': result[5] or 0,
                'last_activity': result[6]
            }
        
        return {
            'total_requests': 0,
            'total_detected': 0,
            'total_transformed': 0,
            'sensitivity_high': 0,
            'sensitivity_medium': 0,
            'sensitivity_low': 0,
            'last_activity': None
        }
    except Exception as e:
        logger.error(f"Error getting privacy metrics: {str(e)}")
        return {'error': str(e)}

# Close database connection when the module is unloaded
import atexit
atexit.register(db_manager.close)

# Simple test if run directly
if __name__ == "__main__":
    # Configure test logging
    logging.basicConfig(level=logging.INFO)
    
    test_text = """
    My email is john.doe@example.com and my credit card is 4111-1111-1111-1111.
    The API key is sk_test_abcdefghijklmnopqrstuvwxyz123456.
    Our internal project name is project="MANHATTAN" and we host it at 192.168.1.100.
    """
    
    print("Original text:")
    print(test_text)
    print("\nTransformed text:")
    transformed, metrics, log = process_input(test_text)
    print(transformed)
    print("\nMetrics:", metrics)
    print("\nTransformation log:", log)
    
    print("\nRestored text:")
    restored = process_output(transformed)
    print(restored) 