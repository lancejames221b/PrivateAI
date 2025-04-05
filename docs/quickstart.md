# Quick Start: Your First Case with Private AI 🕵️

Welcome, Detective! This guide will get you up and running with the Private AI proxy quickly. Follow these steps to start protecting sensitive information during your AI interactions.

## 1. Installation: Gathering Your Tools

First, you need to set up your detective kit.

```bash
# Clone the Private AI repository
git clone https://github.com/lancejames221b/PrivateAI.git
cd PrivateAI

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install required dependencies
pip install -r requirements.txt
```

## 2. Start the Proxy: Going Undercover

Now, start the Private AI proxy server. This server will intercept and analyze your AI requests.

```bash
# Start the proxy server using the run script
./scripts/run/run_proxy.sh

# Alternatively, start the one-page interface (includes proxy):
# ./scripts/run/run_one_page.sh
```

You should see output indicating the proxy is running, typically on `localhost:8080`.

## 3. Install the Certificate: Gaining Access (HTTPS)

To allow Private AI to inspect secure HTTPS traffic (most AI APIs), you need to trust its custom certificate.

1.  **Access the Admin Interface**: Open your web browser and go to `http://localhost:7070` (or the port specified if you used `run_one_page.sh`). Log in if prompted (check `.env` for credentials, default: `admin`/`change_this_password`).
2.  **Download the Certificate**: In the "Proxy Status" section, click the "Install Certificate" button. In the modal window that appears, click "Download Certificate". This will download `mitmproxy-ca-cert.pem`.
3.  **Install the Certificate**: Follow the OS-specific instructions shown in the modal (or in the [Troubleshooting Guide](./troubleshooting.md#case-002-https-certificate-problems)) to install the downloaded certificate into your system or browser trust store.
4.  **Restart**: Restart your browser and any applications you want to use with the proxy.

**Why is this needed?** Without trusting the certificate, your browser/system will block the proxy from inspecting HTTPS traffic, resulting in connection errors.

## 4. Configure Your Application: Setting the Trail

Instruct your application or tool to use the Private AI proxy. This usually involves setting the HTTP and HTTPS proxy environment variables or configuring your application directly.

**Example (Environment Variables):**
```bash
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080

# Optional: For Python requests library to trust the CA cert
export REQUESTS_CA_BUNDLE=~/.mitmproxy/mitmproxy-ca-cert.pem 

# Now run your application
# python your_ai_script.py
# curl https://api.openai.com/v1/models ...
```

**Example (Python Requests):**
```python
import requests
import os

proxies = {
    "http": "http://localhost:8080",
    "https": "http://localhost:8080",
}

# Path to the downloaded certificate
cert_path = os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.pem")

response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    # ... your headers and json payload ...
    proxies=proxies,
    verify=cert_path # Trust the Private AI CA certificate
)

print(response.json())
```

## 5. Monitor the Investigation: Reviewing the Clues

Use the Private AI web interface (`http://localhost:7070`) to:

*   See if the proxy is running.
*   View statistics on detected and replaced sensitive items.
*   Manage custom detection patterns and domain blocklists.
*   Test text transformations directly.

## Case Closed: Next Steps

You've successfully set up Private AI!

*   Explore the features of the [Admin Interface](./admin-interface.md).
*   Learn how to configure [Custom Patterns](./docs/custom-patterns.md) (Link needs update).
*   Dive deeper into the [Architecture](./docs/architecture.md) (Link needs update).
*   Check the [Troubleshooting Guide](./troubleshooting.md) if you encounter issues.