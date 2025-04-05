# Private AI Proxy - Production Deployment Guide

This guide provides instructions for deploying the Private AI Proxy in a production environment with enhanced security, performance, and reliability features.

## Production Features

The production-ready version includes:

- **Enhanced Security**: Automatic HTTPS headers, rate limiting, and authentication
- **Performance Optimization**: Caching, connection pooling, and optimized database queries
- **Reliability**: Graceful shutdown, error recovery, and comprehensive logging
- **Monitoring**: Health check endpoint and detailed metrics
- **Scalability**: Support for multiple worker processes and configurable resource limits

## Deployment Options

### 1. Using the Production Scripts

Two production-ready scripts are provided:

- `run_proxy_prod.sh`: For running the proxy service in production mode
- `run_one_page_prod.sh`: For running the admin interface in production mode

### 2. Docker Deployment

For containerized deployment, use the provided Dockerfile and docker-compose.yml.

## Production Deployment Steps

### Prerequisites

- Python 3.9+ with pip
- Required Python packages: `pip install -r requirements.txt`
- Sufficient disk space for logs and database
- Proper network configuration (ports 8080 and 8081 accessible)

### Basic Deployment

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with production settings (see below)
4. Run the production proxy: `./run_proxy_prod.sh`
5. Run the production admin interface: `./run_one_page_prod.sh --production`

### Production Environment Variables

Create a `.env` file with the following settings:

```
# Security Settings
SECRET_KEY=your_secure_random_key
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=strong_password
BASIC_AUTH_ENABLED=true

# Performance Settings
ENABLE_RATE_LIMITING=true
RATE_LIMIT_RPM=60
MAX_REQUEST_SIZE=10485760

# Network Settings
PROXY_PORT=8080
HEALTH_PORT=8081
FLASK_ENV=production
FLASK_DEBUG=0

# Feature Settings
ENABLE_HEALTH_CHECK=true
BLOCK_ALL_DOMAINS=false
```

### Running as a Service

To run the proxy as a system service:

1. Copy the provided `ai-security-proxy.service` file to `/etc/systemd/system/`
2. Edit the file to set the correct paths and environment
3. Enable and start the service:

```bash
sudo systemctl enable ai-security-proxy
sudo systemctl start ai-security-proxy
```

### Daemon Mode

To run the proxy in the background:

```bash
./run_proxy_prod.sh --daemon
```

This will start the proxy as a background process and redirect output to log files.

## Production Command-Line Options

### Proxy Service

```bash
./run_proxy_prod.sh [OPTIONS]

Options:
  -p, --port PORT       Specify proxy port (default: 8080)
  -h, --health-port PORT Specify health check port (default: 8081)
  -w, --workers N       Number of worker processes (for mitm mode)
  -b, --bind ADDR       Bind address (default: 0.0.0.0)
  -r, --rate-limit RPM  Enable rate limiting with requests per minute
  -l, --log-level LEVEL Set log level (debug, info, warn, error)
  -m, --mitm            Use mitmproxy instead of standalone proxy
  -d, --daemon          Run in daemon mode (background)
  --help                Show this help message
```

### Admin Interface

```bash
./run_one_page_prod.sh [OPTIONS]

Options:
  -p, --production    Run in production mode
  -d, --development   Run in development mode (default)
  --port PORT         Specify port (default: 5002)
  --host HOST         Specify host (default: 0.0.0.0)
  --workers N         Number of workers for production (default: 4)
```

## Monitoring

### Health Check Endpoint

The health check endpoint is available at:

```
http://<host>:8081/health
```

This returns a JSON response with:
- Current status
- Uptime
- Request statistics
- Error count
- Version information

### Log Files

Production logs are stored in the `logs/` directory:
- `aiproxy.log`: Main application log
- `aiproxy.log.1`, `aiproxy.log.2`, etc.: Rotated log files
- `proxy.out`, `proxy.err`: Standard output and error logs when running in daemon mode

## Security Considerations

1. Always use strong passwords for the admin interface
2. Consider running behind a reverse proxy like Nginx for additional security
3. Set up proper firewall rules to restrict access to the proxy ports
4. Regularly update dependencies to get security patches
5. Monitor logs for suspicious activity

## Troubleshooting

If you encounter issues:

1. Check the log files in the `logs/` directory
2. Verify the proxy is running with `ps aux | grep ai_proxy`
3. Test the health check endpoint
4. Ensure all required directories exist and are writable
5. Verify network connectivity and port availability

## Backup and Recovery

Regularly back up the following:
- `data/mapping_store.db`: Contains all mappings and transformations
- `data/custom_patterns.json`: Contains custom patterns
- `.env`: Contains configuration

To restore from backup, simply copy these files back to their original locations.