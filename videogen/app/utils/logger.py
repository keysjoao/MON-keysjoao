import logging
import sys
from pathlib import Path

# Create logs dir
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File Handler
    file_handler = logging.FileHandler(LOGS_DIR / "app.log")
    file_handler.setFormatter(formatter)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger

# Default logger instance
logger = setup_logger("VideoGen")
