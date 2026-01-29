"""
Logger Utilities Module
=======================

This module provides centralized logging infrastructure for the AI Workflows
framework. The LoggerUtils class creates timestamped log files and optionally
echoes messages to the console.

Key Features:
    - Automatic log directory creation
    - Timestamped log filenames for unique identification
    - Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Optional console output alongside file logging
    - Duplicate handler prevention for reused loggers

Log Output Format:
    Each log entry includes timestamp, logger name, log level, and message:
    ``2026-01-15 10:30:45,123 - AIWorkflowLogger - INFO - Message text``

Usage Example:
    >>> logger = LoggerUtils(name="MyLogger", log_to_console=True)
    >>> logger.log(logging.INFO, "Operation completed successfully")
"""

import os
import logging

from pathlib import Path
from datetime import datetime

# Compute project root and log directory path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) 
LOG_DIR = os.path.join(ROOT, "logs")


class LoggerUtils:
    """
    Configurable logging utility for workflow operations.
    
    Wraps the standard logging module to provide consistent file-based
    logging with optional console output. Each instance creates a unique
    timestamped log file.
    
    Attributes:
        _logger: Internal Python logger instance.
        
    Example:
        >>> logger = LoggerUtils(prefix="workflow_run")
        >>> logger.log(logging.INFO, "Starting workflow...")
    """
    
    def __init__(
        self,
        name: str = "AIWorkflowLogger",
        level: int = logging.INFO,
        log_dir: str = LOG_DIR,
        prefix: str = "run",
        log_to_console: bool = False
    ):
        """
        Initialize the logger with file and optional console output.
        
        Args:
            name: Logger name for identification in log entries.
            level: Minimum log level to capture (default: INFO).
            log_dir: Directory for log files (created if missing).
            prefix: Filename prefix for log files.
            log_to_console: If True, also output to stdout.
            
        Note:
            Log filename format: {prefix}_{YYYYMMDD_HHMMSS}.log
        """
        # Ensure log directory exists
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        # Avoid duplicate handlers if logger is reused
        if not self._logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # Console handler (optional)
            if log_to_console:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                self._logger.addHandler(console_handler)

            # File handler with timestamped filename
            log_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"{prefix}_{log_id}.log"
            file_handler = logging.FileHandler(Path(log_dir) / log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)

            self._logger.addHandler(file_handler)

    @property
    def logger(self) -> logging.Logger:
        """
        Access the underlying Python logger instance.
        
        Returns:
            The configured logging.Logger instance.
        """
        return self._logger

    def log(self, level: int, message: str):
        """
        Log a message at the specified level.
        
        Args:
            level: Log level (e.g., logging.INFO, logging.ERROR).
            message: The message string to log.
        """
        self._logger.log(level, message)
