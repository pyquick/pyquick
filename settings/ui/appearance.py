"""
外观设置面板，用于管理应用程序的主题和视觉效果
"""
import tkinter as tk
from tkinter import ttk, colorchooser
import logging

from settings.ui.base_panel import BaseSettingsPanel

class AppearanceSettingsPanel(BaseSettingsPanel):
    """
    外观设置面板类，管理应用程序主题和视觉外观
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
        self.custom_accent_var = tk.BooleanVar()
        self.accent_color_var = tk.StringVar()
        
        # 调用父类初始化方法
        super().__init__(parent, settings_manager, theme_manager)
    
    def setup_ui(self):
        """设置外观设置面板的用户界面"""
        # 主题设置
        theme_section, theme_content = self.create_section_frame("主题设置")
        
        # 主题选择
        themes = [
            "系统默认", 
            "浅色", 
            "深色", 
            "蓝色", 
            "绿色", 
            "彩色", 
            "灰色", 
            "科技感", 
            "简约"
        ]
        theme_frame, _, theme_combo = self.create_labeled_combobox(
            theme_content, "界面主题:", self.theme_var, themes)
        theme_frame.pack(fill=tk.X, pady=5)
        
        # 主题说明
        theme_tip = ttk.Label(
            theme_content, 
            text="注: 主题变更将在重启应用后生效", 
            font=("", 9), 
            foreground="grey"
        )
        theme_tip.pack(anchor=tk.W, padx=5, pady=2)
        
        # 字体设置
        font_section, font_content = self.create_section_frame("字体设置")
        
        # 字体大小
        font_sizes = [9, 10, 11, 12, 13, 14, 16, 18]
        font_frame, _, font_combo = self.create_labeled_combobox(
            font_content, "字体大小:", self.font_size_var, [str(size) for size in font_sizes])
        font_frame.pack(fill=tk.X, pady=5)
        
        # 字体说明
        font_tip = ttk.Label(
            font_content, 
            text="注: 字体大小变更将在重启应用后生效", 
            font=("", 9), 
            foreground="grey"
        )
        font_tip.pack(anchor=tk.W, padx=5, pady=2)
        
        # 自定义颜色设置
        color_section, color_content = self.create_section_frame("颜色设置")
        
        # 自定义强调色
        custom_frame = ttk.Frame(color_content)
        custom_frame.pack(fill=tk.X, pady=5)
        
        custom_check = ttk.Checkbutton(custom_frame, text="使用自定义强调色", 
                                      variable=self.custom_accent_var, 
                                      command=self._toggle_color_selector)
        custom_check.pack(side=tk.LEFT, padx=5)
        
        # 颜色选择区域
        color_frame = ttk.Frame(color_content)
        color_frame.pack(fill=tk.X, pady=5)
        
        color_label = ttk.Label(color_frame, text="强调色:")
        color_label.pack(side=tk.LEFT, padx=5)
        
        # 颜色输入框
        color_entry = ttk.Entry(color_frame, textvariable=self.accent_color_var, width=10)
        color_entry.pack(side=tk.LEFT, padx=5)
        
        # 颜色预览框
        self.color_preview = tk.Frame(color_frame, width=20, height=20, bd=1, relief=tk.SUNKEN)
        self.color_preview.pack(side=tk.LEFT, padx=5)
        
        # 选择颜色按钮
        color_button = ttk.Button(color_frame, text="选择颜色", command=self._choose_color)
        color_button.pack(side=tk.LEFT, padx=5)
        
        # 颜色说明
        color_tip = ttk.Label(
            color_content, 
            text="注: 自定义强调色功能尚处于开发中，当前可能不会完全生效", 
            font=("", 9), 
            foreground="grey"
        )
        color_tip.pack(anchor=tk.W, padx=5, pady=2)
        
        # 保存实例变量
        self.color_frame = color_frame
        self.color_entry = color_entry
        self.color_button = color_button
        
        # 自定义强调色状态设置
        self._toggle_color_selector()
    
    def _toggle_color_selector(self):
        """切换颜色选择器的启用状态"""
        if self.custom_accent_var.get():
            self.color_entry.configure(state="normal")
            self.color_button.configure(state="normal")
            self._update_color_preview()
        else:
            self.color_entry.configure(state="disabled")
            self.color_button.configure(state="disabled")
    
    def _choose_color(self):
        """打开颜色选择器"""
        color_code = colorchooser.askcolor(initialcolor=self.accent_color_var.get() or "#1a73e8")
        if color_code[1]:  # 如果用户选择了颜色(而不是取消)
            self.accent_color_var.set(color_code[1])
            self._update_color_preview()
    
    def _update_color_preview(self):
        """更新颜色预览"""
        try:
            color = self.accent_color_var.get()
            if color:
                self.color_preview.configure(bg=color)
        except Exception as e:
            logging.error(f"更新颜色预览失败: {e}")
    
    def load_settings(self):
        """从设置管理器加载设置"""
        try:
            # 主题设置
            self.theme_var.set(self.settings_manager.get("appearance.theme", "系统默认"))
            
            # 字体设置
            self.font_size_var.set(str(self.settings_manager.get("appearance.font_size", 12)))
            
            # 颜色设置
            self.custom_accent_var.set(self.settings_manager.get("appearance.use_custom_accent", False))
            self.accent_color_var.set(self.settings_manager.get("appearance.custom_accent_color", "#1a73e8"))
            
            # 更新UI
            self._toggle_color_selector()
            self._update_color_preview()
            
            logging.debug("外观设置加载成功")
        except Exception as e:
            logging.error(f"加载外观设置时出错: {e}")
    
    def save_settings(self):
        """保存设置到设置管理器"""
        try:
            # 主题设置
            self.settings_manager.set("appearance.theme", self.theme_var.get())
            
            # 字体设置
            self.settings_manager.set("appearance.font_size", int(self.font_size_var.get()))
            
            # 颜色设置
            self.settings_manager.set("appearance.use_custom_accent", self.custom_accent_var.get())
            self.settings_manager.set("appearance.custom_accent_color", self.accent_color_var.get())
            
            logging.debug("外观设置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存外观设置时出错: {e}")
            return False 