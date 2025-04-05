# Admin Interface Guide

The AI Privacy Proxy includes a comprehensive web-based admin interface for configuration, monitoring, and management. This guide explains its features and usage.

## Accessing the Admin Interface

By default, the admin interface is available at:
- **Local installation**: [http://localhost:5001](http://localhost:5001)
- **Docker installation**: [http://localhost:5001](http://localhost:5001)

## Dashboard

![Admin Dashboard](./images/admin-dashboard.png)

The dashboard provides a high-level overview of:

- **Proxy Status**: Whether the proxy server is running
- **Mapping Statistics**: Total number of mappings, entity types, etc.
- **Recent Activity**: Latest transformations and detections
- **Domain Blocklist Status**: Number of blocked domains
- **System Health**: Key metrics and status indicators

### Starting and Stopping the Proxy

The dashboard includes controls to start and stop the proxy server:

- **Start Proxy**: Launches the proxy service if it's not running
- **Stop Proxy**: Shuts down the proxy service
- **Restart Proxy**: Restarts the proxy service (useful after configuration changes)

## Mappings Management

The Mappings page shows all transformations that have been applied:

![Mappings Page](./images/mappings-page.png)

For each mapping, you can see:
- **Original Value**: The sensitive information that was detected
- **Replacement**: The placeholder or codename that replaced it
- **Entity Type**: The type of entity (ORGANIZATION, EMAIL, API_KEY, etc.)
- **Created/Last Used**: Timestamps for creation and last usage

### Actions

- **Delete**: Remove a mapping (will be recreated if the entity is encountered again)
- **Export**: Download all mappings as a CSV file for backup or analysis

## Pattern Management

The Patterns page allows you to define and manage custom detection patterns:

![Patterns Page](./images/patterns-page.png)

### Adding Patterns

1. **Fill the form**:
   - **Pattern Name**: A unique identifier
   - **Entity Type**: The category of information
   - **Regex Pattern**: A regular expression to match the entity
   - **Description**: Optional explanation
   - **Priority**: Determines processing order (1=high, 3=low)

2. **Click Save Pattern**

### Managing Patterns

- **Toggle Active/Inactive**: Temporarily disable patterns without deleting them
- **Delete**: Permanently remove a pattern
- **Edit**: Modify an existing pattern

### Pattern Types

Patterns are grouped by entity type:
- **Generic Patterns**: General-purpose patterns
- **Domain Patterns**: For detecting domain names
- **API Keys**: For API key formats
- **Organization-specific**: Custom patterns for your organization

## Domain Management

The Domains page controls which domain names are protected:

![Domains Page](./images/domains-page.png)

### Domain Blocklist

The blocklist specifies which domains should be anonymized:

1. **Add Domain**: Enter a domain and click "Add to Blocklist"
2. **Remove Domain**: Click the delete button next to a domain

### Block All Domains

Toggle the "Block All Domains" setting:
- **On**: All domains will be anonymized regardless of blocklist
- **Off**: Only domains in the blocklist will be anonymized

## Logs Viewer

The Logs page shows the proxy's activity:

![Logs Page](./images/logs-page.png)

- **Live Logs**: Real-time log output
- **Filter Options**: Focus on specific message types
- **Log Level**: Adjust the detail level (INFO, DEBUG, WARNING, ERROR)

## Setup Assistant

The Setup page helps with initial configuration:

![Setup Page](./images/setup-page.png)

### Certificate Installation

For HTTPS interception, you need to install the MITM proxy's certificate:

1. **Generate Certificate**: Click "Install Certificate"
2. **Follow Instructions**: System-specific steps to trust the certificate

### Presidio Setup

Microsoft Presidio enhances PII detection:

1. **Install Requirements**: Click "Setup Presidio"
2. **Status Check**: Verify Presidio is properly configured

## Security Check

The Security Check page helps ensure your proxy is securely configured:

![Security Check](./images/security-check.png)

It checks for:
- **Authentication**: Whether basic auth is enabled
- **Default Passwords**: Whether default credentials have been changed
- **Secure Keys**: Whether default secret keys have been replaced
- **Encryption Status**: Whether database encryption is enabled

## API Reference

The admin interface provides a REST API for integration with other tools:

### Endpoints

- **GET /api/stats**: Returns proxy statistics
- **GET /api/mappings**: Lists all mappings
- **GET /api/patterns**: Lists all patterns
- **POST /api/patterns**: Adds a new pattern

### Authentication

API requests must include the same authentication as the web interface.

## Customizing the Interface

You can customize the admin interface by:

1. **Modifying Templates**: Edit files in the `templates/` directory
2. **Styling Changes**: Edit `static/css/style.css`
3. **Logo Replacement**: Replace `static/images/logo.png`

## Command Line Administration

In addition to the web interface, you can administer the proxy via command line:

```bash
# Export mappings
python -c "from pii_transform import export_mappings; export_mappings('export.json')"

# Import mappings
python -c "from pii_transform import import_mappings; import_mappings('export.json')"

# Clear all mappings
python -c "import sqlite3; conn = sqlite3.connect('data/mapping_store.db'); conn.execute('DELETE FROM mappings'); conn.commit()"
```

## Troubleshooting

Common admin interface issues:

- **Interface Not Loading**: Check if the admin process is running
- **Can't Start/Stop Proxy**: Verify you have permission to manage processes
- **Pattern Not Working**: Test your regex with a regex tester tool
- **Missing Logs**: Check file permissions on the logs directory