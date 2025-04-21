"""pip_manager.py - Pip包管理模块"""

import json
import subprocess
import tkinter as tk
from tkinter import ttk
from log import get_logger

logger = get_logger()

class PipManager:
    def __init__(self, config_path):
        self.config_path = config_path
        
    def get_installed_packages(self):
        """获取已安装的包列表"""
        try:
            pip_cmd = self._get_pip_command()
            if not pip_cmd:
                return []
                
            result = subprocess.run(
                [pip_cmd, "list", "--format=json"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
        except Exception as e:
            logger.error(f"获取已安装包列表失败: {e}")
            return []
            
    def _get_pip_command(self):
        """获取pip命令"""
        import os
        try:
            with open(os.path.join(self.config_path, "pythonversion.txt"), "r") as f:
                version_str = f.read().strip()
                if version_str.startswith("Python"):
                    version = version_str[6:]  # 提取版本号
                    return f"pip{version[0]}.{version[2]}"  # 如pip3.10
            return "pip"
        except Exception as e:
            logger.error(f"获取pip命令失败: {e}")
            return None
            
    def create_management_frame(self, parent):
        """创建pip管理界面"""
        frame = ttk.LabelFrame(parent, text="Pip包管理", padding=10)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 包列表显示框
        self.tree = ttk.Treeview(
            frame,
            columns=("name", "version", "latest"),
            show="headings",
            height=10
        )
        self.tree.pack(fill="both", expand=True, pady=5)
        self.tree.heading("name", text="包名")
        self.tree.heading("version", text="当前版本")
        self.tree.heading("latest", text="最新版本")
        
        # 操作按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(
            btn_frame,
            text="刷新",
            command=self.refresh_package_list
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="升级",
            command=self.upgrade_selected
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="卸载",
            command=self.uninstall_selected
        ).pack(side="left", padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(frame, text="")
        self.status_label.pack(fill="x")
        
        # 初始化包列表
        self.refresh_package_list()
        return frame
        
    def refresh_package_list(self):
        """刷新包列表"""
        packages = self.get_installed_packages()
        self.tree.delete(*self.tree.get_children())
        for pkg in packages:
            self.tree.insert("", "end", values=(pkg["name"], pkg["version"], ""))
        self.status_label.config(text=f"已加载 {len(packages)} 个包")
        
    def upgrade_selected(self):
        """升级选中的包"""
        selected = self.tree.selection()
        if not selected:
            self.status_label.config(text="请先选择一个包")
            return
            
        pkg_name = self.tree.item(selected[0])["values"][0]
        self.status_label.config(text=f"正在升级 {pkg_name}...")
        
    def uninstall_selected(self):
        """卸载选中的包"""
        selected = self.tree.selection()
        if not selected:
            self.status_label.config(text="请先选择一个包")
            return
            
        pkg_name = self.tree.item(selected[0])["values"][0]
        self.status_label.config(text=f"正在卸载 {pkg_name}...")
