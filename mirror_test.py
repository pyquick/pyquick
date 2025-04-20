#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
镜像测试模块 - 测试Python和PIP镜像的连接性和速度
提供用户友好的界面来测试多个镜像，并选择最佳镜像
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import time
import json
from urllib.parse import urlparse
import logging
from functools import partial

# 导入必要的语言模块
from lang import get_text, register_language_callback

# 配置日志记录
logger = logging.getLogger(__name__)

def show_mirror_test_window(parent, mirror_type="python", config_path=None):
    """显示镜像测试窗口
    
    参数:
        parent: 父窗口
        mirror_type: 镜像类型（"python"或"pip"）
        config_path: 配置文件路径
    """
    from settings import get_python_mirrors, get_pip_mirrors, set_active_mirror, get_active_mirror
    
    test_window = tk.Toplevel(parent)
    test_window.title(get_text("test_mirror_delay").format("Python" if mirror_type == "python" else "Pip"))
    test_window.resizable(True, True)
    test_window.transient(parent)
    test_window.grab_set()
    
    # 创建主框架
    main_frame = ttk.Frame(test_window, padding=20)
    main_frame.pack(expand=True, fill="both")
    
    # 添加标题
    title_text = get_text("test_mirror_delay").format("Python" if mirror_type == "python" else "Pip")
    ttk.Label(main_frame, text=title_text, font=("微软雅黑", 12, "bold")).pack(pady=(0, 10))
    
    # 获取镜像列表
    mirrors = get_python_mirrors() if mirror_type == "python" else get_pip_mirrors()
    
    # 创建结果框架
    result_frame = ttk.Frame(main_frame)
    result_frame.pack(fill="both", expand=True, pady=10)
    
    # 创建表格标题
    ttk.Label(result_frame, text=get_text("mirror_address"), width=40, anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(result_frame, text=get_text("delay"), width=10, anchor="center").grid(row=0, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(result_frame, text=get_text("status"), width=10, anchor="center").grid(row=0, column=2, sticky="w", padx=5, pady=5)
    
    ttk.Separator(result_frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
    
    # 创建进度条
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", pady=10)
    
    status_var = tk.StringVar(value=get_text("ready_to_test"))
    status_label = ttk.Label(main_frame, textvariable=status_var)
    status_label.pack(pady=5)
    
    # 创建按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)
    
    # 执行测试
    def run_test():
        # 禁用测试按钮
        test_button.config(state="disabled")
        set_button.config(state="disabled")
        
        # 清理之前的结果
        for widget in result_frame.winfo_children()[3:]:  # 跳过标题和分隔线
            widget.destroy()
        
        results = []
        progress_step = 100.0 / len(mirrors)
        
        def test_thread():
            best_mirror = None
            best_delay = float('inf')
            
            for i, mirror in enumerate(mirrors):
                current_progress = progress_step * i
                test_window.after(0, lambda p=current_progress, m=mirror: 
                                [progress_var.set(p), 
                                 status_var.set(get_text("testing").format(m))])
                
                result = test_mirror_delay(mirror, mirror_type)
                
                if (result["connection_success"] and result["download_success"] and 
                    result["delay"] > 0 and result["delay"] < best_delay):
                    best_delay = result["delay"]
                    best_mirror = mirror
                
                results.append((mirror, result))
                test_window.after(0, lambda m=mirror, r=result, row=i+2: update_result(m, r, row))
            
            # 完成所有测试
            test_window.after(0, lambda: [
                progress_var.set(100),
                status_var.set(get_text("test_completed")),
                test_button.config(state="normal"),
                set_button.config(state="normal", command=lambda b=best_mirror: set_best_mirror(b))
            ])
        
        # 更新结果表格
        def update_result(mirror, result, row):
            ttk.Label(result_frame, text=mirror, width=40, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=2)
            
            delay = result["delay"]
            connection_success = result["connection_success"]
            download_success = result["download_success"]
            
            if connection_success and download_success:
                delay_str = f"{delay:.2f}{get_text('second')}"
                status_str = get_text("normal")
                color = "#009900"  # 绿色
            elif connection_success and not download_success:
                delay_str = f"{delay:.2f}{get_text('second')}"
                status_str = get_text("connect_ok_but_download_failed")
                color = "#FF9900"  # 橙色
            else:
                delay_str = get_text("timeout")
                status_str = get_text("failed")
                color = "#CC0000"  # 红色
            
            delay_label = ttk.Label(result_frame, text=delay_str, width=10, anchor="center")
            delay_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            
            status_label = ttk.Label(result_frame, text=status_str, width=10, anchor="center", foreground=color)
            status_label.grid(row=row, column=2, sticky="w", padx=5, pady=2)
        
        # 启动测试线程
        threading.Thread(target=test_thread, daemon=True).start()
    
    # 设置最佳镜像
    def set_best_mirror(best_mirror):
        if best_mirror:
            set_active_mirror(mirror_type, best_mirror)
            messagebox.showinfo(
                get_text("success"), 
                get_text("set_mirror_success").format(mirror_type.upper(), best_mirror)
            )
            test_window.destroy()
    
    # 底部按钮
    test_button = ttk.Button(button_frame, text=get_text("start_test"), command=run_test)
    test_button.pack(side="left", padx=5)
    
    set_button = ttk.Button(button_frame, text=get_text("set_best_mirror"), state="disabled")
    set_button.pack(side="left", padx=5)
    
    ttk.Button(button_frame, text=get_text("close"), command=test_window.destroy).pack(side="right", padx=5)
    
    # 设置居中
    test_window.update_idletasks()
    width = test_window.winfo_width()
    height = test_window.winfo_height()
    x = (test_window.winfo_screenwidth() // 2) - (width // 2)
    y = (test_window.winfo_screenheight() // 2) - (height // 2)
    test_window.geometry('+{}+{}'.format(x, y))

def test_mirror_delay(mirror_url, mirror_type="python"):
    """测试镜像延迟和可用性"""
    result = {"delay": -1, "connection_success": False, "download_success": False}
    
    try:
        start_time = time.time()
        response = requests.get(mirror_url, timeout=5, verify=False)
        if response.status_code == 200:
            result["delay"] = time.time() - start_time
            result["connection_success"] = True
        else:
            logger.warning(get_text("mirror_connection_test_failed").format(response.status_code))
            return result
    except requests.RequestException as e:
        logger.warning(get_text("mirror_connection_test_exception").format(e))
        return result
    
    try:
        if mirror_type == "python":
            version_test_url = f"{mirror_url}/3.10.0"
            test_response = requests.get(version_test_url, timeout=5, verify=False)
            result["download_success"] = (test_response.status_code == 200 and 
                                     (b"python-3.10.0" in test_response.content or
                                      b"Python-3.10.0" in test_response.content))
        else:  # pip
            test_url = f"{mirror_url}/pip"
            test_response = requests.get(test_url, timeout=5, verify=False)
            result["download_success"] = (test_response.status_code == 200)
    except requests.RequestException as e:
        logger.warning(get_text("mirror_download_test_exception").format(e))
        
    return result

if __name__ == "__main__":
    # 测试运行
    root = tk.Tk()
    root.title("Mirror Test")
    
    def open_test():
        show_mirror_test_window(root, "python")
    
    button = ttk.Button(root, text="Test Mirrors", command=open_test)
    button.pack(padx=20, pady=20)
    
    root.mainloop()