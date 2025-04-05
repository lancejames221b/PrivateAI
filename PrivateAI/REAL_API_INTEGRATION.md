# Testing the Privacy AI Proxy with Real API Calls

This guide explains how to test the Privacy Assistant with real API calls, sending requests through the proxy to protect sensitive information.

## Overview

The setup consists of:

1. **Privacy Assistant** (`privacy_assistant.py`): Core module that detects, transforms, and restores sensitive information
2. **Proxy Interceptor** (`proxy_intercept.py`): mitmproxy script that processes requests through the proxy
3. **Proxy Server** (`start_privacy_proxy.sh`): Script to start the proxy server
4. **API Demo** (`real_ai_demo.py`): Script that demonstrates a real OpenAI API call through the proxy
5. **Proxy Test** (`test_proxy.py`): Simple test to verify the proxy is working

## Setup

### 1. Install Prerequisites

Ensure you have all required packages installed:

```bash
pip install -r requirements.txt
```

### 2. Set API Key

Set your OpenAI API key in the environment:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Or save it in a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

### 3. Start the Proxy

In one terminal, start the proxy server:

```bash
./start_privacy_proxy.sh
```

This will start mitmproxy on port 8080 by default.

## Testing Options

### 1. Simple Proxy Test

To quickly verify the proxy is working:

```bash
./test_proxy.py
```

This sends a request with sensitive data to httpbin.org and verifies the proxy is transforming the data correctly.

### 2. Real OpenAI API Call

To make a real API call to OpenAI through the proxy:

```bash
./real_ai_demo.py
```

This demonstrates:
- Sanitizing sensitive information in the prompt
- Sending the sanitized prompt through the proxy to OpenAI
- Restoring original values in the response

### 3. Custom Prompt

You can provide your own prompt with sensitive information:

```bash
./real_ai_demo.py --prompt "My email is user@example.com and my API key is sk_test_1234567890abcdefghijklmnopqrstuvwxyz"
```

### 4. Using Curl

You can also test with curl directly:

```bash
curl -x http://localhost:8080 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "My email is user@example.com and my API key is sk_test_1234567890abcdefghijklmnopqrstuvwxyz"
      }
    ]
  }' \
  https://api.openai.com/v1/chat/completions
```

## Proxy Configuration

You can configure the proxy using environment variables or command-line arguments:

### Proxy Settings

- `PROXY_PORT`: Port for the proxy server (default: 8080)
- `PROXY_MODE`: Mode to run mitmproxy in (`mitmdump` or `mitmweb`) (default: mitmdump)
- `BLOCK_ALL_DOMAINS`: Whether to block all domain names (default: false)
- `LOG_LEVEL`: Logging level (default: info)
- `LOG_FILE`: Log file location (default: proxy.log)

### Demo Settings

- `--api-key`: OpenAI API key (default: uses environment variable)
- `--proxy`: Proxy URL (default: http://localhost:8080)
- `--prompt`: Custom prompt to use (default: uses built-in example)

## Troubleshooting

### Proxy Connection Issues

If you see "Proxy error" messages, check:

1. Is the proxy running in another terminal?
2. Is it running on the correct port?
3. Do you have certificates installed for HTTPS connections?

### Certificate Issues

For HTTPS connections, you need to install the mitmproxy certificate:

```bash
mitmproxy --help
```

Follow the instructions for installing the certificate on your system.

### OpenAI API Key

If you see authentication errors, check your API key:

1. Verify the key is set correctly in the environment
2. Check that the key has not expired
3. Ensure the key has sufficient permissions for the model you're using

## Privacy Metrics

The Privacy Assistant tracks metrics on each request:

- Number of sensitive items detected
- Number of items transformed
- Breakdown by sensitivity level (HIGH, MEDIUM, LOW)

You can view these metrics in the demo output or access them programmatically:

```python
from privacy_assistant import get_privacy_metrics
metrics = get_privacy_metrics()
``` 