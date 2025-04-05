#!/usr/bin/env python3
"""
Private AI 🕵️ - Proxy Base Module

This module provides the foundation for the modular, plugin-based proxy architecture.
It defines the base classes and interfaces for proxy plugins and handlers.

Author: Lance James @ Unit 221B
"""

import os
import sys
import json
import logging
import importlib
import pkgutil
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from mitmproxy import http, ctx

# Initialize logger
from logger import get_logger, log_exception
logger = get_logger("proxy-base", "logs/proxy_base.log")

class ProxyPlugin(ABC):
    """Base class for all proxy plugins"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize the plugin
        
        Args:
            config: Plugin configuration (optional)
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self.enabled = self.config.get("enabled", True)
        self.priority = self.config.get("priority", 50)  # Default priority (0-100, lower runs first)
        
        # Initialize plugin
        self.initialize()
        
    def initialize(self):
        """Initialize the plugin (can be overridden by subclasses)"""
        pass
    
    @abstractmethod
    def should_process_request(self, flow: http.HTTPFlow) -> bool:
        """
        Determine if this plugin should process the request
        
        Args:
            flow: The HTTP flow to check
            
        Returns:
            bool: True if this plugin should process the request, False otherwise
        """
        pass
    
    @abstractmethod
    def process_request(self, flow: http.HTTPFlow) -> None:
        """
        Process an HTTP request
        
        Args:
            flow: The HTTP flow to process
        """
        pass
    
    @abstractmethod
    def should_process_response(self, flow: http.HTTPFlow) -> bool:
        """
        Determine if this plugin should process the response
        
        Args:
            flow: The HTTP flow to check
            
        Returns:
            bool: True if this plugin should process the response, False otherwise
        """
        pass
    
    @abstractmethod
    def process_response(self, flow: http.HTTPFlow) -> None:
        """
        Process an HTTP response
        
        Args:
            flow: The HTTP flow to process
        """
        pass
    
    def get_info(self) -> Dict:
        """
        Get information about this plugin
        
        Returns:
            dict: Plugin information
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "priority": self.priority,
            "config": self.config
        }

class PluginManager:
    """Manager for proxy plugins"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the plugin manager
        
        Args:
            config_path: Path to plugin configuration file (optional)
        """
        self.plugins: List[ProxyPlugin] = []
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "plugins", "config.json")
        self.config = self._load_config()
        
        # Load plugins
        self._load_plugins()
        
    def _load_config(self) -> Dict:
        """
        Load plugin configuration from file
        
        Returns:
            dict: Plugin configuration
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log_exception(logger, e, "load_config")
        
        # Return default configuration if file doesn't exist or can't be read
        return {"plugins": {}}
    
    def _save_config(self) -> bool:
        """
        Save plugin configuration to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            log_exception(logger, e, "save_config")
            return False
    
    def _load_plugins(self) -> None:
        """Load all available plugins"""
        # Clear existing plugins
        self.plugins = []
        
        # Get plugin directory
        plugin_dir = os.path.join(os.path.dirname(__file__), "plugins")
        
        # Create plugin directory if it doesn't exist
        os.makedirs(plugin_dir, exist_ok=True)
        
        # Add plugin directory to path
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        # Load plugins from directory
        for _, name, is_pkg in pkgutil.iter_modules([plugin_dir]):
            if not is_pkg and name.endswith("_plugin"):
                try:
                    # Import plugin module
                    module = importlib.import_module(name)
                    
                    # Find plugin class (should be a subclass of ProxyPlugin)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, ProxyPlugin) and 
                            attr is not ProxyPlugin):
                            
                            # Get plugin configuration
                            plugin_config = self.config.get("plugins", {}).get(attr_name, {})
                            
                            # Create plugin instance
                            plugin = attr(plugin_config)
                            
                            # Add plugin to list
                            self.plugins.append(plugin)
                            
                            logger.info(f"Loaded plugin: {plugin.name}")
                except Exception as e:
                    log_exception(logger, e, f"load_plugin_{name}")
        
        # Sort plugins by priority
        self.plugins.sort(key=lambda p: p.priority)
        
        logger.info(f"Loaded {len(self.plugins)} plugins")
    
    def get_plugins(self) -> List[ProxyPlugin]:
        """
        Get all loaded plugins
        
        Returns:
            list: List of loaded plugins
        """
        return self.plugins
    
    def get_plugin(self, name: str) -> Optional[ProxyPlugin]:
        """
        Get a plugin by name
        
        Args:
            name: Plugin name
            
        Returns:
            ProxyPlugin: Plugin instance, or None if not found
        """
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        return None
    
    def enable_plugin(self, name: str) -> bool:
        """
        Enable a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if successful, False otherwise
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = True
            
            # Update configuration
            if "plugins" not in self.config:
                self.config["plugins"] = {}
            if name not in self.config["plugins"]:
                self.config["plugins"][name] = {}
            self.config["plugins"][name]["enabled"] = True
            
            # Save configuration
            self._save_config()
            
            logger.info(f"Enabled plugin: {name}")
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Disable a plugin
        
        Args:
            name: Plugin name
            
        Returns:
            bool: True if successful, False otherwise
        """
        plugin = self.get_plugin(name)
        if plugin:
            plugin.enabled = False
            
            # Update configuration
            if "plugins" not in self.config:
                self.config["plugins"] = {}
            if name not in self.config["plugins"]:
                self.config["plugins"][name] = {}
            self.config["plugins"][name]["enabled"] = False
            
            # Save configuration
            self._save_config()
            
            logger.info(f"Disabled plugin: {name}")
            return True
        return False
    
    def reload_plugins(self) -> None:
        """Reload all plugins"""
        self._load_plugins()
    
    def process_request(self, flow: http.HTTPFlow) -> None:
        """
        Process an HTTP request using all enabled plugins
        
        Args:
            flow: The HTTP flow to process
        """
        for plugin in self.plugins:
            if plugin.enabled and plugin.should_process_request(flow):
                try:
                    plugin.process_request(flow)
                except Exception as e:
                    log_exception(logger, e, f"process_request_{plugin.name}")
    
    def process_response(self, flow: http.HTTPFlow) -> None:
        """
        Process an HTTP response using all enabled plugins
        
        Args:
            flow: The HTTP flow to process
        """
        for plugin in self.plugins:
            if plugin.enabled and plugin.should_process_response(flow):
                try:
                    plugin.process_response(flow)
                except Exception as e:
                    log_exception(logger, e, f"process_response_{plugin.name}")

class ProxyServer:
    """Main proxy server class"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize the proxy server
        
        Args:
            config_path: Path to proxy configuration file (optional)
        """
        self.config_path = config_path or os.path.join(os.path.dirname(__file__), "config.json")
        self.config = self._load_config()
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(
            os.path.join(os.path.dirname(__file__), "plugins", "config.json")
        )
        
        logger.info("Proxy server initialized")
    
    def _load_config(self) -> Dict:
        """
        Load proxy configuration from file
        
        Returns:
            dict: Proxy configuration
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                log_exception(logger, e, "load_config")
        
        # Return default configuration if file doesn't exist or can't be read
        return {
            "port": 8080,
            "host": "127.0.0.1",
            "ssl_insecure": True,
            "certificate_dir": os.path.expanduser("~/.private-ai")
        }
    
    def _save_config(self) -> bool:
        """
        Save proxy configuration to file
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            return True
        except Exception as e:
            log_exception(logger, e, "save_config")
            return False
    
    def request(self, flow: http.HTTPFlow) -> None:
        """
        Process an HTTP request
        
        Args:
            flow: The HTTP flow to process
        """
        self.plugin_manager.process_request(flow)
    
    def response(self, flow: http.HTTPFlow) -> None:
        """
        Process an HTTP response
        
        Args:
            flow: The HTTP flow to process
        """
        self.plugin_manager.process_response(flow)
    
    def get_command_args(self) -> List[str]:
        """
        Get command-line arguments for mitmdump
        
        Returns:
            list: Command-line arguments
        """
        args = [
            "--set", f"confdir={self.config.get('certificate_dir', os.path.expanduser('~/.private-ai'))}",
            "--set", f"ssl_insecure={str(self.config.get('ssl_insecure', True)).lower()}",
            "-p", str(self.config.get("port", 8080)),
            "--listen-host", self.config.get("host", "127.0.0.1"),
            "-s", __file__  # Use this file as the script
        ]
        
        return args

# Global proxy server instance for mitmproxy
proxy_server = ProxyServer()

# Functions for mitmproxy to call
def request(flow: http.HTTPFlow) -> None:
    """mitmproxy request hook"""
    proxy_server.request(flow)

def response(flow: http.HTTPFlow) -> None:
    """mitmproxy response hook"""
    proxy_server.response(flow)