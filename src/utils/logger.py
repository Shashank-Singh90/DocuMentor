import sys
from pathlib import Path
from loguru import logger
from config.settings import settings

def setup_logger():
    """Setup logger with file and console output"""
    
    # Remove default logger
    logger.remove()
    
    # Console logger with colors
    logger.add(
        sys.stderr,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.LOG_LEVEL
    )
    
    # File logger for all logs
    logger.add(
        settings.LOGS_DIR / "documenter.log",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG"
    )
    
    # Error-only file logger
    logger.add(
        settings.LOGS_DIR / "errors.log",
        rotation="5 MB",
        retention="60 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR"
    )
    
    logger.info("✅ Logger initialized successfully")
    return logger

def get_logger(name: str = __name__):
    """Get logger instance"""
    return logger.bind(name=name)

# Initialize logger when module is imported
setup_logger()




