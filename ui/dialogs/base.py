"""
PyQuick 基础对话框模块

提供对话框的基础功能和工具方法
"""
import os
import sys
import tkinter as tk
from tkinter import ttk

# 获取根目录并添加到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from log import get_logger

# 获取日志记录器
logger = get_logger()

def center_window(window, parent=None):
    """
    居中显示窗口
    
    参数:
        window: 要居中的窗口
        parent: 父窗口，如果有的话
    """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    
    if parent:
        x = parent.winfo_x() + (parent.winfo_width() - width) // 2
        y = parent.winfo_y() + (parent.winfo_height() - height) // 2
    else:
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
    
    window.geometry(f'{width}x{height}+{x}+{y}')

class BaseDialog:
    """对话框基类"""
    
    def __init__(self, parent=None, title="Dialog", icon_path="pyquick.ico", modal=True):
        """
        初始化对话框
        
        参数:
            parent: 父窗口
            title: 对话框标题
            icon_path: 图标路径
            modal: 是否为模态对话框
        """
        self.parent = parent
        self.title = title
        self.icon_path = icon_path
        self.modal = modal
        self.dialog = None
        
    def create_dialog(self):
        """创建对话框，子类应重写此方法"""
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift()
            return
        
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        
        # 设置图标
        if os.path.exists(self.icon_path):
            try:
                self.dialog.iconbitmap(self.icon_path)
            except Exception as e:
                logger.error(f"设置图标失败: {e}")
        
        # 设置为模态窗口
        if self.modal and self.parent:
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
        
        # 关闭按钮动作
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        return self.dialog
    
    def on_close(self):
        """关闭对话框"""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
    
    def show(self):
        """显示对话框"""
        self.create_dialog()
        center_window(self.dialog, self.parent)
        
        # 设置焦点
        self.dialog.focus_set()
        
        # 如果是模态对话框，等待窗口关闭
        if self.modal and self.parent:
            self.parent.wait_window(self.dialog)
            
        return self.dialog 