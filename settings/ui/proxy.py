"""
代理设置面板，用于管理网络代理配置
"""
import tkinter as tk
from tkinter import ttk
import logging

from settings.ui.base_panel import BaseSettingsPanel

class ProxySettingsPanel(BaseSettingsPanel):
    """
    代理设置面板类，管理网络代理配置
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化代理设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.proxy_enabled_var = tk.BooleanVar()
        self.proxy_type_var = tk.StringVar()
        self.proxy_host_var = tk.StringVar()
        self.proxy_port_var = tk.StringVar()
        self.use_auth_var = tk.BooleanVar()
        self.proxy_username_var = tk.StringVar()
        self.proxy_password_var = tk.StringVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置代理设置面板的用户界面"""
        # 代理启用设置
        enable_section, enable_content = self.create_section_frame("代理设置")
        
        # 启用代理
        enable_frame = ttk.Frame(enable_content)
        enable_frame.pack(fill=tk.X, pady=5)
        
        enable_check = ttk.Checkbutton(enable_frame, text="启用代理服务器", 
                                     variable=self.proxy_enabled_var,
                                     command=self._toggle_proxy_fields)
        enable_check.pack(side=tk.LEFT, padx=5)
        
        # 代理服务器设置
        server_section, server_content = self.create_section_frame("服务器配置")
        
        # 代理类型
        proxy_types = ["http", "https", "socks4", "socks5"]
        type_frame, type_label, type_combo = self.create_labeled_combobox(
            server_content, "代理类型:", self.proxy_type_var, proxy_types)
        type_frame.pack(fill=tk.X, pady=5)
        
        # 代理服务器地址
        host_frame, host_label, self.host_entry = self.create_labeled_entry(
            server_content, "服务器地址:", self.proxy_host_var, width=30)
        host_frame.pack(fill=tk.X, pady=5)
        
        # 代理服务器端口
        port_frame, port_label, self.port_entry = self.create_labeled_entry(
            server_content, "服务器端口:", self.proxy_port_var, width=10)
        port_frame.pack(fill=tk.X, pady=5)
        
        # 认证设置
        auth_section, auth_content = self.create_section_frame("认证设置")
        
        # 启用认证
        auth_frame = ttk.Frame(auth_content)
        auth_frame.pack(fill=tk.X, pady=5)
        
        auth_check = ttk.Checkbutton(auth_frame, text="使用认证", 
                                   variable=self.use_auth_var,
                                    command=self._toggle_auth_fields)
        auth_check.pack(side=tk.LEFT, padx=5)
        
        # 用户名
        username_frame, username_label, self.username_entry = self.create_labeled_entry(
            auth_content, "用户名:", self.proxy_username_var, width=30)
        username_frame.pack(fill=tk.X, pady=5)
        
        # 密码
        password_frame, password_label, self.password_entry = self.create_labeled_entry(
            auth_content, "密码:", self.proxy_password_var, width=30)
        password_frame.pack(fill=tk.X, pady=5)
        self.password_entry.config(show="*")  # 显示为星号
        
        # 测试连接按钮
        test_frame = ttk.Frame(auth_content)
        test_frame.pack(fill=tk.X, pady=10)
        
        test_button = ttk.Button(test_frame, text="测试连接", command=self._test_connection)
        test_button.pack(side=tk.RIGHT, padx=5)
        
        # 状态标签
        self.status_label = ttk.Label(test_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 初始化UI状态
        self._toggle_proxy_fields()
        self._toggle_auth_fields()
    
    def _toggle_proxy_fields(self):
        """切换代理设置字段的启用状态"""
        state = "normal" if self.proxy_enabled_var.get() else "disabled"
        
        # 更新代理类型选择
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame) and child.cget("text") == "服务器配置":
                for widget in child.winfo_children():
                    for w in widget.winfo_children():
                        if isinstance(w, (ttk.Entry, ttk.Combobox)):
                            w.configure(state=state)
        
        # 认证部分的启用状态也需要同步
        self._toggle_auth_fields()
    
    def _toggle_auth_fields(self):
        """切换认证设置字段的启用状态"""
        proxy_enabled = self.proxy_enabled_var.get()
        auth_enabled = self.use_auth_var.get() and proxy_enabled
        
        state = "normal" if auth_enabled else "disabled"
        
        # 用户名和密码字段
        if hasattr(self, 'username_entry'):
            self.username_entry.configure(state=state)
        if hasattr(self, 'password_entry'):
            self.password_entry.configure(state=state)
    
    def _test_connection(self):
        """测试代理连接"""
        import requests
        import time
        
        if not self.proxy_enabled_var.get():
            self.status_label.config(text="请先启用代理服务器", foreground="red")
            return
        
        host = self.proxy_host_var.get()
        port = self.proxy_port_var.get()
        
        if not host or not port:
            self.status_label.config(text="请输入服务器地址和端口", foreground="red")
            return
        
        # 构建代理URL
        proxy_type = self.proxy_type_var.get()
        proxy_url = f"{proxy_type}://"
        
        # 添加认证信息
        if self.use_auth_var.get():
            username = self.proxy_username_var.get()
            password = self.proxy_password_var.get()
            if username and password:
                proxy_url += f"{username}:{password}@"
        
        proxy_url += f"{host}:{port}"
        
        # 显示测试中状态
        self.status_label.config(text="正在测试连接...", foreground="blue")
        self.update()  # 更新UI
        
        # 创建一个线程执行测试
        def test_thread():
            try:
                proxies = {
                    "http": proxy_url,
                    "https": proxy_url
                }
                
                # 设置超时时间为5秒
                start_time = time.time()
                response = requests.get("https://www.baidu.com", proxies=proxies, timeout=5)
                end_time = time.time()
                
                if response.status_code == 200:
                    # 在主线程中更新UI
                    ping = int((end_time - start_time) * 1000)
                    self.after(0, lambda: self.status_label.config(
                        text=f"连接成功! 延迟: {ping}ms", foreground="green"))
                else:
                    self.after(0, lambda: self.status_label.config(
                        text=f"连接失败: HTTP {response.status_code}", foreground="red"))
            except Exception as e:
                logging.error(f"代理测试失败: {e}")
                self.after(0, lambda: self.status_label.config(
                    text=f"连接失败: {str(e)}", foreground="red"))
        
        import threading
        threading.Thread(target=test_thread, daemon=True).start()
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 代理启用状态
            self.proxy_enabled_var.set(self.settings_manager.get("proxy.enabled", False))
            
            # 服务器设置
            self.proxy_type_var.set(self.settings_manager.get("proxy.type", "http"))
            self.proxy_host_var.set(self.settings_manager.get("proxy.host", ""))
            self.proxy_port_var.set(self.settings_manager.get("proxy.port", ""))
            
            # 认证设置
            self.use_auth_var.set(self.settings_manager.get("proxy.use_auth", False))
            self.proxy_username_var.set(self.settings_manager.get("proxy.username", ""))
            self.proxy_password_var.set(self.settings_manager.get("proxy.password", ""))
            
            # 更新UI状态
            self._toggle_proxy_fields()
            self._toggle_auth_fields()
            
            logging.debug("代理设置加载成功")
        except Exception as e:
            logging.error(f"加载代理设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 代理启用状态
            self.settings_manager.set("proxy.enabled", self.proxy_enabled_var.get())
            
            # 服务器设置
            self.settings_manager.set("proxy.type", self.proxy_type_var.get())
            self.settings_manager.set("proxy.host", self.proxy_host_var.get())
            self.settings_manager.set("proxy.port", self.proxy_port_var.get())
            
            # 认证设置
            self.settings_manager.set("proxy.use_auth", self.use_auth_var.get())
            self.settings_manager.set("proxy.username", self.proxy_username_var.get())
            self.settings_manager.set("proxy.password", self.proxy_password_var.get())
            
            # 同时保存为proxy.json文件，用于下载和其他模块
            self._save_proxy_json()
            
            logging.debug("代理设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存代理设置时出错: {e}")
            return False
    
    def _save_proxy_json(self):
        """保存代理设置到proxy.json文件"""
        import json
        import os
        
        try:
            if not self.proxy_enabled_var.get():
                proxy_config = None
            else:
                # 构建代理URL
                proxy_type = self.proxy_type_var.get()
                host = self.proxy_host_var.get()
                port = self.proxy_port_var.get()
                
                proxy_url = f"{proxy_type}://"
                
                # 添加认证信息
                if self.use_auth_var.get():
                    username = self.proxy_username_var.get()
                    password = self.proxy_password_var.get()
                    if username and password:
                        proxy_url += f"{username}:{password}@"
                
                proxy_url += f"{host}:{port}"
                
                proxy_config = {
                    "http": proxy_url,
                    "https": proxy_url
                }
            
            # 获取配置路径
            config_path = self.settings_manager.config_path
            proxy_file = os.path.join(config_path, "proxy.json")
            
            # 保存到文件
            with open(proxy_file, 'w', encoding='utf-8') as f:
                json.dump(proxy_config, f, indent=4, ensure_ascii=False)
            
            logging.debug(f"代理配置已保存到 {proxy_file}")
        except Exception as e:
            logging.error(f"保存代理配置文件失败: {e}")
    
    def validate(self):
        """验证设置是否有效"""
        if not self.proxy_enabled_var.get():
            return True
        
        host = self.proxy_host_var.get()
        port = self.proxy_port_var.get()
        
        if not host:
            self.status_label.config(text="请输入代理服务器地址", foreground="red")
            return False
            
        if not port:
            self.status_label.config(text="请输入代理服务器端口", foreground="red")
            return False
            
        try:
            port_num = int(port)
            if port_num <= 0 or port_num > 65535:
                self.status_label.config(text="端口号必须在1-65535之间", foreground="red")
                return False
        except ValueError:
            self.status_label.config(text="端口号必须是数字", foreground="red")
            return False
            
        # 验证认证信息
        if self.use_auth_var.get():
            username = self.proxy_username_var.get()
            password = self.proxy_password_var.get()
            
            if not username:
                self.status_label.config(text="请输入用户名", foreground="red")
                return False
                
            if not password:
                self.status_label.config(text="请输入密码", foreground="red")
                return False
        
        return True 