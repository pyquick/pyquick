#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础设置模块
提供主题切换、自动监测pip更新、日志限制大小和多线程下载开关等功能
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class GeneralSettings:
    """
    通用设置管理类
    负责管理主题、pip更新检查、日志大小和下载线程数等基础设置
    """
    
    def __init__(self, parent, settings_manager, theme_manager):
        """
        初始化通用设置面板
        
        Args:
            parent: 父级窗口
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.frame = ttk.Frame(parent)
        self._create_widgets()
        
    def _create_widgets(self):
        """创建设置界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.frame, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 主题设置部分
        theme_frame = ttk.LabelFrame(main_frame, text="主题设置", padding=(10, 5))
        theme_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(theme_frame, text="当前主题:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 获取可用主题列表
        available_themes = self.theme_manager.get_available_themes()
        self.theme_var = tk.StringVar(value=self.settings_manager.get("theme.current_theme"))
        
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=available_themes, state="readonly")
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_changed)
        
        # 自动检测设置部分
        auto_frame = ttk.LabelFrame(main_frame, text="自动检测设置", padding=(10, 5))
        auto_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # pip更新检测
        self.check_pip_var = tk.BooleanVar(value=self.settings_manager.get("updates.check_pip_updates"))
        pip_check = ttk.Checkbutton(auto_frame, text="自动检测pip更新", variable=self.check_pip_var)
        pip_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 包状态检测
        self.check_pkg_var = tk.BooleanVar(value=self.settings_manager.get("updates.check_package_status"))
        pkg_check = ttk.Checkbutton(auto_frame, text="自动监测包状态", variable=self.check_pkg_var)
        pkg_check.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 日志设置部分
        log_frame = ttk.LabelFrame(main_frame, text="日志设置", padding=(10, 5))
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(log_frame, text="日志文件大小限制:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 日志大小输入
        log_size_frame = ttk.Frame(log_frame)
        log_size_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.log_size_var = tk.StringVar(value=str(self.settings_manager.get("logging.max_size_value")))
        log_size_entry = ttk.Entry(log_size_frame, textvariable=self.log_size_var, width=10)
        log_size_entry.pack(side=tk.LEFT)
        
        # 单位选择
        self.log_unit_var = tk.StringVar(value=self.settings_manager.get("logging.max_size_unit"))
        units = ["KB", "MB", "GB"]
        unit_combo = ttk.Combobox(log_size_frame, textvariable=self.log_unit_var, values=units, state="readonly", width=5)
        unit_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        # 下载设置部分
        download_frame = ttk.LabelFrame(main_frame, text="下载设置", padding=(10, 5))
        download_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 多线程下载开关
        self.multi_thread_var = tk.BooleanVar(value=self.settings_manager.get("downloads.use_multi_thread"))
        multi_thread_check = ttk.Checkbutton(download_frame, text="启用多线程下载", variable=self.multi_thread_var)
        multi_thread_check.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 线程数设置
        ttk.Label(download_frame, text="下载线程数:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.thread_count_var = tk.IntVar(value=self.settings_manager.get("downloads.thread_count"))
        thread_values = list(range(1, 17))  # 1-16线程
        thread_combo = ttk.Combobox(download_frame, textvariable=self.thread_count_var, values=thread_values, state="readonly", width=5)
        thread_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
    def _on_theme_changed(self, event):
        """
        当主题变更时预览新主题
        
        Args:
            event: 组合框选择事件
        """
        selected_theme = self.theme_var.get()
        try:
            self.theme_manager.set_current_theme(selected_theme)
            self.theme_manager.apply_theme(self.parent.winfo_toplevel())
            logger.info(f"预览主题: {selected_theme}")
        except Exception as e:
            logger.error(f"应用主题预览失败: {str(e)}")
            messagebox.showerror("主题预览失败", f"无法应用主题预览: {str(e)}")
    
    def save_settings(self):
        """保存设置到配置管理器"""
        try:
            # 保存主题设置
            self.settings_manager.set("theme.current_theme", self.theme_var.get())
            
            # 保存自动检测设置
            self.settings_manager.set("updates.check_pip_updates", self.check_pip_var.get())
            self.settings_manager.set("updates.check_package_status", self.check_pkg_var.get())
            
            # 保存日志设置
            self.settings_manager.set("logging.max_size_value", float(self.log_size_var.get()))
            self.settings_manager.set("logging.max_size_unit", self.log_unit_var.get())
            
            # 保存下载设置
            self.settings_manager.set("downloads.use_multi_thread", self.multi_thread_var.get())
            self.settings_manager.set("downloads.thread_count", self.thread_count_var.get())
            
            logger.info("通用设置已保存")
            return True
        except Exception as e:
            logger.error(f"保存通用设置时出错: {str(e)}")
            messagebox.showerror("保存失败", f"无法保存设置: {str(e)}")
            return False
    
    def get_frame(self):
        """返回设置框架"""
        return self.frame 