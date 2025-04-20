"""
PyQuick 应用程序示例
演示如何在应用程序中使用对话框模块
"""
import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, Menu

# 导入对话框模块
from ui.dialogs import show_about_dialog, show_settings_dialog, show_debug_dialog

# 设置日志
logger = logging.getLogger("PyQuick")

# 获取配置路径
def get_config_path():
    """获取配置路径"""
    config_path_base = os.path.join(os.environ["APPDATA"], "pyquick")
    config_path = os.path.join(config_path_base, "2020")  # 版本号
    
    # 确保目录存在
    if not os.path.exists(config_path):
        os.makedirs(config_path)
        
    return config_path

def restart_app():
    """重启应用程序"""
    python = sys.executable
    script = os.path.abspath(sys.argv[0])
    os.execl(python, python, script)

def main():
    """主程序入口"""
    # 获取配置路径
    config_path = get_config_path()
    
    # 创建主窗口
    root = tk.Tk()
    root.title("PyQuick - Python安装与管理工具")
    root.geometry("800x600")
    
    # 设置窗口图标
    if os.path.exists("pyquick.ico"):
        root.iconbitmap("pyquick.ico")
    
    # 创建菜单栏
    menu_bar = Menu(root)
    
    # 文件菜单
    file_menu = Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="退出", command=root.quit)
    menu_bar.add_cascade(label="文件", menu=file_menu)
    
    # 设置菜单
    settings_menu = Menu(menu_bar, tearoff=0)
    settings_menu.add_command(
        label="设置", 
        command=lambda: show_settings_dialog(root, config_path, restart_app)
    )
    menu_bar.add_cascade(label="设置", menu=settings_menu)
    
    # 帮助菜单
    help_menu = Menu(menu_bar, tearoff=0)
    help_menu.add_command(
        label="关于", 
        command=lambda: show_about_dialog(root)
    )
    help_menu.add_command(
        label="调试信息", 
        command=lambda: show_debug_dialog(root, config_path)
    )
    menu_bar.add_cascade(label="帮助", menu=help_menu)
    
    # 设置菜单栏
    root.config(menu=menu_bar)
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill="both", expand=True)
    
    # 添加一些界面元素
    title_label = ttk.Label(
        main_frame, 
        text="PyQuick - Python安装与管理工具", 
        font=("Helvetica", 16, "bold")
    )
    title_label.pack(pady=(0, 20))
    
    # 添加按钮来打开对话框
    button_frame = ttk.Frame(main_frame)
    button_frame.pack()
    
    about_button = ttk.Button(
        button_frame, 
        text="关于", 
        command=lambda: show_about_dialog(root)
    )
    about_button.grid(row=0, column=0, padx=10, pady=10)
    
    settings_button = ttk.Button(
        button_frame, 
        text="设置", 
        command=lambda: show_settings_dialog(root, config_path, restart_app)
    )
    settings_button.grid(row=0, column=1, padx=10, pady=10)
    
    debug_button = ttk.Button(
        button_frame, 
        text="调试信息", 
        command=lambda: show_debug_dialog(root, config_path)
    )
    debug_button.grid(row=0, column=2, padx=10, pady=10)
    
    # 设置关闭事件
    def on_closing():
        """关闭窗口时的处理"""
        logger.info("应用程序关闭")
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main() 