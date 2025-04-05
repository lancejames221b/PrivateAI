# Proxy Configuration: Setting the Stage 🕵️

This guide explains how to configure and customize the AI Privacy Proxy to meet your specific needs. Let's set the stage for a secure operation.

## Basic Configuration

### Environment Variables

The proxy can be configured using environment variables in a `.env` file:

```bash
# Core settings
PROXY_PORT=8080
ADMIN_PORT=5001
FLASK_ENV=production
LOG_LEVEL=INFO

# Security settings
SECRET_KEY=your-secure-key-here
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secure-password
ENCRYPT_DATABASE=true

# Feature flags
USE_PRESIDIO=true
BLOCK_ALL_DOMAINS=false
DISABLE_TRANSFORMERS=false
```

Key settings include:

-   **PROXY_PORT**: The port for the proxy service (default: 8080)
-   **ADMIN_PORT**: The port for the admin interface (default: 5001)
-   **FLASK_ENV**: Environment for Flask application (development/production)
-   **LOG_LEVEL**: Detail level for logs (DEBUG, INFO, WARNING, ERROR)
-   **SECRET_KEY**: Secret key for the Flask admin interface
-   **USE_PRESIDIO**: Whether to use Microsoft Presidio for PII detection
-   **BLOCK_ALL_DOMAINS**: Whether to anonymize all domain names
-   **DISABLE_TRANSFORMERS**: Whether to disable transformers
-   **DOCKER_CONTAINER**: Flag to indicate if running in a Docker container (default: true)
-   **PROXY_HOST**: Hostname for the proxy service (default: proxy)
-   **PYTHONUNBUFFERED**: Ensures that the Python output is not buffered
-   **NAME**: A test variable (default: World)
-   **BASIC_AUTH_USERNAME**: Username for admin interface authentication
-   **BASIC_AUTH_PASSWORD**: Password for admin interface authentication

### Configuration Files

Configuration can also be done through files:

- **`data/custom_patterns.json`**: Custom detection patterns
- **`data/domain_blocklist.txt`**: List of domains to anonymize
- **`data/codename_mappings.json`**: Organization and domain codename mappings

## HTTPS Certificates

For the proxy to intercept HTTPS traffic, clients need to trust its certificate:

### Certificate Generation

1.  Run the certificate setup script:
    ```bash
    ./setup_certificates.sh
    ```
2.  This creates:
    -   A Certificate Authority (CA) certificate
    -   A private key
3.  These are stored in `$HOME/.mitmproxy/` directory

### Certificate Installation

#### macOS

1.  Run the helper script:
    ```bash
    ./setup_certificates.sh
    ```
2.  Or manually:
    ```bash
    sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain "$HOME/.mitmproxy/mitmproxy-ca-cert.pem"
    ```

#### Windows

1.  Copy the certificate:
    ```
    copy %USERPROFILE%\.mitmproxy\mitmproxy-ca-cert.p12 mitm.p12
    ```
2.  Double-click mitm.p12, follow the wizard:
    -   Store location: Local Machine
    -   Place all certificates in "Trusted Root Certification Authorities"

#### Linux

1.  Copy to system certificates:
    ```bash
    sudo cp ~/.mitmproxy/mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy.crt
    sudo update-ca-certificates
    ```

### Certificate Verification

To verify certificate installation:

```bash
# Test connection through proxy
curl -x http://localhost:8080 https://example.com
```

If successful, you should see the example.com page without SSL errors.

## Domain Configuration

### Domain Blocklisting

The system can be configured to anonymize specific domains:

1. **Via Admin Interface**:
   - Navigate to the Domains page
   - Add domains to the blocklist

2. **Via Configuration File**:
   - Edit `data/domain_blocklist.txt`
   - Add one domain per line

Example file:
```
sentinelone.net
sentinelone.com
example-secret-domain.com
internal-system.company.net
```

### Block All Domains

For maximum privacy, you can anonymize all domains:

1. **Via Admin Interface**:
   - Toggle "Block All Domains" setting

2. **Via Environment Variable**:
   ```bash
   BLOCK_ALL_DOMAINS=true
   ```

This will replace all domain names with anonymous placeholders regardless of the blocklist.

## Pattern Configuration

### Custom Detection Patterns

Define custom patterns to detect organization-specific information:

1. **Via Admin Interface**:
   - Navigate to the Patterns page
   - Fill the pattern form and save

2. **Via JSON File**:
   - Edit `data/custom_patterns.json`

Example pattern:
```json
{
  "PROJECT_PHOENIX": {
    "name": "PROJECT_PHOENIX",
    "entity_type": "INTERNAL_PROJECT_NAME",
    "pattern": "\\b(Phoenix|Project\\s+Phoenix)\\b",
    "description": "Detects references to our internal Project Phoenix",
    "is_active": true,
    "priority": "1"
  }
}
```

### Pattern Types

Common pattern types to consider adding:

- **Internal Project Names**: Codenames and project identifiers
- **Internal Domains**: Company-specific domains and subdomains
- **Custom Formats**: Organization-specific data formats
- **Product Names**: Names of unreleased or sensitive products
- **Client Identifiers**: Special codes or IDs for clients

## Detection Engine Configuration

### Microsoft Presidio

Presidio enhances PII detection capabilities:

1. **Enable/Disable**:
   ```bash
   USE_PRESIDIO=true
   ```

2. **Custom Presidio Recognizers**:
   Add custom recognizers in `transformers_recognizer.py`

### Transformers Models

Control NER model behavior:

1. **Model Selection**:
   ```bash
   MODEL_NAME=dslim/bert-base-NER
   ```

2. **Disable Transformers**:
   ```bash
   DISABLE_TRANSFORMERS=true
   ```

## Security Configuration

### Admin Authentication

Secure the admin interface:

1. **Enable Basic Auth**:
   ```bash
   # In .env file
   BASIC_AUTH_USERNAME=admin
   BASIC_AUTH_PASSWORD=your-secure-password
   ```

2. **Force Authentication**:
   ```python
   # In app.py
   app.config['BASIC_AUTH_FORCE'] = True
   ```

### Database Encryption

Protect stored mappings:

1. **Enable Encryption**:
   ```bash
   ENCRYPT_DATABASE=true
   ```

2. **Custom Encryption Key**:
   ```bash
   # Generate a secure key
   ENCRYPTION_KEY=$(openssl rand -base64 32)
   # Add to .env
   ENCRYPTION_KEY=$ENCRYPTION_KEY
   ```

## Advanced Proxy Configuration

### Proxy Modes

The proxy supports different interception modes:

1. **Regular Proxy Mode (default)**:
   ```bash
   # In run_proxy.sh
   python ai_proxy.py
   ```

2. **Transparent Mode**:
   ```bash
   # In run_proxy.sh
   python ai_proxy.py --mode transparent
   ```

3. **Reverse Proxy Mode**:
   ```bash
   # In run_proxy.sh
   python ai_proxy.py --mode reverse:https://api.openai.com
   ```

### Request Filtering

Control which requests are processed:

1. **URL Patterns**:
   ```bash
   # In .env file
   PROCESS_URLS=api.openai.com,api.anthropic.com
   ```

2. **Content Types**:
   ```bash
   # In .env file
   PROCESS_CONTENT_TYPES=application/json,text/plain
   ```

## Logging Configuration

### Log Levels

Adjust verbosity of logs:

```bash
# In .env file
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

### Log Rotation

Configure log file management:

```python
# In app.py or ai_proxy.py
handler = RotatingFileHandler(
    'logs/proxy.log',
    maxBytes=10_000_000,  # 10MB
    backupCount=5
)
```

### Log Formatting

Customize log output:

```python
# In app.py or ai_proxy.py
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
```

## Docker-Specific Configuration

When running in Docker, additional configuration options are available:

### Environment Variables

Pass variables to the container:

```bash
# In docker-compose.yml
environment:
  - FLASK_ENV=production
  - SECRET_KEY=${SECRET_KEY:-default_dev_key}
  - USE_PRESIDIO=true
```

### Volume Mounts

Configure persistent storage:

```yaml
# In docker-compose.yml
volumes:
  - ./data:/app/data
  - ./logs:/app/logs
  - ./static:/app/static
  - ./templates:/app/templates
  - ~/.mitmproxy:/root/.mitmproxy
```

### Port Mapping

Change exposed ports:

```yaml
# In docker-compose.yml
ports:
  - "5001:5000"  # Map container port 5000 to host port 5001
  - "8080:8080"  # Map container port 8080 to host port 8080
```

## Application Integration

### Configuring Clients

Examples of how to configure different clients to use the proxy:

#### Python Requests

```python
import requests

proxies = {
    'http': 'http://localhost:8080',
    'https': 'http://localhost:8080',
}

response = requests.get(
    'https://api.example.com',
    proxies=proxies,
    verify=False  # Disable SSL verification
)
```

#### Node.js

```javascript
const axios = require('axios');
const https = require('https');

const agent = new https.Agent({  
  rejectUnauthorized: false  // Disable SSL verification
});

axios.get('https://api.example.com', {
  proxy: {
    host: 'localhost',
    port: 8080
  },
  httpsAgent: agent
})
.then(response => console.log(response.data));
```

#### curl

```bash
curl -x http://localhost:8080 https://api.example.com --insecure
```

## System-wide Proxy

To route all traffic through the proxy:

### macOS

```bash
# Set system proxy
networksetup -setwebproxy Wi-Fi localhost 8080
networksetup -setsecurewebproxy Wi-Fi localhost 8080

# Verify proxy settings
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
```

### Windows

```powershell
# Set system proxy
netsh winhttp set proxy localhost:8080

# Reset when done
netsh winhttp reset proxy
```

### Linux

```bash
# Set environment variables
export http_proxy=http://localhost:8080
export https_proxy=http://localhost:8080
```