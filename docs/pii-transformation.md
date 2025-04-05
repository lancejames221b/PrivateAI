# PII Detection & Transformation

The PII Detection and Transformation system is the core of the AI Privacy Proxy, responsible for identifying and replacing sensitive information in both requests and responses.

## Multi-layered Detection

The system uses multiple detection methods for comprehensive coverage:

### 1. Regular Expression Patterns

Fast, precise pattern matching for structured data like:
- Email addresses
- API keys
- Credit card numbers
- IP addresses
- Domain names
- Phone numbers

```python
PATTERNS = {
    "API_KEY": r'(sk|pk)_(test|live|proj|or-v1|ant-api\d+)_[0-9a-zA-Z_-]{24,}',
    "EMAIL": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "IP_ADDRESS": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    # More patterns...
}
```

### 2. Named Entity Recognition (NER)

Machine learning models that identify entities in unstructured text:
- Organizations
- People
- Locations
- Dates
- Products

The system uses transformer-based models from the Hugging Face library, with a default model of `dslim/bert-base-NER`.

### 3. Microsoft Presidio Integration

Enterprise-grade PII detection framework with advanced analyzers:
- Deep contextual understanding
- Custom entity recognizers
- Confidence scoring
- Adaptable to different domains

### 4. Custom Pattern Definitions

User-defined patterns for organization-specific information:
- Internal project names
- Product codenames
- Custom formats
- Industry-specific terminology

## Transformation Process

The transformation process flows as follows:

1. **Input Analysis**: Text is analyzed to determine if it's plain text or JSON
2. **Entity Detection**: Multiple detection methods are applied
3. **Placeholder Generation**: Consistent placeholders are created for detected entities
4. **Transformation Application**: Original text is modified to replace sensitive information
5. **Mapping Storage**: Mappings between original values and placeholders are stored
6. **Result Return**: Transformed text is returned with a log of changes

### JSON Handling

The system includes special handling for JSON data:

```python
if (text.strip().startswith('{') and text.strip().endswith('}')) or \
   (text.strip().startswith('[') and text.strip().endswith(']')):
    try:
        json_data = json.loads(text)
        transformed_json, log = transform_json(json_data)
        if log:
            transformations_log.extend(log)
            return json.dumps(transformed_json), transformations_log
    except json.JSONDecodeError:
        pass  # Not valid JSON, continue with regular text processing
```

JSON transformation is recursive, handling nested objects and arrays while preserving structure.

## Bidirectional Mapping

One of the key features is bidirectional mapping, allowing original values to be restored:

```python
# Store the mapping in both directions for bidirectional transformation
placeholder_mappings[placeholder_key] = placeholder
reverse_key = f"REVERSE:{placeholder}"
placeholder_mappings[reverse_key] = value if value else f"UNKNOWN_{entity_type}"
```

This enables:
1. Replacing sensitive data in outgoing requests
2. Preserving the meaning and structure of the content
3. Restoring original values in incoming responses

## Placeholder Types

The system generates various types of contextually appropriate placeholders:

| Entity Type | Original | Placeholder Example |
|-------------|----------|---------------------|
| Organization | SentinelOne | CyberGuardian |
| Domain | console.sentinelone.net | domain-381f3c05.example.com |
| Email | user@company.com | redacted.email08cf3@example.com |
| API Key | sk_test_abcdefg123456 | api-key-XXXX...XXXX474d |
| IP Address | 192.168.1.1 | 192.0.2.ab |
| Credit Card | 4111-1111-1111-1111 | XXXX-XXXX-XXXX-XXXX |

## Persistent Storage

Mappings are stored in a SQLite database for persistence across sessions:

```
data/mapping_store.db
```

The database includes encryption capabilities for sensitive mappings:

```python
class DatabaseEncryption:
    def __init__(self):
        self.encryption_enabled = os.environ.get('ENCRYPT_DATABASE', 'true').lower() == 'true'
        # Encryption implementation...
```

## Restoration Process

The restoration process works in reverse:

1. **Placeholder Detection**: Scans text for known placeholders
2. **Mapping Lookup**: Retrieves original values from the mapping store
3. **Substitution**: Replaces placeholders with original values
4. **Result Return**: Returns restored text with context intact

For JSON data, a special recursive restoration process is used:

```python
def restore_json_values(json_data):
    """
    Recursively restore original values in JSON data.
    """
    if isinstance(json_data, dict):
        result = {}
        for key, value in json_data.items():
            # Restore key if it's a placeholder
            restored_key = key
            # Process key...
            
            # Process the value
            if isinstance(value, (dict, list)):
                restored_value = restore_json_values(value)
            elif isinstance(value, str):
                restored_value = restore_original_values(value)
            else:
                restored_value = value
                
            result[restored_key] = restored_value
        return result
    # Handle lists and other types...
```

## Custom Pattern Configuration

You can define custom patterns through:

1. **Admin Interface**: Add patterns via the web UI
2. **Configuration File**: Edit `data/custom_patterns.json`
3. **Direct Database Access**: Modify the patterns table

Example pattern definition:

```json
{
  "INTERNAL_PROJECT_NAME": {
    "name": "INTERNAL_PROJECT_NAME",
    "entity_type": "INTERNAL_PROJECT_NAME",
    "pattern": "\\b(Project\\s+[A-Z][a-z]+|[A-Z][a-z]+\\s+Initiative)\\b",
    "description": "Matches internal project names",
    "is_active": true,
    "priority": "2",
    "created_at": "2023-06-15T14:30:22.123456"
  }
}
```

## Handling Special Cases

### URL Components

URLs receive special treatment to maintain valid structure:

```python
from urllib.parse import urlparse, urlunparse
parsed = urlparse(value)
                    
# Create domain replacement using generate_placeholder
domain_placeholder = generate_placeholder("DOMAIN", parsed.netloc)
                    
# Reconstruct the URL with the placeholder domain
placeholder = urlunparse((
    parsed.scheme,
    domain_placeholder, 
    parsed.path,
    parsed.params,
    parsed.query,
    parsed.fragment
))
```

### API Keys

API keys maintain their prefix structure for better recognition:

```python
if value and len(value) > 12:
    parts = value.split('_')
    if len(parts) > 1 and parts[0].lower() in ['sk', 'pk', 'api']:
        # Keep the prefix pattern but mask the rest
        prefix = '_'.join(parts[:2])
        placeholder = f"{prefix}_XXXX...XXXX{hashlib.md5(value.encode()).hexdigest()[:4]}"
```

## Performance Considerations

The system is designed for performance:

1. **Fast-path Pattern Matching**: Quick regex checks before deeper analysis
2. **Progressive Detection**: Starts with fastest methods, escalates to more intensive ones
3. **Caching**: Reuses previous mappings for consistent entities
4. **Batch Processing**: Handles multiple transformations in a single pass

## Integration with Codename Generator

The PII transformation engine integrates with the Codename Generator:

```python
if CODENAME_GENERATOR_AVAILABLE:
    if entity_type == "ORGANIZATION" or entity_type == "PERSON":
        if value:
            placeholder = get_organization_codename(value)
        else:
            placeholder = f"Organization-{uuid.uuid4().hex[:6]}"
```

This ensures that organization names are replaced with meaningful, consistent codenames rather than generic placeholders.

## Troubleshooting Transformation Issues

Common issues and solutions:

1. **Inconsistent Replacement**: Check if the entity appears differently in different places
2. **Missed Detection**: Add a custom pattern or adjust confidence thresholds
3. **Over-detection**: Make patterns more specific or add exception rules
4. **Restoration Failures**: Verify bidirectional mappings are intact

You can view transformation logs in the admin interface or directly in the log files.