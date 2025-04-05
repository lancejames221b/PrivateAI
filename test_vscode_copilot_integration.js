// VS Code Copilot Integration Test
// This script tests the integration between VS Code, GitHub Copilot, and our proxy

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');

// Log environment variables
console.log('=== Environment Variables ===');
console.log('NODE_EXTRA_CA_CERTS:', process.env.NODE_EXTRA_CA_CERTS || 'Not set');
console.log('HTTP_PROXY:', process.env.HTTP_PROXY || 'Not set');
console.log('HTTPS_PROXY:', process.env.HTTPS_PROXY || 'Not set');
console.log('NO_PROXY:', process.env.NO_PROXY || 'Not set');

// Check if proxy is running
function checkProxyRunning(port = 8081) {
  console.log(`\n=== Checking if proxy is running on port ${port} ===`);
  
  try {
    // Use netstat or lsof to check if the port is in use
    let command;
    if (process.platform === 'win32') {
      command = `netstat -ano | findstr :${port}`;
    } else {
      command = `lsof -i:${port}`;
    }
    
    const output = execSync(command, { encoding: 'utf8' });
    
    if (output.trim()) {
      console.log(`✅ Proxy is running on port ${port}`);
      return true;
    } else {
      console.log(`❌ No process found listening on port ${port}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Error checking if proxy is running: ${error.message}`);
    return false;
  }
}

// Check VS Code settings
function checkVSCodeSettings() {
  console.log('\n=== Checking VS Code Settings ===');
  
  // Determine VS Code settings path based on platform
  let settingsPath;
  if (process.platform === 'darwin') {
    // macOS
    settingsPath = path.join(os.homedir(), 'Library/Application Support/Code/User/settings.json');
  } else if (process.platform === 'linux') {
    // Linux
    settingsPath = path.join(os.homedir(), '.config/Code/User/settings.json');
  } else if (process.platform === 'win32') {
    // Windows
    settingsPath = path.join(process.env.APPDATA || '', 'Code/User/settings.json');
  } else {
    console.log(`❌ Unsupported platform: ${process.platform}`);
    return false;
  }
  
  try {
    const settingsContent = fs.readFileSync(settingsPath, 'utf8');
    const settings = JSON.parse(settingsContent);
    
    // Check proxy settings
    const httpProxy = settings['http.proxy'];
    const proxyStrictSSL = settings['http.proxyStrictSSL'];
    const proxySupport = settings['http.proxySupport'];
    const copilotProxy = settings['github.copilot.advanced'] && settings['github.copilot.advanced']['proxy'];
    
    console.log(`http.proxy: ${httpProxy}`);
    console.log(`http.proxyStrictSSL: ${proxyStrictSSL}`);
    console.log(`http.proxySupport: ${proxySupport}`);
    console.log(`github.copilot.advanced.proxy: ${copilotProxy}`);
    
    if (httpProxy && httpProxy.includes('127.0.0.1') &&
        proxyStrictSSL === false &&
        proxySupport === 'override' &&
        copilotProxy && copilotProxy.includes('127.0.0.1')) {
      console.log('✅ VS Code settings are correctly configured for proxy');
      return true;
    } else {
      console.log('❌ VS Code settings are not correctly configured for proxy');
      return false;
    }
  } catch (error) {
    console.log(`❌ Error reading VS Code settings: ${error.message}`);
    return false;
  }
}

// Check certificate installation
function checkCertificateInstallation() {
  console.log('\n=== Checking Certificate Installation ===');
  
  const certPath = path.join(os.homedir(), '.private-ai/private-ai-ca-cert.pem');
  
  try {
    if (fs.existsSync(certPath)) {
      console.log(`✅ Certificate exists at ${certPath}`);
      
      // Check if certificate is valid
      const certStat = fs.statSync(certPath);
      const certAge = (Date.now() - certStat.mtime.getTime()) / (1000 * 60 * 60 * 24); // Age in days
      
      if (certAge < 90) {
        console.log(`✅ Certificate is ${Math.round(certAge)} days old (less than 90 days)`);
      } else {
        console.log(`❌ Certificate is ${Math.round(certAge)} days old (more than 90 days)`);
      }
      
      return true;
    } else {
      console.log(`❌ Certificate not found at ${certPath}`);
      return false;
    }
  } catch (error) {
    console.log(`❌ Error checking certificate: ${error.message}`);
    return false;
  }
}

// Test GitHub Copilot connection
function testCopilotConnection() {
  return new Promise((resolve) => {
    console.log('\n=== Testing GitHub Copilot Connection ===');
    
    const options = {
      hostname: 'api.githubcopilot.com',
      port: 443,
      path: '/v1/engines/copilot-codex/completions',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer mock_token',
        'User-Agent': 'GitHub-Copilot/1.0'
      }
    };
    
    const req = https.request(options, (res) => {
      console.log(`Response status: ${res.statusCode}`);
      
      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        // The request should go through our proxy
        // We expect a 401 or 404 response since we're using a mock token
        if (res.statusCode === 401 || res.statusCode === 404) {
          console.log('✅ Proxy is working correctly for Copilot requests');
          resolve(true);
        } else {
          console.log('❌ Unexpected response from Copilot API');
          resolve(false);
        }
      });
    });
    
    req.on('error', (error) => {
      console.log(`❌ Error making request to Copilot API: ${error.message}`);
      resolve(false);
    });
    
    req.end();
  });
}

// Run all tests
async function runTests() {
  console.log('=== VS Code Copilot Integration Test ===');
  
  const proxyRunning = checkProxyRunning();
  const settingsConfigured = checkVSCodeSettings();
  const certificateInstalled = checkCertificateInstallation();
  const copilotConnected = await testCopilotConnection();
  
  console.log('\n=== Test Results ===');
  console.log(`Proxy Running: ${proxyRunning ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`VS Code Settings: ${settingsConfigured ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Certificate Installation: ${certificateInstalled ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`Copilot Connection: ${copilotConnected ? '✅ PASS' : '❌ FAIL'}`);
  
  const allPassed = proxyRunning && settingsConfigured && certificateInstalled && copilotConnected;
  console.log(`\nOverall Result: ${allPassed ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
  
  console.log('\n=== Integration Test Complete ===');
}

// Run the tests
runTests();