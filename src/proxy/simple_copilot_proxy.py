from mitmproxy import http, ctx
import sys

def load(loader):
    print("Simple Copilot Proxy Loaded - Monitoring traffic", file=sys.stderr)

def request(flow: http.HTTPFlow) -> None:
    host = flow.request.host
    url = flow.request.url
    method = flow.request.method
    
    if "github" in host or "copilot" in host:
        print(f"REQUEST: {method} {url}", file=sys.stderr)
        print(f"Headers: {dict(flow.request.headers)}", file=sys.stderr)

def response(flow: http.HTTPFlow) -> None:
    host = flow.request.host
    url = flow.request.url
    status = flow.response.status_code
    
    if "github" in host or "copilot" in host:
        print(f"RESPONSE: {url} -> {status}", file=sys.stderr)
        print(f"Response Headers: {dict(flow.response.headers)}", file=sys.stderr) 