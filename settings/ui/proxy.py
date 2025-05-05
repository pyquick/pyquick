"""
代理设置面板，用于管理网络代理配置
"""
import tkinter as tk
from tkinter import ttk
import logging

from settings.ui.base_panel import BaseSettingsPanel
from settings.proxy_settings import ProxySettings

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
        try:
            if not parent or not settings_manager:
                raise ValueError("parent和settings_manager参数不能为None")
                
            # 首先调用父类初始化方法
            super().__init__(parent, settings_manager, theme_manager)
            
            # 初始化代理设置实例 - 修复：传递self.main_container作为父级
            self.proxy_settings = ProxySettings(self.main_container, settings_manager)
            
            # 初始化UI
            self.setup_ui()
            # 加载设置
            self.load_settings()
            
        except Exception as e:
            logging.error(f"初始化ProxySettingsPanel失败: {str(e)}")
            raise
    
    def setup_ui(self):
        """设置代理设置面板的用户界面"""
        # ProxySettings 的 frame 已经以 self.main_container 为父级创建，
        
        self.proxy_settings.get_frame().pack(fill=tk.BOTH, expand=True)
        
        # 初始化UI状态
        self.proxy_settings._toggle_proxy_settings()
        self.proxy_settings._toggle_auth_fields()
    
    def _test_connection(self):
        """测试代理连接"""
        # 使用proxy_settings的测试功能
    
        self.proxy_settings._test_proxy()
    
    def load_settings(self):
        """从设置管理器加载设置"""
        self.proxy_settings._load_proxy_settings()
    
    def save_settings(self):
        """保存设置到设置管理器"""
        return self.proxy_settings.save_settings()
    
    def validate(self):
        """验证设置是否有效"""
        # 仅在启用代理时验证代理设置
        if not self.proxy_settings.proxy_enabled_var.get():
            return True
        return self.proxy_settings._validate_settings()
