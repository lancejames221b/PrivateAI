# Private AI Proxy - Production Deployment Guide 🕵️‍♀️

This guide outlines steps and considerations for deploying the Private AI Proxy in a production environment, focusing on security, performance, and reliability. Time to set up your secure surveillance!

## Production Considerations

Deploying in production requires more robust settings than development:

-   **Security**: Strong credentials, HTTPS for the admin UI (via reverse proxy), rate limiting.
-   **Performance**: Optimized WSGI server (Waitress), potentially multiple workers, proper logging levels.
-   **Reliability**: Running as a service, health checks, backups.
-   **Configuration**: Using a `.env` file with production-specific settings.

## Deployment Method: Running as a Service (Recommended)

Using `systemd` (common on Linux) is recommended for managing the proxy and web UI as background services.

### Prerequisites

-   Python 3.9+ installed system-wide or in a dedicated environment accessible by the service user.
-   Project files cloned to a stable location (e.g., `/opt/PrivateAI`).
-   Dependencies installed: `pip install -r requirements.txt` (potentially using `sudo` if installing system-wide or use a virtual environment owned by the service user).
-   A dedicated user for running the service (optional but recommended, e.g., `privai`).

### Steps

1.  **Create `.env` File**: Copy `.env.production` to `.env` in the project root (`/opt/PrivateAI/.env`).
    ```bash
    sudo cp /opt/PrivateAI/.env.production /opt/PrivateAI/.env
    # Ensure ownership is correct if using a dedicated user
    # sudo chown privai:privai /opt/PrivateAI/.env
    ```
    **Crucially, edit `/opt/PrivateAI/.env` and set strong, unique values for:**
    *   `SECRET_KEY`
    *   `BASIC_AUTH_USERNAME`
    *   `BASIC_AUTH_PASSWORD`
    *   Set `FLASK_ENV=production`
    *   Configure `PROXY_PORT` and `FLASK_APP_PORT` if needed.
    *   Set `LOG_LEVEL=INFO` or `WARNING`.

2.  **Prepare Service Files**: Copy and customize the example service file.
    ```bash
    sudo cp /opt/PrivateAI/ai-security-proxy.service /etc/systemd/system/private-ai.service
    sudo nano /etc/systemd/system/private-ai.service
    ```
    *   **Modify `private-ai.service`**: Update `WorkingDirectory`, `ExecStart` paths to match your installation (`/opt/PrivateAI`). Set the `User` and `Group` if using a dedicated user.
    *   You might need separate service files for the proxy (`ai_proxy.py`) and the web UI (`app.py`) if you want to manage them independently.
The example `ai-security-proxy.service` likely runs `ai_proxy.py`. You would create a similar `private-ai-web.service` for `app.py`.

3.  **Enable and Start Services**: Reload systemd and start the service(s).
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable private-ai.service # Or your specific service names
    sudo systemctl start private-ai.service
    # Repeat for the web UI service if separate
    sudo systemctl status private-ai.service # Check status
    ```

4.  **Certificate Installation (Manual)**:
    *   Access the admin UI via its configured URL (e.g., `http://your-server-ip:7070`).
    *   Click "Install Certificate" -> "Download Certificate".
    *   Install the downloaded `mitmproxy-ca-cert.pem` on **each client machine/browser** that needs to use the proxy, following the instructions in the modal or the [Troubleshooting Guide](../troubleshooting.md#case-002-https-certificate-problems).

5.  **Configure Firewall**: Ensure `PROXY_PORT` (e.g., 8080) and `FLASK_APP_PORT` (e.g., 7070) are allowed through the server's firewall if accessed externally.

6.  **(Optional) Reverse Proxy (Nginx/Apache)**: Set up a reverse proxy to:
    *   Provide HTTPS for the admin UI.
    *   Handle potential load balancing.
    *   Add another layer of security.

## Deployment Method: Using Production Scripts (Simpler, Foreground/Daemon)

Suitable for simpler setups or testing. Uses the scripts in `scripts/run/`.

1.  **Create and Configure `.env`**: Same as step 1 in the service method.
2.  **Run Proxy**: Start the proxy in the background.
    ```bash
    ./scripts/run/run_proxy_prod.sh --daemon
    ```
    Logs will typically go to `logs/proxy.out` and `logs/proxy.err`.
3.  **Run Web UI**: Start the web UI (likely needs separate terminal or backgrounding).
    ```bash
    # Ensure FLASK_ENV=production is set in .env
    python app.py # Or use a process manager like screen/tmux/nohup
    ```
4.  **Certificate Installation**: Same as step 4 in the service method.
5.  **Configure Firewall**: Same as step 5 in the service method.

## Monitoring

*   **Health Check**: If enabled (`ENABLE_HEALTH_CHECK=true` in `.env`), the proxy might expose a health endpoint (check `run_proxy_prod.sh` or `ai_proxy.py` for specifics, often on a separate port like 8081). The web UI might have `/health`.
*   **Logs**: Check `logs/aiproxy.log` (main proxy log) and `logs/admin_ui.log` (if `app.py` is configured to log there) or systemd journal (`journalctl -u private-ai.service`).
*   **System Resources**: Monitor CPU, memory, and network usage on the server.

## Security Considerations

*   **Secrets**: NEVER commit your production `.env` file. Use strong, unique keys/passwords.
*   **Admin UI Access**: Restrict access to the admin UI port (e.g., firewall rules, reverse proxy authentication).
*   **HTTPS**: Use a reverse proxy (Nginx, Apache) to provide TLS/SSL encryption for the admin UI.
*   **Dependencies**: Regularly update `requirements.txt` and rebuild images/reinstall packages (`pip install -r requirements.txt --upgrade`).
*   **Permissions**: Ensure file permissions for `.env`, `data/`, and `logs/` are appropriate (e.g., readable/writable only by the service user).

## Backup and Recovery

Regularly back up:

*   `/opt/PrivateAI/.env` (or wherever your config is)
*   The entire `/opt/PrivateAI/data/` directory (contains DB, patterns, etc.)

To restore, place the backed-up files in their correct locations and restart the services/scripts.