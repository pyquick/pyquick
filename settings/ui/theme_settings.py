#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主题设置界面组件
提供主题切换和预览功能
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class ThemeSettingsFrame(ttk.LabelFrame):
    """主题设置框架组件"""
    
    def __init__(self, parent: tk.Widget, theme_manager=None, on_theme_changed: Optional[Callable[[str], None]] = None):
        """
        初始化主题设置框架
        
        Args:
            parent: 父级组件
            theme_manager: 主题管理器实例
            on_theme_changed: 主题变更回调函数
        """
        super().__init__(parent, text="主题设置", padding=10)
        
        self.theme_manager = theme_manager
        self.on_theme_changed = on_theme_changed
        
        self._init_ui()
        
    def _init_ui(self):
        """初始化UI组件"""
        try:
            # 主题选择区域
            theme_frame = ttk.Frame(self)
            theme_frame.pack(fill="x", padx=5, pady=5)
            
            # 主题选择标签
            theme_label = ttk.Label(theme_frame, text="选择主题:")
            theme_label.pack(side="left", padx=5)
            
            # 主题选择下拉框
            self.theme_combobox = ttk.Combobox(
                theme_frame, 
                values=self._get_theme_names(),
                state="readonly",
                width=30
            )
            self.theme_combobox.pack(side="left", padx=5)
            
            # 设置当前主题
            if self.theme_manager:
                current_theme = self.theme_manager.get_current_theme()
                if current_theme:
                    self.theme_combobox.set(current_theme.get("display_name", "系统默认"))
            
            # 绑定主题变更事件
            self.theme_combobox.bind("<<ComboboxSelected>>", self._on_theme_selected)
            
            # 主题预览区域
            preview_frame = ttk.LabelFrame(self, text="主题预览", padding=10)
            preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
            
            # 预览示例组件
            sample_label = ttk.Label(preview_frame, text="示例文本", style="Theme.TLabel")
            sample_label.pack(pady=5)
            
            sample_button = ttk.Button(preview_frame, text="示例按钮")
            sample_button.pack(pady=5)
            
            sample_entry = ttk.Entry(preview_frame)
            sample_entry.insert(0, "示例输入框")
            sample_entry.pack(pady=5)
            
            sample_progress = ttk.Progressbar(
                preview_frame, 
                orient="horizontal",
                mode="determinate",
                value=50
            )
            sample_progress.pack(fill="x", pady=5)
            
        except Exception as e:
            logger.error(f"初始化主题设置界面失败: {e}")
            raise
    
    def _get_theme_names(self) -> list:
        """获取主题名称列表"""
        if not self.theme_manager:
            return ["系统默认"]
            
        themes = []
        try:
            # 获取所有可用主题
            for theme_name in self.theme_manager.list_available_themes():
                if theme_name == "system":
                    themes.append("系统默认")
                else:
                    try:
                        # 尝试加载主题配置获取显示名称
                        self.theme_manager.set_current_theme(theme_name)
                        theme = self.theme_manager.get_current_theme()
                        if theme:
                            themes.append(theme.get("display_name", theme_name))
                    except:
                        themes.append(theme_name)
        except Exception as e:
            logger.error(f"获取主题列表失败: {e}")
            
        return themes or ["系统默认"]
    
    def _on_theme_selected(self, event):
        """
        主题选择事件处理
        
        Args:
            event: 事件对象
        """
        try:
            if not self.theme_manager:
                return
                
            # 获取选择的主题显示名称
            selected = self.theme_combobox.get()
            
            # 转换为主题名称
            if selected == "系统默认":
                theme_name = "system"
            else:
                # 查找对应的主题名称
                for name in self.theme_manager.list_available_themes():
                    try:
                        self.theme_manager.set_current_theme(name)
                        theme = self.theme_manager.get_current_theme()
                        if theme and theme.get("display_name") == selected:
                            theme_name = name
                            break
                    except:
                        continue
                else:
                    logger.error(f"未找到主题: {selected}")
                    return
            
            # 应用主题
            if self.theme_manager.set_current_theme(theme_name):
                logger.info(f"已切换主题: {selected}")
                
                # 调用回调函数
                if self.on_theme_changed:
                    self.on_theme_changed(theme_name)
                    
        except Exception as e:
            logger.error(f"切换主题失败: {e}")
    
    def update_theme(self):
        """更新主题"""
        try:
            if self.theme_manager:
                current_theme = self.theme_manager.get_current_theme()
                if current_theme:
                    self.theme_combobox.set(current_theme.get("display_name", "系统默认"))
        except Exception as e:
            logger.error(f"更新主题设置界面失败: {e}")