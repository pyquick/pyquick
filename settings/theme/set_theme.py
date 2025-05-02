#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主题应用模块
负责将主题配置应用到UI界面
"""

import tkinter as tk
from tkinter import ttk
import sv_ttk
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ThemeApplier:
    """主题应用器类"""
    
    @staticmethod
    def apply_theme(root: tk.Tk, theme_config: Dict[str, Any]) -> None:
        """
        应用主题到界面
        
        Args:
            root: 根窗口实例
            theme_config: 主题配置字典
        """
        try:
            # 获取主题配置
            name = theme_config.get("name", "system")
            colors = theme_config.get("colors", {})
            
            # 设置sv-ttk主题
            if name == "dark":
                sv_ttk.set_theme("dark")
            else:
                sv_ttk.set_theme("light")
            
            # 获取ttk样式实例
            style = ttk.Style()
            
            # 配置基础样式
            style.configure(".", 
                background=colors.get("background", "#ffffff"),
                foreground=colors.get("text", "#000000"))
            
            # 配置标签样式
            style.configure("TLabel",
                background=colors.get("background", "#ffffff"),
                foreground=colors.get("text", "#000000"))
            
            # 配置按钮样式
            style.configure("TButton",
                background=colors.get("primary", "#007acc"),
                foreground=colors.get("text", "#000000"))
            
            # 配置框架样式
            style.configure("TFrame",
                background=colors.get("background", "#ffffff"))
            
            # 配置主题样式
            style.configure("Theme.TLabel",
                background=colors.get("background", "#ffffff"),
                foreground=colors.get("primary", "#007acc"))
            
            # 配置进度条样式
            style.configure("Horizontal.TProgressbar",
                background=colors.get("primary", "#007acc"),
                troughcolor=colors.get("background", "#ffffff"))
            
            # 更新所有子窗口样式
            ThemeApplier._update_child_widgets(root, colors)
            
            logger.info(f"成功应用主题: {name}")
            
        except Exception as e:
            logger.error(f"应用主题失败: {e}")
            raise
    
    @staticmethod
    def _update_child_widgets(widget: tk.Widget, colors: Dict[str, str]) -> None:
        """
        递归更新所有子组件的样式
        
        Args:
            widget: 要更新的组件
            colors: 颜色配置字典
        """
        try:
            # 更新当前组件
            if isinstance(widget, (tk.Label, ttk.Label)):
                widget.configure(
                    background=colors.get("background", "#ffffff"),
                    foreground=colors.get("text", "#000000")
                )
            elif isinstance(widget, (tk.Button, ttk.Button)):
                widget.configure(
                    background=colors.get("primary", "#007acc"),
                    foreground=colors.get("text", "#000000")
                )
            elif isinstance(widget, (tk.Frame, ttk.Frame)):
                widget.configure(
                    background=colors.get("background", "#ffffff")
                )
            
            # 递归更新子组件
            for child in widget.winfo_children():
                ThemeApplier._update_child_widgets(child, colors)
                
        except Exception as e:
            logger.warning(f"更新组件样式失败: {e}")