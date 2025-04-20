"""
PyQuick - 对话框模块
包含各种对话窗口的相关功能
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import logging

# 获取根目录并添加到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from log import get_logger
from lang import get_text
from utils import safe_config, safe_grid, safe_grid_forget

logger = get_logger()

# 导入各个对话框模块
try:
    from ui.dialogs.about_dialog import show_about_dialog
except ImportError as e:
    logger.error(f"导入关于对话框模块失败: {e}")
    
    # 提供兼容函数
    def show_about_dialog(parent=None):
        """显示关于对话框"""
        try:
            from ab import about
            threading.Thread(target=about.show, daemon=True).start()
        except Exception as e:
            logger.error(f"显示关于对话框出错: {e}")
            messagebox.showerror(get_text("error"), f"显示关于对话框出错: {e}")

try:
    from ui.dialogs.settings_dialog import show_settings_dialog
except ImportError as e:
    logger.error(f"导入设置对话框模块失败: {e}")
    
    # 提供兼容函数
    def show_settings_dialog(parent=None, config_path=None, restart_callback=None):
        """显示设置对话框"""
        try:
            from pyquick import settings1
            settings1()
        except Exception as e:
            logger.error(f"显示设置对话框出错: {e}")
            messagebox.showerror(get_text("error"), f"显示设置对话框出错: {e}")

try:
    from ui.dialogs.debug_dialog import show_debug_dialog
except ImportError as e:
    logger.error(f"导入调试信息对话框模块失败: {e}")
    
    # 提供兼容函数
    def show_debug_dialog(parent=None, config_path=None):
        """显示调试信息对话框"""
        try:
            from pyquick import show_debug_info
            show_debug_info()
        except Exception as e:
            logger.error(f"显示调试信息出错: {e}")
            messagebox.showerror(get_text("error"), f"显示调试信息出错: {e}")

# 导出所有对话框函数
__all__ = [
    'show_about_dialog',
    'show_settings_dialog',
    'show_debug_dialog'
] 