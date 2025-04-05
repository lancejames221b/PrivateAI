#!/usr/bin/env python3
"""
Private AI Proxy Service Controller
This script manages the Private AI Proxy service, including:
- Downloading transformer models before starting the proxy
- Starting and stopping the proxy service
- Managing environment variables

Run with --download to download models without starting the proxy
Run with --start to start the proxy
Run with --stop to stop the proxy
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("proxy-service")

def download_models():
    """Download transformer models if not already downloaded"""
    logger.info("Checking for transformer models...")
    
    # Check if models are already downloaded
    model_dir = Path("models")
    if model_dir.exists():
        bert_ner_path = model_dir / "bert-base-NER"
        piiranha_path = model_dir / "piiranha-v1-detect-personal-information"
        
        if bert_ner_path.exists() and piiranha_path.exists():
            logger.info("Models already downloaded!")
            return True
    
    # Models not found, download them
    logger.info("Models not found or incomplete. Downloading...")
    
    # Ensure proxy is not running during download
    proxy_pid = get_proxy_pid()
    if proxy_pid:
        logger.warning("Proxy is running. Stopping it temporarily to download models...")
        stop_proxy()
        time.sleep(2)  # Give it time to fully stop
    
    # Clear proxy environment variables for the download process
    env = os.environ.copy()
    env.pop("http_proxy", None)
    env.pop("https_proxy", None)
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    
    # Run the download script
    download_script = Path("scripts/download_transformers_models.py")
    if not download_script.exists():
        logger.error(f"Download script not found at {download_script}")
        return False
    
    try:
        logger.info("Running model download script...")
        result = subprocess.run(
            [sys.executable, str(download_script)],
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error downloading models: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

def get_proxy_pid():
    """Check if proxy is running and return its PID if found"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python.*app.py"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout.strip():
            return result.stdout.strip()
        return None
    except Exception as e:
        logger.error(f"Error checking proxy process: {e}")
        return None

def stop_proxy():
    """Stop the running proxy service"""
    proxy_pid = get_proxy_pid()
    if not proxy_pid:
        logger.info("Proxy is not running.")
        return True
    
    logger.info(f"Found running proxy with PID {proxy_pid}. Stopping...")
    try:
        subprocess.run(["kill", proxy_pid], check=True)
        logger.info("Proxy stopped successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error stopping proxy: {e}")
        return False

def start_proxy():
    """Start the proxy service"""
    # Check if proxy is already running
    if get_proxy_pid():
        logger.info("Proxy is already running.")
        return True
    
    # Download models first
    logger.info("Ensuring models are downloaded before starting proxy...")
    if not download_models():
        logger.warning("Model download process didn't complete successfully, but continuing with proxy start.")
    
    # Start the proxy
    logger.info("Starting proxy service...")
    try:
        # Start in background
        subprocess.Popen(
            [sys.executable, "app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Wait to confirm it started
        time.sleep(3)
        if get_proxy_pid():
            logger.info("Proxy started successfully!")
            return True
        else:
            logger.error("Proxy failed to start properly.")
            return False
    except Exception as e:
        logger.error(f"Error starting proxy: {e}")
        return False

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Private AI Proxy Service Manager")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--download", action="store_true", help="Download transformer models only")
    group.add_argument("--start", action="store_true", help="Download models and start the proxy")
    group.add_argument("--stop", action="store_true", help="Stop the running proxy")
    group.add_argument("--status", action="store_true", help="Check proxy status")
    group.add_argument("--restart", action="store_true", help="Restart the proxy")
    return parser.parse_args()

def main():
    """Main function to handle command line arguments"""
    args = parse_args()
    
    if args.download:
        if download_models():
            logger.info("✓ Models downloaded successfully!")
            return 0
        else:
            logger.error("× Failed to download models.")
            return 1
            
    elif args.start:
        if start_proxy():
            logger.info("✓ Proxy started successfully!")
            return 0
        else:
            logger.error("× Failed to start proxy.")
            return 1
            
    elif args.stop:
        if stop_proxy():
            logger.info("✓ Proxy stopped successfully!")
            return 0
        else:
            logger.error("× Failed to stop proxy.")
            return 1
            
    elif args.status:
        proxy_pid = get_proxy_pid()
        if proxy_pid:
            logger.info(f"✓ Proxy is running with PID {proxy_pid}")
            return 0
        else:
            logger.info("× Proxy is not running")
            return 1
            
    elif args.restart:
        logger.info("Restarting proxy...")
        stop_proxy()
        time.sleep(2)  # Give it time to fully stop
        if start_proxy():
            logger.info("✓ Proxy restarted successfully!")
            return 0
        else:
            logger.error("× Failed to restart proxy.")
            return 1

if __name__ == "__main__":
    sys.exit(main()) 