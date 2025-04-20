"""
ToolTip.py - 工具提示实现

提供创建工具提示的功能，当鼠标悬停在控件上时显示提示信息
"""

import tkinter as tk

class ToolTip:
    """工具提示类"""
    
    def __init__(self, widget, text):
        """
        初始化工具提示
        
        参数:
            widget: 要添加提示的控件
            text: 提示文本
        """
        self.widget = widget
        self.text = text
        self.tip_window = None
        
        # 绑定鼠标事件
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
    
    def show_tip(self, event=None):
        """显示工具提示"""
        if self.tip_window or not self.text:
            return
            
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        # 创建顶层窗口
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        
        # 添加标签
        label = tk.Label(
            self.tip_window, 
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            padx=5,
            pady=5
        )
        label.pack()
    
    def hide_tip(self, event=None):
        """隐藏工具提示"""
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None
