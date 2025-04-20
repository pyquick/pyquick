"""
PyQuick Settings UI Module

提供设置界面和相关功能
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import requests
import time
import re
from typing import Dict, List, Any, Optional, Callable

from lang import get_text, set_language, register_language_callback
import settings

class PipManagementUI:
    """pip版本管理UI组件"""
    
    def __init__(self, parent, python_tree):
        """初始化"""
        logger.debug(f"Initializing PipManagementUI with parent: {parent}")
        
        self.parent = parent
        self.frame = ttk.LabelFrame(parent, text=get_text("pip_version_management"), padding=10)
        self.frame.pack(fill="x", pady=(0, 15))
        self.python_tree = python_tree  # 保存对python_tree的引用

        # pip版本标签组
        self.pip_version_frame = ttk.Frame(self.frame)
        self.pip_version_frame.pack(fill="x", pady=5)
        
        # pip版本状态标签
        self.pip_versions_label = ttk.Label(self.pip_version_frame, text="")
        self.pip_versions_label.pack(side="left", padx=5)
        
        # 版本选择区域
        version_frame = ttk.Frame(self.frame)
        version_frame.pack(fill="x", pady=5)
        
        ttk.Label(version_frame, text=get_text("select_pip_version")).pack(side="left", padx=5)
        
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            version_frame, 
            textvariable=self.version_var, 
            state="readonly",
            width=20
        )
        self.version_combo.pack(side="left", padx=5)
        
        # 切换按钮
        self.switch_btn = ttk.Button(
            version_frame,
            text=get_text("switch_version"),
            command=self.switch_version
        )
        self.switch_btn.pack(side="left", padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar()
        ttk.Label(
            self.frame,
            textvariable=self.status_var,
            foreground="green"
        ).pack(fill="x", pady=5)
        
        # 加载可用版本
        self.load_versions()

    def load_versions(self, version=None):
        """加载可用pip版本"""
        # 显示正在加载状态
        self.version_combo["values"] = [get_text("loading_versions")]
        self.version_var.set(get_text("loading_versions"))
        self.pip_versions_label.config(text=get_text("loading_versions"))

        def load_versions_thread():
            try:
                if not version:
                    selected = self.python_tree.selection()
                    if not selected:
                        return
                    item = selected[0]
                    version = self.python_tree.item(item, "values")[0]
                    python_path = self.python_tree.item(item, "values")[1]
                else:
                    # 从tree中找到对应版本的路径
                    for item in self.python_tree.get_children():
                        if self.python_tree.item(item, "values")[0] == version:
                            python_path = self.python_tree.item(item, "values")[1]
                            break
                
                available_versions = []
                major, minor = version.split(".")[:2]
                
                # 1. 尝试pip3.xx.exe
                pip_cmd = f"pip{major}.{minor}.exe"
                try:
                    result = subprocess.run(
                        [pip_cmd, "--version"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result.returncode == 0:
                        pip_version = result.stdout.strip().split()[1]
                        if pip_version not in available_versions:
                            available_versions.append(pip_version)
                except Exception:
                    logger.debug(f"通过{pip_cmd}获取版本失败")
                
                # 2. 尝试Scripts目录中的pip.exe
                scripts_dir = os.path.join(os.path.dirname(python_path), "Scripts")
                pip_path = os.path.join(scripts_dir, "pip.exe")
                if os.path.exists(pip_path):
                    try:
                        result = subprocess.run(
                            [pip_path, "--version"],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if result.returncode == 0:
                            pip_version = result.stdout.strip().split()[1]
                            if pip_version not in available_versions:
                                available_versions.append(pip_version)
                    except Exception:
                        logger.debug(f"通过pip.exe获取版本失败")
                
                # 3. 尝试python -m pip
                try:
                    result = subprocess.run(
                        [python_path, "-m", "pip", "--version"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result.returncode == 0:
                        pip_version = result.stdout.strip().split()[1]
                        if pip_version not in available_versions:
                            available_versions.append(pip_version)
                except Exception:
                    logger.debug(f"通过python -m pip获取版本失败")

                # 在主线程中更新UI
                def update_ui():
                    if available_versions:
                        # 对版本号进行排序
                        sorted_versions = sorted(available_versions, 
                            key=lambda x: [int(i) for i in x.split('.')],
                            reverse=True
                        )
                        self.version_combo["values"] = sorted_versions
                        self.version_var.set(sorted_versions[0])
                        self.pip_versions_label.config(
                            text=get_text("available_versions") + ": " + ", ".join(sorted_versions)
                        )
                        self.status_var.set("")
                    else:
                        self.version_combo["values"] = []
                        self.version_var.set("")
                        self.pip_versions_label.config(text=get_text("no_pip_versions_found"))
                        self.status_var.set(get_text("no_pip_versions_found"))

                if self.parent and hasattr(self.parent, 'after'):
                    self.parent.after(0, update_ui)
                
            except Exception as e:
                logger.error(f"加载pip版本失败: {e}")
                def show_error():
                    self.version_combo["values"] = []
                    self.version_var.set("")
                    self.status_var.set(get_text("load_pip_versions_failed"))
                    self.pip_versions_label.config(text=get_text("load_pip_versions_failed"))
                
                if self.parent and hasattr(self.parent, 'after'):
                    self.parent.after(0, show_error)

        # 启动加载线程
        threading.Thread(target=load_versions_thread, daemon=True).start()

    def switch_version(self):
        """切换pip版本"""
        selected = self.python_tree.selection()
        if not selected:
            self.status_var.set(get_text("no_python_selected"))
            return
            
        item = selected[0]
        version = self.python_tree.item(item, "values")[0]
        pip_version = self.version_var.get()
        python_path = self.python_tree.item(item, "values")[1]
        
        if not pip_version:
            self.status_var.set(get_text("select_pip_version_first"))
            return
            
        try:
            # 使用pip install --upgrade pip==version来切换版本
            scripts_dir = os.path.join(os.path.dirname(python_path), "Scripts")
            pip_path = os.path.join(scripts_dir, "pip.exe")
            
            if os.path.exists(pip_path):
                result = subprocess.run(
                    [pip_path, "install", "--upgrade", f"pip=={pip_version}"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # 如果找不到pip.exe，使用python -m pip
                result = subprocess.run(
                    [python_path, "-m", "pip", "install", "--upgrade", f"pip=={pip_version}"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            if result.returncode == 0:
                self.status_var.set(get_text("pip_version_switched").format(version=pip_version))
                # 刷新父窗口中的Python版本列表
                if hasattr(self.parent.master, "scan_python_versions"):
                    self.parent.master.scan_python_versions()
            else:
                raise Exception(result.stderr)
        except Exception as e:
            logger.error(f"切换pip版本失败: {e}")
            self.status_var.set(get_text("pip_version_switch_failed"))
            self.frame.children["!label"].config(foreground="red")  # 设置错误颜色

from log import get_logger

# 获取日志记录器
logger = get_logger()

class SettingsWindow:
    """设置窗口类"""
    
    def __init__(self, parent, config_path, restart_callback=None):
        """初始化设置窗口"""
        self.parent = parent
        self.config_path = config_path
        self.restart_callback = restart_callback
        self.settings_changed = False
        self.language_changed = False
        
        # 创建设置窗口
        self.window = tk.Toplevel(self.parent)
        self.window.title(get_text("settings"))
        self.window.resizable(True, True)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pyquick.ico')
        if os.path.exists(icon_path):
            self.window.iconbitmap(icon_path)
        
        # 设置为模态窗口
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 加载设置
        self.load_settings()
        
        # 创建各选项卡内容
        self.create_general_tab()
        self.create_mirrors_tab()
        self.create_python_tab()
        self.create_log_tab()
        
        # 创建底部按钮
        self.create_bottom_buttons()
        
        # 设置居中
        self.center_window()
        
        # 绑定关闭事件
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
    def load_settings(self):
        """加载当前设置"""
        try:
            # 从settings模块加载所有设置
            settings.load_settings(self.config_path)
            
        except Exception as e:
            logger.error(f"{get_text('settings_read_fail')}: {e}")
            
    def center_window(self):
        """将窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.parent.winfo_screenwidth() // 2) - (width // 2)
        y = (self.parent.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'+{x}+{y}')
        
    def create_bottom_buttons(self):
        """创建底部按钮"""
        button_frame = ttk.Frame(self.window)
        button_frame.pack(side="bottom", fill="x", pady=10)
        
        ttk.Button(
            button_frame,
            text=get_text("cancel"),
            command=self.window.destroy
        ).pack(side="right", padx=5)
        
        ttk.Button(
            button_frame,
            text=get_text("save"),
            command=self.save_settings
        ).pack(side="right", padx=5)

    def create_general_tab(self):
        """创建常规设置选项卡"""
        general_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(general_frame, text=get_text("settings"))
        
        # 语言设置
        lang_frame = ttk.LabelFrame(general_frame, text=get_text("language_settings"), padding=10)
        lang_frame.pack(fill="x", pady=(0, 15))
        
        # 当前语言
        current_lang = settings.get_setting("language", "zh_CN")
        self.language_var = tk.StringVar(value=current_lang)
        
        # 中文选项
        ttk.Radiobutton(
            lang_frame, 
            text=get_text("simplified_chinese"), 
            variable=self.language_var, 
            value="zh_CN"
        ).pack(anchor="w", padx=5, pady=2)
        
        # 英文选项
        ttk.Radiobutton(
            lang_frame, 
            text=get_text("english"), 
            variable=self.language_var, 
            value="en_US"
        ).pack(anchor="w", padx=5, pady=2)
        
        # 主题设置（仅在Windows 11上显示）
        if not settings.is_windows10_or_lower():
            theme_frame = ttk.LabelFrame(general_frame, text=get_text("theme_settings"), padding=10)
            theme_frame.pack(fill="x", pady=(0, 15))
            
            # 当前主题
            current_theme = settings.get_setting("theme", "light")
            self.theme_var = tk.StringVar(value=current_theme)
            
            # 浅色主题选项
            ttk.Radiobutton(
                theme_frame, 
                text=get_text("light_theme"), 
                variable=self.theme_var, 
                value="light"
            ).pack(anchor="w", padx=5, pady=2)
            
            # 深色主题选项
            ttk.Radiobutton(
                theme_frame, 
                text=get_text("dark_theme"), 
                variable=self.theme_var, 
                value="dark"
            ).pack(anchor="w", padx=5, pady=2)
        else:
            # 在Windows 10或更低版本上，仅使用变量，不显示UI
            self.theme_var = tk.StringVar(value=settings.get_setting("theme", "light"))
        
        # 下载设置
        download_frame = ttk.LabelFrame(general_frame, text=get_text("download_settings"), padding=10)
        download_frame.pack(fill="x", pady=(0, 15))
        
        # 多线程下载设置
        self.multithread_var = tk.BooleanVar(value=settings.get_setting("allow_multithreading", True))
        ttk.Checkbutton(
            download_frame, 
            text=get_text("enable_multithreading"), 
            variable=self.multithread_var
        ).pack(anchor="w", padx=5, pady=2)
        
        # pip 更新检查设置
        self.check_pip_var = tk.BooleanVar(value=settings.get_setting("check_pip_update", True))
        ttk.Checkbutton(
            download_frame, 
            text=get_text("enable_pip_version_check"), 
            variable=self.check_pip_var
        ).pack(anchor="w", padx=5, pady=2)
    
    def create_mirrors_tab(self):
        """创建镜像设置选项卡"""
        mirrors_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(mirrors_frame, text=get_text("download_mirror_settings"))
        
        # Python下载镜像设置
        python_mirror_frame = ttk.LabelFrame(mirrors_frame, text=get_text("python_download_mirror"), padding=10)
        python_mirror_frame.pack(fill="x", pady=(0, 15))
        
        # 获取镜像列表
        python_mirrors = settings.get_python_mirrors()
        active_python_mirror = settings.get_active_mirror("python")
        
        # 创建下拉菜单选项
        python_mirror_options = [get_text("default_source")] + python_mirrors[1:]  # 第一个作为默认源
        
        # 当前镜像
        self.python_mirror_var = tk.StringVar()
        if active_python_mirror == python_mirrors[0]:
            self.python_mirror_var.set(get_text("default_source"))
        else:
            self.python_mirror_var.set(active_python_mirror)
        
        # 创建下拉菜单和标签
        ttk.Label(python_mirror_frame, text=get_text("python_download_mirror")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.python_mirror_combo = ttk.Combobox(python_mirror_frame, textvariable=self.python_mirror_var, width=40, state="readonly")
        self.python_mirror_combo["values"] = python_mirror_options
        self.python_mirror_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # 添加默认源说明
        ttk.Label(
            python_mirror_frame, 
            text=f"{get_text('default_source')}: {python_mirrors[0]}"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5), padx=5)
        
        # 添加测试按钮
        ttk.Button(
            python_mirror_frame, 
            text=get_text("test_python_mirror"), 
            command=lambda: self.test_mirror("python")
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # 添加自定义镜像按钮
        ttk.Button(
            python_mirror_frame, 
            text=get_text("add_custom_mirror"), 
            command=lambda: self.add_custom_mirror("python")
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # pip镜像设置
        pip_mirror_frame = ttk.LabelFrame(mirrors_frame, text=get_text("pip_mirror"), padding=10)
        pip_mirror_frame.pack(fill="x", pady=(0, 15))
        
        # 获取镜像列表
        pip_mirrors = settings.get_pip_mirrors()
        active_pip_mirror = settings.get_active_mirror("pip")
        
        # 创建下拉菜单选项
        pip_mirror_options = [get_text("default_source")] + pip_mirrors[1:]  # 第一个作为默认源
        
        # 当前镜像
        self.pip_mirror_var = tk.StringVar()
        if active_pip_mirror == pip_mirrors[0]:
            self.pip_mirror_var.set(get_text("default_source"))
        else:
            self.pip_mirror_var.set(active_pip_mirror)
        
        # 创建下拉菜单和标签
        ttk.Label(pip_mirror_frame, text=get_text("pip_mirror")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.pip_mirror_combo = ttk.Combobox(pip_mirror_frame, textvariable=self.pip_mirror_var, width=40, state="readonly")
        self.pip_mirror_combo["values"] = pip_mirror_options
        self.pip_mirror_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # 添加默认源说明
        ttk.Label(
            pip_mirror_frame, 
            text=f"{get_text('default_source')}: {pip_mirrors[0]}"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5), padx=5)
        
        # 添加测试按钮
        ttk.Button(
            pip_mirror_frame, 
            text=get_text("test_pip_mirror"), 
            command=lambda: self.test_mirror("pip")
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # 添加自定义镜像按钮
        ttk.Button(
            pip_mirror_frame, 
            text=get_text("add_custom_mirror"), 
            command=lambda: self.add_custom_mirror("pip")
        ).grid(row=1, column=2, padx=5, pady=5)
    
    def create_python_tab(self):
        """创建Python管理选项卡"""
        python_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(python_frame, text=get_text("python_management"))
        
        # 顶部控制区域
        control_frame = ttk.Frame(python_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        # Python环境列表框架
        list_frame = ttk.LabelFrame(python_frame, text=get_text("available_python_versions"), padding=10)
        list_frame.pack(fill="both", expand=True)
        
        # 创建表格视图
        columns = ("version", "path", "pip_version")
        self.python_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # 设置列标题
        self.python_tree.heading("version", text=get_text("version"))
        self.python_tree.heading("path", text=get_text("python_path"))
        self.python_tree.heading("pip_version", text=get_text("pip_version"))
        
        # 设置列宽
        self.python_tree.column("version", width=100)
        self.python_tree.column("path", width=300)
        self.python_tree.column("pip_version", width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.python_tree.yview)
        self.python_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.python_tree.pack(fill="both", expand=True)
        
        # 扫描按钮
        scan_button = ttk.Button(
            control_frame, 
            text=get_text("scan_python_versions"), 
            command=self.scan_python_versions
        )
        scan_button.pack(side="right", padx=5)
        
        # 绑定选择事件
        self.python_tree.bind("<<TreeviewSelect>>", self.on_python_version_select)
        
        # 添加pip版本管理UI - 需要在创建python_tree之后
        pip_management_frame = ttk.LabelFrame(python_frame, text=get_text("pip_version_management"), padding=10)
        pip_management_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # 创建pip版本管理组件
        self.pip_management_ui = PipManagementUI(pip_management_frame, self.python_tree)
        
        # 初始化数据
        self.scan_python_versions()
    
    def on_python_version_select(self, event):
        """当选择Python版本时更新pip版本管理"""
        selected = self.python_tree.selection()
        if selected:
            item = selected[0]
            version = self.python_tree.item(item, "values")[0]
            self.pip_management_ui.load_versions(version)
    
    def create_log_tab(self):
        """创建日志设置选项卡"""
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text=get_text("log_settings"))
        
        # 日志大小设置
        size_frame = ttk.LabelFrame(log_frame, text=get_text("log_settings"), padding=10)
        size_frame.pack(fill="x", pady=(0, 15))
        
        # 当前日志大小设置
        current_log_size = settings.get_setting("max_log_size", 10)
        current_size_unit = settings.get_setting("log_size_unit", "MB")
        
        # 创建日志大小输入和单位选择
        ttk.Label(size_frame, text=get_text("max_log_size")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        
        # 大小输入框
        self.log_size_var = tk.StringVar(value=str(current_log_size))
        log_size_entry = ttk.Entry(size_frame, textvariable=self.log_size_var, width=10)
        log_size_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # 单位选择
        ttk.Label(size_frame, text=get_text("log_size_unit")).grid(row=0, column=2, sticky="w", pady=5, padx=5)
        
        self.log_size_unit_var = tk.StringVar(value=current_size_unit)
        size_unit_combo = ttk.Combobox(size_frame, textvariable=self.log_size_unit_var, width=5, state="readonly")
        size_unit_combo["values"] = ["KB", "MB", "GB"]
        size_unit_combo.grid(row=0, column=3, sticky="w", pady=5, padx=5)
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存各项设置到settings模块
            settings.set_setting("language", self.language_var.get())
            settings.set_setting("theme", self.theme_var.get())
            settings.set_setting("allow_multithreading", self.multithread_var.get())
            settings.set_setting("check_pip_update", self.check_pip_var.get())
            
            # 保存镜像设置
            python_mirror_text = self.python_mirror_var.get()
            if python_mirror_text == get_text("default_source"):
                settings.set_active_mirror("python", "default")
            else:
                settings.set_active_mirror("python", python_mirror_text)
            
            pip_mirror_text = self.pip_mirror_var.get()
            if pip_mirror_text == get_text("default_source"):
                settings.set_active_mirror("pip", "default")
            else:
                settings.set_active_mirror("pip", pip_mirror_text)
            
            # 保存日志大小设置
            try:
                log_size = int(self.log_size_var.get())
                if log_size <= 0:
                    log_size = 10  # 使用默认值
                settings.set_setting("max_log_size", log_size)
            except:
                settings.set_setting("max_log_size", 10)  # 使用默认值
            
            # 保存日志大小单位
            settings.set_setting("log_size_unit", self.log_size_unit_var.get())
            
            # 保存设置到文件
            if settings.save_settings(self.config_path):
                # 设置已变更标志
                self.settings_changed = True
                
                # 检查是否有语言变更
                if settings.check_language_changed():
                    if messagebox.askyesno(
                        get_text("settings_saved"), 
                        get_text("language_changed") + "\n\n" + get_text("restart_now")
                    ):
                        self.window.destroy()
                        # 调用重启回调
                        if self.restart_callback:
                            self.restart_callback()
                        return
                    # 用户选择不立即重启,清除变更记录
                    settings.clear_settings_changes()
                else:
                    # 没有语言变更,显示普通保存成功消息
                    messagebox.showinfo(get_text("success"), get_text("settings_saved"))
                
                # 关闭窗口
                self.window.destroy()
            else:
                # 显示保存失败消息
                messagebox.showerror(get_text("error"), get_text("settings_save_fail"))
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            messagebox.showerror(get_text("error"), get_text("save_failed").format(str(e)))
    
    def on_window_close(self):
        """窗口关闭事件处理"""
        # 如果设置已变更，询问是否保存
        if self.settings_changed:
            if messagebox.askyesno(get_text("warning"), get_text("restart_recommended")):
                if self.restart_callback:
                    self.restart_callback()
        
        # 关闭窗口
        self.window.destroy()

    def test_mirror(self, mirror_type):
        """测试指定类型的镜像"""
        from mirror_test import show_mirror_test_window
        try:
            show_mirror_test_window(self.window, mirror_type, self.config_path)
        except Exception as e:
            logger.error(f"测试{mirror_type}镜像失败: {e}")
            messagebox.showerror(get_text("error"), get_text("mirror_test_failed"))

    def add_custom_mirror(self, mirror_type):
        """添加自定义镜像"""
        # 创建对话框
        dialog = tk.Toplevel(self.window)
        dialog.title(get_text("add_custom_mirror"))
        dialog.transient(self.window)
        dialog.grab_set()
        
        # 创建输入框
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text=get_text("mirror_url")).pack(pady=5)
        url_var = tk.StringVar()
        url_entry = ttk.Entry(frame, textvariable=url_var, width=50)
        url_entry.pack(pady=5)
        url_entry.focus_set()
        
        # 验证并保存
        def save_mirror():
            url = url_var.get().strip()
            if not url:
                messagebox.showwarning(get_text("warning"), get_text("enter_mirror_url"))
                return
                
            try:
                if mirror_type == "python":
                    if not url.startswith(("http://", "https://")):
                        url = "https://" + url
                    settings.save_custom_python_mirror(url)
                    # 刷新Python镜像下拉列表
                    python_mirrors = settings.get_python_mirrors()
                    self.python_mirror_combo["values"] = [get_text("default_source")] + python_mirrors[1:]
                else:
                    if not url.endswith("/"):
                        url += "/"
                    settings.save_custom_pip_mirror(url)
                    # 刷新pip镜像下拉列表
                    pip_mirrors = settings.get_pip_mirrors()
                    self.pip_mirror_combo["values"] = [get_text("default_source")] + pip_mirrors[1:]
                
                dialog.destroy()
                messagebox.showinfo(get_text("success"), get_text("mirror_added"))
            except Exception as e:
                logger.error(f"保存自定义镜像失败: {e}")
                messagebox.showerror(get_text("error"), get_text("mirror_add_failed"))
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text=get_text("save"), command=save_mirror).pack(side="left", padx=5)
        ttk.Button(button_frame, text=get_text("cancel"), command=dialog.destroy).pack(side="left", padx=5)
        
        # 居中显示
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'+{x}+{y}')

    def scan_python_versions(self):
        """扫描系统中安装的Python版本"""
        # 清空现有项目并显示加载状态
        for item in self.python_tree.get_children():
            self.python_tree.delete(item)
        
        # 添加临时加载提示项
        self.python_tree.insert("", "end", values=(get_text("scanning"), "", ""))

        def scan_thread():
            try:
                # 使用 settings 模块的函数获取 Python 环境信息
                environments = settings.scan_python_environments()
                
                # 清除加载提示
                def clear_loading():
                    for item in self.python_tree.get_children():
                        self.python_tree.delete(item)
                
                if self.python_tree.winfo_exists():
                    self.python_tree.after(0, clear_loading)
                
                # 显示环境信息
                for env in environments:
                    def add_version(env=env):
                        self.python_tree.insert(
                            "",
                            "end",
                            values=(
                                env["version"],
                                env["install_path"],  # 使用安装路径而不是可执行文件路径
                                "pip " + (env["pip_version"] if env["pip_version"] else "not available")
                            ),
                            tags=("green" if env["pip_installed"] else "red")
                        )
                        # 配置标签样式
                        self.python_tree.tag_configure("green", foreground="green")
                        self.python_tree.tag_configure("red", foreground="red")
                    
                    if self.python_tree.winfo_exists():
                        self.python_tree.after(0, add_version)

            except Exception as e:
                logger.error(f"扫描Python版本失败: {e}")
                def show_error():
                    messagebox.showerror(
                        get_text("error"),
                        get_text("python_scan_failed") + f"\n{str(e)}"
                    )
                if self.python_tree.winfo_exists():
                    self.python_tree.after(0, show_error)

        # 启动扫描线程
        threading.Thread(target=scan_thread, daemon=True).start()

def show_settings_window(parent, config_path, restart_callback=None):
    """
    显示设置窗口
    
    参数:
        parent: 父窗口
        config_path: 配置文件路径
        restart_callback: 重启应用的回调函数
    """
    # 创建设置窗口
    settings_window = SettingsWindow(parent, config_path, restart_callback)
    return settings_window
