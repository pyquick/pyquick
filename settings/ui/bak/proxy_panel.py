"""
代理设置面板模块

提供网络代理配置选项，支持HTTP和SOCKS代理
"""
import tkinter as tk
from tkinter import ttk
import logging
import re

from settings.ui.base_panel import BaseSettingsPanel

class ProxySettingsPanel(BaseSettingsPanel):
    """
    代理设置面板
    
    提供网络代理配置选项，包括：
    - 代理类型选择
    - 代理服务器地址
    - 代理端口
    - 身份验证信息
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        # 初始化变量
        self.use_proxy_var = tk.BooleanVar()
        self.proxy_type_var = tk.StringVar()
        self.proxy_host_var = tk.StringVar()
        self.proxy_port_var = tk.StringVar()
        self.proxy_username_var = tk.StringVar()
        self.proxy_password_var = tk.StringVar()
        self.bypass_localhost_var = tk.BooleanVar()
        self.bypass_list_var = tk.StringVar()
        
        # 调用父类初始化
        super().__init__(parent, settings_manager, theme_manager)
        
    def setup_ui(self):
        """设置用户界面"""
        # 代理使用开关
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=self.padx, pady=self.pady)
        
        proxy_switch = ttk.Checkbutton(top_frame, text="启用代理", 
                                     variable=self.use_proxy_var,
                                     command=self.toggle_proxy_settings)
        proxy_switch.pack(side=tk.LEFT)
        
        # 测试按钮
        test_button = ttk.Button(top_frame, text="测试代理", 
                               command=self.test_proxy)
        test_button.pack(side=tk.RIGHT)
        
        # 代理设置区域
        self.proxy_frame, proxy_content = self.create_section_frame("代理设置")
        
        # 代理类型
        proxy_type_frame = ttk.Frame(proxy_content)
        ttk.Label(proxy_type_frame, text="代理类型:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        proxy_types = ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]
        proxy_type_combobox = ttk.Combobox(proxy_type_frame, textvariable=self.proxy_type_var,
                                         values=proxy_types, state="readonly")
        proxy_type_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        proxy_type_frame.pack(fill=tk.X, pady=self.pady)
        
        # 服务器地址
        host_frame = ttk.Frame(proxy_content)
        ttk.Label(host_frame, text="服务器地址:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        host_entry = ttk.Entry(host_frame, textvariable=self.proxy_host_var)
        host_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        host_frame.pack(fill=tk.X, pady=self.pady)
        
        # 端口
        port_frame = ttk.Frame(proxy_content)
        ttk.Label(port_frame, text="端口:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        port_entry = ttk.Entry(port_frame, textvariable=self.proxy_port_var)
        port_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.add_tooltip(port_entry, "端口号范围：1-65535")
        port_frame.pack(fill=tk.X, pady=self.pady)
        
        # 认证信息
        auth_frame, auth_content = self.create_section_frame("认证信息")
        
        # 用户名
        username_frame = ttk.Frame(auth_content)
        ttk.Label(username_frame, text="用户名:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        username_entry = ttk.Entry(username_frame, textvariable=self.proxy_username_var)
        username_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        username_frame.pack(fill=tk.X, pady=self.pady)
        
        # 密码
        password_frame = ttk.Frame(auth_content)
        ttk.Label(password_frame, text="密码:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        password_entry = ttk.Entry(password_frame, textvariable=self.proxy_password_var, show="*")
        password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 显示/隐藏密码按钮
        self.show_password_var = tk.BooleanVar(value=False)
        
        def toggle_password_visibility():
            if self.show_password_var.get():
                password_entry.configure(show="")
            else:
                password_entry.configure(show="*")
        
        show_password_cb = ttk.Checkbutton(password_frame, text="显示", 
                                         variable=self.show_password_var,
                                         command=toggle_password_visibility)
        show_password_cb.pack(side=tk.LEFT, padx=(5, 0))
        password_frame.pack(fill=tk.X, pady=self.pady)
        
        # 高级设置
        advanced_frame, advanced_content = self.create_section_frame("高级设置")
        
        # 绕过代理
        bypass_frame = ttk.Frame(advanced_content)
        bypass_checkbox = ttk.Checkbutton(bypass_frame, text="绕过本地地址", 
                                        variable=self.bypass_localhost_var)
        bypass_checkbox.pack(side=tk.LEFT)
        bypass_frame.pack(fill=tk.X, pady=self.pady, anchor=tk.W)
        
        # 绕过列表
        bypass_list_frame = ttk.Frame(advanced_content)
        ttk.Label(bypass_list_frame, text="不使用代理的地址:", 
                 anchor=tk.W).pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        bypass_entry = ttk.Entry(bypass_list_frame, textvariable=self.bypass_list_var)
        bypass_entry.pack(side=tk.TOP, fill=tk.X)
        self.add_tooltip(bypass_entry, "多个地址使用逗号(,)分隔，支持通配符(*)，例如：*.example.com,192.168.1.*")
        
        bypass_list_frame.pack(fill=tk.X, pady=self.pady)
        
        # 初始化控件状态
        self.toggle_proxy_settings()
        
    def toggle_proxy_settings(self):
        """根据是否启用代理切换相关设置的状态"""
        state = "normal" if self.use_proxy_var.get() else "disabled"
        
        # 更新所有子控件的状态
        def update_state(widget):
            widget_class = widget.winfo_class()
            if widget_class in ('TEntry', 'TCombobox', 'TButton', 'TCheckbutton'):
                if widget_class == 'TCheckbutton':
                    widget.configure(state=state)
                else:
                    widget.configure(state=state)
            
            for child in widget.winfo_children():
                update_state(child)
        
        # 更新代理设置区域的状态
        for frame in [self.proxy_frame]:
            for child in frame.winfo_children():
                update_state(child)
                
    def test_proxy(self):
        """测试当前代理设置"""
        if not self.use_proxy_var.get():
            self.show_message("请先启用代理设置")
            return
            
        # 验证代理设置
        if not self.validate_proxy_settings():
            return
            
        # 收集代理信息
        proxy_type = self.proxy_type_var.get().lower()
        proxy_host = self.proxy_host_var.get().strip()
        proxy_port = self.proxy_port_var.get().strip()
        
        proxy_url = f"{proxy_type}://"
        
        # 添加认证信息
        username = self.proxy_username_var.get().strip()
        password = self.proxy_password_var.get()
        if username:
            proxy_url += f"{username}:{password}@"
            
        proxy_url += f"{proxy_host}:{proxy_port}"
        
        # 测试连接
        try:
            import urllib.request
            import socket
            
            # 设置超时时间
            timeout = 10
            socket.setdefaulttimeout(timeout)
            
            # 设置代理处理器
            proxy_handler = urllib.request.ProxyHandler({
                "http": proxy_url if proxy_type in ["http", "socks4", "socks5"] else None,
                "https": proxy_url if proxy_type in ["https", "socks4", "socks5"] else None
            })
            
            # 创建自定义opener
            opener = urllib.request.build_opener(proxy_handler)
            
            # 测试网站 (使用百度，因为确保能够访问)
            test_url = "http://www.baidu.com"
            
            response = opener.open(test_url, timeout=timeout)
            if response.getcode() == 200:
                self.show_message("代理测试成功", "连接成功", "info")
            else:
                self.show_message("代理测试失败", f"HTTP错误: {response.getcode()}", "error")
                
        except Exception as e:
            self.show_message("代理测试失败", str(e), "error")
            logging.error(f"代理测试失败: {e}")
            
    def validate_proxy_settings(self):
        """验证代理设置是否有效"""
        # 检查代理类型
        if not self.proxy_type_var.get():
            self.show_message("代理类型不能为空")
            return False
            
        # 检查主机地址
        host = self.proxy_host_var.get().strip()
        if not host:
            self.show_message("代理服务器地址不能为空")
            return False
            
        # 检查端口
        port = self.proxy_port_var.get().strip()
        if not port:
            self.show_message("代理端口不能为空")
            return False
            
        # 验证端口是否为数字且在有效范围内
        try:
            port_num = int(port)
            if not (1 <= port_num <= 65535):
                self.show_message("端口号必须在1-65535范围内")
                return False
        except ValueError:
            self.show_message("端口号必须为数字")
            return False
            
        return True
        
    def show_message(self, message, detail=None, message_type="warning"):
        """显示消息对话框"""
        try:
            from tkinter import messagebox
            
            if message_type == "info":
                if detail:
                    messagebox.showinfo(message, detail)
                else:
                    messagebox.showinfo("提示", message)
            elif message_type == "error":
                if detail:
                    messagebox.showerror(message, detail)
                else:
                    messagebox.showerror("错误", message)
            else:  # warning
                if detail:
                    messagebox.showwarning(message, detail)
                else:
                    messagebox.showwarning("警告", message)
        except Exception as e:
            logging.error(f"显示消息对话框时出错: {e}")
            
    def get_proxy_url(self):
        """获取当前代理URL"""
        if not self.use_proxy_var.get():
            return None
            
        proxy_type = self.proxy_type_var.get().lower()
        proxy_host = self.proxy_host_var.get().strip()
        proxy_port = self.proxy_port_var.get().strip()
        
        if not proxy_type or not proxy_host or not proxy_port:
            return None
            
        proxy_url = f"{proxy_type}://"
        
        # 添加认证信息
        username = self.proxy_username_var.get().strip()
        password = self.proxy_password_var.get()
        if username:
            proxy_url += f"{username}:{password}@"
            
        proxy_url += f"{proxy_host}:{proxy_port}"
        
        return proxy_url
        
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 加载代理启用状态
            self.use_proxy_var.set(self.settings_manager.get("network.proxy.enabled", False))
            
            # 加载代理设置
            self.proxy_type_var.set(self.settings_manager.get("network.proxy.type", "HTTP"))
            self.proxy_host_var.set(self.settings_manager.get("network.proxy.host", ""))
            self.proxy_port_var.set(self.settings_manager.get("network.proxy.port", ""))
            
            # 加载认证信息
            self.proxy_username_var.set(self.settings_manager.get("network.proxy.username", ""))
            self.proxy_password_var.set(self.settings_manager.get("network.proxy.password", ""))
            
            # 加载高级设置
            self.bypass_localhost_var.set(self.settings_manager.get("network.proxy.bypass_localhost", True))
            self.bypass_list_var.set(self.settings_manager.get("network.proxy.bypass_list", "localhost,127.0.0.1"))
            
            # 更新控件状态
            self.toggle_proxy_settings()
            
        except Exception as e:
            logging.error(f"加载代理设置时出错: {e}")
            
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 保存代理启用状态
            self.settings_manager.set("network.proxy.enabled", self.use_proxy_var.get())
            
            # 如果启用了代理，验证设置是否有效
            if self.use_proxy_var.get() and not self.validate_proxy_settings():
                return False
                
            # 保存代理设置
            self.settings_manager.set("network.proxy.type", self.proxy_type_var.get())
            self.settings_manager.set("network.proxy.host", self.proxy_host_var.get().strip())
            self.settings_manager.set("network.proxy.port", self.proxy_port_var.get().strip())
            
            # 保存认证信息
            self.settings_manager.set("network.proxy.username", self.proxy_username_var.get().strip())
            self.settings_manager.set("network.proxy.password", self.proxy_password_var.get())
            
            # 保存高级设置
            self.settings_manager.set("network.proxy.bypass_localhost", self.bypass_localhost_var.get())
            self.settings_manager.set("network.proxy.bypass_list", self.bypass_list_var.get().strip())
            
            # 应用系统代理设置
            self.apply_system_proxy_settings()
            
            return True
        except Exception as e:
            logging.error(f"保存代理设置时出错: {e}")
            return False
            
    def apply_system_proxy_settings(self):
        """应用代理设置到系统环境变量"""
        try:
            import os
            
            if self.use_proxy_var.get():
                proxy_url = self.get_proxy_url()
                if proxy_url:
                    # 设置HTTP代理
                    os.environ["HTTP_PROXY"] = proxy_url
                    os.environ["http_proxy"] = proxy_url
                    
                    # 设置HTTPS代理
                    os.environ["HTTPS_PROXY"] = proxy_url
                    os.environ["https_proxy"] = proxy_url
                    
                    # 设置不使用代理的地址
                    no_proxy = []
                    if self.bypass_localhost_var.get():
                        no_proxy.extend(["localhost", "127.0.0.1", "::1"])
                        
                    bypass_list = self.bypass_list_var.get().strip()
                    if bypass_list:
                        no_proxy.extend([item.strip() for item in bypass_list.split(",")])
                        
                    if no_proxy:
                        os.environ["NO_PROXY"] = ",".join(no_proxy)
                        os.environ["no_proxy"] = ",".join(no_proxy)
            else:
                # 清除代理设置
                for var in ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy", "NO_PROXY", "no_proxy"]:
                    if var in os.environ:
                        del os.environ[var]
                        
            logging.info("已应用代理设置到系统环境变量")
            
        except Exception as e:
            logging.error(f"应用代理设置到系统环境变量时出错: {e}") 