#!/usr/bin/env python3
"""
Private AI 🕵️ - Enhanced Logging and Error Handling

This module provides enhanced logging and error handling capabilities for the
Private AI proxy system. It includes structured logging, error recovery mechanisms,
and diagnostic tools.

Author: Lance James @ Unit 221B
"""

import os
import sys
import logging
import traceback
import json
import datetime
import platform
import socket
import uuid
import threading
import queue
import signal
import atexit
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

class EnhancedLogger:
    """Enhanced logger with structured logging and error recovery"""
    
    def __init__(self, name: str, log_file: str = None, console: bool = True, 
                 level: int = logging.INFO, max_file_size: int = 10485760, 
                 backup_count: int = 5, json_format: bool = False):
        """
        Initialize the enhanced logger
        
        Args:
            name: Logger name
            log_file: Path to log file (optional)
            console: Whether to log to console (default: True)
            level: Logging level (default: INFO)
            max_file_size: Maximum log file size in bytes (default: 10MB)
            backup_count: Number of backup log files to keep (default: 5)
            json_format: Whether to use JSON format for logs (default: False)
        """
        self.name = name
        self.log_file = log_file
        self.console = console
        self.level = level
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.json_format = json_format
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create formatters
        if json_format:
            self.formatter = self._create_json_formatter()
        else:
            self.formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self.formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if log file is specified
        if log_file:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            # Create rotating file handler
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size,
                backupCount=backup_count
            )
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
        
        # Error queue for asynchronous error handling
        self.error_queue = queue.Queue()
        
        # Start error handler thread
        self.error_handler_thread = threading.Thread(
            target=self._error_handler_loop,
            daemon=True
        )
        self.error_handler_thread.start()
        
        # Register cleanup handler
        atexit.register(self.cleanup)
        
        # Log initialization
        self.logger.info(f"Enhanced logger initialized: {name}")
    
    # Convenience methods to directly access the underlying logger
    def info(self, message: str) -> None:
        """Log an info message"""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message"""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message"""
        self.logger.error(message)
    
    def debug(self, message: str) -> None:
        """Log a debug message"""
        self.logger.debug(message)
    
    def _create_json_formatter(self) -> logging.Formatter:
        """
        Create a JSON formatter for structured logging
        
        Returns:
            logging.Formatter: JSON formatter
        """
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                    "process": record.process,
                    "thread": record.thread,
                    "hostname": socket.gethostname()
                }
                
                # Add exception info if available
                if record.exc_info:
                    log_data["exception"] = {
                        "type": record.exc_info[0].__name__,
                        "message": str(record.exc_info[1]),
                        "traceback": traceback.format_exception(*record.exc_info)
                    }
                
                return json.dumps(log_data)
        
        return JsonFormatter()
    
    def _error_handler_loop(self) -> None:
        """Error handler loop for asynchronous error handling"""
        while True:
            try:
                # Get error from queue
                error_info = self.error_queue.get()
                
                # Process error
                self._process_error(error_info)
                
                # Mark task as done
                self.error_queue.task_done()
            except Exception as e:
                # Log error in error handler
                self.logger.error(f"Error in error handler: {str(e)}")
                traceback.print_exc()
    
    def _process_error(self, error_info: Dict) -> None:
        """
        Process an error
        
        Args:
            error_info: Error information
        """
        # Log error
        self.logger.error(
            f"Error in {error_info.get('function', 'unknown')}: {error_info.get('error', 'unknown')}"
        )
        
        # Log traceback if available
        if 'traceback' in error_info:
            self.logger.error(f"Traceback: {error_info['traceback']}")
        
        # Execute recovery function if available
        recovery_func = error_info.get('recovery_func')
        if recovery_func and callable(recovery_func):
            try:
                recovery_func()
                self.logger.info(f"Recovery function executed for {error_info.get('function', 'unknown')}")
            except Exception as e:
                self.logger.error(f"Error in recovery function: {str(e)}")
                traceback.print_exc()
    
    def log_exception(self, exception: Exception, function_name: str, 
                      recovery_func: Callable = None) -> None:
        """
        Log an exception
        
        Args:
            exception: Exception to log
            function_name: Name of the function where the exception occurred
            recovery_func: Recovery function to execute (optional)
        """
        # Create error information
        error_info = {
            'error': str(exception),
            'function': function_name,
            'traceback': traceback.format_exc(),
            'timestamp': datetime.datetime.now().isoformat(),
            'recovery_func': recovery_func
        }
        
        # Add error to queue for asynchronous processing
        self.error_queue.put(error_info)
    
    def get_system_info(self) -> Dict:
        """
        Get system information for diagnostics
        
        Returns:
            dict: System information
        """
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'hostname': socket.gethostname(),
            'processor': platform.processor(),
            'memory': self._get_memory_info(),
            'disk': self._get_disk_info(),
            'network': self._get_network_info()
        }
    
    def _get_memory_info(self) -> Dict:
        """
        Get memory information
        
        Returns:
            dict: Memory information
        """
        try:
            import psutil
            vm = psutil.virtual_memory()
            return {
                'total': vm.total,
                'available': vm.available,
                'used': vm.used,
                'percent': vm.percent
            }
        except ImportError:
            return {'error': 'psutil not installed'}
    
    def _get_disk_info(self) -> Dict:
        """
        Get disk information
        
        Returns:
            dict: Disk information
        """
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except ImportError:
            return {'error': 'psutil not installed'}
    
    def _get_network_info(self) -> Dict:
        """
        Get network information
        
        Returns:
            dict: Network information
        """
        try:
            import psutil
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv
            }
        except ImportError:
            return {'error': 'psutil not installed'}
    
    def log_diagnostic(self, message: str, data: Dict = None) -> None:
        """
        Log diagnostic information
        
        Args:
            message: Diagnostic message
            data: Additional diagnostic data (optional)
        """
        # Create diagnostic information
        diagnostic_info = {
            'message': message,
            'timestamp': datetime.datetime.now().isoformat(),
            'system_info': self.get_system_info()
        }
        
        # Add additional data if provided
        if data:
            diagnostic_info['data'] = data
        
        # Log diagnostic information
        if self.json_format:
            self.logger.info(json.dumps(diagnostic_info))
        else:
            self.logger.info(f"DIAGNOSTIC: {message}")
            if data:
                self.logger.info(f"DIAGNOSTIC DATA: {json.dumps(data, indent=2)}")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        # Wait for error queue to be empty
        try:
            self.error_queue.join(timeout=1.0)
        except:
            pass
        
        # Log cleanup
        self.logger.info(f"Enhanced logger cleaned up: {self.name}")

# Global logger instances
_loggers = {}

def get_logger(name: str, log_file: str = None, console: bool = True, 
               level: int = logging.INFO, max_file_size: int = 10485760, 
               backup_count: int = 5, json_format: bool = False) -> EnhancedLogger:
    """
    Get or create an enhanced logger
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        console: Whether to log to console (default: True)
        level: Logging level (default: INFO)
        max_file_size: Maximum log file size in bytes (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
        json_format: Whether to use JSON format for logs (default: False)
        
    Returns:
        EnhancedLogger: Enhanced logger instance
    """
    global _loggers
    
    # Return existing logger if available
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = EnhancedLogger(
        name=name,
        log_file=log_file,
        console=console,
        level=level,
        max_file_size=max_file_size,
        backup_count=backup_count,
        json_format=json_format
    )
    
    # Store logger
    _loggers[name] = logger
    
    return logger

def log_exception(logger: logging.Logger, exception: Exception, function_name: str, 
                  recovery_func: Callable = None) -> None:
    """
    Log an exception
    
    Args:
        logger: Logger instance (can be standard logging.Logger or EnhancedLogger.logger)
        exception: Exception to log
        function_name: Name of the function where the exception occurred
        recovery_func: Recovery function to execute (optional)
    """
    # Check if logger is an EnhancedLogger
    if hasattr(logger, 'log_exception') and callable(logger.log_exception):
        logger.log_exception(exception, function_name, recovery_func)
    else:
        # Standard logging
        logger.error(f"Error in {function_name}: {str(exception)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Execute recovery function if available
        if recovery_func and callable(recovery_func):
            try:
                recovery_func()
                logger.info(f"Recovery function executed for {function_name}")
            except Exception as e:
                logger.error(f"Error in recovery function: {str(e)}")
                traceback.print_exc()

def setup_global_exception_handler() -> None:
    """Set up global exception handler"""
    # Create default logger
    default_logger = get_logger("global", "logs/global.log")
    
    # Original excepthook
    original_excepthook = sys.excepthook
    
    # Global exception handler
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        # Log exception
        default_logger.log_exception(
            exc_value,
            "global",
            None
        )
        
        # Call original excepthook
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    # Set global exception handler
    sys.excepthook = global_exception_handler
    
    # Log setup
    default_logger.logger.info("Global exception handler set up")

# Set up global exception handler
setup_global_exception_handler()