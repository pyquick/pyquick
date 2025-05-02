import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from turtle import fillcolor
package_entry = None
import subprocess
import os
import threading
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
import queue
import time
import logging
from xml.sax.handler import property_xml_string
from cryptography.fernet import Fernet
import requests
import proxy
from get_system_build import block_features
import darkdetect
import re
from save_path import create_folder,sav_path
requests.packages.urllib3.disable_warnings()
import sv_ttk
import datetime
from bs4 import BeautifulSoup
import sys
import importlib
import json
import gc
import multiprocessing
from multiprocessing import Process, Queue, Manager, Pool, Event
from functools import partial
from crashes import *
version="1965"
myfilenumber="7079"
try:
    collect.delete_crashes_folder_all(version)
except Exception as e:
    pass
open.repair_path(version)#修复缓存路径
config_path=create_folder.get_path("pyquick",version)
cancel_event = threading.Event()
create_folder.folder_create("pyquick",version)
# 导入新的日志系统
try:
    from log import app_logger, download_logger, error_logger, configure_global_loggers
    from log import file_manager, json_manager, configure_file_managers
    
    # 设置日志目录
    log_dir = os.path.join(config_path, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志系统
    configure_global_loggers(log_level="info", enable_console=True, enable_file=True, log_dir=log_dir)
    
    # 配置文件管理器
    configure_file_managers(base_dir=config_path)
    
    USE_NEW_LOG_SYSTEM = True
except ImportError:
    # 如果导入失败，使用原始日志配置
    USE_NEW_LOG_SYSTEM = False
    
    # 确保日志目录存在
    log_dir = os.path.join(config_path, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
            logging.FileHandler(os.path.join(log_dir, 'pyquick.log')),
        logging.StreamHandler()
    ]
)
app_logger = logging.getLogger('pyquick')
download_logger = logging.getLogger('download')
error_logger = logging.getLogger('error')

# 导入设置和主题管理模块
import settings.settings_manager as settings_manager
from settings.settings_manager import init_manager, get_manager, init_theme_manager, get_theme_manager
from downloader.DownloadManager import DownloadManager  # 导入下载管理器
from downloader import Downloader  # 导入下载器模块
from pipx.upgrade_pip import get_current_pip_version, get_latest_pip_version, upgrade_pip
from pipx.install_unsi import install_package, uninstall_package

# 添加一个兼容函数，以防其他模块调用init_settings_manager
def init_settings_manager(config_path):
    """兼容性函数，转发到init_manager"""
    return init_manager(config_path)

# 添加一个安全的UI更新函数
def safe_ui_update(widget, **kwargs):
    """安全地在主线程中更新UI元素"""
    if widget and widget.winfo_exists():
        try:
            root.after(0, lambda: widget.config(**kwargs))
            return True
        except Exception as e:
            error_logger.error(f"UI更新错误: {e},Line98(maybe),{myfilenumber},safe_ui_update")
            return False
    return False

# 线程安全的Tkinter操作装饰器
def tk_safe(func):
    """确保Tkinter操作在主线程中执行的装饰器"""
    def wrapper(*args, **kwargs):
        if threading.current_thread() == threading.main_thread():
            # 已在主线程，直接执行
            return func(*args, **kwargs)
        else:
            # 不在主线程，使用after方法调度到主线程
            result_queue = queue.Queue()
            def task():
                try:
                    result = func(*args, **kwargs)
                    result_queue.put((True, result))
                except Exception as e:
                    result_queue.put((False, e))
            
            try:
                root.after(0, task)
                # 等待执行结果
                success, result = result_queue.get(timeout=5)
                if success:
                    return result
                else:
                    raise result
            except Exception as e:
                error_logger.error(f"Tkinter操作失败: {func.__name__}, {str(e)},Line128(maybe),{myfilenumber},tk_safe")
                raise
    
    return wrapper

# 全局线程池
THREAD_POOL = ThreadPoolExecutor(max_workers=min(4, os.cpu_count()), thread_name_prefix="PyquickWorker")
# UI更新队列
UI_UPDATE_QUEUE = queue.Queue()


# 全局变量
download_manager = None  # 下载管理器实例
current_task_id = None   # 当前下载任务ID
pip_manager = None       # PIP管理器实例
settings_mgr = None      # 设置管理器实例
theme_mgr = None         # 主题管理器实例

def log_start():
    """记录程序启动信息"""
    app_logger.info("="*50)
    app_logger.info(f"PyQuick 启动于 {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    app_logger.info(f"操作系统: {sys.platform}, Python版本: {sys.version}")
    app_logger.info(f"配置路径: {config_path}")
    app_logger.info("="*50)

# 启动日志
log_start()

# 自动安装依赖
install_package("memory_profiler")
from debug_info.ui import DebugInfoWindow
# 排序版本获取结果
def sort_results(results: list):
    """排序Python版本列表，最新版本排在前面"""
    try:
        # 使用Version类来排序
        results_sorted = sorted(results, key=lambda x: Version(x), reverse=True)
        return results_sorted
    except Exception as e:
        error_logger.error(f"排序版本列表失败: {e},Line168,{myfilenumber},sort_results")
        return results

def update_versions(results_sorted):
    """更新版本下拉框中的版本列表"""
    try:
        if version_combobox and version_combobox.winfo_exists():
            version_combobox.configure(values=results_sorted)
            if results_sorted and len(results_sorted) > 0:
                version_combobox.current(0)  # 选择最新版本
        if version_reload and version_reload.winfo_exists():
            version_reload.config(text="刷新版本列表", state="normal")
    except Exception as e:
        error_logger.error(f"更新版本列表失败: {e},Line181,{myfilenumber},update_versions")

def handle_error(exception):
    """处理版本列表加载错误"""
    app_logger.error(f"Version reload error: {str(exception)}")
    if version_reload and version_reload.winfo_exists():
        version_reload.config(text="刷新失败", state="normal")
        # 3秒后自动恢复按钮文本
        root.after(3000, lambda: version_reload.config(text="刷新版本列表", state="normal"))

def python_version_reload():
    """重新加载Python版本列表"""
    def thread():
        try:
            response = requests.get("https://www.python.org/ftp/python/", timeout=10)
            response.raise_for_status()
            
            bs = BeautifulSoup(response.content, "lxml")
            r1 = r'\d+\.\d+\.\d+/$'
            results = []
            for i in bs.find_all("a"):
                # 使用正则匹配版本号格式
                if re.match(r1, i.text):
                    version = i.text.strip('/')
                    results.append(version)
                    
            # 排序结果
            results_sorted = sort_results(results)
            
            # 保存最新结果到文件中
            sav_path.save_path(config_path, "version.txt", "w", str(results_sorted))
            
            # 更新UI
            root.after(0, lambda: update_versions(results_sorted))
            
            # 定期释放内存
            gc.collect()
        except Exception as e:
            # 更新UI显示错误
            root.after(0, lambda: handle_error(e))
    
    # 线程启动
    threading.Thread(target=thread, daemon=True).start()



def python_file_reload():
    try:
        ver=version_combobox.get()
        response = requests.get(f"https://www.python.org/ftp/python/{ver}/", timeout=10)
        response.raise_for_status()
        
        bs = BeautifulSoup(response.content, "lxml")
        r1 = r'python-\S+-macos\S+.pkg'
        r2 = r'python-\S+-macos\S+.dmg'
        r3 = r'python-\S+.tgz'
        r4 = r'python-\S+.tar.xz'
        r5 = r'python-\S+.json'
        r6 = r'python-\S+.sig'
        r7 = r'python-\S+.asc'
    
        
        results = []
        for i in bs.find_all("a"):
            # 使用正则匹配版本号格式
            if (re.match(r1, i.text) or re.match(r2, i.text) or re.match(r3, i.text) or re.match(r4, i.text) or re.match(r5, i.text) or re.match(r6, i.text) or re.match(r7, i.text)) and "exe" not in i.text and "win" not in i.text and "embed" not in i.text:
                packages = i.text.strip(" ")
                results.append(packages)
        return results
    except Exception as e:
        # 更新UI显示错误
        return []
def show_name():
    while True:
        try:
            ver=version_combobox.get()
            if os.path.exists(os.path.join(config_path,"crashes","download","ver.txt")):
                ver1=edit.read_file(version,"download","ver.txt")
                if ver1==ver:
                    app_logger.info("版本号相同")
                else:
                    ver2=version_combobox.get()
                    edit.edit_file(version,"download","ver.txt",ver2)
                    app_logger.info("修改版本号")
            else:
                open.create_crashes_folder(version,"download")
                open.create_crashes_file(version,"download","ver.txt")
            a=python_file_reload()
            choose_file_combobox.configure(values=a)
            time.sleep(0.5)
            gc.collect()
        except Exception as e:
            error_logger.error(f"显示python包失败: {str(e)},Line272,{myfilenumber}")
def read_python_list():
    """读取Python版本列表"""
    try:
        base1 = str(sav_path.read_path(config_path, "version.txt", "readline"))
        base2 = base1.strip("[]").split(",")
        base3 = []
        for i in base2:
            j = i.strip("'")
            base3.append(j.strip(" '"))
        
        # 通过root.after在主线程中更新UI
        def update_ui():
            try:
                if version_combobox and version_combobox.winfo_exists():
                    version_combobox.configure(values=base3)
            except Exception as e:
                error_logger.error(f"更新版本列表失败: {str(e)},Line289,{myfilenumber},update_versions")
        
        # 确保在主线程中执行UI更新
        if threading.current_thread() == threading.main_thread():
            update_ui()
        else:
            root.after(0, update_ui)
    except Exception as e:
        error_logger.error(f"读取Python版本列表失败: {str(e)},Line297,{myfilenumber},read_python_list")

class Version:
    def __init__(self, version_str: str):
        self.version = version_str.split('.')
        while len(self.version) < 3:
            self.version.append('0')

    def __lt__(self, other):
        for i in range(3):
            if (v1 := int(self.version[i])) < (v2 := int(other.version[i])):
                return True
            elif v1 > v2:
                return False
        else:
            return False


def check_python_installation(delay=3000):
    """
    检查Python3是否已安装。
    
    本函数尝试执行'python3 --version'命令来检查Python3的安装情况。
    如果命令执行出错，说明Python3未安装，则更新界面标签并禁用相关按钮。
    """
    try:
        # 执行命令并获取输出
        version_output = subprocess.check_output(["python3", "--version"], stderr=subprocess.STDOUT, text=True)
        
        # 验证输出是否包含预期的Python版本信息
        if "Python 3" not in version_output:
            raise ValueError("Unexpected Python version output: " + version_output.strip())
    except subprocess.CalledProcessError:
        # 如果命令执行失败，说明Python3未安装
        status_label.config(text="Python3 is not installed.")
        pip_upgrade_button.config(state="disabled")
        install_button.config(state="disabled")
        uninstall_button.config(state="disabled")
        
        # 延时指定时间后清除当前状态标签的文本
        root.after(delay, clear_a)
    except ValueError as e:
        # 处理其他异常，例如版本输出不符合预期
        status_label.config(text=str(e))
        root.after(delay, clear_a)

def clear_a():
    status_label.config(text="")
    package_label.config(text="")
    download_pb['value'] = 0  # 重置进度条
def select_destination():
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)

# 全局变量
file_size = 0
executor: ThreadPoolExecutor
futures = []
lock = threading.Lock()
downloaded_bytes = [0]
is_downloading = False
def validate_path(path):
    """
    验证路径是否存在

    参数:
    path (str): 需要验证的路径

    返回:
    bool: 如果路径存在返回True，否则返回False
    """
    if not path:
        return False
    return os.path.isdir(path)
def validate_version(version):
    """
    验证版本号格式是否符合预期的格式

    此函数通过正则表达式检查传入的版本号是否符合 major.minor.patch 的格式，
    其中 major、minor 和 patch 都是数字

    参数:
    version (str): 需要验证的版本号字符串

    返回:
    bool: 如果版本号符合预期格式，则返回 True，否则返回 False
    """
    # 定义版本号的正则表达式模式，确保版本号是 major.minor.patch 的格式
    pattern = r'^\d+\.\d+\.\d+$'
    patten2=r'^\d+\.\d+$'
    # 使用正则表达式匹配版本号，返回匹配结果的布尔值
    if re.match(patten2,version):
        return True
    return bool(re.match(pattern, version))

def load_proxy_config():
    """加载代理配置"""
    try:
        if USE_NEW_LOG_SYSTEM:
            # 使用新的日志系统加载代理配置
            proxy_config = json_manager.read_json(os.path.join(config_path, "proxy.json"))
            if proxy_config:
                app_logger.info(f"已加载代理配置: {proxy_config}")
                return proxy_config
        else:
            # 使用旧的方式加载代理配置
            proxy_config = sav_path.read_path(config_path, "proxy.json", "read")
            if proxy_config:
                return json.loads(proxy_config)
    except Exception as e:
        error_logger.error(f"加载代理配置出错: {e},Line409,{myfilenumber},load_proxy_config")
    return None

def init_download_manager():
    """初始化下载管理器"""
    global download_manager
    if download_manager is None:
        try:
        # 优化线程数配置
            thread_count = min(max(2, int(threads_entry.get())), os.cpu_count() * 2)
            download_manager = DownloadManager(
                task_db_path=os.path.join(config_path, "downloads.json"),
                max_concurrent_downloads=min(3, os.cpu_count()),
                num_threads_per_download=thread_count,
                on_task_status_changed=on_download_status_changed
            )
            app_logger.info(f"下载管理器初始化成功: 线程数={thread_count}")
        except Exception as e:
            error_logger.error(f"初始化下载管理器失败: {e},Line427,{myfilenumber},init_download_manager")
            messagebox.showerror("错误", f"初始化下载管理器失败: {e},Line428,{myfilenumber},init_download_manager")

def on_download_status_changed(task):
    """下载状态变化回调函数"""
    if task.task_id == current_task_id:
        update_download_ui()

def update_download_ui():
    """更新下载UI状态"""
    global file_size, downloaded_bytes

    if not is_downloading:
            return

    try:
        # 使用锁确保线程安全
        with lock:
            downloaded = sum(downloaded_bytes)
            percent = int(downloaded / file_size * 100) if file_size > 0 else 0
            size_str = f"{downloaded / 1024 / 1024:.2f} MB / {file_size / 1024 / 1024:.2f} MB"
        
        # 计算下载速度
        current_time = time.time()
        if not hasattr(update_download_ui, "last_update_time"):
            update_download_ui.last_update_time = current_time
            update_download_ui.last_downloaded = downloaded
            speed = 0
        else:
            time_diff = current_time - update_download_ui.last_update_time
            if time_diff > 0:
                bytes_diff = downloaded - update_download_ui.last_downloaded
                speed = bytes_diff / time_diff
                update_download_ui.last_update_time = current_time
                update_download_ui.last_downloaded = downloaded
            else:
                speed = 0
        
        # 格式化下载速度
        speed_str = f"{speed / 1024 / 1024:.2f} MB/s" if speed > 0 else ""
        
        # 更新进度条和标签
        if download_pb and download_pb.winfo_exists():
            download_pb['value'] = percent
        if size_label and size_label.winfo_exists():
            size_label.config(text=size_str)
        if speed_label and speed_label.winfo_exists():
            speed_label.config(text=speed_str)
        
        # 当新的进度信息已经显示，计划下一次更新
        if is_downloading:
            # 降低更新频率，减少CPU使用
            update_interval = 500  # 毫秒
            root.after(update_interval, update_download_ui)
            
            # 定期释放内存
            if not hasattr(update_download_ui, "gc_counter"):
                update_download_ui.gc_counter = 0
            update_download_ui.gc_counter += 1
            if update_download_ui.gc_counter >= 10:  # 每10次更新释放一次内存
                update_download_ui.gc_counter = 0
                gc.collect()
    except Exception as e:
        error_logger.error(f"更新下载UI失败: {e},Line490,{myfilenumber},update_download_ui")
        if is_downloading:
            root.after(1000, update_download_ui)

def update_button_states(can_download: bool, can_resume: bool, can_cancel: bool):
    """更新按钮状态"""
    download_button.config(state="normal" if can_download else "disabled")
    resume_button.config(state="normal" if can_resume else "disabled")
    pause_button.config(state="normal" if not can_resume and can_cancel else "disabled")
    cancel_download_button.config(state="normal" if can_cancel else "disabled")

def update_task_progress():
    """定期更新下载任务进度"""
    try:
        if download_manager and current_task_id:
            task = download_manager.get_task(current_task_id)
            if task and hasattr(task, 'status') and 'downloading' in str(task.status).lower():
                # 使用安全的进度更新
                update_download_ui()
                
        # 获取当前进度值，确保它是数字
        try:
            progress = float(download_pb['value']) if 'value' in download_pb else 0
        except (ValueError, TypeError, AttributeError):
            progress = 0
            
        # 动态调整刷新间隔
        if progress > 95:
            refresh_interval = 2000  # 接近完成时显著减少刷新频率
        elif progress > 80:
            refresh_interval = 1000  # 高进度时减少刷新频率
        else:
            refresh_interval = 500   # 正常刷新频率
        
        # 安排下一次更新
        root.after(refresh_interval, update_task_progress)
        
    except Exception as e:
        error_logger.error(f"任务进度更新错误: {str(e)},Line528,{myfilenumber},update_task_progress")
        root.after(1000, update_task_progress)  # 出错时使用较长的刷新间隔

def validate_download_config():
    """验证下载配置是否有效"""
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    file_name = choose_file_combobox.get()
    thread_count = threads_entry.get()
    
    # 初始化时默认禁用下载按钮
    download_button.config(state="disabled")
    
    # 收集所有错误消息
    errors = []
    
    # 验证版本选择
    if not selected_version:
        errors.append("请选择Python版本！")
    
    # 验证目标路径
    if not destination_path:
        errors.append("请选择目标路径！")
    elif not os.path.exists(destination_path):
        errors.append(f"路径无效: {destination_path}")
    
    # 验证文件选择
    if not file_name:
        errors.append("请选择要下载的文件！")
    
    # 验证线程数
    try:
        thread_count = int(thread_count)
        if thread_count < 1:
            raise ValueError
    except (ValueError, TypeError):
        errors.append("无效的线程数！")
    
    # 如果有错误，显示所有错误消息
    if errors:
        status_label.config(text="\n".join(errors), foreground="red")
        return False
    
    # 只有所有验证都通过才启用下载按钮
    download_button.config(state="normal")
    status_label.config(foreground="black")
    return True

def download_selected_version():
    """开始下载所选Python版本"""
    global current_task_id
    
    # 验证下载配置
    if not validate_download_config():
        return
    
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    file_name = choose_file_combobox.get()
    thread_count = int(threads_entry.get())
    
    # 准备保存路径
    save_path = os.path.join(destination_path, file_name)
    
    # 检查文件是否已存在
    if os.path.exists(save_path):
        if messagebox.askyesno("文件已存在", f"文件 {file_name} 已存在。\n是否覆盖？"):
            try:
                os.remove(save_path)
            except Exception as e:
                error_logger.error(f"删除已存在文件失败: {e}")
                messagebox.showerror("错误", f"无法删除已存在的文件: {e}")
                return
        else:
            return
    
    # 初始化下载管理器
    init_download_manager()
    
    # 构建下载URL和文件保存路径
    url = f"https://www.python.org/ftp/python/{selected_version}/{file_name}"
    
    # 获取代理设置
    proxies = load_proxy_config()
    
    app_logger.info(f"开始下载: URL={url}, 保存路径={save_path}, 线程数={thread_count}")
    
    # 创建下载任务
    try:
        current_task_id = download_manager.add_task(
        url=url,
            file_path=save_path,
            thread_count=thread_count,
            proxies=proxies
        )
        
        # 开始下载
        download_manager.start_task(current_task_id)
        
        # 更新UI
        download_pb['value'] = 0
        status_label.config(text="准备下载...")
        update_button_states(False, False, True)
        
        # 立即进行一次UI更新
        update_download_ui()
    
    except Exception as e:
        error_logger.error(f"创建下载任务失败: {e},Line636,{myfilenumber},download_selected_version")
        messagebox.showerror("下载错误", f"创建下载任务失败: {e}")
        download_pb['value'] = 0
        status_label.config(text=f"下载失败: {e}")
        update_button_states(True, False, False)

def cancel_download():
    """取消下载"""
    global current_task_id
    if current_task_id and download_manager:
        try:
            download_manager.cancel_task(current_task_id)
            app_logger.info(f"用户取消下载: task_id={current_task_id}")
            update_download_ui()
        except Exception as e:
            error_logger.error(f"取消下载失败: {e},Line651,{myfilenumber},cancel_download")
            messagebox.showerror("错误", f"取消下载失败: {e}")

def resume_download():
    """恢复下载"""
    global current_task_id
    if current_task_id and download_manager:
        try:
            download_manager.resume_task(current_task_id)
            app_logger.info(f"用户恢复下载: task_id={current_task_id}")
            update_download_ui()
        except Exception as e:
            error_logger.error(f"恢复下载失败: {e},Line663,{myfilenumber},resume_download")
            messagebox.showerror("错误", f"恢复下载失败: {e}")

def pause_download():
    """暂停下载"""
    global current_task_id
    if current_task_id and download_manager:
        try:
            download_manager.pause_task(current_task_id)
            app_logger.info(f"用户暂停下载: task_id={current_task_id}")
            update_download_ui()
        except Exception as e:
            error_logger.error(f"暂停下载失败: {e},Line675,{myfilenumber},pause_download")
            messagebox.showerror("错误", f"暂停下载失败: {e}")

def show_about():
    messagebox.showinfo("About", f"Version: dev\nBuild: 1962\n10086 days left.")

def on_closing():
    try:
        global is_downloading, file_reload_stop_event
        if is_downloading:
            cancel_download()
        
        # 停止文件刷新线程并终止进程
        if 'file_reload_stop_event' in globals() and file_reload_stop_event:
            try:
                if isinstance(file_reload_stop_event, dict):
                    file_reload_stop_event["stop_event"].set()
                    if "process" in file_reload_stop_event:
                        file_reload_stop_event["process"].terminate()
                else:
                    file_reload_stop_event.set()
            except Exception as e:
                error_logger.error(f"停止文件刷新线程失败: {e},Line696,{myfilenumber},on_closing")
            
        # 如果主题管理器存在，保存当前主题设置
        if settings_mgr:
            try:
                settings_mgr.save_settings()
                app_logger.info("设置已保存")
            except Exception as e:
                error_logger.error(f"保存设置失败: {e},Line704,{myfilenumber},on_closing")
        
        # 确保所有线程都有机会终止
        time.sleep(0.1)
        try:
            collect.delete_crashes_folder_all(version)
        except Exception as e:
            error_logger.error(f"删除缓存文件夹失败: {e},Line712,{myfilenumber},on_closing")
        root.destroy()
        exit(0)
    except Exception as e:
        subprocess.Popen("killall Python",text=True,shell=True)
        subprocess.Popen("killall pyquick",text=True,shell=True)
        subprocess.Popen("killall Pyquick",text=True,shell=True)

def update_pip_ui(result, operation, package_name=None):
    """Update UI state after pip operation"""
    if result:
        if operation == "upgrade":
            message = "pip升级成功"
        elif operation == "install":
            message = f"包 {package_name} 安装成功"
        elif operation == "uninstall":
            message = f"包 {package_name} 卸载成功"
        UI_UPDATE_QUEUE.put(lambda: messagebox.showinfo("成功", message))
    else:
        if operation == "upgrade":
            message = "pip升级失败"
        elif operation == "install":
            message = f"包 {package_name} 安装失败"
        elif operation == "uninstall":
            message = f"包 {package_name} 卸载失败"
        UI_UPDATE_QUEUE.put(lambda: messagebox.showerror("错误", message))
    UI_UPDATE_QUEUE.put(lambda: clear_a())

def pip_upgrade_wrapper():
    """Wrapper for pip upgrade operation, add UI update"""
    def upgrade_thread():
        result = upgrade_pip()
        update_pip_ui(result, "upgrade")
    threading.Thread(target=upgrade_thread, daemon=True).start()

def pip_install_wrapper(package_name):
    """Wrapper for package installation operation, add UI update"""
    def install_thread():
        result = install_package(package_name)
        update_pip_ui(result, "install", package_name)
    threading.Thread(target=install_thread, daemon=True).start()

def pip_uninstall_wrapper(package_name):
    """Wrapper for package uninstallation operation, add UI update"""
    def uninstall_thread():
        result = uninstall_package(package_name)
        update_pip_ui(result, "uninstall", package_name)
    threading.Thread(target=uninstall_thread, daemon=True).start()

def init_pip_manager():
    """初始化pip_manager"""
    global pip_manager, settings_tab
    
    if HAS_PIP_MANAGER:
        # 使用新的PipManager类
        pip_manager = PipManager(root, settings_tab, config_path)
    else:
        # 使用旧的方式
        package_label = ttk.Label(settings_tab, text="Enter Package Name:")
        package_label.grid(row=1, column=0, pady=20, padx=20)

        package_entry = ttk.Entry(settings_tab, width=60)
        package_entry.grid(row=1, column=1, pady=20, padx=20)

        install_button = ttk.Button(settings_tab, text="Install Package", 
                                command=lambda: pip_install_wrapper(package_entry.get()))
        install_button.grid(row=2, column=0, columnspan=3, pady=20, padx=20)

        uninstall_button = ttk.Button(settings_tab, text="Uninstall Package", 
                                    command=lambda: pip_uninstall_wrapper(package_entry.get()))
        uninstall_button.grid(row=3, column=0, columnspan=3, pady=20, padx=20)

        pip_upgrade_button = ttk.Button(settings_tab, text="Upgrade Pip", command=pip_upgrade_wrapper)
        pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=20, padx=20)

# 在合适的位置添加PIP管理器的导入
try:
    from pipx.pip_manager import PipManager
    HAS_PIP_MANAGER = True
except ImportError:
    HAS_PIP_MANAGER = False

def init_settings():
    """初始化设置管理器和主题管理器"""
    global settings_mgr, theme_mgr
    try:
        # 初始化设置管理器
        settings_mgr = init_manager(config_path)
        app_logger.info("设置管理器初始化成功")
        
        # 初始化主题管理器
        # 确保themes目录存在
        themes_dir = os.path.join(os.path.dirname(__file__), "themes")
        if not os.path.exists(themes_dir):
            os.makedirs(themes_dir, exist_ok=True)
            app_logger.info(f"创建主题目录: {themes_dir}")
        
        # 检查是否存在主题文件，如果不存在则创建默认主题
        theme_files = {
            "theme_config.json": {
                "theme_type": "dark",
                "allow_custom_themes": True,
                "current_theme": "系统默认"
            },
            "light.json": {
                "name": "亮色主题",
                "type": "light",
                "description": "默认亮色主题",
                "colors": {
                    "background": "#ffffff",
                    "foreground": "#000000",
                    "accent": "#0078d7",
                    "text": "#333333",
                    "button.background": "#f0f0f0",
                    "button.foreground": "#000000",
                    "entry.background": "#ffffff",
                    "entry.foreground": "#000000",
                    "label.foreground": "#333333"
                }
            },
            "dark.json": {
                "name": "暗色主题",
                "type": "dark",
                "description": "默认暗色主题",
                "colors": {
                    "background": "#1e1e1e",
                    "foreground": "#ffffff",
                    "accent": "#0078d7",
                    "text": "#e0e0e0",
                    "button.background": "#333333",
                    "button.foreground": "#ffffff",
                    "entry.background": "#252525",
                    "entry.foreground": "#ffffff",
                    "label.foreground": "#e0e0e0"
                }
            }
        }
        
        for theme_file, theme_data in theme_files.items():
            theme_path = os.path.join(themes_dir, theme_file)
            if not os.path.exists(theme_path):
                try:
                    with open(theme_path, 'w', encoding='utf-8') as f:
                        json.dump(theme_data, f, indent=4, ensure_ascii=False)
                    app_logger.info(f"创建默认主题文件: {theme_path}")
                except Exception as e:
                    app_logger.error(f"创建主题文件失败: {theme_path}, {e},Line853,{myfilenumber},init_settings")
        
        try:
            theme_mgr = init_theme_manager(themes_dir)
            app_logger.info("主题管理器初始化成功")
        except Exception as e:
            error_logger.error(f"主题管理器初始化失败: {e},Line859,{myfilenumber},init_settings")
            # 创建一个空的主题管理器，防止程序崩溃
            theme_mgr = None
        
        return True
    except Exception as e:
        error_logger.error(f"初始化设置管理器失败: {e},Line865,{myfilenumber},init_settings")
        return False

def show_settings():
    """打开设置窗口"""
    global settings_mgr, theme_mgr, root
    
    try:
        # 确保设置管理器已初始化
        if settings_mgr is None:
            if not init_settings():
                messagebox.showerror("错误", "无法初始化设置管理器")
                return
        
        # 使用设置模块中的函数打开设置窗口
        from settings.ui.window import SettingsWindow
        settings_window = SettingsWindow(root, settings_mgr, theme_mgr)
        
        app_logger.info("已打开设置窗口")
    except Exception as e:
        error_logger.error(f"打开设置窗口失败: {e},Line885,{myfilenumber},show_settings")
        messagebox.showerror("错误", f"打开设置窗口失败: {e},Line886,{myfilenumber},show_settings")

def apply_theme():
    """应用当前主题到界面"""
    global theme_mgr, root
    
    try:
        # 如果主题管理器不可用，使用默认的sv_ttk主题
        if theme_mgr is None:
            try:
                import sv_ttk
                import darkdetect
                
                # 默认使用系统设置或light主题
                theme = "light"  # 设置默认为light主题
                try:
                    # 检测系统主题
                    if darkdetect.isDark():
                        theme = "dark"
                    else:
                        theme = "light"
                except:
                    pass  # 如果无法检测，使用默认light主题
                
                # 从设置中读取主题（如果有）
                if settings_mgr:
                    user_theme = settings_mgr.get("theme.current_theme", "系统默认")
                    if user_theme == "暗色主题" or user_theme == "dark":
                        theme = "dark"
                    elif user_theme == "亮色主题" or user_theme == "light":
                        theme = "light"
                    elif user_theme == "系统默认":
                        # 已经在上面设置了基于系统的默认值
                        pass
                
                sv_ttk.set_theme(theme)
                app_logger.info(f"应用程序样式初始化: 使用{theme}主题")
            except Exception as e:
                error_logger.error(f"应用默认主题失败: {e},Line924,{myfilenumber},apply_theme")
            return
        
        # 使用主题管理器
        # 获取当前主题
        theme_name = settings_mgr.get("theme.current_theme", "系统默认")
        theme_type = "light"  # 默认使用亮色主题
        
        if theme_name == "暗色主题":
            theme_type = "dark"
        elif theme_name == "亮色主题":
            theme_type = "light"
        elif theme_name == "系统默认":
            # 自动检测系统主题
            try:
                import darkdetect
                theme_type = "dark" if darkdetect.isDark() else "light"
            except ImportError:
                theme_type = "light"  # 无法检测时默认使用亮色主题
        
        # 应用主题
        try:
            import sv_ttk
            sv_ttk.set_theme(theme_type)
            app_logger.info(f"已应用sv_ttk主题: {theme_type}")
        except Exception as e:
            error_logger.error(f"应用sv_ttk主题失败: {e},Line950,{myfilenumber},apply_theme")
        
        # 应用自定义主题设置（如果有）
        try:
            theme_mgr.apply_theme(root)
            app_logger.info("已应用主题到主界面")
        except Exception as e:
            error_logger.error(f"应用主题到主界面失败: {e},Line957,{myfilenumber},apply_theme")
            
    except Exception as e:
        error_logger.error(f"应用主题失败: {e},Line960,{myfilenumber},apply_theme")

#GUI
if __name__ == "__main__" and block_features.block_start():
    try:
        # 初始化日志记录
        log_start()
        
        # 初始化设置管理器和主题管理器
        init_settings()
        
        # 创建主窗口
        root = tk.Tk()
        root.title("Pyquick")
        root.protocol("WM_DELETE_WINDOW", on_closing)
    
        # 设置图标 (Removed icon setting)

        # 应用主题
        apply_theme()
        
        # 初始化并启动文件刷新线程
        file_reload_stop_event = python_file_reload()

        # 创建菜单栏
        menu_bar = tk.Menu(root)
        root.config(menu=menu_bar)
        help_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="应用设置", command=show_settings)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=show_about)
        help_menu.add_command(label="调试信息", command=lambda: DebugInfoWindow())
        help_menu.add_separator()

        #TAB CONTROL
        tab_control = ttk.Notebook(root)
        #MODE TAB
        fmode = ttk.Frame(root, padding="20")
        tab_control.add(fmode, text="Python下载")
        tab_control.grid(row=0, padx=10, pady=10)

        fsettings=ttk.Frame(root, padding="20")
        tab_control.add(fsettings, text="Pip管理")
        tab_control.grid(row=0, padx=10, pady=10)

        # 创建主下载界面框架
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        main_frame = ttk.Frame(fmode)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        settings_tab=ttk.Frame(fsettings)
        settings_tab.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        settings_tab.grid_columnconfigure(0, weight=1)
        settings_tab.grid_rowconfigure(0, weight=1)

        # 版本选择模块
        version_frame = ttk.LabelFrame(main_frame, text="版本选择", padding=10)
        version_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        version_label = ttk.Label(version_frame, text="Python版本:")
        version_label.grid(row=0, column=0, pady=5, padx=5)

        selected_version = tk.StringVar()
        version_combobox = ttk.Combobox(version_frame, textvariable=selected_version, values=[], state="readonly", width=30)
        version_combobox.grid(row=0, column=1, pady=5, padx=5)

        version_reload = ttk.Button(version_frame, text="刷新版本列表", command=python_version_reload)
        version_reload.grid(row=0, column=2, pady=5, padx=5)

        # 文件选择模块
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding=10)
        file_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

        choose_label = ttk.Label(file_frame, text="Python安装包:")
        choose_label.grid(row=0, column=0, pady=5, padx=5)

        choose_file = tk.StringVar()
        choose_file_combobox = ttk.Combobox(file_frame, textvariable=choose_file, values=[], state="readonly", width=50)
        choose_file_combobox.grid(row=0, column=1, columnspan=2, pady=5, padx=5)

        # 下载设置模块
        settings_frame = ttk.LabelFrame(main_frame, text="下载设置", padding=10)
        settings_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        destination_label = ttk.Label(settings_frame, text="保存位置:")
        destination_label.grid(row=0, column=0, pady=5, padx=5)

        destination_entry = ttk.Entry(settings_frame, width=50)
        destination_entry.grid(row=0, column=1, pady=5, padx=5)

        select_button = ttk.Button(settings_frame, text="浏览", command=select_destination)
        select_button.grid(row=0, column=2, pady=5, padx=5)

        threads_label = ttk.Label(settings_frame, text="线程数:")
        threads_label.grid(row=1, column=0, pady=5, padx=5)

        threads = tk.IntVar()
        threads_entry = ttk.Combobox(settings_frame, width=10, textvariable=threads, values=[str(i) for i in range(1, 17)], state="readonly")
        threads_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        threads_entry.current(3)  # 默认4线程

        # 线程数说明
        threads_tip = ttk.Label(settings_frame, text="推荐值: 2-8线程，过多可能导致连接问题", font=("", 8), foreground="grey")
        threads_tip.grid(row=1, column=1, sticky="e", pady=5, padx=5)

        # 下载控制模块
        control_frame = ttk.LabelFrame(main_frame, text="下载控制", padding=10)
        control_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, sticky="w")

        download_button = ttk.Button(button_frame, text="下载", command=download_selected_version)
        download_button.grid(row=0, column=0, padx=5)

        pause_button = ttk.Button(button_frame, text="暂停", command=pause_download, state="disabled")
        pause_button.grid(row=0, column=1, padx=5)

        resume_button = ttk.Button(button_frame, text="恢复", command=resume_download, state="disabled")
        resume_button.grid(row=0, column=2, padx=5)

        cancel_download_button = ttk.Button(button_frame, text="取消", command=cancel_download, state="disabled")
        cancel_download_button.grid(row=0, column=3, padx=5)

        # 进度显示模块
        progress_frame = ttk.LabelFrame(main_frame, text="下载进度", padding=10)
        progress_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        # 使用更现代的进度条样式
        download_pb = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", length=300)
        download_pb.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # 状态信息带框架，让布局更整洁
        status_frame = ttk.Frame(progress_frame)
        status_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        status_frame.columnconfigure(0, weight=1)

        status_label = ttk.Label(status_frame, text="请完成所有配置项", padding=5)
        status_label.grid(row=0, column=0, sticky="w")

        # 文件详情区域
        file_details_frame = ttk.Frame(progress_frame)
        file_details_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        file_details_frame.columnconfigure(0, weight=1)
        file_details_frame.columnconfigure(1, weight=1)

        # 左侧：文件大小
        size_label = ttk.Label(file_details_frame, text="", padding=2)
        size_label.grid(row=0, column=0, sticky="w")

        # 右侧：下载速度
        speed_label = ttk.Label(file_details_frame, text="", padding=2)
        speed_label.grid(row=0, column=1, sticky="e")

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
    
        # 确保进度条和详情区域能水平拉伸
        progress_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(0, weight=1)
        
        # 设置设置标签页
        pip_frame = ttk.LabelFrame(settings_tab, text="PIP包管理", padding=10)
        pip_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # 版本信息显示
        version_frame = ttk.Frame(pip_frame)
        version_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
    
        current_pip_version = get_current_pip_version()
        latest_pip_version = get_latest_pip_version()
    
        version_label = ttk.Label(version_frame, 
                                    text=f"当前pip版本: {current_pip_version}\n最新pip版本: {latest_pip_version}")
        version_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
        pip_upgrade_button = ttk.Button(version_frame, text="升级Pip", 
                                  command=pip_upgrade_wrapper)
        pip_upgrade_button.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        # 包管理区域
        package_frame = ttk.LabelFrame(pip_frame, text="包操作", padding=10)
        package_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # 包名输入区域
        name_frame = ttk.Frame(package_frame)
        name_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
    
        package_label = ttk.Label(name_frame, text="包名称:")
        package_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
        package_entry = ttk.Entry(name_frame, width=50)
        package_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # 操作按钮区域
        button_frame = ttk.Frame(package_frame)
        button_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
    
        install_button = ttk.Button(button_frame, text="安装", 
                              command=lambda: pip_install_wrapper(package_entry.get()))
        install_button.grid(row=0, column=0, padx=5)
    
        uninstall_button = ttk.Button(button_frame, text="卸载", 
                                command=lambda: pip_uninstall_wrapper(package_entry.get()))
        uninstall_button.grid(row=0, column=1, padx=5)

        # 进度显示区域
        progress_frame = ttk.Frame(package_frame)
        progress_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        pip_progress = ttk.Progressbar(progress_frame, mode="indeterminate", length=300)
        pip_progress.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        status_label = ttk.Label(progress_frame, text="")
        status_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

        # 配置网格权重
        pip_frame.columnconfigure(0, weight=1)
        package_frame.columnconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
    
        # 移除旧的直接放置在settings_tab上的组件
        for widget in settings_tab.winfo_children():
            if widget != pip_frame:
                widget.destroy()

        progress_frame.grid_columnconfigure(0, weight=1)
        settings_tab.grid_rowconfigure(0, weight=1)

            # 状态标签
        package_label = ttk.Label(settings_tab, text="", padding="10")
        package_label.grid(row=7, column=0, columnspan=3, pady=20, padx=20)
    
        # 初始化pip_manager和settings_manager
        init_pip_manager()
        
        # 修改状态标签，让其更符合中文界面
        status_label = ttk.Label(
            control_frame,
            text="请完成所有配置项",
            style="TLabel"
        )
        status_label.grid(row=5, column=0, columnspan=3, pady=5)

        def init_ui_state():
            """初始化UI状态"""
            download_button.config(state="disabled")
            status_label.config(text="请完成所有配置项")
            
            # 设置主题
            try:
                if theme_mgr:
                    current_theme = settings_mgr.get("theme.current_theme", "系统默认")
                    app_logger.info(f"加载主题: {current_theme}")
            except Exception as e:
                error_logger.error(f"加载主题失败: {e}")
            
            # 尝试读取上次的下载目录，并设置为默认值
            try:
                last_dir = None
                if USE_NEW_LOG_SYSTEM:
                    last_dir = json_manager.read_json(os.path.join(config_path, "last_download.json"), {}).get("last_dir")
                else:
                    import json
                    last_dir_data = sav_path.read_path(config_path, "last_download.json", "read")
                    if last_dir_data:
                        last_dir = json.loads(last_dir_data).get("last_dir")
                        
                if last_dir and os.path.exists(last_dir):
                    destination_entry.delete(0, tk.END)
                    destination_entry.insert(0, last_dir)
                    app_logger.info(f"加载上次下载目录: {last_dir}")
            except Exception as e:
                error_logger.error(f"加载上次下载目录失败: {e},Line1239,{myfilenumber},init_ui_state")
    
        def validate_download_config_thread():
            """在后台线程中验证下载配置，避免在UI线程中直接运行可能阻塞的验证"""
            try:
                # 获取当前值，以便在线程中使用
                def get_ui_values():
                    values = {}
                    try:
                        values["version"] = version_combobox.get()
                        values["file_name"] = choose_file_combobox.get()
                        values["dest_path"] = destination_entry.get()
                        return values
                    except Exception as ex:
                        error_logger.error(f"获取UI值失败: {str(ex)},Line1253,{myfilenumber},validate_download_config_thread")
                        return {}
                
                # 首先在主线程中获取值
                if threading.current_thread() == threading.main_thread():
                    ui_values = get_ui_values()
                else:
                    values_queue = queue.Queue()
                    root.after(0, lambda: values_queue.put(get_ui_values()))
                    ui_values = values_queue.get(timeout=1)
                
                # 验证值
                version = ui_values.get("version", "")
                file_name = ui_values.get("file_name", "")
                dest_path = ui_values.get("dest_path", "")
                
                version_valid = validate_version(version)
                file_valid = bool(file_name)
                path_valid = validate_path(dest_path)
                all_valid = version_valid and file_valid and path_valid
                
                # 将验证结果调度到主线程
                def update_ui():
                    # 只有在界面没有正在下载的任务时才更新按钮状态
                    if not is_downloading:
                        # 更新下载按钮状态
                        if download_button and download_button.winfo_exists():
                            download_button.config(state="normal" if all_valid else "disabled")
                        
                        # 更新状态消息
                        if status_label and status_label.winfo_exists():#判断状态标签是否存在
                            all_error=[]
                            if version_valid is not None:
                                all_error.append("请选择有效的Python版本")
                            else:
                                all_error.remove("请选择有效的Python版本")
                            if file_valid is not None:
                                all_error.append("请选择要下载的文件")
                            else:
                                all_error.remove("请选择要下载的文件")
                            if path_valid is not None:
                                all_error.append("请选择有效的下载目录")
                            else:
                                all_error.remove("请选择有效的下载目录")
                            all_error_str=""
                            for i in all_error:
                                all_error_str+=i+"\n"
                            if all_error_str!="":
                                status_label.config(text=all_error_str,foreground="red")
                            else:
                                status_label.config(text="配置有效，可以开始下载")
                # 在主线程中安全地执行UI更新
                
                def update_ui_thread():
                    while True:
                        a=threading.Thread(target=update_ui, daemon=True)
                        a.start()
                        a.join()
                        time.sleep(0.3)
                threading.Thread(target=update_ui_thread, daemon=True).start()
               
            except Exception as error_ex:
                def show_error(error_msg):
                    if status_label and status_label.winfo_exists():
                        status_label.config(text=f"验证配置时出错: {error_msg},Line1302,{myfilenumber},validate_download_config_thread")
                    app_logger.error(f"验证下载配置出错: {error_msg},Line1303,{myfilenumber},validate_download_config_thread")
                
                error_msg = str(error_ex)
                if threading.current_thread() == threading.main_thread():
                    show_error(error_msg)
                else:
                    root.after(0, lambda: show_error(error_msg))
        
        # 启动验证线程
        threading.Thread(target=validate_download_config_thread, daemon=True).start()

        # 启动监控进程
        threading.Thread(target=show_name, daemon=True).start()
        
        # 检查Python安装
        check_python_installation()
        
        # 读取Python版本列表
        threading.Thread(target=read_python_list, daemon=True).start()
        
        # 设置窗口不可调整大小
        root.resizable(False, False)
        
        # 初始化UI状态
        init_ui_state()
    
        # 启动任务进度更新定时器
        root.after(500, update_task_progress)
        
        # 设置主题
        sv_ttk.set_theme("dark")
        
        def finalize_window_setup():
            """完成窗口设置"""
            root.update_idletasks()
            root.eval('tk::PlaceWindow . center')
            app_logger.info("GUI初始化完成")

        # 完成窗口设置
        finalize_window_setup()
        
        # 启动主循环
        root.mainloop()
    except Exception as e:
        error_logger.error(f"主程序执行失败: {e},Line1320,{myfilenumber},main")
        messagebox.showerror("错误", f"主程序执行失败: {e},Line1321,{myfilenumber},main")
    exit(1)

if block_features.block_start()==False:
    from get_system_build import system_build
    messagebox.showerror("错误",f"无法运行Pyquick:\n您的系统不受支持。\n(当前版本: {system_build.get_system_name()} {system_build.get_system_release_build_version()})\n请升级到macOS 10.13(Darwin 17)或更高版本。")
    exit(1)
