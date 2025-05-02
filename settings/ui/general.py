"""
通用设置面板，提供语言、UI显示和行为设置
"""
import tkinter as tk
from tkinter import ttk
import logging

from settings.ui.base_panel import BaseSettingsPanel

class GeneralSettingsPanel(BaseSettingsPanel):
    """
    通用设置面板类，管理基本应用程序设置如语言、界面和行为
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化通用设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.language_var = tk.StringVar()
        self.enable_tray_var = tk.BooleanVar()
        self.start_minimized_var = tk.BooleanVar()
        self.auto_check_updates_var = tk.BooleanVar()
        self.confirm_exit_var = tk.BooleanVar()
        self.save_window_position_var = tk.BooleanVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置通用设置面板的用户界面"""
        # 语言设置
        language_section, language_content = self.create_section_frame("语言设置")
        
        # 语言选择
        languages = ["简体中文", "English", "日本語", "한국어"]
        language_frame, _, language_combo = self.create_labeled_combobox(
            language_content, "界面语言:", self.language_var, languages)
        language_frame.pack(fill=tk.X, pady=5)
        
        # UI行为设置
        ui_section, ui_content = self.create_section_frame("界面行为")
        
        # 托盘图标
        tray_frame = ttk.Frame(ui_content)
        tray_frame.pack(fill=tk.X, pady=5)
        
        tray_check = ttk.Checkbutton(tray_frame, text="启用系统托盘图标", 
                                    variable=self.enable_tray_var)
        tray_check.pack(side=tk.LEFT, padx=5)
        
        # 启动时最小化
        minimized_frame = ttk.Frame(ui_content)
        minimized_frame.pack(fill=tk.X, pady=5)
        
        minimized_check = ttk.Checkbutton(minimized_frame, text="启动时最小化到托盘", 
                                         variable=self.start_minimized_var)
        minimized_check.pack(side=tk.LEFT, padx=5)
        
        # 保存窗口位置
        position_frame = ttk.Frame(ui_content)
        position_frame.pack(fill=tk.X, pady=5)
        
        position_check = ttk.Checkbutton(position_frame, text="记住窗口位置和大小", 
                                        variable=self.save_window_position_var)
        position_check.pack(side=tk.LEFT, padx=5)
        
        # 应用程序行为
        app_section, app_content = self.create_section_frame("应用程序行为")
        
        # 自动检查更新
        update_frame = ttk.Frame(app_content)
        update_frame.pack(fill=tk.X, pady=5)
        
        update_check = ttk.Checkbutton(update_frame, text="启动时自动检查更新", 
                                      variable=self.auto_check_updates_var)
        update_check.pack(side=tk.LEFT, padx=5)
        
        # 退出确认
        exit_frame = ttk.Frame(app_content)
        exit_frame.pack(fill=tk.X, pady=5)
        
        exit_check = ttk.Checkbutton(exit_frame, text="退出时显示确认对话框", 
                                    variable=self.confirm_exit_var)
        exit_check.pack(side=tk.LEFT, padx=5)
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 语言设置
            self.language_var.set(self.settings_manager.get("interface.language", "简体中文"))
            
            # UI行为设置
            self.enable_tray_var.set(self.settings_manager.get("interface.enable_tray_icon", True))
            self.start_minimized_var.set(self.settings_manager.get("interface.start_minimized", False))
            self.save_window_position_var.set(self.settings_manager.get("interface.save_window_position", True))
            
            # 应用程序行为
            self.auto_check_updates_var.set(self.settings_manager.get("updates.auto_check", True))
            self.confirm_exit_var.set(self.settings_manager.get("interface.confirm_exit", True))
            
            logging.debug("通用设置加载成功")
        except Exception as e:
            logging.error(f"加载通用设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 语言设置
            self.settings_manager.set("interface.language", self.language_var.get())
            
            # UI行为设置
            self.settings_manager.set("interface.enable_tray_icon", self.enable_tray_var.get())
            self.settings_manager.set("interface.start_minimized", self.start_minimized_var.get())
            self.settings_manager.set("interface.save_window_position", self.save_window_position_var.get())
            
            # 应用程序行为
            self.settings_manager.set("updates.auto_check", self.auto_check_updates_var.get())
            self.settings_manager.set("interface.confirm_exit", self.confirm_exit_var.get())
            
            logging.debug("通用设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存通用设置时出错: {e}")
            return False 