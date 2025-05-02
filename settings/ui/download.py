"""
下载设置面板，管理下载路径、并发数和超时等配置
"""
import tkinter as tk
from tkinter import ttk, filedialog
import os
import logging

from settings.ui.base_panel import BaseSettingsPanel

class DownloadSettingsPanel(BaseSettingsPanel):
    """
    下载设置面板类，管理下载相关配置项
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
        self.download_path_var = tk.StringVar()
        self.max_threads_var = tk.IntVar()
        self.timeout_var = tk.IntVar()
        self.auto_retry_var = tk.BooleanVar()
        self.retry_count_var = tk.IntVar()
        self.auto_unzip_var = tk.BooleanVar()
        self.keep_archive_var = tk.BooleanVar()
        self.auto_checksum_var = tk.BooleanVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置下载设置面板的用户界面"""
        # 下载路径设置
        path_section, path_content = self.create_section_frame("下载路径设置")
        
        # 下载路径选择
        path_frame = ttk.Frame(path_content)
        path_frame.pack(fill=tk.X, pady=5)
        
        path_label = ttk.Label(path_frame, text="下载保存路径:")
        path_label.pack(side=tk.LEFT, padx=5)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var)
        path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(path_frame, text="浏览...", 
                                  command=self._browse_download_path)
        browse_button.pack(side=tk.LEFT, padx=5)
        
        # 自动解压选项
        unzip_frame = ttk.Frame(path_content)
        unzip_frame.pack(fill=tk.X, pady=5)
        
        unzip_check = ttk.Checkbutton(unzip_frame, text="下载完成后自动解压缩文件", 
                                     variable=self.auto_unzip_var)
        unzip_check.pack(side=tk.LEFT, padx=5)
        
        # 保留压缩包选项
        keep_frame = ttk.Frame(path_content)
        keep_frame.pack(fill=tk.X, pady=5)
        
        keep_check = ttk.Checkbutton(keep_frame, text="解压后保留原始压缩包", 
                                    variable=self.keep_archive_var)
        keep_check.pack(side=tk.LEFT, padx=5)
        
        # 连接设置
        connection_section, connection_content = self.create_section_frame("连接设置")
        
        # 最大线程数
        threads_frame, _, threads_spinbox = self.create_labeled_spinbox(
            connection_content, "最大下载线程数:", self.max_threads_var, from_=1, to=32)
        threads_frame.pack(fill=tk.X, pady=5)
        
        # 超时设置
        timeout_frame, _, timeout_spinbox = self.create_labeled_spinbox(
            connection_content, "连接超时(秒):", self.timeout_var, from_=5, to=300)
        timeout_frame.pack(fill=tk.X, pady=5)
        
        # 自动重试
        retry_frame = ttk.Frame(connection_content)
        retry_frame.pack(fill=tk.X, pady=5)
        
        retry_check = ttk.Checkbutton(retry_frame, text="下载失败时自动重试", 
                                     variable=self.auto_retry_var,
                                     command=self._toggle_retry_count)
        retry_check.pack(side=tk.LEFT, padx=5)
        
        retry_label = ttk.Label(retry_frame, text="重试次数:")
        retry_label.pack(side=tk.LEFT, padx=(15, 5))
        
        retry_spinbox = ttk.Spinbox(retry_frame, textvariable=self.retry_count_var, 
                                   from_=1, to=10, width=5)
        retry_spinbox.pack(side=tk.LEFT)
        
        # 安全设置
        security_section, security_content = self.create_section_frame("安全设置")
        
        # 校验和验证
        checksum_frame = ttk.Frame(security_content)
        checksum_frame.pack(fill=tk.X, pady=5)
        
        checksum_check = ttk.Checkbutton(checksum_frame, text="下载完成后自动验证文件校验和", 
                                        variable=self.auto_checksum_var)
        checksum_check.pack(side=tk.LEFT, padx=5)
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 下载路径设置
            default_download_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_path_var.set(self.settings_manager.get("download.path", default_download_path))
            self.auto_unzip_var.set(self.settings_manager.get("download.auto_unzip", True))
            self.keep_archive_var.set(self.settings_manager.get("download.keep_archive", True))
            
            # 连接设置
            self.max_threads_var.set(self.settings_manager.get("download.max_threads", 4))
            self.timeout_var.set(self.settings_manager.get("download.timeout", 30))
            self.auto_retry_var.set(self.settings_manager.get("download.auto_retry", True))
            self.retry_count_var.set(self.settings_manager.get("download.retry_count", 3))
            
            # 安全设置
            self.auto_checksum_var.set(self.settings_manager.get("download.auto_checksum", True))
            
            # 更新UI状态
            self._toggle_retry_count()
            
            logging.debug("下载设置加载成功")
        except Exception as e:
            logging.error(f"加载下载设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 验证下载路径
            download_path = self.download_path_var.get().strip()
            if not download_path:
                logging.error("下载路径不能为空")
                return False
                
            # 确保下载目录存在
            if not os.path.exists(download_path):
                try:
                    os.makedirs(download_path, exist_ok=True)
                    logging.info(f"创建下载目录: {download_path}")
                except Exception as e:
                    logging.error(f"无法创建下载目录: {e}")
                    return False
            
            # 下载路径设置
            self.settings_manager.set("download.path", download_path)
            self.settings_manager.set("download.auto_unzip", self.auto_unzip_var.get())
            self.settings_manager.set("download.keep_archive", self.keep_archive_var.get())
            
            # 连接设置
            self.settings_manager.set("download.max_threads", self.max_threads_var.get())
            self.settings_manager.set("download.timeout", self.timeout_var.get())
            self.settings_manager.set("download.auto_retry", self.auto_retry_var.get())
            self.settings_manager.set("download.retry_count", self.retry_count_var.get())
            
            # 安全设置
            self.settings_manager.set("download.auto_checksum", self.auto_checksum_var.get())
            
            logging.debug("下载设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存下载设置时出错: {e}")
            return False
    
    def _browse_download_path(self):
        """打开文件对话框选择下载路径"""
        current_path = self.download_path_var.get()
        if not current_path or not os.path.exists(current_path):
            current_path = os.path.expanduser("~")
            
        new_path = filedialog.askdirectory(initialdir=current_path,
                                          title="选择下载文件保存位置")
        if new_path:
            self.download_path_var.set(new_path)
            logging.debug(f"已选择下载路径: {new_path}")
    
    def _toggle_retry_count(self):
        """根据自动重试选项启用或禁用重试次数设置"""
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for frame in child.winfo_children():
                    if isinstance(frame, ttk.Frame):
                        for widget in frame.winfo_children():
                            if isinstance(widget, ttk.Spinbox) and widget.winfo_name() == self.retry_count_var._name:
                                if self.auto_retry_var.get():
                                    widget.configure(state="normal")
                                else:
                                    widget.configure(state="disabled") 