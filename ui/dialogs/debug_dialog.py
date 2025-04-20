"""
PyQuick 调试信息对话框模块

提供系统和应用程序调试信息窗口
"""
import os
import sys
import tkinter as tk
from tkinter import ttk
import threading
import platform
import psutil
import gc
import logging
import time
import datetime
import subprocess

# 获取根目录并添加到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from log import get_logger
from lang import get_text
from ui.dialogs.base import BaseDialog, center_window
import settings

# 获取日志记录器
logger = get_logger()

class DebugDialog(BaseDialog):
    """调试信息对话框类"""
    
    def __init__(self, parent=None, config_path=None):
        """
        初始化调试信息对话框
        
        参数:
            parent: 父窗口
            config_path: 配置文件路径
        """
        super().__init__(
            parent=parent,
            title=get_text("debug_info"),
            icon_path="pyquick.ico",
            modal=False  # 非模态对话框，允许用户与主窗口交互
        )
        self.config_path = config_path
        
        # 用于存储UI元素的引用
        self.notebook = None
        self.system_info_text = None
        self.app_info_text = None
        self.log_info_text = None
        
        # 用于系统信息更新的变量
        self.update_interval = 1000  # 毫秒
        self.update_task_id = None
        self.log_level_var = None
        
        # 当前主题
        self.is_dark_theme = False
        
        # 颜色方案
        self.colors = {}
        
    def create_dialog(self):
        """创建调试信息对话框"""
        dialog = super().create_dialog()
        if not dialog:
            return
        
        # 设置窗口大小
        dialog.geometry("800x600")
        dialog.resizable(True, True)
        
        # 设置当前主题
        current_theme = settings.get_setting("theme", "light")
        self.is_dark_theme = current_theme == "dark"
        
        # 定义颜色方案 - 根据主题设置不同的颜色
        self.colors = {
            "title": "#0066cc" if not self.is_dark_theme else "#66b2ff",
            "section": "#555555" if not self.is_dark_theme else "#ffffff",
            "label": "#333333" if not self.is_dark_theme else "#cccccc", 
            "value": "#000000" if not self.is_dark_theme else "#ffffff",
            "config_section": "#996633" if not self.is_dark_theme else "#ffcc99",
            "dynamic_section": "#009933" if not self.is_dark_theme else "#66ff99",
            "info_log": "#000000" if not self.is_dark_theme else "#ffffff"
        }
        
        # 创建主框架
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(expand=True, fill="both")
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(expand=True, fill="both")
        
        # 创建各选项卡内容
        self._create_system_info_tab()
        self._create_app_info_tab()
        self._create_log_info_tab()
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        close_button = ttk.Button(
            button_frame, 
            text=get_text("close"), 
            command=self.on_close,
            width=15
        )
        close_button.pack(side="right", padx=5)
        
        # 居中显示窗口
        center_window(dialog, self.parent)
        
        # 开始更新系统信息
        self._start_update_system_info()
        
        # 设置关闭事件
        dialog.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        return dialog
    
    def _create_system_info_tab(self):
        """创建系统信息选项卡"""
        system_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(system_frame, text=get_text("system_info"))
        
        # 创建含滚动条的系统信息框架
        system_info_frame = ttk.Frame(system_frame)
        system_info_frame.pack(fill="both", expand=True)
        
        # 创建文本框显示系统信息
        self.system_info_text = tk.Text(system_info_frame, wrap=tk.WORD, width=70, height=20)
        self.system_info_text.pack(side=tk.LEFT, fill="both", expand=True)
        self.system_info_text.config(state=tk.DISABLED)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(system_info_frame, command=self.system_info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.system_info_text.config(yscrollcommand=scrollbar.set)
        
        # 更新系统信息
        self._update_system_info()
    
    def _create_app_info_tab(self):
        """创建应用信息选项卡"""
        app_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(app_frame, text=get_text("app_info"))
        
        # 创建刷新按钮
        app_refresh_frame = ttk.Frame(app_frame)
        app_refresh_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            app_refresh_frame, 
            text=get_text("refresh_info"), 
            command=self._refresh_app_info
        ).pack(side=tk.RIGHT, padx=5)
        
        # 创建含滚动条的应用信息框架
        app_info_frame = ttk.Frame(app_frame)
        app_info_frame.pack(fill="both", expand=True)
        
        self.app_info_text = tk.Text(app_info_frame, wrap=tk.WORD, width=70, height=20)
        self.app_info_text.pack(side=tk.LEFT, fill="both", expand=True)
        self.app_info_text.config(state=tk.DISABLED)
        
        # 添加滚动条
        app_scrollbar = ttk.Scrollbar(app_info_frame, command=self.app_info_text.yview)
        app_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.app_info_text.config(yscrollcommand=app_scrollbar.set)
        
        # 更新应用信息
        self._update_app_info()
    
    def _create_log_info_tab(self):
        """创建日志信息选项卡"""
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text=get_text("log_info"))
        
        # 创建日志控制面板
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill="x", pady=5)
        
        # 添加日志级别选择
        self.log_level_var = tk.StringVar(value="all")
        
        ttk.Label(log_control_frame, text=get_text("log_filter")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            log_control_frame, 
            text=get_text("show_errors_only"), 
            variable=self.log_level_var, 
            value="error"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            log_control_frame, 
            text=get_text("show_errors_warnings"), 
            variable=self.log_level_var, 
            value="warning"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            log_control_frame, 
            text=get_text("show_all_logs"), 
            variable=self.log_level_var, 
            value="all"
        ).pack(side=tk.LEFT, padx=5)
        
        # 刷新日志按钮
        ttk.Button(
            log_control_frame, 
            text=get_text("refresh_log"), 
            command=self._refresh_log_info
        ).pack(side=tk.RIGHT, padx=5)
        
        # 创建含滚动条的日志信息框架
        log_info_frame = ttk.Frame(log_frame)
        log_info_frame.pack(fill="both", expand=True)
        
        self.log_info_text = tk.Text(log_info_frame, wrap=tk.WORD, width=70, height=20)
        self.log_info_text.pack(side=tk.LEFT, fill="both", expand=True)
        self.log_info_text.config(state=tk.DISABLED)
        
        # 添加滚动条
        log_scrollbar = ttk.Scrollbar(log_info_frame, command=self.log_info_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_info_text.config(yscrollcommand=log_scrollbar.set)
        
        # 更新日志信息
        self._update_log_info()
    
    def _update_system_info(self):
        """更新系统信息"""
        if not self.system_info_text or not self.dialog or not self.dialog.winfo_exists():
            return
        
        # 清空文本框
        self.system_info_text.config(state=tk.NORMAL)
        self.system_info_text.delete(1.0, tk.END)
        
        # 添加基本系统信息标题
        self.system_info_text.insert(tk.END, f"{get_text('basic_system_info')}\n\n", f"title")
        
        # 系统信息
        self.system_info_text.insert(tk.END, f"{get_text('os')}", f"label")
        self.system_info_text.insert(tk.END, f"{platform.platform()}\n", f"value")
        
        self.system_info_text.insert(tk.END, f"{get_text('system_arch')}", f"label")
        self.system_info_text.insert(tk.END, f"{platform.machine()}\n", f"value")
        
        self.system_info_text.insert(tk.END, f"{get_text('processor')}", f"label")
        self.system_info_text.insert(tk.END, f"{platform.processor()}\n", f"value")
        
        self.system_info_text.insert(tk.END, f"{get_text('python_version')}", f"label")
        self.system_info_text.insert(tk.END, f"{platform.python_version()}\n", f"value")
        
        self.system_info_text.insert(tk.END, f"{get_text('tkinter_version')}", f"label")
        self.system_info_text.insert(tk.END, f"{tk.TkVersion}\n", f"value")
        
        # CPU核心数
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_count_logical = psutil.cpu_count(logical=True)
        self.system_info_text.insert(tk.END, f"{get_text('cpu_cores')}", f"label")
        self.system_info_text.insert(
            tk.END, 
            f"{cpu_count_physical} {get_text('physical_cores')}, {cpu_count_logical} {get_text('logical_cores')}\n\n",
            f"value"
        )
        
        # 添加实时系统信息标题
        self.system_info_text.insert(tk.END, f"{get_text('realtime_system_info')}\n\n", f"title")
        
        # CPU使用率
        self.system_info_text.insert(tk.END, f"{get_text('cpu_usage')}", f"label")
        self.system_info_text.insert(tk.END, f"{psutil.cpu_percent()}%\n", f"value")
        
        # 内存信息
        memory = psutil.virtual_memory()
        self.system_info_text.insert(tk.END, f"{get_text('memory')}", f"label")
        self.system_info_text.insert(
            tk.END, 
            f"{memory.percent}% {get_text('used')} ({memory.used / 1024 / 1024:.2f} MB / {memory.total / 1024 / 1024:.2f} MB)\n",
            f"value"
        )
        
        # 应用内存使用
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        self.system_info_text.insert(tk.END, f"{get_text('pyquick_memory')}", f"label")
        self.system_info_text.insert(
            tk.END, 
            f"{memory_info.rss / 1024 / 1024:.2f} MB\n",
            f"value"
        )
        
        # 磁盘信息
        disk = psutil.disk_usage('/')
        self.system_info_text.insert(tk.END, f"{get_text('disk')}", f"label")
        self.system_info_text.insert(
            tk.END, 
            f"{disk.percent}% {get_text('used')} ({disk.used / 1024 / 1024 / 1024:.2f} GB / {disk.total / 1024 / 1024 / 1024:.2f} GB)\n",
            f"value"
        )
        
        # 设置文本标签样式
        self.system_info_text.tag_configure("title", foreground=self.colors["title"], font=("Helvetica", 12, "bold"))
        self.system_info_text.tag_configure("label", foreground=self.colors["label"], font=("Helvetica", 10, "bold"))
        self.system_info_text.tag_configure("value", foreground=self.colors["value"], font=("Helvetica", 10))
        
        self.system_info_text.config(state=tk.DISABLED)
    
    def _update_app_info(self):
        """更新应用信息"""
        if not self.app_info_text or not self.dialog or not self.dialog.winfo_exists():
            return
        
        # 清空文本框
        self.app_info_text.config(state=tk.NORMAL)
        self.app_info_text.delete(1.0, tk.END)
        
        # 应用程序信息标题
        self.app_info_text.insert(tk.END, f"{get_text('app_info_title')}\n\n", "title")
        
        # 应用程序名称和版本
        self.app_info_text.insert(tk.END, f"{get_text('app_name')}", "label")
        self.app_info_text.insert(tk.END, "PyQuick\n", "value")
        
        self.app_info_text.insert(tk.END, f"{get_text('app_version')}", "label")
        self.app_info_text.insert(tk.END, "Dev (App build:2020)\n", "value")
        
        # 配置路径
        self.app_info_text.insert(tk.END, f"{get_text('config_path')}", "label")
        self.app_info_text.insert(tk.END, f"{self.config_path}\n", "value")
        
        # 工作目录
        self.app_info_text.insert(tk.END, f"{get_text('working_dir')}", "label")
        self.app_info_text.insert(tk.END, f"{os.getcwd()}\n\n", "value")
        
        # 配置文件信息标题
        self.app_info_text.insert(tk.END, f"{get_text('config_file_info')}\n\n", "config_section")
        
        # 多线程配置
        self.app_info_text.insert(tk.END, f"{get_text('multithread_enabled')}", "label")
        try:
            thread_file = os.path.join(self.config_path, "allowthread.txt")
            if os.path.exists(thread_file):
                with open(thread_file, "r") as f:
                    thread_config = f.read().strip().lower() == "true"
                    self.app_info_text.insert(tk.END, f"{thread_config}\n", "value")
            else:
                self.app_info_text.insert(tk.END, f"{get_text('config_not_found')}\n", "value")
        except Exception as e:
            self.app_info_text.insert(tk.END, f"{get_text('multithread_read_fail')}{e}\n", "value")
        
        # 主题配置
        self.app_info_text.insert(tk.END, f"{get_text('theme_setting')}", "label")
        try:
            theme_file = os.path.join(self.config_path, "theme.txt")
            if os.path.exists(theme_file):
                with open(theme_file, "r") as f:
                    theme = f.read().strip()
                    self.app_info_text.insert(tk.END, f"{theme}\n", "value")
            else:
                self.app_info_text.insert(tk.END, f"{get_text('config_not_found')}\n", "value")
        except Exception as e:
            self.app_info_text.insert(tk.END, f"{get_text('theme_read_fail')}{e}\n", "value")
        
        # Python镜像配置
        self.app_info_text.insert(tk.END, f"{get_text('python_mirror')}", "label")
        try:
            mirror_file = os.path.join(self.config_path, "pythonmirror.txt")
            if os.path.exists(mirror_file):
                with open(mirror_file, "r") as f:
                    mirror = f.read().strip() or get_text("default_source")
                    self.app_info_text.insert(tk.END, f"{mirror}\n", "value")
            else:
                self.app_info_text.insert(tk.END, f"{get_text('config_not_found')}\n", "value")
        except Exception as e:
            self.app_info_text.insert(tk.END, f"{get_text('python_mirror_read_fail')}{e}\n", "value")
        
        # Pip镜像配置
        self.app_info_text.insert(tk.END, f"{get_text('pip_mirror_config')}", "label")
        try:
            mirror_file = os.path.join(self.config_path, "pipmirror.txt")
            if os.path.exists(mirror_file):
                with open(mirror_file, "r") as f:
                    mirror = f.read().strip() or get_text("default_source")
                    self.app_info_text.insert(tk.END, f"{mirror}\n", "value")
            else:
                self.app_info_text.insert(tk.END, f"{get_text('config_not_found')}\n", "value")
        except Exception as e:
            self.app_info_text.insert(tk.END, f"{get_text('pip_mirror_read_fail')}{e}\n", "value")
        
        # 语言配置
        self.app_info_text.insert(tk.END, f"{get_text('language_setting')}", "label")
        try:
            language_file = os.path.join(self.config_path, "language.txt")
            if os.path.exists(language_file):
                with open(language_file, "r") as f:
                    language = f.read().strip() or "zh_CN"
                    self.app_info_text.insert(tk.END, f"{language}\n", "value")
            else:
                self.app_info_text.insert(tk.END, f"{get_text('config_not_found')}\n", "value")
        except Exception as e:
            self.app_info_text.insert(tk.END, f"{get_text('language_read_fail')}{e}\n", "value")
        
        # 日志大小配置
        self.app_info_text.insert(tk.END, f"{get_text('log_size_limit')}", "label")
        try:
            log_size_file = os.path.join(self.config_path, "log_size.txt")
            if os.path.exists(log_size_file):
                with open(log_size_file, "r") as f:
                    log_size = f.read().strip() or "10"
                    self.app_info_text.insert(tk.END, f"{log_size} MB\n", "value")
            else:
                self.app_info_text.insert(tk.END, f"{get_text('config_not_found')}\n", "value")
        except Exception as e:
            self.app_info_text.insert(tk.END, f"{get_text('log_size_read_fail')}{e}\n", "value")
        
        # 设置文本标签样式
        self.app_info_text.tag_configure("title", foreground=self.colors["title"], font=("Helvetica", 12, "bold"))
        self.app_info_text.tag_configure("config_section", foreground=self.colors["config_section"], font=("Helvetica", 12, "bold"))
        self.app_info_text.tag_configure("label", foreground=self.colors["label"], font=("Helvetica", 10, "bold"))
        self.app_info_text.tag_configure("value", foreground=self.colors["value"], font=("Helvetica", 10))
        
        self.app_info_text.config(state=tk.DISABLED)
    
    def _update_log_info(self, log_level="all"):
        """更新日志信息"""
        if not self.log_info_text or not self.dialog or not self.dialog.winfo_exists():
            return
        
        # 清空文本框
        self.log_info_text.config(state=tk.NORMAL)
        self.log_info_text.delete(1.0, tk.END)
        
        # 查找日志目录
        log_dir = os.path.join(self.config_path, "log")
        if not os.path.exists(log_dir):
            self.log_info_text.insert(tk.END, f"{get_text('no_log_dir')}\n", "error")
            self.log_info_text.config(state=tk.DISABLED)
            return
        
        # 查找最新的日志文件
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if not log_files:
            self.log_info_text.insert(tk.END, f"{get_text('no_log_files')}\n", "error")
            self.log_info_text.config(state=tk.DISABLED)
            return
        
        # 获取最新的日志文件
        latest_log = max([os.path.join(log_dir, f) for f in log_files], key=os.path.getmtime)
        
        # 显示最新日志文件名
        self.log_info_text.insert(tk.END, f"{get_text('latest_log_file')} {os.path.basename(latest_log)}\n\n", "title")
        
        # 读取日志文件
        try:
            with open(latest_log, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
                
                # 根据日志级别过滤
                filtered_lines = []
                if log_level == "error":
                    filtered_lines = [line for line in log_lines if "ERROR" in line]
                elif log_level == "warning":
                    filtered_lines = [line for line in log_lines if "ERROR" in line or "WARNING" in line]
                else:  # all
                    filtered_lines = log_lines
                
                # 显示日志条目数
                if filtered_lines:
                    self.log_info_text.insert(
                        tk.END, 
                        f"{get_text('log_entries').format(log_level)}\n\n", 
                        "section"
                    )
                    
                    # 显示最多100行
                    max_lines = 100
                    if len(filtered_lines) > max_lines:
                        filtered_lines = filtered_lines[-max_lines:]
                        self.log_info_text.insert(tk.END, f"(只显示最新的 {max_lines} 行...)\n\n", "section")
                    
                    # 显示每行日志
                    for line in filtered_lines:
                        if "ERROR" in line:
                            self.log_info_text.insert(tk.END, line, "error")
                        elif "WARNING" in line:
                            self.log_info_text.insert(tk.END, line, "warning")
                        else:
                            self.log_info_text.insert(tk.END, line, "info")
                else:
                    self.log_info_text.insert(
                        tk.END, 
                        f"{get_text('no_log_entries').format(log_level)}\n", 
                        "warning"
                    )
        except Exception as e:
            self.log_info_text.insert(
                tk.END, 
                f"{get_text('log_read_error').format(e)}\n", 
                "error"
            )
        
        # 设置文本标签样式
        self.log_info_text.tag_configure("title", foreground=self.colors["title"], font=("Helvetica", 12, "bold"))
        self.log_info_text.tag_configure("section", foreground=self.colors["section"], font=("Helvetica", 10, "bold"))
        self.log_info_text.tag_configure("error", foreground="red", font=("Courier", 9))
        self.log_info_text.tag_configure("warning", foreground="orange", font=("Courier", 9))
        self.log_info_text.tag_configure("info", foreground=self.colors["info_log"], font=("Courier", 9))
        
        self.log_info_text.config(state=tk.DISABLED)
    
    def _start_update_system_info(self):
        """开始定期更新系统信息"""
        if self.dialog and self.dialog.winfo_exists():
            self._update_system_info()
            self.update_task_id = self.dialog.after(self.update_interval, self._start_update_system_info)
    
    def _refresh_app_info(self):
        """刷新应用信息"""
        self._update_app_info()
        gc.collect()  # 执行垃圾回收
    
    def _refresh_log_info(self):
        """刷新日志信息"""
        self._update_log_info(self.log_level_var.get())
        gc.collect()  # 执行垃圾回收
    
    def _on_window_close(self):
        """关闭窗口"""
        # 停止定时更新任务
        if self.update_task_id and self.dialog and self.dialog.winfo_exists():
            self.dialog.after_cancel(self.update_task_id)
            self.update_task_id = None
        
        # 执行垃圾回收
        gc.collect()
        
        # 关闭窗口
        self.on_close()

def show_debug_dialog(parent=None, config_path=None):
    """
    显示调试信息对话框
    
    参数:
        parent: 父窗口
        config_path: 配置文件路径
    """
    try:
        # 创建并显示对话框
        if threading.current_thread() is threading.main_thread():
            debug_dialog = DebugDialog(parent, config_path)
            debug_dialog.show()
        else:
            # 如果在非主线程中调用，则在主线程中执行
            if parent:
                parent.after(0, lambda: DebugDialog(parent, config_path).show())
            else:
                # 没有父窗口时，创建新窗口运行
                logger.warning("在非主线程中调用调试信息对话框，且没有提供父窗口")
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                debug_dialog = DebugDialog(root, config_path)
                debug_dialog.show()
                root.mainloop()
    except Exception as e:
        logger.error(f"显示调试信息对话框时出错: {e}")
        return None 