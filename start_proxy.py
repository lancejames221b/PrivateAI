#!/usr/bin/env python3
"""
Private AI 🕵️ - Proxy Server Starter

This script starts the proxy server for testing purposes.

Author: Lance James @ Unit 221B
"""

import os
import sys
import subprocess
import time
import argparse
from enhanced_logger import get_logger

# Initialize logger
logger = get_logger("proxy-starter", "logs/proxy_starter.log")

def start_proxy(port=8080, host="127.0.0.1", script="proxy_base.py"):
    """
    Start the proxy server
    
    Args:
        port: Port to listen on (default: 8080)
        host: Host to listen on (default: 127.0.0.1)
        script: Script to use (default: proxy_base.py)
        
    Returns:
        subprocess.Popen: Proxy process
    """
    # Create certificate directory if it doesn't exist
    cert_dir = os.path.expanduser("~/.private-ai")
    os.makedirs(cert_dir, exist_ok=True)
    
    # Build command
    cmd = [
        "mitmdump",
        "--set", f"confdir={cert_dir}",
        "--set", "ssl_insecure=true",
        "-p", str(port),
        "--listen-host", host,
        "-s", script
    ]
    
    # Start proxy
    logger.info(f"Starting proxy: {' '.join(cmd)}")
    proxy_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for proxy to start
    time.sleep(2)
    
    # Check if proxy is running
    if proxy_process.poll() is not None:
        stderr = proxy_process.stderr.read()
        logger.error(f"Proxy failed to start: {stderr}")
        return None
    
    logger.info(f"Proxy started on {host}:{port}")
    return proxy_process

def main():
    """Main function"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the proxy server")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--host", "-H", default="127.0.0.1", help="Host to listen on")
    parser.add_argument("--script", "-s", default="proxy_base.py", help="Script to use")
    args = parser.parse_args()
    
    # Start proxy
    proxy_process = start_proxy(args.port, args.host, args.script)
    if not proxy_process:
        logger.error("Failed to start proxy")
        sys.exit(1)
    
    # Keep running until interrupted
    try:
        logger.info("Proxy server running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        # Stop proxy
        if proxy_process:
            proxy_process.terminate()
            try:
                proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proxy_process.kill()
            logger.info("Proxy stopped")

if __name__ == "__main__":
    main()