"""
pip_management_ui.py - Multi-version pip management UI module

Provides UI components for:
- Displaying current pip version
- Scanning all pip versions
- Switching between pip versions
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import re
from typing import List, Dict

import pip_manager
from lang import get_text
from log import get_logger
from utils.tooltip import ToolTip

logger = get_logger()

class PipManagementUI:
    def __init__(self, parent):
        """初始化pip管理UI"""
        self.parent = parent
        self.frame = ttk.LabelFrame(parent, text=get_text("pip_version_management"), padding=10)
        self.frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # 版本选择
        ttk.Label(self.frame, text=get_text("select_pip_version")).grid(row=0, column=0, sticky="w", padx=5)
        
        self.version_var = tk.StringVar()
        self.version_combo = ttk.Combobox(
            self.frame, 
            textvariable=self.version_var, 
            state="readonly"
        )
        self.version_combo.grid(row=0, column=1, sticky="ew", padx=5)
        
        # 切换按钮
        self.switch_btn = ttk.Button(
            self.frame,
            text=get_text("switch_version"),
            command=self.switch_version
        )
        self.switch_btn.grid(row=0, column=2, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar()
        ttk.Label(
            self.frame,
            textvariable=self.status_var,
            foreground="green"
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 0))
        
    def load_versions(self, python_version):
        """加载指定Python版本的pip版本"""
        # 获取所有pip版本
        versions = pip_manager.scan_pip_versions()
        filtered_versions = [
            f"Python {v['python_version']} - pip {v['pip_version']}"
            for v in versions if v['python_version'] == python_version
        ]
        
        if filtered_versions:
            self.version_combo["values"] = filtered_versions
            self.version_combo.current(0)
            self.switch_btn.config(state="normal")
        else:
            self.version_combo["values"] = [get_text("no_pip_versions_found")]
            self.version_combo.current(0)
            self.switch_btn.config(state="disabled")
            
    def switch_version(self):
        """切换到选中的pip版本"""
        selected = self.version_combo.get()
        if not selected or selected == get_text("no_pip_versions_found"):
            return
            
        # 解析选中的Python路径
        match = re.search(r"Python (\d+\.\d+\.\d+)", selected)
        if not match:
            return
            
        python_version = match.group(1)
        pip_versions = pip_manager.scan_pip_versions()
        selected_pip = next(
            (v for v in pip_versions if v["python_version"] == python_version),
            None
        )
        
        if not selected_pip or not selected_pip["python_path"]:
            return
            
        self.switch_btn.config(state="disabled")
        
        def switch_thread():
            try:
                success = pip_manager.switch_pip_version(selected_pip["python_path"])
                if success:
                    self.status_var.set(
                        get_text("pip_version_switched").format(selected_pip["pip_version"])
                    )
            except Exception as e:
                logger.error(f"切换pip版本失败: {e}")
                self.status_var.set(get_text("switch_pip_failed"))
            finally:
                self.switch_btn.config(state="normal")
        
        threading.Thread(target=switch_thread, daemon=True).start()
