#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代理设置模块
负责管理网络代理设置并应用到全局
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import subprocess
import platform
from typing import Dict, Any, List, Optional, Tuple
import urllib.request
import socket
import time

logger = logging.getLogger(__name__)

class ProxySettings:
    """
    代理设置管理类
    负责管理HTTP/HTTPS/SOCKS代理设置
    """
    
    def __init__(self, parent, settings_manager):
        """
        初始化代理设置管理器
        
        Args:
            parent: 父级窗口
            settings_manager: 设置管理器实例
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.frame = ttk.Frame(parent)
        
        # 代理配置缓存
        self.proxy_config = {}
        
        # 创建变量
        self.proxy_enabled_var = tk.BooleanVar()
        self.proxy_type_var = tk.StringVar(value="HTTP")
        self.proxy_host_var = tk.StringVar()
        self.proxy_port_var = tk.StringVar()
        self.auth_enabled_var = tk.BooleanVar()
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.test_result_var = tk.StringVar()
        
        # 加载已保存的代理设置
        self._load_proxy_settings()
        
        # 创建UI组件
        self._create_widgets()
        
    def _create_widgets(self):
        """创建设置界面组件"""
        # 代理启用开关
        enable_frame = ttk.Frame(self.frame)
        enable_frame.pack(fill=tk.X, padx=5, pady=5)
        
        enable_proxy = ttk.Checkbutton(enable_frame, text="启用代理",
                                      variable=self.proxy_enabled_var,
                                      command=self._toggle_proxy_settings)
        enable_proxy.pack(side=tk.LEFT)
        
        # 代理设置区域
        settings_frame = ttk.LabelFrame(self.frame, text="代理设置")
        settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 代理类型
        type_frame = ttk.Frame(settings_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="代理类型:").pack(side=tk.LEFT)
        
        proxy_types = ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]
        type_combo = ttk.Combobox(type_frame, textvariable=self.proxy_type_var,
                                 values=proxy_types, state="readonly")
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)
        
        # 服务器地址
        host_frame = ttk.Frame(settings_frame)
        host_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(host_frame, text="服务器:").pack(side=tk.LEFT)
        
        host_entry = ttk.Entry(host_frame, textvariable=self.proxy_host_var)
        host_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(host_frame, text="端口:").pack(side=tk.LEFT)
        
        port_entry = ttk.Entry(host_frame, textvariable=self.proxy_port_var,
                              width=6)
        port_entry.pack(side=tk.LEFT, padx=5)
        
        # 认证设置
        auth_frame = ttk.LabelFrame(settings_frame, text="认证设置")
        auth_frame.pack(fill=tk.X, padx=5, pady=5)
        
        auth_check = ttk.Checkbutton(auth_frame, text="需要认证",
                                    variable=self.auth_enabled_var,
                                    command=self._toggle_auth_fields)
        auth_check.pack(anchor=tk.W, padx=5, pady=2)
        
        username_frame = ttk.Frame(auth_frame)
        username_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(username_frame, text="用户名:").pack(side=tk.LEFT)
        
        username_entry = ttk.Entry(username_frame, textvariable=self.username_var)
        username_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        password_frame = ttk.Frame(auth_frame)
        password_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(password_frame, text="密码:").pack(side=tk.LEFT)
        
        password_entry = ttk.Entry(password_frame, textvariable=self.password_var,
                                 show="*")
        password_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 测试按钮和结果
        test_frame = ttk.Frame(settings_frame)
        test_frame.pack(fill=tk.X, padx=5, pady=5)
        
        test_button = ttk.Button(test_frame, text="测试代理",
                                command=self._test_proxy)
        test_button.pack(side=tk.LEFT)
        
        self.test_result_label = ttk.Label(test_frame, textvariable=self.test_result_var)
        self.test_result_label.pack(side=tk.LEFT, padx=5)
        
        # 初始化UI状态
        self._toggle_proxy_settings()
        self._on_type_changed(None)
        
    def _toggle_proxy_settings(self):
        """切换代理设置的启用状态"""
        state = "normal" if self.proxy_enabled_var.get() else "disabled"
        
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for widget in child.winfo_children():
                    if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Button)):
                        widget.configure(state=state)
        
        # 更新认证字段状态
        if self.proxy_enabled_var.get():
            self._toggle_auth_fields()
            
    def _toggle_auth_fields(self):
        """切换认证字段的启用状态"""
        if not self.proxy_enabled_var.get():
            return
            
        state = "normal" if self.auth_enabled_var.get() else "disabled"
        
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.LabelFrame) and frame.cget("text") == "认证设置":
                        for widget in frame.winfo_children():
                            if isinstance(widget, ttk.Frame):
                                for entry in widget.winfo_children():
                                    if isinstance(entry, ttk.Entry):
                                        entry.configure(state=state)
                                        
    def _on_type_changed(self, event):
        """处理代理类型变化"""
        proxy_type = self.proxy_type_var.get().upper()
        
        # 更新默认端口
        default_ports = {
            "HTTP": "8080",
            "HTTPS": "8443",
            "SOCKS4": "1080",
            "SOCKS5": "1080"
        }
        
        if not self.proxy_port_var.get():
            self.proxy_port_var.set(default_ports.get(proxy_type, ""))
            
    def _load_proxy_settings(self):
        """从设置管理器加载代理设置"""
        try:
            # 获取代理设置
            self.proxy_config = {
                "enable_proxy": self.settings_manager.get("proxy.enable", False),
                "proxy_type": self.settings_manager.get("proxy.type", "HTTP"),
                "host": self.settings_manager.get("proxy.host", ""),
                "port": self.settings_manager.get("proxy.port", ""),
                "use_auth": self.settings_manager.get("proxy.auth.enable", False),
                "username": self.settings_manager.get("proxy.auth.username", ""),
                "password": self.settings_manager.get("proxy.auth.password", "")
            }
            
            # 更新UI变量
            self.proxy_enabled_var.set(self.proxy_config["enable_proxy"])
            self.proxy_type_var.set(self.proxy_config["proxy_type"])
            self.proxy_host_var.set(self.proxy_config["host"])
            self.proxy_port_var.set(self.proxy_config["port"])
            self.auth_enabled_var.set(self.proxy_config["use_auth"])
            self.username_var.set(self.proxy_config["username"])
            self.password_var.set(self.proxy_config["password"])
            
            logger.info("代理设置已加载")
        except Exception as e:
            logger.error(f"加载代理设置失败: {str(e)}")
            
    def save_settings(self):
        """保存设置到配置文件"""
        try:
            # 验证设置
            if self.proxy_enabled_var.get():
                if not self._validate_settings():
                    return False
            
            # 更新代理配置
            self.proxy_config["enable_proxy"] = self.proxy_enabled_var.get()
            self.proxy_config["proxy_type"] = self.proxy_type_var.get()
            self.proxy_config["host"] = self.proxy_host_var.get()
            self.proxy_config["port"] = self.proxy_port_var.get()
            self.proxy_config["use_auth"] = self.auth_enabled_var.get()
            self.proxy_config["username"] = self.username_var.get()
            self.proxy_config["password"] = self.password_var.get()
            
            # 保存到设置管理器
            self.settings_manager.set("proxy.enable", self.proxy_config["enable_proxy"])
            self.settings_manager.set("proxy.type", self.proxy_config["proxy_type"])
            self.settings_manager.set("proxy.host", self.proxy_config["host"])
            self.settings_manager.set("proxy.port", self.proxy_config["port"])
            self.settings_manager.set("proxy.auth.enable", self.proxy_config["use_auth"])
            self.settings_manager.set("proxy.auth.username", self.proxy_config["username"])
            self.settings_manager.set("proxy.auth.password", self.proxy_config["password"])
            
            # 应用代理设置
            if self.proxy_enabled_var.get():
                self.apply_proxy_settings()
            else:
                self.clear_proxy_settings()
                
            logger.info("代理设置已保存")
            return True
        except Exception as e:
            logger.error(f"保存代理设置失败: {str(e)}")
            return False
            
    def _validate_settings(self):
        """验证代理设置"""
        # 检查主机名
        host = self.proxy_host_var.get().strip()
        if not host:
            messagebox.showerror("错误", "代理服务器地址不能为空")
            return False
            
        # 检查端口
        try:
            port = int(self.proxy_port_var.get())
            if port <= 0 or port > 65535:
                messagebox.showerror("错误", "端口号必须在1-65535之间")
                return False
        except ValueError:
            messagebox.showerror("错误", "端口号必须是有效的数字")
            return False
            
        # 检查认证信息
        if self.auth_enabled_var.get():
            username = self.username_var.get().strip()
            password = self.password_var.get()
            
            if not username or not password:
                messagebox.showerror("错误", "启用认证时用户名和密码不能为空")
                return False
                
        return True
        
    def _test_proxy(self):
        """测试代理连接"""
        if not self._validate_settings():
            return
            
        # 构建代理URL
        proxy_type = self.proxy_type_var.get().lower()
        host = self.proxy_host_var.get()
        port = self.proxy_port_var.get()
        
        if self.auth_enabled_var.get():
            username = self.username_var.get()
            password = self.password_var.get()
            proxy_url = f"{proxy_type}://{username}:{password}@{host}:{port}"
        else:
            proxy_url = f"{proxy_type}://{host}:{port}"
            
        # 执行测试
        self.test_result_var.set("正在测试...")
        self.test_result_label.configure(foreground="black")
        
        def do_test():
            success, message = self._perform_proxy_test(proxy_type, proxy_url)
            
            def update_ui():
                if success:
                    self.test_result_var.set("测试成功")
                    self.test_result_label.configure(foreground="green")
                else:
                    self.test_result_var.set(f"测试失败: {message}")
                    self.test_result_label.configure(foreground="red")
                    
            self.parent.after(0, update_ui)
            
        threading.Thread(target=do_test, daemon=True).start()
        
    def _perform_proxy_test(self, proxy_type: str, proxy_url: str) -> Tuple[bool, str]:
        """
        执行代理测试
        
        Args:
            proxy_type: 代理类型
            proxy_url: 代理URL
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 先测试端口是否开放
            host = self.proxy_host_var.get()
            port = int(self.proxy_port_var.get())
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            if sock.connect_ex((host, port)) != 0:
                return False, "无法连接到代理服务器"
                
            sock.close()
            
            # 测试HTTP请求
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy_url if proxy_type in ['http', 'socks4', 'socks5'] else None,
                'https': proxy_url if proxy_type in ['https', 'socks4', 'socks5'] else None
            })
            
            opener = urllib.request.build_opener(proxy_handler)
            opener.addheaders = [('User-Agent', 'PyQuick-ProxyTest/1.0')]
            
            # 尝试访问一个测试URL
            test_url = "http://www.google.com"
            response = opener.open(test_url, timeout=10)
            
            if response.getcode() == 200:
                return True, "代理测试成功"
            else:
                return False, f"HTTP请求失败: {response.getcode()}"
                
        except Exception as e:
            return False, str(e)
            
    def apply_proxy_settings(self):
        """应用代理设置"""
        if not self.proxy_config["enable_proxy"]:
            self.clear_proxy_settings()
            return True
            
        try:
            proxy_type = self.proxy_config["proxy_type"].lower()
            host = self.proxy_config["host"]
            port = self.proxy_config["port"]
            
            # 构建代理URL
            if self.proxy_config["use_auth"]:
                username = self.proxy_config["username"]
                password = self.proxy_config["password"]
                proxy_url = f"{proxy_type}://{username}:{password}@{host}:{port}"
            else:
                proxy_url = f"{proxy_type}://{host}:{port}"
                
            # 设置环境变量
            os.environ["HTTP_PROXY"] = proxy_url if proxy_type in ["http", "socks4", "socks5"] else ""
            os.environ["HTTPS_PROXY"] = proxy_url if proxy_type in ["https", "socks4", "socks5"] else ""
            os.environ["NO_PROXY"] = "localhost,127.0.0.1"
            
            logger.info(f"已应用{proxy_type.upper()}代理设置")
            return True
        except Exception as e:
            logger.error(f"应用代理设置失败: {str(e)}")
            return False
            
    def clear_proxy_settings(self):
        """清除代理设置"""
        for var in ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
                   "http_proxy", "https_proxy", "no_proxy"]:
            if var in os.environ:
                del os.environ[var]
                
        logger.info("已清除代理设置")
        
    def get_frame(self):
        """返回设置框架"""
        return self.frame


# 测试代码
if __name__ == "__main__":
    # 创建简单的测试窗口
    root = tk.Tk()
    root.title("代理设置测试")
    root.geometry("700x400")
    
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
    
    # 创建代理设置管理器
    proxy_settings = ProxySettings(root, settings_manager)
    proxy_settings.get_frame().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    root.mainloop()