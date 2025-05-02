"""
PIP包管理界面，提供UI与功能的统一接口
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import json
import subprocess
import sys
import logging
import concurrent.futures

try:
    from log import app_logger, error_logger
except ImportError:
    app_logger = logging.getLogger("app")
    error_logger = logging.getLogger("error")

from .upgrade_pip import get_current_pip_version, get_latest_pip_version, upgrade_pip
from .install_unsi import install_package, uninstall_package, verify_package_exists, get_installed_version

class PipManager:
    """PIP包管理器，提供统一的UI与功能接口"""
    
    def __init__(self, root, container_frame, config_path=None):
        """
        初始化PIP管理器
        
        Args:
            root: 根窗口
            container_frame: 容器框架
            config_path: 配置路径
        """
        self.root = root
        self.container_frame = container_frame
        self.config_path = config_path
        self.pip_operations_running = False
        self.ui_update_queue = queue.Queue()
        
        # 构建UI
        self._build_ui()
        
        # 启动UI更新线程
        self._start_ui_updater()
        
        # 刷新PIP版本信息
        self.refresh_pip_version()
    
    def _build_ui(self):
        """构建PIP管理UI"""
        # 清空容器
        for widget in self.container_frame.winfo_children():
            widget.destroy()
            
        # 设置列权重
        self.container_frame.columnconfigure(0, weight=1)
        
        # 创建PIP版本信息框架
        version_frame = ttk.LabelFrame(self.container_frame, text="PIP版本信息", padding=10)
        version_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        version_frame.columnconfigure(1, weight=1)
        
        # 当前版本
        ttk.Label(version_frame, text="当前版本:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.current_version_label = ttk.Label(version_frame, text="正在检查...", foreground="grey")
        self.current_version_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        # 最新版本
        ttk.Label(version_frame, text="最新版本:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.latest_version_label = ttk.Label(version_frame, text="正在检查...", foreground="grey")
        self.latest_version_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # 刷新和升级按钮
        button_frame = ttk.Frame(version_frame)
        button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        
        self.refresh_version_btn = ttk.Button(button_frame, text="刷新版本信息", command=self.refresh_pip_version)
        self.refresh_version_btn.grid(row=0, column=0, padx=5)
        
        self.upgrade_pip_btn = ttk.Button(button_frame, text="升级PIP", state="disabled", command=self.upgrade_pip)
        self.upgrade_pip_btn.grid(row=0, column=1, padx=5)
        
        # 创建包管理框架和已安装包列表框架，使用左右布局
        main_frame = ttk.Frame(self.container_frame)
        main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        self.container_frame.rowconfigure(1, weight=1)

        # 创建包管理框架（左侧）
        package_frame = ttk.LabelFrame(main_frame, text="包管理", padding=10)
        package_frame.grid(row=0, column=0, padx=5, pady=10, sticky="nsew")
        package_frame.columnconfigure(1, weight=1)
        package_frame.rowconfigure(3, weight=1)
        
        # 包名输入
        ttk.Label(package_frame, text="包名:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.package_entry = ttk.Entry(package_frame)
        self.package_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # 已安装版本
        ttk.Label(package_frame, text="已安装版本:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.installed_version_label = ttk.Label(package_frame, text="")
        self.installed_version_label.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # 最新版本显示
        ttk.Label(package_frame, text="最新版本:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.latest_version_pkg_label = ttk.Label(package_frame, text="")
        self.latest_version_pkg_label.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # 检查按钮
        self.check_package_btn = ttk.Button(package_frame, text="检查包信息", command=self.check_package)
        self.check_package_btn.grid(row=3, column=0, padx=5, pady=5)
        
        # 安装和卸载按钮
        button_group = ttk.Frame(package_frame)
        button_group.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        self.install_btn = ttk.Button(button_group, text="安装", command=lambda: self.install_package(False), state="disabled")
        self.install_btn.grid(row=0, column=0, padx=5)
        
        self.upgrade_btn = ttk.Button(button_group, text="升级", command=lambda: self.install_package(True), state="disabled")
        self.upgrade_btn.grid(row=0, column=1, padx=5)
        
        self.uninstall_btn = ttk.Button(button_group, text="卸载", command=self.uninstall_package, state="disabled")
        self.uninstall_btn.grid(row=0, column=2, padx=5)
        
        # 创建已安装包列表框架（右侧）
        installed_frame = ttk.LabelFrame(main_frame, text="已安装的包", padding=10)
        installed_frame.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")
        installed_frame.columnconfigure(0, weight=1)
        installed_frame.rowconfigure(1, weight=1)
        
        # 创建刷新按钮
        refresh_frame = ttk.Frame(installed_frame)
        refresh_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        refresh_frame.columnconfigure(1, weight=1)
        
        self.refresh_packages_btn = ttk.Button(refresh_frame, text="刷新列表", command=self.refresh_installed_packages)
        self.refresh_packages_btn.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        # 创建包列表
        list_frame = ttk.Frame(installed_frame)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建带滚动条的包列表 - 修改列定义，添加"最新版本"和"状态"列
        self.packages_treeview = ttk.Treeview(list_frame, columns=("name", "version", "latest", "status"), show="headings", selectmode="browse")
        self.packages_treeview.heading("name", text="包名")
        self.packages_treeview.heading("version", text="当前版本")
        self.packages_treeview.heading("latest", text="最新版本")
        self.packages_treeview.heading("status", text="状态")
        self.packages_treeview.column("name", width=120)
        self.packages_treeview.column("version", width=80)
        self.packages_treeview.column("latest", width=80)
        self.packages_treeview.column("status", width=80)
        self.packages_treeview.grid(row=0, column=0, sticky="nsew")
        
        # 添加垂直滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.packages_treeview.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.packages_treeview.configure(yscrollcommand=scrollbar.set)
        
        # 绑定双击事件
        self.packages_treeview.bind("<Double-1>", self.on_package_select)
        
        # 创建进度框架
        progress_frame = ttk.LabelFrame(self.container_frame, text="操作进度", padding=10)
        progress_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, mode="indeterminate", length=300)
        self.progress_bar.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 状态标签
        self.status_label = ttk.Label(progress_frame, text="")
        self.status_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # 初始加载已安装的包列表
        self.refresh_installed_packages()
    
    def _start_ui_updater(self):
        """启动UI更新器"""
        def update_ui():
            try:
                while not self.ui_update_queue.empty():
                    update_func = self.ui_update_queue.get_nowait()
                    if callable(update_func):
                        update_func()
            finally:
                self.root.after(100, update_ui)
                
        self.root.after(100, update_ui)
    
    def refresh_pip_version(self):
        """刷新PIP版本信息"""
        if self.pip_operations_running:
            return
            
        self.pip_operations_running = True
        self.set_status("正在获取PIP版本信息...", True)
        self.refresh_version_btn.config(state="disabled")
        self.upgrade_pip_btn.config(state="disabled")
        
        def update_ui(current, latest, error=None):
            if error:
                self.set_status(f"获取版本信息失败: {error}", False)
                self.current_version_label.config(text="未知", foreground="red")
                self.latest_version_label.config(text="未知", foreground="red")
            else:
                if current == latest:
                    # 已是最新版本
                    self.current_version_label.config(text=current, foreground="green")
                    self.latest_version_label.config(text=latest, foreground="green")
                    self.set_status("PIP已是最新版本", False)
                    self.upgrade_pip_btn.config(state="disabled")
                else:
                    # 有新版本
                    self.current_version_label.config(text=current, foreground="orange")
                    self.latest_version_label.config(text=latest, foreground="green")
                    self.set_status(f"有新版本可用: {latest}", False)
                    self.upgrade_pip_btn.config(state="normal")
            
            self.refresh_version_btn.config(state="normal")
            self.pip_operations_running = False
        
        def check_thread():
            try:
                current = get_current_pip_version()
                latest = get_latest_pip_version()
                app_logger.info(f"PIP版本检查: 当前={current}, 最新={latest}")
                
                self.ui_update_queue.put(lambda: update_ui(current, latest))
            except Exception as e:
                error_logger.error(f"检查PIP版本失败: {str(e)}")
                self.ui_update_queue.put(lambda: update_ui(None, None, str(e)))
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def upgrade_pip(self):
        """升级PIP"""
        if self.pip_operations_running:
            return
            
        self.pip_operations_running = True
        self.set_status("正在升级PIP...", True)
        self.refresh_version_btn.config(state="disabled")
        self.upgrade_pip_btn.config(state="disabled")
        
        def update_ui(success, error=None):
            if success:
                self.set_status("PIP升级成功", False)
                # 刷新版本信息
                self.refresh_pip_version()
            else:
                self.set_status(f"PIP升级失败: {error}", False)
                self.pip_operations_running = False
                self.refresh_version_btn.config(state="normal")
                self.upgrade_pip_btn.config(state="normal")
        
        def upgrade_thread():
            try:
                success = upgrade_pip()
                app_logger.info(f"PIP升级结果: {'成功' if success else '失败'}")
                
                self.ui_update_queue.put(lambda: update_ui(success))
            except Exception as e:
                error_logger.error(f"升级PIP失败: {str(e)}")
                self.ui_update_queue.put(lambda: update_ui(False, str(e)))
        
        threading.Thread(target=upgrade_thread, daemon=True).start()
    
    def check_package(self):
        """检查包信息"""
        package_name = self.package_entry.get().strip()
        if not package_name:
            messagebox.showwarning("警告", "请输入包名")
            return
            
        if self.pip_operations_running:
            return
            
        self.pip_operations_running = True
        self.set_status(f"正在检查包 {package_name}...", True)
        self.check_package_btn.config(state="disabled")
        self.install_btn.config(state="disabled")
        self.upgrade_btn.config(state="disabled")
        self.uninstall_btn.config(state="disabled")
        
        def update_ui(exists, installed_version, latest_version, error=None):
            if error:
                self.set_status(f"检查包失败: {error}", False)
                self.installed_version_label.config(text="检查失败", foreground="red")
                self.latest_version_pkg_label.config(text="", foreground="red")
                self.install_btn.config(state="disabled")
                self.upgrade_btn.config(state="disabled")
                self.uninstall_btn.config(state="disabled")
            else:
                # 更新UI显示版本信息
                if installed_version:
                    self.installed_version_label.config(text=installed_version, foreground="green")
                    
                    # 显示最新版本信息
                    if exists and latest_version:
                        try:
                            from packaging import version
                            has_newer = version.parse(latest_version) > version.parse(installed_version)
                            if has_newer:
                                self.latest_version_pkg_label.config(text=latest_version, foreground="orange")
                                self.set_status(f"已安装版本 {installed_version}，最新版本 {latest_version}", False)
                                self.upgrade_btn.config(state="normal")
                            else:
                                self.latest_version_pkg_label.config(text=latest_version, foreground="green")
                                self.set_status(f"已安装最新版本 {installed_version}", False)
                                self.upgrade_btn.config(state="disabled")
                        except:
                            self.latest_version_pkg_label.config(text=latest_version, foreground="blue")
                            self.set_status(f"已安装版本 {installed_version}", False)
                            self.upgrade_btn.config(state="normal")
                    else:
                        self.latest_version_pkg_label.config(text="未知", foreground="gray")
                        self.set_status(f"已安装版本 {installed_version}", False)
                        self.upgrade_btn.config(state="disabled")
                    
                    self.install_btn.config(state="disabled")
                    self.uninstall_btn.config(state="normal")
                else:
                    self.installed_version_label.config(text="未安装", foreground="orange")
                    
                    if exists:
                        self.latest_version_pkg_label.config(text=latest_version, foreground="blue")
                        self.set_status(f"包 {package_name} 可用，最新版本 {latest_version}", False)
                        self.install_btn.config(state="normal")
                    else:
                        self.latest_version_pkg_label.config(text="", foreground="red")
                        self.set_status(f"包 {package_name} 不存在", False)
                        self.install_btn.config(state="disabled")
                        
                    self.upgrade_btn.config(state="disabled")
                    self.uninstall_btn.config(state="disabled")
            
            self.check_package_btn.config(state="normal")
            self.pip_operations_running = False
        
        def check_thread():
            try:
                # 检查本地安装版本
                installed_version = get_installed_version(package_name)
                
                # 检查远程版本
                exists, latest_version = verify_package_exists(package_name)
                
                app_logger.info(f"包检查结果: {package_name}, 已安装={installed_version}, 存在={exists}, 最新={latest_version}")
                
                self.ui_update_queue.put(lambda: update_ui(exists, installed_version, latest_version))
            except Exception as e:
                error_logger.error(f"检查包失败: {str(e)}")
                self.ui_update_queue.put(lambda: update_ui(False, None, None, str(e)))
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def install_package(self, upgrade=False):
        """安装或升级包"""
        package_name = self.package_entry.get().strip()
        if not package_name:
            messagebox.showwarning("警告", "请输入包名")
            return
            
        if self.pip_operations_running:
            return
            
        self.pip_operations_running = True
        action = "升级" if upgrade else "安装"
        self.set_status(f"正在{action}包 {package_name}...", True)
        self.check_package_btn.config(state="disabled")
        self.install_btn.config(state="disabled")
        self.upgrade_btn.config(state="disabled")
        self.uninstall_btn.config(state="disabled")
        
        def update_ui(success, error=None):
            if success:
                self.set_status(f"包 {package_name} {action}成功", False)
                # 重置状态并刷新包信息
                self.pip_operations_running = False # Reset flag before calling check_package
                self.check_package()
            else:
                self.set_status(f"包 {package_name} {action}失败: {error}", False)
                self.pip_operations_running = False
                self.check_package_btn.config(state="normal")
                if upgrade:
                    self.upgrade_btn.config(state="normal")
                else:
                    self.install_btn.config(state="normal")
        
        def install_thread():
            try:
                success = install_package(package_name, upgrade=upgrade)
                app_logger.info(f"包{action}结果: {package_name}, {'成功' if success else '失败'}")
                
                self.ui_update_queue.put(lambda: update_ui(success))
            except Exception as e:
                error_logger.error(f"{action}包失败: {str(e)}")
                self.ui_update_queue.put(lambda: update_ui(False, str(e)))
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def uninstall_package(self):
        """卸载包"""
        package_name = self.package_entry.get().strip()
        if not package_name:
            messagebox.showwarning("警告", "请输入包名")
            return
            
        if not messagebox.askyesno("确认", f"确定要卸载包 {package_name} 吗？"):
            return
            
        if self.pip_operations_running:
            return
            
        self.pip_operations_running = True
        self.set_status(f"正在卸载包 {package_name}...", True)
        self.check_package_btn.config(state="disabled")
        self.install_btn.config(state="disabled")
        self.upgrade_btn.config(state="disabled")
        self.uninstall_btn.config(state="disabled")
        
        def update_ui(success, error=None):
            if success:
                self.set_status(f"包 {package_name} 卸载成功", False)
                # 重置状态并刷新包信息
                self.pip_operations_running = False # Reset flag before calling check_package
                self.check_package()
            else:
                self.set_status(f"包 {package_name} 卸载失败: {error}", False)
                self.pip_operations_running = False
                self.check_package_btn.config(state="normal")
                self.uninstall_btn.config(state="normal")
        
        def uninstall_thread():
            try:
                success = uninstall_package(package_name)
                app_logger.info(f"包卸载结果: {package_name}, {'成功' if success else '失败'}")
                
                self.ui_update_queue.put(lambda: update_ui(success))
            except Exception as e:
                error_logger.error(f"卸载包失败: {str(e)}")
                self.ui_update_queue.put(lambda: update_ui(False, str(e)))
        
        threading.Thread(target=uninstall_thread, daemon=True).start()
    
    def set_status(self, message, in_progress=False):
        """设置状态信息"""
        # 使用after方法确保在主线程中更新UI
        self.root.after(0, lambda: self._update_status(message, in_progress))
    
    def _update_status(self, message, in_progress):
        """实际执行状态更新的内部方法"""
        self.status_label.config(text=message)
        
        if in_progress:
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()
            self.progress_bar['value'] = 0
    
    def on_package_select(self, event):
        """当用户双击包列表中的项目时调用"""
        selected_items = self.packages_treeview.selection()
        if selected_items:
            item = selected_items[0]
            values = self.packages_treeview.item(item, "values")
            package_name = values[0]
            current_version = values[1]
            latest_version = values[2]
            
            # 使用after方法确保在主线程中更新UI
            def update_ui():
                # 填充包信息
                self.package_entry.delete(0, tk.END)
                self.package_entry.insert(0, package_name)
                self.installed_version_label.config(text=current_version)
                self.latest_version_pkg_label.config(text=latest_version)
                
                # 设置按钮状态
                has_update = latest_version and latest_version != current_version
                self.upgrade_btn.config(state="normal" if has_update else "disabled")
                self.uninstall_btn.config(state="normal")
                self.install_btn.config(state="disabled")
                
                # 更新状态消息
                if has_update:
                    self.set_status(f"包 {package_name} 有新版本 {latest_version} 可用", False)
                else:
                    self.set_status(f"包 {package_name} 已安装最新版本 {current_version}", False)
            
            self.root.after(0, update_ui)

    def refresh_installed_packages(self):
        """刷新已安装包列表"""
        if hasattr(self, "running") and self.running:
            return

        def update_ui(packages_info):
            # 清空当前列表
            self.packages_treeview.delete(*self.packages_treeview.get_children())
            
            # 添加排序后的包到列表中
            for package in sorted(packages_info, key=lambda x: x['name'].lower()):
                name = package['name']
                version = package['version']
                latest = package.get('latest', '')
                
                # 判断是否需要升级
                upgradable = ''
                try:
                    if latest and version != latest:
                        from packaging import version as pkg_version
                        current = pkg_version.parse(version)
                        latest_ver = pkg_version.parse(latest)
                        if latest_ver > current:
                            upgradable = '✓'
                except Exception as e:
                    # 版本比较出错时，不标记为可升级
                    logging.warning(f"版本比较错误 {name}: {str(e)}")
                
                # 添加到UI
                self.packages_treeview.insert(
                    '', 'end', values=(name, version, latest, upgradable)
                )
            
            # 更新统计信息
            self.update_package_count()
            self.running = False

        def get_packages_with_latest_version():
            self.running = True
            packages_info = []
            error_msg = None
            
            try:
                # 线程安全地更新UI
                self.post_to_ui(lambda: self.status_label.config(text="正在获取已安装的包列表..."))
                self.post_to_ui(lambda: self.refresh_packages_btn.config(state="disabled"))
                self.post_to_ui(lambda: self.package_entry.config(state="disabled"))
                
                # 获取已安装的包列表
                import json
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "list", "--format=json"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    error_msg = f"获取包列表失败: {result.stderr}"
                    raise Exception(error_msg)
                
                packages = json.loads(result.stdout)
                
                # 按名称排序
                packages.sort(key=lambda x: x['name'].lower())
                
                # 先展示基本信息
                basic_info = [{'name': pkg['name'], 'version': pkg['version'], 'latest': ''} for pkg in packages]
                self.post_to_ui(lambda: update_ui(basic_info))
                
                # 更新状态 - 使用after方法确保在主线程更新UI
                total = len(packages)
                self.post_to_ui(lambda: self.status_label.config(text=f"正在获取最新版本信息 (0/{total})..."))
                
                def update_progress(current):
                    # 使用after方法确保在主线程更新UI
                    self.post_to_ui(lambda: self.status_label.config(text=f"正在获取最新版本信息 ({current}/{total})..."))
                
                # 通过并行处理获取每个包的最新版本
                from concurrent.futures import ThreadPoolExecutor
                import time
                
                def check_latest_version(index, package):
                    pkg_name = package['name']
                    current_version = package['version']
                    latest_version = ''
                    
                    try:
                        # 查询包的最新版本
                        cmd = [sys.executable, "-m", "pip", "index", "versions", pkg_name]
                        proc = subprocess.run(cmd, capture_output=True, text=True)
                        
                        if proc.returncode == 0:
                            # 解析输出以获取最新版本
                            output = proc.stdout
                            if 'Available versions:' in output:
                                versions_part = output.split('Available versions:')[1].strip()
                                if versions_part:
                                    # 获取第一个版本，通常是最新的
                                    latest_version = versions_part.split(',')[0].strip()
                    except Exception as e:
                        logging.warning(f"获取 {pkg_name} 最新版本失败: {str(e)}")
                    
                    # 更新进度 - 此处不需要修改，已经在主线程更新UI
                    self.post_to_ui(lambda: update_progress(index + 1))
                    
                    return {
                        'name': pkg_name,
                        'version': current_version,
                        'latest': latest_version
                    }
                
                # 使用线程池并行获取最新版本
                final_results = []
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {executor.submit(check_latest_version, i, pkg): i for i, pkg in enumerate(packages)}
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                            if result:
                                final_results.append(result)
                        except Exception as e:
                            logging.error(f"获取包版本时出错: {str(e)}")
                
                # 更新UI显示最终结果 - 此处不需要修改，已经在主线程更新UI
                self.root.after(0, lambda: update_ui(final_results))
                
                # 更新状态 - 使用after方法确保在主线程更新UI
                self.root.after(0, lambda: self.status_label.config(text=f"已安装 {len(final_results)} 个包"))
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"刷新包列表失败: {error_msg}")
                # 使用after方法确保在主线程更新UI
                self.root.after(0, lambda: self.status_label.config(text=f"错误: {error_msg}"))
                self.running = False
        
        # 在新线程中执行
        threading.Thread(target=get_packages_with_latest_version, daemon=True).start()

    def update_package_count(self):
        """更新包数量统计信息"""
        try:
            # 获取已安装包的数量
            count = len(self.packages_treeview.get_children())
            
            # 统计可升级包的数量
            upgradable_count = 0
            for item in self.packages_treeview.get_children():
                values = self.packages_treeview.item(item, "values")
                if len(values) >= 4 and values[3] == '✓':
                    upgradable_count += 1
            
            # 更新状态消息
            if count > 0:
                message = f"共 {count} 个已安装的包"
                if upgradable_count > 0:
                    message += f"，其中 {upgradable_count} 个可升级"
                # 使用after方法确保在主线程中更新UI
                self.root.after(0, lambda: self.set_status(message, False))
            else:
                self.root.after(0, lambda: self.set_status("没有已安装的包", False))
        except Exception as e:
            error_logger.error(f"更新包数量统计时出错: {str(e)}")

    def post_to_ui(self, func):
        """线程安全地在UI线程中执行函数"""
        try:
            if not self.root:
                return False
            
            if not hasattr(self.root, 'winfo_exists'):
                return False
            
            try:
                # 检查窗口是否还存在
                if not self.root.winfo_exists():
                    return False
            except:
                # 如果检查失败，假设窗口已不存在
                return False
            
            # 现在我们确定root存在且有效
            if threading.current_thread() == threading.main_thread():
                # 已在UI线程中，直接执行
                func()
            else:
                # 在其他线程中，使用after方法调度到UI线程
                # 包装在try-except中以防止错误
                def safe_execute():
                    try:
                        func()
                    except Exception as e:
                        error_logger.error(f"UI操作执行失败: {e}")
                
                try:
                    self.root.after(0, safe_execute)
                except Exception as e:
                    error_logger.error(f"调度UI操作失败: {e}")
                    return False
                
            return True
        except Exception as e:
            try:
                error_logger.error(f"更新UI失败: {e}")
            except:
                pass  # 即使日志记录也失败，我们也不能做更多
            return False
