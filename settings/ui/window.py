"""
设置窗口模块
提供应用程序的设置界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

# 导入设置面板
from settings.ui.general import GeneralSettingsPanel
from settings.ui.appearance import AppearanceSettingsPanel
from settings.ui.download import DownloadSettingsPanel
from settings.ui.proxy import ProxySettingsPanel
from settings.ui.python import PythonSettingsPanel
from settings.ui.advanced import AdvancedSettingsPanel

logger = logging.getLogger(__name__)

class SettingsWindow:
    """设置窗口类，管理所有设置面板"""

    def __init__(self, parent, settings_manager):
        self.parent = parent
        self.settings_manager = settings_manager
        self.panels = []  # 存储所有设置面板
        
        # 创建设置窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 设置居中显示
        self.window.geometry("650x500")
        self.window.resizable(True, True)
        
        # 创建面板和按钮
        self._create_ui()
        
        # 居中显示
        self._center_window()
        
    def _center_window(self):
        """将窗口居中显示在父窗口上"""
        self.window.update_idletasks()
        
        # 获取父窗口和当前窗口的尺寸和位置
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # 设置窗口位置
        self.window.geometry(f"+{x}+{y}")
        
    def _create_ui(self):
        """创建设置界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡控件
        tab_control = ttk.Notebook(main_frame)
        tab_control.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建各个设置面板
        try:
            # 常规设置选项卡
            general_panel = GeneralSettingsPanel(tab_control, self.settings_manager)
            tab_control.add(general_panel, text="常规设置")
            self.panels.append(general_panel)
            
            # 外观设置选项卡
            appearance_panel = AppearanceSettingsPanel(tab_control, self.settings_manager)
            tab_control.add(appearance_panel, text="外观设置")
            self.panels.append(appearance_panel)
            
            # 下载设置选项卡
            download_panel = DownloadSettingsPanel(tab_control, self.settings_manager)
            tab_control.add(download_panel, text="下载设置")
            self.panels.append(download_panel)
            
            # 代理设置选项卡
            proxy_panel = ProxySettingsPanel(tab_control, self.settings_manager)
            tab_control.add(proxy_panel, text="代理设置")
            self.panels.append(proxy_panel)
            
            # Python版本管理选项卡
            python_panel = PythonSettingsPanel(tab_control, self.settings_manager)
            tab_control.add(python_panel, text="Python版本")
            self.panels.append(python_panel)
            
            # 高级设置选项卡
            advanced_panel = AdvancedSettingsPanel(tab_control, self.settings_manager)
            tab_control.add(advanced_panel, text="高级设置")
            self.panels.append(advanced_panel)
            
        except Exception as e:
            logger.error(f"创建设置面板失败: {e}")
            messagebox.showerror("错误", f"创建设置面板失败: {e}")
        
        # 添加确定和取消按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加应用按钮
        apply_button = ttk.Button(button_frame, text="应用", command=self._apply_settings)
        apply_button.pack(side=tk.RIGHT, padx=5)
        
        # 添加确定按钮
        save_button = ttk.Button(button_frame, text="确定", command=self._save_settings)
        save_button.pack(side=tk.RIGHT, padx=5)
        
        # 添加取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=self.window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
    def _save_settings(self):
        """保存设置并关闭窗口"""
        if self._validate_and_save_all():
            # 保存到文件
            if self.settings_manager.save_settings():
                self.window.destroy()
            else:
                messagebox.showerror("错误", "保存设置失败")
    
    def _apply_settings(self):
        """应用设置但不关闭窗口"""
        if self._validate_and_save_all():
            # 保存到文件
            if self.settings_manager.save_settings():
                # 立即应用主题变更
                try:
                    # 检查是否有外观设置变更
                    appearance_changed = False
                    for panel in self.panels:
                        if isinstance(panel, AppearanceSettingsPanel):
                            appearance_changed = True
                            break
                    
                    if appearance_changed:
                        # 调用主题应用函数
                        from pyquick import apply_theme
                        apply_theme(refresh=True)
                    
                    messagebox.showinfo("提示", "设置已应用")
                except Exception as e:
                    logger.error(f"应用设置失败: {e}")
                    messagebox.showerror("错误", f"应用设置失败: {e}")
            else:
                messagebox.showerror("错误", "应用设置失败")
    
    def _validate_and_save_all(self):
        """验证并保存所有面板的设置"""
        try:
            # 验证所有面板的设置
            for panel in self.panels:
                if hasattr(panel, 'validate') and callable(panel.validate):
                    if not panel.validate():
                        return False
            
            # 保存所有面板的设置
            for panel in self.panels:
                if hasattr(panel, 'save_settings') and callable(panel.save_settings):
                    if not panel.save_settings():
                        logger.error(f"保存设置失败: {panel.__class__.__name__}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"验证和保存设置时出错: {e}")
            messagebox.showerror("错误", f"保存设置时出错: {e}")
            return False