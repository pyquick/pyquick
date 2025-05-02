"""
日志模块，提供可配置的文件和控制台日志记录
支持日志文件轮转、自定义格式和多级别记录
"""

import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import traceback

class LoggerManager:
    """日志管理类，负责创建和配置日志记录器"""
    
    # 日志级别映射
    LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    
    # 默认日志格式
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    def __init__(self, log_dir="log", app_name="pyquick"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志文件存储目录
            app_name: 应用名称，用于日志文件命名
        """
        self.log_dir = log_dir
        self.app_name = app_name
        self.loggers = {}
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                print(f"无法创建日志目录: {e}")
    
    def set_log_dir(self, log_dir):
        """
        设置日志目录
        
        Args:
            log_dir: 新的日志目录
        """
        self.log_dir = log_dir
        
        # 确保日志目录存在
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                print(f"无法创建日志目录: {e}")
                
        # 更新现有日志记录器的处理器
        for name, logger in self.loggers.items():
            self._update_file_handlers(logger, name)
            
    def _update_file_handlers(self, logger, name):
        """
        更新日志记录器的文件处理器
        
        Args:
            logger: 日志记录器
            name: 日志记录器名称
        """
        # 保存现有配置
        formatter = None
        level = None
        max_bytes = 10*1024*1024
        backup_count = 5
        
        # 移除旧的文件处理器
        new_handlers = []
        for handler in logger.handlers:
            if isinstance(handler, (RotatingFileHandler, TimedRotatingFileHandler)):
                # 保存配置
                formatter = handler.formatter
                level = handler.level
                if hasattr(handler, 'maxBytes'):
                    max_bytes = handler.maxBytes
                if hasattr(handler, 'backupCount'):
                    backup_count = handler.backupCount
            else:
                new_handlers.append(handler)
        
        # 添加新的文件处理器
        if formatter:
            log_file = os.path.join(self.log_dir, f"{self.app_name}_{name}.log")
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level if level else logging.INFO)
            new_handlers.append(file_handler)
        
        # 更新处理器
        logger.handlers = new_handlers
    
    def get_logger(self, name="root", level="info", enable_console=True, 
                  enable_file=True, max_bytes=10*1024*1024, backup_count=5, 
                  log_format=None):
        """
        获取或创建一个日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别 (debug, info, warning, error, critical)
            enable_console: 是否启用控制台日志
            enable_file: 是否启用文件日志
            max_bytes: 单个日志文件的最大大小（字节）
            backup_count: 保留的备份文件数量
            log_format: 自定义日志格式
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        # 如果已经创建过，直接返回
        if name in self.loggers:
            return self.loggers[name]
        
        # 创建新的日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(self.LEVELS.get(level.lower(), logging.INFO))
        
        # 清除已有的处理器
        logger.handlers = []
        
        # 设置日志格式
        formatter = logging.Formatter(
            log_format or self.DEFAULT_FORMAT
        )
        
        # 添加控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(self.LEVELS.get(level.lower(), logging.INFO))
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if enable_file:
            log_file = os.path.join(self.log_dir, f"{self.app_name}_{name}.log")
            file_handler = RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 缓存该日志记录器
        self.loggers[name] = logger
        return logger
    
    def get_daily_logger(self, name="daily", level="info", enable_console=True, 
                        enable_file=True, backup_count=30, log_format=None):
        """
        获取按天轮转的日志记录器
        
        Args:
            name: 日志记录器名称
            level: 日志级别 (debug, info, warning, error, critical)
            enable_console: 是否启用控制台日志
            enable_file: 是否启用文件日志
            backup_count: 保留的备份文件数量
            log_format: 自定义日志格式
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.LEVELS.get(level.lower(), logging.INFO))
        logger.handlers = []
        
        formatter = logging.Formatter(
            log_format or self.DEFAULT_FORMAT
        )
        
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        if enable_file:
            log_file = os.path.join(self.log_dir, f"{self.app_name}_{name}.log")
            file_handler = TimedRotatingFileHandler(
                log_file, 
                when='midnight',
                interval=1,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        self.loggers[name] = logger
        return logger

# 创建全局日志管理器实例
logger_manager = LoggerManager()

# 全局公用日志对象
app_logger = logger_manager.get_logger("app", level="info")
download_logger = logger_manager.get_logger("download", level="info")
error_logger = logger_manager.get_logger("error", level="error")

def log_exception(exc_info=None):
    """
    记录异常详细信息
    
    Args:
        exc_info: 异常信息，默认获取当前异常
    """
    if exc_info is None:
        exc_info = sys.exc_info()
        
    if exc_info and exc_info[0]:
        error_msg = "".join(traceback.format_exception(*exc_info))
        error_logger.error(f"异常详情:\n{error_msg}")

def configure_global_loggers(log_level="info", enable_console=True, enable_file=True, log_dir=None):
    """
    配置全局日志对象
    
    Args:
        log_level: 日志级别
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件记录
        log_dir: 日志目录，如果指定则更新日志目录
    """
    global app_logger, download_logger, error_logger
    
    # 更新日志目录
    if log_dir:
        logger_manager.set_log_dir(log_dir)
    
    app_logger = logger_manager.get_logger(
        "app", level=log_level, enable_console=enable_console, enable_file=enable_file
    )
    
    download_logger = logger_manager.get_logger(
        "download", level=log_level, enable_console=enable_console, enable_file=enable_file
    )
    
    error_logger = logger_manager.get_logger(
        "error", level="error", enable_console=enable_console, enable_file=enable_file
    )
    
def get_all_log_files():
    """
    获取所有日志文件路径
    
    Returns:
        list: 日志文件路径列表
    """
    log_files = []
    if os.path.exists(logger_manager.log_dir):
        for filename in os.listdir(logger_manager.log_dir):
            if filename.endswith('.log'):
                log_files.append(os.path.join(logger_manager.log_dir, filename))
    return log_files 