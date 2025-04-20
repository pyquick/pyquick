#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyQuick - Python安装与管理工具
主程序入口

此模块是应用程序的主入口点，负责初始化界面和功能
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import platform
import datetime

# 将当前目录添加到模块搜索路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 导入必要的模块
from log import get_logger
from lang import get_text, set_language

# 获取日志记录器
logger = get_logger()

def get_system_build():
    """获取Windows系统内部版本号"""
    try:
        build = int(str(platform.platform().split("-")[2]).split(".")[2])
        return build
    except:
        return 22000  # 默认返回一个较高的版本号

def main():
    """应用程序主函数"""
    # 记录启动信息
    logger.info("PyQuick应用程序启动")
    
    # 检查过期时间
    if datetime.datetime.now() >= datetime.datetime(2025, 8, 13):
        from ab.expire import show
        show(code="0x0000001A", mode="err", info="PyQuick is expired.")
        return 1
    
    # 获取系统版本信息
    build = get_system_build()
    if build < 9600:
        from ab.expire import show
        show(code="0x0000002A", mode="err", info="Unexpected Happened.")
        return 1
    
    # 创建根窗口
    root = tk.Tk()
    root.title("PyQuick - Python安装与管理工具")
    root.resizable(False, False)
    
    # 设置图标
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyquick.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    # 创建配置目录
    version_pyquick = "2020"
    config_path_base = os.path.join(os.environ["APPDATA"], "pyquick")
    config_path = os.path.join(config_path_base, version_pyquick)
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    
    # 创建菜单栏
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # 创建菜单项
    help_menu = tk.Menu(menubar, tearoff=0)
    settings_menu = tk.Menu(menubar, tearoff=0)
    
    menubar.add_cascade(label=get_text("settings_menu"), menu=settings_menu)
    menubar.add_cascade(label=get_text("help_menu"), menu=help_menu)
    
    # 导入对话框模块
    try:
        from ui.dialogs import show_about_dialog, show_settings_dialog, show_debug_dialog
        
        # 添加菜单项
        help_menu.add_command(label=get_text("about"), command=lambda: show_about_dialog(root))
        help_menu.add_separator()
        help_menu.add_command(label=get_text("debug_info"), command=lambda: show_debug_dialog(root))
        
        # 添加设置选项
        settings_menu.add_command(label=get_text("settings"), command=lambda: show_settings_dialog(root, config_path))
    except ImportError as e:
        logger.error(f"导入对话框模块失败: {e}")
        # 导入原始模块
        from pyquick import show_about, show_debug_info, settings1
        
        help_menu.add_command(label=get_text("about"), command=show_about)
        help_menu.add_separator()
        help_menu.add_command(label=get_text("debug_info"), command=show_debug_info)
        settings_menu.add_command(label=get_text("settings"), command=settings1)
    
    # 创建主选项卡
    note = ttk.Notebook(root)
    note.pack(expand=True, fill="both")
    
    # 导入主要功能模块
    try:
        # 尝试导入模块化版本
        from modules.download_manager import create_download_tab
        from modules.pip_manager import create_pip_tab
        
        # 创建下载选项卡
        download_frame = create_download_tab(note, config_path)
        note.add(download_frame, text=get_text("python_download"))
        
        # 创建Pip管理选项卡
        pip_frame = create_pip_tab(note, config_path)
        note.add(pip_frame, text=get_text("pip_management"))
    except ImportError as e:
        logger.error(f"导入功能模块失败，使用原始实现: {e}")
        # 导入原始实现
        from pyquick import create_tabs
        create_tabs(root, note, config_path)
    
    # 加载语言设置
    try:
        language_file = os.path.join(config_path, "language.txt")
        if os.path.exists(language_file):
            with open(language_file, "r") as r:
                lang = r.read().strip() or "zh_CN"
                set_language(lang)  # 设置当前语言
                # 更新界面文本
                
                #update_interface_language()  # 在启动时应用语言设置
    except Exception as e:
        logger.error(f"加载语言设置失败: {e}")
    
    # 设置关闭窗口处理
    def on_closing():
        logger.info("关闭应用程序")
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动主循环
    root.mainloop()
    return 0

if __name__ == "__main__":
    sys.exit(main()) 