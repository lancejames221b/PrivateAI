# Dynamic Codename System for Data Privacy

We've implemented a sophisticated dynamic codename generation system that provides consistent, reversible transformations for organizations, domains, URLs, and other sensitive entities. This system ensures that:

1. When sensitive data like domain names, URLs, or organization names are detected, they are replaced with consistent codenames rather than generic placeholders
2. The system maintains bidirectional mappings to restore original values in responses from AI systems
3. Codenames are persistent across sessions and consistently applied

## Key Components

### 1. Codename Generator (`codename_generator.py`)

This module offers dynamic generation of professional-sounding codenames for organizations and domains:

- Generates codenames based on entity type, name characteristics, and industry
- Uses hash-based deterministic generation for consistency
- Maintains an SQLite database of mappings for persistence across sessions
- Provides import/export functionality for mapping tables

### 2. Bidirectional Placeholder Mapping

The system maintains two-way mappings between original values and their codenames:

- Forward mapping: `entity_type:value -> codename`
- Reverse mapping: `REVERSE:codename -> value`

This ensures that any transformed content can be properly restored when received back from AI services.

### 3. Custom URL Handlers

Special handling for known domains and URLs:

- Specific URL patterns are detected and given consistent replacements
- JSON field-specific handling for special data structures
- Context-aware replacement for partial entity mentions

## Example Transformations

| Original | Transformed | Notes |
|----------|-------------|-------|
| `SentinelOne` | `CyberGuardian` | Organization name |
| `https://console.sentinelone.net` | `<URL-CONSOLE>` | Special URL handling |
| `ssh root@s1.com` | `ssh root@redacted.emailXXXXX@example.com` | Email address protection |
| API tokens | `api-key-XXXX...XXXX{hash}` | Format-preserving redaction |

## Advantages Over Generic PII Systems

1. **Consistency**: Same entity always gets the same codename
2. **Readability**: Generated codenames are meaningful (vs. random placeholders)
3. **Bidirectional**: System can restore original values from codenames
4. **Extensible**: New entity types can be easily added
5. **Context-Preserving**: Maintains conversation flow with natural-sounding replacements

## Future Improvements

- Better handling of partial entity mentions (e.g., "S1" vs "SentinelOne")
- Enhanced support for domain variants and subdomains
- More sophisticated industry detection for better codename generation
- Handling of compound entities (e.g., "SentinelOne agent") 
- Enhanced URL reverse mapping consistency
- User-defined codename preferences