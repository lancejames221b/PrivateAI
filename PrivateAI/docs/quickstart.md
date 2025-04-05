# Quick Start Guide: Private AI 🕵️

This guide will help you get the Private AI detective up and running quickly to protect your sensitive information.

*Prepared by Lance James @ Unit 221B*

## System Requirements

- Python 3.9 or higher
- pip package manager
- 2GB+ RAM recommended
- Optional: Docker and Docker Compose for containerized deployment

## Installation

### Option 1: Direct Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/private-ai.git
cd private-ai
```

2. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-privacy.txt
```

3. Set up environment variables (optional):

```bash
# Create a .env file
cp .env.example .env

# Edit the file with your preferred settings
# vim .env
```

4. Start the admin interface:

```bash
python app.py
```

5. In a separate terminal, start the proxy server:

```bash
python ai_proxy.py
```

### Option 2: Docker Installation (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/yourusername/private-ai.git
cd private-ai
```

2. Run the Docker setup script:

```bash
./run_docker.sh
```

This will start both the admin interface and proxy server in Docker containers.

## Initial Configuration

1. Access the admin interface at [http://localhost:5001](http://localhost:5001)

2. Configure your AI client to use the proxy:
   - Proxy address: `http://localhost:8080`
   - No authentication required by default

3. Test the proxy with a simple request:

```bash
# Using curl
curl -x http://localhost:8080 https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-your-api-key" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello from ACME Corp!"}]
  }'
```

You should see that "ACME Corp" gets replaced in the request, but appears normally in the response you receive.

4. Set up IDE AI integration (optional):

For GitHub Copilot, VS Code, or other AI coding assistants, configure your IDE to use the proxy:

```json
// VS Code settings.json
{
  "http.proxy": "http://localhost:8080",
  "http.proxyStrictSSL": false
}
```

For Cursor AI, set environment variables before starting:

```bash
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
```

See the [IDE AI Integration](./ide-ai-integration.md) guide for detailed instructions.

## Configure Your Application

How you configure your application depends on the programming language and HTTP client you're using:

### Python Example

```python
import requests

proxies = {
    'http': 'http://localhost:8080',
    'https': 'http://localhost:8080',
}

response = requests.post(
    'https://api.openai.com/v1/chat/completions',
    json={
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': 'Hello from SentinelOne!'}]
    },
    headers={'Authorization': 'Bearer sk-your-api-key'},
    proxies=proxies,
    verify=False  # Required for the HTTPS interception to work
)

print(response.json())
```

### Node.js Example

```javascript
const axios = require('axios');
const https = require('https');

const agent = new https.Agent({  
  rejectUnauthorized: false
});

axios.post('https://api.openai.com/v1/chat/completions', 
  {
    model: 'gpt-3.5-turbo',
    messages: [{role: 'user', content: 'Hello from Acme Corp!'}]
  },
  {
    headers: {
      'Authorization': 'Bearer sk-your-api-key'
    },
    proxy: {
      host: 'localhost',
      port: 8080
    },
    httpsAgent: agent
  }
)
.then(response => console.log(response.data));
```

## Next Steps

1. [Set up HTTPS certificates](./proxy-configuration.md#https-certificates) for more secure communication
2. [Configure detection patterns](./pii-transformation.md#custom-patterns) for your organization's specific needs
3. [Add domain blocklisting](./proxy-configuration.md#domain-blocklisting) for specific sensitive domains
4. Explore the [Admin Interface](./admin-interface.md) for more configuration options

## Troubleshooting

If you encounter issues:

- Check the [Troubleshooting Guide](./troubleshooting.md)
- Look for error messages in the terminal windows running the services
- Examine the log files in the `logs/` directory