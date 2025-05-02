#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
日志管理模块
负责配置和管理应用程序的日志功能
"""

import os
import sys
import json
import logging
import logging.handlers
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
import time
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
            if isinstance(handler, (logging.handlers.RotatingFileHandler, logging.handlers.TimedRotatingFileHandler)):
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
            file_handler = logging.handlers.RotatingFileHandler(
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
                  log_format=None, debug_mode=False):
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
            debug_mode: 是否为调试模式，非调试模式下控制台只输出error级别的日志
            
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
            
            # 在非调试模式下，控制台只输出error级别以上的日志
            if not debug_mode:
                console_handler.setLevel(logging.ERROR)
                logger.info(f"非调试模式: 控制台日志级别设置为ERROR")
            else:
                console_handler.setLevel(self.LEVELS.get(level.lower(), logging.INFO))
                logger.info(f"调试模式: 控制台日志级别设置为{level.upper()}")
                
            # 添加一个自定义的Filter，用于添加颜色
            class ColorFilter(logging.Filter):
                def filter(self, record):
                    # 根据日志级别添加颜色前缀
                    if record.levelno >= logging.ERROR:
                        # 红色
                        record.msg = f"\033[31m{record.msg}\033[0m"
                    elif record.levelno >= logging.WARNING:
                        # 黄色
                        record.msg = f"\033[33m{record.msg}\033[0m"
                    elif record.levelno >= logging.INFO:
                        # 蓝色
                        record.msg = f"\033[34m{record.msg}\033[0m"
                    elif record.levelno >= logging.DEBUG:
                        # 蓝色
                        record.msg = f"\033[34m{record.msg}\033[0m"
                    return True
            
            # 只在支持颜色的终端添加颜色过滤器
            if sys.stdout.isatty():
                console_handler.addFilter(ColorFilter())
                
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if enable_file:
            log_file = os.path.join(self.log_dir, f"{self.app_name}_{name}.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, 
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            # 文件中保留所有日志
            file_handler.setLevel(self.LEVELS.get(level.lower(), logging.INFO))
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
            file_handler = logging.handlers.TimedRotatingFileHandler(
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

def configure_global_loggers(log_level="info", enable_console=True, enable_file=True, log_dir=None, debug_mode=False):
    """
    配置全局日志对象
    
    Args:
        log_level: 日志级别
        enable_console: 是否启用控制台输出
        enable_file: 是否启用文件记录
        log_dir: 日志目录，如果指定则更新日志目录
        debug_mode: 是否为调试模式，非调试模式下控制台只输出error级别的日志
    """
    global app_logger, download_logger, error_logger
    
    # 更新日志目录
    if log_dir:
        logger_manager.set_log_dir(log_dir)
    
    app_logger = logger_manager.get_logger(
        "app", level=log_level, enable_console=enable_console, enable_file=enable_file, debug_mode=debug_mode
    )
    
    download_logger = logger_manager.get_logger(
        "download", level=log_level, enable_console=enable_console, enable_file=enable_file, debug_mode=debug_mode
    )
    
    error_logger = logger_manager.get_logger(
        "error", level="error", enable_console=enable_console, enable_file=enable_file, debug_mode=debug_mode
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

class LogManager:
    """日志管理类,负责配置和管理应用程序日志"""
    
    def __init__(self, parent, settings_manager):
        """
        初始化日志管理器
        
        Args:
            parent: 父级窗口
            settings_manager: 设置管理器实例
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.frame = ttk.Frame(parent)
        
        # 默认设置
        self.default_settings = {
            "log.max_size": 10 * 1024 * 1024,  # 10MB
            "log.backup_count": 3,
            "log.app_level": "INFO",
            "log.file_level": "DEBUG",
            "log.console_level": "INFO"
        }
        
        # 创建界面组件
        self._create_widgets()
        
        # 应用当前设置
        self._apply_settings()
        
    def _create_widgets(self):
        """创建设置界面组件"""
        # 日志级别设置
        level_frame = ttk.LabelFrame(self.frame, text="日志级别设置")
        level_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 应用日志级别
        app_frame = ttk.Frame(level_frame)
        app_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(app_frame, text="应用日志级别:").pack(side=tk.LEFT)
        
        self.app_level_var = tk.StringVar(
            value=self.settings_manager.get("log.app_level", "INFO"))
        app_combo = ttk.Combobox(app_frame, textvariable=self.app_level_var,
                                values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                state="readonly", width=10)
        app_combo.pack(side=tk.LEFT, padx=5)
        
        # 文件日志级别
        file_frame = ttk.Frame(level_frame)
        file_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(file_frame, text="文件日志级别:").pack(side=tk.LEFT)
        
        self.file_level_var = tk.StringVar(
            value=self.settings_manager.get("log.file_level", "DEBUG"))
        file_combo = ttk.Combobox(file_frame, textvariable=self.file_level_var,
                                 values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                 state="readonly", width=10)
        file_combo.pack(side=tk.LEFT, padx=5)
        
        # 控制台日志级别
        console_frame = ttk.Frame(level_frame)
        console_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(console_frame, text="控制台日志级别:").pack(side=tk.LEFT)
        
        self.console_level_var = tk.StringVar(
            value=self.settings_manager.get("log.console_level", "INFO"))
        console_combo = ttk.Combobox(console_frame, textvariable=self.console_level_var,
                                   values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                   state="readonly", width=10)
        console_combo.pack(side=tk.LEFT, padx=5)
        
        # 日志文件设置
        file_settings_frame = ttk.LabelFrame(self.frame, text="日志文件设置")
        file_settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 最大文件大小
        size_frame = ttk.Frame(file_settings_frame)
        size_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(size_frame, text="单个日志文件最大大小(MB):").pack(side=tk.LEFT)
        
        self.max_size_var = tk.StringVar(
            value=str(self.settings_manager.get("log.max_size", 10*1024*1024) // (1024*1024)))
        size_entry = ttk.Entry(size_frame, textvariable=self.max_size_var, width=10)
        size_entry.pack(side=tk.LEFT, padx=5)
        
        # 备份文件数量
        backup_frame = ttk.Frame(file_settings_frame)
        backup_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(backup_frame, text="保留的备份文件数:").pack(side=tk.LEFT)
        
        self.backup_count_var = tk.StringVar(
            value=str(self.settings_manager.get("log.backup_count", 3)))
        backup_entry = ttk.Entry(backup_frame, textvariable=self.backup_count_var, width=10)
        backup_entry.pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="应用设置",
                   command=self._apply_settings).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="重置为默认",
                   command=self._reset_to_default).pack(side=tk.RIGHT)
        
        # 日志预览区域
        preview_frame = ttk.LabelFrame(self.frame, text="日志预览")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text = tk.Text(preview_frame, wrap=tk.WORD, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.preview_text, orient=tk.VERTICAL,
                                command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._update_preview()
        
    def _get_log_level(self, level_str: str) -> int:
        """将日志级别字符串转换为logging常量"""
        return getattr(logging, level_str.upper())
        
    def _apply_settings(self):
        """应用日志设置"""
        try:
            # 验证并获取设置值
            max_size = int(self.max_size_var.get()) * 1024 * 1024  # 转换为字节
            if max_size <= 0:
                raise ValueError("日志文件大小必须大于0")
                
            backup_count = int(self.backup_count_var.get())
            if backup_count < 0:
                raise ValueError("备份文件数不能为负数")
                
            # 保存设置
            self.settings_manager.set("log.max_size", max_size)
            self.settings_manager.set("log.backup_count", backup_count)
            self.settings_manager.set("log.app_level", self.app_level_var.get())
            self.settings_manager.set("log.file_level", self.file_level_var.get())
            self.settings_manager.set("log.console_level", self.console_level_var.get())
            
            # 配置根日志记录器
            root_logger = logging.getLogger()
            root_logger.setLevel(self._get_log_level(self.app_level_var.get()))
            
            # 更新所有处理器的日志级别
            for handler in root_logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.setLevel(self._get_log_level(self.file_level_var.get()))
                elif isinstance(handler, logging.StreamHandler):
                    handler.setLevel(self._get_log_level(self.console_level_var.get()))
                    
            # 更新预览
            self._update_preview()
            
            messagebox.showinfo("成功", "日志设置已更新")
            
        except ValueError as e:
            messagebox.showerror("错误", f"输入无效: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"应用设置失败: {str(e)}")
            
    def _reset_to_default(self):
        """重置为默认设置"""
        if not messagebox.askyesno("确认", "确定要重置为默认设置吗？"):
            return
            
        # 恢复默认值
        self.max_size_var.set(str(self.default_settings["log.max_size"] // (1024*1024)))
        self.backup_count_var.set(str(self.default_settings["log.backup_count"]))
        self.app_level_var.set(self.default_settings["log.app_level"])
        self.file_level_var.set(self.default_settings["log.file_level"])
        self.console_level_var.set(self.default_settings["log.console_level"])
        
        # 应用设置
        self._apply_settings()
        
    def _update_preview(self):
        """更新日志预览区域"""
        self.preview_text.delete("1.0", tk.END)
        
        # 获取当前设置的预览
        preview_text = f"""当前日志设置预览:

应用日志级别: {self.app_level_var.get()}
文件日志级别: {self.file_level_var.get()}
控制台日志级别: {self.console_level_var.get()}

单个日志文件最大大小: {self.max_size_var.get()}MB
保留的备份文件数: {self.backup_count_var.get()}

日志文件位置:
- 应用日志: app.log
- 错误日志: error.log
- 下载日志: download.log

注意: 更改日志级别将立即生效,但文件大小和备份数量的更改将在下次日志轮换时生效。
"""
        
        self.preview_text.insert("1.0", preview_text)
        self.preview_text.configure(state="disabled")
        
    def get_frame(self):
        """返回设置框架"""
        return self.frame