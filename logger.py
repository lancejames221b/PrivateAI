"""
Private AI 🕵️ - Centralized Logging Module

This module provides a consistent logging framework for the Private AI system.
It configures loggers with appropriate handlers and formatting for different components.

Author: Lance James @ Unit 221B
"""

import os
import logging
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Define log levels
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def get_logger(name, log_file=None, level=None):
    """
    Get a configured logger with consistent formatting and handlers.
    
    Args:
        name (str): Name of the logger
        log_file (str, optional): Path to the log file. If None, uses name.log
        level (str, optional): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                              If None, uses the LOG_LEVEL environment variable or defaults to INFO
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Get log level from parameter, environment, or default to INFO
    if level:
        log_level_name = level.upper()
    else:
        log_level_name = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    log_level = LOG_LEVELS.get(log_level_name, logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates when called multiple times
    if logger.handlers:
        logger.handlers.clear()
    
    # Determine log file path
    if not log_file:
        log_file = f"logs/{name.replace(' ', '_').lower()}.log"
    
    # Configure handlers
    handlers = []
    
    # Add rotating file handler (10MB max size, keep 5 backup files)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        handlers.append(file_handler)
    except Exception as e:
        # Fallback to basic file handler if rotation fails
        print(f"Warning: Could not create rotating file handler: {str(e)}")
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            handlers.append(file_handler)
        except Exception as e2:
            print(f"Error: Could not create file handler: {str(e2)}")
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Apply formatter to all handlers and add them to the logger
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_exception(logger, exc, context=None):
    """
    Log an exception with detailed information.
    
    Args:
        logger (logging.Logger): Logger to use
        exc (Exception): The exception to log
        context (str, optional): Additional context information
    """
    import traceback
    
    if context:
        logger.error(f"Exception in {context}: {str(exc)}")
    else:
        logger.error(f"Exception: {str(exc)}")
    
    logger.error(traceback.format_exc())

# Create a default application logger
app_logger = get_logger("ai-security-proxy")