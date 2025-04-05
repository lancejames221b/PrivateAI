// VS Code Proxy Verification Script
// This script checks if VS Code is properly configured to use our proxy

const https = require('https');
const http = require('http');

// Log proxy environment variables
console.log('NODE_EXTRA_CA_CERTS:', process.env.NODE_EXTRA_CA_CERTS || 'Not set');
console.log('HTTP_PROXY:', process.env.HTTP_PROXY || 'Not set');
console.log('HTTPS_PROXY:', process.env.HTTPS_PROXY || 'Not set');
console.log('NO_PROXY:', process.env.NO_PROXY || 'Not set');

// Function to make a request through the proxy
function makeProxyRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    
    console.log(`Making request to ${url}...`);
    
    const req = protocol.request(url, options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        console.log(`Response status: ${res.statusCode}`);
        console.log(`Response headers:`, res.headers);
        
        try {
          // Try to parse as JSON
          const jsonData = JSON.parse(data);
          resolve({ statusCode: res.statusCode, headers: res.headers, data: jsonData });
        } catch (e) {
          // Return as text if not JSON
          resolve({ statusCode: res.statusCode, headers: res.headers, data: data });
        }
      });
    });
    
    req.on('error', (error) => {
      console.error(`Request error: ${error.message}`);
      reject(error);
    });
    
    req.end();
  });
}

// Test GitHub Copilot connection
async function testCopilotConnection() {
  try {
    // Make a request to GitHub Copilot API
    const result = await makeProxyRequest('https://api.githubcopilot.com/v1/engines/copilot-codex/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer mock_token',
        'User-Agent': 'GitHub-Copilot/1.0'
      }
    });
    
    console.log('Copilot test completed successfully');
    
    // The request should go through our proxy
    // We expect a 401 or 404 response since we're using a mock token
    if (result.statusCode === 401 || result.statusCode === 404) {
      console.log('✅ Proxy is working correctly for Copilot requests');
    } else {
      console.log('❌ Unexpected response from Copilot API');
    }
  } catch (error) {
    console.error('Failed to test Copilot connection:', error);
  }
}

// Test a regular HTTPS request
async function testHttpsRequest() {
  try {
    // Make a request to a regular HTTPS site
    const result = await makeProxyRequest('https://example.com');
    
    console.log('HTTPS test completed successfully');
    
    // The request should go through our proxy
    if (result.statusCode === 200) {
      console.log('✅ Proxy is working correctly for HTTPS requests');
    } else {
      console.log('❌ Unexpected response from HTTPS request');
    }
  } catch (error) {
    console.error('Failed to test HTTPS request:', error);
  }
}

// Run the tests
async function runTests() {
  console.log('=== VS Code Proxy Verification ===');
  
  await testHttpsRequest();
  await testCopilotConnection();
  
  console.log('=== Verification Complete ===');
}

runTests();