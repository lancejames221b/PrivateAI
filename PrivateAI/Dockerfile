FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi-dev \
    openssl \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt requirements-privacy.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt -r requirements-privacy.txt

# Copy all project files
COPY . .

# Create directories
RUN mkdir -p data logs

# Expose ports for the admin panel and proxy
EXPOSE 5000 8080

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Starting AI Security Proxy..."\n\
if [ "$1" = "admin" ]; then\n\
  python app.py\n\
elif [ "$1" = "proxy" ]; then\n\
  python ai_proxy.py\n\
else\n\
  echo "Starting both services..."\n\
  python ai_proxy.py & python app.py\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["admin"] 