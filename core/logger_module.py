# logger_module.py
# 功能：提供可在多个 .py 文件间共享的日志系统，自动滚动、防乱码、防重复。

import logging
from logging.handlers import RotatingFileHandler
import sys

DEFAULT_LOGGER_NAME = "ImpactSimulator"

def setup_logger(log_filename="simulation_log.txt", max_bytes=2*1024*1024, backup_count=3, logger_name=DEFAULT_LOGGER_NAME):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    # ... 文件和控制台 handler 配置 ...
    return logger

def get_logger(logger_name=DEFAULT_LOGGER_NAME):
    return logging.getLogger(logger_name)