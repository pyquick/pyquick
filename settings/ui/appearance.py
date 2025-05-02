"""
外观设置面板，提供主题、字体和样式设置
"""
import tkinter as tk
from tkinter import ttk
import logging

from settings.ui.base_panel import BaseSettingsPanel

class AppearanceSettingsPanel(BaseSettingsPanel):
    """
    外观设置面板类，管理应用程序主题、字体和样式设置
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化外观设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        # 初始化变量
        self.theme_var = tk.StringVar()
        self.font_size_var = tk.IntVar()
        self.custom_font_var = tk.StringVar()
        self.use_custom_font_var = tk.BooleanVar()
        self.enable_animations_var = tk.BooleanVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置外观设置面板的用户界面"""
        # 主题设置
        theme_section, theme_content = self.create_section_frame("主题设置")
        
        # 主题选择
        theme_frame = ttk.Frame(theme_content)
        theme_frame.pack(fill=tk.X, pady=5)
        
        theme_label = ttk.Label(theme_frame, text="应用主题:")
        theme_label.pack(side=tk.LEFT, padx=5)
        
        # 获取可用主题
        available_themes = ["默认主题", "暗黑模式", "经典模式"]
        if self.theme_manager:
            try:
                manager_themes = self.theme_manager.get_available_themes()
                if manager_themes:
                    available_themes = manager_themes
            except Exception as e:
                logging.error(f"获取主题列表失败: {e}")
        
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                  values=available_themes, state="readonly")
        theme_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 预览主题按钮
        preview_button = ttk.Button(theme_frame, text="预览", 
                                   command=self._preview_theme)
        preview_button.pack(side=tk.LEFT, padx=5)
        
        # 字体设置
        font_section, font_content = self.create_section_frame("字体设置")
        
        # 字体大小
        font_size_frame, _, font_size_spinbox = self.create_labeled_spinbox(
            font_content, "界面字体大小:", self.font_size_var, from_=8, to=24)
        font_size_frame.pack(fill=tk.X, pady=5)
        
        # 自定义字体
        custom_font_frame = ttk.Frame(font_content)
        custom_font_frame.pack(fill=tk.X, pady=5)
        
        custom_font_check = ttk.Checkbutton(custom_font_frame, text="使用自定义字体", 
                                           variable=self.use_custom_font_var,
                                           command=self._toggle_custom_font)
        custom_font_check.pack(side=tk.LEFT, padx=5)
        
        custom_font_entry = ttk.Entry(custom_font_frame, textvariable=self.custom_font_var)
        custom_font_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 可用字体查看按钮
        font_button = ttk.Button(custom_font_frame, text="可用字体", 
                                command=self._show_available_fonts)
        font_button.pack(side=tk.LEFT, padx=5)
        
        # 界面效果
        effect_section, effect_content = self.create_section_frame("界面效果")
        
        # 启用动画
        animation_frame = ttk.Frame(effect_content)
        animation_frame.pack(fill=tk.X, pady=5)
        
        animation_check = ttk.Checkbutton(animation_frame, text="启用界面动画效果", 
                                         variable=self.enable_animations_var)
        animation_check.pack(side=tk.LEFT, padx=5)
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 主题设置
            current_theme = self.settings_manager.get("theme.current", "默认主题")
            self.theme_var.set(current_theme)
            
            # 字体设置
            self.font_size_var.set(self.settings_manager.get("theme.font_size", 12))
            self.use_custom_font_var.set(self.settings_manager.get("theme.use_custom_font", False))
            self.custom_font_var.set(self.settings_manager.get("theme.custom_font", ""))
            
            # 界面效果
            self.enable_animations_var.set(self.settings_manager.get("theme.enable_animations", True))
            
            # 更新界面状态
            self._toggle_custom_font()
            
            logging.debug("外观设置加载成功")
        except Exception as e:
            logging.error(f"加载外观设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 主题设置
            self.settings_manager.set("theme.current", self.theme_var.get())
            
            # 字体设置
            self.settings_manager.set("theme.font_size", self.font_size_var.get())
            self.settings_manager.set("theme.use_custom_font", self.use_custom_font_var.get())
            self.settings_manager.set("theme.custom_font", self.custom_font_var.get())
            
            # 界面效果
            self.settings_manager.set("theme.enable_animations", self.enable_animations_var.get())
            
            logging.debug("外观设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存外观设置时出错: {e}")
            return False
    
    def _toggle_custom_font(self):
        """切换自定义字体选项的启用状态"""
        for child in self.winfo_children():
            if isinstance(child, ttk.Frame):
                for widget in child.winfo_children():
                    if isinstance(widget, ttk.Entry) and widget.cget("textvariable").endswith("custom_font_var"):
                        if self.use_custom_font_var.get():
                            widget.configure(state="normal")
                        else:
                            widget.configure(state="disabled")
    
    def _preview_theme(self):
        """预览选中的主题"""
        if self.theme_manager:
            try:
                theme_name = self.theme_var.get()
                self.theme_manager.set_theme(theme_name, preview=True)
                logging.debug(f"预览主题: {theme_name}")
            except Exception as e:
                logging.error(f"预览主题失败: {e}")
    
    def _show_available_fonts(self):
        """显示系统可用字体列表"""
        try:
            from tkinter import font
            import tkinter.simpledialog as simpledialog
            
            # 获取可用字体
            available_fonts = sorted(font.families())
            
            # 创建一个新窗口显示字体列表
            font_window = tk.Toplevel(self)
            font_window.title("可用字体")
            font_window.geometry("400x500")
            font_window.transient(self.parent)
            font_window.grab_set()
            
            # 创建滚动列表
            font_frame = ttk.Frame(font_window)
            font_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(font_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            font_list = tk.Listbox(font_frame, yscrollcommand=scrollbar.set)
            font_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=font_list.yview)
            
            # 添加字体到列表
            for f in available_fonts:
                font_list.insert(tk.END, f)
            
            # 双击选择字体
            def on_font_select(event):
                selected_index = font_list.curselection()
                if selected_index:
                    selected_font = font_list.get(selected_index[0])
                    self.custom_font_var.set(selected_font)
                    font_window.destroy()
            
            font_list.bind("<Double-1>", on_font_select)
            
            # 关闭按钮
            close_button = ttk.Button(font_window, text="关闭", 
                                     command=font_window.destroy)
            close_button.pack(pady=10)
            
        except Exception as e:
            logging.error(f"显示字体列表失败: {e}") 