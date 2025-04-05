#!/bin/bash

# Run Frontend for Private AI Proxy
# This script starts the Flask application with the new frontend components

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export BASIC_AUTH_USERNAME=admin
export BASIC_AUTH_PASSWORD=privacy2025

# Create necessary directories if they don't exist
mkdir -p data
mkdir -p logs

# Check if the database exists, if not create it
if [ ! -f data/mapping_store.db ]; then
    echo "Initializing database..."
    python -c "
import sqlite3
conn = sqlite3.connect('data/mapping_store.db')
conn.execute('''
CREATE TABLE IF NOT EXISTS mappings (
    original TEXT PRIMARY KEY,
    replacement TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()
"
fi

# Check if custom patterns file exists, if not create it
if [ ! -f data/custom_patterns.json ]; then
    echo "Creating custom patterns file..."
    echo '{}' > data/custom_patterns.json
fi

# Check if domain blocklist file exists, if not create it
if [ ! -f data/domain_blocklist.txt ]; then
    echo "Creating domain blocklist file..."
    touch data/domain_blocklist.txt
fi

# Start the Flask application
echo "Starting Private AI Proxy Frontend..."
echo "Login credentials:"
echo "Username: admin"
echo "Password: privacy2025"
echo "Access the application at http://localhost:7070"

# Run the Flask application directly with Python instead of using the flask command
python3 run_flask.py