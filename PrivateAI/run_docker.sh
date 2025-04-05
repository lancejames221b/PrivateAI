#!/bin/bash
# This script runs the AI Privacy Proxy in Docker

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker before proceeding."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose before proceeding."
    exit 1
fi

# Create necessary directories
mkdir -p data logs

# Check for existing containers and stop them if running
echo "Checking for existing containers..."
if docker ps -a | grep -q "private-ai"; then
    echo "Stopping existing containers..."
    docker-compose down
fi

# Build and start the services
echo "Building and starting AI Privacy Proxy services..."
docker-compose up -d

# Show status
echo 
echo "AI Privacy Proxy Services:"
echo "-------------------------"
echo "Admin Interface: http://localhost:7070"
echo "Proxy Service: http://localhost:8080"
echo
echo "Configure your application to use the proxy at localhost:8080"
echo
echo "To view logs, run: docker-compose logs -f"
echo "To stop services, run: docker-compose down"