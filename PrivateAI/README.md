# Private AI 🕵️

A privacy-preserving middleware for AI model interactions that protects sensitive information - your AI detective on the case.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

*Created by Lance James @ Unit 221B*

## Overview

Private AI is a middleware system that acts as a privacy layer between your applications and AI APIs. It detects and transforms sensitive information before sending requests to AI models, and then restores the original data in the responses. Like a detective (hence the pun on "Private Eye"), it investigates and protects your sensitive information.

**Key Benefits:**
- Protect personal, financial, and proprietary information in AI interactions
- Maintain data privacy compliance while leveraging AI capabilities
- Add a privacy layer to existing AI integrations with minimal code changes

## Quick Start

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/private-ai.git
cd private-ai
pip install -r requirements.txt
```

### 2. Start the Privacy Proxy

```bash
./start_privacy_proxy.sh
```

### 3. Test with a Sample AI Call

```bash
./real_ai_demo.py
```

## Documentation

- [Project Summary](PROJECT_SUMMARY.md) - High-level overview of the system
- [API Integration Guide](REAL_API_INTEGRATION.md) - How to test with real API calls
- [Privacy Assistant Documentation](README-privacy-assistant.md) - Detailed documentation of the core module
- [Implementation Details](implementation_summary.md) - Technical details of the implementation
- [Piiranha Integration](docs/piiranha_integration.md) - Details on the enhanced PII detection with transformer models

## Features

- **Advanced AI-based Detection**: Uses state-of-the-art Piiranha transformer model for superior PII detection
- **Pattern-based Detection**: Identifies emails, addresses, phone numbers, credit cards, API keys, and more
- **Hybrid Detection Approach**: Combines Microsoft Presidio framework with modern transformer models
- **Privacy Classification**: Categorizes information by sensitivity level (HIGH, MEDIUM, LOW)
- **Reversible Transformation**: Converts sensitive data to privacy-preserving placeholders
- **Consistent Mapping**: Preserves relationships between sensitive data points
- **Secure Storage**: Encrypted database for sensitive information mapping
- **API Proxy**: Transparent middleware for all API calls
- **Extensibility**: Custom patterns and sensitivity classifications
- **JSON Support**: Handles complex nested JSON structures
- **Privacy Metrics**: Tracks and reports on sensitive information handling
- **Multilingual Support**: Enhanced PII detection across multiple languages
- **Multi-AI Protocol Support**: Compatible with all major AI API formats including OpenAI, Anthropic, and IDE-specific formats
- **Format Adaptation**: Automatically detects and adapts to different AI request/response formats

## Components

| Component | Description |
|-----------|-------------|
| `privacy_assistant.py` | Core module for sensitive data handling |
| `proxy_intercept.py` | mitmproxy script for request/response modification |
| `transformers_recognizer.py` | Custom recognizer for transformer model integration |
| `start_privacy_proxy.sh` | Launcher script for the proxy server |
| `real_ai_demo.py` | Demo script for OpenAI API integration |
| `test_proxy.py` | Test script for proxy functionality |
| `test_privacy_assistant.py` | Validation tests for the core module |
| `test_enhanced_pii.py` | Benchmark test comparing standard and enhanced PII detection |

## Use Cases

- **Enterprise AI Integration**: Safely use external AI services with internal data
- **Healthcare**: Process medical data while preserving patient privacy
- **Financial Services**: Analyze financial data without exposing account details
- **Legal**: Extract insights from legal documents while protecting client information
- **Customer Support**: Use AI for support inquiries while protecting customer data

## Requirements

- Python 3.8+
- mitmproxy
- cryptography
- sqlite3
- spaCy with en_core_web_lg model
- transformers and torch (for enhanced PII detection capabilities)
- Microsoft Presidio (for NER and anonymization framework)

## IDE AI Integration

The proxy supports all major AI-powered coding assistants and IDE integrations, including:

- **GitHub Copilot**: Full support for GitHub Copilot's JSONRPC protocol and agent.js interactions
- **Cursor AI**: Compatible with Cursor's AI chat and code assistance formats
- **VS Code AI Extensions**: Supports VS Code-specific AI extensions and formats
- **JetBrains AI**: Compatible with JetBrains IDEs and their AI assistants
- **Other IDE Tools**: Support for TabNine, Codeium, Sourcegraph Cody, Amazon CodeWhisperer, and more

The proxy is designed to automatically detect and adapt to these different formats, ensuring privacy protection with:

- **Protocol Detection**: Automatically identifies the AI format being used based on request structure and headers
- **Format Adaptation**: Converts between formats to ensure compatibility with existing privacy protection mechanisms
- **Response Formatting**: Returns responses in the original format expected by the client application
- **Seamless Integration**: Works transparently with IDE plugins without requiring any configuration changes

This allows developers to safely use AI coding assistants even in environments with sensitive code and data.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 