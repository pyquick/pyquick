import tkinter as tk
from tkinter import ttk
import psutil
from .system import get_system_info, get_memory_usage

class DebugInfoWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("系统调试信息")
        self.geometry("400x300")
        self.initUI()
        self.update_data()

    def initUI(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True)

        # 系统信息标签
        self.system_labels = {
            "芯片类型": ttk.Label(main_frame),
            "核心数": ttk.Label(main_frame),
            "内存总量": ttk.Label(main_frame),
            "磁盘使用": ttk.Label(main_frame)
        }
        
        # 内存监控标签
        self.mem_label = ttk.Label(main_frame)
        
        # 刷新按钮
        refresh_btn = ttk.Button(main_frame, text="手动刷新", command=self.update_data)
        
        # 布局组件
        for label in self.system_labels.values():
            label.pack(anchor='w')
        self.mem_label.pack(anchor='w')
        refresh_btn.pack(side='bottom', pady=5)

    def update_data(self):
        system_data = get_system_info()
        self.system_labels["芯片类型"].config(text=f"处理器架构: {system_data['Mac芯片类型']}")
        self.system_labels["核心数"].config(
            text=f"核心数: {system_data['物理核心数']} 物理 / {system_data['逻辑核心数']} 逻辑")
        self.system_labels["内存总量"].config(text=f"内存总量: {system_data['内存总量']}")
        self.system_labels["磁盘使用"].config(
            text="磁盘使用: " + ", ".join([f"{k}: {v}" for k,v in system_data['磁盘使用'].items()]))
        
        self.mem_label.config(text=f"当前内存占用: {get_memory_usage()}")
        self.after(1000, self.update_data)