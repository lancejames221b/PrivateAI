# AI Privacy Proxy - Docker Setup

This document explains how to run the AI Privacy Proxy using Docker containers.

## Prerequisites

- Docker Engine
- Docker Compose

## Quick Start

Run the provided script to start all services:

```bash
./run_docker.sh
```

This will:
1. Create necessary directories
2. Build Docker images
3. Start both the admin interface and proxy service

## Services

After starting, the following services will be available:

- **Admin Interface**: http://localhost:5001
  - Web interface for managing the proxy settings
  - View detected sensitive information
  - Configure patterns and rules

- **Proxy Service**: http://localhost:8080
  - HTTP/HTTPS proxy for your AI API calls
  - Automatically scrubs sensitive information

## Configuration

1. Configure your application to use the proxy at `localhost:8080`
2. Access the admin interface at http://localhost:5001 to:
   - See what information is being detected
   - Add custom patterns
   - Configure domain blocking

## Directory Structure

- `data/`: Persistent storage for proxy mappings and settings
- `logs/`: Service logs
- `static/`: Static web assets
- `templates/`: Web interface templates

## Manual Commands

If you prefer not to use the script, you can run these commands directly:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Troubleshooting

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Ensure ports 5001 and 8080 are not in use by other applications
3. Make sure you have the latest version of Docker and Docker Compose

## Security Notes

- For production use, update the SECRET_KEY environment variable
- Consider enabling basic authentication for the admin interface
- Data is persisted in the local `data/` directory