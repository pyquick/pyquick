import tkinter as tk
from tkinter import ttk, scrolledtext
import psutil
import os
import time
import threading
from .debug_info import get_system_info, get_memory_usage

# 尝试导入日志模块
try:
    from log import get_all_log_files, app_logger
    HAS_LOG_MODULE = True
except ImportError:
    HAS_LOG_MODULE = False
    app_logger = None

class DebugInfoWindow(tk.Toplevel):
    """系统调试信息窗口，提供系统信息、内存使用情况和日志查看功能"""

    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """单例模式实现"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self, lazy_load=True):
        """
        初始化调试信息窗口

        Args:
            lazy_load: 是否延迟加载内容（提高启动性能）
        """
        if DebugInfoWindow._initialized:
            # 如果已经初始化过，仅确保窗口显示
            self.show_window()
            return

        # 正确调用父类初始化
        tk.Toplevel.__init__(self)
        DebugInfoWindow._initialized = True

        # 基本窗口配置
        self.title("系统调试信息")
        self.geometry("800x600")
        self.minsize(600, 500)

        # 配置变量
        self.update_interval = 2000  # 默认更新间隔2秒
        self.disk_update_interval = 10  # 磁盘信息每10次更新一次
        self.disk_counter = 0
        self.progress_bar_length = 150  # 减小进度条长度
        self.current_log_path = None
        self.log_file_paths = {}
        self.auto_refresh_log = False
        self.log_refresh_job = None

        # 定义样式 (Corrected Indentation)
        self.style = ttk.Style()
        self.style.configure("Critical.TLabel", foreground="red")
        self.style.configure("Warning.TLabel", foreground="orange")
        self.style.configure("Good.TLabel", foreground="green")
        self.style.configure("Info.TLabel", foreground="blue")

        # 创建UI框架
        self.setup_ui_framework()

        if lazy_load:
            # 延迟加载内容以提高启动速度
            self.after(100, self.initialize_content)
        else:
            # 立即加载
            self.initialize_content()
            
            # 设置窗口关闭处理
            self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 确保窗口置顶显示
        self.show_window()

    def show_window(self):
        """显示窗口并置于前台"""
        self.lift()
        self.focus_force()
        self.state('normal')  # 如果被最小化则恢复

    def setup_ui_framework(self):
        """创建UI基本框架"""
        # 创建标签页控件
        self.tab_control = ttk.Notebook(self)
        self.tab_control.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 创建系统信息标签页
        self.system_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.system_tab, text='系统信息')
        self.system_tab.grid_columnconfigure(0, weight=1)
        self.system_tab.grid_rowconfigure(0, weight=1)

        # 如果有日志模块，创建日志标签页
        if HAS_LOG_MODULE:
            self.log_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(self.log_tab, text='日志信息')
            self.log_tab.grid_columnconfigure(0, weight=1)
            self.log_tab.grid_rowconfigure(0, weight=1)

    def initialize_content(self):
        """初始化内容区域"""
        # 初始化系统信息UI
        self.initialize_system_tab()

        # 如果有日志模块，初始化日志UI
        if HAS_LOG_MODULE:
            self.initialize_log_tab()

        # 开始数据更新
        self.update_data()

    def initialize_system_tab(self):
        """初始化系统信息标签页内容"""
        # 创建主框架
        main_frame = ttk.Frame(self.system_tab, padding="5")
        main_frame.grid(row=0, column=0, sticky='nsew')
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # 创建带双向滚动条的画布
        self.canvas = tk.Canvas(main_frame)

        # 垂直滚动条
        y_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)

        # 水平滚动条
        x_scrollbar = ttk.Scrollbar(main_frame, orient="horizontal", command=self.canvas.xview)

        # 配置画布
        self.canvas.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # 放置滚动条和画布
        self.canvas.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar.grid(row=1, column=0, sticky='ew')

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # 创建内容框架
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # 系统信息分组
        self.create_system_section()

        # 内存信息分组
        self.create_memory_section()

        # 进程内存分组
        self.create_process_section()

        # 磁盘信息分组
        self.create_disk_section()

        # 绑定鼠标滚轮事件
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 在窗口底部添加刷新控制
        control_frame = ttk.Frame(self.system_tab, padding="5")
        control_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)

        # 刷新按钮
        refresh_btn = ttk.Button(control_frame, text="手动刷新", command=self.update_data)
        refresh_btn.grid(row=0, column=0, padx=5)

        # 更新频率控制
        ttk.Label(control_frame, text="更新频率:").grid(row=0, column=1, padx=5)
        self.update_interval_var = tk.StringVar(value="2")
        interval_combo = ttk.Combobox(control_frame, textvariable=self.update_interval_var,
                                     values=["1", "2", "5", "10"], width=5)
        interval_combo.grid(row=0, column=2, padx=5)
        ttk.Label(control_frame, text="秒").grid(row=0, column=3)

        interval_combo.bind("<<ComboboxSelected>>", self._update_refresh_interval)

    def create_system_section(self):
        """创建系统信息部分"""
        system_group = ttk.LabelFrame(self.scrollable_frame, text="系统信息", padding="10")
        system_group.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        system_group.grid_columnconfigure(0, weight=1)

        self.system_labels = {
            "系统类型": ttk.Label(system_group),
            "处理器架构": ttk.Label(system_group),
            "芯片类型": ttk.Label(system_group),
            "CPU信息": ttk.Label(system_group),
            "CPU使用率": ttk.Label(system_group)
        }
        
        # 添加CPU使用率进度条
        self.cpu_progressbar = ttk.Progressbar(system_group, orient="horizontal",
                                              length=self.progress_bar_length,
                                              mode="determinate")
        self.cpu_progressbar.grid(row=len(self.system_labels), column=0, sticky='w', pady=2)

        # 布局系统信息标签
        for i, label in enumerate(self.system_labels.values()):
            label.grid(row=i, column=0, sticky='w', pady=2)

    def create_memory_section(self):
        """创建内存信息部分"""
        memory_group = ttk.LabelFrame(self.scrollable_frame, text="内存信息", padding="10")
        memory_group.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        memory_group.grid_columnconfigure(0, weight=1)
        
        self.memory_labels = {
            "内存总量": ttk.Label(memory_group),
            "内存使用": ttk.Label(memory_group),
            "内存可用": ttk.Label(memory_group)
        }
        
        # 添加内存使用率进度条
        self.memory_progressbar = ttk.Progressbar(memory_group, orient="horizontal",
                                                 length=self.progress_bar_length,
                                                 mode="determinate")
        self.memory_progressbar.grid(row=len(self.memory_labels), column=0, sticky='w', pady=2)

        # 布局内存信息标签
        for i, label in enumerate(self.memory_labels.values()):
            label.grid(row=i, column=0, sticky='w', pady=2)
        
    def create_process_section(self):
        """创建进程内存部分"""
        process_group = ttk.LabelFrame(self.scrollable_frame, text="进程内存", padding="10")
        process_group.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        process_group.grid_columnconfigure(0, weight=1)
        
        self.process_labels = {
            "物理内存": ttk.Label(process_group),
            "虚拟内存": ttk.Label(process_group),
            "进程占用": ttk.Label(process_group)
        }
        
        # 添加进程内存使用率进度条
        self.process_progressbar = ttk.Progressbar(process_group, orient="horizontal",
                                                  length=self.progress_bar_length,
                                                  mode="determinate")
        self.process_progressbar.grid(row=len(self.process_labels), column=0, sticky='w', pady=2)

        # 布局进程内存标签
        for i, label in enumerate(self.process_labels.values()):
            label.grid(row=i, column=0, sticky='w', pady=2)

    def create_disk_section(self):
        """创建磁盘信息部分"""
        # 磁盘信息大框架
        self.disk_main_frame = ttk.LabelFrame(self.scrollable_frame, text="磁盘信息", padding="10")
        self.disk_main_frame.grid(row=3, column=0, sticky='ew', padx=5, pady=5)
        self.disk_main_frame.grid_columnconfigure(0, weight=1)

        # 磁盘信息分组
        self.disk_group = ttk.Frame(self.disk_main_frame)
        self.disk_group.grid(row=0, column=0, sticky='ew')
        self.disk_group.grid_columnconfigure(0, weight=1)

        self.disk_labels = {}
        self.disk_progressbars = {}

    def initialize_log_tab(self):
        """初始化日志信息标签页内容"""
        # 创建日志显示框架
        log_frame = ttk.Frame(self.log_tab)
        log_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        # 创建日志文件选择下拉框
        select_frame = ttk.Frame(log_frame)
        select_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        select_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(select_frame, text="选择日志文件:").grid(row=0, column=0, padx=5)

        self.log_file_var = tk.StringVar()
        self.log_combo = ttk.Combobox(select_frame, textvariable=self.log_file_var, state="readonly", width=50)
        self.log_combo.grid(row=0, column=1, padx=5, sticky='ew')

        refresh_log_btn = ttk.Button(select_frame, text="刷新文件列表", command=self.refresh_log_files)
        refresh_log_btn.grid(row=0, column=2, padx=5)

        # 创建日志内容文本框和双向滚动条
        log_content_frame = ttk.LabelFrame(log_frame, text="日志内容")
        log_content_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        log_content_frame.grid_columnconfigure(0, weight=1)
        log_content_frame.grid_rowconfigure(0, weight=1)

        # 创建带两个滚动条的文本框框架
        text_frame = ttk.Frame(log_content_frame)
        text_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        # 创建文本框和滚动条
        self.log_text = tk.Text(text_frame, wrap=tk.NONE, background='white',
                              font=('Consolas', 10))

        y_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        x_scrollbar = ttk.Scrollbar(text_frame, orient="horizontal", command=self.log_text.xview)

        self.log_text.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # 放置文本框和滚动条
        self.log_text.grid(row=0, column=0, sticky='nsew')
        y_scrollbar.grid(row=0, column=1, sticky='ns')
        x_scrollbar.grid(row=1, column=0, sticky='ew')

        # 创建按钮框架
        button_frame = ttk.Frame(log_frame)
        button_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=5)

        view_btn = ttk.Button(button_frame, text="查看日志", command=self.view_log)
        view_btn.grid(row=0, column=0, padx=5)

        refresh_btn = ttk.Button(button_frame, text="刷新内容", command=self.refresh_log_content)
        refresh_btn.grid(row=0, column=1, padx=5)

        # 创建自动刷新选项
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_check = ttk.Checkbutton(button_frame, text="自动刷新",
                                           variable=self.auto_refresh_var,
                                           command=self.toggle_auto_refresh)
        auto_refresh_check.grid(row=0, column=2, padx=5)

        # 添加日志过滤功能
        filter_frame = ttk.Frame(button_frame)
        filter_frame.grid(row=0, column=3, padx=10)

        ttk.Label(filter_frame, text="过滤:").grid(row=0, column=0, padx=2)
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=15)
        filter_entry.grid(row=0, column=1, padx=2)

        filter_btn = ttk.Button(filter_frame, text="应用", command=self.apply_log_filter)
        filter_btn.grid(row=0, column=2, padx=2)

        clear_btn = ttk.Button(filter_frame, text="清除", command=lambda: self.filter_var.set("") or self.apply_log_filter())
        clear_btn.grid(row=0, column=3, padx=2)

        # 初始化日志文件列表
        self.refresh_log_files()

        # 绑定选择事件
        self.log_combo.bind("<<ComboboxSelected>>", lambda e: self.view_log())

        # 添加快捷键
        self.log_text.bind("<Control-f>", lambda e: filter_entry.focus_set())

    def toggle_auto_refresh(self):
        """切换自动刷新日志功能"""
        self.auto_refresh = self.auto_refresh_var.get()

        if self.auto_refresh:
            # 如果启用自动刷新，则每5秒刷新一次
            self.schedule_log_refresh()
        elif self.log_refresh_job:
            # 如果禁用自动刷新，则取消定时任务
            self.after_cancel(self.log_refresh_job)
            self.log_refresh_job = None

    def schedule_log_refresh(self):
        """安排下一次日志刷新"""
        if self.auto_refresh:
            self.refresh_log_content()
            self.log_refresh_job = self.after(5000, self.schedule_log_refresh)

    def apply_log_filter(self):
        """应用日志过滤器"""
        self.refresh_log_content()

    def refresh_log_files(self):
        """刷新日志文件列表"""
        if not HAS_LOG_MODULE:
            return

        try:
            log_files = get_all_log_files()

            # 提取文件名（不含路径）
            file_names = []
            self.log_file_paths = {}

            for path in log_files:
                name = os.path.basename(path)
                file_names.append(name)
                self.log_file_paths[name] = path

            # 按修改时间排序（最新的在前面）
            file_names.sort(key=lambda x: os.path.getmtime(self.log_file_paths[x]), reverse=True)

            # 更新下拉框
            self.log_combo['values'] = file_names

            # 如果有日志文件，默认选择第一个
            if file_names:
                self.log_combo.current(0)
                self.view_log()

        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"获取日志文件出错: {str(e)}")

    def view_log(self):
        """查看所选日志文件内容"""
        if not HAS_LOG_MODULE:
            return

        selected = self.log_file_var.get()
        if not selected or selected not in self.log_file_paths:
            return

        try:
            log_path = self.log_file_paths[selected]
            self.current_log_path = log_path
            self.refresh_log_content()

        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"读取日志文件出错: {str(e)}")

    def refresh_log_content(self):
        """刷新日志内容"""
        if not hasattr(self, 'current_log_path') or not self.current_log_path:
            return

        try:
            # 读取日志文件内容
            if os.path.exists(self.current_log_path):
                with open(self.current_log_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 应用过滤器
                filter_text = self.filter_var.get().strip()
                if filter_text:
                    # 保留包含过滤文本的行
                    filtered_lines = [line for line in content.splitlines()
                                     if filter_text.lower() in line.lower()]
                    content = '\n'.join(filtered_lines) if filtered_lines else f"没有包含 '{filter_text}' 的行"

                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, content)

                # 滚动到底部
                self.log_text.see(tk.END)

                # 高亮过滤关键字
                if filter_text:
                    self.highlight_text(filter_text)

        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"刷新日志内容出错: {str(e)}")

    def highlight_text(self, text):
        """高亮显示文本中的关键字"""
        if not text:
            return

        # 配置高亮标签
        self.log_text.tag_configure("highlight", background="yellow", foreground="black")

        # 搜索并高亮所有匹配
        start_pos = "1.0"
        while True:
            start_pos = self.log_text.search(text, start_pos, tk.END, nocase=1)
            if not start_pos:
                break

            end_pos = f"{start_pos}+{len(text)}c"
            self.log_text.tag_add("highlight", start_pos, end_pos)
            start_pos = end_pos

    def get_style_by_percent(self, percent):
        """根据百分比返回对应的样式"""
        try:
            value = float(percent.strip('%'))
            if value >= 90:
                return "Critical.TLabel"
            elif value >= 70:
                return "Warning.TLabel"
            elif value >= 0:
                return "Good.TLabel"
        except (ValueError, AttributeError):
            pass
        return "Info.TLabel"

    def update_data(self):
        """更新显示数据"""
        try:
            # 更新CPU和内存信息
            self.update_system_info()

            # 根据计数器决定是否更新磁盘信息（减少I/O操作）
            self.disk_counter += 1
            if self.disk_counter >= self.disk_update_interval:
                self.update_disk_info()
                self.disk_counter = 0

            # 安排下一次更新
            interval_ms = int(float(self.update_interval_var.get()) * 1000)
            self._update_job = self.after(interval_ms, self.update_data)

        except Exception as e:
            if app_logger:
                app_logger.error(f"更新系统信息时发生错误: {e}")
            else:
                print(f"更新系统信息时发生错误: {e}")
            # 发生错误时，尝试在2秒后重新更新
            self._update_job = self.after(2000, self.update_data)

    def update_system_info(self):
        """更新系统和内存信息（分离磁盘更新以提高性能）"""
        # Corrected Indentation
        system_data = get_system_info()
        mem_usage = get_memory_usage()
        
        # 更新系统信息
        cpu_usage = float(system_data['CPU使用率'].strip('%'))
        self.system_labels["系统类型"].config(
            text=f"系统类型: {system_data['系统类型']}", 
            style="Info.TLabel"
        )
        self.system_labels["处理器架构"].config(
            text=f"处理器架构: {system_data['处理器架构']}", 
            style="Info.TLabel"
        )
        self.system_labels["芯片类型"].config(
            text=f"芯片类型: {system_data['Mac芯片类型']}", 
            style="Info.TLabel"
        )
        self.system_labels["CPU信息"].config(
            text=f"CPU信息: {system_data['物理核心数']} 物理核心 / {system_data['逻辑核心数']} 逻辑核心", 
            style="Info.TLabel"
        )
        self.system_labels["CPU使用率"].config(
            text=f"CPU使用率: {system_data['CPU使用率']}", 
            style=self.get_style_by_percent(system_data['CPU使用率'])
        )
        self.cpu_progressbar['value'] = cpu_usage
        
        # 更新内存信息
        mem_info = system_data['内存信息']
        mem_usage_percent = float(mem_info['使用率'].strip('%'))
        self.memory_labels["内存总量"].config(
            text=f"内存总量: {mem_info['总量']}", 
            style="Info.TLabel"
        )
        self.memory_labels["内存使用"].config(
            text=f"已用内存: {mem_info['已用']} ({mem_info['使用率']})", 
            style=self.get_style_by_percent(mem_info['使用率'])
        )
        self.memory_labels["内存可用"].config(
            text=f"可用内存: {mem_info['可用']}", 
            style="Good.TLabel"
        )
        self.memory_progressbar['value'] = mem_usage_percent
        
        # 更新进程内存信息
        process_usage_percent = float(mem_usage['内存占用率'].strip('%'))
        self.process_labels["物理内存"].config(
            text=f"物理内存: {mem_usage['物理内存']}", 
            style="Info.TLabel"
        )
        self.process_labels["虚拟内存"].config(
            text=f"虚拟内存: {mem_usage['虚拟内存']}", 
            style="Info.TLabel"
        )
        self.process_labels["进程占用"].config(
            text=f"占用率: {mem_usage['内存占用率']}", 
            style=self.get_style_by_percent(mem_usage['内存占用率'])
        )
        self.process_progressbar['value'] = process_usage_percent
            
    def update_disk_info(self):
        """单独更新磁盘信息（I/O密集，降低频率）"""
        # Corrected In  dentation
        system_data = get_system_info()
            
            # 更新磁盘信息
        for i, (mountpoint, info) in enumerate(system_data['磁盘使用'].items()):
            # Corrected Indentation
            if mountpoint not in self.disk_labels:
                # 创建新的磁盘行 (Corrected Indentation)
                disk_frame = ttk.Frame(self.disk_group)
                disk_frame.grid(row=i, column=0, sticky='ew', padx=5, pady=2)
                disk_frame.grid_columnconfigure(0, weight=1)
                
                self.disk_labels[mountpoint] = ttk.Label(disk_frame)
                self.disk_labels[mountpoint].grid(row=0, column=0, sticky='w')
                
                self.disk_progressbars[mountpoint] = ttk.Progressbar(
                    disk_frame, orient="horizontal",
                    length=self.progress_bar_length,
                    mode="determinate"
                )
                self.disk_progressbars[mountpoint].grid(row=1, column=0, sticky='w', pady=2)
                
        # 更新现有磁盘信息 (Corrected Indentation - aligned with 'if')
                disk_usage_percent = float(info['使用率'].strip('%'))
                self.disk_labels[mountpoint].config(
                    text=f"{mountpoint}: 总空间{info['总空间']}, "
                         f"已用{info['已用']}, 可用{info['可用']} "
                         f"(使用率{info['使用率']})",
                    style=self.get_style_by_percent(info['使用率'])
                )
        # Ensure progressbar exists before setting value
        if mountpoint in self.disk_progressbars:
                self.disk_progressbars[mountpoint]['value'] = disk_usage_percent
            
    def _on_mousewheel(self, event):
        """处理鼠标滚轮事件"""
        try:
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                # 根据平台决定滚动方向
                if event.num == 5 or event.delta < 0:
                    self.canvas.yview_scroll(1, "units")
                elif event.num == 4 or event.delta > 0:
                    self.canvas.yview_scroll(-1, "units")
        except Exception as e:
            if app_logger:
                app_logger.error(f"鼠标滚轮事件处理失败: {e}")

    def _update_refresh_interval(self, event=None):
        """更新刷新频率"""
        try:
            # 如果有正在进行的更新，先取消
            if hasattr(self, '_update_job'):
                self.after_cancel(self._update_job)

            # 立即更新一次
            self.update_data()
        except:
            pass

    def on_closing(self):
        """处理窗口关闭事件"""
        # 停止更新定时器
        if hasattr(self, '_update_job'):
            self.after_cancel(self._update_job)

        # 停止日志自动刷新
        if self.log_refresh_job:
            self.after_cancel(self.log_refresh_job)

        # 销毁窗口
        self.destroy()

    def destroy(self):
        """重写destroy方法以便清理单例实例"""
        try:
            # 解绑鼠标滚轮事件
            if hasattr(self, 'canvas'):
                self.canvas.unbind_all("<MouseWheel>")
        except Exception as e:
            if app_logger:
                app_logger.error(f"解绑事件失败: {e}")
        
        # 清理单例实例
        DebugInfoWindow._initialized = False
        
        # 调用父类销毁方法
        super().destroy()
