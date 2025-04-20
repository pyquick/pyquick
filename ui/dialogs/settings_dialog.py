"""
PyQuick 设置对话框模块

提供应用程序的设置对话框
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# 获取根目录并添加到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from log import get_logger
from lang import get_text, set_language
from ui.dialogs.base import BaseDialog, center_window
import settings

# 获取日志记录器
logger = get_logger()

class SettingsDialog(BaseDialog):
    """设置对话框类"""
    
    def __init__(self, parent=None, config_path=None, restart_callback=None):
        """
        初始化设置对话框
        
        参数:
            parent: 父窗口
            config_path: 配置文件路径
            restart_callback: 重启应用的回调函数
        """
        super().__init__(
            parent=parent,
            title=get_text("settings"),
            icon_path="pyquick.ico",
            modal=True
        )
        self.config_path = config_path
        self.restart_callback = restart_callback
        self.settings_changed = False
        self.language_changed = False
        
        # 设置变量
        self.language_var = None
        self.theme_var = None
        self.multithread_var = None
        self.auto_check_pip_var = None
        self.python_mirror_var = None
        self.pip_mirror_var = None
        self.log_size_var = None
        
    def create_dialog(self):
        """创建设置对话框"""
        dialog = super().create_dialog()
        if not dialog:
            return
        
        # 读取设置
        self._load_settings()
        
        # 创建主框架
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(expand=True, fill="both")
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建各选项卡内容
        self._create_general_tab()
        self._create_mirrors_tab()
        self._create_log_tab()
        
        # 底部按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(15, 0))
        
        save_button = ttk.Button(
            button_frame, 
            text=get_text("save"), 
            command=self._save_settings
        )
        save_button.pack(side="right", padx=5)
        
        cancel_button = ttk.Button(
            button_frame, 
            text=get_text("cancel"), 
            command=self.on_close
        )
        cancel_button.pack(side="right", padx=5)
        
        # 居中显示窗口
        center_window(dialog, self.parent)
        
        return dialog
    
    def _load_settings(self):
        """加载配置"""
        try:
            # 读取多线程下载设置
            allow_multithreading = settings.get_setting("allow_multithreading", True)
            
            # 读取语言设置
            language = settings.get_setting("language", "zh_CN")
            
            # 读取主题设置
            theme = settings.get_setting("theme", "light")
            
            # 读取Python镜像设置
            python_mirror = settings.get_setting("python_mirror", get_text("default_source"))
            
            # 读取Pip镜像设置
            pip_mirror = settings.get_setting("pip_mirror", get_text("default_source"))
            
            # 读取日志大小设置
            max_log_size = settings.get_setting("max_log_size", 10)
            
            # 读取pip版本检查设置
            auto_check_pip = True  # 默认启用
            try:
                with open(os.path.join(self.config_path, "allowupdatepip.txt"), "r") as f:
                    lines = f.readlines()
                    if lines:
                        auto_check_pip = lines[0].strip().lower() == "true"
            except Exception as e:
                logger.error(f"读取pip版本检查设置失败: {e}")
            
            # 初始化UI变量
            self.language_var = tk.StringVar(value=language)
            self.theme_var = tk.StringVar(value=theme)
            self.multithread_var = tk.BooleanVar(value=allow_multithreading)
            self.auto_check_pip_var = tk.BooleanVar(value=auto_check_pip)
            self.python_mirror_var = tk.StringVar(value=python_mirror)
            self.pip_mirror_var = tk.StringVar(value=pip_mirror)
            self.log_size_var = tk.StringVar(value=str(max_log_size))
            
        except Exception as e:
            logger.error(f"{get_text('settings_read_fail')}: {e}")
            messagebox.showerror(get_text("error"), f"{get_text('settings_read_fail')}: {e}")
    
    def _create_general_tab(self):
        """创建常规设置选项卡"""
        general_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(general_frame, text=get_text("settings"))
        
        # 语言设置
        lang_frame = ttk.LabelFrame(general_frame, text=get_text("language_settings"), padding=10)
        lang_frame.pack(fill="x", pady=(0, 15))
        
        # 中文选项
        ttk.Radiobutton(
            lang_frame, 
            text=get_text("simplified_chinese"), 
            variable=self.language_var, 
            value="zh_CN"
        ).pack(anchor="w", padx=5, pady=2)
        
        # 英文选项
        ttk.Radiobutton(
            lang_frame, 
            text=get_text("english"), 
            variable=self.language_var, 
            value="en_US"
        ).pack(anchor="w", padx=5, pady=2)
        
        # 主题设置（仅在Windows 11上显示）
        if not settings.is_windows10_or_lower():
            theme_frame = ttk.LabelFrame(general_frame, text=get_text("theme_settings"), padding=10)
            theme_frame.pack(fill="x", pady=(0, 15))
            
            # 浅色主题选项
            ttk.Radiobutton(
                theme_frame, 
                text=get_text("light_theme"), 
                variable=self.theme_var, 
                value="light"
            ).pack(anchor="w", padx=5, pady=2)
            
            # 深色主题选项
            ttk.Radiobutton(
                theme_frame, 
                text=get_text("dark_theme"), 
                variable=self.theme_var, 
                value="dark"
            ).pack(anchor="w", padx=5, pady=2)
        
        # 下载设置
        download_frame = ttk.LabelFrame(general_frame, text=get_text("download_settings"), padding=10)
        download_frame.pack(fill="x", pady=(0, 15))
        
        # 多线程下载设置
        ttk.Checkbutton(
            download_frame, 
            text=get_text("enable_multithreading"), 
            variable=self.multithread_var
        ).pack(anchor="w", padx=5, pady=2)
        
        # pip 更新检查设置
        ttk.Checkbutton(
            download_frame, 
            text=get_text("enable_pip_version_check"), 
            variable=self.auto_check_pip_var
        ).pack(anchor="w", padx=5, pady=2)
    
    def _create_mirrors_tab(self):
        """创建镜像设置选项卡"""
        mirrors_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(mirrors_frame, text=get_text("download_mirror_settings"))
        
        # Python下载镜像设置
        python_mirror_frame = ttk.LabelFrame(mirrors_frame, text=get_text("python_download_mirror"), padding=10)
        python_mirror_frame.pack(fill="x", pady=(0, 15))
        
        # 获取镜像列表
        python_mirrors = settings.get_python_mirrors()
        
        # 创建下拉菜单选项
        python_mirror_options = [get_text("default_source")] + python_mirrors[1:]  # 第一个作为默认源
        
        # 创建下拉菜单和标签
        ttk.Label(python_mirror_frame, text=get_text("python_download_mirror")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        python_mirror_combo = ttk.Combobox(python_mirror_frame, textvariable=self.python_mirror_var, width=40, state="readonly")
        python_mirror_combo["values"] = python_mirror_options
        python_mirror_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # 添加默认源说明
        ttk.Label(
            python_mirror_frame, 
            text=f"{get_text('default_source')}: {python_mirrors[0]}"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5), padx=5)
        
        # 添加测试按钮
        ttk.Button(
            python_mirror_frame, 
            text=get_text("test_python_mirror"), 
            command=lambda: self._test_mirror("python")
        ).grid(row=0, column=2, padx=5, pady=5)
        
        # pip镜像设置
        pip_mirror_frame = ttk.LabelFrame(mirrors_frame, text=get_text("pip_mirror"), padding=10)
        pip_mirror_frame.pack(fill="x", pady=(0, 15))
        
        # 获取镜像列表
        pip_mirrors = settings.get_pip_mirrors()
        
        # 创建下拉菜单选项
        pip_mirror_options = [get_text("default_source")] + pip_mirrors[1:]  # 第一个作为默认源
        
        # 创建下拉菜单和标签
        ttk.Label(pip_mirror_frame, text=get_text("pip_mirror")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        pip_mirror_combo = ttk.Combobox(pip_mirror_frame, textvariable=self.pip_mirror_var, width=40, state="readonly")
        pip_mirror_combo["values"] = pip_mirror_options
        pip_mirror_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # 添加默认源说明
        ttk.Label(
            pip_mirror_frame, 
            text=f"{get_text('default_source')}: {pip_mirrors[0]}"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5), padx=5)
        
        # 添加测试按钮
        ttk.Button(
            pip_mirror_frame, 
            text=get_text("test_pip_mirror"), 
            command=lambda: self._test_mirror("pip")
        ).grid(row=0, column=2, padx=5, pady=5)
    
    def _create_log_tab(self):
        """创建日志设置选项卡"""
        log_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(log_frame, text=get_text("log_settings"))
        
        # 日志大小设置
        log_size_frame = ttk.LabelFrame(log_frame, text=get_text("log_settings"), padding=10)
        log_size_frame.pack(fill="x", pady=(0, 15))
        
        # 日志大小设置
        ttk.Label(log_size_frame, text=get_text("max_log_size")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        log_size_combo = ttk.Combobox(log_size_frame, textvariable=self.log_size_var, width=10, state="readonly")
        log_size_combo["values"] = ["5", "10", "20", "50", "100"]
        log_size_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        # 单位标签
        ttk.Label(log_size_frame, text="MB").grid(row=0, column=2, sticky="w", pady=5, padx=5)
    
    def _test_mirror(self, mirror_type):
        """测试镜像"""
        from pyquick import show_mirror_test_window
        
        try:
            # 关闭设置窗口
            self.dialog.withdraw()
            
            # 显示镜像测试窗口
            show_mirror_test_window(mirror_type)
            
            # 重新显示设置窗口
            self.dialog.deiconify()
        except Exception as e:
            logger.error(f"{get_text('mirror_test_window_error')}: {e}")
            messagebox.showerror(get_text("error"), f"{get_text('mirror_test_window_error')}: {e}")
    
    def _save_settings(self):
        """保存设置"""
        try:
            old_language = settings.get_setting("language", "zh_CN")
            
            # 更新设置字典
            settings.set_setting("theme", self.theme_var.get())
            settings.set_setting("python_mirror", self.python_mirror_var.get())
            settings.set_setting("pip_mirror", self.pip_mirror_var.get())
            settings.set_setting("allow_multithreading", self.multithread_var.get())
            settings.set_setting("language", self.language_var.get())
            settings.set_setting("max_log_size", int(self.log_size_var.get()))
            settings.set_setting("auto_check_pip", self.auto_check_pip_var.get())
            
            # 保存设置
            if settings.save_settings(self.config_path):
                # 保存多线程设置
                with open(os.path.join(self.config_path, "allowthread.txt"), "w") as f:
                    f.write("True" if self.multithread_var.get() else "False")
                
                # 保存pip版本检查设置
                try:
                    # 保持当前版本信息不变
                    current_version = ""
                    with open(os.path.join(self.config_path, "allowupdatepip.txt"), "r") as f:
                        lines = f.readlines()
                        if len(lines) > 1:
                            current_version = lines[1].strip()
                    
                    with open(os.path.join(self.config_path, "allowupdatepip.txt"), "w") as f:
                        f.write("True" if self.auto_check_pip_var.get() else "False")
                        f.write("\n")
                        if current_version:
                            f.write(current_version)
                except Exception as e:
                    logger.error(f"保存pip版本检查设置失败: {e}")
                
                # 检查语言是否更改
                new_language = str(self.language_var.get()).strip().lower()
                old_language = str(old_language).strip().lower()
                
                logger.debug(f"Checking language change - old: '{old_language}', new: '{new_language}'")
                
                if old_language != new_language:
                    self.language_changed = True
                    set_language(new_language)
                    # 显示需要重启的提示
                    restart_msg = get_text("language_changed")
                    logger.info(f"Language changed from '{old_language}' to '{new_language}', showing restart prompt")
                    messagebox.showinfo(get_text("success"), restart_msg, parent=self.dialog)
                    self.on_close()
                    
                    # 如果提供了重启回调，则调用
                    if self.restart_callback:
                        self.restart_callback()
                else:
                    # 没有更改语言，正常关闭
                    logger.debug("No language change detected")
                    messagebox.showinfo(get_text("success"), get_text("settings_saved"), parent=self.dialog)
                    self.on_close()
            else:
                messagebox.showerror(get_text("error"), get_text("settings_save_fail"), parent=self.dialog)
        except Exception as e:
            logger.error(f"{get_text('settings_save_fail')}: {e}")
            messagebox.showerror(get_text("error"), f"{get_text('settings_save_fail')}: {e}", parent=self.dialog)

def show_settings_dialog(parent=None, config_path=None, restart_callback=None):
    """
    显示设置对话框
    
    参数:
        parent: 父窗口
        config_path: 配置文件路径
        restart_callback: 重启应用的回调函数
    """
    try:
        # 创建并显示对话框
        if threading.current_thread() is threading.main_thread():
            settings_dialog = SettingsDialog(parent, config_path, restart_callback)
            settings_dialog.show()
        else:
            # 如果在非主线程中调用，则在主线程中执行
            if parent:
                parent.after(0, lambda: SettingsDialog(parent, config_path, restart_callback).show())
            else:
                # 没有父窗口时，创建新窗口运行
                logger.warning("在非主线程中调用设置对话框，且没有提供父窗口")
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                settings_dialog = SettingsDialog(root, config_path, restart_callback)
                settings_dialog.show()
                root.mainloop()
    except Exception as e:
        logger.error(f"显示设置对话框时出错: {e}")
        return None 