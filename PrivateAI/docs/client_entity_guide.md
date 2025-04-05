# Client-Specific Entity Protection Guide

This document explains how to configure the Private AI system to protect client-specific entities and sensitive information.

## Overview

The Private AI system can be configured to protect any client-specific information through:

1. Domain blocklists
2. Custom entity patterns
3. Entity type definitions
4. Customizable replacement text

This approach eliminates the need to add individual entities one by one, as it uses pattern matching to detect and protect entire categories of sensitive information.

## Setup Process

### 1. Domain Blocklist

The domain blocklist allows you to specify which domains should be automatically detected and redacted.

**Location**: `data/domain_blocklist.txt`

**Format**:
```
# Comments are supported with #
client-domain.com
subdomain.client-domain.com
```

**Usage**:
- Add all client domains, subdomains, and partner domains
- The system will detect these domains in URLs, email addresses, and plain text

### 2. Custom Entity Patterns

Custom entity patterns let you define regex patterns for client-specific information.

**Location**: `data/custom_patterns.json`

**Format**:
```json
{
  "pattern_name": {
    "name": "pattern_name",
    "entity_type": "CUSTOM",
    "pattern": "regex_pattern_here",
    "description": "Description of what this pattern matches",
    "is_active": true,
    "priority": "1",
    "created_at": "timestamp"
  }
}
```

**Entity Types**:
- `INTERNAL_PROJECT_NAME`: For project codenames
- `SECURITYDATA`: For security-related identifiers
- `CUSTOM`: For any client-specific custom entities
- Many other predefined types are available

**Priority Levels**:
- `1`: High priority (processed first)
- `2`: Medium priority
- `3`: Low priority (processed last)

### 3. Web Interface

You can also manage domains and patterns through the admin web interface:

1. Start the admin panel: `./run_admin.sh`
2. Access: http://localhost:5000
3. Navigate to "Domains" or "Patterns" section
4. Add, edit, or remove entries

## Examples

### Example: Project Names

To protect project codenames like "PROJECT APOLLO", "PROJECT ZEUS":

```json
{
  "client_project_names": {
    "name": "client_project_names",
    "entity_type": "INTERNAL_PROJECT_NAME",
    "pattern": "PROJECT\\s+(APOLLO|ZEUS|ATHENA|MERCURY|JUPITER)",
    "description": "Client's internal project code names",
    "is_active": true,
    "priority": "1"
  }
}
```

### Example: Team Names

```json
{
  "client_team_names": {
    "name": "client_team_names",
    "entity_type": "CUSTOM",
    "pattern": "Team\\s+(Alpha|Beta|Gamma|Delta|Omega)",
    "description": "Client's internal team names",
    "is_active": true,
    "priority": "2"
  }
}
```

## Verification

To verify your configuration works:

1. Run the client demo: `python client_demo.py`
2. Start the proxy: `./run_proxy.sh`
3. Configure your application to use the proxy (localhost:8080)
4. Send test messages and verify sensitive information is protected

## Troubleshooting

If entities aren't being detected:

1. Check that the pattern syntax is valid regex
2. Verify the pattern is marked as `"is_active": true`
3. Look at the logs (`data/proxy.log`) for detection details
4. Try with explicit examples using `client_demo.py`

## Advanced Configuration

### Global Domain Blocking

To block all domains (not just those in the blocklist):

```bash
# In .env file
BLOCK_ALL_DOMAINS=true
```

### Custom Entity Types

You can define new entity types by adding them to the form in `app.py` and then using them in your patterns.

### Custom Replacement Text

The system generates context-aware replacement text based on the entity type. To customize the format, modify the `_generate_placeholder` function in `privacy_assistant.py`.