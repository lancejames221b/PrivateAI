const https = require('https');

// Set environment for Node.js to use our proxy
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0'; // Disable certificate validation
process.env.HTTP_PROXY = 'http://127.0.0.1:8080';
process.env.HTTPS_PROXY = 'http://127.0.0.1:8080';

// Copilot completions endpoint
const options = {
  hostname: 'copilot-proxy.githubusercontent.com',
  path: '/v1/engines/copilot-codex/completions',
  method: 'POST',
  headers: {
    'User-Agent': 'GitHubCopilot/1.93.0',
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE' // This will need to be replaced with a real token
  },
  rejectUnauthorized: false // Bypass certificate validation
};

console.log('Sending request to Copilot completions API through proxy...');

// Simple completion request
const requestData = JSON.stringify({
  "prompt": "// Simple function to add two numbers\nfunction add(a, b) {\n  ",
  "max_tokens": 50,
  "temperature": 0.5,
  "top_p": 1,
  "n": 1,
  "stop": ["\n\n"],
  "stream": false
});

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

req.write(requestData);
req.end(); 