"""
PyQuick - Python安装与管理工具
主窗口模块

负责创建和管理应用程序的主窗口
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import logging

# 添加父目录到模块搜索路径
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# 导入自定义模块
from log import get_logger
from lang import get_text, set_language, update_interface_language
from ui.settings_window import settings1
from ui.debug_window import show_debug_info
from ui.about_window import show_about
from utils import safe_config, safe_grid, safe_grid_forget, safe_ui_update, read_config, write_config

# 导入镜像测试模块
try:
    from mirror_test import show_mirror_test_window
except ImportError:
    def show_mirror_test_window(*args, **kwargs):
        messagebox.showerror(get_text("error"), "无法导入mirror_test模块")

# 导入其他功能模块
from modules.pip_manager import show_pip_version, retry_pip_ui
from modules.download_manager import download_selected_version, cancel_download, pause_resume_download
from modules.version_manager import python_version_reload

# 获取日志记录器
logger = get_logger()

# 全局变量
root = None
config_path = None
settings = {}
app_running = True

# 各种UI组件
download_frame = None
pip_frame = None
version_combobox = None
download_file_combobox = None
destination_entry = None
thread_combobox = None
download_button = None
cancel_button = None
pause_button = None
status_label = None
progress_bar = None
pip_upgrade_button = None
package_entry = None
install_button = None
uninstall_button = None
upgrade_button = None
pip_retry_button = None
package_status_label = None
pip_progress_bar = None
thread_label = None

def initialize_paths():
    """初始化配置路径"""
    global config_path
    version_pyquick = "2020"
    config_path_base = os.path.join(os.environ["APPDATA"], "pyquick")
    config_path = os.path.join(config_path_base, version_pyquick)
    
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    
    return config_path

def setup_menu():
    """设置菜单栏"""
    global root
    
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    
    # 添加菜单项
    help_menu = tk.Menu(menubar, tearoff=0)
    settings_menu = tk.Menu(menubar, tearoff=0)
    
    safe_config(menubar, tearoff=0, add_cascade=True, label=get_text("settings_menu"), menu=settings_menu)
    safe_config(menubar, tearoff=0, add_cascade=True, label=get_text("help_menu"), menu=help_menu)

    help_menu.add_command(label=get_text("about"), command=show_about)
    help_menu.add_separator()
    help_menu.add_command(label=get_text("debug_info"), command=show_debug_info)
    
    # 添加设置选项
    settings_menu.add_command(label=get_text("settings"), command=settings1)

def create_download_tab():
    """创建下载选项卡"""
    global download_frame, version_combobox, download_file_combobox, destination_entry
    global thread_combobox, download_button, cancel_button, pause_button
    global status_label, progress_bar, thread_label
    
    # 创建Python下载框架
    download_frame = ttk.Frame(note, padding="10")
    
    # 添加版本选择
    ttk.Label(download_frame, text=get_text("select_python_version")).grid(row=0, column=0, pady=10, padx=10, sticky="e")
    version_combobox = ttk.Combobox(download_frame, width=20)
    version_combobox.grid(row=0, column=1, pady=10, padx=10, sticky="w")
    version_combobox["values"] = [get_text("loading_files")]
    version_combobox.current(0)
    version_combobox.config(state="readonly")
    
    # 添加刷新按钮
    reload_button = ttk.Button(download_frame, text=get_text("reload"), command=python_version_reload)
    reload_button.grid(row=0, column=2, pady=10, padx=10, sticky="w")
    
    # 添加文件选择
    ttk.Label(download_frame, text=get_text("choose_download_file")).grid(row=1, column=0, pady=10, padx=10, sticky="e")
    download_file_combobox = ttk.Combobox(download_frame, width=60)
    download_file_combobox.grid(row=1, column=1, columnspan=2, pady=10, padx=10, sticky="w")
    download_file_combobox["values"] = [""]
    download_file_combobox.config(state="disabled")
    
    # 添加目标路径选择
    ttk.Label(download_frame, text=get_text("select_destination")).grid(row=2, column=0, pady=10, padx=10, sticky="e")
    destination_frame = ttk.Frame(download_frame)
    destination_frame.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky="w")
    
    destination_entry = ttk.Entry(destination_frame, width=50)
    destination_entry.pack(side="left", fill="x", expand=True)
    
    select_path_button = ttk.Button(destination_frame, text=get_text("select_path"), command=select_destination)
    select_path_button.pack(side="right", padx=5)
    
    # 添加线程选择
    thread_label = ttk.Label(download_frame, text=get_text("select_threads"))
    thread_label.grid(row=3, column=0, pady=10, padx=10, sticky="e")
    thread_combobox = ttk.Combobox(download_frame, width=20)
    thread_combobox.grid(row=3, column=1, pady=10, padx=10, sticky="w")
    thread_combobox["values"] = [1, 2, 4, 8, 16]
    thread_combobox.current(2)  # 默认选择4线程
    
    # 添加下载按钮
    download_button = ttk.Button(download_frame, text=get_text("download"), command=download_selected_version)
    download_button.grid(row=4, column=0, columnspan=3, pady=10, padx=10)
    
    # 添加取消按钮（初始隐藏）
    cancel_button = ttk.Button(download_frame, text=get_text("cancel_download"), command=cancel_download)
    
    # 添加暂停/恢复按钮（初始隐藏）
    pause_button = ttk.Button(download_frame, text=get_text("pause_download"), command=pause_resume_download)
    
    # 添加状态标签
    status_label = ttk.Label(download_frame, text="")
    status_label.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
    
    # 添加进度条（初始隐藏）
    progress_bar = ttk.Progressbar(download_frame, length=500, mode="determinate")
    
    # 启动版本加载
    python_version_reload()
    
    return download_frame

def create_pip_tab():
    """创建Pip管理选项卡"""
    global pip_frame, pip_upgrade_button, package_entry, install_button, uninstall_button
    global upgrade_button, pip_retry_button, package_status_label, pip_progress_bar
    
    # 创建Pip管理框架
    pip_frame = ttk.Frame(note, padding="10")
    
    # 添加pip版本显示
    ttk.Label(pip_frame, text=get_text("pip_version")).grid(row=0, column=0, pady=10, padx=10, sticky="e")
    pip_upgrade_button = ttk.Button(pip_frame, text=get_text("pip_checking"))
    pip_upgrade_button.grid(row=0, column=1, columnspan=2, pady=10, padx=10, sticky="w")
    
    # 添加重试按钮（初始隐藏）
    pip_retry_button = ttk.Button(pip_frame, text=get_text("retry"), command=retry_pip_ui)
    
    # 添加包名输入
    package_label = ttk.Label(pip_frame, text=get_text("enter_package_name"))
    package_label.grid(row=2, column=0, pady=10, padx=10, sticky="e")
    package_entry = ttk.Entry(pip_frame, width=40)
    package_entry.grid(row=2, column=1, columnspan=2, pady=10, padx=10, sticky="w")
    
    # 添加操作按钮
    button_frame = ttk.Frame(pip_frame)
    button_frame.grid(row=3, column=0, columnspan=3, pady=10, padx=10)
    
    install_button = ttk.Button(button_frame, text=get_text("install_package"), command=install_package_ui)
    install_button.pack(side="left", padx=5)
    
    uninstall_button = ttk.Button(button_frame, text=get_text("uninstall_package"), command=uninstall_package_ui)
    uninstall_button.pack(side="left", padx=5)
    
    # 添加升级按钮（初始隐藏）
    upgrade_button = ttk.Button(button_frame, text=get_text("upgrade_package"), command=upgrade_package_ui)
    
    # 添加状态标签
    package_status_label = ttk.Label(pip_frame, text="")
    package_status_label.grid(row=4, column=0, columnspan=3, pady=10, padx=10)
    
    # 添加进度条（初始隐藏）
    pip_progress_bar = ttk.Progressbar(pip_frame, length=500, mode="determinate")
    
    return pip_frame

def load_settings():
    """加载设置"""
    global settings
    
    # 初始化默认设置
    settings = {
        "theme": "light",
        "python_mirror": get_text("default_source"),
        "pip_mirror": get_text("default_source"),
        "allow_multithreading": True,
        "language": "zh_CN",  # 默认简体中文
        "max_log_size": 10    # 默认最大日志大小(MB)
    }
    
    # 读取语言设置并更新UI
    try:
        language_file = os.path.join(config_path, "language.txt")
        if os.path.exists(language_file):
            with open(language_file, "r") as r:
                lang = r.read().strip() or "zh_CN"
                settings["language"] = lang
                set_language(lang)  # 设置当前语言
                # 更新界面文本
                update_interface_language()  # 在启动时应用语言设置
    except Exception as e:
        logger.error(f"加载语言设置失败: {e}")

def install_package_ui():
    """安装包UI入口点"""
    from modules.pip_manager import install_package
    package_name = package_entry.get().strip()
    if not package_name:
        messagebox.showwarning(get_text("warning"), get_text("enter_package_name_first"))
        return
    
    install_package(package_name, config_path, package_status_label, pip_progress_bar, 
                   install_button, uninstall_button, upgrade_button, pip_upgrade_button, 
                   package_entry, root)

def uninstall_package_ui():
    """卸载包UI入口点"""
    from modules.pip_manager import uninstall_package
    package_name = package_entry.get().strip()
    if not package_name:
        messagebox.showwarning(get_text("warning"), get_text("enter_package_name_first"))
        return
    
    uninstall_package(package_name, config_path, package_status_label, pip_progress_bar, 
                     install_button, uninstall_button, upgrade_button, pip_upgrade_button, 
                     package_entry, root)

def upgrade_package_ui():
    """升级包UI入口点"""
    from modules.pip_manager import upgrade_package
    package_name = package_entry.get().strip()
    if not package_name:
        messagebox.showwarning(get_text("warning"), get_text("enter_package_name_first"))
        return
    
    upgrade_package(package_name, config_path, package_status_label, pip_progress_bar, 
                   upgrade_button, pip_upgrade_button, package_entry, install_button, 
                   uninstall_button, root)

def select_destination():
    """选择下载目标路径"""
    from tkinter import filedialog
    directory = filedialog.askdirectory()
    if directory:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, directory)

def on_closing():
    """窗口关闭处理"""
    global app_running
    
    # 设置全局标志，所有线程在循环中检查此标志
    app_running = False
    
    # 等待一段时间让后台线程完成工作
    time.sleep(0.5)
    
    # 销毁窗口
    root.destroy()

def start_background_threads():
    """启动后台线程"""
    from modules.thread_manager import allow_thread, save_path, get_pip_mirror
    
    # 启动线程检查
    threading.Thread(target=allow_thread, daemon=True).start()
    
    # 使用延迟确保GUI已完全初始化
    root.after(100, show_pip_version)
    
    # 启动配置保存和镜像获取线程
    threading.Thread(target=save_path, daemon=True).start()
    threading.Thread(target=get_pip_mirror, daemon=True).start()

def create_main_window():
    """创建主窗口"""
    global root, note
    
    # 初始化配置路径
    initialize_paths()
    
    # 创建主窗口
    root = tk.Tk()
    root.title("PyQuick - Python安装与管理工具")
    root.resizable(False, False)
    
    # 设置图标
    icon_path = os.path.join(os.path.dirname(parent_dir), 'pyquick.ico')
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    
    # 设置关闭窗口处理
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 设置菜单栏
    setup_menu()
    
    # 创建选项卡
    note = ttk.Notebook(root)
    note.pack(expand=True, fill="both")
    
    # 创建下载选项卡
    download_frame = create_download_tab()
    note.add(download_frame, text=get_text("python_download"))
    
    # 创建Pip管理选项卡
    pip_frame = create_pip_tab()
    note.add(pip_frame, text=get_text("pip_management"))
    
    # 加载设置
    load_settings()
    
    # 启动后台线程
    start_background_threads()
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    # 如果直接运行此文件，则启动应用程序
    create_main_window() 