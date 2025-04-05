import requests
import os

# Configure to use our proxy
proxies = {
    "http": "http://localhost:8080",
    "https": "http://localhost:8080"
}

# Disable SSL verification when using proxy
os.environ['REQUESTS_CA_BUNDLE'] = os.path.expanduser('~/.mitmproxy-fresh/mitmproxy-ca-cert.pem')

# Test GitHub API
print("Testing connection to GitHub API...")
try:
    response = requests.get("https://api.github.com/zen", proxies=proxies, verify=False)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
    print("SUCCESS: Connection successful through proxy")
except Exception as e:
    print(f"ERROR: {e}")

# Test Copilot endpoint
print("\nTesting connection to Copilot endpoint...")
try:
    response = requests.get("https://api.githubcopilot.com/status", proxies=proxies, verify=False)
    print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")
    print("SUCCESS: Connection successful through proxy")
except Exception as e:
    print(f"ERROR: {e}") 