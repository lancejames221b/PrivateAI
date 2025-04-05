# IDE AI Integration

Private AI 🕵️ now provides comprehensive support for IDE-based AI assistants and coding tools, ensuring privacy protection for developers working with sensitive codebases.

*Authored by Lance James @ Unit 221B*

## Supported AI Coding Assistants

| AI System | Integration Type | Privacy Support |
|-----------|------------------|----------------|
| GitHub Copilot | Full protocol support | Complete |
| Cursor AI | Native protocol support | Complete |
| VS Code AI Extensions | API format handling | Complete |
| JetBrains AI Assistant | API format handling | Complete |
| Amazon CodeWhisperer | API endpoint handling | Complete |
| Codeium | API format handling | Complete |
| TabNine | API format handling | Complete |
| Sourcegraph Cody | API format handling | Complete |
| Replit AI | API format handling | Complete |

## How It Works

The AI Privacy Proxy provides transparent integration for IDE AI tools by:

1. **Detecting formats automatically**: The proxy analyzes request structures and headers to identify the AI system
2. **Converting formats**: All requests are converted to a standard format for privacy processing
3. **Protecting sensitive data**: Private code, comments, and context are protected according to privacy rules
4. **Restoring format**: Responses are converted back to the original format expected by the AI assistant
5. **Maintaining context**: Relationships between code elements are preserved despite redaction

This ensures developers can safely use AI coding assistants without exposing sensitive data.

## Setup for IDE Integration

### GitHub Copilot

1. Configure your proxy settings in VS Code:
   ```json
   "http.proxy": "http://localhost:8080",
   "http.proxyStrictSSL": false
   ```

2. Make sure GitHub Copilot is installed and authenticated.

3. Start using Copilot as normal - the proxy will handle privacy protection automatically.

### Cursor AI

1. Set environment variables before launching Cursor:
   ```bash
   # For macOS/Linux
   export HTTP_PROXY=http://localhost:8080
   export HTTPS_PROXY=http://localhost:8080
   
   # For Windows PowerShell
   $env:HTTP_PROXY = "http://localhost:8080"
   $env:HTTPS_PROXY = "http://localhost:8080"
   
   # Then launch Cursor
   open -a Cursor
   ```

2. Use Cursor AI features normally - the proxy will handle privacy protection.

### VS Code AI Extensions

1. Configure VS Code proxy settings:
   ```json
   "http.proxy": "http://localhost:8080",
   "http.proxyStrictSSL": false
   ```

2. Install and configure your AI extensions as normal.

### JetBrains IDEs

1. Go to Settings → Appearance & Behavior → System Settings → HTTP Proxy
2. Select "Manual proxy configuration"
3. Set:
   - Host: localhost
   - Port: 8080
   - No proxy for: (leave as needed)
4. Uncheck "Proxy authentication"

### Other AI Coding Tools

Most AI coding tools respect the system proxy settings. Set your system proxy to:
- Host: localhost
- Port: 8080

## Format Adapters

The proxy includes intelligent format adapters for:

- **JSONRPC Protocol**: Used by GitHub Copilot (agent.js)
- **OpenAI Protocol**: Used by many AI systems (chat completions API)
- **Cursor AI Protocol**: Cursor's specialized AI format
- **Anthropic Protocol**: Claude-based coding assistants
- **VS Code Extension Protocol**: VS Code AI extension format
- **JetBrains Protocol**: JetBrains AI assistant format

These adapters ensure the proxy can handle any future AI system formats by converting to a standard internal format for processing.

## Testing IDE Integration

To verify your IDE AI integration is working with privacy protection:

1. Check the proxy logs for format detection messages:
   ```
   tail -f proxy.log | grep "format"
   ```

2. Look for messages like:
   ```
   Adapted request format from github-copilot to OpenAI format
   ```

3. Test with code containing sensitive data. The AI should not reflect this data back in completions.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| IDE fails to connect to AI | Verify proxy is running and correctly configured |
| No privacy protection visible | Check logs for format detection; ensure sensitive patterns are defined |
| Certificate errors | Import proxy certificates using `setup_certificates.sh` |
| AI assistant not responding | Check proxy logs for format conversion errors |
| Response format incorrect | Update to latest version for format compatibility fixes |

## Custom IDE Integration

For custom IDE plugins or AI tools not officially supported:

1. Add the domain to the `AI_API_DOMAINS` list in `ai_proxy.py`
2. Add format detection to `detect_and_adapt_ai_format` in `utils.py`
3. Add response handling to `adapt_ai_response` in `utils.py`

## Privacy Considerations for Code

When using AI coding assistants, be aware of the following privacy considerations:

1. **Comments may contain sensitive data**: Ensure comment scanning is enabled
2. **Import statements can reveal internal dependencies**: Pattern detection for internal paths
3. **Function names may reveal business logic**: Consider enabling code identifier pattern matching
4. **Documentation strings often contain company data**: Enable thorough docstring scanning
5. **Test data in code**: Watch for hardcoded test values with sensitive data

The AI Privacy Proxy aims to protect all these aspects, but it's good practice to review privacy settings specifically for code contexts. 