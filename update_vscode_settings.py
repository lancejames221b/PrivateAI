#!/usr/bin/env python3
"""
Update VS Code settings to use the PrivateAI proxy
"""

import json
import os
import sys

def update_vscode_settings():
    """Update VS Code settings to use the proxy and disable SSL verification"""
    # Determine VS Code settings path based on OS
    if sys.platform == 'darwin':  # macOS
        settings_file = os.path.expanduser('~/Library/Application Support/Code/User/settings.json')
    elif sys.platform == 'win32':  # Windows
        settings_file = os.path.expanduser('%APPDATA%/Code/User/settings.json')
    else:  # Linux
        settings_file = os.path.expanduser('~/.config/Code/User/settings.json')
    
    print(f"Using settings file: {settings_file}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    
    # Load existing settings or create new ones
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        settings = {}
    
    # Update proxy settings
    settings['http.proxy'] = 'http://localhost:8080'
    settings['http.proxyStrictSSL'] = False
    
    # Write updated settings
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)
    
    print('VS Code settings updated successfully:')
    print(f'  http.proxy = {settings["http.proxy"]}')
    print(f'  http.proxyStrictSSL = {settings["http.proxyStrictSSL"]}')

if __name__ == "__main__":
    update_vscode_settings() 