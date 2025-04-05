from mitmproxy import http
import json
import os
import time

# Create logs directory if it doesn't exist
log_dir = "proxy_logs"
os.makedirs(log_dir, exist_ok=True)

# Initialize log file
log_file_path = os.path.join(log_dir, f"proxy_log_{int(time.time())}.txt")
with open(log_file_path, "w") as f:
    f.write(f"Proxy logging started at {time.ctime()}\n")
    f.write("-" * 50 + "\n\n")

def log_request(flow):
    """Log request details to file"""
    with open(log_file_path, "a") as f:
        f.write(f"REQUEST: {flow.request.method} {flow.request.url}\n")
        f.write(f"Headers:\n")
        for key, value in flow.request.headers.items():
            # Avoid logging sensitive headers
            if key.lower() not in ["authorization", "cookie"]:
                f.write(f"  {key}: {value}\n")
        f.write("\n")

def log_response(flow):
    """Log response details to file"""
    with open(log_file_path, "a") as f:
        f.write(f"RESPONSE: {flow.response.status_code} {flow.response.reason}\n")
        f.write(f"Headers:\n")
        for key, value in flow.response.headers.items():
            f.write(f"  {key}: {value}\n")
        
        # Try to parse and log JSON content (limit size)
        if flow.response.headers.get("content-type", "").startswith("application/json"):
            try:
                content = flow.response.content.decode("utf-8")
                if len(content) > 500:
                    content = content[:500] + "... [truncated]"
                f.write(f"Body (truncated):\n{content}\n")
            except:
                f.write("Could not decode response body\n")
        
        f.write("-" * 50 + "\n\n")

def request(flow: http.HTTPFlow) -> None:
    """Process requests"""
    # Log all requests
    log_request(flow)
    # Print console feedback for immediate visibility
    print(f"REQ: {flow.request.method} {flow.request.url}")

def response(flow: http.HTTPFlow) -> None:
    """Process responses"""
    # Log all responses
    log_response(flow)
    # Print to console for immediate feedback
    print(f"RESP: {flow.request.method} {flow.request.url} → {flow.response.status_code}") 