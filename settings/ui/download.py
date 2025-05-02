"""
下载设置面板，用于管理下载配置和默认选项
"""
import tkinter as tk
from tkinter import ttk, filedialog
import logging
import os

from settings.ui.base_panel import BaseSettingsPanel

class DownloadSettingsPanel(BaseSettingsPanel):
    """
    下载设置面板类，管理下载配置和默认选项
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化下载设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.default_path_var = tk.StringVar()
        self.thread_count_var = tk.IntVar()
        self.auto_retry_var = tk.BooleanVar()
        self.retry_count_var = tk.IntVar()
        self.timeout_var = tk.IntVar()
        self.verify_ssl_var = tk.BooleanVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置下载设置面板的用户界面"""
        # 下载位置设置
        location_section, location_content = self.create_section_frame("下载位置")
        
        # 默认下载路径
        path_frame = ttk.Frame(location_content)
        path_frame.pack(fill=tk.X, pady=5)
        
        path_label = ttk.Label(path_frame, text="默认下载路径:")
        path_label.pack(side=tk.LEFT, padx=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.default_path_var, width=30)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(path_frame, text="浏览", command=self._browse_path)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # 下载参数设置
        params_section, params_content = self.create_section_frame("下载参数")
        
        # 线程数
        thread_frame = ttk.Frame(params_content)
        thread_frame.pack(fill=tk.X, pady=5)
        
        thread_label = ttk.Label(thread_frame, text="下载线程数:")
        thread_label.pack(side=tk.LEFT, padx=5)
        
        thread_spinbox = ttk.Spinbox(thread_frame, from_=1, to=16, width=5,
                                   textvariable=self.thread_count_var)
        thread_spinbox.pack(side=tk.LEFT, padx=5)
        
        thread_tip = ttk.Label(thread_frame, text="(推荐值: 4-8线程，较大值可能导致连接问题)",
                             foreground="gray", font=("", 9))
        thread_tip.pack(side=tk.LEFT, padx=5)
        
        # 超时设置
        timeout_frame = ttk.Frame(params_content)
        timeout_frame.pack(fill=tk.X, pady=5)
        
        timeout_label = ttk.Label(timeout_frame, text="连接超时:")
        timeout_label.pack(side=tk.LEFT, padx=5)
        
        timeout_spinbox = ttk.Spinbox(timeout_frame, from_=5, to=120, width=5,
                                    textvariable=self.timeout_var)
        timeout_spinbox.pack(side=tk.LEFT, padx=5)
        
        timeout_unit = ttk.Label(timeout_frame, text="秒")
        timeout_unit.pack(side=tk.LEFT)
        
        # 重试设置
        retry_section, retry_content = self.create_section_frame("重试设置")
        
        # 自动重试
        auto_retry_frame = ttk.Frame(retry_content)
        auto_retry_frame.pack(fill=tk.X, pady=5)
        
        auto_retry_check = ttk.Checkbutton(auto_retry_frame, text="下载失败后自动重试",
                                         variable=self.auto_retry_var,
                                         command=self._toggle_retry_count)
        auto_retry_check.pack(side=tk.LEFT, padx=5)
        
        # 重试次数
        retry_count_frame = ttk.Frame(retry_content)
        retry_count_frame.pack(fill=tk.X, pady=5)
        
        retry_count_label = ttk.Label(retry_count_frame, text="重试次数:")
        retry_count_label.pack(side=tk.LEFT, padx=5)
        
        self.retry_count_spinbox = ttk.Spinbox(retry_count_frame, from_=1, to=10, width=5,
                                          textvariable=self.retry_count_var)
        self.retry_count_spinbox.pack(side=tk.LEFT, padx=5)
        
        # 安全设置
        security_section, security_content = self.create_section_frame("安全设置")
        
        # 验证SSL证书
        ssl_frame = ttk.Frame(security_content)
        ssl_frame.pack(fill=tk.X, pady=5)
        
        ssl_check = ttk.Checkbutton(ssl_frame, text="验证SSL证书",
                                  variable=self.verify_ssl_var)
        ssl_check.pack(side=tk.LEFT, padx=5)
        
        ssl_tip = ttk.Label(ssl_frame, 
                          text="(禁用此选项可能导致安全风险，但可解决某些证书问题)",
                          foreground="gray", font=("", 9))
        ssl_tip.pack(side=tk.LEFT, padx=5)
    
    def _browse_path(self):
        """浏览选择默认下载路径"""
        path = filedialog.askdirectory(title="选择默认下载路径")
        if path:
            self.default_path_var.set(path)
    
    def _toggle_retry_count(self):
        """切换重试次数控件的启用状态"""
        if hasattr(self, 'retry_count_spinbox'):
            self.retry_count_spinbox.configure(
                state="normal" if self.auto_retry_var.get() else "disabled")
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 下载路径
            default_path = self.settings_manager.get("download.default_path", "")
            if not default_path:
                # 如果没有设置默认路径，使用用户下载目录
                default_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.default_path_var.set(default_path)
            
            # 线程数
            self.thread_count_var.set(self.settings_manager.get("download.thread_count", 4))
            
            # 重试设置
            self.auto_retry_var.set(self.settings_manager.get("download.auto_retry", True))
            self.retry_count_var.set(self.settings_manager.get("download.retry_count", 3))
            
            # 超时设置
            self.timeout_var.set(self.settings_manager.get("download.timeout", 30))
            
            # 安全设置
            self.verify_ssl_var.set(self.settings_manager.get("download.verify_ssl", True))
            
            # 更新UI状态
            self._toggle_retry_count()
            
            logging.debug("下载设置加载成功")
        except Exception as e:
            logging.error(f"加载下载设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 下载路径
            self.settings_manager.set("download.default_path", self.default_path_var.get())
            
            # 线程数
            self.settings_manager.set("download.thread_count", self.thread_count_var.get())
            
            # 重试设置
            self.settings_manager.set("download.auto_retry", self.auto_retry_var.get())
            self.settings_manager.set("download.retry_count", self.retry_count_var.get())
            
            # 超时设置
            self.settings_manager.set("download.timeout", self.timeout_var.get())
            
            # 安全设置
            self.settings_manager.set("download.verify_ssl", self.verify_ssl_var.get())
            
            # 保存最近的下载目录到专用文件，以便主程序加载
            self._save_last_download_path()
            
            logging.debug("下载设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存下载设置时出错: {e}")
            return False
    
    def _save_last_download_path(self):
        """保存最近的下载路径到专用文件"""
        try:
            import json
            import os
            
            # 获取配置路径
            config_path = self.settings_manager.config_path
            path_file = os.path.join(config_path, "last_download.json")
            
            # 保存到文件
            with open(path_file, 'w', encoding='utf-8') as f:
                json.dump({"last_dir": self.default_path_var.get()}, f, indent=4, ensure_ascii=False)
            
            logging.debug(f"最近下载路径已保存到 {path_file}")
        except Exception as e:
            logging.error(f"保存最近下载路径失败: {e}")
    
    def validate(self):
        """验证设置是否有效"""
        # 检查下载路径
        path = self.default_path_var.get()
        if not path:
            # 如果路径为空，自动设置为用户下载目录
            default_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.default_path_var.set(default_path)
            return True
        
        # 如果路径不存在，询问是否创建
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
                logging.info(f"已创建下载目录: {path}")
                return True
            except Exception as e:
                logging.error(f"创建下载目录失败: {e}")
                return False
        
        return True 