#!/bin/bash

# AI Security Proxy - Docker Production Deployment Script
# =====================================================

# Exit on error
set -e

# Function to handle errors
handle_error() {
    echo "Error occurred at line $1"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Function to display usage
print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -b, --build         Build images before starting containers"
    echo "  -d, --detach        Run containers in detached mode"
    echo "  -p, --pull          Pull latest base images"
    echo "  -c, --clean         Remove existing containers and volumes"
    echo "  -l, --logs          Follow logs after starting"
    echo "  -s, --stop          Stop running containers"
    echo "  -r, --restart       Restart running containers"
    echo "  -h, --help          Show this help message"
    exit 1
}

# Default values
BUILD=false
DETACH=false
PULL=false
CLEAN=false
LOGS=false
STOP=false
RESTART=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--build)
            BUILD=true
            shift
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -p|--pull)
            PULL=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -l|--logs)
            LOGS=true
            shift
            ;;
        -s|--stop)
            STOP=true
            shift
            ;;
        -r|--restart)
            RESTART=true
            shift
            ;;
        -h|--help)
            print_usage
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            ;;
    esac
done

# Create required directories
mkdir -p data logs

# Check if .env.production exists and copy to .env if needed
if [ -f .env.production ] && [ ! -f .env ]; then
    echo "Copying .env.production to .env"
    cp .env.production .env
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Using default environment variables."
    echo "Consider creating an .env file based on .env.production template."
fi

# Stop running containers if requested
if [ "$STOP" = true ]; then
    echo "Stopping containers..."
    docker-compose -f docker-compose.production.yml down
    exit 0
fi

# Restart running containers if requested
if [ "$RESTART" = true ]; then
    echo "Restarting containers..."
    docker-compose -f docker-compose.production.yml restart
    exit 0
fi

# Clean up if requested
if [ "$CLEAN" = true ]; then
    echo "Cleaning up containers and volumes..."
    docker-compose -f docker-compose.production.yml down -v
    echo "Pruning unused images..."
    docker image prune -f
fi

# Pull latest base images if requested
if [ "$PULL" = true ]; then
    echo "Pulling latest base images..."
    docker pull python:3.9-slim
fi

# Build images if requested
if [ "$BUILD" = true ]; then
    echo "Building Docker images..."
    docker-compose -f docker-compose.production.yml build
fi

# Prepare detach flag
DETACH_FLAG=""
if [ "$DETACH" = true ]; then
    DETACH_FLAG="-d"
fi

# Start containers
echo "Starting containers..."
docker-compose -f docker-compose.production.yml up $DETACH_FLAG

# Follow logs if requested and in detached mode
if [ "$LOGS" = true ] && [ "$DETACH" = true ]; then
    echo "Following logs..."
    docker-compose -f docker-compose.production.yml logs -f
fi