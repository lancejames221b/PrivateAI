# Dynamic Codename Generation: The Art of Disguise 🕵️

The Dynamic Codename Generation system is a core feature of the AI Privacy Proxy. It creates consistent, natural-sounding replacement names for organizations, products, and domains, enhancing both privacy and readability. Let's explore how it works.

## How It Works

Unlike simple UUID or hash-based replacements, the codename generator creates meaningful, contextually appropriate names through these steps:

1.  **Industry Detection**: Analyzing the organization name to infer its industry.
2.  **Consistent Hashing**: Using a hash of the original name to ensure the same entity always gets the same codename.
3.  **Name Construction**: Combining industry-appropriate prefixes with relevant nouns.
4.  **Database Storage**: Storing mappings persistently for consistency across sessions.
5.  **Bidirectional Mapping**: Maintaining both original→codename and codename→original mappings.

## Examples

| Original Name | Generated Codename | Industry |
|---------------|-------------------|----------|
| SentinelOne | CyberGuardian | Security |
| Microsoft | LogicStream | Software |
| Acme Corp | DevMind | Software |
| CloudNine Solutions | SkyCircuit | Cloud |
| HealthFirst Medical | VitalCare | Healthcare |

## Industry Detection

The system detects industries based on keywords in the organization name:

```python
industry_keywords = {
    "security": ["security", "cyber", "protect", "defense", "guard"],
    "cloud": ["cloud", "aws", "azure", "gcp", "hosting", "saas"],
    "ai": ["ai", "ml", "artificial", "intelligence", "neural"],
    "software": ["software", "app", "tech", "code", "dev", "system"],
    # Additional industries...
}
```

If no industry is detected, it defaults to "software" as the most generic option.

## Codename Structure

Codenames are constructed by selecting:

1. An industry-appropriate prefix (e.g., "Cyber" for security companies)
2. A relevant noun (e.g., "Guardian", "Shield", "Sentinel")

This combination creates natural-sounding names that are:
- Memorable and easy to recognize
- Consistent across sessions
- Appropriate to the entity's domain

## Domain Name Generation

For domain names, the system creates replacements that maintain the structure:

```
original: api.sentinelone.com
codename: cyberguardian-12ab34cd.example.com
```

Domain codenames include:
- Organization association (when detected)
- Unique hash component for subdomain variety
- Consistent .example.com TLD

## URL Handling

URLs receive special treatment to maintain their structure:

```
original: https://console.sentinelone.net/api/v2/sites
codename: https://domain-381f3c05.example.com/api/v2/sites
```

Notice how the path components are preserved while the domain is replaced.

## Using the Codename Generator

### In Proxy Mode

When running as a proxy, the codename generation happens automatically.

### Programmatic API

You can also use the codename generator programmatically:

```python
from codename_generator import get_organization_codename, get_domain_codename

# Generate a codename for an organization
org_codename = get_organization_codename("SentinelOne")
print(org_codename)  # Output: CyberGuardian

# Generate a codename for a domain
domain_codename = get_domain_codename("console.sentinelone.net")
print(domain_codename)  # Output: domain-381f3c05.example.com
```

## Database Backend

Codenames are stored in a SQLite database for persistence:

```
data/codename_mappings.db
```

The database has two main tables:
- `organization_mappings`: Maps organization names to codenames
- `domain_mappings`: Maps domain names to codenames, with optional organization links

### Schema

```sql
CREATE TABLE organization_mappings (
    original TEXT PRIMARY KEY,
    codename TEXT NOT NULL,
    industry TEXT,
    created_at TEXT,
    last_used TEXT
);

CREATE TABLE domain_mappings (
    original TEXT PRIMARY KEY,
    codename TEXT NOT NULL,
    organization_id TEXT,
    created_at TEXT,
    last_used TEXT,
    FOREIGN KEY (organization_id) REFERENCES organization_mappings(original)
);
```

## Importing and Exporting Mappings

You can export mappings to JSON for backup or transfer:

```python
from codename_generator import export_mappings

# Export to a custom location
export_mappings("path/to/export.json")
```

And import them back:

```python
from codename_generator import import_mappings

success, message = import_mappings("path/to/export.json")
if success:
    print("Import successful")
else:
    print(f"Import failed: {message}")
```

## Customizing Codename Generation

You can customize the codename generation by modifying these lists in `codename_generator.py`:

- `ADJECTIVES`: List of general adjectives for codenames
- `TECH_NOUNS`: List of tech-related nouns for codenames
- `INDUSTRY_PREFIXES`: Dictionary mapping industries to appropriate prefixes

For example, to add healthcare-specific prefixes:

```python
INDUSTRY_PREFIXES["healthcare"].extend(["Wellness", "Remedy", "Heal", "Vitality"])
```

## Viewing Codename Mappings

You can view all mappings through the admin interface at `/mappings` or directly in the database using SQLite tools:

```bash
sqlite3 data/codename_mappings.db "SELECT original, codename, industry FROM organization_mappings;"
```

## Advanced Usage

### Mapping Between Multiple Systems

If you need to use the same codenames across multiple instances:

1. Export mappings from the first system:
   ```python
   from codename_generator import export_mappings
   export_mappings("mappings_export.json")
   ```

2. Transfer the JSON file to the second system

3. Import on the second system:
   ```python
   from codename_generator import import_mappings
   import_mappings("mappings_export.json")
   ```

### Adding Fixed Mappings

For critical organizations that should always have specific codenames:

```python
import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('data/codename_mappings.db')
cursor = conn.cursor()

# Add a fixed mapping
cursor.execute("""
    INSERT OR REPLACE INTO organization_mappings (original, codename, industry, created_at, last_used)
    VALUES (?, ?, ?, ?, ?)
""", (
    "SensitiveOrg", "FixedCodename", "security",
    datetime.now().isoformat(), datetime.now().isoformat()
))

conn.commit()
conn.close()
```