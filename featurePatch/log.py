"""
Globally scoped logging.Logger, set to INFO by default.
Functions provided to change logging level or create a logfile duplicating the console logging.

Use:
from <path to log>.log import log
"""

import logging
from typing import Optional

log: Optional[logging.Logger] = None


def init_log():
    global log
    # Initialize console logger, Info by default
    if log is None:
        streamHandler = logging.StreamHandler()
        # Apply formatting
        source_descriptor = "%(levelname)s:%(filename)s|%(funcName)s:"
        message = "%(message)s\n"
        streamHandler.setFormatter(logging.Formatter(source_descriptor + "\n" + message))
        log = logging.getLogger("feature-patch")
        streamHandler.setLevel(logging.DEBUG)
        log.addHandler(streamHandler)
        log.setLevel(logging.INFO)
        log.info("Logger initialized!")


def initialize_file_handler(log_file_path):
    """
    Initializes File handler with given path as destination file. Creates or truncates file.
    :param: log_file_path: where to log to.
    """
    with open(log_file_path, "w"):
        pass
    # Use similar formatting to the console formatter but more compact
    file_formatter = logging.Formatter(source_descriptor + ":" + message)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    log.addHandler(file_handler)
    return log


def set_debug_logger():
    log.setLevel(logging.DEBUG)


def set_info_logger():
    log.setLevel(logging.DEBUG)


def set_warning_logger():
    log.setLevel(logging.WARNING)


def set_error_logger():
    log.setLevel(logging.ERROR)
