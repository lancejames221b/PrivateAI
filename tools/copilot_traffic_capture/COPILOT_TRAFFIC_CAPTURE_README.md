# GitHub Copilot Traffic Capture Tools

This directory contains tools for capturing and analyzing the HTTPS traffic between VS Code and GitHub Copilot servers.

## Quick Start

1. Install mitmproxy certificate:
   ```bash
   ./install_mitmproxy_cert.sh
   ```

2. Launch VS Code with proxy to capture traffic:
   ```bash
   ./launch_vscode_with_proxy.sh
   ```

3. Use GitHub Copilot in VS Code to generate completions and chat.

4. Close VS Code when done.

5. Analyze the captured traffic:
   ```bash
   ./analyze_copilot_traffic.sh
   ```

6. Reset VS Code to connect directly without proxy:
   ```bash
   ./reset_vscode_direct.sh
   ```

## Available Scripts

- `install_mitmproxy_cert.sh`: Installs the mitmproxy certificate in the system trust store and VS Code.
- `launch_vscode_with_proxy.sh`: Launches VS Code with mitmproxy for capturing GitHub Copilot traffic.
- `analyze_copilot_traffic.sh`: Analyzes the captured traffic and generates a summary report.
- `reset_vscode_direct.sh`: Resets VS Code to connect directly without proxy.

## Detailed Documentation

For more detailed information, see [GITHUB_COPILOT_TRAFFIC_CAPTURE.md](GITHUB_COPILOT_TRAFFIC_CAPTURE.md).

## Requirements

- mitmproxy installed (`brew install mitmproxy` on macOS)
- VS Code with GitHub Copilot extension installed
- jq installed (`brew install jq` on macOS)
- Administrative access (for certificate installation)

## Troubleshooting

If you encounter issues:

1. Check that the mitmproxy certificate is correctly installed in both the system trust store and VS Code.
2. Ensure VS Code is configured to use the proxy and has Proxy Strict SSL disabled.
3. Try using a different port if 8080 is already in use.
4. Check the logs in `~/copilot_logs/` for more information.

## License

MIT