#!/usr/bin/env python3
"""
Private AI 🕵️ - Simple Proxy Script

This is a simplified proxy script for testing purposes.

Author: Lance James @ Unit 221B
"""

from mitmproxy import http

def request(flow: http.HTTPFlow) -> None:
    """Process an HTTP request"""
    print(f"Request: {flow.request.method} {flow.request.url}")

def response(flow: http.HTTPFlow) -> None:
    """Process an HTTP response"""
    print(f"Response: {flow.request.method} {flow.request.url} -> {flow.response.status_code}")