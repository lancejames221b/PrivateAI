# Private AI Proxy Frontend - Quick Start Guide

This guide provides quick instructions to get the Private AI Proxy frontend up and running.

## Prerequisites

- Python 3.7 or higher
- Flask and other dependencies installed (see `requirements.txt`)
- Basic understanding of the Private AI Proxy system

## Quick Start

1. Make sure all the frontend files are in place:
   - Template files in the `templates/` directory
   - CSS files in the `static/css/` directory
   - JavaScript files in the `static/js/` directory
   - Updated routes in `app.py`

2. Run the application:
   ```bash
   ./run_frontend.sh
   ```

3. Access the application in your browser:
   ```
   http://localhost:5000
   ```

4. Log in with the default credentials:
   - **Username:** admin
   - **Password:** privacy2025

## Features

The frontend provides access to:

- **Privacy Control Panel** - Manage privacy settings and view transformations
- **Configuration Interface** - Configure privacy rules and model connections
- **System Monitoring** - Monitor system health and performance
- **Analytics Panel** - View privacy effectiveness and usage statistics

## Troubleshooting

If you encounter issues:

1. Check that Flask is installed:
   ```bash
   pip install flask flask-wtf flask-basicauth
   ```

2. Ensure the database is initialized:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/mapping_store.db'); conn.execute('CREATE TABLE IF NOT EXISTS mappings (original TEXT PRIMARY KEY, replacement TEXT NOT NULL, entity_type TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'); conn.commit(); conn.close()"
   ```

3. Verify that the application is running:
   ```bash
   ps aux | grep flask
   ```

4. Check the logs for errors:
   ```bash
   cat admin_ui.log
   ```

## Next Steps

After logging in, explore the different sections of the application:

1. Start with the **Dashboard** to get an overview of the system
2. Configure privacy rules in the **Configuration** section
3. Monitor system performance in the **Monitoring** section
4. Analyze privacy effectiveness in the **Analytics** section

For more detailed information, refer to the `FRONTEND_INTEGRATION.md` document.