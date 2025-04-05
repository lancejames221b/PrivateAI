# 🕵️ Private AI: Your AI Security Detective

Welcome to the Private AI documentation! This guide will help you understand, set up, and use the system to secure your AI interactions.

*Developed by Lance James @ Unit 221B*

## Table of Contents

1. [Introduction](./introduction.md)
2. [Quick Start](./quickstart.md)
3. [Docker Setup](./docker-setup.md)
4. [Admin Interface](./admin-interface.md)
5. [Proxy Configuration](./proxy-configuration.md)
6. [Dynamic Codename Generation](./codename-generation.md)
7. [PII Detection & Transformation](./pii-transformation.md)
8. [API Reference](./api-reference.md)
9. [IDE AI Integration](./ide-ai-integration.md)
10. [AI Server Management](./ai-server-management.md)
11. [Troubleshooting](./troubleshooting.md)

## About AI Privacy Proxy

The AI Privacy Proxy is a secure middleware system designed to protect your sensitive information when interacting with AI models and APIs. By dynamically detecting and replacing personally identifiable information (PII), credentials, organization names, and other sensitive data, it ensures your AI interactions remain secure without compromising functionality.

![AI Privacy Proxy Architecture](./images/architecture-overview.png)

## Key Features

- **Bidirectional Transformation**: Replace sensitive data in requests and restore original context in responses
- **Dynamic Codename Generation**: Create consistent, natural-sounding replacements for organizations and domains
- **Multi-Method Detection**: Combine regex patterns, NER models, and Microsoft Presidio for comprehensive coverage
- **Web Admin Interface**: Easy configuration and monitoring through a browser-based dashboard
- **Docker Integration**: Simple deployment with containerization
- **Customizable Rules**: Define your own patterns and transformation rules
- **Multi-AI Protocol Support**: Seamless integration with all major AI systems including IDE AI assistants

## Getting Started

For first-time users, we recommend starting with the [Quick Start Guide](./quickstart.md) or the [Docker Setup Instructions](./docker-setup.md).

## License

This project is licensed under the terms specified in the LICENSE file in the root directory.