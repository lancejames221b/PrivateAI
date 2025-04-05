#!/usr/bin/env python3
from mitmproxy import http
import os
import json
import logging
from mitmproxy import ctx

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("copilot_proxy.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define the domains we're interested in
COPILOT_DOMAINS = [
    "api.github.com",
    "github.com",
    "api.githubcopilot.com",
    "copilot-proxy.githubusercontent.com",
    "githubcopilot.com",
    "default.exp-tas.com"
]

def load(loader):
    logger.info("Loading proxy script with enhanced Copilot logging")

def request(flow: http.HTTPFlow) -> None:
    host = flow.request.host
    
    # Log all requests to github.com or api.github.com
    if "github.com" in host or "copilot" in host:
        logger.info(f"REQUEST: {flow.request.method} {flow.request.url}")
        logger.info(f"Headers: {dict(flow.request.headers)}")
        
        if flow.request.content:
            try:
                body = flow.request.content.decode('utf-8')
                # Try to parse as JSON for better logging
                try:
                    body_json = json.loads(body)
                    logger.info(f"Body (JSON): {json.dumps(body_json, indent=2)}")
                except:
                    # If not JSON, log as plain text
                    logger.info(f"Body: {body[:1000]}...")
            except:
                logger.info(f"Binary body: {len(flow.request.content)} bytes")

def response(flow: http.HTTPFlow) -> None:
    host = flow.request.host
    
    # Log all responses from github.com or api.github.com
    if "github.com" in host or "copilot" in host:
        logger.info(f"RESPONSE: {flow.request.method} {flow.request.url} -> {flow.response.status_code}")
        logger.info(f"Response Headers: {dict(flow.response.headers)}")
        
        if flow.response.content:
            try:
                body = flow.response.content.decode('utf-8')
                # Try to parse as JSON for better logging
                try:
                    body_json = json.loads(body)
                    logger.info(f"Response Body (JSON): {json.dumps(body_json, indent=2)}")
                except:
                    # If not JSON, log as plain text if not too large
                    if len(body) < 5000:
                        logger.info(f"Response Body: {body}")
                    else:
                        logger.info(f"Response Body (large): {len(body)} bytes")
            except:
                logger.info(f"Binary response body: {len(flow.response.content)} bytes") 