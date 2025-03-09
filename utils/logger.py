import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.config import LOG_FORMAT, LOG_FILE, LOG_LEVEL

def setup_logger(name: str) -> logging.Logger:
    """Set up logger with file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # Create logs directory if it doesn't exist
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File Handler (with rotation)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)

    return logger

# Create the main logger
logger = setup_logger('anime_bot')

def log_command(command_name: str, user_id: int, guild_id: int) -> None:
    """Log command usage"""
    logger.info(f"Command '{command_name}' used by user {user_id} in guild {guild_id}")

def log_error(error: Exception, command_name: str = None) -> None:
    """Log error with context"""
    if command_name:
        logger.error(f"Error in command '{command_name}': {str(error)}", exc_info=True)
    else:
        logger.error(f"Error: {str(error)}", exc_info=True)

def log_startup() -> None:
    """Log bot startup"""
    logger.info("Bot is starting up...")

def log_shutdown() -> None:
    """Log bot shutdown"""
    logger.info("Bot is shutting down...") 