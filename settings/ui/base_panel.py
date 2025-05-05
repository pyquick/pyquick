"""
基础设置面板模块，提供所有设置面板的通用功能和接口
"""
import tkinter as tk
from tkinter import ttk
import logging


class BaseSettingsPanel(ttk.Frame):
    """
    基础设置面板类，所有具体的设置面板都应继承此类
    提供通用的UI创建、设置加载和保存功能
    """
    
    def __init__(self, parent, settings_manager, theme_manager=None):
        """
        初始化基础设置面板
        
        参数:
            parent: 父级窗口组件
            settings_manager: 设置管理器实例
            theme_manager: 主题管理器实例
        """
        super().__init__(parent)
        self.parent = parent
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        
        # 创建带滚动条的主容器
        self.create_scrollable_frame()
        
        # 设置UI 和 加载设置 的调用已从此移除
       #self.setup_ui()
       #self.load_settings()
        # 子类应在其 __init__ 中完成自身属性初始化后调用这些方法
       
    
    def setup_ui(self):
        """
        设置用户界面组件
        子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现setup_ui方法")
    
    def load_settings(self):
        """
        从设置管理器加载设置
        子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现load_settings方法")
    
    def save_settings(self):
        """
        保存设置到设置管理器
        子类必须实现此方法
        
        返回:
            bool: 保存是否成功
        """
        raise NotImplementedError("子类必须实现save_settings方法")
    
    def apply_theme(self):
        """
        应用当前主题到面板组件
        如果有主题管理器，会自动应用当前主题
        """
        # 默认不做任何操作，子类可以选择性地重写此方法
        pass
    
    def create_section_frame(self, title):
        """
        创建一个带标题的分节框架
        
        参数:
            title: 分节标题
            
        返回:
            tuple: (section_frame, content_frame) 分节框架和内容框架
        """
        # 创建分节框架
        section_frame = ttk.LabelFrame(self.main_container, text=title)
        section_frame.pack(fill=tk.X, expand=False, padx=5, pady=5, anchor="n")
        
        # 创建内容框架
        content_frame = ttk.Frame(section_frame)
        content_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        return section_frame, content_frame
    
    def create_labeled_entry(self, parent, label_text, variable, width=20):
        """
        创建一个带标签的输入框
        
        参数:
            parent: 父级组件
            label_text: 标签文本
            variable: 关联的变量
            width: 输入框宽度
            
        返回:
            tuple: (frame, label, entry) 框架、标签和输入框
        """
        frame = ttk.Frame(parent)
        
        label = ttk.Label(frame, text=label_text)
        label.pack(side=tk.LEFT, padx=5)
        
        entry = ttk.Entry(frame, textvariable=variable, width=width)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        return frame, label, entry
    
    def create_labeled_combobox(self, parent, label_text, variable, values, width=20):
        """
        创建一个带标签的下拉框
        
        参数:
            parent: 父级组件
            label_text: 标签文本
            variable: 关联的变量
            values: 下拉选项列表
            width: 下拉框宽度
            
        返回:
            tuple: (frame, label, combobox) 框架、标签和下拉框
        """
        frame = ttk.Frame(parent)
        
        label = ttk.Label(frame, text=label_text)
        label.pack(side=tk.LEFT, padx=5)
        
        combobox = ttk.Combobox(frame, textvariable=variable, values=values, 
                               state="readonly", width=width)
        combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        return frame, label, combobox
    
    def create_labeled_spinbox(self, parent, label_text, variable, from_=0, to=100, width=5):
        """
        创建一个带标签的数字调节框
        
        参数:
            parent: 父级组件
            label_text: 标签文本
            variable: 关联的变量
            from_: 最小值
            to: 最大值
            width: 调节框宽度
            
        返回:
            tuple: (frame, label, spinbox) 框架、标签和数字调节框
        """
        frame = ttk.Frame(parent)
        
        label = ttk.Label(frame, text=label_text)
        label.pack(side=tk.LEFT, padx=5)
        
        spinbox = ttk.Spinbox(frame, textvariable=variable, from_=from_, to=to, width=width)
        spinbox.pack(side=tk.LEFT, padx=5)
        
        return frame, label, spinbox
    
    def create_scrollable_frame(self):
        """创建可滚动的框架"""
        # 创建画布和滚动条
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # 设置画布的滚动区域
        self.main_container = ttk.Frame(self.canvas, padding=(10, 10, 5, 10))  # 左、上、右、下内边距
        self.canvas_window = self.canvas.create_window((0, 0), window=self.main_container, anchor="nw")
        
        # 配置画布滚动
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # 放置组件
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 绑定事件
        self.main_container.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # 绑定鼠标滚轮事件 - 改为仅绑定当前控件的滚轮事件
        self.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.main_container.bind("<MouseWheel>", self.on_mousewheel)
        
        # 为macOS添加触控板滚动支持
        self.bind("<Button-4>", self.on_mousewheel)
        self.bind("<Button-5>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)
        self.canvas.bind("<Button-5>", self.on_mousewheel)
        self.main_container.bind("<Button-4>", self.on_mousewheel)
        self.main_container.bind("<Button-5>", self.on_mousewheel)
    
    def on_frame_configure(self, event):
        """当框架大小改变时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def on_canvas_configure(self, event):
        """当画布大小改变时调整内部框架的宽度"""
        # 更新内部框架的宽度以匹配画布
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        # 移除对bind_all的使用，仅处理当前组件的滚轮事件
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")
        # 防止事件传播
        return "break"
    
    def create_setting_row(self, parent, label_text, widget, tooltip_text=None):
        """
        创建设置行，包含标签、控件和可选的工具提示
        
        参数:
            parent: 父级框架
            label_text: 标签文本
            widget: 要添加的控件
            tooltip_text: 工具提示文本（可选）
        """
        # 创建行框架
        row_frame = ttk.Frame(parent)
        row_frame.pack(fill=tk.X, pady=5)
        
        # 添加标签
        label = ttk.Label(row_frame, text=label_text)
        label.pack(side=tk.LEFT, padx=5)
        
        # 添加控件
        widget.pack(side=tk.RIGHT, padx=5, fill=tk.X, expand=True)
        
        # 如果有工具提示，添加图标和绑定事件
        if tooltip_text:
            self._create_tooltip(row_frame, tooltip_text)
    
    def _create_tooltip(self, parent, text):
        """
        创建工具提示
        
        参数:
            parent: 父级框架
            text: 工具提示文本
        """
        info_icon = ttk.Label(parent, text="?", cursor="question_arrow")
        info_icon.pack(side=tk.LEFT, padx=2)
        
        tooltip = tk.Toplevel(parent)
        tooltip.wm_overrideredirect(True)
        tooltip.withdraw()
        
        tooltip_label = ttk.Label(tooltip, text=text, wraplength=250, 
                                justify="left", relief="solid", borderwidth=1)
        tooltip_label.pack(ipadx=5, ipady=5)
        
        def show_tooltip(event):
            x, y, _, _ = info_icon.bbox("all")
            x += info_icon.winfo_rootx() + 25
            y += info_icon.winfo_rooty() + 25
            tooltip.wm_geometry(f"+{x}+{y}")
            tooltip.deiconify()
        
        def hide_tooltip(event):
            tooltip.withdraw()
        
        info_icon.bind("<Enter>", show_tooltip)
        info_icon.bind("<Leave>", hide_tooltip)
    
    def validate(self):
        """
        验证设置面板中的所有输入
        
        返回:
            bool: 验证是否通过
        """
        # 默认实现总是返回True
        # 子类应该根据需要重写此方法
        return True
