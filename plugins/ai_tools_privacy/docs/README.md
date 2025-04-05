# GitHub Copilot Privacy Plugin

This plugin provides privacy protection for GitHub Copilot by intercepting and transforming sensitive information in code before it's sent to GitHub Copilot.

## Overview

GitHub Copilot is a powerful AI coding assistant, but it sends your code to GitHub's servers for processing. This can potentially expose sensitive information like:

- API keys and credentials
- Personal information
- Internal company information
- Database connection strings
- IP addresses and server paths

This plugin provides privacy protection by intercepting the traffic between VS Code and GitHub Copilot, detecting sensitive information, and transforming it before it reaches GitHub's servers.

## How It Works

The plugin works by:

1. **Intercepting Traffic**: Using mitmproxy to intercept HTTPS traffic between VS Code and GitHub Copilot
2. **Detecting PII**: Using transformer models and pattern matching to detect sensitive information
3. **Transforming PII**: Replacing sensitive information with innocuous placeholders
4. **Preserving Functionality**: Ensuring GitHub Copilot still works effectively with the transformed data
5. **Analyzing Results**: Providing metrics on what was protected

## Components

The plugin consists of three main scripts:

1. **launch_vscode_with_privacy.sh**: Launches VS Code with the Private AI proxy for GitHub Copilot privacy protection
2. **analyze_privacy.sh**: Analyzes captured traffic and provides privacy metrics
3. **test_privacy.sh**: Creates test files with known PII to verify the privacy protection

## Prerequisites

- Private AI installed and configured
- mitmproxy installed (`brew install mitmproxy` on macOS)
- VS Code with GitHub Copilot extension installed
- jq installed (`brew install jq` on macOS)

## Setup Instructions

### 1. Make Scripts Executable

```bash
chmod +x plugins/copilot_privacy/scripts/*.sh
```

### 2. Create Test Files (Optional)

If you want to test the privacy protection with known PII:

```bash
cd /path/to/private-ai
./plugins/copilot_privacy/scripts/test_privacy.sh
```

This will create test files with known PII in the `privacy_test` directory.

### 3. Launch VS Code with Privacy Protection

```bash
cd /path/to/private-ai
./plugins/copilot_privacy/scripts/launch_vscode_with_privacy.sh
```

This will:
- Install the mitmproxy certificate if needed
- Configure VS Code to use the proxy
- Start the Private AI proxy
- Launch VS Code

### 4. Use GitHub Copilot as Normal

Use GitHub Copilot as you normally would. The Private AI proxy will automatically detect and transform sensitive information before it reaches GitHub's servers.

### 5. Analyze Privacy Protection

After using GitHub Copilot, you can analyze the captured traffic and see what was protected:

```bash
cd /path/to/private-ai
./plugins/copilot_privacy/scripts/analyze_privacy.sh
```

This will generate reports in the `proxy_logs/analysis` directory with:
- Traffic summary
- Privacy metrics
- PII detection and transformation statistics

## Technical Details

### Plugin Architecture

This plugin extends the base `CopilotPlugin` class to add enhanced privacy protection features:

- More comprehensive PII detection
- Detailed privacy metrics
- Improved certificate management
- Better error handling

### Certificate Management

The plugin handles certificate management by:
- Using mitmproxy's certificate authority (CA) certificate
- Installing it in the system trust store
- Configuring VS Code to trust the certificate
- Setting the `NODE_EXTRA_CA_CERTS` environment variable

### Format Adaptation

Private AI detects and adapts different AI service formats:
- GitHub Copilot uses a JSONRPC format with specific methods like `getCompletions`
- The `AIFormatDetector` class detects this format based on request structure and headers
- The `AIRequestAdapters` class converts it to a standard OpenAI format for processing
- The `AIResponseAdapters` class converts responses back to the GitHub Copilot format

### PII Protection

Private AI uses multiple methods to detect and transform PII:
- Transformer models for Named Entity Recognition (NER)
- Pattern matching with regular expressions
- Custom recognizers for specific data types
- Consistent replacement of detected entities

## Troubleshooting

### Certificate Issues

If you see certificate errors:
1. Check that the mitmproxy certificate is installed in your system trust store
2. Verify that VS Code is configured to use the certificate
3. Try restarting VS Code after certificate installation

### Proxy Connection Issues

If VS Code can't connect to GitHub Copilot:
1. Verify that the proxy is running
2. Check VS Code's proxy settings
3. Ensure the `NODE_EXTRA_CA_CERTS` environment variable is set correctly

### Performance Issues

If you experience performance issues:
1. Check the proxy logs for errors
2. Consider disabling some PII detection features if needed
3. Increase the resources allocated to the proxy

## Privacy Considerations

While this plugin helps protect sensitive information, it's important to note:
- It may not catch all sensitive information
- It may transform some non-sensitive information
- It adds a layer of processing that may impact performance
- It requires trusting the Private AI proxy with your code

## Conclusion

By using the GitHub Copilot Privacy Plugin, you can use GitHub Copilot more securely, protecting sensitive information while still benefiting from its AI-powered code suggestions.