# Private AI Proxy - One-Page Interface

This is a simplified, all-in-one interface for managing the Private AI Proxy. It combines the core functionality into a single page for easier management and monitoring.

## Features

- **Proxy Control**: Start/stop the proxy service directly from the interface
- **Protection Statistics**: View key privacy metrics at a glance
- **Privacy Settings**: Toggle different privacy protection features
- **Test Interface**: Test text processing with instant results
- **Connection Configuration**: Configure proxy and AI model endpoints

## Getting Started

### Development Mode

To run the one-page interface in development mode:

```bash
./run_one_page.sh
```

Access the interface at: http://localhost:5002

### Production Mode

For production deployment, use the production script with enhanced security and performance:

```bash
./run_one_page_prod.sh --production
```

Additional options:

```bash
# Run on a different port
./run_one_page_prod.sh --production --port 8080

# Specify number of worker processes
./run_one_page_prod.sh --production --workers 8

# Get help on all available options
./run_one_page_prod.sh --help
```

## Production Enhancements

The production mode includes several enhancements:

- **HTTPS Security Headers**: Protection against common web vulnerabilities
- **Compression**: Reduced bandwidth usage and faster page loads
- **Caching**: Improved performance for static assets
- **Metrics**: Prometheus metrics for monitoring
- **Production Server**: Uses Gunicorn/Waitress instead of Flask's development server
- **Secure Defaults**: Automatically enables authentication and generates secure keys

## Installation Requirements

For development:
```bash
pip install -r requirements.txt
```

For production:
```bash
pip install -r requirements.txt
```

## Privacy Protection Types

The interface includes toggles for these privacy protection categories:

- **PII Protection**: Names, emails, phone numbers, addresses, etc.
- **Domain Protection**: Internal domain names and URLs
- **Security Data**: API keys, credentials, tokens
- **API Key Protection**: API credentials for various services
- **Inference Prevention**: Protects against model inference about private data
- **Code Protection**: Sanitizes code snippets of sensitive information

## Troubleshooting

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Ensure all required directories exist (`data/` and `logs/`)
3. Verify that the database is properly initialized
4. For production issues, check that all required packages are installed

## Security Considerations

1. Always use production mode with authentication enabled in production environments
2. Regularly update dependencies to get security patches
3. Consider enabling HTTPS in production by setting `force_https=True` in the Talisman configuration
4. Use strong passwords for the admin interface