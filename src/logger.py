import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name="AiTrader", log_file="ai_trader.log", level=logging.INFO):
    """
    Setup a logger that prints to stdout and writes to a file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times
    if logger.hasHandlers():
        return logger

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3) # 5MB per file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to set up file logging: {e}")

    return logger

# Global logger instance
logger = setup_logger()
