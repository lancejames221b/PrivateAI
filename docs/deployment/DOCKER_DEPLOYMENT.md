# Docker Deployment Guide for Private AI Proxy 🕵️

This guide provides instructions for deploying the Private AI Proxy using Docker in both development and production environments. Ensure your Docker setup is as secure as a locked evidence room!

## Prerequisites

- Docker Engine (version 20.10.0 or later)
- Docker Compose (version 2.0.0 or later)
- Git (for cloning the repository)
- At least 2GB of RAM available for containers
- At least 5GB of disk space

## Quick Start (Production)

For a quick production deployment:

```bash
# Clone the repository
git clone https://github.com/lancejames221b/PrivateAI.git
cd PrivateAI

# Copy and configure environment variables
cp .env.production .env

# IMPORTANT: Edit .env and set strong passwords for BASIC_AUTH_PASSWORD and SECRET_KEY
# nano .env

# Build and start the production environment
# Use the scripts located in the scripts/docker directory
./scripts/docker/run_docker_prod.sh --build --detach
```

Access the admin interface at `http://localhost:7070` (or the port configured in `.env`).
Access the proxy on `http://localhost:8080` (or the port configured in `.env`).

## Development vs Production

Two separate Docker setups are provided:

1.  **Development Environment**:
    *   Uses `docker-compose.yml`
    *   Mounts code as volumes for live reloading
    *   Exposes debugging ports
    *   Runs in development mode with verbose logging (`FLASK_ENV=development`)
    *   Run using `./scripts/docker/run_docker.sh`

2.  **Production Environment**:
    *   Uses `docker-compose.production.yml` and `Dockerfile.production`
    *   Uses multi-stage builds for smaller, more secure images
    *   Implements security best practices (non-root user, etc.)
    *   Includes health checks
    *   Runs with optimized settings (e.g., Waitress for Flask)
    *   Run using `./scripts/docker/run_docker_prod.sh`

## Production Deployment Details

### Configuration

1.  Copy the production environment template:
    ```bash
    cp .env.production .env
    ```

2.  **Edit the `.env` file** and customize:
    *   `SECRET_KEY`: **MUST be changed** to a strong, random value.
    *   `BASIC_AUTH_USERNAME`, `BASIC_AUTH_PASSWORD`: **MUST be changed**.
    *   `FLASK_APP_PORT`: Port for the admin UI (default: 7070).
    *   `PROXY_PORT`: Port for the MITM proxy (default: 8080).
    *   `LOG_LEVEL`: Set to `INFO` or `WARNING` for production.
    *   Other relevant settings (e.g., PII detection levels).

### Building and Running with Script

The `scripts/docker/run_docker_prod.sh` script simplifies management:

```bash
# Build and start containers in detached mode
./scripts/docker/run_docker_prod.sh --build --detach

# Start existing containers in detached mode
./scripts/docker/run_docker_prod.sh --detach

# Stop containers
./scripts/docker/run_docker_prod.sh --stop

# Restart containers
./scripts/docker/run_docker_prod.sh --restart

# View logs
./scripts/docker/run_docker_prod.sh --logs

# Clean up containers, networks, and volumes (USE WITH CAUTION)
./scripts/docker/run_docker_prod.sh --clean
```

### Manual Docker Compose Commands (Production)

```bash
# Build images
docker compose -f docker-compose.production.yml build

# Start containers in detached mode
docker compose -f docker-compose.production.yml up -d

# View logs
docker compose -f docker-compose.production.yml logs -f

# Stop containers
docker compose -f docker-compose.production.yml down

# Stop and remove volumes (USE WITH CAUTION)
docker compose -f docker-compose.production.yml down -v
```

## Certificate Installation in Docker

When running Private AI inside Docker, you still need client applications *outside* Docker to trust the proxy's CA certificate to inspect HTTPS traffic.

1.  **Start the Containers**: Use `./scripts/docker/run_docker_prod.sh --build --detach` or the development equivalent.
2.  **Access Admin UI**: Open `http://localhost:7070` (or your configured `FLASK_APP_PORT`) in your host machine's browser.
3.  **Download Certificate**: Click "Install Certificate" -> "Download Certificate" to get `mitmproxy-ca-cert.pem`.
4.  **Install on Host**: Install the downloaded certificate into your **host machine's** system or browser trust store using the instructions provided in the modal or the [Troubleshooting Guide](../troubleshooting.md#case-002-https-certificate-problems).
5.  **Configure Clients**: Configure applications running on your host machine to use the proxy address (e.g., `http://localhost:8080`).

## Container Architecture (Production)

The `docker-compose.production.yml` setup typically includes:

1.  **`web` Service (Admin Interface)**:
    *   Runs `app.py` using Waitress.
    *   Handles UI interactions, configuration management.
    *   Listens on the `FLASK_APP_PORT`.

2.  **`proxy` Service**:
    *   Runs `ai_proxy.py` (which executes `mitmproxy` with `proxy_intercept.py`).
    *   Intercepts and transforms AI traffic.
    *   Listens on the `PROXY_PORT`.

These services communicate over a Docker network.

## Security Considerations

The production Docker setup includes features like:

*   Running containers as a non-root user (`privaiuser`).
*   Using official, slim base images.
*   Multi-stage builds to reduce attack surface.
*   Basic health checks (can be expanded).
*   **Crucially**, relying on secure configuration in the `.env` file (strong keys, passwords).

## Volumes and Persistence

Named Docker volumes are used for data persistence:

*   `privateai_data`: Stores SQLite database (`mapping_store.db`), configuration JSON files (`custom_patterns.json`, etc.). Maps to `/home/privaiuser/data` inside containers.
*   `privateai_logs`: Stores application logs. Maps to `/home/privaiuser/logs` inside containers.

These ensure data isn't lost when containers are recreated. *Note: These are Docker-managed volumes, not direct host mounts by default in the production setup for better encapsulation.*

## Health Checks

Basic health checks might be defined in the Dockerfiles or Compose file. Extend these as needed for robust monitoring.
*   `web`: Check if the Flask app is responding (e.g., `/health` endpoint).
*   `proxy`: Check if the mitmproxy process is running and the port is open.

## Customizing the Docker Setup

### Changing Ports

Modify the `ports` section in `docker-compose.production.yml` (or `docker-compose.yml`) **AND** update the corresponding `FLASK_APP_PORT` and `PROXY_PORT` variables in your `.env` file.

Example (`docker-compose.production.yml`):
```yaml
services:
  web:
    ports:
      - "${FLASK_APP_PORT:-7070}:${FLASK_APP_PORT:-7070}" # Exposes host:container
  proxy:
    ports:
      - "${PROXY_PORT:-8080}:${PROXY_PORT:-8080}"
```

### Adding Custom Certificates (Less Common)

If you need the proxy container itself to trust external CAs, you would modify the `Dockerfile` to copy certificates and update the system trust store within the image build process.

## Troubleshooting Docker

### Container Fails to Start

Check the logs:
```bash
# Production
docker compose -f docker-compose.production.yml logs web
docker compose -f docker-compose.production.yml logs proxy

# Development
docker compose logs web
docker compose logs proxy
```
Common issues: Port conflicts on the host, permission errors (less likely with named volumes), configuration errors in `.env`, insufficient host resources (RAM/CPU).

### Performance Issues

*   Allocate more resources (CPU/memory) to Docker Desktop or your Docker daemon.
*   Review container resource usage (`docker stats`).
*   Ensure `FLASK_ENV` is *not* set to `development` in the production `.env` file.

## Production Deployment Checklist

- [x] **Change default credentials** in `.env` (`SECRET_KEY`, `BASIC_AUTH_PASSWORD`).
- [ ] Review and configure `LOG_LEVEL` in `.env`.
- [ ] Test proxy functionality thoroughly.
- [ ] Verify health checks are operational.
- [ ] Set up external monitoring if required.
- [ ] Ensure data persistence (volumes) is working correctly.
- [ ] Implement a backup strategy for the persistent volumes.