const https = require('https');
const fs = require('fs');
const path = require('path');

// Path to our mitmproxy certificate
const certPath = path.join(process.env.HOME, '.mitmproxy-fresh', 'mitmproxy-ca-cert.pem');
const cert = fs.readFileSync(certPath);

// Configure process-wide environment variable to trust this certificate
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
process.env.NODE_EXTRA_CA_CERTS = certPath;

// Configure proxy
const proxy = 'http://127.0.0.1:8080';
process.env.HTTP_PROXY = proxy;
process.env.HTTPS_PROXY = proxy;

// Options for GitHub API request
const githubOptions = {
  hostname: 'api.github.com',
  path: '/zen',
  method: 'GET',
  headers: {
    'User-Agent': 'VSCode-Copilot-Test/1.0'
  }
};

// Options for Copilot API request
const copilotOptions = {
  hostname: 'api.githubcopilot.com',
  path: '/status',
  method: 'GET',
  headers: {
    'User-Agent': 'VSCode-Copilot-Test/1.0'
  }
};

// Make a request to GitHub API
console.log('Testing connection to GitHub API...');
const req = https.request(githubOptions, (res) => {
  console.log(`Status code: ${res.statusCode}`);
  
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log(`Response data: ${data}`);
    
    // Test Copilot endpoint
    console.log('\nTesting connection to Copilot endpoint...');
    const req2 = https.request(copilotOptions, (res2) => {
      console.log(`Status code: ${res2.statusCode}`);
      
      let data2 = '';
      res2.on('data', (chunk) => {
        data2 += chunk;
      });
      
      res2.on('end', () => {
        console.log(`Response data: ${data2}`);
      });
    });

    req2.on('error', (e) => {
      console.error(`Got error: ${e.message}`);
    });
    
    req2.end();
  });
});

req.on('error', (e) => {
  console.error(`Got error: ${e.message}`);
});

req.end(); 