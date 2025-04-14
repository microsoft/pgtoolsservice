import logging
from functools import lru_cache
from pathlib import Path

from evaluations.settings import EvaluationSettings, get_settings


@lru_cache(maxsize=1)
def configure_logging(eval_settings: EvaluationSettings | None = None) -> None:
    """Configure logging to log only this package's logs to a file for pytest tests."""
    eval_settings = eval_settings or get_settings()
    eval_log_file = Path(eval_settings.eval_log_file).absolute()
    pgts_log_dir = Path(eval_settings.pgts_log_dir).absolute()

    # Create a logger evaluations
    package_logger = logging.getLogger("evaluations")
    package_logger.setLevel(logging.INFO)  # Set the desired logging level

    # Create handlers
    file_handler = logging.FileHandler(eval_log_file, mode="a")

    # Set formatter
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add handlers to the package logger
    package_logger.addHandler(file_handler)

