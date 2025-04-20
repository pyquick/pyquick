"""
PyQuick 关于对话框模块

提供应用程序的关于信息窗口
"""
import os
import sys
import tkinter as tk
from tkinter import ttk
import datetime
import webbrowser
import threading

# 获取根目录并添加到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from log import get_logger
from lang import get_text
from ui.dialogs.base import BaseDialog, center_window

# 获取日志记录器
logger = get_logger()

class AboutDialog(BaseDialog):
    """关于对话框类"""
    
    def __init__(self, parent=None):
        """
        初始化关于对话框
        
        参数:
            parent: 父窗口
        """
        super().__init__(
            parent=parent,
            title=get_text("about"),
            icon_path="pyquick.ico",
            modal=True
        )
        
        # 图片资源
        self.logo_image = None
    
    def create_dialog(self):
        """创建关于对话框"""
        dialog = super().create_dialog()
        if not dialog:
            return
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # 应用图标
        if os.path.exists("magic.png"):
            try:
                self.logo_image = tk.PhotoImage(file="magic.png")
                logo_label = ttk.Label(main_frame, image=self.logo_image)
                logo_label.pack(pady=(0, 10))
            except Exception as e:
                logger.error(f"加载应用图标失败: {e}")
        
        # 应用名称和版本
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=(0, 10))
        
        app_name = ttk.Label(title_frame, text="PyQuick", font=("Helvetica", 16, "bold"))
        app_name.pack()
        
        version_label = ttk.Label(title_frame, text=f"{get_text('version')}: Dev (App build:2020)")
        version_label.pack()
        
        # 计算过期时间
        expiry_date = datetime.datetime(2025, 8, 13)
        days_remaining = (expiry_date - datetime.datetime.now()).days
        expiry_label = ttk.Label(title_frame, text=f"{get_text('expiration_time')}: 2025.8.13 ({days_remaining} {get_text('days')})")
        expiry_label.pack()
        
        # 项目链接
        link_frame = ttk.Frame(main_frame)
        link_frame.pack(fill="x", pady=5)
        
        link_label = ttk.Label(link_frame, text=get_text("project_website"), foreground="blue", cursor="hand2")
        link_label.pack()
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/pyquick/pyquick/"))
        
        # 添加警告（如果即将过期）
        if days_remaining <= 14:
            warning_frame = ttk.Frame(main_frame)
            warning_frame.pack(fill="x", pady=5)
            
            warning_label = ttk.Label(warning_frame, text=get_text("version_expire_soon"), foreground="red")
            warning_label.pack()
        
        # 开发版警告
        dev_frame = ttk.Frame(main_frame)
        dev_frame.pack(fill="x", pady=5)
        
        dev_label1 = ttk.Label(dev_frame, text=get_text("dev_version_warning"), foreground="red")
        dev_label1.pack()
        
        dev_label2 = ttk.Label(dev_frame, text=get_text("report_issues_prompt"), foreground="red")
        dev_label2.pack()
        
        # GPL 许可证
        license_frame = ttk.LabelFrame(main_frame, text=get_text("license"))
        license_frame.pack(fill="both", expand=True, pady=10)
        
        # 创建带滚动条的文本框
        license_text = tk.Text(license_frame, wrap="word", width=60, height=15)
        license_text.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(license_frame, command=license_text.yview)
        scrollbar.pack(side="right", fill="y")
        license_text.config(yscrollcommand=scrollbar.set)
        
        # 加载许可证文本
        try:
            with open("gpl3.txt", "r", encoding="utf-8") as f:
                license_content = f.read()
                license_text.insert("1.0", license_content)
        except Exception as e:
            logger.error(f"加载许可证文件失败: {e}")
            license_text.insert("1.0", get_text("license_load_failed"))
        
        license_text.config(state="disabled")  # 设为只读
        
        # 版权信息
        copyright_label = ttk.Label(main_frame, text="®Pyquick™ 2025. All rights reserved.")
        copyright_label.pack(pady=(10, 5))
        
        # 确定按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ok_button = ttk.Button(button_frame, text=get_text("ok"), command=self.on_close, width=15)
        ok_button.pack(side="right")
        
        # 居中显示窗口
        center_window(dialog, self.parent)
        
        return dialog

def show_about_dialog(parent=None):
    """
    显示关于对话框
    
    参数:
        parent: 父窗口
    """
    try:
        # 创建并显示对话框
        if threading.current_thread() is threading.main_thread():
            about_dialog = AboutDialog(parent)
            about_dialog.show()
        else:
            # 如果在非主线程中调用，则在主线程中执行
            if parent:
                parent.after(0, lambda: AboutDialog(parent).show())
            else:
                # 没有父窗口时，创建新窗口运行
                logger.warning("在非主线程中调用关于对话框，且没有提供父窗口")
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                AboutDialog(root).show()
                root.mainloop()
    except Exception as e:
        logger.error(f"显示关于对话框时出错: {e}")
        return None 