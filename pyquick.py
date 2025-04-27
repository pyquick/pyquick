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
import pip_manager  # 导入pip管理模块
import settings.settings_manager as settings_manager  # 导入设置管理模块
from downloader import Downloader, DownloadManager  # 导入下载器模块

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pyquick.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('pyquick')

# 全局线程池
THREAD_POOL = ThreadPoolExecutor(max_workers=10, thread_name_prefix="PyquickWorker")
# UI更新队列
UI_UPDATE_QUEUE = queue.Queue()

config_path=create_folder.get_path("pyquick","1965")
cancel_event = threading.Event()
create_folder.folder_create("pyquick","1965")

# 全局变量
download_manager = None  # 下载管理器实例
current_task_id = None   # 当前下载任务ID

def install_package(package):
    try:
        importlib.import_module(package)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            logging.error(f"Failed to install {package}")
            return False
    return True

# 自动安装依赖
install_package("memory_profiler")
from debug_info.ui import DebugInfoWindow
# 排序版本获取结果
def sort_results(results: list):
    _results = results.copy()
    length = len(_results)
    for i in range(length):
        for ii in range(0, length - i - 1):
            v1 = Version(_results[ii])
            v2 = Version(_results[ii + 1])
            if v1 < v2:
                _results[ii], _results[ii + 1] = _results[ii + 1], _results[ii]
    version_combobox.configure(values=_results)
    with open(os.path.join(config_path, "version.txt"), "w") as f:
        f.write(str(_results))
def python_version_reload():
    global is_reloading
    def thread():
        global is_reloading
        url = "https://www.python.org/ftp/python/"
        is_reloading = True
        version_reload.config(text="Reloading...", state="disabled")
        
        # 设置重试次数和延迟
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 配置requests会话
                session = requests.Session()
                session.verify = False
                session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                response = session.get(url, timeout=10)
                response.raise_for_status()
                
                bs = BeautifulSoup(response.content, "lxml")
                results = []
                for i in bs.find_all("a"):
                    if i.text[0].isnumeric():
                        results.append(i.text[:-1])
                        
                if results:
                    version_reload.config(text="Sorting...")
                    is_reloading = False
                    sort_results(results)
                    version_reload.config(text="Reload", state="normal")
                    break
                    
            except requests.exceptions.SSLError as e:
                logging.error(f"SSL Error (attempt {attempt + 1}/{max_retries}): {e}")
            except requests.exceptions.RequestException as e:
                logging.error(f"Request Error (attempt {attempt + 1}/{max_retries}): {e}")
            except Exception as e:
                logging.error(f"Unexpected Error (attempt {attempt + 1}/{max_retries}): {e}")
                
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # 指数退避
            else:
                version_reload.config(text="Reload failed", state="normal")
                is_reloading = False
                
    threading.Thread(target=thread, daemon=True).start()
def python_file_reload():
    r1 = r'\S+/'
    stop_event = threading.Event()
    
    def thread():
        session = requests.Session()
        session.verify = False
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        while not stop_event.is_set():
            ver1 = version_combobox.get()
            if not ver1:
                time.sleep(0.3)
                continue
                
            url = f"https://www.python.org/ftp/python/{ver1}"
            max_retries = 3
            retry_delay = 1
            
            for attempt in range(max_retries):
                try:
                    response = session.get(url, timeout=10)
                    response.raise_for_status()
                    
                    bs = BeautifulSoup(response.content, "lxml")
                    results = []
                    for i in bs.find_all("a"):
                        if (re.match(r1, i.text) is None and 
                            i.text[-1] != "/" and 
                            ".exe" not in i.text and 
                            "-embed-" not in i.text):
                            results.append(i.text)
                    
                    ver2 = version_combobox.get()
                    if ver1 == ver2:
                        choose_file_combobox.configure(values=results)
                    else:
                        choose_file_combobox.configure(values=[])
                    break
                    
                except requests.exceptions.SSLError as e:
                    logging.error(f"SSL Error (attempt {attempt + 1}/{max_retries}): {e}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"Request Error (attempt {attempt + 1}/{max_retries}): {e}")
                except Exception as e:
                    logging.error(f"Unexpected Error (attempt {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
            
            time.sleep(0.3)
    
    thread = threading.Thread(target=thread, daemon=True)
    thread.start()
    return stop_event  # 返回停止事件，以便在需要时停止线程
def read_python_list():
    base1=str(sav_path.read_path(config_path,"version.txt","readline"))
    base2=base1.strip("[]").split(",")
    base3=[]
    for i in base2:
        j=i.strip("'")
        base3.append(j.strip(" '"))
    version_combobox.configure(values=base3)

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
        import json
        proxy_config = sav_path.read_path(config_path, "proxy.json", "read")
        if proxy_config:
            return json.loads(proxy_config)
    except:
        pass
    return None

def init_download_manager():
    """初始化下载管理器"""
    global download_manager
    if download_manager is None:
        # 优化线程数配置
        thread_count = min(max(2, int(threads_entry.get())), os.cpu_count() * 2)
        download_manager = DownloadManager(
            task_db_path=os.path.join(config_path, "downloads.json"),
            max_concurrent_downloads=min(3, os.cpu_count()),
            num_threads_per_download=thread_count,
            on_task_status_changed=on_download_status_changed
        )
        logger.info(f"Download manager initialized with {thread_count} threads per download")

def on_download_status_changed(task_id, status):
    """下载状态变化回调函数"""
    if task_id == current_task_id:
        update_download_ui()

def update_download_ui():
    """更新下载UI"""
    if not current_task_id:
        return

    # 使用UI更新队列来处理界面更新
    try:
        task = download_manager.get_task(current_task_id)
        if not task:
            return

        UI_UPDATE_QUEUE.put({
            'task': task,
            'status': task.status,
            'progress': task.progress,
            'speed': task.speed,
            'total_size': task.total_size,
            'downloaded_size': task.downloaded_size,
            'error': task.error if hasattr(task, 'error') else None
        })
        
        # 使用after方法在主线程中处理UI更新
        root.after(1, process_ui_updates)
    except Exception as e:
        logger.error(f"Error updating UI: {str(e)}")

def process_ui_updates():
    """处理UI更新队列"""
    try:
        while not UI_UPDATE_QUEUE.empty():
            update = UI_UPDATE_QUEUE.get_nowait()
            task = update['task']
            
            # 更新进度条
            if update['status'] == 'downloading':
                download_pb['value'] = update['progress']
                speed_kb = update['speed'] / 1024
                speed_text = f"{speed_kb:.2f} KB/s" if speed_kb < 1024 else f"{speed_kb / 1024:.2f} MB/s"
                
                remaining_mb = (update['total_size'] - update['downloaded_size']) / (1024 * 1024)
                eta = task.get_eta() if hasattr(task, 'get_eta') else 0
                eta_text = f"ETA: {eta:.0f}s" if eta else ""
                
                status_text = f"Downloading: {update['progress']:.1f}% ({speed_text}) - {remaining_mb:.1f}MB remaining {eta_text}"
                status_label.config(text=status_text)
                
                update_button_states(True, False, True)
                
            elif update['status'] == 'paused':
                status_label.config(text="Download paused")
                update_button_states(False, True, True)
                
            elif update['status'] == 'completed':
                download_pb['value'] = 100
                status_label.config(text="Download completed successfully")
                update_button_states(True, False, False)
                
            elif update['status'] in ['cancelled', 'error']:
                download_pb['value'] = 0
                error_text = f"Download failed: {update['error']}" if update['status'] == 'error' else "Download cancelled by user"
                status_label.config(text=error_text)
                update_button_states(True, False, False)
                
    except Exception as e:
        logger.error(f"Error processing UI updates: {str(e)}")
    finally:
        # 继续处理队列中的更新
        if not UI_UPDATE_QUEUE.empty():
            root.after(1, process_ui_updates)

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
            if task and task.status == 'downloading':
                update_download_ui()
                
        # 动态调整刷新间隔
        progress = download_pb['value']
        refresh_interval = min(
            2000 if progress > 95 else  # 接近完成时大幅降低刷新频率
            1000 if progress > 80 else  # 高进度时降低刷新频率
            500,                        # 正常刷新频率
        )
        root.after(refresh_interval, update_task_progress)
    except Exception as e:
        logger.error(f"Error in task progress update: {str(e)}")
        root.after(1000, update_task_progress)  # 发生错误时使用较长的刷新间隔

def validate_download_config():
    """验证下载配置是否有效"""
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    file_name = choose_file_combobox.get()
    thread_count = threads_entry.get()
    
    # 初始化时默认禁用下载按钮
    download_button.config(state="disabled")
    
    # 收集所有错误信息
    errors = []
    
    # 验证版本选择
    if not selected_version:
        errors.append("请选择Python版本！")
    
    # 验证目标路径
    if not destination_path or not os.path.exists(destination_path):
        errors.append("路径无效！")
    
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
    
    # 如果有错误，显示所有错误信息
    if errors:
        status_label.config(text="\n".join(errors), style="Error.TLabel", foreground="red")
        return False
    
    # 所有验证通过才启用下载按钮
    download_button.config(state="normal")
    return True

def download_selected_version():
    """开始下载选定的Python版本"""
    global current_task_id
    
    # 验证下载配置
    if not validate_download_config():
        return
    
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    file_name = choose_file_combobox.get()
    
    # 初始化下载管理器
    init_download_manager()
    
    # 构建下载URL和文件保存路径
    url = f"https://www.python.org/ftp/python/{selected_version}/{file_name}"
    save_path = os.path.join(destination_path, file_name)
    
    from downloader import download_manager
    # 创建下载任务
    current_task_id = download_manager.add_task(
        url=url,
        file_path=destination_path,
        thread_count=4,
        proxies=None
    )
    
    # 更新UI
    update_download_ui()

def cancel_download():
    """取消下载"""
    global current_task_id
    if current_task_id:
        download_manager.cancel_task(current_task_id)
        update_download_ui()

def resume_download():
    """恢复下载"""
    global current_task_id
    if current_task_id:
        download_manager.resume_task(current_task_id)
        update_download_ui()

def pause_download():
    """暂停下载"""
    global current_task_id
    if current_task_id:
        download_manager.pause_task(current_task_id)
        update_download_ui()

def show_about():
    time_lim=(datetime.datetime(2025,5,2)-datetime.datetime.now()).days
    if (datetime.datetime.now()>=datetime.datetime(2025,4,1)):
        messagebox.showwarning("About", f"Version: dev\nBuild: 1962\n{time_lim} days left.")
    else:
        messagebox.showinfo("About", f"Version: dev\nBuild: 1962\n{time_lim} days left.")

def on_closing():
    global is_downloading
    if is_downloading:
        cancel_download()
    settings_manager.save_theme()  # 使用settings_manager中的函数
    root.destroy()
    exit(0)
    subprocess.Popen("killall Python",text=True,shell=True)
    subprocess.Popen("killall pyquick",text=True,shell=True)
    subprocess.Popen("killall Pyquick",text=True,shell=True)











#GUI
if __name__ == "__main__" and block_features.block_start():
    #启动laugh = True
    if(datetime.datetime.now()>=datetime.datetime(2025,9,2)):
        messagebox.showerror("Error","You can not open python_tool:exitcode(0x1)")
        exit(1)
    elif(datetime.datetime.now()>=datetime.datetime(2025,8,1)):
        messagebox.showwarning("up","Will cannot open on 2025,5.2")
    
    root = tk.Tk()
    root.title("Pyquick")
    root.protocol("WM_DELETE_WINDOW", on_closing)
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    help_menu = tk.Menu(menu_bar, tearoff=0)
    settings_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)
    settings_menu.add_command(label="Settings", command=settings_manager.open_settings)  # 使用settings_manager中的函数
    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=show_about)
    help_menu.add_separator()

    #TAB CONTROL
    tab_control = ttk.Notebook(root)
    #MODE TAB
    fmode = ttk.Frame(root, padding="20")
    tab_control.add(fmode,text="Python Download")
    tab_control.grid(row=0, padx=10, pady=10)

    fsettings=ttk.Frame(root,padding="20")
    tab_control.add(fsettings,text="Pip")
    tab_control.grid(row=0, padx=10, pady=10)

    # 创建主下载界面框架
    main_frame = ttk.Frame(fmode)
    main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    settings_tab=ttk.Frame(fsettings)
    settings_tab.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

    # 版本选择模块
    version_frame = ttk.LabelFrame(main_frame, text="Version Selection", padding=10)
    version_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    version_label = ttk.Label(version_frame, text="Python Version:")
    version_label.grid(row=0, column=0, pady=5, padx=5)

    selected_version = tk.StringVar()
    version_combobox = ttk.Combobox(version_frame, textvariable=selected_version, values=[], state="read", width=30)
    version_combobox.grid(row=0, column=1, pady=5, padx=5)

    version_reload = ttk.Button(version_frame, text="Reload Versions", command=python_version_reload)
    version_reload.grid(row=0, column=2, pady=5, padx=5)

    # 文件选择模块
    file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
    file_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")

    choose_label = ttk.Label(file_frame, text="Python Package:")
    choose_label.grid(row=0, column=0, pady=5, padx=5)

    choose_file = tk.StringVar()
    choose_file_combobox = ttk.Combobox(file_frame, textvariable=choose_file, values=[], state="readonly", width=50)
    choose_file_combobox.grid(row=0, column=1, columnspan=2, pady=5, padx=5)

    # 下载设置模块
    settings_frame = ttk.LabelFrame(main_frame, text="Download Settings", padding=10)
    settings_frame.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

    destination_label = ttk.Label(settings_frame, text="Save Location:")
    destination_label.grid(row=0, column=0, pady=5, padx=5)

    destination_entry = ttk.Entry(settings_frame, width=50)
    destination_entry.grid(row=0, column=1, pady=5, padx=5)

    select_button = ttk.Button(settings_frame, text="Browse", command=select_destination)
    select_button.grid(row=0, column=2, pady=5, padx=5)

    threads_label = ttk.Label(settings_frame, text="Threads:")
    threads_label.grid(row=1, column=0, pady=5, padx=5)

    threads = tk.IntVar()
    threads_entry = ttk.Combobox(settings_frame, width=10, textvariable=threads, values=[str(i) for i in range(1, 129)], state="readonly")
    threads_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
    threads_entry.current(7)

    # 下载控制模块
    control_frame = ttk.LabelFrame(main_frame, text="Download Control", padding=10)
    control_frame.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

    button_frame = ttk.Frame(control_frame)
    button_frame.grid(row=0, column=0, sticky="w")

    download_button = ttk.Button(button_frame, text="Download", command=download_selected_version)
    download_button.grid(row=0, column=0, padx=5)

    pause_button = ttk.Button(button_frame, text="Pause", command=pause_download, state="disabled")
    pause_button.grid(row=0, column=1, padx=5)

    resume_button = ttk.Button(button_frame, text="Resume", command=resume_download, state="disabled")
    resume_button.grid(row=0, column=2, padx=5)

    cancel_download_button = ttk.Button(button_frame, text="Cancel", command=cancel_download)
    cancel_download_button.grid(row=0, column=3, padx=5)

    # 进度显示模块
    progress_frame = ttk.LabelFrame(main_frame, text="Download Progress", padding=10)
    progress_frame.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

    download_pb = ttk.Progressbar(progress_frame, orient="horizontal", mode="determinate", length=280)
    download_pb.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

    status_label = ttk.Label(progress_frame, text="", padding=5)
    status_label.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    main_frame.grid_rowconfigure(0, weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    pip_upgrade_button = ttk.Button(settings_tab, text="Upgrade Pip", command=pip_manager.upgrade_pip)
    pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=20, padx=20)
    
    progress_frame.grid_columnconfigure(0, weight=1)
    settings_tab.grid_rowconfigure(0, weight=1)

    package_label = ttk.Label(settings_tab, text="Enter Package Name:")
    package_label.grid(row=1, column=0, pady=20, padx=20)

    package_entry = ttk.Entry(settings_tab, width=60)
    package_entry.grid(row=1, column=1, pady=20, padx=20)

    #PIP(INSTALL)
    install_button = ttk.Button(settings_tab, text="Install Package", command=pip_manager.install_package)
    install_button.grid(row=2, column=0, columnspan=3, pady=20, padx=20)

    #PIP(UNINSTALL)
    uninstall_button = ttk.Button(settings_tab, text="Uninstall Package", command=pip_manager.uninstall_package)
    uninstall_button.grid(row=3, column=0, columnspan=3, pady=20, padx=20)

    #progressbar-options:length(number),mode(determinate(从左到右)，indeterminate(来回滚动)),...length=500,mode="indeterminate"
    package_label = ttk.Label(settings_tab, text="", padding="10")
    package_label.grid(row=7, column=0, columnspan=3, pady=20, padx=20)
    
    # 初始化pip_manager和settings_manager
    pip_manager.init_ui_references(root, package_label, install_button, pip_upgrade_button, uninstall_button, package_entry)
    settings_manager.init_settings_manager(root, config_path)
    
    # 启动更新任务进度的定时器
    root.after(500, update_task_progress)

    # Set sv_ttk theme
    threading.Thread(target=python_file_reload, daemon=True).start()
    check_python_installation()
    threading.Thread(target=read_python_list, daemon=True).start()
    root.resizable(False,False)
    settings_manager.load_theme() 
    status_label = ttk.Label(
        control_frame,
        text="请完成所有配置项",
        style="Error.TLabel"
    )
    status_label.grid(row=5, column=0, columnspan=3, pady=5)

    # 初始化下载按钮状态
    download_button.config(state="disabled")
    status_label.config(text="请完成所有配置项", style="Error.TLabel")
    
    # 在界面元素初始化后调用验证
    def validate_download_config_threadind():
        while True:
            a=threading.Thread(target=validate_download_config,daemon=True)
            a.start()
            a.join()
            
    threading.Thread(target=validate_download_config_threadind,daemon=True).start()   
    root.mainloop()
    #root.after(3000,)
if block_features.block_start()==False:
    from get_system_build import system_build
    messagebox.showerror("Error",f"You can not open Pyquick:\nYour system is not supported. \n(Your version: {system_build.get_system_name()} {system_build.get_system_release_build_version()})\n Please upgrade to macOS 10.13(Darwin 17) or later.")
    exit(1)
