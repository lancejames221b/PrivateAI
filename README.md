# Private AI - AI Tools Privacy Plugin

A privacy protection plugin for AI-powered development tools that intercepts and transforms sensitive information in code before it's sent to external AI services.

## 🔒 Features

- **PII Detection**: Uses transformer models and pattern matching to detect sensitive information
- **Privacy Transformation**: Replaces sensitive information with innocuous placeholders
- **Traffic Analysis**: Provides detailed metrics on what was protected
- **Plugin Architecture**: Integrates with the Private AI plugin system
- **IDE Integration**: Works seamlessly with VS Code and various AI coding tools

## 🚀 Quick Start

```bash
# Launch VS Code with Private AI protection
./private_ai.sh launch

# Analyze captured AI tool traffic
./private_ai.sh analyze

# Create test files with known PII
./private_ai.sh test
```

## 🔍 Why This Matters

AI-powered development tools like GitHub Copilot, Amazon CodeWhisperer, Tabnine, and others send your code to external servers for processing. This can potentially expose sensitive information like:

- API keys and credentials
- Personal information
- Internal company information
- Database connection strings
- IP addresses and server paths

Private AI provides privacy protection by intercepting the traffic between your IDE and AI services, detecting sensitive information, and transforming it before it reaches external servers.

## 🛠️ How It Works

1. **Intercepting Traffic**: Uses mitmproxy to intercept HTTPS traffic between your IDE and AI services
2. **Detecting PII**: Uses transformer models and pattern matching to detect sensitive information
3. **Transforming PII**: Replaces sensitive information with innocuous placeholders
4. **Preserving Functionality**: Ensures AI tools still work effectively with the transformed data
5. **Analyzing Results**: Provides metrics on what was protected

## 📋 Prerequisites

- Python 3.8+
- mitmproxy (`brew install mitmproxy` on macOS)
- VS Code with AI coding extensions
- jq (`brew install jq` on macOS)

## 📦 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/lancejames221b/privateAI.git
   cd privateAI
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make scripts executable:
   ```bash
   chmod +x private_ai.sh
   chmod +x plugins/ai_tools_privacy/scripts/*.sh
   ```

## 📚 Project Structure

```
.
├── private_ai.sh              # Main script for easy access
├── proxy_base.py              # Base proxy module
├── plugins/
│   ├── config.json            # Plugin configuration
│   ├── ai_tools_plugin.py     # Base AI tools plugin
│   └── ai_tools_privacy/      # AI tools privacy plugin
│       ├── __init__.py
│       ├── ai_tools_privacy_plugin.py
│       ├── scripts/
│       │   ├── launch_ide_with_privacy.sh
│       │   ├── analyze_privacy.sh
│       │   └── test_privacy.sh
│       └── docs/
│           └── README.md
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Configuration

The plugin can be configured by editing the `plugins/config.json` file:

```json
{
  "plugins": {
    "AIToolsPrivacyPlugin": {
      "enabled": true,
      "priority": 5,
      "domains": [
        "api.github.com",
        "github.com",
        "api.githubcopilot.com",
        "copilot-proxy.githubusercontent.com",
        "githubcopilot.com",
        "default.exp-tas.com",
        "api.openai.com",
        "api.anthropic.com",
        "codewhisperer.amazonaws.com",
        "tabnine.com",
        "api.sourcegraph.com"
      ]
    }
  }
}
```

## 🔍 Troubleshooting

### Certificate Issues

If you see certificate errors:
1. Check that the mitmproxy certificate is installed in your system trust store
2. Verify that your IDE is configured to use the certificate
3. Try restarting your IDE after certificate installation

### Proxy Connection Issues

If your IDE can't connect to AI services:
1. Verify that the proxy is running
2. Check your IDE's proxy settings
3. Ensure the `NODE_EXTRA_CA_CERTS` environment variable is set correctly

## 📝 Privacy Considerations

While Private AI helps protect sensitive information, it's important to note:
- It may not catch all sensitive information
- It may transform some non-sensitive information
- It adds a layer of processing that may impact performance
- It requires trusting the Private AI proxy with your code

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

Lance James, Unit 221B

## 🙏 Acknowledgments

- [mitmproxy](https://mitmproxy.org/) for the proxy functionality
- [Hugging Face Transformers](https://huggingface.co/transformers/) for NER models
- Various AI coding tools for enhancing developer productivity