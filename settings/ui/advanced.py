"""
高级设置面板，用于管理应用程序高级选项和调试功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import shutil

from settings.ui.base_panel import BaseSettingsPanel

class AdvancedSettingsPanel(BaseSettingsPanel):
    """
    高级设置面板类，管理应用程序高级选项和调试功能
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化高级设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.debug_mode_var = tk.BooleanVar()
        self.log_level_var = tk.StringVar()
        self.clear_cache_var = tk.BooleanVar()
        self.update_channel_var = tk.StringVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置高级设置面板的用户界面"""
        # 调试设置
        debug_section, debug_content = self.create_section_frame("调试设置")
        
        # 调试模式
        debug_frame = ttk.Frame(debug_content)
        debug_frame.pack(fill=tk.X, pady=5)
        
        debug_check = ttk.Checkbutton(debug_frame, text="启用调试模式", 
                                    variable=self.debug_mode_var)
        debug_check.pack(side=tk.LEFT, padx=5)
        
        debug_tip = ttk.Label(debug_frame, 
                            text="(启用后将显示更多技术信息，影响性能)",
                            foreground="gray", font=("", 9))
        debug_tip.pack(side=tk.LEFT, padx=5)
        
        # 日志级别
        log_frame = ttk.Frame(debug_content)
        log_frame.pack(fill=tk.X, pady=5)
        
        log_label = ttk.Label(log_frame, text="日志级别:")
        log_label.pack(side=tk.LEFT, padx=5)
        
        log_levels = ["debug", "info", "warning", "error"]
        log_combobox = ttk.Combobox(log_frame, textvariable=self.log_level_var,
                                  values=log_levels, state="readonly", width=10)
        log_combobox.pack(side=tk.LEFT, padx=5)
        
        # 缓存设置
        cache_section, cache_content = self.create_section_frame("缓存设置")
        
        # 退出时清除缓存
        cache_frame = ttk.Frame(cache_content)
        cache_frame.pack(fill=tk.X, pady=5)
        
        cache_check = ttk.Checkbutton(cache_frame, text="退出时清除缓存", 
                                    variable=self.clear_cache_var)
        cache_check.pack(side=tk.LEFT, padx=5)
        
        # 清除缓存按钮
        clear_button = ttk.Button(cache_frame, text="立即清除缓存", 
                                command=self._clear_cache_now)
        clear_button.pack(side=tk.RIGHT, padx=5)
        
        # 更新设置
        update_section, update_content = self.create_section_frame("更新设置")
        
        # 更新渠道
        channel_frame = ttk.Frame(update_content)
        channel_frame.pack(fill=tk.X, pady=5)
        
        channel_label = ttk.Label(channel_frame, text="更新渠道:")
        channel_label.pack(side=tk.LEFT, padx=5)
        
        channels = ["stable", "beta", "dev"]
        channel_combobox = ttk.Combobox(channel_frame, textvariable=self.update_channel_var,
                                      values=channels, state="readonly", width=10)
        channel_combobox.pack(side=tk.LEFT, padx=5)
        
        # 渠道说明
        channel_desc_frame = ttk.Frame(update_content)
        channel_desc_frame.pack(fill=tk.X, pady=5)
        
        channel_desc = ttk.Label(channel_desc_frame, 
                               text="stable: 稳定版本，推荐使用\n"
                                    "beta: 测试版本，包含新功能\n"
                                    "dev: 开发版本，可能不稳定",
                               justify=tk.LEFT, font=("", 9))
        channel_desc.pack(side=tk.LEFT, padx=5)
        
        # 重置设置
        reset_section, reset_content = self.create_section_frame("重置设置")
        
        # 重置按钮
        reset_frame = ttk.Frame(reset_content)
        reset_frame.pack(fill=tk.X, pady=5)
        
        reset_button = ttk.Button(reset_frame, text="重置所有设置为默认值", 
                                     command=self._reset_all_settings)
        reset_button.pack(side=tk.RIGHT, padx=5)
        
        reset_warning = ttk.Label(reset_frame, 
                                text="警告: 此操作不可撤销", 
                                foreground="red")
        reset_warning.pack(side=tk.LEFT, padx=5)
        
    def _clear_cache_now(self):
        """立即清除缓存"""
        if messagebox.askyesno("清除缓存", "确定要清除所有缓存吗？"):
            try:
                # 获取缓存目录
                config_path = self.settings_manager.config_path
                cache_dir = os.path.join(config_path, "cache")
                
                # 如果缓存目录不存在，创建空目录
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                    messagebox.showinfo("清除缓存", "缓存目录已创建，无需清除。")
                    return
                
                # 删除缓存目录中的所有文件
                for filename in os.listdir(cache_dir):
                    file_path = os.path.join(cache_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logging.error(f"清除缓存文件失败: {e}")
                
                # 清除临时目录中的临时文件
                temp_dir = os.path.join(config_path, "temp")
                if os.path.exists(temp_dir):
                    try:
                        for filename in os.listdir(temp_dir):
                            file_path = os.path.join(temp_dir, filename)
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                    except Exception as e:
                        logging.error(f"清除临时文件失败: {e}")
                
                # 清除崩溃日志
                crash_dir = os.path.join(config_path, "crashes")
                if os.path.exists(crash_dir):
                    try:
                        for filename in os.listdir(crash_dir):
                            if filename.endswith(".log") or filename.endswith(".dmp"):
                                file_path = os.path.join(crash_dir, filename)
                                os.unlink(file_path)
                    except Exception as e:
                        logging.error(f"清除崩溃日志失败: {e}")
                
                messagebox.showinfo("清除缓存", "已成功清除所有缓存文件！")
                logging.info("已手动清除所有缓存文件")
            except Exception as e:
                messagebox.showerror("清除缓存", f"清除缓存时出错: {e}")
                logging.error(f"清除缓存时出错: {e}")
    
    def _reset_all_settings(self):
        """重置所有设置为默认值"""
        if messagebox.askyesno("重置设置", 
                              "确定要将所有设置重置为默认值吗？\n"
                              "此操作将删除所有自定义设置，且不可撤销！"):
            try:
                # 创建一个确认对话框
                confirm = messagebox.askokcancel("确认重置", 
                                               "最后确认：\n"
                                               "重置将清除所有自定义设置，包括下载路径、代理设置等，"
                                               "并恢复到默认状态。\n\n"
                                               "确定要继续吗？")
                if confirm:
                    # 删除设置文件
                    settings_file = self.settings_manager.settings_file
                    if os.path.exists(settings_file):
                        os.unlink(settings_file)
                        
                    # 重新初始化设置管理器
                    self.settings_manager._init_default_settings()
                    self.settings_manager.save_settings()
                    
                    # 重新加载设置到UI
                    self.load_settings()
                    
                    # 通知用户
                    messagebox.showinfo("重置设置", "所有设置已重置为默认值！\n重启应用后生效。")
                    logging.info("用户已手动重置所有设置为默认值")
            except Exception as e:
                messagebox.showerror("重置设置", f"重置设置时出错: {e}")
                logging.error(f"重置设置时出错: {e}")
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 调试设置
            self.debug_mode_var.set(self.settings_manager.get("advanced.debug_mode", False))
            self.log_level_var.set(self.settings_manager.get("advanced.log_level", "info"))
            
            # 缓存设置
            self.clear_cache_var.set(self.settings_manager.get("advanced.clear_cache_on_exit", False))
            
            # 更新设置
            self.update_channel_var.set(self.settings_manager.get("advanced.update_channel", "stable"))
            
            logging.debug("高级设置加载成功")
        except Exception as e:
            logging.error(f"加载高级设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 调试设置
            self.settings_manager.set("advanced.debug_mode", self.debug_mode_var.get())
            self.settings_manager.set("advanced.log_level", self.log_level_var.get())
            
            # 缓存设置
            self.settings_manager.set("advanced.clear_cache_on_exit", self.clear_cache_var.get())
            
            # 更新设置
            self.settings_manager.set("advanced.update_channel", self.update_channel_var.get())
            
            logging.debug("高级设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存高级设置时出错: {e}")
            return False