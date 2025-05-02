#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础设置模块
提供自动检测pip更新、日志限制大小和多线程下载开关等功能
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GeneralSettings:
    """
    通用设置管理类
    负责管理pip更新检查、日志大小和下载线程数等基础设置
    """
    
    def __init__(self, parent, settings_manager):
        """
        初始化通用设置面板
        
        Args:
            parent: 父级窗口
            settings_manager: 设置管理器实例
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.frame = ttk.Frame(parent)
        
        # 创建变量
        self.check_pip_var = tk.BooleanVar()
        self.check_pkg_var = tk.BooleanVar()
        self.log_size_var = tk.StringVar()
        self.log_unit_var = tk.StringVar()
        self.multi_thread_var = tk.BooleanVar()
        self.thread_count_var = tk.StringVar()
        
        # 加载设置
        self.load_settings()
        
        # 创建界面
        self._create_widgets()
        
    def _create_widgets(self):
        """创建设置界面组件"""
        # 更新检查设置
        update_frame = ttk.LabelFrame(self.frame, text="自动更新检查")
        update_frame.pack(fill=tk.X, padx=5, pady=5)
        
        check_pip = ttk.Checkbutton(update_frame, text="自动检查pip更新", 
                                   variable=self.check_pip_var)
        check_pip.pack(anchor=tk.W, padx=5, pady=2)
        
        check_pkg = ttk.Checkbutton(update_frame, text="检查包状态", 
                                   variable=self.check_pkg_var)
        check_pkg.pack(anchor=tk.W, padx=5, pady=2)
        
        # 日志设置
        log_frame = ttk.LabelFrame(self.frame, text="日志设置")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        size_frame = ttk.Frame(log_frame)
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(size_frame, text="日志文件大小限制:").pack(side=tk.LEFT)
        
        size_entry = ttk.Entry(size_frame, textvariable=self.log_size_var, 
                              width=10)
        size_entry.pack(side=tk.LEFT, padx=5)
        
        units = ["KB", "MB", "GB"]
        unit_combo = ttk.Combobox(size_frame, textvariable=self.log_unit_var,
                                 values=units, state="readonly", width=5)
        unit_combo.pack(side=tk.LEFT)
        
        # 下载设置
        download_frame = ttk.LabelFrame(self.frame, text="下载设置")
        download_frame.pack(fill=tk.X, padx=5, pady=5)
        
        multi_thread = ttk.Checkbutton(download_frame, text="启用多线程下载", 
                                      variable=self.multi_thread_var,
                                      command=self._toggle_thread_count)
        multi_thread.pack(anchor=tk.W, padx=5, pady=2)
        
        thread_frame = ttk.Frame(download_frame)
        thread_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(thread_frame, text="下载线程数:").pack(side=tk.LEFT)
        
        thread_entry = ttk.Entry(thread_frame, textvariable=self.thread_count_var,
                                width=5)
        thread_entry.pack(side=tk.LEFT, padx=5)
        
    def _toggle_thread_count(self):
        """启用/禁用线程数输入"""
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "下载设置":
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.Frame):
                        for widget in frame.winfo_children():
                            if isinstance(widget, ttk.Entry):
                                if self.multi_thread_var.get():
                                    widget.configure(state="normal")
                                else:
                                    widget.configure(state="disabled")
                                    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 加载更新检查设置
            self.check_pip_var.set(self.settings_manager.get("general.auto_check_pip_updates", True))
            self.check_pkg_var.set(self.settings_manager.get("general.check_package_status", True))
            
            # 加载日志设置
            self.log_size_var.set(str(self.settings_manager.get("general.log_size_limit", 10.0)))
            self.log_unit_var.set(self.settings_manager.get("general.log_size_unit", "MB"))
            
            # 加载下载设置
            self.multi_thread_var.set(self.settings_manager.get("general.enable_multi_thread_download", True))
            self.thread_count_var.set(str(self.settings_manager.get("general.download_threads", 4)))
            
            # 更新界面状态
            self._toggle_thread_count()
            
            logger.debug("通用设置加载成功")
        except Exception as e:
            logger.error(f"加载通用设置时出错: {e}")
            
    def save_settings(self):
        """保存设置到配置管理器"""
        try:
            # 保存自动检测设置
            self.settings_manager.set("general.auto_check_pip_updates", self.check_pip_var.get())
            self.settings_manager.set("general.check_package_status", self.check_pkg_var.get())
            
            # 保存日志设置
            self.settings_manager.set("general.log_size_limit", float(self.log_size_var.get()))
            self.settings_manager.set("general.log_size_unit", self.log_unit_var.get())
            
            # 保存下载设置
            self.settings_manager.set("general.enable_multi_thread_download", self.multi_thread_var.get())
            self.settings_manager.set("general.download_threads", int(self.thread_count_var.get()))
            
            logger.info("通用设置已保存")
            return True
        except Exception as e:
            logger.error(f"保存通用设置时出错: {str(e)}")
            return False
    
    def get_frame(self):
        """返回设置框架"""
        return self.frame