#!/usr/bin/env python3
"""
Private AI 🕵️ - Trusted Proxy Script

This script sets up a proxy that automatically accepts all certificates
and handles GitHub Copilot requests.

Author: Lance James @ Unit 221B
"""

import os
import sys
import ssl
import certifi
import requests
from mitmproxy import http, ctx
from mitmproxy.net import tls

# Disable SSL verification warnings
requests.packages.urllib3.disable_warnings()

class TrustedProxy:
    """Proxy that automatically accepts all certificates"""
    
    def __init__(self):
        """Initialize the proxy"""
        self.copilot_hosts = [
            "api.githubcopilot.com",
            "copilot-proxy.githubusercontent.com",
            "api.github.com",
            "github.com",
            "api.business.githubcopilot.com",
            "telemetry.business.githubcopilot.com",
            "copilot-telemetry.githubusercontent.com"
        ]
        
        # Create a custom SSL context that accepts all certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # Log initialization
        ctx.log.info("Trusted Proxy initialized")
        ctx.log.info(f"Monitoring Copilot hosts: {', '.join(self.copilot_hosts)}")
    
    def request(self, flow: http.HTTPFlow) -> None:
        """Process an HTTP request"""
        # Log the request
        host = flow.request.host
        method = flow.request.method
        url = flow.request.url
        
        ctx.log.info(f"Request: {method} {url}")
        
        # Add custom headers for Copilot requests
        if host in self.copilot_hosts:
            ctx.log.info(f"Detected Copilot request to {host}")
            
            # Add custom headers
            flow.request.headers["X-Private-AI-Proxy"] = "true"
    
    def response(self, flow: http.HTTPFlow) -> None:
        """Process an HTTP response"""
        # Log the response
        host = flow.request.host
        method = flow.request.method
        url = flow.request.url
        status = flow.response.status_code
        
        ctx.log.info(f"Response: {method} {url} -> {status}")
        
        # Add custom headers for Copilot responses
        if host in self.copilot_hosts:
            ctx.log.info(f"Detected Copilot response from {host}")
            
            # Add custom headers
            flow.response.headers["X-Private-AI-Proxy"] = "true"

# Create an instance of the proxy
addons = [TrustedProxy()]

# Configure mitmproxy to accept all certificates
def configure(updated):
    """Configure mitmproxy"""
    ctx.options.ssl_insecure = True
    ctx.options.http2 = True
    ctx.options.upstream_cert = False
    ctx.options.confdir = os.path.expanduser("~/.private-ai")