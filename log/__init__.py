"""
日志系统模块，提供文件操作和日志记录功能
"""

from .log import (
    logger_manager, 
    app_logger, 
    download_logger, 
    error_logger,
    log_exception,
    configure_global_loggers
)

from .base import (
    file_manager,
    json_manager,
    FileManager,
    JsonFileManager,
    configure_file_managers
)

# 版本信息
__version__ = '1965'
