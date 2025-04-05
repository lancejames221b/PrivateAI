# Installation Guide for AI Security Proxy

This guide explains how to install the AI Security Proxy as a system service.

## Prerequisites

- Python 3.6 or higher
- pip
- Git

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-security-proxy.git
cd ai-security-proxy
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Test the Installation

```bash
# Run the admin panel
./run_admin.sh
```

Visit http://localhost:5000 to ensure the admin panel works correctly.

### 4. Install as System Service (Linux/systemd)

1. Edit the service file with your user and installation path:

```bash
# Copy the example service file
cp ai-security-proxy.service /tmp/ai-security-proxy.service

# Edit the service file with your details
sed -i "s/<USER>/$(whoami)/g" /tmp/ai-security-proxy.service
sed -i "s:/path/to/ai-security-proxy:$(pwd):g" /tmp/ai-security-proxy.service

# Install the service
sudo cp /tmp/ai-security-proxy.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Enable and start the service:

```bash
sudo systemctl enable ai-security-proxy.service
sudo systemctl start ai-security-proxy.service
```

3. Check service status:

```bash
sudo systemctl status ai-security-proxy.service
```

### 5. Create a Separate Service for the Proxy (Optional)

If you want to run the proxy as a separate service:

1. Create a service file:

```bash
cat > /tmp/ai-security-proxy-mitmproxy.service << EOF
[Unit]
Description=AI Security Proxy mitmproxy
After=network.target ai-security-proxy.service
Requires=ai-security-proxy.service

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=/bin/bash -c "./run_proxy.sh"
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/ai-security-proxy-mitmproxy.service /etc/systemd/system/
sudo systemctl daemon-reload
```

2. Enable and start the proxy service:

```bash
sudo systemctl enable ai-security-proxy-mitmproxy.service
sudo systemctl start ai-security-proxy-mitmproxy.service
```

## Docker Installation

Alternatively, you can use Docker to run the AI Security Proxy:

```bash
# Build and run using docker-compose
docker-compose up -d
```

The admin panel will be available at http://localhost:5000, and the proxy will listen on http://localhost:8080.

## Configuration

1. Create a `.env` file with your desired configuration:

```bash
cp .env.example .env
# Edit .env with your preferred settings
nano .env
```

2. Configure SSL certificates through the admin panel:
   - Visit http://localhost:5000/setup
   - Follow the instructions to install certificates

## Troubleshooting

- Check the logs:
  ```bash
  sudo journalctl -u ai-security-proxy.service
  ```

- Restart the service:
  ```bash
  sudo systemctl restart ai-security-proxy.service
  ```

- If you're having permission issues, make sure the user specified in the service file has access to the installation directory.

- For Docker installations, check the logs:
  ```bash
  docker-compose logs -f
  ``` 