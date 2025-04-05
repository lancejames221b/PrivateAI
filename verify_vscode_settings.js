// VS Code Settings Verification Script
// This script checks if VS Code settings are properly configured for our proxy

const fs = require('fs');
const path = require('path');
const os = require('os');

// Determine VS Code settings path based on platform
function getVSCodeSettingsPath() {
  const homedir = os.homedir();
  
  if (process.platform === 'darwin') {
    // macOS
    return path.join(homedir, 'Library/Application Support/Code/User/settings.json');
  } else if (process.platform === 'linux') {
    // Linux
    return path.join(homedir, '.config/Code/User/settings.json');
  } else if (process.platform === 'win32') {
    // Windows
    return path.join(process.env.APPDATA || '', 'Code/User/settings.json');
  } else {
    throw new Error(`Unsupported platform: ${process.platform}`);
  }
}

// Read VS Code settings
function readVSCodeSettings() {
  const settingsPath = getVSCodeSettingsPath();
  console.log(`Reading VS Code settings from: ${settingsPath}`);
  
  try {
    const settingsContent = fs.readFileSync(settingsPath, 'utf8');
    return JSON.parse(settingsContent);
  } catch (error) {
    console.error(`Error reading VS Code settings: ${error.message}`);
    return null;
  }
}

// Verify proxy settings
function verifyProxySettings(settings) {
  console.log('\n=== VS Code Proxy Settings Verification ===');
  
  // Check http.proxy setting
  if (settings['http.proxy']) {
    console.log(`✅ http.proxy is set to: ${settings['http.proxy']}`);
  } else {
    console.log('❌ http.proxy is not set');
  }
  
  // Check http.proxyStrictSSL setting
  if (settings['http.proxyStrictSSL'] === false) {
    console.log('✅ http.proxyStrictSSL is set to false');
  } else {
    console.log(`❌ http.proxyStrictSSL is not set to false: ${settings['http.proxyStrictSSL']}`);
  }
  
  // Check http.proxySupport setting
  if (settings['http.proxySupport'] === 'override') {
    console.log('✅ http.proxySupport is set to override');
  } else {
    console.log(`❌ http.proxySupport is not set to override: ${settings['http.proxySupport']}`);
  }
  
  // Check GitHub Copilot proxy settings
  if (settings['github.copilot.advanced'] && 
      settings['github.copilot.advanced']['proxy']) {
    console.log(`✅ github.copilot.advanced.proxy is set to: ${settings['github.copilot.advanced']['proxy']}`);
  } else {
    console.log('❌ github.copilot.advanced.proxy is not set');
  }
  
  console.log('\n=== Verification Complete ===');
}

// Main function
function main() {
  const settings = readVSCodeSettings();
  
  if (settings) {
    verifyProxySettings(settings);
  }
}

// Run the script
main();