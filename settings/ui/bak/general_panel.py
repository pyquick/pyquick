"""
通用设置面板模块

提供应用程序的基本设置，如界面语言、主题、自动更新等
"""
import tkinter as tk
from tkinter import ttk
import logging
import os

from settings.ui.base_panel import BaseSettingsPanel

class GeneralSettingsPanel(BaseSettingsPanel):
    """
    通用设置面板
    
    提供应用程序的基本设置，包括：
    - 界面语言
    - 界面主题
    - 自动更新选项
    - 启动选项
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        # 初始化变量
        self.language_var = tk.StringVar()
        self.theme_var = tk.StringVar()
        self.check_updates_var = tk.BooleanVar()
        self.auto_install_updates_var = tk.BooleanVar()
        self.startup_check_var = tk.BooleanVar()
        self.show_welcome_var = tk.BooleanVar()
        self.debug_mode_var = tk.BooleanVar()
        
        # 调用父类初始化
        super().__init__(parent, settings_manager, theme_manager)
        
    def setup_ui(self):
        """设置用户界面"""
        # 界面设置区域
        ui_frame, ui_content = self.create_section_frame("界面设置")
        
        # 语言选择
        language_combobox = ttk.Combobox(ui_content, textvariable=self.language_var, state="readonly")
        language_combobox["values"] = ["简体中文", "English"]
        self.create_setting_row(ui_content, "界面语言:", language_combobox, 
                              "选择应用程序的界面语言，更改后需要重启应用")
        
        # 主题选择
        theme_combobox = ttk.Combobox(ui_content, textvariable=self.theme_var, state="readonly")
        if self.theme_manager:
            theme_combobox["values"] = self.theme_manager.get_available_themes()
        else:
            theme_combobox["values"] = ["默认主题", "暗色主题"]
        
        theme_frame = self.create_setting_row(ui_content, "界面主题:", theme_combobox, 
                                           "选择应用程序的界面主题")
        
        # 添加主题预览按钮
        preview_button = ttk.Button(theme_frame, text="预览", width=8,
                                  command=self.preview_theme)
        preview_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # 更新设置区域
        update_frame, update_content = self.create_section_frame("更新设置")
        
        # 自动检查更新选项
        check_updates_cb = ttk.Checkbutton(update_content, text="自动检查更新", 
                                         variable=self.check_updates_var,
                                         command=self.toggle_auto_update)
        self.create_setting_row(update_content, "", check_updates_cb, 
                              "应用程序启动时自动检查是否有新版本")
        
        # 自动安装更新选项
        auto_install_cb = ttk.Checkbutton(update_content, text="自动安装更新", 
                                        variable=self.auto_install_updates_var)
        self.auto_install_row = self.create_setting_row(update_content, "", auto_install_cb, 
                                                     "发现新版本时自动下载并安装")
        
        # 启动设置区域
        startup_frame, startup_content = self.create_section_frame("启动设置")
        
        # 启动检查选项
        startup_check_cb = ttk.Checkbutton(startup_content, text="启动时检查Python环境", 
                                         variable=self.startup_check_var)
        self.create_setting_row(startup_content, "", startup_check_cb, 
                              "应用程序启动时检查Python环境是否正确配置")
        
        # 显示欢迎页面选项
        welcome_cb = ttk.Checkbutton(startup_content, text="启动时显示欢迎页面", 
                                   variable=self.show_welcome_var)
        self.create_setting_row(startup_content, "", welcome_cb, 
                              "应用程序启动时显示欢迎页面")
        
        # 高级设置区域
        advanced_frame, advanced_content = self.create_section_frame("高级设置")
        
        # 调试模式选项
        debug_cb = ttk.Checkbutton(advanced_content, text="启用调试模式", 
                                 variable=self.debug_mode_var)
        self.create_setting_row(advanced_content, "", debug_cb, 
                              "启用调试模式，将会记录更详细的日志信息")
        
        # 日志目录按钮
        log_frame = ttk.Frame(advanced_content)
        log_frame.pack(fill=tk.X, pady=self.pady)
        
        ttk.Label(log_frame, text="日志文件位置:", width=15, anchor=tk.E).pack(side=tk.LEFT)
        
        log_path_var = tk.StringVar(value=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "log"))
        log_entry = ttk.Entry(log_frame, textvariable=log_path_var, state="readonly")
        log_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        open_log_button = ttk.Button(log_frame, text="打开", width=8,
                                    command=self.open_log_directory)
        open_log_button.pack(side=tk.LEFT, padx=(5, 0))
        
    def toggle_auto_update(self):
        """根据自动检查更新状态切换自动安装更新选项的状态"""
        if self.check_updates_var.get():
            self.auto_install_updates_var.configure(state=tk.NORMAL)
        else:
            self.auto_install_updates_var.set(False)
            self.auto_install_updates_var.configure(state=tk.DISABLED)
            
    def preview_theme(self):
        """预览所选主题"""
        if not self.theme_manager:
            logging.warning("主题管理器未初始化，无法预览主题")
            return
            
        try:
            selected_theme = self.theme_var.get()
            if not selected_theme:
                return
                
            # 保存当前主题
            current_theme = self.theme_manager.get_current_theme()
            
            # 临时应用所选主题
            self.theme_manager.set_current_theme(selected_theme)
            self.theme_manager.apply_theme(self.parent)
            
            # 创建预览窗口
            preview = tk.Toplevel(self)
            preview.title(f"主题预览: {selected_theme}")
            preview.geometry("400x300")
            preview.transient(self.parent)
            preview.grab_set()
            
            # 应用主题到预览窗口
            self.theme_manager.apply_theme(preview)
            
            # 添加一些控件以展示主题效果
            frame = ttk.Frame(preview, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text="主题预览", font=("", 14, "bold")).pack(pady=10)
            
            # 按钮
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(fill=tk.X, pady=10)
            
            ttk.Button(buttons_frame, text="标准按钮").pack(side=tk.LEFT, padx=5)
            ttk.Button(buttons_frame, text="禁用按钮", state="disabled").pack(side=tk.LEFT, padx=5)
            
            # 输入框
            entry_frame = ttk.Frame(frame)
            entry_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(entry_frame, text="输入框:").pack(side=tk.LEFT, padx=5)
            ttk.Entry(entry_frame).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            
            # 复选框
            checkbox_frame = ttk.Frame(frame)
            checkbox_frame.pack(fill=tk.X, pady=10)
            
            ttk.Checkbutton(checkbox_frame, text="复选框 1").pack(side=tk.LEFT, padx=5)
            ttk.Checkbutton(checkbox_frame, text="复选框 2").pack(side=tk.LEFT, padx=5)
            
            # 下拉菜单
            combo_frame = ttk.Frame(frame)
            combo_frame.pack(fill=tk.X, pady=10)
            
            ttk.Label(combo_frame, text="下拉菜单:").pack(side=tk.LEFT, padx=5)
            combo = ttk.Combobox(combo_frame, values=["选项 1", "选项 2", "选项 3"])
            combo.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
            combo.current(0)
            
            # 关闭按钮，恢复原主题
            def close_preview():
                self.theme_manager.set_current_theme(current_theme)
                self.theme_manager.apply_theme(self.parent)
                preview.destroy()
                
            ttk.Button(frame, text="关闭预览", command=close_preview).pack(pady=20)
            
            # 窗口关闭时恢复原主题
            preview.protocol("WM_DELETE_WINDOW", close_preview)
            
        except Exception as e:
            logging.error(f"预览主题时出错: {e}")
            
    def open_log_directory(self):
        """打开日志目录"""
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "log")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # 根据操作系统打开文件夹
            if os.name == 'nt':  # Windows
                os.startfile(log_dir)
            elif os.name == 'posix':  # macOS, Linux
                import subprocess
                
                if 'darwin' in os.sys.platform:  # macOS
                    subprocess.run(['open', log_dir])
                else:  # Linux
                    subprocess.run(['xdg-open', log_dir])
                    
        except Exception as e:
            logging.error(f"打开日志目录时出错: {e}")
            
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 加载界面设置
            self.language_var.set(self.settings_manager.get("interface.language", "简体中文"))
            
            # 加载主题设置
            if self.theme_manager:
                self.theme_var.set(self.theme_manager.get_current_theme())
            else:
                self.theme_var.set(self.settings_manager.get("interface.theme", "默认主题"))
                
            # 加载更新设置
            self.check_updates_var.set(self.settings_manager.get("updates.check_automatically", True))
            self.auto_install_updates_var.set(self.settings_manager.get("updates.install_automatically", False))
            
            # 更新自动安装更新选项的状态
            self.toggle_auto_update()
            
            # 加载启动设置
            self.startup_check_var.set(self.settings_manager.get("startup.check_environment", True))
            self.show_welcome_var.set(self.settings_manager.get("startup.show_welcome", True))
            
            # 加载高级设置
            self.debug_mode_var.set(self.settings_manager.get("advanced.debug_mode", False))
            
        except Exception as e:
            logging.error(f"加载通用设置时出错: {e}")
            
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 保存界面设置
            self.settings_manager.set("interface.language", self.language_var.get())
            
            # 保存主题设置
            selected_theme = self.theme_var.get()
            if self.theme_manager and selected_theme:
                self.theme_manager.set_current_theme(selected_theme)
            self.settings_manager.set("interface.theme", selected_theme)
            
            # 保存更新设置
            self.settings_manager.set("updates.check_automatically", self.check_updates_var.get())
            self.settings_manager.set("updates.install_automatically", self.auto_install_updates_var.get())
            
            # 保存启动设置
            self.settings_manager.set("startup.check_environment", self.startup_check_var.get())
            self.settings_manager.set("startup.show_welcome", self.show_welcome_var.get())
            
            # 保存高级设置
            self.settings_manager.set("advanced.debug_mode", self.debug_mode_var.get())
            
            return True
        except Exception as e:
            logging.error(f"保存通用设置时出错: {e}")
            return False 