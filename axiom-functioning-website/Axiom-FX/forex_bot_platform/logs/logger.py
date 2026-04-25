"""Logging configuration."""
import logging
import os
from datetime import datetime

def setup_logger(name: str = "AxiomFX", level: int = logging.INFO) -> logging.Logger:
    """Setup logger for the trading bot."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(
            f"logs/axiom_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "AxiomFX") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)