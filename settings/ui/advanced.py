"""
高级设置面板，提供日志级别、调试选项和性能设置
"""
import tkinter as tk
from tkinter import ttk
import logging
import os
import sys

from settings.ui.base_panel import BaseSettingsPanel

class AdvancedSettingsPanel(BaseSettingsPanel):
    """
    高级设置面板类，管理日志、调试和性能等高级选项
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
        self.log_level_var = tk.StringVar()
        self.log_to_file_var = tk.BooleanVar()
        self.log_max_size_var = tk.IntVar()
        self.log_backup_count_var = tk.IntVar()
        self.debug_mode_var = tk.BooleanVar()
        self.dev_tools_var = tk.BooleanVar()
        self.performance_mode_var = tk.StringVar()
        self.memory_limit_var = tk.IntVar()
        self.limit_memory_var = tk.BooleanVar()
        self.auto_clean_temp_var = tk.BooleanVar()
        self.clear_cache_days_var = tk.IntVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置高级设置面板的用户界面"""
        # 日志设置
        log_section, log_content = self.create_section_frame("日志设置")
        
        # 日志级别
        level_frame = ttk.Frame(log_content)
        level_frame.pack(fill=tk.X, pady=5)
        
        level_label = ttk.Label(level_frame, text="日志记录级别:")
        level_label.pack(side=tk.LEFT, padx=5)
        
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        level_combo = ttk.Combobox(level_frame, textvariable=self.log_level_var, 
                                  values=log_levels, state="readonly", width=10)
        level_combo.pack(side=tk.LEFT, padx=5)
        
        # 日志文件选项
        file_frame = ttk.Frame(log_content)
        file_frame.pack(fill=tk.X, pady=5)
        
        file_check = ttk.Checkbutton(file_frame, text="将日志写入文件", 
                                    variable=self.log_to_file_var,
                                    command=self._toggle_log_file_options)
        file_check.pack(side=tk.LEFT, padx=5)
        
        # 日志文件大小
        size_frame = ttk.Frame(log_content)
        size_frame.pack(fill=tk.X, pady=5)
        
        size_label = ttk.Label(size_frame, text="最大日志文件大小(MB):")
        size_label.pack(side=tk.LEFT, padx=5)
        
        size_spin = ttk.Spinbox(size_frame, textvariable=self.log_max_size_var, 
                               from_=1, to=100, width=5)
        size_spin.pack(side=tk.LEFT, padx=5)
        
        # 日志文件备份数
        backup_frame = ttk.Frame(log_content)
        backup_frame.pack(fill=tk.X, pady=5)
        
        backup_label = ttk.Label(backup_frame, text="保留的日志文件数量:")
        backup_label.pack(side=tk.LEFT, padx=5)
        
        backup_spin = ttk.Spinbox(backup_frame, textvariable=self.log_backup_count_var, 
                                 from_=1, to=10, width=5)
        backup_spin.pack(side=tk.LEFT, padx=5)
        
        # 查看日志按钮
        view_log_button = ttk.Button(log_content, text="查看当前日志文件", 
                                    command=self._view_log_file)
        view_log_button.pack(anchor=tk.W, pady=5, padx=5)
        
        # 调试设置
        debug_section, debug_content = self.create_section_frame("调试设置")
        
        # 调试模式
        debug_check = ttk.Checkbutton(debug_content, text="启用调试模式", 
                                     variable=self.debug_mode_var)
        debug_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 开发者工具
        dev_tools_check = ttk.Checkbutton(debug_content, text="显示开发者工具菜单", 
                                         variable=self.dev_tools_var)
        dev_tools_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 性能设置
        perf_section, perf_content = self.create_section_frame("性能设置")
        
        # 性能模式
        mode_frame = ttk.Frame(perf_content)
        mode_frame.pack(fill=tk.X, pady=5)
        
        mode_label = ttk.Label(mode_frame, text="性能模式:")
        mode_label.pack(side=tk.LEFT, padx=5)
        
        modes = ["平衡", "高性能", "节能"]
        mode_combo = ttk.Combobox(mode_frame, textvariable=self.performance_mode_var, 
                                 values=modes, state="readonly", width=10)
        mode_combo.pack(side=tk.LEFT, padx=5)
        
        # 内存限制
        mem_check = ttk.Checkbutton(perf_content, text="限制内存使用", 
                                   variable=self.limit_memory_var,
                                   command=self._toggle_memory_limit)
        mem_check.pack(anchor=tk.W, padx=5, pady=5)
        
        mem_frame = ttk.Frame(perf_content)
        mem_frame.pack(fill=tk.X, pady=5)
        
        mem_label = ttk.Label(mem_frame, text="最大内存使用(MB):")
        mem_label.pack(side=tk.LEFT, padx=5)
        
        mem_spin = ttk.Spinbox(mem_frame, textvariable=self.memory_limit_var, 
                              from_=128, to=8192, width=6)
        mem_spin.pack(side=tk.LEFT, padx=5)
        
        # 清理设置
        clean_section, clean_content = self.create_section_frame("临时文件清理")
        
        # 自动清理
        clean_check = ttk.Checkbutton(clean_content, text="自动清理临时文件", 
                                     variable=self.auto_clean_temp_var,
                                     command=self._toggle_clean_days)
        clean_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # 清理天数
        days_frame = ttk.Frame(clean_content)
        days_frame.pack(fill=tk.X, pady=5)
        
        days_label = ttk.Label(days_frame, text="清理超过这些天数的临时文件:")
        days_label.pack(side=tk.LEFT, padx=5)
        
        days_spin = ttk.Spinbox(days_frame, textvariable=self.clear_cache_days_var, 
                               from_=1, to=90, width=5)
        days_spin.pack(side=tk.LEFT, padx=5)
        
        # 立即清理按钮
        clean_now_button = ttk.Button(clean_content, text="立即清理所有临时文件", 
                                     command=self._clean_temp_files_now)
        clean_now_button.pack(anchor=tk.W, pady=5, padx=5)
        
        # 重置设置
        reset_section, reset_content = self.create_section_frame("重置设置")
        
        # 重置按钮
        reset_frame = ttk.Frame(reset_content)
        reset_frame.pack(fill=tk.X, pady=10)
        
        reset_all_button = ttk.Button(reset_frame, text="重置所有设置", 
                                     command=self._reset_all_settings)
        reset_all_button.pack(side=tk.LEFT, padx=5)
        
        reset_current_button = ttk.Button(reset_frame, text="重置高级设置", 
                                        command=self._reset_advanced_settings)
        reset_current_button.pack(side=tk.LEFT, padx=5)
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 日志设置
            self.log_level_var.set(self.settings_manager.get("advanced.log_level", "INFO"))
            self.log_to_file_var.set(self.settings_manager.get("advanced.log_to_file", True))
            self.log_max_size_var.set(self.settings_manager.get("advanced.log_max_size", 10))
            self.log_backup_count_var.set(self.settings_manager.get("advanced.log_backup_count", 3))
            
            # 调试设置
            self.debug_mode_var.set(self.settings_manager.get("advanced.debug_mode", False))
            self.dev_tools_var.set(self.settings_manager.get("advanced.dev_tools", False))
            
            # 性能设置
            self.performance_mode_var.set(self.settings_manager.get("advanced.performance_mode", "平衡"))
            self.limit_memory_var.set(self.settings_manager.get("advanced.limit_memory", False))
            self.memory_limit_var.set(self.settings_manager.get("advanced.memory_limit", 512))
            
            # 清理设置
            self.auto_clean_temp_var.set(self.settings_manager.get("advanced.auto_clean_temp", True))
            self.clear_cache_days_var.set(self.settings_manager.get("advanced.clear_cache_days", 7))
            
            # 更新UI状态
            self._toggle_log_file_options()
            self._toggle_memory_limit()
            self._toggle_clean_days()
            
            logging.debug("高级设置加载成功")
        except Exception as e:
            logging.error(f"加载高级设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 日志设置
            self.settings_manager.set("advanced.log_level", self.log_level_var.get())
            self.settings_manager.set("advanced.log_to_file", self.log_to_file_var.get())
            self.settings_manager.set("advanced.log_max_size", self.log_max_size_var.get())
            self.settings_manager.set("advanced.log_backup_count", self.log_backup_count_var.get())
            
            # 调试设置
            self.settings_manager.set("advanced.debug_mode", self.debug_mode_var.get())
            self.settings_manager.set("advanced.dev_tools", self.dev_tools_var.get())
            
            # 性能设置
            self.settings_manager.set("advanced.performance_mode", self.performance_mode_var.get())
            self.settings_manager.set("advanced.limit_memory", self.limit_memory_var.get())
            self.settings_manager.set("advanced.memory_limit", self.memory_limit_var.get())
            
            # 清理设置
            self.settings_manager.set("advanced.auto_clean_temp", self.auto_clean_temp_var.get())
            self.settings_manager.set("advanced.clear_cache_days", self.clear_cache_days_var.get())
            
            # 应用日志设置
            self._apply_log_settings()
            
            logging.debug("高级设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存高级设置时出错: {e}")
            return False
    
    def _toggle_log_file_options(self):
        """根据日志文件选项启用或禁用相关字段"""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "日志设置" in child.cget("text"):
                    for frame in child.winfo_children():
                        if isinstance(frame, ttk.Frame):
                            if "最大日志" in frame.winfo_children()[0].cget("text") or \
                               "保留的日志" in frame.winfo_children()[0].cget("text"):
                                for widget in frame.winfo_children():
                                    if isinstance(widget, ttk.Spinbox):
                                        if self.log_to_file_var.get():
                                            widget.configure(state="normal")
                                        else:
                                            widget.configure(state="disabled")
    
    def _toggle_memory_limit(self):
        """根据内存限制选项启用或禁用相关字段"""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "性能设置" in child.cget("text"):
                    for frame in child.winfo_children():
                        if isinstance(frame, ttk.Frame) and "最大内存" in frame.winfo_children()[0].cget("text"):
                            for widget in frame.winfo_children():
                                if isinstance(widget, ttk.Spinbox):
                                    if self.limit_memory_var.get():
                                        widget.configure(state="normal")
                                    else:
                                        widget.configure(state="disabled")
    
    def _toggle_clean_days(self):
        """根据自动清理选项启用或禁用相关字段"""
        for child in self.winfo_children():
            if isinstance(child, ttk.LabelFrame):
                if "临时文件清理" in child.cget("text"):
                    for frame in child.winfo_children():
                        if isinstance(frame, ttk.Frame) and "清理超过" in frame.winfo_children()[0].cget("text"):
                            for widget in frame.winfo_children():
                                if isinstance(widget, ttk.Spinbox):
                                    if self.auto_clean_temp_var.get():
                                        widget.configure(state="normal")
                                    else:
                                        widget.configure(state="disabled")
    
    def _apply_log_settings(self):
        """应用日志设置"""
        try:
            # 获取当前日志级别
            level_name = self.log_level_var.get()
            level = getattr(logging, level_name)
            
            # 设置根日志记录器级别
            logging.getLogger().setLevel(level)
            
            # 如果日志处理器已经存在，更新它们
            for handler in logging.getLogger().handlers:
                handler.setLevel(level)
                
                # 更新文件处理器
                if hasattr(handler, 'baseFilename'):
                    if not self.log_to_file_var.get():
                        logging.getLogger().removeHandler(handler)
                    else:
                        # 更新大小和备份数量 (对于RotatingFileHandler)
                        if hasattr(handler, 'maxBytes'):
                            max_size_bytes = self.log_max_size_var.get() * 1024 * 1024
                            handler.maxBytes = max_size_bytes
                            
                        if hasattr(handler, 'backupCount'):
                            handler.backupCount = self.log_backup_count_var.get()
            
            logging.info(f"已应用日志设置: 级别={level_name}, 文件记录={self.log_to_file_var.get()}")
        except Exception as e:
            logging.error(f"应用日志设置时出错: {e}")
    
    def _view_log_file(self):
        """查看当前日志文件"""
        from tkinter import messagebox
        import subprocess
        
        # 查找当前日志文件
        log_file = None
        for handler in logging.getLogger().handlers:
            if hasattr(handler, 'baseFilename'):
                log_file = handler.baseFilename
                break
        
        if not log_file or not os.path.exists(log_file):
            messagebox.showinfo("日志文件", "当前没有活动的日志文件")
            return
            
        try:
            # 尝试用系统默认应用打开日志文件
            if sys.platform == "win32":
                os.startfile(log_file)
            elif sys.platform == "darwin":
                subprocess.call(["open", log_file])
            else:
                subprocess.call(["xdg-open", log_file])
                
            logging.debug(f"已打开日志文件: {log_file}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开日志文件: {e}")
            logging.error(f"打开日志文件时出错: {e}")
    
    def _clean_temp_files_now(self):
        """立即清理所有临时文件"""
        from tkinter import messagebox
        import tempfile
        import time
        import shutil
        
        try:
            # 清理应用临时目录
            app_temp_dir = os.path.join(tempfile.gettempdir(), "pyquick")
            if os.path.exists(app_temp_dir):
                shutil.rmtree(app_temp_dir, ignore_errors=True)
                
            # 清理下载缓存
            cache_dir = os.path.join(os.path.expanduser("~"), ".pyquick", "cache")
            if os.path.exists(cache_dir):
                shutil.rmtree(cache_dir, ignore_errors=True)
                
            # 清理会话文件
            session_dir = os.path.join(os.path.expanduser("~"), ".pyquick", "sessions")
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)
                
            # 清理过时的日志文件
            log_dir = os.path.join(os.path.expanduser("~"), ".pyquick", "logs")
            if os.path.exists(log_dir):
                now = time.time()
                for f in os.listdir(log_dir):
                    if f.endswith(".log") and f != "pyquick.log":
                        file_path = os.path.join(log_dir, f)
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                
            messagebox.showinfo("清理完成", "所有临时文件已清理")
            logging.info("所有临时文件已手动清理")
        except Exception as e:
            messagebox.showerror("清理失败", f"清理临时文件时出错: {e}")
            logging.error(f"清理临时文件时出错: {e}")
    
    def _reset_all_settings(self):
        """重置所有设置"""
        from tkinter import messagebox
        
        if messagebox.askyesno("确认重置", 
                              "确定要重置所有设置为默认值吗？\n\n此操作不可撤销。"):
            try:
                # 重置所有设置
                self.settings_manager.reset_to_defaults()
                
                # 重新加载当前面板设置
                self.load_settings()
                
                messagebox.showinfo("重置完成", 
                                   "所有设置已重置为默认值。\n\n请点击保存以应用更改。")
                logging.info("已重置所有设置为默认值")
            except Exception as e:
                messagebox.showerror("重置失败", f"重置设置时出错: {e}")
                logging.error(f"重置所有设置时出错: {e}")
    
    def _reset_advanced_settings(self):
        """重置高级设置"""
        from tkinter import messagebox
        
        if messagebox.askyesno("确认重置", 
                              "确定要重置高级设置为默认值吗？"):
            try:
                # 仅重置高级设置
                self.settings_manager.reset_to_defaults("advanced")
                
                # 重新加载当前面板设置
                self.load_settings()
                
                messagebox.showinfo("重置完成", 
                                   "高级设置已重置为默认值。\n\n请点击保存以应用更改。")
                logging.info("已重置高级设置为默认值")
            except Exception as e:
                messagebox.showerror("重置失败", f"重置高级设置时出错: {e}")
                logging.error(f"重置高级设置时出错: {e}") 