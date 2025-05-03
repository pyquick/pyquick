#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pip包管理模块
负责管理pip包的安装、卸载、更新等操作
"""

import os
import sys
import json
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
import logging
import threading
import subprocess
import platform
from typing import Dict, Any, List, Optional, Tuple
import re
import requests
import time

logger = logging.getLogger(__name__)

class PipManager:
    """
    pip包管理类
    负责pip包的安装、卸载和更新等操作
    """
    
    def __init__(self, parent, container, config_path):
        """
        初始化pip包管理器
        
        Args:
            parent: 父级窗口
            container: 容器实例
            config_path: 配置路径
        """
        self.parent = parent
        self.container = container
        self.config_path = config_path
        
        # 记录ttkbootstrap信息
        try:
            if hasattr(ttk, 'Style'):
                style = ttk.Style()
                current_theme = style.theme_use() if hasattr(style, 'theme_use') else "未知"
                logger.info(f"PIP管理器初始化，当前ttkbootstrap主题: {current_theme}")
            else:
                logger.warning("未检测到ttkbootstrap主题支持")
        except Exception as theme_error:
            logger.error(f"获取ttkbootstrap主题信息失败: {theme_error}")
        
        # 获取Python管理器实例
        try:
            from settings.python_manager import PythonManager
            settings_manager = None
            try:
                from settings.settings_manager import get_manager
                settings_manager = get_manager()
                
                # 确保settings_manager不是None
                if settings_manager is None:
                    logger.warning("设置管理器为None，创建模拟管理器")
                    settings_manager = type('MockSettingsManager', (), {
                        'get': lambda s, k, d=None: d,
                        'set': lambda s, k, v: True,
                        'settings': {'python_versions': {'installations': []}}
                    })()
            except ImportError as ie:
                logger.error(f"导入设置管理器失败: {ie}")
                # 如果无法导入设置管理器，使用模拟的
                settings_manager = type('MockSettingsManager', (), {
                    'get': lambda s, k, d=None: d,
                    'set': lambda s, k, v: True,
                    'settings': {'python_versions': {'installations': []}}
                })()
            
            # 创建Python管理器实例
            try:
                self.python_manager = PythonManager(parent, settings_manager)
                
                # 确保python_manager不是字符串或其他基本类型
                if not isinstance(self.python_manager, PythonManager):
                    logger.error(f"Python管理器创建失败，类型: {type(self.python_manager)}")
                    raise TypeError(f"Python管理器类型错误: {type(self.python_manager)}")
                
                # 确保python_installations属性可用
                if not hasattr(self.python_manager, 'python_installations'):
                    logger.warning("Python管理器中没有python_installations属性，初始化为空列表")
                    self.python_manager.python_installations = []
            except Exception as pm_error:
                logger.error(f"创建Python管理器失败: {pm_error}")
                # 创建一个简单的模拟对象
                self.python_manager = type('MockPythonManager', (), {
                    'python_installations': [],
                    'get_default_python': lambda: None
                })()
        except Exception as module_error:
            logger.error(f"加载Python管理器模块失败: {module_error}")
            # 创建一个简单的模拟对象
            self.python_manager = type('MockPythonManager', (), {
                'python_installations': [],
                'get_default_python': lambda: None
            })()
        
        # 创建变量
        self.search_var = tk.StringVar()
        self.selected_python_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.sort_by_var = tk.StringVar(value="名称")
        self.show_outdated_var = tk.BooleanVar()
        
        # 包信息缓存
        self.package_cache = {}
        self.outdated_packages = set()
        
        # 创建界面组件
        self._create_widgets()
        
        # 初始化PyPI镜像
        self._init_pypi_mirrors()
        
        # 更新Python环境信息
        self._update_python_environment_info()
        
        # 刷新包列表
        self.refresh_installed_packages()
        
        # 设置定期刷新Python环境列表的定时器（每30秒检查一次）
        def periodic_refresh():
            self._update_python_environments()
            self.parent.after(30000, periodic_refresh)
        
        # 启动定时器
        self.parent.after(30000, periodic_refresh)
        
    def _create_widgets(self):
        """创建界面组件"""
        # 工具栏
        toolbar = ttk.Frame(self.parent)
        toolbar.grid(row=0, column=0, sticky="ew", padx=15, pady=15)  # 增加内边距
        toolbar.grid_columnconfigure(5, weight=1)  # 让搜索框可以自动扩展
        
        # 创建版本信息框架
        version_frame = ttk.LabelFrame(self.parent, text="PIP版本信息", bootstyle="primary")
        version_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=15)  # 增加内边距
        version_frame.grid_columnconfigure(0, weight=1)
        
        # 版本信息显示
        self.current_pip_var = tk.StringVar(value="当前版本: 获取中...")
        self.latest_pip_var = tk.StringVar(value="最新版本: 获取中...")
        
        pip_info_frame = ttk.Frame(version_frame)
        pip_info_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=15)  # 增加内边距
        pip_info_frame.grid_columnconfigure(1, weight=1)
        
        self.current_pip_label = ttk.Label(pip_info_frame, textvariable=self.current_pip_var)
        self.current_pip_label.grid(row=0, column=0, sticky="w", padx=15, pady=10)  # 增加内边距
        
        self.latest_pip_label = ttk.Label(pip_info_frame, textvariable=self.latest_pip_var)
        self.latest_pip_label.grid(row=0, column=1, sticky="w", padx=15, pady=10)  # 增加内边距
        
        # 刷新和升级按钮框架
        button_frame = ttk.Frame(version_frame)
        button_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=15)  # 增加内边距
        
        # 自动升级选项
        self.auto_upgrade_var = tk.BooleanVar(value=False)
        auto_upgrade_check = ttk.Checkbutton(button_frame, text="自动更新PIP", 
                                           variable=self.auto_upgrade_var,
                                           command=self._save_auto_upgrade_setting,
                                           bootstyle="success-round-toggle")
        auto_upgrade_check.grid(row=0, column=0, sticky="w", padx=15, pady=10)  # 增加内边距
        
        # 加载自动升级设置
        self._load_auto_upgrade_setting()
        
        # 刷新按钮
        refresh_pip_btn = ttk.Button(button_frame, text="刷新版本", command=self._refresh_pip_version, bootstyle="info")
        refresh_pip_btn.grid(row=0, column=1, padx=15, pady=10)  # 增加内边距
        
        # 升级按钮
        upgrade_pip_btn = ttk.Button(button_frame, text="升级pip", command=self._upgrade_pip, bootstyle="success")
        upgrade_pip_btn.grid(row=0, column=2, padx=15, pady=10)  # 增加内边距
        
        # Python环境信息框架
        python_frame = ttk.LabelFrame(self.parent, text="Python环境", bootstyle="primary")
        python_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=15)  # 增加内边距
        python_frame.grid_columnconfigure(1, weight=1)
        
        # 默认Python环境显示 - 改用Label而不是Combobox
        ttk.Label(python_frame, text="当前Python环境:").grid(row=0, column=0, sticky="w", padx=15, pady=10)
        
        # 创建默认Python环境显示标签
        self.python_env_label = ttk.Label(python_frame, text="获取中...", font=("", 10))
        self.python_env_label.grid(row=0, column=1, padx=15, pady=15, sticky="w")
        
        # 路径显示标签
        ttk.Label(python_frame, text="安装路径:").grid(row=1, column=0, sticky="w", padx=15, pady=10)
        self.python_path_label = ttk.Label(python_frame, text="获取中...", font=("", 10))
        self.python_path_label.grid(row=1, column=1, padx=15, pady=15, sticky="w")
        
        # 刷新Python环境按钮
        refresh_python_btn = ttk.Button(python_frame, text="刷新", command=self._update_python_environment_info, bootstyle="info")
        refresh_python_btn.grid(row=2, column=0, columnspan=2, padx=15, pady=15)
        
        # 搜索和过滤区域
        filter_frame = ttk.Frame(self.parent)
        filter_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=15)  # 增加内边距
        filter_frame.grid_columnconfigure(1, weight=1)
        
        # 搜索框
        ttk.Label(filter_frame, text="搜索:").grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self._filter_packages())
        search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=25, bootstyle="info")
        search_entry.grid(row=0, column=1, padx=15, pady=10, sticky="ew")
        
        # 排序选项
        ttk.Label(filter_frame, text="排序:").grid(row=0, column=2, padx=15, pady=10, sticky="w")
        
        self.sort_by_var = tk.StringVar(value="名称")
        sort_combo = ttk.Combobox(filter_frame, textvariable=self.sort_by_var,
                               values=["名称", "版本", "描述"], state="readonly", width=10, bootstyle="info")
        sort_combo.grid(row=0, column=3, padx=15, pady=10, sticky="w")
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self._filter_packages())
        
        # 刷新按钮
        refresh_btn = ttk.Button(filter_frame, text="刷新包列表", command=self._refresh_all, bootstyle="info")
        refresh_btn.grid(row=0, column=4, padx=15, pady=10, sticky="e")
        
        # 创建树状视图
        tree_frame = ttk.Frame(self.parent)
        tree_frame.grid(row=4, column=0, sticky="nsew", padx=15, pady=15)  # 增加内边距
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(tree_frame, bootstyle="primary-round")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # 创建树状视图
        self.tree = ttk.Treeview(tree_frame, columns=("名称", "当前版本", "最新版本", "描述"), 
                              show="headings", height=15, yscrollcommand=scrollbar.set, bootstyle="primary")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.tree.yview)
        
        # 配置列
        self.tree.heading("名称", text="名称")
        self.tree.heading("当前版本", text="当前版本")
        self.tree.heading("最新版本", text="最新版本")
        self.tree.heading("描述", text="描述")
        
        self.tree.column("名称", width=150)
        self.tree.column("当前版本", width=100)
        self.tree.column("最新版本", width=100)
        self.tree.column("描述", width=400)  # 增加描述列宽度
        
        # 配置标签
        self.tree.tag_configure("outdated", foreground="red")
        
        # 绑定右键菜单
        self.tree.bind("<Button-3>", self._show_context_menu)
        
        # 状态栏
        status_frame = ttk.Frame(self.parent)
        status_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=10)
        
        self.status_var = tk.StringVar(value="正在加载包信息...")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=0, sticky="w")
        
        # 按钮栏
        button_frame = ttk.Frame(self.parent)
        button_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=15)
        
        ttk.Button(button_frame, text="安装新包", 
                command=self._install_package, bootstyle="success").grid(row=0, column=0, padx=15)
        ttk.Button(button_frame, text="更新所有", 
                command=self._update_all_packages, bootstyle="warning").grid(row=0, column=1, padx=15)
        
        # 创建右键菜单 - 使用ttkbootstrap的方式
        # ttkbootstrap会自动设置菜单样式，只需使用标准的tk.Menu即可
        # 但我们需要使用通过ttk.Style获取的主题颜色
        try:
            style = ttk.Style()
            if hasattr(style, 'colors'):
                # ttkbootstrap 1.0+版本
                bg_color = style.colors.bg
                fg_color = style.colors.fg
                select_bg = style.colors.selectbg
                select_fg = style.colors.selectfg
            else:
                # 使用默认颜色
                bg_color = "#2b2b2b"
                fg_color = "#ffffff"
                select_bg = "#007bff"
                select_fg = "#ffffff"
                
            # 创建符合当前主题的菜单
            self.context_menu = tk.Menu(self.parent, tearoff=0,
                                      background=bg_color,
                                      foreground=fg_color,
                                      activebackground=select_bg,
                                      activeforeground=select_fg,
                                      relief="flat",
                                      borderwidth=1)
        except Exception as e:
            logger.error(f"创建主题化菜单失败: {e}")
            # 使用普通菜单作为后备方案
            self.context_menu = tk.Menu(self.parent, tearoff=0)
        
        self.context_menu.add_command(label="更新", command=self._update_package)
        self.context_menu.add_command(label="卸载", command=self._uninstall_package)
        self.context_menu.add_command(label="查看信息", command=self._show_package_info)
        
        # 初始化变量
        self.outdated_packages = {}
                
        # 加载包信息
        self._load_package_info()
        
        # 刷新pip版本
        self._refresh_pip_version()
        
    def _update_python_environment_info(self):
        """从settings.json读取并更新Python环境信息"""
        try:
            # 默认Python信息
            default_python = {
                "version": sys.version.split()[0],
                "path": sys.executable,
                "name": "系统默认Python"
            }
            
            # 尝试从设置中获取标记为default=true的Python环境
            try:
                from settings.settings_manager import get_manager
                settings_manager = get_manager()
                if settings_manager:
                    # 获取安装列表
                    installations = settings_manager.get("python.installations", [])
                    
                    # 查找default=true的环境
                    for install in installations:
                        if install.get("is_default", False) or install.get("default", False):
                            default_python = {
                                "version": install.get("version", "未知"),
                                "path": install.get("path", sys.executable),
                                "name": f"Python {install.get('version', '未知')}"
                            }
                            break
            except Exception as settings_error:
                logger.error(f"从settings.json获取Python环境失败: {settings_error}")
            
            # 更新UI
            self.python_env_label.config(text=f"Python {default_python.get('version', '未知')} ({default_python.get('name', '系统默认')})")
            self.python_path_label.config(text=default_python.get('path', '未知'))
            
            # 获取当前pip版本
            try:
                # 使用环境路径获取pip版本
                python_path = default_python.get('path', sys.executable)
                pip_version = self._get_current_pip_version(python_path)
                if pip_version:
                    self.current_pip_var.set(f"当前版本: {pip_version}")
                else:
                    self.current_pip_var.set("当前版本: 未知")
            except Exception as pip_error:
                logger.error(f"获取pip版本失败: {pip_error}")
                self.current_pip_var.set("当前版本: 获取失败")
            
            return default_python
        except Exception as e:
            logger.error(f"更新Python环境信息失败: {str(e)}")
            self.python_env_label.config(text="获取失败")
            self.python_path_label.config(text="未知")
            return None
        
    def _refresh_all(self):
        """刷新所有信息"""
        try:
            # 刷新环境信息
            self._update_python_environment_info()
            
            # 刷新包列表
            self.refresh_installed_packages()
            
            # 刷新PIP版本信息
            self._refresh_pip_version()
            
            # 提示刷新完成
            self.status_var.set("刷新完成")
        except Exception as e:
            logger.error(f"刷新数据失败: {str(e)}")
            self.status_var.set(f"刷新失败: {str(e)}")
        
    def _load_package_info(self):
        """加载已安装的包信息"""
        self.status_var.set("正在加载包信息...")
        self.tree.delete(*self.tree.get_children())
        
        def do_load():
            try:
                # 获取当前选择的Python环境
                current_python = self._get_current_python()
                if not current_python:
                    raise Exception("未找到Python环境")
                    
                # 获取已安装的包
                result = subprocess.run(
                    [current_python, "-m", "pip", "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                packages = json.loads(result.stdout)
                self.package_cache = {pkg["name"]: pkg for pkg in packages}
                
                # 获取可更新的包
                result = subprocess.run(
                    [current_python, "-m", "pip", "list", "--outdated", "--format=json"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                outdated = json.loads(result.stdout)
                self.outdated_packages = {pkg["name"] for pkg in outdated}
                
                # 更新界面
                def update_ui():
                    self._filter_packages()
                    self.status_var.set(f"已加载 {len(self.package_cache)} 个包")
                    
                self.parent.after(0, update_ui)
                
            except Exception as e:
                logger.error(f"加载包信息失败: {str(e)}")
                
                def show_error():
                    self.status_var.set("加载失败")
                    messagebox.showerror("错误", f"加载包信息失败: {str(e)}")
                    
                self.parent.after(0, show_error)
                
        threading.Thread(target=do_load, daemon=True).start()
        
    def _filter_packages(self):
        """根据搜索条件筛选包"""
        self.tree.delete(*self.tree.get_children())
        
        search_text = self.search_var.get().lower()
        show_outdated = self.show_outdated_var.get()
        
        # 过滤和排序包
        packages = []
        for name, info in self.package_cache.items():
            if show_outdated and name not in self.outdated_packages:
                continue
                
            if search_text and search_text not in name.lower():
                continue
                
            packages.append(info)
            
        # 排序
        sort_by = self.sort_by_var.get()
        if sort_by == "名称":
            packages.sort(key=lambda x: x["name"].lower())
        elif sort_by == "版本":
            packages.sort(key=lambda x: x["version"])
        elif sort_by == "描述":
            packages.sort(key=lambda x: x.get("description", "").lower())
            
        # 显示结果
        for pkg in packages:
            name = pkg["name"]
            version = pkg["version"]
            latest = "可更新" if name in self.outdated_packages else version
            description = pkg.get("description", "")
            
            values = (name, version, latest, description)
            item = self.tree.insert("", tk.END, values=values)
            
            if name in self.outdated_packages:
                self.tree.item(item, tags=("outdated",))
                
        if not packages:
            self.status_var.set("没有找到匹配的包")
        else:
            self.status_var.set(f"显示 {len(packages)} 个包")
            
    def _get_current_python(self):
        """获取当前Python环境路径"""
        try:
            # 从设置中获取标记为default=true的Python环境
            try:
                from settings.settings_manager import get_manager
                settings_manager = get_manager()
                if settings_manager:
                    # 获取安装列表
                    installations = settings_manager.get("python.installations", [])
                    
                    # 查找default=true的环境
                    for install in installations:
                        if install.get("is_default", False) or install.get("default", False):
                            return install.get("path", sys.executable)
            except Exception as settings_error:
                logger.error(f"从settings.json获取Python路径失败: {settings_error}")
            
            # 尝试从Python管理器获取默认环境
            if hasattr(self, 'python_manager') and self.python_manager:
                default_python = self.python_manager.get_default_python()
                if default_python and 'path' in default_python:
                    return default_python['path']
            
            # 兜底：返回系统Python路径
            return sys.executable
        except Exception as e:
            logger.error(f"获取当前Python路径失败: {e}")
        return sys.executable
        
    def _show_context_menu(self, event):
        """显示右键菜单"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            # 计算菜单位置（相对于树视图的坐标）
            x = self.tree.winfo_rootx() + event.x
            y = self.tree.winfo_rooty() + event.y
            self.context_menu.post(x, y)
            
    def _update_package(self):
        """更新选中的包"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要更新的包")
            return
            
        item = selected[0]
        package_name = self.tree.item(item)["values"][0]
        
        if package_name not in self.outdated_packages:
            messagebox.showinfo("提示", "此包已是最新版本")
            return
            
        if not messagebox.askyesno("确认", f"确定要更新 {package_name} 吗？"):
            return
            
        self._run_pip_command("update", package_name)
        
    def _uninstall_package(self):
        """卸载选中的包"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要卸载的包")
            return
            
        item = selected[0]
        package_name = self.tree.item(item)["values"][0]
        
        if not messagebox.askyesno("确认", f"确定要卸载 {package_name} 吗？"):
            return
            
        self._run_pip_command("uninstall", package_name)
        
    def _install_package(self):
        """安装新包"""
        # 创建安装对话框
        dialog = tk.Toplevel(self.parent)
        dialog.title("安装新包")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # 应用ttkbootstrap样式到对话框
        try:
            style = ttk.Style()
            if hasattr(style, 'colors'):
                dialog.configure(background=style.colors.bg)
        except Exception as e:
            logger.error(f"应用对话框样式失败: {e}")
        
        # 设置窗口大小和位置
        window_width = 400
        window_height = 150
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        dialog.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 包名输入
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(name_frame, text="包名:").pack(side=tk.LEFT)
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=name_var, bootstyle="info")
        name_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # 版本输入（可选）
        version_frame = ttk.Frame(dialog)
        version_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(version_frame, text="版本:").pack(side=tk.LEFT)
        
        version_var = tk.StringVar()
        version_entry = ttk.Entry(version_frame, textvariable=version_var, bootstyle="info")
        version_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        ttk.Label(version_frame, text="(可选)").pack(side=tk.LEFT)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=15, pady=15)
        
        def do_install():
            package = name_var.get().strip()
            if not package:
                messagebox.showwarning("警告", "请输入包名")
                return
                
            version = version_var.get().strip()
            if version:
                package = f"{package}=={version}"
                
            dialog.destroy()
            self._run_pip_command("install", package)
            
        ttk.Button(button_frame, text="安装", command=do_install, bootstyle="success").pack(side=tk.RIGHT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, bootstyle="danger").pack(side=tk.RIGHT)
        
        # 焦点设置
        name_entry.focus()
        
    def _update_all_packages(self):
        """更新所有可更新的包"""
        if not self.outdated_packages:
            messagebox.showinfo("提示", "没有可更新的包")
            return
            
        if not messagebox.askyesno("确认",
                                  f"确定要更新所有 {len(self.outdated_packages)} 个可更新的包吗？"):
            return
            
        packages = list(self.outdated_packages)
        self._run_pip_command("update", *packages)
        
    def _show_package_info(self):
        """显示包详细信息"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个包")
            return
            
        item = selected[0]
        package_name = self.tree.item(item)["values"][0]
        
        # 创建信息窗口
        info_window = tk.Toplevel(self.parent)
        info_window.title(f"包信息 - {package_name}")
        info_window.transient(self.parent)
        
        # 应用ttkbootstrap样式到对话框
        try:
            style = ttk.Style()
            if hasattr(style, 'colors'):
                info_window.configure(background=style.colors.bg)
        except Exception as e:
            logger.error(f"应用对话框样式失败: {e}")
        
        # 设置窗口大小和位置
        window_width = 500
        window_height = 400
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        info_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建主框架
        main_frame = ttk.Frame(info_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 信息文本框
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文本框和滚动条
        text = tk.Text(text_frame, wrap=tk.WORD, width=60, height=20)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条 - 使用ttkbootstrap的滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview, bootstyle="primary-round")
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        close_button = ttk.Button(button_frame, text="关闭", 
                              command=info_window.destroy, 
                              bootstyle="info")
        close_button.pack(side=tk.RIGHT)
        
        # 加载包信息
        def load_info():
            try:
                # 获取包信息
                result = subprocess.run(
                    [self._get_current_python(), "-m", "pip", "show", package_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                info = result.stdout
                
                def update_ui():
                    text.delete("1.0", tk.END)
                    text.insert(tk.END, info)
                    # 配置文本颜色以匹配主题
                    try:
                        style = ttk.Style()
                        if hasattr(style, 'colors'):
                            text.config(bg=style.colors.inputbg if hasattr(style.colors, 'inputbg') else style.colors.bg,
                                      fg=style.colors.inputfg if hasattr(style.colors, 'inputfg') else style.colors.fg)
                    except Exception as style_error:
                        logger.error(f"应用文本样式失败: {style_error}")
                    text.configure(state="disabled")
                    
                info_window.after(0, update_ui)
                
            except Exception as e:
                logger.error(f"获取包信息失败: {str(e)}")
                
                def show_error():
                    text.delete("1.0", tk.END)
                    text.insert(tk.END, f"获取包信息失败: {str(e)}")
                    text.configure(state="disabled")
                    
                info_window.after(0, show_error)
                
        threading.Thread(target=load_info, daemon=True).start()
        
    def _run_pip_command(self, command: str, *packages: str):
        """
        执行pip命令
        
        Args:
            command: 命令类型（install/uninstall/update）
            packages: 包名列表
        """
        if not packages:
            return
            
        # 创建进度窗口
        progress = tk.Toplevel(self.parent)
        progress.title("pip操作")
        progress.transient(self.parent)
        progress.grab_set()
        
        # 应用ttkbootstrap样式到对话框
        try:
            style = ttk.Style()
            if hasattr(style, 'colors'):
                progress.configure(background=style.colors.bg)
        except Exception as e:
            logger.error(f"应用对话框样式失败: {e}")
        
        # 设置窗口大小和位置
        window_width = 500
        window_height = 300
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        progress.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 主内容框架
        main_frame = ttk.Frame(progress)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 进度标签
        status_var = tk.StringVar()
        status_label = ttk.Label(main_frame, textvariable=status_var, font=("", 12))
        status_label.pack(pady=15)
        
        # 输出文本框
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        output_text = tk.Text(text_frame, height=12, width=60)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 自定义文本颜色以匹配主题
        try:
            if hasattr(style, 'colors'):
                output_text.config(
                    bg=style.colors.inputbg if hasattr(style.colors, 'inputbg') else style.colors.bg,
                    fg=style.colors.inputfg if hasattr(style.colors, 'inputfg') else style.colors.fg
                )
        except Exception as text_error:
            logger.error(f"自定义文本样式失败: {text_error}")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                command=output_text.yview, bootstyle="primary-round")
        output_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架 - 预先创建但初始隐藏
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        close_button = ttk.Button(button_frame, text="关闭",
                              command=progress.destroy, bootstyle="info")
        close_button.pack(side=tk.RIGHT)
        close_button.pack_forget()  # 初始隐藏
        
        def append_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            
        def do_command():
            try:
                python_path = self._get_current_python()
                
                # 准备命令
                if command == "install":
                    cmd = [python_path, "-m", "pip", "install"] + list(packages)
                    status_var.set("正在安装...")
                elif command == "uninstall":
                    cmd = [python_path, "-m", "pip", "uninstall", "-y"] + list(packages)
                    status_var.set("正在卸载...")
                elif command == "update":
                    cmd = [python_path, "-m", "pip", "install", "--upgrade"] + list(packages)
                    status_var.set("正在更新...")
                else:
                    raise ValueError(f"无效的命令: {command}")
                    
                # 执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 读取输出
                for line in process.stdout:
                    def update_output(text=line):
                        append_output(text.strip())
                    progress.after(0, update_output)
                    
                process.wait()
                
                def finish():
                    if process.returncode == 0:
                        status_var.set("操作完成")
                        self._load_package_info()  # 刷新包列表
                    else:
                        status_var.set("操作失败")
                        
                    # 显示关闭按钮
                    close_button.pack(side=tk.RIGHT, padx=10)
                    
                progress.after(0, finish)
                
            except Exception as e:
                logger.error(f"执行pip命令失败: {str(e)}")
                
                def show_error():
                    status_var.set("操作失败")
                    append_output(f"错误: {str(e)}")
                    close_button.pack(side=tk.RIGHT, padx=10)
                    
                progress.after(0, show_error)
                
        threading.Thread(target=do_command, daemon=True).start()
        
    def _upgrade_pip(self):
        """升级pip"""
        # 创建进度窗口
        progress = tk.Toplevel(self.parent)
        progress.title("升级pip")
        progress.transient(self.parent)
        progress.grab_set()
        
        # 应用ttkbootstrap样式到对话框
        try:
            style = ttk.Style()
            if hasattr(style, 'colors'):
                progress.configure(background=style.colors.bg)
        except Exception as e:
            logger.error(f"应用对话框样式失败: {e}")
        
        # 设置窗口大小和位置
        window_width = 500
        window_height = 300
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        progress.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 主内容框架
        main_frame = ttk.Frame(progress)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 进度标签
        status_var = tk.StringVar()
        status_label = ttk.Label(main_frame, textvariable=status_var, font=("", 12))
        status_label.pack(pady=15)
        
        # 输出文本框
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        output_text = tk.Text(text_frame, height=12, width=60)
        output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 自定义文本颜色以匹配主题
        try:
            if hasattr(style, 'colors'):
                output_text.config(
                    bg=style.colors.inputbg if hasattr(style.colors, 'inputbg') else style.colors.bg,
                    fg=style.colors.inputfg if hasattr(style.colors, 'inputfg') else style.colors.fg
                )
        except Exception as text_error:
            logger.error(f"自定义文本样式失败: {text_error}")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL,
                                command=output_text.yview, bootstyle="primary-round")
        output_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架 - 预先创建但初始隐藏
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        close_button = ttk.Button(button_frame, text="关闭",
                              command=progress.destroy, bootstyle="info")
        close_button.pack(side=tk.RIGHT)
        close_button.pack_forget()  # 初始隐藏
        
        def append_output(text):
            output_text.insert(tk.END, text + "\n")
            output_text.see(tk.END)
            
        def do_upgrade():
            try:
                python_path = self._get_current_python()
                
                # 准备命令
                cmd = [python_path, "-m", "pip", "install", "--upgrade", "pip"]
                status_var.set("正在升级pip...")
                
                # 执行命令
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # 读取输出
                for line in process.stdout:
                    def update_output(text=line):
                        append_output(text.strip())
                    progress.after(0, update_output)
                    
                process.wait()
                
                def finish():
                    if process.returncode == 0:
                        status_var.set("pip升级完成")
                        self._refresh_pip_version()  # 刷新pip版本显示
                    else:
                        status_var.set("pip升级失败")
                        
                    # 显示关闭按钮
                    close_button.pack(side=tk.RIGHT, padx=10)
                    
                progress.after(0, finish)
                
            except Exception as e:
                logger.error(f"升级pip失败: {str(e)}")
                
                def show_error():
                    status_var.set("升级pip失败")
                    append_output(f"错误: {str(e)}")
                    close_button.pack(side=tk.RIGHT, padx=10)
                    
                progress.after(0, show_error)
                
        threading.Thread(target=do_upgrade, daemon=True).start()

    def _refresh_pip_version(self):
        """刷新pip版本"""
        self.current_pip_var.set("当前版本: 获取中...")
        self.latest_pip_var.set("最新版本: 获取中...")
        
        # 尝试更新当前pip版本标签的样式
        try:
            self.current_pip_label.config(foreground="black")
            self.latest_pip_label.config(foreground="black")
        except Exception as e:
            logger.debug(f"更新PIP版本标签样式失败: {e}")
        
        def do_refresh():
            try:
                python_path = self._get_current_python()
                
                # 获取当前版本
                current_version = self._get_current_pip_version(python_path)
                # 获取最新版本
                latest_version = self._get_latest_pip_version(python_path)
                
                # 更新界面
                def update_ui():
                    try:
                        self.current_pip_var.set(f"当前版本: {current_version}")
                        self.latest_pip_var.set(f"最新版本: {latest_version}")
                        
                        # 如果版本不一致，用红色显示当前版本
                        if current_version and latest_version and current_version != latest_version:
                            self.current_pip_label.config(foreground="red")
                            self.latest_pip_label.config(foreground="green")
                            
                            # 如果设置了自动升级，自动执行升级
                            if self.auto_upgrade_var.get():
                                logger.info("自动升级已启用，开始升级PIP")
                                self._upgrade_pip()
                        else:
                            self.current_pip_label.config(foreground="green")
                            self.latest_pip_label.config(foreground="green")
                    except Exception as ui_error:
                        logger.error(f"更新PIP版本UI失败: {ui_error}")
                
                if self.parent and hasattr(self.parent, 'after'):
                    self.parent.after(0, update_ui)
            except Exception as e:
                logger.error(f"刷新PIP版本失败: {e}")
                
                # 更新界面显示错误
                def show_error():
                    self.current_pip_var.set("当前版本: 获取失败")
                    self.latest_pip_var.set("最新版本: 获取失败")
                
                if self.parent and hasattr(self.parent, 'after'):
                    self.parent.after(0, show_error)
        
        # 在后台线程中执行
        threading.Thread(target=do_refresh, daemon=True).start()
    
    def _get_current_pip_version(self, python_path):
        """获取当前pip版本"""
        try:
            # 使用pip --version命令获取版本
            result = subprocess.run(
                [python_path, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # 解析输出中的版本号
            output = result.stdout
            match = re.search(r'pip (\d+\.\d+(\.\d+)?)', output)
            if match:
                return match.group(1)
            return "未知"
        except Exception as e:
            logger.error(f"获取当前PIP版本失败: {e}")
            return "错误"
    
    def _get_latest_pip_version(self, python_path=None):
        """获取最新pip版本"""
        try:
            # 使用PyPI API直接获取最新版本
            r = requests.get("https://pypi.org/pypi/pip/json", verify=False, timeout=5)
            return r.json()["info"]["version"]
        except Exception as e:
            logger.error(f"获取最新PIP版本失败: {e}")
            return "未知"
            
    def _save_auto_upgrade_setting(self):
        """保存自动升级设置"""
        try:
            settings_file = os.path.join(self.config_path, "pip_settings.json")
            settings = {"auto_upgrade": self.auto_upgrade_var.get()}
            
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f)
                
            logger.debug(f"已保存PIP自动升级设置: {settings}")
        except Exception as e:
            logger.error(f"保存PIP设置失败: {e}")
    
    def _load_auto_upgrade_setting(self):
        """加载自动升级设置"""
        try:
            settings_file = os.path.join(self.config_path, "pip_settings.json")
            if os.path.exists(settings_file):
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    
                # 设置自动升级选项
                if "auto_upgrade" in settings:
                    self.auto_upgrade_var.set(settings["auto_upgrade"])
                    logger.debug(f"已加载PIP自动升级设置: {settings['auto_upgrade']}")
        except Exception as e:
            logger.error(f"加载PIP设置失败: {e}")
            # 使用默认值
            self.auto_upgrade_var.set(False)

    def _update_python_environments(self):
        """周期性刷新Python环境信息，简单地调用_update_python_environment_info方法"""
        try:
            self._update_python_environment_info()
            logger.debug("已刷新Python环境信息")
        except Exception as e:
            logger.error(f"周期性刷新Python环境信息失败: {e}")

    def _get_theme_color(self, color_type):
        """获取当前主题的颜色"""
        try:
            style = ttk.Style()
            if hasattr(style, 'colors') and hasattr(style.colors, color_type):
                return getattr(style.colors, color_type)
            elif hasattr(style, 'lookup'):
                # 尝试使用lookup方法
                mapping = {
                    'bg': 'TFrame.background',
                    'fg': 'TLabel.foreground',
                    'selectbg': 'Treeview.selectBackground',
                    'selectfg': 'Treeview.selectForeground'
                }
                return style.lookup(mapping.get(color_type, 'TFrame'), color_type)
        except Exception as e:
            logger.error(f"获取主题颜色失败: {e}")
            return "black"
        
    def get_frame(self):
        """返回设置框架"""
        return self.parent

    def refresh_installed_packages(self):
        """刷新已安装的包列表"""
        self._load_package_info()

    def _init_pypi_mirrors(self):
        """初始化PyPI镜像列表"""
        # 这个方法是为了兼容性而添加的，可以在将来扩展添加镜像功能
        try:
            # 读取镜像配置文件（如果存在）
            mirrors_file = os.path.join(self.config_path, "pip_mirrors.json")
            if os.path.exists(mirrors_file):
                with open(mirrors_file, "r", encoding="utf-8") as f:
                    self.mirrors = json.load(f)
            else:
                # 默认镜像列表
                self.mirrors = [
                    {"name": "PyPI官方", "url": "https://pypi.org/simple/"},
                    {"name": "阿里云", "url": "https://mirrors.aliyun.com/pypi/simple/"},
                    {"name": "清华大学", "url": "https://pypi.tuna.tsinghua.edu.cn/simple/"},
                    {"name": "中国科技大学", "url": "https://pypi.mirrors.ustc.edu.cn/simple/"}
                ]
            
            logger.debug("PyPI镜像初始化成功")
        except Exception as e:
            logger.error(f"初始化PyPI镜像失败: {str(e)}")
            # 设置默认镜像
            self.mirrors = [{"name": "PyPI官方", "url": "https://pypi.org/simple/"}]
