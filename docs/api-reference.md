# API Reference: Unveiling the Secrets 🕵️

The Private AI Proxy offers a REST API via its admin interface (`app.py`) for configuration, monitoring, and management.

## REST API (via Admin Interface - `app.py`)

The admin interface (typically running on port 7070) provides the following REST API endpoints.

### Authentication

All API endpoints use Basic Authentication unless explicitly exempted (like `/test_proxy_connection`). Configure the username and password in your `.env` file using `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD`.

```bash
# Example using curl with basic auth (replace with actual credentials)
curl -u admin:change_this_password http://localhost:7070/api/stats
```

### API Endpoints

#### Proxy Status & Control

**POST /start_proxy**

Attempts to start the `mitmproxy` process using the configured script (`scripts/run/run_proxy.sh` or similar). Requires form submission with CSRF token if accessed via browser, or standard POST if via API client.

*   **Success**: Redirects to `/one-page` with a success flash message.
*   **Failure**: Redirects to `/one-page` with an error flash message.

**POST /stop_proxy**

Attempts to stop any running `mitmproxy` or related processes. Requires form submission with CSRF token if accessed via browser, or standard POST if via API client.

*   **Success**: Redirects to `/one-page` with a success flash message.
*   **Failure**: Redirects to `/one-page` with an error flash message.

**POST /test_proxy_connection**

Tests connectivity to the proxy service. CSRF Exempt.

*Request Body (JSON):*
```json
{
  "proxy_port": 8080
}
```
*   **Success (200 OK):**
    ```json
    {
      "success": true,
      "message": "Proxy connection successful on port 8080. The proxy is operational."
    }
    ```
*   **Failure (200 OK / 500 Internal Server Error):**
    ```json
    {
      "success": false,
      "message": "Proxy is not running on 127.0.0.1:8080. Please start the proxy service first."
      // or other error messages
    }
    ```

**GET /download_cert**

Downloads the `mitmproxy-ca-cert.pem` file required for clients to trust the proxy for HTTPS inspection. The server attempts to locate the file in `~/.mitmproxy/` or `data/` and may attempt to generate it if missing.

*   **Success (200 OK):** Returns the certificate file as an attachment.
*   **Failure (404 Not Found):** Certificate file could not be found or generated.
*   **Failure (500 Internal Server Error):** Server error during file serving.

**POST /install_cert** (DEPRECATED)

*Deprecated route for attempting automatic certificate installation.* This method is unreliable due to `sudo` requirements and timeouts. Use the `/download_cert` route and manual installation instead.

*   **Response (410 Gone):**
    ```json
    {
      "success": false,
      "message": "Deprecated: Certificate installation via script is unreliable.",
      "details": "Please use the Download Certificate button and follow manual instructions."
    }
    ```

#### Statistics

**GET /api/stats**

Retrieve system statistics, including mapping counts and proxy status.

*   **Success (200 OK):**
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
*   **Failure (500 Internal Server Error):** If database or other errors occur.

#### Configuration Data (Patterns, Domains, etc.)

*(These endpoints interact with JSON files in the `data/` directory or the `.env` file)*

**GET /api/patterns**

Retrieve all custom detection patterns from `data/custom_patterns.json`.

*   **Success (200 OK):**
    ```json
    {
      "patterns": {
        "API_KEY": {
          "name": "API_KEY",
          "entity_type": "API_KEY",
          "pattern": "(sk|pk)_(test|live|...)...",
          // ... other fields
        }
        // ... other patterns
      }
    }
    ```

**POST /add_pattern**

Adds a new pattern to `data/custom_patterns.json`. Requires form submission with CSRF token.

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

**GET /delete_pattern/<name>**

Deletes a pattern specified by `<name>` from `data/custom_patterns.json`.

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

**GET /toggle_pattern/<name>**

Toggles the `is_active` status of a pattern specified by `<name>` in `data/custom_patterns.json`.

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

**POST /add_domain**

Adds a domain to the blocklist (`data/domain_blocklist.txt`). Requires form submission with CSRF token.

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

**GET /remove_domain/<domain>**

Removes a `<domain>` from the blocklist (`data/domain_blocklist.txt`).

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

**POST /toggle_block_all_domains**

Toggles the `BLOCK_ALL_DOMAINS` setting in the `.env` file. Requires form submission with CSRF token.

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

**GET /api/settings**

Retrieves current configuration settings relevant to the UI (like domain blocklist, block_all status, test URLs).

*   **Success (200 OK):**
    ```json
    {
      "domain_blocklist": ["domain1.com", "domain2.net"],
      "block_all_domains": false,
      "custom_patterns": { /* ... patterns ... */ },
      "ai_test_urls": [ /* ... test urls ... */ ]
    }
    ```
*   **Failure (500 Internal Server Error):** If reading configuration fails.

#### Mappings (Database Interaction)

*(These endpoints interact with `data/mapping_store.db`)*

**GET /api/mappings**

Retrieve all current PII mappings stored in the database.

*   **Success (200 OK):**
    ```json
    {
      "mappings": [
        {
          "original": "SentinelOne",
          "replacement": "CyberGuardian",
          "entity_type": "ORGANIZATION",
          "created_at": "...",
          "last_used": "..."
        },
        // ... other mappings
      ]
    }
    ```

**GET /delete_mapping/<original>**

Delete a specific mapping identified by its `<original>` value from the database.

*   **Success**: Redirects to `/one-page` with success flash message.
*   **Failure**: Redirects to `/one-page` with error flash message.

## Programmatic API (Core Library - `PrivateAI/`)

*(This section would detail how to use modules like `pii_transform.py` directly in Python code if intended for library use. Currently, the primary interaction is via the proxy.)*

**Example (Conceptual - If library usage is supported):**

```python
# This is a conceptual example; actual implementation may vary.
# from PrivateAI.pii_transform import transform_text, initialize_db

# initialize_db()
# text = "Contact support@example.com about Project Phoenix."
# transformed_text, mappings = transform_text(text)
# print(transformed_text)
# print(mappings)
```

*Note: Focus on documenting the REST API provided by `app.py` as that's the primary external interface.*

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