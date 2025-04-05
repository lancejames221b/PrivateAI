#!/usr/bin/env python3
"""
Private AI 🕵️ - GitHub Copilot Privacy Plugin

This plugin extends the base Copilot plugin to add enhanced privacy protection
for GitHub Copilot by intercepting and transforming sensitive information in code
before it's sent to GitHub Copilot.

Author: Lance James @ Unit 221B
"""

import os
import json
import re
import uuid
import subprocess
import shutil
from typing import Dict, List, Any, Optional, Tuple, Union
from mitmproxy import http

from proxy_base import ProxyPlugin
from logger import get_logger, log_exception
from pii_transform import PIITransformer
from plugins.copilot_plugin import CopilotPlugin

# Initialize logger
logger = get_logger("copilot-privacy-plugin", "logs/copilot_privacy_plugin.log")

# Initialize PII transformer
pii_transformer = PIITransformer()

class CopilotPrivacyPlugin(CopilotPlugin):
    """Plugin for enhanced privacy protection for GitHub Copilot"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize the plugin
        
        Args:
            config: Plugin configuration (optional)
        """
        super().__init__(config)
        
        # Set priority (lower runs first)
        self.priority = 5  # Higher priority than base Copilot plugin
        
        # Plugin paths
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.plugin_dir, "scripts")
        self.docs_dir = os.path.join(self.plugin_dir, "docs")
        
        # Create directories if they don't exist
        os.makedirs(self.scripts_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Certificate paths
        self.cert_dir = os.path.expanduser("~/.mitmproxy")
        self.cert_path = os.path.join(self.cert_dir, "mitmproxy-ca-cert.pem")
        
        # Log directory
        self.log_dir = os.path.join(os.getcwd(), "proxy_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Privacy metrics
        self.privacy_metrics = {
            "requests_processed": 0,
            "responses_processed": 0,
            "pii_detected": 0,
            "pii_types": {}
        }
        
        logger.info(f"Copilot Privacy plugin initialized")
    
    def should_process_request(self, flow: http.HTTPFlow) -> bool:
        """
        Determine if this plugin should process the request
        
        Args:
            flow: The HTTP flow to check
            
        Returns:
            bool: True if this plugin should process the request, False otherwise
        """
        # Use the base Copilot plugin's detection logic
        return super().should_process_request(flow)
    
    def process_request(self, flow: http.HTTPFlow) -> None:
        """
        Process a Copilot request with enhanced privacy protection
        
        Args:
            flow: The HTTP flow to process
        """
        try:
            # Generate a unique request ID for tracking
            request_id = str(uuid.uuid4())
            flow.request.id = request_id
            
            logger.info(f"Processing Copilot request to {flow.request.host}{flow.request.path} (ID: {request_id})")
            
            # Try to parse the request as JSON
            try:
                content = flow.request.content.decode('utf-8', errors='ignore')
                request_data = json.loads(content)
                
                # Store original request for response handling
                self.request_map[request_id] = {
                    "original": request_data,
                    "host": flow.request.host,
                    "path": flow.request.path
                }
                
                # Apply enhanced PII transformation to the request
                transformed_data, pii_metrics = self._transform_request_with_metrics(request_data)
                
                # Update privacy metrics
                self.privacy_metrics["requests_processed"] += 1
                self.privacy_metrics["pii_detected"] += pii_metrics["pii_detected"]
                
                # Update PII types
                for pii_type, count in pii_metrics["pii_types"].items():
                    if pii_type in self.privacy_metrics["pii_types"]:
                        self.privacy_metrics["pii_types"][pii_type] += count
                    else:
                        self.privacy_metrics["pii_types"][pii_type] = count
                
                # Convert back to JSON and update the request
                flow.request.content = json.dumps(transformed_data).encode('utf-8')
                flow.request.headers["content-length"] = str(len(flow.request.content))
                
                logger.info(f"Successfully transformed Copilot request (ID: {request_id})")
                if pii_metrics["pii_detected"] > 0:
                    logger.info(f"Detected and transformed {pii_metrics['pii_detected']} instances of PII")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Non-JSON request or encoding error: {str(e)} (ID: {request_id})")
        except Exception as e:
            log_exception(logger, e, "process_request")
    
    def should_process_response(self, flow: http.HTTPFlow) -> bool:
        """
        Determine if this plugin should process the response
        
        Args:
            flow: The HTTP flow to check
            
        Returns:
            bool: True if this plugin should process the response, False otherwise
        """
        # Use the base Copilot plugin's detection logic
        return super().should_process_response(flow)
    
    def process_response(self, flow: http.HTTPFlow) -> None:
        """
        Process a Copilot response with enhanced privacy protection
        
        Args:
            flow: The HTTP flow to process
        """
        try:
            # Get the request ID
            request_id = getattr(flow.request, 'id', None)
            if not request_id or request_id not in self.request_map:
                return
            
            # Get the original request
            request_info = self.request_map.pop(request_id)
            
            logger.info(f"Processing Copilot response for request {request_id}")
            
            # Try to parse the response as JSON
            try:
                content = flow.response.content.decode('utf-8', errors='ignore')
                response_data = json.loads(content)
                
                # Apply enhanced PII transformation to the response
                transformed_data, pii_metrics = self._transform_response_with_metrics(response_data)
                
                # Update privacy metrics
                self.privacy_metrics["responses_processed"] += 1
                self.privacy_metrics["pii_detected"] += pii_metrics["pii_detected"]
                
                # Update PII types
                for pii_type, count in pii_metrics["pii_types"].items():
                    if pii_type in self.privacy_metrics["pii_types"]:
                        self.privacy_metrics["pii_types"][pii_type] += count
                    else:
                        self.privacy_metrics["pii_types"][pii_type] = count
                
                # Convert back to JSON and update the response
                flow.response.content = json.dumps(transformed_data).encode('utf-8')
                flow.response.headers["content-length"] = str(len(flow.response.content))
                
                logger.info(f"Successfully transformed Copilot response (ID: {request_id})")
                if pii_metrics["pii_detected"] > 0:
                    logger.info(f"Detected and transformed {pii_metrics['pii_detected']} instances of PII")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Non-JSON response or encoding error: {str(e)} (ID: {request_id})")
        except Exception as e:
            log_exception(logger, e, "process_response")
    
    def _transform_request_with_metrics(self, request_data: Dict) -> Tuple[Dict, Dict]:
        """
        Apply PII transformation to the request data and track metrics
        
        Args:
            request_data: The request data to transform
            
        Returns:
            tuple: (transformed_data, metrics)
        """
        # Initialize metrics
        metrics = {
            "pii_detected": 0,
            "pii_types": {}
        }
        
        # Clone the request data
        transformed_data = json.loads(json.dumps(request_data))
        
        # Handle Copilot-specific request formats
        
        # Handle completions request
        if 'prompt' in transformed_data and isinstance(transformed_data['prompt'], str):
            original = transformed_data['prompt']
            transformed_data['prompt'] = pii_transformer.transform_text(original)
            
            # Count PII instances
            if original != transformed_data['prompt']:
                metrics["pii_detected"] += 1
                metrics["pii_types"]["prompt"] = metrics["pii_types"].get("prompt", 0) + 1
        
        # Handle chat completions request
        if 'messages' in transformed_data and isinstance(transformed_data['messages'], list):
            for message in transformed_data['messages']:
                if 'content' in message and isinstance(message['content'], str):
                    original = message['content']
                    message['content'] = pii_transformer.transform_text(original)
                    
                    # Count PII instances
                    if original != message['content']:
                        metrics["pii_detected"] += 1
                        metrics["pii_types"]["message"] = metrics["pii_types"].get("message", 0) + 1
        
        # Handle Copilot code context
        if 'source' in transformed_data and isinstance(transformed_data['source'], str):
            original = transformed_data['source']
            transformed_data['source'] = pii_transformer.transform_text(original)
            
            # Count PII instances
            if original != transformed_data['source']:
                metrics["pii_detected"] += 1
                metrics["pii_types"]["source"] = metrics["pii_types"].get("source", 0) + 1
        
        # Handle Copilot document context
        if 'document' in transformed_data:
            if isinstance(transformed_data['document'], str):
                original = transformed_data['document']
                transformed_data['document'] = pii_transformer.transform_text(original)
                
                # Count PII instances
                if original != transformed_data['document']:
                    metrics["pii_detected"] += 1
                    metrics["pii_types"]["document"] = metrics["pii_types"].get("document", 0) + 1
            elif isinstance(transformed_data['document'], dict) and 'content' in transformed_data['document']:
                if isinstance(transformed_data['document']['content'], str):
                    original = transformed_data['document']['content']
                    transformed_data['document']['content'] = pii_transformer.transform_text(original)
                    
                    # Count PII instances
                    if original != transformed_data['document']['content']:
                        metrics["pii_detected"] += 1
                        metrics["pii_types"]["document_content"] = metrics["pii_types"].get("document_content", 0) + 1
        
        # Handle prefix/suffix format
        if 'prefix' in transformed_data and isinstance(transformed_data['prefix'], str):
            original = transformed_data['prefix']
            transformed_data['prefix'] = pii_transformer.transform_text(original)
            
            # Count PII instances
            if original != transformed_data['prefix']:
                metrics["pii_detected"] += 1
                metrics["pii_types"]["prefix"] = metrics["pii_types"].get("prefix", 0) + 1
        
        if 'suffix' in transformed_data and isinstance(transformed_data['suffix'], str):
            original = transformed_data['suffix']
            transformed_data['suffix'] = pii_transformer.transform_text(original)
            
            # Count PII instances
            if original != transformed_data['suffix']:
                metrics["pii_detected"] += 1
                metrics["pii_types"]["suffix"] = metrics["pii_types"].get("suffix", 0) + 1
        
        return transformed_data, metrics
    
    def _transform_response_with_metrics(self, response_data: Dict) -> Tuple[Dict, Dict]:
        """
        Apply PII transformation to the response data and track metrics
        
        Args:
            response_data: The response data to transform
            
        Returns:
            tuple: (transformed_data, metrics)
        """
        # Initialize metrics
        metrics = {
            "pii_detected": 0,
            "pii_types": {}
        }
        
        # Clone the response data
        transformed_data = json.loads(json.dumps(response_data))
        
        # Handle Copilot-specific response formats
        
        # Handle completions response
        if 'choices' in transformed_data and isinstance(transformed_data['choices'], list):
            for choice in transformed_data['choices']:
                if 'text' in choice and isinstance(choice['text'], str):
                    original = choice['text']
                    choice['text'] = pii_transformer.transform_text(original)
                    
                    # Count PII instances
                    if original != choice['text']:
                        metrics["pii_detected"] += 1
                        metrics["pii_types"]["choice_text"] = metrics["pii_types"].get("choice_text", 0) + 1
                
                if 'message' in choice and 'content' in choice['message']:
                    if isinstance(choice['message']['content'], str):
                        original = choice['message']['content']
                        choice['message']['content'] = pii_transformer.transform_text(original)
                        
                        # Count PII instances
                        if original != choice['message']['content']:
                            metrics["pii_detected"] += 1
                            metrics["pii_types"]["message_content"] = metrics["pii_types"].get("message_content", 0) + 1
        
        # Handle Copilot completions response
        if 'completions' in transformed_data and isinstance(transformed_data['completions'], list):
            for completion in transformed_data['completions']:
                if 'text' in completion and isinstance(completion['text'], str):
                    original = completion['text']
                    completion['text'] = pii_transformer.transform_text(original)
                    
                    # Count PII instances
                    if original != completion['text']:
                        metrics["pii_detected"] += 1
                        metrics["pii_types"]["completion_text"] = metrics["pii_types"].get("completion_text", 0) + 1
        
        # Handle direct text response
        if 'text' in transformed_data and isinstance(transformed_data['text'], str):
            original = transformed_data['text']
            transformed_data['text'] = pii_transformer.transform_text(original)
            
            # Count PII instances
            if original != transformed_data['text']:
                metrics["pii_detected"] += 1
                metrics["pii_types"]["text"] = metrics["pii_types"].get("text", 0) + 1
        
        return transformed_data, metrics
    
    def get_privacy_metrics(self) -> Dict:
        """
        Get privacy metrics
        
        Returns:
            dict: Privacy metrics
        """
        return self.privacy_metrics
    
    def reset_privacy_metrics(self) -> None:
        """Reset privacy metrics"""
        self.privacy_metrics = {
            "requests_processed": 0,
            "responses_processed": 0,
            "pii_detected": 0,
            "pii_types": {}
        }
    
    def install_certificate(self) -> bool:
        """
        Install the mitmproxy certificate
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if certificate exists
            if not os.path.exists(self.cert_path):
                logger.warning(f"Certificate not found at {self.cert_path}")
                return False
            
            # Install certificate based on platform
            platform = os.name
            if platform == "posix":
                # macOS or Linux
                if os.path.exists("/usr/bin/security"):
                    # macOS
                    logger.info("Installing certificate in macOS system keychain...")
                    subprocess.run([
                        "sudo", "security", "add-trusted-cert", 
                        "-d", "-r", "trustRoot",
                        "-k", "/Library/Keychains/System.keychain",
                        self.cert_path
                    ], check=True)
                else:
                    # Linux
                    logger.info("Installing certificate in Linux system trust store...")
                    if os.path.exists("/usr/local/share/ca-certificates/"):
                        # Debian/Ubuntu
                        cert_dest = "/usr/local/share/ca-certificates/mitmproxy-ca.crt"
                        subprocess.run(["sudo", "cp", self.cert_path, cert_dest], check=True)
                        subprocess.run(["sudo", "update-ca-certificates"], check=True)
                    elif os.path.exists("/etc/pki/ca-trust/source/anchors/"):
                        # RHEL/CentOS/Fedora
                        cert_dest = "/etc/pki/ca-trust/source/anchors/mitmproxy-ca.crt"
                        subprocess.run(["sudo", "cp", self.cert_path, cert_dest], check=True)
                        subprocess.run(["sudo", "update-ca-trust", "extract"], check=True)
            elif platform == "nt":
                # Windows
                logger.info("Installing certificate in Windows certificate store...")
                subprocess.run([
                    "certutil", "-addstore", "ROOT", self.cert_path
                ], check=True)
            
            # Install certificate in VS Code
            vscode_cert_dir = os.path.expanduser("~/Library/Application Support/Code/User/certificates")
            os.makedirs(vscode_cert_dir, exist_ok=True)
            shutil.copy(self.cert_path, vscode_cert_dir)
            
            logger.info("Certificate installed successfully")
            return True
        except Exception as e:
            log_exception(logger, e, "install_certificate")
            return False
    
    def get_info(self) -> Dict:
        """
        Get information about this plugin
        
        Returns:
            dict: Plugin information
        """
        info = super().get_info()
        info.update({
            "privacy_metrics": self.privacy_metrics
        })
        return info