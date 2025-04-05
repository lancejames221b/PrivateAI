# Private AI Proxy - Simple One-Page Interface

This is a simplified, all-in-one interface for managing the Private AI Proxy. It combines the core functionality into a single page for easier management and monitoring.

## Features

- **Proxy Control**: Start/stop the proxy service directly from the interface
- **Protection Statistics**: View key privacy metrics at a glance
- **Privacy Settings**: Toggle different privacy protection features
- **Test Interface**: Test text processing with instant results
- **Connection Configuration**: Configure proxy and AI model endpoints

## Getting Started

1. Run the one-page interface:
   ```
   ./run_one_page.sh
   ```

2. Access the interface at:
   ```
   http://localhost:5001/one-page
   ```

3. Use the start/stop buttons to control the proxy service

4. Test your privacy protection by entering text in the test area

## Privacy Protection Types

The interface includes toggles for these privacy protection categories:

- **PII Protection**: Names, emails, phone numbers, addresses, etc.
- **Domain Protection**: Internal domain names and URLs
- **Security Data**: API keys, credentials, tokens
- **API Key Protection**: API credentials for various services
- **Inference Prevention**: Protects against model inference about private data
- **Code Protection**: Sanitizes code snippets of sensitive information

## Screenshots

![One-Page Interface](docs/one_page_interface.png)

## Notes

This simplified interface provides core functionality for daily use, while the full interface offers more detailed configuration and monitoring capabilities. 