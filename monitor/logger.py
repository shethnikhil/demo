import logging
import os
from datetime import date

LOG_DIR = "logs"


def setup_logger(name: str = "nifty_monitor") -> logging.Logger:
    """Configure and return the application logger.

    Writes INFO+ to stdout and DEBUG+ to a daily rotating log file.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured — return existing logger
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — INFO and above
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # File handler — DEBUG and above, one file per day
    log_file = os.path.join(LOG_DIR, f"monitor_{date.today().isoformat()}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
