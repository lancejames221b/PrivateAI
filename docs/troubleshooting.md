# Troubleshooting: Case Closed - Solutions for Common Issues 🕵️

This guide provides solutions for common issues you might encounter with the AI Privacy Proxy. Let's close these cases!

## Proxy Connection Issues

### Case 001: Proxy Won't Start

**Symptoms**:
- Error messages when running `python ai_proxy.py`
- "Proxy not running" status in admin interface
- Unable to connect to proxy from client applications

**Solutions**:

1. **Check for port conflicts**:
   ```bash
   # Check if port 8080 is already in use
   lsof -i :8080
   netstat -tuln | grep 8080
   ```
   
   If the port is in use, either:
   - Stop the conflicting application
   - Change the proxy port in the configuration

2. **Check dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Check log files**:
   ```bash
   cat logs/proxy.log
   ```

4. **Verify permissions**:
   ```bash
   # Ensure you have write permission to logs directory
   chmod 755 logs
   ```

### Case 002: HTTPS Certificate Problems

**Symptoms**:
- SSL errors when connecting to HTTPS endpoints
- "SSL verification failed" errors
- Client applications unable to connect to secure sites

**Solutions**:

1. **Install MITM Proxy CA Certificate Manually**:
   * **Why?** The proxy needs to intercept encrypted HTTPS traffic. To do this without browser/application warnings, its custom Certificate Authority (CA) must be trusted by your system.
   * **How?**
      1. Ensure the proxy has run at least once (or run `scripts/deployment/setup_certificates.sh` manually in your terminal, *without* `sudo`). This generates the certificate.
      2. In the Private AI web interface, click the "Install Certificate" button.
      3. A modal window will appear. Click the "Download Certificate" button to download `mitmproxy-ca-cert.pem`.
      4. Follow the **OS-specific instructions** provided in the modal (or below) to install the downloaded certificate into your system's or browser's trust store.

   * **Common Instructions (Simplified):**
      1. **macOS**: Open Keychain Access > System keychain > Drag `.pem` file in > Double-click cert > Trust > Always Trust.
      2. **Windows**: Double-click `.pem` file > Install Certificate > Local Machine > Place in store > Browse > Trusted Root Certification Authorities > OK > Next > Finish.
      3. **Linux (Ubuntu/Debian)**: `sudo cp mitmproxy-ca-cert.pem /usr/local/share/ca-certificates/mitmproxy-ca.crt && sudo update-ca-certificates`
      4. **Linux (Fedora/CentOS)**: `sudo cp mitmproxy-ca-cert.pem /etc/pki/ca-trust/source/anchors/mitmproxy-ca.crt && sudo update-ca-trust`
      5. **Firefox**: Settings > Privacy & Security > Certificates > View Certificates > Authorities > Import > Select `.pem` > Trust this CA to identify websites > OK.

   * **Important**: Restart your browser and potentially your application after installing the certificate.

2. **(Alternative - Less Secure) Configure Client to Ignore Errors**: *Not recommended for general use.*
   * Python `requests`: `verify=False`
   * `curl`: `--insecure`
   * Node.js: `rejectUnauthorized: false`

3. **Verify Certificate Exists**: The file should be at `~/.mitmproxy/mitmproxy-ca-cert.pem` or `data/mitmproxy-ca-cert.pem`.

### Case 003: Client Configuration Issues

**Symptoms**:
- Requests not going through the proxy
- "Connection refused" errors
- Direct connections instead of proxied connections

**Solutions**:

1. **Verify proxy URL**:
   - Ensure you're using `http://localhost:8080` (not https)
   - Check for typos in the hostname or port

2. **Test proxy connection**:
   ```bash
   curl -x http://localhost:8080 https://example.com
   ```

3. **Check client configuration**:
   - Python: Ensure `proxies` parameter is correctly formatted
   - Node.js: Verify `proxy` configuration in axios/request
   - curl: Check -x parameter format

## Transformation Issues: Data in Disguise

### Case 004: Entity Not Being Detected

**Symptoms**:
- Sensitive information appears unchanged in requests
- No entry for the entity in mappings table

**Solutions**:

1. **Add a custom pattern**:
   - Go to the Patterns page in the admin interface
   - Create a new pattern that matches your entity

2. **Check entity format**:
   - Ensure the entity follows a consistent format
   - Test with simplified examples first

3. **Adjust detection settings**:
   ```bash
   # Edit .env file
   USE_PRESIDIO=true
   ```

4. **Check transformation logs**:
   - Review `logs/proxy.log` for transformation attempts
   - Look for any error messages during detection

### Case 005: Inconsistent Replacements

**Symptoms**:
- Same entity gets different replacements in different requests
- Replacements change after restart

**Solutions**:

1. **Check mapping database**:
   ```bash
   sqlite3 data/mapping_store.db "SELECT * FROM mappings WHERE original LIKE '%sensitive-text%';"
   ```

2. **Verify database persistence**:
   - Ensure the `data` directory is not being deleted
   - Check permissions on the directory

3. **Look for variant spellings/formats**:
   - "CompanyName" vs "Company Name" vs "company-name"
   - Case sensitivity issues

### Case 006: JSON Transformation Problems

**Symptoms**:
- JSON requests not being properly transformed
- JSON syntax errors after transformation
- Only parts of JSON being transformed

**Solutions**:

1. **Validate JSON format**:
   - Ensure your request JSON is well-formed
   - Check for escaped quotes or special characters

2. **Review the JSON structure**:
   - Complex nested structures might need special handling
   - Check the `transform_json` function logs

3. **Test with simplified JSON**:
   - Start with a simple JSON object to confirm functionality
   - Gradually add complexity to find the breaking point

## Admin Interface Issues: Control Room Down

### Case 007: Admin Interface Not Loading

**Symptoms**:
- Unable to access http://localhost:5001
- Browser shows connection errors

**Solutions**:

1. **Check if admin process is running**:
   ```bash
   ps aux | grep app.py
   ```

2. **Verify port availability**:
   ```bash
   lsof -i :5001
   ```

3. **Check logs**:
   ```bash
   cat logs/admin_ui.log
   ```

4. **Restart the admin interface**:
   ```bash
   python app.py
   ```

### Case 008: Authentication Problems

**Symptoms**:
- Unable to log in to admin interface
- Authentication loop
- "Unauthorized" errors

**Solutions**:

1. **Reset credentials**:
   ```python
   # Edit .env file
   BASIC_AUTH_USERNAME=admin
   BASIC_AUTH_PASSWORD=password
   ```

2. **Check auth configuration**:
   ```python
   # In app.py, verify BASIC_AUTH is properly configured
   app.config['BASIC_AUTH_FORCE'] = True
   ```

3. **Clear browser cookies**:
   - Delete cookies for localhost
   - Try in incognito/private browsing mode

## Database Issues: Data Integrity at Risk

### Case 009: Database Corruption

**Symptoms**:
- SQLite errors in logs
- Missing or inconsistent data
- "Database is locked" errors

**Solutions**:

1. **Check database integrity**:
   ```bash
   sqlite3 data/mapping_store.db "PRAGMA integrity_check;"
   ```

2. **Backup and recreate database**:
   ```bash
   cp data/mapping_store.db data/mapping_store.db.bak
   rm data/mapping_store.db
   python -c "from pii_transform import initialize_db; initialize_db()"
   ```

3. **Fix permissions**:
   ```bash
   chmod 644 data/mapping_store.db
   ```

### Case 010: Encryption Issues

**Symptoms**:
- "Invalid token" errors during decryption
- Unable to restore original values
- Encryption key errors

**Solutions**:

1. **Check encryption key**:
   ```bash
   ls -la data/.encryption_key
   ```

2. **Reset encryption**:
   ```bash
   # Disable encryption temporarily
   export ENCRYPT_DATABASE=false
   ```

3. **Re-encrypt database**:
   ```bash
   python -c "from pii_transform import migrate_to_encrypted_database; migrate_to_encrypted_database()"
   ```

## Docker Issues: Container Lockdown

### Case 011: Container Not Starting

**Symptoms**:
- `docker-compose up` fails
- Container exits immediately
- Health check failing

**Solutions**:

1. **Check container logs**:
   ```bash
   docker-compose logs
   ```

2. **Verify volume mounts**:
   - Ensure directories exist
   - Check permissions

3. **Update Docker images**:
   ```bash
   docker-compose build --no-cache
   ```

### Case 012: Volume Mount Problems

**Symptoms**:
- Data not persisting between restarts
- "Permission denied" errors
- Container can't write to volumes

**Solutions**:

1. **Check host directories**:
   ```bash
   ls -la data logs static templates
   ```

2. **Fix permissions**:
   ```bash
   chmod -R 755 data logs static templates
   ```

3. **Verify volume configuration**:
   ```bash
   docker-compose config
   ```

## Performance Issues: Slow Operation

### Case 013: Slow Response Times

**Symptoms**:
- Requests taking a long time to process
- High CPU usage
- Time-outs in client applications

**Solutions**:

1. **Check resource usage**:
   ```bash
   top -p $(pgrep -f "python ai_proxy.py")
   ```

2. **Optimize pattern matching**:
   - Reduce the number of active patterns
   - Prioritize patterns by frequency

3. **Disable resource-intensive features**:
   ```bash
   # Edit .env file
   USE_PRESIDIO=false
   ```

4. **Increase client timeouts**:
   - Adjust timeouts in your client application
   - Allow more time for processing complex requests

## Case Assistance: Getting Help

If you've tried the solutions above and still have issues, it's time to call in reinforcements:
1. **Check the logs**:
   - `logs/proxy.log`
   - `logs/admin_ui.log`

2. **Enable debug logging**:
   ```bash
   # Edit .env file
   FLASK_ENV=development
   LOG_LEVEL=DEBUG
   ```

3. **Collect diagnostic information**:
   ```bash
   python -c "import sys, platform; print(f'Python: {sys.version}, OS: {platform.platform()}')"
   pip freeze > requirements_installed.txt
   ```

4. **File an issue** with:
   - Description of the problem
   - Steps to reproduce
   - Error messages and logs
   - System information
      - Attach the `requirements_installed.txt` file