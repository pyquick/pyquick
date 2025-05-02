"""
代理设置面板，提供HTTP/HTTPS/SOCKS代理配置功能
"""
import tkinter as tk
from tkinter import ttk
import logging
import re

from settings.ui.base_panel import BaseSettingsPanel

class ProxySettingsPanel(BaseSettingsPanel):
    """
    代理设置面板类，管理HTTP/HTTPS/SOCKS代理配置
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
        self.enable_proxy_var = tk.BooleanVar()
        self.proxy_type_var = tk.StringVar()
        self.proxy_host_var = tk.StringVar()
        self.proxy_port_var = tk.StringVar()
        self.proxy_auth_var = tk.BooleanVar()
        self.proxy_username_var = tk.StringVar()
        self.proxy_password_var = tk.StringVar()
        self.no_proxy_var = tk.StringVar()
        self.enable_system_proxy_var = tk.BooleanVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置代理设置面板的用户界面"""
        # 代理开关
        enable_frame = ttk.Frame(self.main_container)
        enable_frame.pack(fill=tk.X, pady=10)
        
        enable_proxy_check = ttk.Checkbutton(enable_frame, text="启用代理服务器", 
                                            variable=self.enable_proxy_var,
                                            command=self._toggle_proxy_settings)
        enable_proxy_check.pack(side=tk.LEFT, padx=5)
        
        # 系统代理
        system_proxy_check = ttk.Checkbutton(enable_frame, text="使用系统代理设置", 
                                           variable=self.enable_system_proxy_var,
                                           command=self._toggle_proxy_settings)
        system_proxy_check.pack(side=tk.LEFT, padx=30)
        
        # 代理设置区域
        self.proxy_container = ttk.LabelFrame(self.main_container, text="代理服务器设置")
        self.proxy_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 代理类型
        type_frame = ttk.Frame(self.proxy_container)
        type_frame.pack(fill=tk.X, pady=5)
        
        type_label = ttk.Label(type_frame, text="代理类型:")
        type_label.pack(side=tk.LEFT, padx=5)
        
        proxy_types = ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]
        type_combo = ttk.Combobox(type_frame, textvariable=self.proxy_type_var, 
                                 values=proxy_types, state="readonly", width=10)
        type_combo.pack(side=tk.LEFT, padx=5)
        
        # 代理服务器
        server_frame = ttk.Frame(self.proxy_container)
        server_frame.pack(fill=tk.X, pady=5)
        
        host_label = ttk.Label(server_frame, text="服务器地址:")
        host_label.pack(side=tk.LEFT, padx=5)
        
        host_entry = ttk.Entry(server_frame, textvariable=self.proxy_host_var, width=20)
        host_entry.pack(side=tk.LEFT, padx=5)
        
        port_label = ttk.Label(server_frame, text="端口:")
        port_label.pack(side=tk.LEFT, padx=5)
        
        port_entry = ttk.Entry(server_frame, textvariable=self.proxy_port_var, width=6)
        port_entry.pack(side=tk.LEFT, padx=5)
        
        # 代理认证
        auth_frame = ttk.Frame(self.proxy_container)
        auth_frame.pack(fill=tk.X, pady=5)
        
        auth_check = ttk.Checkbutton(auth_frame, text="需要身份验证", 
                                    variable=self.proxy_auth_var,
                                    command=self._toggle_auth_fields)
        auth_check.pack(side=tk.LEFT, padx=5)
        
        # 认证用户名密码
        self.auth_container = ttk.Frame(self.proxy_container)
        self.auth_container.pack(fill=tk.X, pady=5)
        
        username_frame = ttk.Frame(self.auth_container)
        username_frame.pack(fill=tk.X, pady=5)
        
        username_label = ttk.Label(username_frame, text="用户名:")
        username_label.pack(side=tk.LEFT, padx=5)
        
        username_entry = ttk.Entry(username_frame, textvariable=self.proxy_username_var, width=20)
        username_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        password_frame = ttk.Frame(self.auth_container)
        password_frame.pack(fill=tk.X, pady=5)
        
        password_label = ttk.Label(password_frame, text="密码:")
        password_label.pack(side=tk.LEFT, padx=5)
        
        password_entry = ttk.Entry(password_frame, textvariable=self.proxy_password_var, 
                                  show="*", width=20)
        password_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 不使用代理的地址
        no_proxy_section, no_proxy_content = self.create_section_frame("不使用代理的地址")
        
        no_proxy_label = ttk.Label(no_proxy_content, 
                                  text="以下地址将不使用代理(使用逗号分隔，可使用通配符*):")
        no_proxy_label.pack(anchor=tk.W, padx=5, pady=5)
        
        no_proxy_entry = ttk.Entry(no_proxy_content, textvariable=self.no_proxy_var)
        no_proxy_entry.pack(fill=tk.X, padx=5, pady=5)
        
        example_label = ttk.Label(no_proxy_content, 
                                 text="示例: localhost, 127.0.0.1, *.example.com", 
                                 foreground="gray")
        example_label.pack(anchor=tk.W, padx=5)
        
        # 测试连接
        test_frame = ttk.Frame(self.main_container)
        test_frame.pack(fill=tk.X, pady=10)
        
        test_button = ttk.Button(test_frame, text="测试代理连接", 
                                command=self._test_proxy_connection)
        test_button.pack(side=tk.RIGHT, padx=5)
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 代理开关
            self.enable_proxy_var.set(self.settings_manager.get("proxy.enable", False))
            self.enable_system_proxy_var.set(self.settings_manager.get("proxy.use_system", False))
            
            # 代理设置
            self.proxy_type_var.set(self.settings_manager.get("proxy.type", "HTTP"))
            self.proxy_host_var.set(self.settings_manager.get("proxy.host", ""))
            self.proxy_port_var.set(str(self.settings_manager.get("proxy.port", "")))
            
            # 认证设置
            self.proxy_auth_var.set(self.settings_manager.get("proxy.auth.enable", False))
            self.proxy_username_var.set(self.settings_manager.get("proxy.auth.username", ""))
            self.proxy_password_var.set(self.settings_manager.get("proxy.auth.password", ""))
            
            # 不使用代理的地址
            self.no_proxy_var.set(self.settings_manager.get("proxy.no_proxy", "localhost,127.0.0.1"))
            
            # 更新UI状态
            self._toggle_proxy_settings()
            self._toggle_auth_fields()
            
            logging.debug("代理设置加载成功")
        except Exception as e:
            logging.error(f"加载代理设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 验证代理端口
            if self.enable_proxy_var.get() and not self.enable_system_proxy_var.get():
                if not self._validate_proxy_settings():
                    return False
            
            # 代理开关
            self.settings_manager.set("proxy.enable", self.enable_proxy_var.get())
            self.settings_manager.set("proxy.use_system", self.enable_system_proxy_var.get())
            
            # 代理设置
            self.settings_manager.set("proxy.type", self.proxy_type_var.get())
            self.settings_manager.set("proxy.host", self.proxy_host_var.get())
            
            # 尝试转换端口为整数
            port_str = self.proxy_port_var.get().strip()
            port = 0
            if port_str:
                try:
                    port = int(port_str)
                except ValueError:
                    port = 0
            self.settings_manager.set("proxy.port", port)
            
            # 认证设置
            self.settings_manager.set("proxy.auth.enable", self.proxy_auth_var.get())
            self.settings_manager.set("proxy.auth.username", self.proxy_username_var.get())
            self.settings_manager.set("proxy.auth.password", self.proxy_password_var.get())
            
            # 不使用代理的地址
            self.settings_manager.set("proxy.no_proxy", self.no_proxy_var.get())
            
            logging.debug("代理设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存代理设置时出错: {e}")
            return False
    
    def _toggle_proxy_settings(self):
        """根据代理开关状态，启用或禁用代理设置"""
        if self.enable_proxy_var.get():
            self.proxy_container.configure(state="normal")
            
            # 如果使用系统代理，禁用手动配置
            if self.enable_system_proxy_var.get():
                for child in self.proxy_container.winfo_children():
                    if isinstance(child, (ttk.Frame, ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                        child.configure(state="disabled")
            else:
                for child in self.proxy_container.winfo_children():
                    if isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                        for widget in child.winfo_children():
                            if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                                widget.configure(state="normal")
                    elif isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                        child.configure(state="normal")
                        
                # 更新认证字段状态
                self._toggle_auth_fields()
        else:
            # 禁用所有代理设置
            for child in self.proxy_container.winfo_children():
                if isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                    for widget in child.winfo_children():
                        if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                            widget.configure(state="disabled")
                elif isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Checkbutton)):
                    child.configure(state="disabled")
    
    def _toggle_auth_fields(self):
        """根据认证复选框状态，启用或禁用认证字段"""
        if self.enable_proxy_var.get() and not self.enable_system_proxy_var.get():
            if self.proxy_auth_var.get():
                for frame in self.auth_container.winfo_children():
                    for widget in frame.winfo_children():
                        if isinstance(widget, ttk.Entry):
                            widget.configure(state="normal")
            else:
                for frame in self.auth_container.winfo_children():
                    for widget in frame.winfo_children():
                        if isinstance(widget, ttk.Entry):
                            widget.configure(state="disabled")
    
    def _validate_proxy_settings(self):
        """验证代理设置"""
        # 检查主机名
        host = self.proxy_host_var.get().strip()
        if not host:
            logging.error("代理服务器地址不能为空")
            return False
            
        # 检查端口号
        port = self.proxy_port_var.get().strip()
        if not port:
            logging.error("代理服务器端口不能为空")
            return False
            
        try:
            port_num = int(port)
            if port_num <= 0 or port_num > 65535:
                logging.error("代理服务器端口必须在1-65535之间")
                return False
        except ValueError:
            logging.error("代理服务器端口必须是有效的数字")
            return False
            
        # 检查认证
        if self.proxy_auth_var.get():
            username = self.proxy_username_var.get().strip()
            password = self.proxy_password_var.get()
            
            if not username:
                logging.error("代理认证用户名不能为空")
                return False
                
        return True
    
    def _test_proxy_connection(self):
        """测试代理连接"""
        import urllib.request
        import socket
        from tkinter import messagebox
        
        if not self.enable_proxy_var.get():
            messagebox.showinfo("代理测试", "请先启用代理服务器")
            return
            
        if self.enable_system_proxy_var.get():
            messagebox.showinfo("代理测试", "使用系统代理，无法在此测试")
            return
            
        if not self._validate_proxy_settings():
            messagebox.showerror("代理测试", "代理设置无效，请检查配置")
            return
            
        host = self.proxy_host_var.get().strip()
        port = int(self.proxy_port_var.get().strip())
        
        try:
            # 首先测试是否可以连接到代理服务器
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            logging.info(f"正在测试连接到代理服务器: {host}:{port}")
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result != 0:
                messagebox.showerror("代理测试", f"无法连接到代理服务器: {host}:{port}")
                return
                
            # 使用代理测试HTTP请求
            proxy_type = self.proxy_type_var.get().lower()
            proxy_handler = None
            
            if self.proxy_auth_var.get():
                username = self.proxy_username_var.get()
                password = self.proxy_password_var.get()
                auth = f"{username}:{password}@"
            else:
                auth = ""
                
            proxy_url = f"{proxy_type}://{auth}{host}:{port}"
            logging.info(f"使用代理URL: {proxy_url}")
            
            proxy_handler = urllib.request.ProxyHandler({
                'http': proxy_url,
                'https': proxy_url
            })
            
            opener = urllib.request.build_opener(proxy_handler)
            opener.addheaders = [('User-agent', 'Mozilla/5.0')]
            urllib.request.install_opener(opener)
            
            # 测试连接
            logging.info("正在通过代理测试连接...")
            response = urllib.request.urlopen("http://www.baidu.com", timeout=10)
            
            if response.getcode() == 200:
                messagebox.showinfo("代理测试", "代理服务器连接成功！")
            else:
                messagebox.showwarning("代理测试", f"代理服务器连接异常，响应码: {response.getcode()}")
                
        except Exception as e:
            logging.error(f"代理测试失败: {e}")
            messagebox.showerror("代理测试", f"代理测试失败: {str(e)}") 