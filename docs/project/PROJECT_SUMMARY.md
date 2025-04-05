# Private AI: Privacy-Preserving AI Interaction System

## Purpose

Private AI is a middleware system designed to protect sensitive information in API interactions with AI models. It enables secure use of AI capabilities while preventing exposure of personal, financial, or proprietary data.

## Core Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌───────────┐     ┌──────────┐
│ Application │────▶│ Privacy Proxy   │────▶│ AI API    │────▶│ Response │
│ with        │     │ - Detection     │     │ Service   │     │ with     │
│ Sensitive   │     │ - Transformation│     │           │     │ Privacy  │
│ Data        │     │ - Restoration   │     │           │     │ Preserved│
└─────────────┘     └─────────────────┘     └───────────┘     └──────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Secure Mapping│
                    │ Database      │
                    └───────────────┘
```

## Key Components

1. **Privacy Assistant (`privacy_assistant.py`)**
   - Core engine for data transformation
   - Pattern-based detection with regex and NLP
   - Reversible transformation system
   - Sensitivity classification (HIGH/MEDIUM/LOW)

2. **Proxy System**
   - `start_privacy_proxy.sh`: Launches mitmproxy
   - `proxy_intercept.py`: Script for intercepting and processing API calls
   - Certificate management for HTTPS inspection

3. **Testing and Demo Components**
   - `test_privacy_assistant.py`: Validates core functionality
   - `private_ai_demo.py`: Simulation of privacy system in action
   - `real_ai_demo.py`: Actual OpenAI API integration
   - `test_proxy.py`: Verifies proxy functionality

4. **Documentation**
   - `README-privacy-assistant.md`: User guide and API documentation
   - `REAL_API_INTEGRATION.md`: Testing instructions
   - `requirements-privacy.txt`: Dependency specifications

## Key Features

- **Privacy Preservation**: Transforms sensitive data before sending to AI services
- **Consistent Transformation**: Maintains consistency for coherent AI responses
- **Data Restoration**: Seamlessly restores original values in AI responses
- **Security First**: Encrypted storage of transformation mappings
- **API Proxy**: Acts as a transparent middleware for all API calls
- **Extensibility**: Custom patterns and sensitivity levels
- **Metrics**: Tracks privacy statistics for monitoring and reporting

## Use Cases

1. **Enterprise AI Integration**: Safely use external AI services with internal data
2. **Healthcare**: Process medical information while preserving patient privacy
3. **Financial Analysis**: Analyze financial data without exposing account details
4. **Legal Document Processing**: Extract insights while protecting client information
5. **Research**: Share data with AI models while maintaining compliance

## Technical Stack

- **Language**: Python 3.8+
- **Proxy Technology**: mitmproxy
- **Cryptography**: Using Fernet for symmetric encryption
- **NLP Components**: spaCy (optional)
- **Storage**: SQLite with encryption
- **API Support**: HTTP/HTTPS with JSON processing

## Getting Started

See `REAL_API_INTEGRATION.md` for detailed setup and testing instructions. 