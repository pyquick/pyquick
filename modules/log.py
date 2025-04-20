#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志模块
负责程序日志记录和管理
"""
import os
import logging
import logging.handlers
from datetime import datetime

# 日志相关常量
LOG_DIR = "logs"
LOG_FILE = "pyquick.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_MAX_LOG_SIZE = 5 * 1024 * 1024  # 5MB

# 全局日志对象
_logger = None

def init_logging(log_level=None, max_size=None):
    """初始化日志系统
    
    Args:
        log_level: 日志级别（默认INFO）
        max_size: 日志文件最大大小（默认5MB）
    
    Returns:
        logger: 日志对象
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # 创建日志目录
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 设置日志级别
    if log_level is None:
        log_level = DEFAULT_LOG_LEVEL
    elif isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), DEFAULT_LOG_LEVEL)
    
    # 设置日志文件最大大小
    if max_size is None:
        max_size = DEFAULT_MAX_LOG_SIZE
    elif isinstance(max_size, int):
        max_size = max_size * 1024 * 1024  # 转换为字节
    
    # 创建日志对象
    logger = logging.getLogger("PyQuick")
    logger.setLevel(log_level)
    
    # 防止日志重复
    if logger.handlers:
        return logger
    
    # 创建日志处理器
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=max_size, backupCount=3, encoding='utf-8'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置日志格式
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # 记录启动信息
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {logging.getLevelName(log_level)}")
    logger.info(f"日志文件: {log_path}")
    logger.info(f"最大日志大小: {max_size/1024/1024:.1f}MB")
    
    _logger = logger
    return logger

def get_logger():
    """获取日志对象
    
    Returns:
        logger: 日志对象
    """
    global _logger
    
    if _logger is None:
        _logger = init_logging()
    
    return _logger

def set_log_level(level):
    """设置日志级别
    
    Args:
        level: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    """
    logger = get_logger()
    
    if isinstance(level, str):
        level = getattr(logging, level.upper(), DEFAULT_LOG_LEVEL)
    
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
    
    logger.info(f"日志级别已设置为: {logging.getLevelName(level)}")

def archive_logs():
    """归档旧日志文件"""
    if not os.path.exists(LOG_DIR):
        return
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    archive_dir = os.path.join(LOG_DIR, "archive")
    
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
    
    log_path = os.path.join(LOG_DIR, LOG_FILE)
    if os.path.exists(log_path):
        archive_path = os.path.join(archive_dir, f"pyquick_{timestamp}.log")
        try:
            # 关闭当前日志
            logger = get_logger()
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    handler.close()
                    logger.removeHandler(handler)
            
            # 移动日志文件
            os.rename(log_path, archive_path)
            
            # 重新初始化日志
            global _logger
            _logger = None
            logger = init_logging()
            
            logger.info(f"日志已归档到: {archive_path}")
            return True
        except Exception as e:
            print(f"归档日志失败: {e}")
            return False
    
    return False 