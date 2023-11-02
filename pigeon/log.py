import logging
import logging.handlers
import os

NONE = logging.CRITICAL + 1
CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG


def initialize(file_level=logging.DEBUG,
               console_level=logging.CRITICAL,
               filename="log"):
    log_file = os.path.join("data", "logs", "main")
    os.makedirs(os.path.dirname(log_file), exist_ok=True) # make sure data/logs exists

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    max_megabytes = 10
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_megabytes * 1024 * 1024, backupCount=5)
    file_formatter = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s: %(message)s")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(file_level)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(console_level)
    logger.addHandler(console_handler)
