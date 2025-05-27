"""
Compatibility module for swerex.utils.log imports.

This module provides compatibility with the original swerex.utils.log module,
enabling imports to work correctly in the Django integration.
"""

import logging

logger = logging.getLogger(__name__)

def setup_logging(level=logging.INFO, log_file=None):
    """
    Set up logging configuration.
    
    Args:
        level: Logging level
        log_file: Log file path
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=log_file
    )
    
    return logger

def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
