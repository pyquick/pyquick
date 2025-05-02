#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自定义主题管理模块
负责获取和管理用户自定义的主题设置
"""

import os
import json
import logging
import tkinter as tk
import sv_ttk
from typing import Dict, Any, Optional
import darkdetect
from tkinter import ttk

logger = logging.getLogger(__name__)

class ThemeManager:
    """主题管理器类"""
    
    def __init__(self, config_path: str):
        """
        初始化主题管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.themes_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "themes")
        self.config_file = os.path.join(config_path, "theme_config.json")
        self.current_theme = None
        
        # 确保主题目录存在
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir, exist_ok=True)
            
        self._load_config()
        
    def _load_config(self) -> None:
        """加载主题配置"""
        try:
            # 先尝试从配置文件加载
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    theme_name = config.get('current_theme', {}).get('name')
                    if theme_name:
                        # 确保主题文件存在
                        theme_file = os.path.join(self.themes_dir, f"{theme_name}.json")
                        if os.path.exists(theme_file):
                            self.current_theme = config.get('current_theme')
                            logger.info(f"已加载主题: {theme_name}")
                            return
                        
            # 如果加载失败或未找到配置,使用系统主题
            system_mode = darkdetect.theme().lower()
            default_theme = "dark" if system_mode == "dark" else "light"
            theme_file = os.path.join(self.themes_dir, f"{default_theme}.json")
            
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    self.current_theme = json.load(f)
                    logger.info(f"已加载系统对应的{default_theme}主题")
            else:
                # 如果对应主题文件不存在，使用默认主题
                self.current_theme = self.get_default_theme()
                logger.info("使用默认主题")
                
            # 保存当前配置
            self._save_config()
            
        except Exception as e:
            logger.error(f"加载主题配置失败: {e}")
            self.current_theme = self.get_default_theme()
            
    def _save_config(self) -> None:
        """保存主题配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'current_theme': self.current_theme}, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存主题配置: {self.current_theme.get('name')}")
        except Exception as e:
            logger.error(f"保存主题配置失败: {e}")
    
    def get_default_theme(self) -> Dict[str, Any]:
        """
        获取默认主题配置
        
        Returns:
            默认主题配置字典
        """
        # 检查系统主题
        system_mode = darkdetect.theme()
        
        if system_mode and system_mode.lower() == "dark":
            theme_file = os.path.join(self.themes_dir, "dark.json")
        else:
            theme_file = os.path.join(self.themes_dir, "light.json")
            
        # 尝试加载对应主题文件
        try:
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载默认主题失败: {e}")
        
        # 如果加载失败，返回基础主题配置
        return {
            "name": "system",
            "display_name": "系统默认",
            "colors": {
                "primary": "#007acc",
                "secondary": "#0098ff",
                "background": "#ffffff",
                "surface": "#f5f5f5",
                "text": "#000000",
                "text_secondary": "#666666",
                "border": "#e0e0e0",
                "success": "#28a745",
                "warning": "#ffc107", 
                "error": "#dc3545",
                "info": "#17a2b8"
            },
            "fonts": {
                "default": {
                    "family": "系统默认",
                    "size": 12
                },
                "title": {
                    "family": "系统默认",
                    "size": 14,
                    "weight": "bold"
                },
                "small": {
                    "family": "系统默认",
                    "size": 10
                }
            }
        }
        
    def set_current_theme(self, theme_name: str) -> bool:
        """
        设置当前主题
        
        Args:
            theme_name: 主题名称
            
        Returns:
            bool: 是否设置成功
        """
        try:
            if theme_name == "system":
                # 获取系统主题
                import darkdetect
                system_mode = darkdetect.theme().lower()
                theme_name = "dark" if system_mode == "dark" else "light"
                
            # 加载主题文件
            theme_file = os.path.join(self.themes_dir, f"{theme_name}.json")
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    self.current_theme = json.load(f)
                    logger.info(f"已切换到主题: {theme_name}")
                    
                    # 保存主题配置
                    self._save_config()
                    return True
            else:
                logger.error(f"主题文件不存在: {theme_file}")
                return False
                
        except Exception as e:
            logger.error(f"设置主题失败: {e}")
            return False

    def apply_theme(self, root: tk.Tk) -> None:
        """
        应用主题到界面
        
        Args:
            root: 根窗口实例
        """
        try:
            if not self.current_theme:
                self.current_theme = self.get_default_theme()
            
            theme_name = self.current_theme.get("name", "light")
            colors = self.current_theme.get("colors", {})
            
            # 设置sv_ttk主题
            if theme_name == "dark":
                sv_ttk.set_theme("dark")
            else:
                sv_ttk.set_theme("light")
            
            try:
                # 配置ttk样式
                style = ttk.Style()
                
                # 基础样式
                style.configure(".", 
                    background=colors.get("background"),
                    foreground=colors.get("text"),
                    fieldbackground=colors.get("surface")
                )
                
                # 标签样式
                style.configure("TLabel", 
                    foreground=colors.get("text"),
                    background=colors.get("background")
                )
                
                # 按钮样式
                style.configure("TButton",
                    background=colors.get("primary"),
                    foreground=colors.get("text")
                )
                
                # 框架样式
                style.configure("TFrame",
                    background=colors.get("background")
                )
                
                # 特殊标签样式
                style.configure("Success.TLabel", foreground=colors.get("success"))
                style.configure("Warning.TLabel", foreground=colors.get("warning"))
                style.configure("Error.TLabel", foreground=colors.get("error"))
                style.configure("Info.TLabel", foreground=colors.get("info"))
                
                # 更新所有顶层窗口
                self._update_all_windows(root)
                
            except Exception as e:
                logger.error(f"配置ttk样式失败: {e}")
                
        except Exception as e:
            logger.error(f"应用主题失败: {e}")
            # 发生错误时保持当前主题
    
    def _update_child_windows(self, parent: tk.Widget) -> None:
        """
        递归更新所有子窗口的主题
        
        Args:
            parent: 父窗口实例
        """
        try:
            for child in parent.winfo_children():
                if hasattr(child, "update_theme"):
                    child.update_theme()
                self._update_child_windows(child)
        except Exception as e:
            logger.error(f"更新子窗口主题失败: {e}")
    
    def _update_all_windows(self, root: tk.Tk) -> None:
        """
        更新所有窗口的主题
        
        Args:
            root: 根窗口实例
        """
        try:
            # 更新所有子窗口
            self._update_child_windows(root)
            
            # 更新所有顶层窗口
            for window in root.winfo_children():
                if isinstance(window, tk.Toplevel):
                    # 向顶层窗口发送主题更新事件
                    window.event_generate("<<ThemeChanged>>")
                    # 更新顶层窗口的子窗口
                    self._update_child_windows(window)
                    
        except Exception as e:
            logger.error(f"更新窗口主题失败: {e}")
    
    def list_available_themes(self) -> list:
        """
        列出所有可用的主题
        
        Returns:
            主题名称列表
        """
        themes = ["system"]  # 始终包含系统默认主题
        try:
            if os.path.exists(self.themes_dir):
                for file in os.listdir(self.themes_dir):
                    if file.endswith(".json"):
                        themes.append(file[:-5])
        except Exception as e:
            logger.error(f"列出主题失败: {e}")
        return themes