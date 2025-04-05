#!/bin/bash

# Exit on error
set -e

# Function to handle errors
handle_error() {
    echo "Error occurred at line $1"
    exit 1
}

# Set up error handling
trap 'handle_error $LINENO' ERR

# Check if running in production mode
if [ "$1" == "production" ]; then
    echo "Starting in PRODUCTION mode"
    export FLASK_ENV=production
    export BASIC_AUTH_ENABLED=true
    # Use a secure random key in production
    export SECRET_KEY=$(openssl rand -hex 24)
    # Disable debug mode in production
    export FLASK_DEBUG=0
else
    echo "Starting in DEVELOPMENT mode"
    export FLASK_ENV=development
    export FLASK_DEBUG=1
fi

# Set up environment
export FLASK_APP=app.py
export FLASK_RUN_PORT=${PORT:-5002}
export FLASK_RUN_HOST=0.0.0.0
export DEFAULT_INTERFACE=one-page

# Create required directories if they don't exist
mkdir -p data logs

# Start the Flask app
echo "Starting Private AI Proxy one-page interface..."
echo "Navigate to http://localhost:7070 to access the interface"

# Run with gunicorn in production mode for better performance
if [ "$FLASK_ENV" == "production" ]; then
    if command -v gunicorn &> /dev/null; then
        echo "Using gunicorn for production deployment"
        gunicorn --bind 0.0.0.0:${FLASK_RUN_PORT} --workers 4 --access-logfile logs/access.log --error-logfile logs/error.log "app:app"
    else
        echo "Warning: gunicorn not found, falling back to Flask development server"
        python3 -m flask run
    fi
else
    python -m flask run
fi