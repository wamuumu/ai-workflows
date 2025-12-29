import os
import logging

from pathlib import Path
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) 
LOG_DIR = os.path.join(ROOT, "logs")

class LoggerUtils:
    def __init__(
        self,
        name: str = "AIWorkflowLogger",
        level: int = logging.INFO,
        log_dir: str = LOG_DIR,
        log_to_console: bool = False
    ):
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

            # File handler
            log_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"run_{log_id}.log"
            file_handler = logging.FileHandler(Path(log_dir) / log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)

            self._logger.addHandler(file_handler)

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    def log(self, level: int, message: str):
        self._logger.log(level, message)
