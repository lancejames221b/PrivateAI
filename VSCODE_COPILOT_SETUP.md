# VS Code + GitHub Copilot Setup with Private AI Proxy

This guide walks you through the process of setting up VS Code with GitHub Copilot while using the Private AI proxy to protect your sensitive data.

## The Issue

GitHub Copilot authentication requires secure connections to GitHub's servers. When an HTTPS intercepting proxy like Private AI is active, this can cause authentication to fail with errors like:

- "Failed to fetch"
- "No response received"
- "An error occurred while signing up for the Copilot Free plan"

## Two-Step Solution

We've created two scripts to solve this problem:

1. **Step 1**: Authenticate with GitHub Copilot **without** the proxy
2. **Step 2**: Enable the proxy for protecting your sensitive data while using Copilot

## Instructions

### Step 1: Authenticate with GitHub Copilot

Run the first script to create a test project and disable the proxy for authentication:

```bash
./start_vscode_with_copilot.sh
```

This script will:
1. Create a test directory with sample files
2. Stop any running proxy processes
3. Update VS Code settings to **disable** the proxy
4. Launch VS Code with the test project

When VS Code opens:
1. Sign in to GitHub Copilot when prompted
2. Verify that Copilot is working (test it in the test.py file)
3. **Close VS Code completely** after successful authentication

### Step 2: Enable Private AI Proxy

After successfully authenticating with GitHub Copilot, run the second script:

```bash
./enable_proxy_after_auth.sh
```

This script will:
1. Set up the database required by the proxy
2. Create a properly configured .env file
3. Start the Private AI proxy with GitHub domains excluded
4. Update VS Code settings to use the proxy
5. Launch VS Code with the test project

When VS Code opens, GitHub Copilot should work normally while the Private AI proxy protects your sensitive data.

## How It Works

The key to making this work is:

1. **Certificate Installation**: The mitmproxy certificate must be installed in your system trust store
2. **GitHub Domain Exclusion**: All GitHub-related domains are excluded from interception in the .env file
3. **Two-Phase Process**: First authenticate without proxy, then enable the proxy

## Troubleshooting

If you still encounter issues:

1. **Certificate Issues**: Verify the certificate is properly installed:
   ```bash
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem
   ```

2. **Domain Exclusions**: Check the EXCLUDED_DOMAINS in .env includes all GitHub domains

3. **Proxy Connection**: Verify the proxy is running:
   ```bash
   curl -x http://localhost:8080 -I https://example.com
   ```

4. **VS Code Settings**: Check that VS Code is configured correctly:
   ```
   "http.proxy": "http://localhost:8080",
   "http.proxyStrictSSL": false
   ```

5. **Restore Original Settings**: If needed, restore your original VS Code settings:
   ```bash
   cp "~/Library/Application Support/Code/User/settings.json.bak" "~/Library/Application Support/Code/User/settings.json"
   ```

## Testing Privacy Protection

Once set up, you can test that the Private AI proxy is protecting your sensitive data:

1. Open the test.py file in VS Code
2. Use Copilot to generate code based on the sensitive data
3. Check the proxy logs to verify interception and transformation

## Restoring Your Environment

To restore your original environment:

1. Kill the proxy process (Ctrl+C in the terminal running the enable_proxy_after_auth.sh script)
2. Restore your original VS Code settings from the backup

## Advanced Users

If you prefer to set things up manually:

1. Install the mitmproxy certificate in your system trust store
2. Update your .env file to exclude GitHub domains
3. Start the proxy manually with:
   ```bash
   mitmdump -p 8080 --set confdir=~/.mitmproxy --set block_global=false --set ssl_insecure=true -s proxy_intercept.py
   ```
4. Configure VS Code to use the proxy 