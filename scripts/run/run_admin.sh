#!/bin/bash

# Script to run the AI Security Proxy Admin Panel

echo "AI Security Proxy Admin Panel"
echo "============================"
echo

# Check for required dependencies
if ! command -v python &> /dev/null; then
    echo "Python not found. Please install Python 3.6 or higher."
    exit 1
fi

# Make sure data directory exists
mkdir -p data

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating default .env file..."
    echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(16))')" > .env
    echo "FLASK_APP=app.py" >> .env
fi

# Check if Flask is installed
if ! python -c "import flask" &> /dev/null; then
    echo "Flask not found. Installing dependencies..."
    python -m pip install -r requirements.txt
fi

# Run the app
echo "Starting the Admin Panel on http://localhost:7070"
echo "Press Ctrl+C to stop"
echo
python3 run_flask.py
python app.py 