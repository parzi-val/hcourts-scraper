import logging
import os
from datetime import datetime

def setup_logging(log_level='INFO', log_to_file=True, log_to_console=True):
    """
    Setup logging configuration for the scraper
    
    Args:
        log_level (str): Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_to_file (bool): Whether to log to file
        log_to_console (bool): Whether to log to console
    """
    # Create logs directory if it doesn't exist
    if log_to_file and not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Get the logger
    logger = logging.getLogger('ECourtsHCSScraper')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        # Set encoding to handle Unicode characters
        console_handler.stream.reconfigure(encoding='utf-8')
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(f'logs/scraper_log_{timestamp}.log')
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger():
    """Get the configured logger"""
    return logging.getLogger('ECourtsHCSScraper') 