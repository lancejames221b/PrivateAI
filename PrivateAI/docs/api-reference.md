# API Reference

The AI Privacy Proxy provides both a REST API for configuration and management, and a programmatic API for direct integration with your applications.

## REST API

The admin interface exposes a REST API that can be used to interact with the proxy programmatically.

### Authentication

All API endpoints use the same authentication as the web interface:

```bash
# Using curl with basic auth
curl -u username:password http://localhost:5001/api/stats
```

### API Endpoints

#### Statistics

**GET /api/stats**

Retrieve system statistics including mapping counts and proxy status.

```bash
curl -X GET http://localhost:5001/api/stats
```

Response:
```json
{
  "total_mappings": 156,
  "entity_types": {
    "ORGANIZATION": 24,
    "DOMAIN": 35,
    "EMAIL": 18,
    "API_KEY": 7,
    "CREDENTIAL": 15,
    "URL": 42,
    "IP_ADDRESS": 15
  },
  "inference_count": 23,
  "proxy_running": true
}
```

#### Mappings

**GET /api/mappings**

Retrieve all current mappings.

```bash
curl -X GET http://localhost:5001/api/mappings
```

Response:
```json
{
  "mappings": [
    {
      "original": "SentinelOne",
      "replacement": "CyberGuardian",
      "entity_type": "ORGANIZATION",
      "created_at": "2023-06-15T14:30:22.123456",
      "last_used": "2023-06-16T09:45:12.567890"
    },
    {
      "original": "user@example.com",
      "replacement": "redacted.email08cf3@example.com",
      "entity_type": "EMAIL",
      "created_at": "2023-06-15T14:32:45.654321",
      "last_used": "2023-06-16T10:12:34.987654"
    }
  ]
}
```

**DELETE /api/mappings/:id**

Delete a specific mapping.

```bash
curl -X DELETE http://localhost:5001/api/mappings/SentinelOne
```

Response:
```json
{
  "success": true,
  "message": "Mapping deleted successfully"
}
```

#### Patterns

**GET /api/patterns**

Retrieve all detection patterns.

```bash
curl -X GET http://localhost:5001/api/patterns
```

Response:
```json
{
  "patterns": {
    "API_KEY": {
      "name": "API_KEY",
      "entity_type": "API_KEY",
      "pattern": "(sk|pk)_(test|live|proj|or-v1|ant-api\\d+)_[0-9a-zA-Z_-]{24,}",
      "description": "Detects API keys",
      "is_active": true,
      "priority": "2"
    }
  }
}
```

**POST /api/patterns**

Add a new pattern.

```bash
curl -X POST http://localhost:5001/api/patterns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "INTERNAL_PROJECT",
    "entity_type": "INTERNAL_PROJECT_NAME",
    "pattern": "\\b(Project\\s+Phoenix|Phoenix\\s+Initiative)\\b",
    "description": "Detects internal project names",
    "is_active": true,
    "priority": "1"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Pattern added successfully"
}
```

**PUT /api/patterns/:name**

Update an existing pattern.

```bash
curl -X PUT http://localhost:5001/api/patterns/INTERNAL_PROJECT \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'
```

Response:
```json
{
  "success": true,
  "message": "Pattern updated successfully"
}
```

**DELETE /api/patterns/:name**

Delete a pattern.

```bash
curl -X DELETE http://localhost:5001/api/patterns/INTERNAL_PROJECT
```

Response:
```json
{
  "success": true,
  "message": "Pattern deleted successfully"
}
```

#### Domains

**GET /api/domains**

Retrieve the domain blocklist.

```bash
curl -X GET http://localhost:5001/api/domains
```

Response:
```json
{
  "blocklist": [
    "sentinelone.net",
    "sentinelone.com",
    "internal-system.company.net"
  ],
  "block_all_domains": false
}
```

**POST /api/domains**

Add a domain to the blocklist.

```bash
curl -X POST http://localhost:5001/api/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example-secret-domain.com"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Domain added to blocklist"
}
```

**DELETE /api/domains/:domain**

Remove a domain from the blocklist.

```bash
curl -X DELETE http://localhost:5001/api/domains/example-secret-domain.com
```

Response:
```json
{
  "success": true,
  "message": "Domain removed from blocklist"
}
```

**PUT /api/domains/block-all**

Update the "block all domains" setting.

```bash
curl -X PUT http://localhost:5001/api/domains/block-all \
  -H "Content-Type: application/json" \
  -d '{
    "block_all_domains": true
  }'
```

Response:
```json
{
  "success": true,
  "message": "Block all domains setting updated"
}
```

#### Logs

**GET /api/logs**

Retrieve recent log entries.

```bash
curl -X GET http://localhost:5001/api/logs
```

Response:
```json
{
  "logs": [
    {
      "timestamp": "2023-06-16T10:15:23.456789",
      "level": "INFO",
      "message": "Transformed request to OpenAI API"
    },
    {
      "timestamp": "2023-06-16T10:15:24.567890",
      "level": "INFO",
      "message": "Restored response from OpenAI API"
    }
  ]
}
```

## Programmatic API

The proxy can also be used programmatically in your Python applications.

### PII Transformation

To use the transformation system directly:

```python
from pii_transform import detect_and_transform, restore_original_values

# Transform sensitive text
text = "Contact support@sentinelone.com for assistance with API key sk_test_1234567890."
transformed_text, log = detect_and_transform(text)
print(f"Transformed: {transformed_text}")

# Restore original values
restored_text = restore_original_values(transformed_text)
print(f"Restored: {restored_text}")
```

### Codename Generation

To use the codename generator:

```python
from codename_generator import get_organization_codename, get_domain_codename

# Generate a codename for an organization
org_name = "Acme Corporation"
codename = get_organization_codename(org_name)
print(f"{org_name} → {codename}")

# Generate a codename for a domain
domain = "api.acmecorp.com"
domain_codename = get_domain_codename(domain)
print(f"{domain} → {domain_codename}")
```

### Custom Transformation Handlers

You can create custom transformation handlers for specialized needs:

```python
from pii_transform import placeholder_mappings, generate_placeholder

def custom_transform(text, entity_type, pattern):
    """Custom transformation function for specific entity types"""
    import re
    
    def replace_match(match):
        value = match.group(0)
        placeholder = generate_placeholder(entity_type, value)
        return placeholder
    
    return re.sub(pattern, replace_match, text)

# Example usage
text = "Project Phoenix launch scheduled for Q3 2023"
pattern = r'\b(Project\s+Phoenix)\b'
transformed = custom_transform(text, "INTERNAL_PROJECT_NAME", pattern)
print(transformed)
```

### Database Integration

Access the mapping database directly:

```python
import sqlite3

def get_mappings_by_type(entity_type):
    """Retrieve all mappings of a specific entity type"""
    conn = sqlite3.connect('data/mapping_store.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT original, replacement, created_at FROM mappings WHERE entity_type = ?",
        (entity_type,)
    )
    
    mappings = cursor.fetchall()
    conn.close()
    
    return mappings

# Example usage
org_mappings = get_mappings_by_type("ORGANIZATION")
for original, replacement, created_at in org_mappings:
    print(f"{original} → {replacement} (created: {created_at})")
```

### Extending the Proxy

To add custom middleware to the proxy:

```python
from mitmproxy import http
from pii_transform import detect_and_transform, restore_original_values

class CustomInterceptor:
    """Custom interceptor for specific API endpoints"""
    
    def __init__(self):
        self.target_endpoints = [
            "api.example.com/v1/sensitive",
            "api.internal.company/data"
        ]
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Process outgoing requests"""
        if any(endpoint in flow.request.pretty_url for endpoint in self.target_endpoints):
            # Apply custom logic to these endpoints
            if flow.request.content:
                content = flow.request.content.decode("utf-8", "ignore")
                transformed, _ = detect_and_transform(content)
                flow.request.content = transformed.encode("utf-8")
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Process incoming responses"""
        if any(endpoint in flow.request.pretty_url for endpoint in self.target_endpoints):
            if flow.response.content:
                content = flow.response.content.decode("utf-8", "ignore")
                restored = restore_original_values(content)
                flow.response.content = restored.encode("utf-8")

# To use this interceptor, add it to the proxy_intercept.py file
```

## WebSocket API

The admin interface also provides a WebSocket API for real-time updates:

### Connection

```javascript
const socket = new WebSocket('ws://localhost:5001/ws');

socket.onopen = function(event) {
  console.log('Connected to AI Privacy Proxy');
};

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Events

The WebSocket API emits events for:

- New transformations
- Proxy status changes
- New entity detections

Example event:
```json
{
  "event": "transformation",
  "data": {
    "original": "SentinelOne",
    "replacement": "CyberGuardian",
    "entity_type": "ORGANIZATION",
    "timestamp": "2023-06-16T14:32:45.654321"
  }
}
```

## Error Handling

All API endpoints use standard HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **401**: Unauthorized (authentication required)
- **404**: Not found (resource doesn't exist)
- **500**: Server error

Error responses include a descriptive message:

```json
{
  "error": "Invalid pattern format",
  "message": "Pattern must be a valid regular expression"
}
```