"""
设置窗口主类，包含所有设置面板和控件
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import logging

# 尝试导入sv_ttk主题包
try:
    import sv_ttk
except ImportError:
    logging.warning("sv_ttk未安装，将使用默认主题")

class SettingsWindow:
    """设置窗口类，管理所有设置面板"""
    
    def __init__(self, parent, settings_manager, theme_manager):
        """
        初始化设置窗口
        
        参数:
            parent: 父窗口
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        self.parent = parent
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        
        # 创建一个新的顶层窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.resizable(True, True)
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        # 确保窗口在屏幕中央
        self.center_window()
        
        # 初始化界面
        self.setup_ui()
        
        # 应用当前主题 - 先应用主题再初始化组件
        self.apply_theme()
        
        # 设置窗口为模态（阻止与其他窗口的交互直到此窗口关闭）
        self.window.transient(parent)
        self.window.grab_set()
        self.window.focus_set()
    
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        # 增加窗口初始大小
        width = 900
        height = 700
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # 计算窗口的x,y坐标
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 设置窗口位置和初始大小
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # 等待UI完成初始化后再更新
        self.window.update_idletasks()
        
        # 设置合理的最小大小，确保按钮可见
        min_width = 800
        min_height = 600
        self.window.minsize(min_width, min_height)
    
    def setup_ui(self):
        """设置用户界面"""
        # 设置窗口的行列配置
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)  # 让内容区域可以拉伸
        self.window.rowconfigure(1, weight=0)  # 按钮区域不拉伸
        
        # 创建内容区域框架
        content_frame = ttk.Frame(self.window, padding=5)
        content_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 存储所有设置面板的引用
        self.panels = {}
        
        # 添加通用设置面板
        from settings.ui.general import GeneralSettingsPanel
        general_panel = GeneralSettingsPanel(self.notebook, self.settings_manager, self.theme_manager)
        self.notebook.add(general_panel, text="通用")
        self.panels['general'] = general_panel
        
        # 添加外观设置面板
        from settings.ui.appearance import AppearanceSettingsPanel
        appearance_panel = AppearanceSettingsPanel(self.notebook, self.settings_manager, self.theme_manager)
        self.notebook.add(appearance_panel, text="外观")
        self.panels['appearance'] = appearance_panel
        
        # 添加下载设置面板
        from settings.ui.download import DownloadSettingsPanel
        download_panel = DownloadSettingsPanel(self.notebook, self.settings_manager)
        self.notebook.add(download_panel, text="下载")
        self.panels['download'] = download_panel
        
        # 添加代理设置面板
        from settings.ui.proxy import ProxySettingsPanel
        proxy_panel = ProxySettingsPanel(self.notebook, self.settings_manager)
        self.notebook.add(proxy_panel, text="代理")
        self.panels['proxy'] = proxy_panel
        
        # 添加Python设置面板
        from settings.ui.python import PythonSettingsPanel
        python_panel = PythonSettingsPanel(self.notebook, self.settings_manager)
        self.notebook.add(python_panel, text="Python")
        self.panels['python'] = python_panel
        
        # 添加高级设置面板
        from settings.ui.advanced import AdvancedSettingsPanel
        advanced_panel = AdvancedSettingsPanel(self.notebook, self.settings_manager)
        self.notebook.add(advanced_panel, text="高级")
        self.panels['advanced'] = advanced_panel
        
        # 底部按钮框架
        button_frame = ttk.Frame(self.window, padding=5)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        button_frame.columnconfigure(0, weight=1)  # 让左侧占据空间
        
        # 保存按钮
        self.save_button = ttk.Button(
            button_frame, 
            text="保存",
            command=self.on_save,
            style="Accent.TButton"
        )
        self.save_button.grid(row=0, column=3, padx=5)
        
        # 取消按钮
        self.cancel_button = ttk.Button(
            button_frame, 
            text="取消",
            command=self.on_cancel
        )
        self.cancel_button.grid(row=0, column=2, padx=5)
        
        # 应用按钮
        self.apply_button = ttk.Button(
            button_frame, 
            text="应用",
            command=self.on_apply
        )
        self.apply_button.grid(row=0, column=1, padx=5)
        
        # 添加一个空的标签作为空间填充
        spacer = ttk.Label(button_frame, text="")
        spacer.grid(row=0, column=0, sticky="w")
    
    def apply_theme(self):
        """应用当前主题到所有组件"""
        try:
            # 获取当前主题
            current_theme = self.theme_manager.get_current_theme()
            theme_type = "light"  # 默认亮色主题
            
            # 获取主题类型，支持不同的主题数据结构
            if isinstance(current_theme, dict):
                # 尝试从不同可能的键获取主题类型
                theme_type = current_theme.get('type', 
                            current_theme.get('mode', 
                            current_theme.get('theme_type', 'light')))
            
            # 确保类型是合法的
            if theme_type not in ["light", "dark"]:
                theme_type = "light"
                
            # 如果使用sv_ttk，应用对应的主题
            if 'sv_ttk' in sys.modules:
                import sv_ttk
                sv_ttk.set_theme(theme_type)
                logging.info(f"已应用sv_ttk主题: {theme_type}")
            
            # 应用主题到各个面板
            for panel_name, panel in self.panels.items():
                if hasattr(panel, 'apply_theme'):
                    try:
                        panel.apply_theme()
                    except Exception as e:
                        logging.error(f"应用主题到面板 {panel_name} 失败: {e}")
        except Exception as e:
            logging.error(f"应用主题时出错: {e}")
    
    def on_save(self):
        """保存所有设置并关闭窗口"""
        try:
            # 收集各个面板的设置
            for panel_name, panel in self.panels.items():
                if hasattr(panel, 'save_settings'):
                    panel.save_settings()
            
            # 保存设置到文件
            self.settings_manager.save_settings()
            logging.info("设置已保存")
            
            # 关闭窗口
            self.window.destroy()
        except Exception as e:
            logging.error(f"保存设置时出错: {e}")
            messagebox.showerror("保存失败", f"无法保存设置: {e}")
    
    def on_apply(self):
        """应用设置但不关闭窗口"""
        try:
            # 收集各个面板的设置
            for panel_name, panel in self.panels.items():
                if hasattr(panel, 'save_settings'):
                    panel.save_settings()
            
            # 保存设置到文件
            self.settings_manager.save_settings()
            logging.info("设置已应用")
            
            # 通知主窗口应用新设置
            if hasattr(self.parent, 'apply_settings'):
                self.parent.apply_settings()
                
        except Exception as e:
            logging.error(f"应用设置时出错: {e}")
            messagebox.showerror("应用失败", f"无法应用设置: {e}")
    
    def on_cancel(self):
        """取消设置并关闭窗口"""
        self.window.destroy() 