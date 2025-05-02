"""
镜像管理模块

实现Python和pip镜像站点的配置和管理，支持测试镜像连接速度并选择最佳镜像。
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List, Tuple

# 导入测试网络模块
import test_net
from test_net.python_mirror import PythonMirrorTester
from test_net.pip_mirror import PipMirrorTester

logger = logging.getLogger("settings")

class MirrorSettings:
    """镜像设置类"""
    
    def __init__(self, settings_manager):
        """
        初始化镜像设置
        
        Args:
            settings_manager: 设置管理器实例
        """
        self.settings_manager = settings_manager
    
    def get_python_mirror(self) -> Dict[str, Any]:
        """
        获取Python镜像设置
        
        Returns:
            Python镜像设置
        """
        return self.settings_manager.get_setting("mirrors.python_mirror", {
            "name": "官方源",
            "url": "https://www.python.org/ftp/python/",
            "enabled": True
        })
    
    def set_python_mirror(self, mirror: Dict[str, Any]) -> bool:
        """
        设置Python镜像
        
        Args:
            mirror: 镜像信息字典，包含name、url和enabled字段
            
        Returns:
            是否成功设置
        """
        if not isinstance(mirror, dict) or not all(k in mirror for k in ["name", "url", "enabled"]):
            logger.warning(f"无效的Python镜像信息: {mirror}")
            return False
        
        return self.settings_manager.set_setting("mirrors.python_mirror", mirror)
    
    def get_pip_mirror(self) -> Dict[str, Any]:
        """
        获取pip镜像设置
        
        Returns:
            pip镜像设置
        """
        return self.settings_manager.get_setting("mirrors.pip_mirror", {
            "name": "官方源",
            "url": "https://pypi.org/simple/",
            "enabled": True
        })
    
    def set_pip_mirror(self, mirror: Dict[str, Any]) -> bool:
        """
        设置pip镜像
        
        Args:
            mirror: 镜像信息字典，包含name、url和enabled字段
            
        Returns:
            是否成功设置
        """
        if not isinstance(mirror, dict) or not all(k in mirror for k in ["name", "url", "enabled"]):
            logger.warning(f"无效的pip镜像信息: {mirror}")
            return False
        
        return self.settings_manager.set_setting("mirrors.pip_mirror", mirror)
    
    def get_auto_select_best_mirror(self) -> bool:
        """
        获取是否自动选择最佳镜像
        
        Returns:
            是否自动选择最佳镜像
        """
        return self.settings_manager.get_setting("mirrors.auto_select_best_mirror", True)
    
    def set_auto_select_best_mirror(self, enabled: bool) -> bool:
        """
        设置是否自动选择最佳镜像
        
        Args:
            enabled: 是否启用
            
        Returns:
            是否成功设置
        """
        return self.settings_manager.set_setting("mirrors.auto_select_best_mirror", bool(enabled))
    
    def apply_pip_mirror_to_config(self, mirror: Dict[str, Any], user_only: bool = True) -> bool:
        """
        将pip镜像应用到pip配置
        
        Args:
            mirror: 镜像信息字典
            user_only: 是否仅应用到用户级配置
            
        Returns:
            是否成功应用
        """
        if not mirror or not mirror.get("url"):
            return False
        
        try:
            # 创建配置命令
            cmd = ["pip", "config", "set"]
            
            # 添加用户选项
            if user_only:
                cmd.append("--user")
            
            # 添加配置键和值
            cmd.extend(["global.index-url", mirror["url"]])
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            
            if result.returncode == 0:
                logger.info(f"已应用pip镜像配置: {mirror['name']} - {mirror['url']}")
                return True
            else:
                logger.error(f"应用pip镜像配置失败: {result.stderr}")
                return False
            
        except Exception as e:
            logger.error(f"应用pip镜像配置出错: {e}")
            return False
    
    def test_python_mirrors(self) -> Dict[str, Dict]:
        """
        测试所有Python镜像的连接速度
        
        Returns:
            测试结果字典
        """
        return test_net.test_python_mirrors()
    
    def test_pip_mirrors(self) -> Dict[str, Dict]:
        """
        测试所有pip镜像的连接速度
        
        Returns:
            测试结果字典
        """
        return test_net.test_pip_mirrors()
    
    def select_best_python_mirror(self) -> Optional[Dict[str, Any]]:
        """
        选择最佳Python镜像
        
        Returns:
            最佳镜像信息，如果没有可用镜像则返回None
        """
        best_mirror = test_net.get_best_python_mirror()
        if best_mirror:
            # 添加enabled字段
            best_mirror["enabled"] = True
            self.set_python_mirror(best_mirror)
            logger.info(f"已选择最佳Python镜像: {best_mirror['name']} - {best_mirror['url']}")
        return best_mirror
    
    def select_best_pip_mirror(self) -> Optional[Dict[str, Any]]:
        """
        选择最佳pip镜像
        
        Returns:
            最佳镜像信息，如果没有可用镜像则返回None
        """
        best_mirror = test_net.get_best_pip_mirror()
        if best_mirror:
            # 添加enabled字段
            best_mirror["enabled"] = True
            self.set_pip_mirror(best_mirror)
            logger.info(f"已选择最佳pip镜像: {best_mirror['name']} - {best_mirror['url']}")
        return best_mirror
    
    def create_settings_frame(self, parent):
        """
        创建镜像设置界面
        
        Args:
            parent: 父容器
            
        Returns:
            设置面板
        """
        frame = ttk.Frame(parent)
        
        # 自动选择最佳镜像
        auto_frame = ttk.Frame(frame)
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        auto_var = tk.BooleanVar(value=self.get_auto_select_best_mirror())
        auto_check = ttk.Checkbutton(
            auto_frame, 
            text="自动选择最佳镜像", 
            variable=auto_var,
            command=lambda: self.set_auto_select_best_mirror(auto_var.get())
        )
        auto_check.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(auto_frame, text="(将根据测试结果自动选择连接最快的镜像)").pack(side=tk.LEFT)
        
        # Python镜像设置
        python_frame = ttk.LabelFrame(frame, text="Python下载镜像")
        python_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Python镜像信息
        python_mirror = self.get_python_mirror()
        
        python_info_frame = ttk.Frame(python_frame)
        python_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(python_info_frame, text="当前镜像:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        python_name_label = ttk.Label(python_info_frame, text=python_mirror.get("name", "未设置"))
        python_name_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(python_info_frame, text="地址:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        python_url_label = ttk.Label(python_info_frame, text=python_mirror.get("url", ""))
        python_url_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        python_enabled_var = tk.BooleanVar(value=python_mirror.get("enabled", True))
        python_enabled = ttk.Checkbutton(
            python_frame, 
            text="启用Python镜像", 
            variable=python_enabled_var,
            command=self._toggle_python_mirror
        )
        python_enabled.pack(anchor=tk.W, padx=5, pady=5)
        
        # Python镜像操作按钮
        python_button_frame = ttk.Frame(python_frame)
        python_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            python_button_frame, 
            text="选择Python镜像", 
            command=self._show_python_mirror_selector
        ).pack(side=tk.LEFT, padx=5)
        
        # Pip镜像设置
        pip_frame = ttk.LabelFrame(frame, text="Pip包管理器镜像")
        pip_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Pip镜像信息
        pip_mirror = self.get_pip_mirror()
        
        pip_info_frame = ttk.Frame(pip_frame)
        pip_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(pip_info_frame, text="当前镜像:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        pip_name_label = ttk.Label(pip_info_frame, text=pip_mirror.get("name", "未设置"))
        pip_name_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(pip_info_frame, text="地址:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        pip_url_label = ttk.Label(pip_info_frame, text=pip_mirror.get("url", ""))
        pip_url_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        pip_enabled_var = tk.BooleanVar(value=pip_mirror.get("enabled", True))
        pip_enabled = ttk.Checkbutton(
            pip_frame, 
            text="启用Pip镜像", 
            variable=pip_enabled_var,
            command=self._toggle_pip_mirror
        )
        pip_enabled.pack(anchor=tk.W, padx=5, pady=5)
        
        # Pip镜像操作按钮
        pip_button_frame = ttk.Frame(pip_frame)
        pip_button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            pip_button_frame, 
            text="选择Pip镜像", 
            command=self._show_pip_mirror_selector
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            pip_button_frame, 
            text="应用镜像配置", 
            command=lambda: self._apply_pip_mirror(user_only=True)
        ).pack(side=tk.LEFT, padx=5)
        
        # 保存UI组件引用，以便后续更新
        self._ui = {
            "python_name_label": python_name_label,
            "python_url_label": python_url_label,
            "python_enabled_var": python_enabled_var,
            "pip_name_label": pip_name_label,
            "pip_url_label": pip_url_label,
            "pip_enabled_var": pip_enabled_var,
            "auto_var": auto_var
        }
        
        return frame
    
    def _toggle_python_mirror(self):
        """切换Python镜像启用状态"""
        if not hasattr(self, "_ui"):
            return
        
        python_mirror = self.get_python_mirror()
        python_mirror["enabled"] = self._ui["python_enabled_var"].get()
        self.set_python_mirror(python_mirror)
    
    def _toggle_pip_mirror(self):
        """切换Pip镜像启用状态"""
        if not hasattr(self, "_ui"):
            return
        
        pip_mirror = self.get_pip_mirror()
        pip_mirror["enabled"] = self._ui["pip_enabled_var"].get()
        self.set_pip_mirror(pip_mirror)
    
    def _show_python_mirror_selector(self):
        """显示Python镜像选择器窗口"""
        def on_mirror_selected(mirror):
            if mirror:
                # 添加enabled字段
                mirror["enabled"] = True
                self.set_python_mirror(mirror)
                
                # 更新UI
                if hasattr(self, "_ui"):
                    self._ui["python_name_label"].config(text=mirror["name"])
                    self._ui["python_url_label"].config(text=mirror["url"])
                    self._ui["python_enabled_var"].set(True)
                
                logger.info(f"已选择Python镜像: {mirror['name']} - {mirror['url']}")
        
        # 获取父窗口
        parent = None
        if hasattr(self, "_ui") and "python_name_label" in self._ui:
            parent = self._ui["python_name_label"].winfo_toplevel()
        
        # 创建镜像选择器窗口
        PythonMirrorTester(parent, on_mirror_selected)
    
    def _show_pip_mirror_selector(self):
        """显示Pip镜像选择器窗口"""
        def on_mirror_selected(mirror):
            if mirror:
                # 添加enabled字段
                mirror["enabled"] = True
                self.set_pip_mirror(mirror)
                
                # 更新UI
                if hasattr(self, "_ui"):
                    self._ui["pip_name_label"].config(text=mirror["name"])
                    self._ui["pip_url_label"].config(text=mirror["url"])
                    self._ui["pip_enabled_var"].set(True)
                
                logger.info(f"已选择Pip镜像: {mirror['name']} - {mirror['url']}")
        
        # 获取父窗口
        parent = None
        if hasattr(self, "_ui") and "pip_name_label" in self._ui:
            parent = self._ui["pip_name_label"].winfo_toplevel()
        
        # 创建镜像选择器窗口
        PipMirrorTester(parent, on_mirror_selected)
    
    def _apply_pip_mirror(self, user_only=True):
        """应用当前pip镜像配置"""
        pip_mirror = self.get_pip_mirror()
        if not pip_mirror.get("enabled", False):
            messagebox.showinfo("提示", "当前Pip镜像未启用，无需应用配置")
            return
        
        # 在后台线程中应用配置
        def apply_thread():
            success = self.apply_pip_mirror_to_config(pip_mirror, user_only)
            
            # 在主线程中显示结果
            if hasattr(self, "_ui") and "pip_name_label" in self._ui:
                parent = self._ui["pip_name_label"].winfo_toplevel()
                
                def show_result():
                    if success:
                        messagebox.showinfo("成功", f"已成功应用Pip镜像: {pip_mirror['name']}")
                    else:
                        messagebox.showerror("错误", "应用Pip镜像配置失败")
                
                parent.after(0, show_result)
        
        threading.Thread(target=apply_thread, daemon=True).start()

class MirrorManager:
    """镜像源管理类,负责管理Python和pip镜像源设置"""
    
    def __init__(self, parent, settings_manager):
        """
        初始化镜像源管理器
        
        Args:
            parent: 父级窗口
            settings_manager: 设置管理器实例 
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.frame = ttk.Frame(parent)
        
        # 预定义的镜像源
        self.predefined_mirrors = {
            "Python": {
                "官方源": "https://www.python.org/ftp/python",
                "阿里云": "https://mirrors.aliyun.com/python",
                "华为云": "https://repo.huaweicloud.com/python",
                "腾讯云": "https://mirrors.cloud.tencent.com/python",
                "清华源": "https://pypi.tuna.tsinghua.edu.cn/simple"
            },
            "PyPI": {
                "官方源": "https://pypi.org/simple",
                "阿里云": "https://mirrors.aliyun.com/pypi/simple",
                "华为云": "https://repo.huaweicloud.com/pypi/simple",
                "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple",
                "清华源": "https://pypi.tuna.tsinghua.edu.cn/simple"
            }
        }
        
        # 创建界面组件
        self._create_widgets()
        
        # 应用当前设置
        self._load_settings()
        
    def _create_widgets(self):
        """创建设置界面组件"""
        # Python镜像设置
        python_frame = ttk.LabelFrame(self.frame, text="Python镜像设置")
        python_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Python镜像选择
        python_mirror_frame = ttk.Frame(python_frame)
        python_mirror_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(python_mirror_frame, text="Python镜像源:").pack(side=tk.LEFT)
        
        self.python_mirror_var = tk.StringVar()
        python_combo = ttk.Combobox(python_mirror_frame,
                                  textvariable=self.python_mirror_var,
                                  values=list(self.predefined_mirrors["Python"].keys()),
                                  state="readonly",
                                  width=30)
        python_combo.pack(side=tk.LEFT, padx=5)
        
        # 自定义Python镜像
        custom_python_frame = ttk.Frame(python_frame)
        custom_python_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(custom_python_frame, text="自定义Python镜像:").pack(side=tk.LEFT)
        
        self.custom_python_var = tk.StringVar()
        custom_python_entry = ttk.Entry(custom_python_frame,
                                      textvariable=self.custom_python_var,
                                      width=50)
        custom_python_entry.pack(side=tk.LEFT, padx=5)
        
        # PyPI镜像设置
        pip_frame = ttk.LabelFrame(self.frame, text="PyPI镜像设置")
        pip_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # PyPI镜像选择
        pip_mirror_frame = ttk.Frame(pip_frame)
        pip_mirror_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(pip_mirror_frame, text="PyPI镜像源:").pack(side=tk.LEFT)
        
        self.pip_mirror_var = tk.StringVar()
        pip_combo = ttk.Combobox(pip_mirror_frame,
                                textvariable=self.pip_mirror_var,
                                values=list(self.predefined_mirrors["PyPI"].keys()),
                                state="readonly",
                                width=30)
        pip_combo.pack(side=tk.LEFT, padx=5)
        
        # 自定义PyPI镜像
        custom_pip_frame = ttk.Frame(pip_frame)
        custom_pip_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(custom_pip_frame, text="自定义PyPI镜像:").pack(side=tk.LEFT)
        
        self.custom_pip_var = tk.StringVar()
        custom_pip_entry = ttk.Entry(custom_pip_frame,
                                   textvariable=self.custom_pip_var,
                                   width=50)
        custom_pip_entry.pack(side=tk.LEFT, padx=5)
        
        # 镜像测试状态
        status_frame = ttk.Frame(self.frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.python_status_var = tk.StringVar(value="Python镜像: 未测试")
        ttk.Label(status_frame, textvariable=self.python_status_var).pack(side=tk.LEFT)
        
        ttk.Label(status_frame, text="  |  ").pack(side=tk.LEFT)
        
        self.pip_status_var = tk.StringVar(value="PyPI镜像: 未测试")
        ttk.Label(status_frame, textvariable=self.pip_status_var).pack(side=tk.LEFT)
        
        # 按钮区域
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="测试镜像",
                   command=self._test_mirrors).pack(side=tk.LEFT, padx=5)
                   
        ttk.Button(button_frame, text="应用设置",
                   command=self._apply_settings).pack(side=tk.RIGHT, padx=5)
                   
        ttk.Button(button_frame, text="重置为默认",
                   command=self._reset_to_default).pack(side=tk.RIGHT)
                   
        # 绑定事件
        python_combo.bind("<<ComboboxSelected>>",
                         lambda e: self._on_mirror_selected("Python"))
        pip_combo.bind("<<ComboboxSelected>>",
                      lambda e: self._on_mirror_selected("PyPI"))
                      
    def _load_settings(self):
        """加载当前设置"""
        # 加载Python镜像设置
        python_mirror = self.settings_manager.get("mirror.python", "官方源")
        custom_python = self.settings_manager.get("mirror.python_custom", "")
        
        if custom_python:
            self.custom_python_var.set(custom_python)
            self.python_mirror_var.set("自定义")
        else:
            self.python_mirror_var.set(python_mirror)
            
        # 加载PyPI镜像设置    
        pip_mirror = self.settings_manager.get("mirror.pypi", "官方源")
        custom_pip = self.settings_manager.get("mirror.pypi_custom", "")
        
        if custom_pip:
            self.custom_pip_var.set(custom_pip)
            self.pip_mirror_var.set("自定义")
        else:
            self.pip_mirror_var.set(pip_mirror)
            
    def _on_mirror_selected(self, mirror_type: str):
        """
        处理镜像源选择变化
        
        Args:
            mirror_type: 镜像类型("Python"或"PyPI")
        """
        if mirror_type == "Python":
            selected = self.python_mirror_var.get()
            if selected in self.predefined_mirrors["Python"]:
                self.custom_python_var.set(self.predefined_mirrors["Python"][selected])
        else:
            selected = self.pip_mirror_var.get()
            if selected in self.predefined_mirrors["PyPI"]:
                self.custom_pip_var.set(self.predefined_mirrors["PyPI"][selected])
                
    def _test_mirrors(self):
        """测试镜像源连接性"""
        import threading
        import requests
        from urllib.parse import urljoin
        
        def test_mirror(url: str, mirror_type: str):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                
                def update_status(success=True):
                    status_var = (self.python_status_var if mirror_type == "Python" 
                                else self.pip_status_var)
                    if success:
                        status_var.set(f"{mirror_type}镜像: 连接正常")
                    else:
                        status_var.set(f"{mirror_type}镜像: 连接失败")
                        
                self.parent.after(0, update_status)
                
            except Exception as e:
                self.parent.after(0, lambda: update_status(False))
                
        # 获取当前镜像URL
        python_url = self.custom_python_var.get()
        pip_url = self.custom_pip_var.get()
        
        # 启动测试线程
        threading.Thread(target=test_mirror, args=(python_url, "Python"),
                        daemon=True).start()
        threading.Thread(target=test_mirror, args=(pip_url, "PyPI"),
                        daemon=True).start()
                        
    def _apply_settings(self):
        """应用镜像设置"""
        try:
            # 保存Python镜像设置
            python_mirror = self.python_mirror_var.get()
            custom_python = self.custom_python_var.get()
            
            self.settings_manager.set("mirror.python", python_mirror)
            if python_mirror == "自定义":
                self.settings_manager.set("mirror.python_custom", custom_python)
            else:
                self.settings_manager.set("mirror.python_custom", "")
                
            # 保存PyPI镜像设置
            pip_mirror = self.pip_mirror_var.get()
            custom_pip = self.custom_pip_var.get()
            
            self.settings_manager.set("mirror.pypi", pip_mirror)
            if pip_mirror == "自定义":
                self.settings_manager.set("mirror.pypi_custom", custom_pip)
            else:
                self.settings_manager.set("mirror.pypi_custom", "")
                
            messagebox.showinfo("成功", "镜像设置已更新")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")
            
    def _reset_to_default(self):
        """重置为默认设置"""
        if not messagebox.askyesno("确认", "确定要重置为默认镜像设置吗？"):
            return
            
        # 重置为官方源
        self.python_mirror_var.set("官方源")
        self.pip_mirror_var.set("官方源")
        self.custom_python_var.set(self.predefined_mirrors["Python"]["官方源"])
        self.custom_pip_var.set(self.predefined_mirrors["PyPI"]["官方源"])
        
        # 应用设置
        self._apply_settings()
        
    def get_frame(self):
        """返回设置框架"""
        return self.frame