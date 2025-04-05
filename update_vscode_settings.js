// VS Code Settings Update Script
// This script updates VS Code settings to use our proxy on port 8081

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

// Write VS Code settings
function writeVSCodeSettings(settings) {
  const settingsPath = getVSCodeSettingsPath();
  console.log(`Writing VS Code settings to: ${settingsPath}`);
  
  try {
    fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2), 'utf8');
    console.log('VS Code settings updated successfully');
    return true;
  } catch (error) {
    console.error(`Error writing VS Code settings: ${error.message}`);
    return false;
  }
}

// Update proxy settings
function updateProxySettings(settings) {
  console.log('\n=== Updating VS Code Proxy Settings ===');
  
  // Update http.proxy setting
  settings['http.proxy'] = 'http://127.0.0.1:8081';
  console.log(`✅ http.proxy updated to: ${settings['http.proxy']}`);
  
  // Update http.proxyStrictSSL setting
  settings['http.proxyStrictSSL'] = false;
  console.log('✅ http.proxyStrictSSL set to false');
  
  // Update http.proxySupport setting
  settings['http.proxySupport'] = 'override';
  console.log('✅ http.proxySupport set to override');
  
  // Update GitHub Copilot proxy settings
  if (!settings['github.copilot.advanced']) {
    settings['github.copilot.advanced'] = {};
  }
  settings['github.copilot.advanced']['proxy'] = 'http://127.0.0.1:8081';
  console.log(`✅ github.copilot.advanced.proxy updated to: ${settings['github.copilot.advanced']['proxy']}`);
  
  console.log('\n=== Update Complete ===');
  
  return settings;
}

// Main function
function main() {
  const settings = readVSCodeSettings();
  
  if (settings) {
    const updatedSettings = updateProxySettings(settings);
    writeVSCodeSettings(updatedSettings);
  }
}

// Run the script
main();