# PrivateAI Integration with IDE-based AI Assistants

This guide explains how to configure PrivateAI to work with popular IDE-based AI assistants like GitHub Copilot, Cursor, VS Code AI, and JetBrains AI.

## Overview

PrivateAI now features enhanced capabilities to automatically detect, intercept, and apply PII protection to traffic from IDE-based AI assistants, without the need for manual endpoint configuration in most cases. The system uses a combination of:

1. Domain-based detection
2. Path pattern matching 
3. Heuristic analysis of request content
4. HTTP header inspection

This allows PrivateAI to identify and protect AI traffic even when the endpoint is not in our known list.

## Setup Steps

### 1. Install Certificates

For IDE-based AI assistants to work with our MITM proxy, you must install the PrivateAI certificate authority (CA) certificate. Run the following command:

```bash
python setup_certificates.py
```

This automatically:
- Generates a new certificate if one doesn't exist
- Installs the certificate in your operating system's trust store
- Configures common IDEs to trust the certificate

If automatic installation fails, you can run:

```bash
python setup_certificates.py --print-instructions
```

This will print instructions for manual certificate installation.

### 2. Configure System-wide Proxy

Run the proxy configuration script to set up system-wide proxy settings:

```bash
python setup_proxy.py --enable
```

This configures your system to route all traffic through the PrivateAI proxy.

To disable the proxy settings:

```bash
python setup_proxy.py --disable
```

### 3. Configure IDE-specific Proxy Settings

In addition to system-wide proxy settings, it's often necessary to configure the proxy settings directly in your IDE:

#### Visual Studio Code

1. Open VSCode Settings (File > Preferences > Settings)
2. Search for "proxy"
3. Set "Http: Proxy" to "http://localhost:8080"
4. Set "Http: Proxy Strict SSL" to false

Alternatively, add to your `settings.json`:

```json
{
  "http.proxy": "http://localhost:8080",
  "http.proxyStrictSSL": false
}
```

#### JetBrains IDEs (IntelliJ, PyCharm, WebStorm, etc.)

1. Go to Settings/Preferences > Appearance & Behavior > System Settings > HTTP Proxy
2. Select "Manual proxy configuration"
3. Set "Host name" to "localhost"
4. Set "Port number" to "8080"
5. Check "No proxy for" and add "localhost,127.0.0.1"
6. Under "Check connection" enter any URL to verify the proxy is working

#### Cursor

1. Open Settings (File > Preferences > Settings)
2. Search for "proxy"
3. Set "Http: Proxy" to "http://localhost:8080"
4. Set "Http: Proxy Strict SSL" to false

### 4. Start the PrivateAI Proxy

Start the proxy with enhanced detection capabilities:

```bash
./run_proxy.sh
```

Or directly with Python:

```bash
mitmdump -s proxy_intercept.py --set confdir=~/.mitmproxy --set ssl_insecure=true
```

## Testing Your Setup

To verify that your IDE's AI assistant is being properly intercepted:

1. Start the proxy with verbose logging:
   ```bash
   mitmdump -s proxy_intercept.py --set confdir=~/.mitmproxy --set ssl_insecure=true --verbose
   ```

2. Open your IDE and trigger an AI completion request
   - In VS Code with Copilot: Type a code comment and wait for suggestions
   - In Cursor: Use the AI chat feature
   - In JetBrains IDEs: Trigger an AI completion

3. Check the proxy logs for messages indicating interception and transformation

## Troubleshooting

### Certificate Issues

If your IDE reports SSL/TLS errors:

1. Verify the certificate was installed in your system's trust store
2. Check IDE-specific certificate settings
3. Try restarting your IDE after certificate installation
4. For persistent issues, try manually importing the certificate in your IDE

### Connection Issues

If your IDE can't connect to AI services:

1. Verify that the proxy is running
2. Check if your proxy settings are correctly configured in the IDE
3. Test if other applications can connect through the proxy
4. Check if the AI service is accessible directly (without proxy)

### Format Detection Issues

If you're experiencing issues with specific AI assistants:

1. Enable debug logging by setting the environment variable:
   ```bash
   export LOG_LEVEL=DEBUG
   ```

2. Check the logs for format detection results
   
3. If a specific format isn't being detected, create a GitHub issue with:
   - IDE and version information
   - AI assistant name and version
   - Sample request (with sensitive information removed)

## Format Adapters

PrivateAI now supports the following IDE-based AI assistant formats:

| Assistant | Format Name | Description |
|-----------|-------------|-------------|
| GitHub Copilot | github-copilot | Code completions in VS Code, Neovim, etc. |
| Cursor AI | cursor | AI chat and completions in Cursor editor |
| VS Code AI | vscode | VS Code's built-in AI features |
| JetBrains AI | jetbrains | AI features in IntelliJ, PyCharm, etc. |
| Codeium | codeium | Code completions by Codeium |
| TabNine | tabnine | TabNine code completions |
| Sourcegraph Cody | sourcegraph-cody | Sourcegraph's Cody AI assistant |
| AWS CodeWhisperer | amazon-codewhisperer | Amazon's code completion tool |
| Replit | replit | Replit's AI coding features |
| Kite | kite | Kite programming assistant |

If your preferred IDE AI assistant isn't listed, please open an issue on our GitHub repository.

## Advanced Configuration

### Custom Domain Configuration

To add additional domains to be intercepted:

```bash
export ADDITIONAL_DOMAINS="mydomain1.com,mydomain2.com"
```

To exclude specific domains from interception:

```bash
export EXCLUDED_DOMAINS="ignoredomain.com,skippeddomain.com"
```

### Custom AI Endpoint Patterns

To add additional AI endpoint path patterns:

1. Open `proxy_intercept.py` 
2. Add your patterns to the `AI_ENDPOINT_PATTERNS` list

### Custom Heuristic Keywords

To improve detection of AI requests:

1. Open `proxy_intercept.py` 
2. Add relevant keywords to the `AI_REQUEST_KEYWORDS` list

## Adapting to New AI Formats

If you want to add support for a new IDE AI assistant format:

1. Identify the format's request and response structure
2. Add a detector method in `ai_format_detector.py`
3. Add request adapters in `ai_format_request_adapters.py`
4. Add response adapters in `ai_format_response_adapters.py`
5. Update the tests in `test_ai_format_adapter.py`

## Security Considerations

When using PrivateAI with IDE-based AI assistants:

1. **Certificate Trust**: Installing the MITM certificate in your system trust store is required but introduces security considerations. Our certificate is only used for PII protection.

2. **Proxy Flow**: All traffic from your IDE will flow through the PrivateAI proxy. The proxy only transforms AI-related traffic and passes through all other traffic unchanged.

3. **SSL Validation**: Some IDEs require disabling strict SSL validation to work with MITM proxies. This is necessary for the proxy to work but should be limited to the specific IDE.

## Performance Considerations

The additional format detection and adaptation may slightly impact performance. To optimize performance:

1. Use domain-based filtering when possible by setting `AI_DOMAINS` environment variable
2. Consider disabling heuristic detection if not needed
3. For high-traffic environments, increase the proxy's resources

## Conclusion

By following this guide, you should have a working setup where your IDE-based AI assistants automatically route through PrivateAI, ensuring that sensitive information is protected before being sent to AI services.

For further assistance, please open an issue on our GitHub repository.