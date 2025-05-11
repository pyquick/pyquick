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
import winreg
import re

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
            # 检查settings_manager是否存在
            if self.settings_manager is None:
                logger.warning("settings_manager为None，使用空列表作为默认值")
                self.python_installations = []
                return
                
            installations = self.settings_manager.get("python.installations", [])
            
            # 确保installations是列表类型
            if isinstance(installations, str):
                try:
                    # 尝试将字符串解析为JSON
                    import json
                    installations = json.loads(installations)
                except:
                    logger.error("Python安装信息格式错误，重置为空列表")
                    installations = []
            
            # 如果仍然不是列表，设置为空列表
            if not isinstance(installations, list):
                logger.error(f"Python安装信息类型错误: {type(installations)}，重置为空列表")
                installations = []
                
            self.python_installations = installations
            
            # 检查默认版本标记
            default_found = False
            for install in self.python_installations:
                if install.get("is_default", False):
                    default_found = True
                    break
            
            # 如果没有默认标记，标记第一个为默认（如果存在）
            if not default_found and self.python_installations:
                self.python_installations[0]["is_default"] = False
            
            # 检查sys.executable是否在列表中
            sys_executable_path = os.path.normcase(sys.executable)
            sys_executable_found = any(
                os.path.normcase(install.get("path", "")) == sys_executable_path
                for install in self.python_installations
            )
            
            # 如果sys.executable不在列表中，添加并设为默认
            if not sys_executable_found:
                from downloader import PythonManager
                from .save import SettingsManager
                from save_path import create_folder
                version="1965"
                config_path=create_folder.get_path("pyquick",version)
                self.b=SettingsManager(config_path)
                self.a=PythonManager.PythonManager(None)
                self.python_version=self.a._get_python_version(sys.executable)["version"]
                
                self.python_installations.append({
                    "path": sys.executable,
                    "version": self.python_version,
                    "is_default": True
                })
            
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
            
    def get_default_python(self):
        """
        获取标记为默认的Python安装信息
        
        Returns:
            包含默认Python信息的字典，如果未找到则返回None
        """
        try:
            for install in self.python_installations:
                if install.get("is_default", False):
                    logger.debug(f"找到默认Python环境: {install.get('path')}")
                    return install
            logger.warning("未找到标记为默认的Python环境")
            return None
        except Exception as e:
            logger.error(f"获取默认Python环境时出错: {e}")
            return None

    def _create_widgets(self):
        """创建设置界面组件"""
        # 当前Python信息
        current_frame = ttk.LabelFrame(self.frame, text="当前Python环境")
        current_frame.pack(fill=tk.X, padx=5, pady=5)
        
        info_frame = ttk.Frame(current_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 版本信息
        ttk.Label(info_frame, text="版本:").grid(row=0, column=0, sticky=tk.W)
        self.version_label = ttk.Label(info_frame, text="")
        self.version_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # 路径信息
        ttk.Label(info_frame, text="路径:").grid(row=1, column=0, sticky=tk.W)
        self.path_label = ttk.Label(info_frame, text="")
        self.path_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # pip版本
        ttk.Label(info_frame, text="pip版本:").grid(row=2, column=0, sticky=tk.W)
        self.pip_label = ttk.Label(info_frame, text="")
        self.pip_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Python安装列表
        list_frame = ttk.LabelFrame(self.frame, text="已安装的Python版本")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建树形视图
        columns = ("version", "path", "default")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                selectmode="browse")
        
        # 设置列
        self.tree.heading("version", text="版本")
        self.tree.heading("path", text="安装路径")
        self.tree.heading("default", text="默认")
        
        self.tree.column("version", width=100)
        self.tree.column("path", width=300)
        self.tree.column("default", width=50, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮区域
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        add_btn = ttk.Button(button_frame, text="添加",
                            command=lambda: self._add_python_installation(self.tree))
        add_btn.pack(side=tk.LEFT, padx=2)
        
        remove_btn = ttk.Button(button_frame, text="移除",
                               command=lambda: self._remove_python_installation(self.tree))
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        default_btn = ttk.Button(button_frame, text="设为默认",
                                command=lambda: self._set_default_python(self.tree))
        default_btn.pack(side=tk.LEFT, padx=2)
        
        detect_btn = ttk.Button(button_frame, text="自动检测",
                               command=lambda: self._auto_detect_python(self.tree))
        detect_btn.pack(side=tk.LEFT, padx=2)
        
        # 刷新当前信息
        self._refresh_current_info()
        
        # 显示已保存的Python安装
        self._refresh_python_list(self.tree)
        
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
            info["version"] = platform.python_version()
            
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
        python_path = filedialog.askopenfilename(
            title="选择Python解释器",
            filetypes=[
                ("Python解释器", "python*"),
                ("所有文件", "*.*")
            ]
        )
        
        if not python_path:
            return
            
        # 检查路径是否已存在
        for install in self.python_installations:
            if install["path"] == python_path:
                messagebox.showinfo("提示", "此Python安装已在列表中")
                return
                
        # 获取版本信息
        try:
            result = subprocess.run(
                [python_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip().split()[1]
            
            # 添加到列表
            install_info = {
                "version": version,
                "path": python_path,
                "is_default": not bool(self.python_installations)  # 如果是第一个则设为默认
            }
            
            self.python_installations.append(install_info)
            self._save_python_installations()
            
            # 刷新列表
            self._refresh_python_list(tree)
            
        except Exception as e:
            messagebox.showerror("错误", f"无法获取Python版本信息: {str(e)}")
            
    def _remove_python_installation(self, tree):
        """移除选定的Python安装"""
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要移除的Python安装")
            return
            
        selected_idx = tree.index(selected_items[0])
        
        if selected_idx < 0 or selected_idx >= len(self.python_installations):
            return
            
        # 询问确认
        if not messagebox.askyesno("确认", "确定要移除选定的Python安装吗？"):
            return
            
        # 如果移除的是默认版本，将第一个可用版本设为默认
        if self.python_installations[selected_idx].get("is_default", False):
            remaining = [i for i in range(len(self.python_installations))
                       if i != selected_idx]
            if remaining:
                self.python_installations[remaining[0]]["is_default"] = True
                
        # 移除安装信息
        del self.python_installations[selected_idx]
        self._save_python_installations()
        
        # 刷新列表
        self._refresh_python_list(tree)
        
    def _set_default_python(self, tree):
        """将选定的Python安装设为默认"""
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要设为默认的Python安装")
            return
            
        selected_idx = tree.index(selected_items[0])
        
        if selected_idx < 0 or selected_idx >= len(self.python_installations):
            return
            
        # 如果已经是默认版本，则不做更改
        if self.python_installations[selected_idx].get("is_default", False):
            messagebox.showinfo("提示", "此版本已经是默认版本")
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
        
    def _get_python_installations_from_registry(self) -> List[Dict[str, str]]:
        """
        从Windows注册表读取Python安装信息

        Returns:
            包含Python安装信息的字典列表
        """
        installations = []
        if platform.system() != "Windows":
            return installations

        # 获取注册表搜索路径 from settings_manager
        registry_paths = self.settings_manager.get(
            "python_versions.windows_specific.registry_paths",
            [
                "SOFTWARE\\Python\\PythonCore",
                "SOFTWARE\\Wow6432Node\\Python\\PythonCore",
            ]
        )

        for base_path in registry_paths:
            try:
                # 打开注册表项
                # HKEY_CURRENT_USER
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base_path) as hkey:
                        i = 0
                        while True:
                            try:
                                # 枚举子项 (Python版本)
                                version_key_name = winreg.EnumKey(hkey, i)
                                version_path = f"{base_path}\\{version_key_name}"
                                try:
                                    # Open the version key
                                    with winreg.OpenKey(hkey, version_path) as version_hkey:
                                        # Try to read InstallPath
                                        try:
                                            install_path, _ = winreg.QueryValueEx(version_hkey, "InstallPath")
                                            python_exe = os.path.join(install_path, "python.exe")
                                            if os.path.exists(python_exe) and python_exe not in [inst['path'] for inst in installations]:
                                                installations.append({"version": version_key_name, "path": python_exe, "is_default": False})
                                                logger.debug(f"从注册表(HKCU)找到Python: {version_key_name} at {python_exe}")
                                        except FileNotFoundError:
                                             logger.warning(f"注册表路径 {version_path} 下的 InstallPath 不存在")
                                        except Exception as e:
                                            logger.error(f"读取注册表 InstallPath 失败 ({version_path}): {e}")
                                except FileNotFoundError:
                                    logger.warning(f"注册表路径 {version_path} 不存在")
                                except Exception as e:
                                    logger.error(f"打开注册表路径 {version_path} 失败: {e}")

                                i += 1
                            except OSError:
                                # 没有更多子项
                                break
                            except Exception as e:
                                logger.error(f"枚举注册表子项失败 ({base_path}, index {i}): {e}")
                                i += 1 # 继续下一个子项

                except FileNotFoundError:
                    logger.debug(f"注册表路径 {base_path} (HKCU) 不存在")
                except Exception as e:
                    logger.error(f"访问注册表路径 {base_path} (HKCU) 失败: {e}")

                # HKEY_LOCAL_MACHINE
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path) as hkey:
                        i = 0
                        while True:
                            try:
                                # 枚举子项 (Python版本)
                                version_key_name = winreg.EnumKey(hkey, i)
                                version_path = f"{base_path}\\{version_key_name}"
                                try:
                                    # Open the version key
                                    with winreg.OpenKey(hkey, version_path) as version_hkey:
                                        # Try to read InstallPath
                                        try:
                                            install_path, _ = winreg.QueryValueEx(version_hkey, "InstallPath")
                                            python_exe = os.path.join(install_path, "python.exe")
                                            if os.path.exists(python_exe) and python_exe not in [inst['path'] for inst in installations]:
                                                installations.append({"version": version_key_name, "path": python_exe, "is_default": False})
                                                logger.debug(f"从注册表(HKLM)找到Python: {version_key_name} at {python_exe}")
                                        except FileNotFoundError:
                                             logger.warning(f"注册表路径 {version_path} 下的 InstallPath 不存在")
                                        except Exception as e:
                                            logger.error(f"读取注册表 InstallPath 失败 ({version_path}): {e}")
                                except FileNotFoundError:
                                    logger.warning(f"注册表路径 {version_path} 不存在")
                                except Exception as e:
                                    logger.error(f"打开注册表路径 {version_path} 失败: {e}")

                                i += 1
                            except OSError:
                                # 没有更多子项
                                break
                            except Exception as e:
                                logger.error(f"枚举注册表子项失败 ({base_path}, index {i}): {e}")
                                i += 1 # 继续下一个子项

                except FileNotFoundError:
                    logger.debug(f"注册表路径 {base_path} (HKLM) 不存在")
                except Exception as e:
                    logger.error(f"访问注册表路径 {base_path} (HKLM) 失败: {e}")

            except Exception as e:
                logger.error(f"处理注册表路径 {base_path} 时出错: {e}")

        return installations

    def _auto_detect_python(self, tree):
        """自动检测系统中安装的Python版本"""
        # 创建进度窗口
        progress_window = tk.Toplevel(self.parent)
        progress_window.title("检测Python安装")
        progress_window.transient(self.parent)
        progress_window.grab_set()
        
        # 窗口尺寸和位置
        window_width = 300
        window_height = 100
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 进度标签
        status_label = ttk.Label(progress_window, text="正在检测Python安装...")
        status_label.pack(pady=20)
        
        # 进度条
        progress_bar = ttk.Progressbar(progress_window, mode="indeterminate")
        progress_bar.pack(fill=tk.X, padx=20)
        progress_bar.start(10)
        
        # 首先检测系统默认Python
        try:
            default_python = sys.executable
            if default_python and os.path.isfile(default_python):
                # 获取版本信息
                version_output = subprocess.check_output([default_python, "--version"], stderr=subprocess.STDOUT).decode().strip()
                version_match = re.search(r"Python\s+(\d+\.\d+\.\d+)", version_output)
                version = version_match.group(1) if version_match else "未知版本"
                
                # 获取更多详细信息
                try:
                    import sysconfig
                    prefix = sysconfig.get_config_var('prefix')
                    base_prefix = sysconfig.get_config_var('base_prefix')
                    is_virtualenv = prefix != base_prefix
                except Exception:
                    is_virtualenv = False
                
                # 添加到安装列表
                self.python_installations.append({
                    "version": version,
                    "path": default_python,
                    "is_default": True,
                    "is_system": True,
                    "is_virtualenv": is_virtualenv,
                    "prefix": prefix if 'prefix' in locals() else None,
                    "base_prefix": base_prefix if 'base_prefix' in locals() else None
                })
                self._save_python_installations()
                self._refresh_python_list(tree)
                
                # 更新UI显示
                self._refresh_current_info()
                
        except Exception as e:
            logger.error(f"检测系统默认Python失败: {str(e)}")
        
        # 在新线程中执行其他检测
        detection_thread = threading.Thread(
            target=lambda: self._perform_auto_detection(tree, progress_window, status_label),
            daemon=True
        )
        detection_thread.start()
        
    def _perform_auto_detection(self, tree, progress_window, status_label):
        """
        执行自动检测Python安装
        增加Windows注册表检测
        """
        try:
            status_label.config(text="正在从注册表检测Python安装...")
            # 从注册表获取安装路径
            registry_installations = self._get_python_installations_from_registry()

            status_label.config(text="正在搜索常见目录中的Python安装...")
            # 可能的Python安装位置 (文件系统)
            search_paths = []

            if platform.system() == "Windows":
                # 获取常见路径 from settings_manager
                common_paths = self.settings_manager.get(
                    "python_versions.windows_specific.common_paths",
                    [
                        "C:\\Python*",
                        "%USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python*",
                        "%USERPROFILE%\\scoop\\apps\\python\\current\\python.exe",
                        "%USERPROFILE%\\miniconda3\\python.exe",
                        "%USERPROFILE%\\anaconda3\\python.exe"
                    ]
                )
                for path in common_paths:
                     search_paths.append(os.path.expandvars(path))

            else:  # Unix-like systems
                search_paths.extend([
                    "/usr/bin/python*",
                    "/usr/local/bin/python*",
                    os.path.expanduser("~") + "/.pyenv/versions/*/bin/python*"
                ])

            # 收集所有可能的Python路径 (文件系统)
            file_system_paths = []
            for path_pattern in search_paths:
                import glob
                file_system_paths.extend(glob.glob(path_pattern))

            # 合并注册表和文件系统找到的路径，并去重
            all_potential_paths = list(set([inst['path'] for inst in registry_installations] + file_system_paths))

            # 过滤并验证Python安装
            new_installations = []
            total_paths = len(all_potential_paths)
            for i, path in enumerate(all_potential_paths):
                status_label.config(text=f"正在验证 {path} ({i+1}/{total_paths})...")
                progress_window.update()
                try:
                    # 跳过已知的安装
                    if any(install["path"] == path for install in self.python_installations):
                        logger.debug(f"跳过已知的Python安装: {path}")
                        continue

                    # 检查路径是否存在且是文件
                    if not os.path.isfile(path):
                         logger.debug(f"路径不是文件或不存在: {path}")
                         continue

                    # 获取版本信息
                    # 检查文件名是否包含 'python' 且是可执行文件 (简单判断)
                    if "python" in os.path.basename(path).lower():
                         # 尝试运行获取版本
                         try:
                            # 使用适当的启动方法防止窗口弹出 (subprocess.STARTUPINFO on Windows)
                            startupinfo = None
                            if platform.system() == "Windows":
                                startupinfo = subprocess.STARTUPINFO()
                                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                startupinfo.wShowWindow = subprocess.SW_HIDE # 隐藏窗口

                            result = subprocess.run(
                                [path, "--version"],
                                capture_output=True,
                                text=True, # Capture output as text
                                check=True, # Raise exception for non-zero exit codes
                                encoding='utf-8', # Ensure correct encoding
                                startupinfo=startupinfo # Use startupinfo on Windows
                            )
                            # 提取版本号，可能在stdout或stderr
                            version_output = result.stdout.strip() if result.stdout else result.stderr.strip()
                            version_match = re.search(r"Python\s+(\d+\.\d+\.\d+)", version_output)
                            if version_match:
                                version = version_match.group(1)
                            else:
                                logger.warning(f"无法从输出中提取版本号: {version_output}")
                                version = "未知版本"

                            # 添加到新发现列表
                            new_installations.append({
                                "version": version,
                                "path": path,
                                "is_default": False
                            })
                            logger.debug(f"成功验证Python安装: {version} at {path}")
                         except FileNotFoundError:
                            logger.warning(f"Python可执行文件未找到: {path}")
                            continue
                         except subprocess.CalledProcessError as e:
                             logger.warning(f"运行 {path} --version 失败 (exit code {e.returncode}): {e.stdout} {e.stderr}")
                             continue
                         except Exception as e:
                            logger.error(f"验证Python安装 {path} 失败: {e}")
                            continue
                    else:
                        logger.debug(f"跳过非Python可执行文件: {path}")
                except Exception as e:
                        logger.error(f"验证Python安装 {path} 失败: {e}")
                        continue
                    


            def process_results():
                # 添加新发现的安装
                added_count = 0
                for install in new_installations:
                    # 再次检查是否已存在 (防止多线程或异步问题)
                    if not any(existing["path"] == install["path"]
                             for existing in self.python_installations):
                        # 如果是第一个安装则设为默认
                        if not self.python_installations:
                            install["is_default"] = True

                        self.python_installations.append(install)
                        added_count += 1

                self._save_python_installations()
                self._refresh_python_list(tree)

                # 关闭进度窗口
                if progress_window.winfo_exists():
                    progress_window.destroy()

                if added_count > 0:
                    messagebox.showinfo("检测结果", f"已添加{added_count}个新的Python安装")
                else:
                     messagebox.showinfo("检测结果", "未发现新的Python安装")

            # 在主线程中更新UI
            self.parent.after(0, process_results)

        except Exception as e:
            logger.error(f"自动检测Python安装失败: {str(e)}")

            def show_error():
                if progress_window.winfo_exists():
                    progress_window.destroy()
                messagebox.showerror("错误", f"检测Python安装时出错: {str(e)}")

            self.parent.after(0, show_error)
            
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