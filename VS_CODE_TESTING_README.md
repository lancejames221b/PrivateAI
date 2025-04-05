# Testing PrivateAI with VS Code

This document provides an overview of how to test the PrivateAI proxy with Visual Studio Code and its AI extensions.

## Components Implemented

We've implemented several components to facilitate testing with VS Code:

1. **Enhanced AI Format Detection and Adaptation**:
   - `ai_format_adapter.py`: Main adapter class
   - `ai_format_detector.py`: Format detection module
   - `ai_format_request_adapters.py`: Request format adapters
   - `ai_format_response_adapters.py`: Response format adapters

2. **Updated Proxy Interceptor**:
   - Enhanced `proxy_intercept.py` with heuristic-based detection

3. **Certificate and Proxy Management**:
   - `setup_certificates.py`: Certificate generation and installation
   - `setup_proxy.py`: System-wide proxy configuration

4. **Testing Tools**:
   - `test_vscode_ai_proxy.py`: Automated test script
   - `test_with_vscode.sh`: One-click testing script

5. **Documentation**:
   - `docs/vscode_testing_guide.md`: Detailed testing guide
   - `docs/ide-ai-integration.md`: General IDE integration guide

## Quick Start

The easiest way to test the PrivateAI proxy with VS Code is to use the provided shell script:

```bash
./test_with_vscode.sh
```

This script will:
1. Install the necessary certificates
2. Configure VS Code settings
3. Set up system-wide proxy
4. Start the proxy
5. Run automated tests
6. Provide instructions for manual testing

## Manual Testing Steps

If you prefer to test manually, follow these steps:

### 1. Install Certificates

```bash
python setup_certificates.py
```

### 2. Configure System Proxy

```bash
python setup_proxy.py --enable
```

### 3. Configure VS Code

Add these settings to your VS Code `settings.json`:

```json
{
  "http.proxy": "http://localhost:8080",
  "http.proxyStrictSSL": false
}
```

### 4. Start the Proxy

```bash
LOG_LEVEL=DEBUG mitmdump -s proxy_intercept.py --set confdir=~/.mitmproxy --set ssl_insecure=true --verbose
```

### 5. Test with VS Code

1. Open VS Code
2. Create a new file with some PII (names, emails, etc.)
3. Use GitHub Copilot or another AI extension
4. Check the proxy logs to verify interception and transformation

## Automated Testing

You can run automated tests that simulate VS Code AI requests:

```bash
python test_vscode_ai_proxy.py --proxy http://localhost:8080
```

This script simulates requests from:
- VS Code AI
- GitHub Copilot
- Cursor AI
- OpenAI API (requires API key)

## Supported VS Code AI Extensions

The implementation supports:

- GitHub Copilot
- VS Code's built-in AI features
- Cursor AI
- Codeium
- TabNine
- Sourcegraph Cody
- AWS CodeWhisperer
- Replit AI
- Kite

## Troubleshooting

If you encounter issues:

1. **Certificate Problems**:
   - Run `python setup_certificates.py --print-instructions` for manual installation instructions
   - Restart VS Code after certificate installation

2. **Connection Issues**:
   - Verify the proxy is running
   - Check VS Code proxy settings
   - Try disabling and re-enabling the proxy

3. **Format Detection Issues**:
   - Enable debug logging with `LOG_LEVEL=DEBUG`
   - Check the proxy logs for format detection results

## Cleanup

When you're done testing:

1. Stop the proxy (Ctrl+C if running in foreground)
2. Disable the system proxy:
   ```bash
   python setup_proxy.py --disable
   ```

## Additional Resources

For more detailed information, refer to:

- `docs/vscode_testing_guide.md`: Comprehensive testing guide
- `docs/ide-ai-integration.md`: General IDE integration documentation
- `ide_ai_proxy_research_summary.md`: Research findings and implementation details

## Conclusion

The implemented solution provides a robust way to test PrivateAI's PII protection capabilities with VS Code and its AI extensions. The modular design allows for easy extension to support new AI formats as they emerge.