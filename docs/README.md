# 🕵️ Private AI: Your AI Security Detective

Welcome to the Private AI documentation! This guide will help you understand, set up, and use Private AI to secure your AI interactions.

## Table of Contents

1. [Introduction](./introduction.md)
2. [Quick Start](./quickstart.md)
3. [API Reference](./api-reference.md)
4. [IDE AI Integration](./ide-ai-integration.md)
5. [Admin Interface](./admin-interface.md)
6. [Proxy Configuration](./proxy-configuration.md)
7. [PII Detection & Transformation](./pii-transformation.md)
8. [Deployment Guides](#deployment-guides)
9. [Project Documentation](#project-documentation)
10. [Troubleshooting](./troubleshooting.md)

## Deployment Guides

- [Docker Setup](./deployment/DOCKER_DEPLOYMENT.md)
- [Production Deployment](./deployment/PRODUCTION_DEPLOYMENT.md)
- [Installation Guide](./deployment/INSTALL.md)

## Project Documentation

- [Frontend Integration](./project/FRONTEND_INTEGRATION.md)
- [Codename Generation](./project/codename_summary.md)
- [One-Page Interface](./project/ONE_PAGE_README.md)
- [Privacy Design](./privacy_design.md)
- [Client Entity Guide](./client_entity_guide.md)
- [Piiranha Integration](./piiranha_integration.md)

## About Private AI

Private AI is a privacy-preserving middleware that acts as a detective for your data, intercepting communications between your applications and AI services to automatically detect and redact sensitive information before it reaches external AI models.

![Private AI Architecture](./images/architecture-overview.png)

## Key Features

- **Universal Protection**: Works with all major AI providers (OpenAI, Claude, Google, Mistral, etc.)
- **Comprehensive Coverage**: Protects PII, API keys, credentials, and company-specific information
- **Dual Operation Modes**: Run as a proxy server or integrate directly as a library
- **Seamless Integration**: Zero-code changes required for existing applications
- **Bi-directional Protection**: Secures data in both requests and responses

## How It Works

Private AI operates by:

1. **Intercepting Requests**: Acts as a MITM proxy between your application and AI services
2. **Analyzing Content**: Detects sensitive information using pattern matching and NLP techniques
3. **Transforming Data**: Replaces sensitive data with innocuous placeholders
4. **Forwarding Requests**: Sends the sanitized requests to the AI service
5. **Restoring Responses**: Translates placeholders back to original values in responses

## Getting Started

For first-time users, we recommend starting with the [Quick Start Guide](./quickstart.md) or the [Docker Setup Instructions](./deployment/DOCKER_DEPLOYMENT.md).

## License

This project is licensed under the MIT License - see the LICENSE file in the root directory.

---

*Created by Lance James @ Unit 221B*