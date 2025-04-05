# Testing PrivateAI Proxy with VS Code

This guide provides step-by-step instructions for testing the PrivateAI proxy with Visual Studio Code and its AI extensions (like GitHub Copilot or VS Code's built-in AI features).

## Prerequisites

- Visual Studio Code installed
- GitHub Copilot or another AI extension installed in VS Code
- PrivateAI proxy code set up on your machine

## Setup Steps

### 1. Install Certificates

First, we need to install the PrivateAI certificate authority (CA) certificate:

```bash
python setup_certificates.py
```

This will:
- Generate a new certificate if one doesn't exist
- Install the certificate in your system's trust store
- Configure VS Code to trust the certificate (if possible)

If the automatic installation doesn't work for VS Code, you may need to manually configure it:

```bash
python setup_certificates.py --print-instructions
```

Follow the VS Code-specific instructions from the output.

### 2. Configure System-wide Proxy

Set up system-wide proxy settings:

```bash
python setup_proxy.py --enable
```

### 3. Configure VS Code Proxy Settings

VS Code needs specific proxy settings:

1. Open VS Code Settings (File > Preferences > Settings)
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

### 4. Start the PrivateAI Proxy with Verbose Logging

Start the proxy with enhanced logging to see the interception in action:

```bash
mitmdump -s proxy_intercept.py --set confdir=~/.mitmproxy --set ssl_insecure=true --verbose
```

Or use the provided script with additional logging:

```bash
LOG_LEVEL=DEBUG ./run_proxy.sh
```

## Testing with GitHub Copilot

### 1. Create a Test File with PII

Create a new file in VS Code (e.g., `test.py`) with some code and PII:

```python
# My name is John Smith and my email is john.smith@example.com
# My credit card number is 4111-1111-1111-1111
# My phone number is (555) 123-4567

def greet_user():
    """
    This function greets the user with their name and contact info.
    """
    # TODO: Implement greeting with user's name and contact info
    pass
```

### 2. Trigger Copilot Suggestions

1. Position your cursor at the end of the `pass` line and press Enter
2. Type a comment like `# Implement the function to` and wait for Copilot to suggest code
3. Alternatively, use the Copilot chat panel to ask for help implementing the function

### 3. Check Proxy Logs

Watch the proxy terminal for logs showing:
- Request interception from Copilot
- Format detection (should show "github-copilot" format)
- PII transformation in the request
- Response transformation

### 4. Verify PII Protection

The suggestions from Copilot should:
- Not contain the exact PII (like "John Smith" or the email address)
- Use codenames or placeholders instead of the original PII
- Still be contextually relevant to the task

## Testing with VS Code AI Chat

If you have VS Code's built-in AI chat feature:

1. Open the AI chat panel
2. Ask a question that references the code with PII, like "Can you help me implement the greet_user function in my code?"
3. Check the proxy logs to verify interception and transformation
4. Verify that the AI response doesn't contain the original PII

## Testing with Other VS Code AI Extensions

For other AI extensions (like Tabnine, Codeium, etc.):

1. Install the extension
2. Configure it to use the system proxy (if needed)
3. Use it in a similar way to Copilot, with code containing PII
4. Check the proxy logs for interception and transformation

## Troubleshooting

### Certificate Issues

If VS Code reports SSL/TLS errors:

1. Verify the certificate was installed in your system's trust store
2. Check VS Code's proxy settings again
3. Try restarting VS Code after certificate installation
4. For persistent issues, try manually importing the certificate

### Connection Issues

If VS Code can't connect to AI services:

1. Verify that the proxy is running
2. Check if your proxy settings are correctly configured in VS Code
3. Test if other applications can connect through the proxy
4. Check if the AI service is accessible directly (without proxy)

### Format Detection Issues

If the proxy isn't detecting VS Code's AI requests:

1. Enable debug logging:
   ```bash
   export LOG_LEVEL=DEBUG
   ```
2. Check the logs for format detection results
3. Try using the AI feature in different ways (suggestions, chat, etc.)
4. If a specific format isn't being detected, you may need to update the format detector

## Advanced Testing

### Testing with Different AI Models

If your VS Code AI extension allows selecting different models:

1. Try different models to see if the proxy handles them correctly
2. Check if the format detection works for all models

### Testing with Custom AI Endpoints

If your VS Code extension allows configuring custom AI endpoints:

1. Configure a custom endpoint
2. Check if the proxy's heuristic detection identifies it correctly
3. If not, add the domain to the `ADDITIONAL_DOMAINS` environment variable

### Testing Performance Impact

To measure the performance impact of the proxy:

1. Time how long it takes to get AI suggestions with and without the proxy
2. Monitor CPU and memory usage of the proxy process
3. Check if there's any noticeable lag in the VS Code UI

## Conclusion

By following this guide, you should be able to verify that the PrivateAI proxy correctly intercepts and transforms AI requests from VS Code. If you encounter any issues, check the troubleshooting section or refer to the main documentation.