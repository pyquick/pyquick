#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python版本管理器模块
负责管理和切换不同的Python版本
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import threading
import subprocess
import platform
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PythonManager:
    """
    Python版本管理类
    负责管理多个Python安装、切换默认版本等功能
    """
    
    def __init__(self, parent, settings_manager):
        """
        初始化Python版本管理器
        
        Args:
            parent: 父级窗口
            settings_manager: 设置管理器实例
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.frame = ttk.Frame(parent)
        
        # 管理的Python版本列表
        self.python_installations = []
        
        # 加载已经保存的Python版本信息
        self._load_python_installations()
        
        # 创建界面组件
        self._create_widgets()
    
    def _load_python_installations(self):
        """加载已保存的Python安装信息"""
        try:
            installations = self.settings_manager.get("python.installations", [])
            self.python_installations = installations
            
            # 检查默认版本标记
            default_found = False
            for install in self.python_installations:
                if install.get("is_default", False):
                    default_found = True
                    break
            
            # 如果没有默认标记，标记第一个为默认（如果存在）
            if not default_found and self.python_installations:
                self.python_installations[0]["is_default"] = True
                
            logger.info(f"已加载{len(self.python_installations)}个Python安装信息")
        except Exception as e:
            logger.error(f"加载Python安装信息失败: {str(e)}")
            self.python_installations = []
    
    def _save_python_installations(self):
        """保存Python安装信息到设置"""
        try:
            self.settings_manager.set("python.installations", self.python_installations)
            logger.info(f"已保存{len(self.python_installations)}个Python安装信息")
            return True
        except Exception as e:
            logger.error(f"保存Python安装信息失败: {str(e)}")
            return False
    
    def _create_widgets(self):
        """创建设置界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.frame, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 当前Python版本信息
        info_frame = ttk.LabelFrame(main_frame, text="当前Python环境", padding=(10, 5))
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        current_info = self._get_current_python_info()
        
        # 显示当前版本信息
        ttk.Label(info_frame, text="版本:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.version_label = ttk.Label(info_frame, text=current_info.get("version", "未知"))
        self.version_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="路径:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.path_label = ttk.Label(info_frame, text=current_info.get("path", "未知"))
        self.path_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(info_frame, text="pip版本:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.pip_label = ttk.Label(info_frame, text=current_info.get("pip_version", "未知"))
        self.pip_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        refresh_button = ttk.Button(info_frame, text="刷新", command=self._refresh_current_info)
        refresh_button.grid(row=0, column=2, rowspan=3, padx=5, pady=5, sticky=tk.E)
        
        # Python版本列表
        versions_frame = ttk.LabelFrame(main_frame, text="管理Python版本", padding=(10, 5))
        versions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ("版本", "路径", "默认")
        tree = ttk.Treeview(versions_frame, columns=columns, show="headings", height=6)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(versions_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 设置列标题和宽度
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column("版本", width=100, anchor=tk.W)
        tree.column("路径", width=300, anchor=tk.W)
        tree.column("默认", width=50, anchor=tk.CENTER)
        
        # 填充Python版本列表
        self._refresh_python_list(tree)
        
        # 双击处理
        tree.bind("<Double-1>", lambda event: self._set_default_python(tree))
        
        # 添加按钮框架
        button_frame = ttk.Frame(versions_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        add_button = ttk.Button(button_frame, text="添加", command=lambda: self._add_python_installation(tree))
        add_button.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_button = ttk.Button(button_frame, text="移除", command=lambda: self._remove_python_installation(tree))
        remove_button.pack(side=tk.LEFT, padx=5)
        
        set_default_button = ttk.Button(button_frame, text="设为默认", command=lambda: self._set_default_python(tree))
        set_default_button.pack(side=tk.LEFT, padx=5)
        
        detect_button = ttk.Button(button_frame, text="自动检测", command=lambda: self._auto_detect_python(tree))
        detect_button.pack(side=tk.LEFT, padx=5)
        
        # 保存树视图引用
        self.python_tree = tree
    
    def _get_current_python_info(self) -> Dict[str, str]:
        """
        获取当前Python环境信息
        
        Returns:
            包含版本、路径和pip版本的字典
        """
        info = {
            "version": "",
            "path": "",
            "pip_version": ""
        }
        
        try:
            # 获取Python版本
            version = platform.python_version()
            info["version"] = version
            
            # 获取Python路径
            info["path"] = sys.executable
            
            # 获取pip版本
            try:
                pip_process = subprocess.run(
                    [sys.executable, "-m", "pip", "--version"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                pip_output = pip_process.stdout.strip()
                # 提取pip版本，格式通常为 "pip X.Y.Z from ..."
                if pip_output:
                    pip_version = pip_output.split()[1]
                    info["pip_version"] = pip_version
            except Exception as e:
                logger.warning(f"获取pip版本失败: {str(e)}")
                info["pip_version"] = "未安装"
        
        except Exception as e:
            logger.error(f"获取Python信息失败: {str(e)}")
        
        return info
    
    def _refresh_current_info(self):
        """刷新当前Python环境信息"""
        current_info = self._get_current_python_info()
        
        self.version_label.config(text=current_info.get("version", "未知"))
        self.path_label.config(text=current_info.get("path", "未知"))
        self.pip_label.config(text=current_info.get("pip_version", "未知"))
    
    def _refresh_python_list(self, tree):
        """刷新Python版本列表"""
        # 清空现有项目
        for item in tree.get_children():
            tree.delete(item)
        
        # 添加Python安装信息
        for install in self.python_installations:
            is_default = install.get("is_default", False)
            default_mark = "✓" if is_default else ""
            tree.insert("", tk.END, values=(install["version"], install["path"], default_mark))
    
    def _add_python_installation(self, tree):
        """添加Python安装"""
        # 打开文件选择对话框
        python_path = filedialog.askopenfilename(
            title="选择Python解释器",
            filetypes=[
                ("Python解释器", "python*.exe" if platform.system() == "Windows" else "python*"),
                ("所有文件", "*.*")
            ]
        )
        
        if not python_path:
            return
        
        # 验证选择的Python解释器
        try:
            process = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                messagebox.showerror("错误", "无效的Python解释器")
                return
            
            # 提取版本信息
            version_output = process.stdout.strip() or process.stderr.strip()
            version = version_output.replace("Python ", "").strip()
            
            # 检查是否已存在此路径
            for install in self.python_installations:
                if install["path"] == python_path:
                    messagebox.showinfo("信息", "此Python安装已在列表中")
                    return
            
            # 添加到安装列表
            new_install = {
                "version": version,
                "path": python_path,
                "is_default": not self.python_installations  # 如果列表为空则设为默认
            }
            
            self.python_installations.append(new_install)
            self._save_python_installations()
            
            # 刷新列表
            self._refresh_python_list(tree)
            
        except Exception as e:
            logger.error(f"添加Python安装失败: {str(e)}")
            messagebox.showerror("错误", f"添加Python安装失败: {str(e)}")
    
    def _remove_python_installation(self, tree):
        """移除选定的Python安装"""
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showinfo("信息", "请先选择要移除的Python安装")
            return
        
        selected_idx = tree.index(selected_items[0])
        
        if selected_idx < 0 or selected_idx >= len(self.python_installations):
            return
        
        # 检查是否是默认版本
        if self.python_installations[selected_idx].get("is_default", False):
            if len(self.python_installations) > 1:
                # 如果有其他版本，询问用户是否要设置新的默认版本
                msg = "你要移除的是默认版本。是否要将列表中的下一个版本设为默认？"
                if messagebox.askyesno("确认", msg):
                    # 找到下一个可用版本
                    next_idx = (selected_idx + 1) % len(self.python_installations)
                    self.python_installations[next_idx]["is_default"] = True
                else:
                    return
            else:
                messagebox.showinfo("提示", "这是唯一的Python版本，不能移除")
                return
        
        # 移除选定版本
        del self.python_installations[selected_idx]
        self._save_python_installations()
        
        # 刷新列表
        self._refresh_python_list(tree)
    
    def _set_default_python(self, tree):
        """将选定的Python安装设为默认"""
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showinfo("信息", "请先选择要设为默认的Python安装")
            return
        
        selected_idx = tree.index(selected_items[0])
        
        if selected_idx < 0 or selected_idx >= len(self.python_installations):
            return
        
        # 如果已经是默认版本，则不做更改
        if self.python_installations[selected_idx].get("is_default", False):
            messagebox.showinfo("信息", "此版本已经是默认版本")
            return
        
        # 询问用户确认
        python_info = self.python_installations[selected_idx]
        msg = f"确定要将Python {python_info['version']} 设为默认版本吗？"
        
        if not messagebox.askyesno("确认", msg):
            return
        
        # 更新默认版本标记
        for i, install in enumerate(self.python_installations):
            install["is_default"] = (i == selected_idx)
        
        self._save_python_installations()
        
        # 刷新列表
        self._refresh_python_list(tree)
        
        # 提示用户重启应用以使用新版本
        messagebox.showinfo("提示", "默认Python版本已更改。请重启应用程序以使用新版本。")
    
    def _auto_detect_python(self, tree):
        """自动检测系统中安装的Python版本"""
        # 显示进度对话框
        progress_window = tk.Toplevel(self.parent)
        progress_window.title("检测Python安装")
        progress_window.geometry("300x100")
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        # 居中显示
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
        y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        # 创建进度指示
        ttk.Label(progress_window, text="正在检测系统中的Python安装...").pack(pady=(10, 5))
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(fill=tk.X, padx=20, pady=5)
        
        status_label = ttk.Label(progress_window, text="初始化...")
        status_label.pack(pady=5)
        
        progress.start()
        
        # 启动检测线程
        detect_thread = threading.Thread(
            target=self._perform_auto_detection,
            args=(tree, progress_window, status_label),
            daemon=True
        )
        detect_thread.start()
    
    def _perform_auto_detection(self, tree, progress_window, status_label):
        """执行自动检测Python安装"""
        detected_installations = []
        
        try:
            # 更新状态
            def update_status(text):
                if progress_window.winfo_exists():
                    status_label.config(text=text)
            
            # 在Windows上检测
            if platform.system() == "Windows":
                update_status("检测Windows注册表中的Python安装...")
                
                # 检查常见Python安装位置
                paths_to_check = [
                    os.path.expanduser("~\\AppData\\Local\\Programs\\Python"),
                    "C:\\Python",
                    "C:\\Program Files\\Python",
                    "C:\\Program Files (x86)\\Python"
                ]
                
                # 自定义检测函数
                def check_windows_python_dir(base_dir):
                    if not os.path.isdir(base_dir):
                        return
                    
                    # 检查子目录
                    for dir_name in os.listdir(base_dir):
                        dir_path = os.path.join(base_dir, dir_name)
                        python_exe = os.path.join(dir_path, "python.exe")
                        
                        if os.path.isfile(python_exe):
                            update_status(f"检测到: {python_exe}")
                            try:
                                # 获取版本信息
                                process = subprocess.run(
                                    [python_exe, "--version"],
                                    capture_output=True,
                                    text=True
                                )
                                
                                if process.returncode == 0:
                                    version_output = process.stdout.strip() or process.stderr.strip()
                                    version = version_output.replace("Python ", "").strip()
                                    
                                    detected_installations.append({
                                        "version": version,
                                        "path": python_exe,
                                        "is_default": False
                                    })
                            except Exception as e:
                                logger.warning(f"检测Python版本失败: {python_exe}, {str(e)}")
                
                # 检查所有路径
                for path in paths_to_check:
                    check_windows_python_dir(path)
            
            # 在macOS/Linux上检测
            else:
                update_status("检测UNIX系统中的Python安装...")
                
                # 检查常见位置
                paths_to_check = [
                    "/usr/bin/python*",
                    "/usr/local/bin/python*",
                    os.path.expanduser("~/Library/Python/*/bin/python*"),  # macOS
                    "/opt/homebrew/bin/python*",  # Homebrew on M1 Macs
                    "/opt/python/bin/python*"
                ]
                
                # 使用which命令查找不同版本的Python
                python_versions = ["python", "python3", "python3.9", "python3.10", "python3.11", "python3.12"]
                
                for py_ver in python_versions:
                    update_status(f"检测 {py_ver} ...")
                    try:
                        which_process = subprocess.run(
                            ["which", py_ver],
                            capture_output=True,
                            text=True
                        )
                        
                        if which_process.returncode == 0:
                            python_path = which_process.stdout.strip()
                            
                            if python_path and os.path.isfile(python_path):
                                # 获取版本信息
                                version_process = subprocess.run(
                                    [python_path, "--version"],
                                    capture_output=True,
                                    text=True
                                )
                                
                                if version_process.returncode == 0:
                                    version_output = version_process.stdout.strip() or version_process.stderr.strip()
                                    version = version_output.replace("Python ", "").strip()
                                    
                                    detected_installations.append({
                                        "version": version,
                                        "path": python_path,
                                        "is_default": False
                                    })
                    except Exception as e:
                        logger.warning(f"检测Python版本失败: {py_ver}, {str(e)}")
            
            # 处理检测结果
            def process_results():
                # 移除重复项
                unique_installations = []
                paths = set()
                
                for install in detected_installations:
                    if install["path"] not in paths:
                        paths.add(install["path"])
                        unique_installations.append(install)
                
                # 从现有安装中移除已经存在的路径
                existing_paths = {install["path"] for install in self.python_installations}
                new_installations = [install for install in unique_installations if install["path"] not in existing_paths]
                
                if not new_installations:
                    messagebox.showinfo("检测结果", "未检测到新的Python安装")
                else:
                    # 将检测到的安装添加到列表
                    for install in new_installations:
                        # 如果是第一个Python安装，则设为默认
                        if not self.python_installations:
                            install["is_default"] = True
                        
                        self.python_installations.append(install)
                    
                    self._save_python_installations()
                    self._refresh_python_list(tree)
                    messagebox.showinfo("检测结果", f"已添加{len(new_installations)}个新的Python安装")
                
                # 关闭进度窗口
                if progress_window.winfo_exists():
                    progress_window.destroy()
            
            # 在主线程中处理结果
            self.parent.after(0, process_results)
            
        except Exception as e:
            logger.error(f"自动检测Python安装失败: {str(e)}")
            
            def show_error():
                messagebox.showerror("错误", f"自动检测Python安装失败: {str(e)}")
                if progress_window.winfo_exists():
                    progress_window.destroy()
            
            self.parent.after(0, show_error)
    
    def get_default_python(self) -> Optional[Dict[str, Any]]:
        """获取默认Python安装信息"""
        for install in self.python_installations:
            if install.get("is_default", False):
                return install
        return None
    
    def get_frame(self):
        """返回设置框架"""
        return self.frame
    
    def save_settings(self):
        """保存设置"""
        return self._save_python_installations()


# 测试代码
if __name__ == "__main__":
    # 创建简单的测试窗口
    root = tk.Tk()
    root.title("Python版本管理器测试")
    root.geometry("600x500")
    
    # 创建一个模拟的设置管理器
    class MockSettingsManager:
        def __init__(self):
            self.settings = {}
        
        def get(self, key, default=None):
            keys = key.split(".")
            current = self.settings
            for k in keys[:-1]:
                if k not in current:
                    return default
                current = current[k]
            
            return current.get(keys[-1], default)
        
        def set(self, key, value):
            keys = key.split(".")
            current = self.settings
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            return True
    
    settings_manager = MockSettingsManager()
    
    # 创建Python版本管理器
    python_manager = PythonManager(root, settings_manager)
    python_manager.get_frame().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    root.mainloop() 