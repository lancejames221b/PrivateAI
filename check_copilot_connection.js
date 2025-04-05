const https = require('https');
const http = require('http');

// Set environment for Node.js to use our proxy
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // Disable certificate validation
process.env.HTTP_PROXY = 'http://127.0.0.1:8080';
process.env.HTTPS_PROXY = 'http://127.0.0.1:8080';

// GitHub Copilot endpoint
const options = {
  hostname: 'api.github.com',
  path: '/copilot_internal/v2/token',
  method: 'GET',
  headers: {
    'User-Agent': 'GitHubCopilot/1.0'
  },
  rejectUnauthorized: false // Also set in request options
};

console.log('Sending request to Copilot API through proxy...');

// Make the request
const req = https.request(options, (res) => {
  console.log(`STATUS: ${res.statusCode}`);
  console.log(`HEADERS: ${JSON.stringify(res.headers)}`);
  
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log('Response Body:');
    try {
      const parsedData = JSON.parse(data);
      console.log(JSON.stringify(parsedData, null, 2));
    } catch (e) {
      console.log(data);
    }
  });
});

req.on('error', (e) => {
  console.error(`Problem with request: ${e.message}`);
});

req.end(); 