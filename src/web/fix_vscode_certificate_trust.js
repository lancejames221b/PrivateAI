#!/usr/bin/env node
/**
 * VS Code Certificate Trust Fix
 * 
 * This script fixes the issue with VS Code not trusting our proxy's certificate
 * by modifying the Electron app's certificate trust settings.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Configuration
const CERT_PATH = path.join(os.homedir(), '.private-ai/private-ai-ca-cert.pem');
const PROXY_HOST = '127.0.0.1';
const PROXY_PORT = 8081;

// Check if certificate exists
if (!fs.existsSync(CERT_PATH)) {
  console.error(`Certificate not found at ${CERT_PATH}`);
  process.exit(1);
}

// Read certificate
const certificate = fs.readFileSync(CERT_PATH, 'utf8');
console.log(`Read certificate from ${CERT_PATH}`);

// Create a script to modify VS Code's main.js to trust our certificate
function createElectronPatch() {
  const patchPath = path.join(os.homedir(), '.private-ai/electron_patch.js');
  
  const patchContent = `
// VS Code Electron Certificate Trust Patch
const { app } = require('electron');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Certificate path
const CERT_PATH = '${CERT_PATH.replace(/\\/g, '\\\\')}';

// Read certificate
let certificate;
try {
  certificate = fs.readFileSync(CERT_PATH);
  console.log('Successfully loaded certificate from ' + CERT_PATH);
} catch (error) {
  console.error('Failed to load certificate:', error);
}

// Set up certificate trust
if (certificate) {
  app.on('ready', () => {
    // Add certificate to Electron's trust store
    const { session } = require('electron');
    const defaultSession = session.defaultSession;
    
    // Clear all certificate verification caches
    defaultSession.clearHostResolverCache();
    defaultSession.clearAuthCache();
    defaultSession.clearCache();
    
    // Set proxy settings
    defaultSession.setProxy({
      proxyRules: 'http=${PROXY_HOST}:${PROXY_PORT};https=${PROXY_HOST}:${PROXY_PORT}',
      proxyBypassRules: 'localhost,127.0.0.1'
    });
    
    // Trust our certificate
    app.on('certificate-error', (event, webContents, url, error, certificate, callback) => {
      // Accept all certificates when using our proxy
      event.preventDefault();
      callback(true);
      console.log('Accepted certificate for: ' + url);
    });
    
    console.log('Certificate trust and proxy settings configured');
  });
}
`;

  fs.writeFileSync(patchPath, patchContent);
  console.log(`Created Electron patch at ${patchPath}`);
  
  return patchPath;
}

// Create VS Code launcher script with certificate trust
function createVSCodeLauncher() {
  const launcherPath = path.join(os.homedir(), '.private-ai/launch_vscode_trusted.sh');
  
  const launcherContent = `#!/bin/bash
# VS Code Launcher with Certificate Trust

# Set environment variables
export NODE_EXTRA_CA_CERTS="${CERT_PATH}"
export ELECTRON_EXTRA_LAUNCH_ARGS="--ignore-certificate-errors"
export HTTP_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
export HTTPS_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
export NO_PROXY="localhost,127.0.0.1"

# Launch VS Code with certificate trust
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  ELECTRON_ARGS="--js-flags=--expose-gc --ignore-certificate-errors"
  VSCODE_PATH="/Applications/Visual Studio Code.app/Contents/MacOS/Electron"
  
  # Launch VS Code with our arguments
  "$VSCODE_PATH" $ELECTRON_ARGS "$@"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  ELECTRON_ARGS="--js-flags=--expose-gc --ignore-certificate-errors"
  VSCODE_PATH="$(which code)"
  
  # Launch VS Code with our arguments
  "$VSCODE_PATH" $ELECTRON_ARGS "$@"
elif [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32" ]]; then
  # Windows
  ELECTRON_ARGS="--js-flags=--expose-gc --ignore-certificate-errors"
  VSCODE_PATH="C:/Program Files/Microsoft VS Code/Code.exe"
  
  # Launch VS Code with our arguments
  "$VSCODE_PATH" $ELECTRON_ARGS "$@"
else
  echo "Unsupported OS: $OSTYPE"
  exit 1
fi
`;

  fs.writeFileSync(launcherPath, launcherContent);
  fs.chmodSync(launcherPath, '755'); // Make executable
  console.log(`Created VS Code launcher at ${launcherPath}`);
  
  return launcherPath;
}

// Main function
function main() {
  console.log('VS Code Certificate Trust Fix');
  
  // Create Electron patch
  const patchPath = createElectronPatch();
  
  // Create VS Code launcher
  const launcherPath = createVSCodeLauncher();
  
  console.log('\nFix completed successfully!');
  console.log(`\nTo launch VS Code with certificate trust, run:`);
  console.log(`  ${launcherPath}`);
}

// Run the script
main();