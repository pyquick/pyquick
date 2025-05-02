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
        
        # 加载已保存的代理设置
        self._load_proxy_settings()
        
        # 创建UI组件
        self._create_widgets()
    
    def _load_proxy_settings(self):
        """从设置管理器加载代理设置"""
        try:
            # 获取代理设置
            self.proxy_config = {
                "enable_proxy": self.settings_manager.get("proxy.enable", False),
                "proxy_type": self.settings_manager.get("proxy.type", "http"),
                "http_proxy": self.settings_manager.get("proxy.http", ""),
                "https_proxy": self.settings_manager.get("proxy.https", ""),
                "socks_proxy": self.settings_manager.get("proxy.socks", ""),
                "no_proxy": self.settings_manager.get("proxy.exclude", "localhost,127.0.0.1")
            }
            
            logger.info("代理设置已加载")
        except Exception as e:
            logger.error(f"加载代理设置失败: {str(e)}")
            # 设置默认值
            self.proxy_config = {
                "enable_proxy": False,
                "proxy_type": "http",
                "http_proxy": "",
                "https_proxy": "",
                "socks_proxy": "",
                "no_proxy": "localhost,127.0.0.1"
            }
    
    def _save_proxy_settings(self):
        """保存代理设置到设置管理器"""
        try:
            self.settings_manager.set("proxy.enable", self.proxy_config["enable_proxy"])
            self.settings_manager.set("proxy.type", self.proxy_config["proxy_type"])
            self.settings_manager.set("proxy.http", self.proxy_config["http_proxy"])
            self.settings_manager.set("proxy.https", self.proxy_config["https_proxy"])
            self.settings_manager.set("proxy.socks", self.proxy_config["socks_proxy"])
            self.settings_manager.set("proxy.exclude", self.proxy_config["no_proxy"])
            
            logger.info("代理设置已保存")
            return True
        except Exception as e:
            logger.error(f"保存代理设置失败: {str(e)}")
            return False
    
    def _create_widgets(self):
        """创建设置界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.frame, padding=(20, 10))
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 代理启用框架
        enable_frame = ttk.Frame(main_frame)
        enable_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 代理启用开关
        self.enable_var = tk.BooleanVar(value=self.proxy_config["enable_proxy"])
        enable_check = ttk.Checkbutton(enable_frame, text="启用代理", variable=self.enable_var,
                                       command=self._toggle_proxy_settings)
        enable_check.pack(side=tk.LEFT)
        
        # 创建代理设置框架
        settings_frame = ttk.LabelFrame(main_frame, text="代理设置", padding=(10, 5))
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 代理类型
        ttk.Label(settings_frame, text="代理类型:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.type_var = tk.StringVar(value=self.proxy_config["proxy_type"])
        type_combo = ttk.Combobox(settings_frame, textvariable=self.type_var, state="readonly", width=10)
        type_combo["values"] = ["http", "https", "socks"]
        type_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        type_combo.bind("<<ComboboxSelected>>", self._on_type_changed)
        
        # HTTP代理
        self.http_frame = ttk.Frame(settings_frame)
        self.http_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.http_frame, text="HTTP代理:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.http_var = tk.StringVar(value=self.proxy_config["http_proxy"])
        http_entry = ttk.Entry(self.http_frame, textvariable=self.http_var, width=40)
        http_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.http_frame, text="例如: http://127.0.0.1:8080").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        
        # HTTPS代理
        self.https_frame = ttk.Frame(settings_frame)
        self.https_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.https_frame, text="HTTPS代理:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.https_var = tk.StringVar(value=self.proxy_config["https_proxy"])
        https_entry = ttk.Entry(self.https_frame, textvariable=self.https_var, width=40)
        https_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.https_frame, text="例如: https://127.0.0.1:8080").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        
        # SOCKS代理
        self.socks_frame = ttk.Frame(settings_frame)
        self.socks_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.socks_frame, text="SOCKS代理:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.socks_var = tk.StringVar(value=self.proxy_config["socks_proxy"])
        socks_entry = ttk.Entry(self.socks_frame, textvariable=self.socks_var, width=40)
        socks_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.socks_frame, text="例如: socks5://127.0.0.1:1080").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        
        # 不使用代理的地址
        ttk.Label(settings_frame, text="不使用代理:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.no_proxy_var = tk.StringVar(value=self.proxy_config["no_proxy"])
        no_proxy_entry = ttk.Entry(settings_frame, textvariable=self.no_proxy_var, width=40)
        no_proxy_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(settings_frame, text="以逗号分隔，如: localhost,127.0.0.1").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        
        # 测试按钮
        test_button = ttk.Button(settings_frame, text="测试代理", command=self._test_proxy)
        test_button.grid(row=5, column=0, sticky=tk.W, padx=5, pady=10)
        
        # 测试结果标签
        self.test_result_var = tk.StringVar(value="")
        self.test_result_label = ttk.Label(settings_frame, textvariable=self.test_result_var)
        self.test_result_label.grid(row=5, column=1, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        # 初始化UI状态
        self._toggle_proxy_settings()
        self._on_type_changed(None)
    
    def _toggle_proxy_settings(self):
        """切换代理设置的启用状态"""
        enabled = self.enable_var.get()
        state = "normal" if enabled else "disabled"
        
        # 更新组件状态
        for widget in self.http_frame.winfo_children():
            if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                widget.configure(state=state)
        
        for widget in self.https_frame.winfo_children():
            if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                widget.configure(state=state)
        
        for widget in self.socks_frame.winfo_children():
            if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                widget.configure(state=state)
        
        # 更新代理设置缓存
        self.proxy_config["enable_proxy"] = enabled
    
    def _on_type_changed(self, event):
        """处理代理类型变化"""
        proxy_type = self.type_var.get()
        self.proxy_config["proxy_type"] = proxy_type
        
        # 根据代理类型调整UI显示
        if proxy_type == "http":
            self.http_frame.grid()
            self.https_frame.grid()
            self.socks_frame.grid_remove()
        elif proxy_type == "https":
            self.http_frame.grid_remove()
            self.https_frame.grid()
            self.socks_frame.grid_remove()
        elif proxy_type == "socks":
            self.http_frame.grid_remove()
            self.https_frame.grid_remove()
            self.socks_frame.grid()
    
    def _test_proxy(self):
        """测试代理连接"""
        if not self.enable_var.get():
            messagebox.showinfo("提示", "请先启用代理")
            return
        
        # 获取当前代理设置
        proxy_type = self.type_var.get()
        proxy_url = ""
        
        if proxy_type == "http":
            proxy_url = self.http_var.get()
        elif proxy_type == "https":
            proxy_url = self.https_var.get()
        elif proxy_type == "socks":
            proxy_url = self.socks_var.get()
        
        if not proxy_url:
            messagebox.showinfo("提示", f"请先填写{proxy_type.upper()}代理地址")
            return
        
        # 更新测试状态
        self.test_result_var.set("测试中...")
        self.test_result_label.configure(foreground="black")
        self.parent.update()
        
        # 启动测试线程
        threading.Thread(
            target=self._perform_proxy_test,
            args=(proxy_type, proxy_url),
            daemon=True
        ).start()
    
    def _perform_proxy_test(self, proxy_type, proxy_url):
        """执行代理测试"""
        result = {"success": False, "message": "", "time": 0}
        
        try:
            # 设置代理
            proxy_handler = None
            
            if proxy_type == "http":
                proxy_handler = urllib.request.ProxyHandler({
                    "http": proxy_url,
                    "https": self.https_var.get() or proxy_url
                })
            elif proxy_type == "https":
                proxy_handler = urllib.request.ProxyHandler({
                    "https": proxy_url
                })
            elif proxy_type == "socks":
                # SOCKS代理需要额外的处理
                try:
                    import socks
                    import socket
                    
                    # 解析代理地址
                    if "://" in proxy_url:
                        proto, rest = proxy_url.split("://", 1)
                        socks_version = socks.PROXY_TYPE_SOCKS5 if proto == "socks5" else socks.PROXY_TYPE_SOCKS4
                    else:
                        socks_version = socks.PROXY_TYPE_SOCKS5
                        rest = proxy_url
                    
                    if ":" in rest:
                        host, port = rest.split(":", 1)
                        port = int(port)
                    else:
                        host = rest
                        port = 1080
                    
                    # 创建带SOCKS支持的socket
                    socks.set_default_proxy(socks_version, host, port)
                    socket.socket = socks.socksocket
                    
                except ImportError:
                    raise Exception("使用SOCKS代理需要安装PySocks库")
            
            # 如果有代理处理器，创建opener
            if proxy_handler:
                opener = urllib.request.build_opener(proxy_handler)
                urllib.request.install_opener(opener)
            
            # 执行测试
            test_url = "https://www.baidu.com"
            
            start_time = time.time()
            response = urllib.request.urlopen(test_url, timeout=10)
            end_time = time.time()
            
            if response.getcode() == 200:
                result["success"] = True
                result["time"] = round((end_time - start_time) * 1000, 2)
                result["message"] = f"连接成功 ({result['time']} ms)"
            else:
                result["message"] = f"连接返回非200状态码: {response.getcode()}"
            
            response.close()
            
        except urllib.error.URLError as e:
            result["message"] = f"连接失败: {e.reason}"
        except socket.timeout:
            result["message"] = "连接超时"
        except Exception as e:
            result["message"] = f"测试出错: {str(e)}"
        
        # 在主线程中更新UI
        def update_ui():
            if result["success"]:
                self.test_result_var.set(result["message"])
                self.test_result_label.configure(foreground="green")
            else:
                self.test_result_var.set(result["message"])
                self.test_result_label.configure(foreground="red")
        
        self.parent.after(0, update_ui)
    
    def apply_proxy_settings(self):
        """应用代理设置到全局环境"""
        if not self.proxy_config["enable_proxy"]:
            # 清除环境变量中的代理设置
            for var in ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", 
                        "http_proxy", "https_proxy", "no_proxy"]:
                if var in os.environ:
                    del os.environ[var]
            
            logger.info("已清除全局代理设置")
            return True
        
        try:
            # 设置环境变量
            proxy_type = self.proxy_config["proxy_type"]
            
            if proxy_type in ["http", "https"]:
                # HTTP代理
                if proxy_type == "http" and self.proxy_config["http_proxy"]:
                    os.environ["HTTP_PROXY"] = self.proxy_config["http_proxy"]
                    os.environ["http_proxy"] = self.proxy_config["http_proxy"]
                
                # HTTPS代理
                if self.proxy_config["https_proxy"]:
                    os.environ["HTTPS_PROXY"] = self.proxy_config["https_proxy"]
                    os.environ["https_proxy"] = self.proxy_config["https_proxy"]
                elif proxy_type == "http" and self.proxy_config["http_proxy"]:
                    # 如果没有设置HTTPS代理但有HTTP代理，使用HTTP代理
                    os.environ["HTTPS_PROXY"] = self.proxy_config["http_proxy"]
                    os.environ["https_proxy"] = self.proxy_config["http_proxy"]
            
            elif proxy_type == "socks" and self.proxy_config["socks_proxy"]:
                # 尝试配置SOCKS代理
                try:
                    import socks
                    import socket
                    
                    # 解析代理地址
                    proxy_url = self.proxy_config["socks_proxy"]
                    if "://" in proxy_url:
                        proto, rest = proxy_url.split("://", 1)
                        socks_version = socks.PROXY_TYPE_SOCKS5 if proto == "socks5" else socks.PROXY_TYPE_SOCKS4
                    else:
                        socks_version = socks.PROXY_TYPE_SOCKS5
                        rest = proxy_url
                    
                    if ":" in rest:
                        host, port = rest.split(":", 1)
                        port = int(port)
                    else:
                        host = rest
                        port = 1080
                    
                    # 创建带SOCKS支持的socket
                    socks.set_default_proxy(socks_version, host, port)
                    socket.socket = socks.socksocket
                    
                    logger.info(f"已配置SOCKS代理: {proxy_url}")
                    
                except ImportError:
                    logger.warning("使用SOCKS代理需要安装PySocks库")
                    return False
            
            # 设置不使用代理的地址
            if self.proxy_config["no_proxy"]:
                os.environ["NO_PROXY"] = self.proxy_config["no_proxy"]
                os.environ["no_proxy"] = self.proxy_config["no_proxy"]
            
            logger.info(f"已应用{proxy_type.upper()}代理设置")
            return True
            
        except Exception as e:
            logger.error(f"应用代理设置失败: {str(e)}")
            return False
    
    def get_frame(self):
        """返回设置框架"""
        return self.frame
    
    def save_settings(self):
        """保存设置到配置文件"""
        # 更新代理配置
        self.proxy_config["http_proxy"] = self.http_var.get()
        self.proxy_config["https_proxy"] = self.https_var.get()
        self.proxy_config["socks_proxy"] = self.socks_var.get()
        self.proxy_config["no_proxy"] = self.no_proxy_var.get()
        
        return self._save_proxy_settings()


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