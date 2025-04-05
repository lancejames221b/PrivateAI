# Docker Setup: Containerizing the Clues 🕵️

This guide explains how to deploy the AI Privacy Proxy using Docker containers for a clean, isolated, and easy-to-manage installation. Let's get started with containerizing our investigation.

## Prerequisites

- Docker Engine
- Docker Compose
- 2GB+ available RAM
- 1GB+ free disk space

## One-Command Setup

The easiest way to get started is with the provided setup script:

```bash
./run_docker.sh
```

This script will:
1. Check for Docker and Docker Compose
2. Create necessary directories
3. Build the Docker images
4. Start both services in detached mode
5. Provide URLs and basic instructions

## Manual Docker Setup

If you prefer to run commands manually or customize the setup:

### 1. Build the Images

```bash
docker-compose build
```

### 2. Start the Services

```bash
docker-compose up -d
```

This starts both services in detached mode:
- Admin interface on port 5001
- Proxy service on port 8080

### 3. View Logs

```bash
# View all logs
docker-compose logs -f

# View only admin interface logs
docker-compose logs -f admin

# View only proxy logs
docker-compose logs -f proxy
```

### 4. Stop the Services

```bash
docker-compose down
```

## Available Services

After starting the containers, you can access:

- **Admin Interface**: [http://localhost:5001](http://localhost:5001)
  - Web dashboard for configuration and monitoring
  - Access to logs, mappings, and settings

- **Proxy Service**: http://localhost:8080
  - HTTP/HTTPS proxy for AI API requests
  - Use this as your proxy server in applications

## Volume Mounts

The Docker setup uses volume mounts to persist data:

- `./data:/app/data`: Databases and configuration files
- `./logs:/app/logs`: Log files
- `./static:/app/static`: Static web assets
- `./templates:/app/templates`: Web interface templates
- `~/.mitmproxy:/root/.mitmproxy`: MITM proxy certificates

These mounts ensure that:
1. Your data persists between container restarts
2. You can easily access logs and data files
3. You can modify templates and static assets without rebuilding

## Environment Variables

You can customize the behavior with environment variables:

```yaml
# Example .env file
FLASK_ENV=production
SECRET_KEY=your-secure-key-here
BLOCK_ALL_DOMAINS=false
USE_PRESIDIO=true
ENCRYPT_DATABASE=true
BASIC_AUTH_USERNAME=admin
BASIC_AUTH_PASSWORD=secure-password
```

### Key Variables

- `FLASK_ENV`: Environment for Flask application (development/production)
- `SECRET_KEY`: Secret key for the Flask admin interface
- `BLOCK_ALL_DOMAINS`: Whether to block all domains by default (true/false)
- `USE_PRESIDIO`: Enable Microsoft Presidio integration (true/false)
- `ENCRYPT_DATABASE`: Encrypt stored mappings (true/false)
- `BASIC_AUTH_USERNAME`: Username for admin interface authentication
- `BASIC_AUTH_PASSWORD`: Password for admin interface authentication
- `PROXY_PORT`: Port for the proxy service (default: 8080)
- `LOG_LEVEL`: Log level for the proxy service (default: debug)
- `LOG_FILE`: Log file for the proxy service (default: /app/logs/proxy.log)
- `DOCKER_CONTAINER`: Flag to indicate if running in a Docker container (default: true)
- `PROXY_HOST`: Hostname for the proxy service (default: proxy)
- `PYTHONUNBUFFERED`: Ensures that the Python output is not buffered
- `NAME`: A test variable (default: World)

## Docker Networking

By default, the services use the following ports:

- **5001**: Admin interface (host) → 5000 (container)
- **8080**: Proxy service (both host and container)

If you need to change these ports due to conflicts, edit the `docker-compose.yml` file:

```yaml
ports:
  - "YOUR_CUSTOM_PORT:5000"  # For admin interface
  - "YOUR_PROXY_PORT:8080"   # For proxy service
```

## Production Deployment Considerations

For production deployments:

1. **Set a Strong Secret Key**: Generate a secure random key
   ```bash
   openssl rand -hex 32
   ```

2. **Enable Authentication**: Set BASIC_AUTH_USERNAME and BASIC_AUTH_PASSWORD

3. **Use HTTPS**: Consider putting the admin interface behind a reverse proxy with HTTPS

4. **Secure Persistence**: Mount volumes to secure, backed-up locations

5. **Resource Allocation**: Consider setting resource limits in docker-compose.yml
   ```yaml
   services:
     admin:
       # ... other settings
       deploy:
         resources:
           limits:
             cpus: '0.5'
             memory: 512M
   ```

## Upgrading

To upgrade to a newer version:

1. Pull the latest code
   ```bash
   git pull origin main
   ```

2. Rebuild the images
   ```bash
   docker-compose build
   ```

3. Restart the services
   ```bash
   docker-compose down
   docker-compose up -d
   ```

Your data will be preserved because it's stored in mounted volumes.

## Troubleshooting

-   **Container won't start**: Check logs with `docker-compose logs`
-   **Port conflicts**: Change the exposed ports in docker-compose.yml
-   **Volume permission issues**: Check ownership of the mounted directories
-   **Admin interface not loading**: Ensure the container is running with `docker-compose ps`
-   **General issues**: Check the logs for detailed error messages