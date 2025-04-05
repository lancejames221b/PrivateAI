# Docker Deployment Guide for Private AI Proxy

This guide provides instructions for deploying the Private AI Proxy using Docker in both development and production environments.

## Prerequisites

- Docker Engine (version 20.10.0 or later)
- Docker Compose (version 2.0.0 or later)
- At least 2GB of RAM available for containers
- At least 5GB of disk space

## Quick Start

For a quick production deployment:

```bash
# Clone the repository
git clone https://github.com/yourusername/private-ai-proxy.git
cd private-ai-proxy

# Copy and configure environment variables
cp .env.production .env
# Edit .env with your settings

# Start the production environment
./run_docker_prod.sh --build
```

## Development vs Production

Two separate Docker setups are provided:

1. **Development Environment**:
   - Uses `docker-compose.yml`
   - Mounts code as volumes for live reloading
   - Exposes debugging ports
   - Runs in development mode with verbose logging

2. **Production Environment**:
   - Uses `docker-compose.production.yml`
   - Uses multi-stage builds for smaller images
   - Implements security best practices
   - Includes health checks and resource limits
   - Runs with optimized settings for performance

## Production Deployment

### Configuration

1. Copy the production environment template:
   ```bash
   cp .env.production .env
   ```

2. Edit the `.env` file to set:
   - Security credentials
   - Resource limits
   - Feature flags
   - Network settings

### Building and Running

Use the provided script for managing the production deployment:

```bash
# Build and start containers
./run_docker_prod.sh --build

# Start containers in detached mode
./run_docker_prod.sh --detach

# Stop containers
./run_docker_prod.sh --stop

# Restart containers
./run_docker_prod.sh --restart

# Clean up containers and volumes
./run_docker_prod.sh --clean

# View logs
./run_docker_prod.sh --logs
```

### Manual Docker Compose Commands

If you prefer to use Docker Compose directly:

```bash
# Build images
docker-compose -f docker-compose.production.yml build

# Start containers
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Stop containers
docker-compose -f docker-compose.production.yml down
```

## Container Architecture

The production setup consists of two main services:

1. **Web Service (Admin Interface)**:
   - Runs on port 5002
   - Provides the admin interface for managing the proxy
   - Uses Waitress as a production WSGI server
   - Implements authentication and security headers

2. **Proxy Service**:
   - Runs on port 8080 (main proxy) and 8081 (health check)
   - Handles AI API requests with privacy transformations
   - Implements rate limiting and request validation
   - Provides health check endpoint for monitoring

## Security Features

The production Docker setup includes:

- Non-root user for running containers
- Read-only file system where possible
- Resource limits to prevent DoS attacks
- Secure environment variable handling
- Health checks for reliability
- Container restart policies
- Network isolation

## Volumes and Persistence

Two Docker volumes are used for data persistence:

1. **data-volume**: Stores database files and mappings
2. **logs-volume**: Stores application logs

These volumes are mounted to the host machine's `./data` and `./logs` directories.

## Health Checks and Monitoring

Both services include health check endpoints:

- Web service: `http://localhost:5002/health`
- Proxy service: `http://localhost:8081/health`

These endpoints return JSON with service status and metrics.

## Customizing the Docker Setup

### Changing Ports

To change the exposed ports, edit the `docker-compose.production.yml` file:

```yaml
services:
  web:
    ports:
      - "8000:5002"  # Change 8000 to your desired port
```

### Adding Custom Certificates

To use custom SSL certificates:

1. Place your certificates in a directory (e.g., `./certs`)
2. Add a volume mount in `docker-compose.production.yml`:
   ```yaml
   volumes:
     - ./certs:/app/certs
   ```
3. Set the certificate paths in your `.env` file

## Troubleshooting

### Container Fails to Start

Check the logs:
```bash
docker-compose -f docker-compose.production.yml logs
```

Common issues:
- Port conflicts: Change the exposed ports
- Permission issues: Check volume mount permissions
- Memory limits: Increase container memory limits

### Performance Issues

If you experience performance issues:
- Increase CPU and memory limits in `docker-compose.production.yml`
- Adjust worker counts in the `.env` file
- Check for resource contention on the host machine

## Production Deployment Checklist

Before deploying to production:

- [ ] Set strong passwords in `.env`
- [ ] Configure rate limiting appropriately
- [ ] Set up proper logging
- [ ] Test health check endpoints
- [ ] Verify resource limits are appropriate
- [ ] Ensure data persistence is working
- [ ] Test graceful container shutdown