"""
Logging setup for the application.
"""

import logging
import sys

def setup_logging(log_file="app.log", level=logging.INFO):
    """
    Configures logging to output to both console and a file.

    Args:
        log_file (str): The name of the file to log to.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Prevent duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        try:
            file_handler = logging.FileHandler(log_file, mode='a') # Append mode
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            # Log error about file handler creation to console if it fails
            console_handler.handle(logging.LogRecord(
                name='logger_setup',
                level=logging.ERROR,
                pathname=__file__,
                lineno=0,
                msg=f"Failed to create log file handler for {log_file}: {e}",
                args=[],
                exc_info=None,
                func='setup_logging'
            ))

    # Example log message to indicate logging is configured
    logging.info("Logging configured. Outputting to console and %s", log_file) 