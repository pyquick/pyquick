import tkinter as tk
from tkinter import ttk, filedialog, messagebox
package_entry = None
import subprocess
import os
import threading
from xml.sax.handler import property_xml_string
from cryptography.fernet import Fernet
import requests
import proxy
from get_system_build import block_features
import darkdetect
import re
import time
from save_path import create_folder,sav_path
requests.packages.urllib3.disable_warnings()
import sv_ttk
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import sys
import importlib
import pip_manager  # 导入pip管理模块
import settings.settings_manager as settings_manager  # 导入设置管理模块
config_path=create_folder.get_path("pyquick","1965")
cancel_event = threading.Event()
create_folder.folder_create("pyquick","1965")

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

def python_version_reload():
    global is_reloading
    def thread():
        global is_reloading
        url=f"https://www.python.org/ftp/python/"
        is_reloading=True
        version_reload.config(text="Reloading...",state="disabled")
        try:
            with requests.get(url,verify=False) as r:
                bs = BeautifulSoup(r.content, "lxml")
                results = []
                for i in bs.find_all("a"):
                    if i.text[0].isnumeric():
                        results.append(i.text[:-1])
                if results:
                    version_reload.config(text="Sorting...")
                    is_reloading=False
                    sort_results(results)
        except Exception as e:
            logging.error(f"Python Version Reload Wrong:{e}")
    threadings=threading.Thread(target=thread)
    threadings.start()
def python_file_reload():
    r1=r'\S+/'
    def thread():
        ver1=version_combobox.get()
        if ver1!="":
            url=f"https://www.python.org/ftp/python/{ver1}"
        else:
            return
        with requests.get(url,verify=False) as r:
            bs = BeautifulSoup(r.content, "lxml")
            results = []
            for i in bs.find_all("a"):
                if (re.match(r1,i.text)==None) and (i.text[-1]!="/") and(".exe" not in i.text) and("-embed-"not in i.text):
                    results.append(i.text)
        ver2=version_combobox.get()
        if ver1==ver2:
            choose_file_combobox.configure(values=results)
        else:
            choose_file_combobox.configure(values=[])
    while True:
        threading.Thread(target=thread).start()
        time.sleep(0.3)
def read_python_list():
    base1=str(sav_path.read_path(config_path,"python_version_list.txt","readline"))
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

def download_file(selected_version, destination_path, num_threads):
    """下载指定版本的Python安装程序"""
    global file_size, executor, futures, downloaded_bytes, is_downloading, destination, url,lock
    
    # 加载代理配置
    proxy_config = load_proxy_config()
    proxies = None
    if proxy_config and proxy_config.get('enabled'):
        proxy_addr = proxy_config.get('proxy')
        proxy_port = proxy_config.get('port')
        if proxy_addr and proxy_port:
            if proxy_config.get('use_auth'):
                username = proxy_config.get('username')
                password = proxy_config.get('password')
                if username and password:
                    proxies = {
                        "http": f"http://{username}:{password}@{proxy_addr}:{proxy_port}",
                        "https": f"http://{username}:{password}@{proxy_addr}:{proxy_port}"
                    }
            else:
                proxies = {
                    "http": f"http://{proxy_addr}:{proxy_port}",
                    "https": f"https://{proxy_addr}:{proxy_port}"
                }
    
    # 计算每个线程下载的数据块大小
    chunk_size = file_size // num_threads
    lock = threading.Lock()
    futures = []
    downloaded_bytes = [0]
    is_downloading = True
    # 设置进度条为不定式模式
    download_pb.config(mode="indeterminate")
    download_pb.start()
    # 验证目标路径是否有效
    if not validate_path(destination_path):
        status_label.config(text="Invalid destination path")
        download_pb.stop()
        download_pb.config(mode="determinate")
        download_pb['value'] = 0
        enable_download()


    # 构造文件名和目标路径
    file_name = choose_file_combobox.get()
    destination = os.path.join(destination_path, file_name)

    url = f"https://www.python.org/ftp/python/{selected_version}/{file_name}"

    # 获取文件大小
    try:
        # 获取代理设置
        proxy_settings = None
        if proxy.proxy_check_status(1965):
            result = proxy.read_proxy(1965)
            username = result['username'] if proxy.password_check_status(1965) else None
            password = result['password'] if proxy.password_check_status(1965) else None
            proxy_settings = proxy.proxy_address(result['address'], result['port'], username, password, result['key'].encode())

        response = requests.head(url, timeout=10, verify=False, proxies=proxy_settings)
        response.raise_for_status()
        file_size = int(response.headers['Content-Length'])
    except requests.RequestException as e:
        status_label.config(text=f"Failed to get file size: {str(e)}")
        download_pb.stop()
        download_pb.config(mode="determinate")
        download_pb['value'] = 0
        enable_download()


    # 创建目标文件并预分配空间
    try:
        with open(destination, 'wb') as f:
            f.truncate(file_size)
    except IOError as e:
        status_label.config(text=f"Failed to create file: {str(e)}")
        download_pb.stop()
        download_pb.config(mode="determinate")
        download_pb['value'] = 0
        enable_download()




    # 使用线程池执行下载任务
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for i in range(num_threads):
            if not is_downloading:
                break
            start_byte = i * chunk_size
            end_byte = start_byte + chunk_size - 1 if i != num_threads - 1 else file_size - 1
            futures.append(executor.submit(download_chunk, url, start_byte, end_byte, destination))

        # 显示并启用取消下载按钮
        cancel_download_button.grid(row=5, column=0, columnspan=3, pady=20, padx=20)
        cancel_download_button.config(state="normal")
        
        # 设置进度条为定式模式
        download_pb.config(mode="determinate")
        download_pb.stop()
        download_pb['value'] = 0
        download_pb['maximum'] = 100
        
        # 启动一个线程来更新下载进度
        threading.Thread(target=update_progress, daemon=True).start()

def download_chunk(url, start_byte, end_byte, destination, retries=5):
    """下载文件的指定部分"""
    global is_downloading
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    
    # 加载代理配置
    proxy_config = load_proxy_config()
    proxies = None
    if proxy_config and proxy_config.get('enabled'):
        proxy_addr = proxy_config.get('proxy')
        proxy_port = proxy_config.get('port')
        if proxy_addr and proxy_port:
            if proxy_config.get('use_auth'):
                username = proxy_config.get('username')
                password = proxy_config.get('password')
                if username and password:
                    proxies = {
                        "http": f"http://{username}:{password}@{proxy_addr}:{proxy_port}",
                        "https": f"http://{username}:{password}@{proxy_addr}:{proxy_port}"
                    }
            else:
                proxies = {
                    "http": f"http://{proxy_addr}:{proxy_port}",
                    "https": f"https://{proxy_addr}:{proxy_port}"
                }
    
    for attempt in range(retries):
        if not is_downloading:
            return False
        try:
            # 发起请求
            with requests.get(url, headers=headers, stream=True, verify=False, proxies=proxies) as response:
                response.raise_for_status()
                # 写入文件
                with lock:
                    with open(destination, 'r+b') as f:
                        f.seek(start_byte)
                        for chunk in response.iter_content(chunk_size=8192):
                            if not is_downloading:
                                return False
                            f.write(chunk)
                            with lock:
                                downloaded_bytes[0] += len(chunk)
            return True
                
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            with lock:
                status_label.config(text=f"Download Failed!")
                is_downloading = False
                download_pb.stop()
                download_pb.config(mode="determinate")
                download_pb['value'] = 0
            return False

def update_progress():
    """更新进度条和状态标签"""
    global file_size, is_downloading
    
    start_time = time.time()  # 记录下载开始时间
    last_bytes = 0  # 记录上一次的下载字节数
    
    while any(not future.done() for future in futures):
        if not is_downloading:
            break
        with lock:
            current_bytes = downloaded_bytes[0]
        cancel_download_button.grid(row=5, column=0, columnspan=3, pady=20, padx=20)
        progress = float(current_bytes / file_size * 100) if file_size != 0 else 0  # 保留3位小数
        download_pb['value'] = progress
        download_pb.update()  # 确保进度条及时更新
        # 计算下载速度
        elapsed = time.time() - start_time
        speed = (current_bytes - last_bytes) / elapsed if elapsed > 0 else 0

        # 更新速度显示
        speed_kb = speed / 1024
        speed_text = f"{speed_kb:.2f} KB/s" if speed_kb < 1024 else f"{speed_kb / 1024:.2f} MB/s"

        status_label.config(text=f"Downloading: {progress:.3f}% ({speed_text})")

        last_bytes = current_bytes
        start_time = time.time()  # 重置计时器
        time.sleep(0.2)  # 降低更新频率避免闪烁
        
    if is_downloading:
        download_pb['value'] = 100
        status_label.config(text="Download Complete!")
        enable_download()
    else:
        download_pb['value'] = 0
        status_label.config(text="Download Cancelled!")
        enable_download()
        
    is_downloading = False
    cancel_download_button.grid_forget()

def cancel_download():
    global executor,is_downloading
    if is_downloading:
        cancel_event.set()
        executor.shutdown(wait=False)
        is_downloading = False
        status_label.config(text="Cancelling download...")
        download_pb['value'] = 0  # 重置进度条
        cancel_download_button.grid_forget()  # 立即隐藏取消按钮
        
        destination_path = destination_entry.get()
        filename=choose_file_combobox.get()
        file_name = filename
        destination = os.path.join(destination_path, file_name)
        
        if os.path.exists(destination):
            os.remove(destination)
            status_label.config(text="Download cancelled and incomplete file removed.")
            enable_download()
        else:
            status_label.config(text="Download cancelled.")
            enable_download()
    root.after(3000, clear_a)

def disable_download():
    version_combobox.config(state="disabled")
    choose_file_combobox.config(state="disabled")
    destination_entry.config(state="disabled")
    threads_entry.config(state="disabled")
    version_reload.config(state="disabled")
    select_button.config(state="disabled")
    download_button.config(state="disabled")
    
def enable_download():
    global is_reloading
    version_combobox.config(state="readonly")
    choose_file_combobox.config(state="readonly")
    destination_entry.config(state="normal")
    threads_entry.config(state="readonly")
    download_button.config(state="normal")
    try:
        if is_reloading:
            version_reload.config(state="disabled")
        else:
            version_reload.config(state="normal")
    except:
        version_reload.config(state="normal")
    select_button.config(state="normal")
    cancel_download_button.grid_forget()

def sort_results(results: list):
    global is_downloading
    _results = results.copy()
    length = len(_results)
    for i in range(length):
        for ii in range(0, length - i - 1):
            v1 = Version(_results[ii])
            v2 = Version(_results[ii + 1])
            if v1 < v2:
                _results[ii], _results[ii + 1] = _results[ii + 1], _results[ii]
    version_combobox.configure(values=_results)
    sav_path.save_path(config_path,"python_version_list.txt","w",_results)
    try:
        if is_downloading:
            version_reload.config(text="Reload",state="disabled")
        else:
            version_reload.config(text="Reload",state="normal")
    except:
        version_reload.config(text="Reload",state="normal")

def download_selected_version():
    """开始下载选定的Python版本"""
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    num_threads = int(threads_entry.get())

    if not os.path.exists(destination_path):
        status_label.config(text="Invalid path!")
        root.after(5000, clear_a)
        return
    if choose_file_combobox.get()==None or choose_file_combobox.get()=="":
        status_label.config(text="Please choose a file!")
        root.after(5000,clear_a)
        return
    disable_download()
    cancel_download_button.config(state="normal")
    cancel_download_button.grid(row=5, column=0, columnspan=3, pady=20, padx=20)  # 确保取消按钮可见

    clear_a()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    threading.Thread(target=download_file, args=(selected_version, destination_path, num_threads), daemon=True).start()

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
    if(datetime.datetime.now()>=datetime.datetime(2025,5,2)):
        messagebox.showerror("Error","You can not open python_tool:exitcode(0x1)")
        exit(1)
    elif(datetime.datetime.now()>=datetime.datetime(2025,4,1)):
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

    framea_tab = ttk.Frame(fmode)
    framea_tab.pack(padx=20, pady=20)

    settings_tab=ttk.Frame(fsettings)
    settings_tab.pack(padx=20, pady=20)


    #PYTHON VERSION
    version_label = ttk.Label(framea_tab, text="Select Python Version:")
    version_label.grid(row=0, column=0, pady=20, padx=20)


    selected_version = tk.StringVar()
    version_combobox = ttk.Combobox(framea_tab, textvariable=selected_version, values=[], state="read")
    version_combobox.grid(row=0, column=1, pady=20, padx=20)
    version_reload=ttk.Button(framea_tab,text="Reload",command=python_version_reload)
    version_reload.grid(row=0,column=2, pady=20, padx=20)


    
    

    destination_label = ttk.Label(framea_tab, text="Select Destination:")
    destination_label.grid(row=1, column=0, pady=20, padx=20)

    destination_entry = ttk.Entry(framea_tab, width=50)
    destination_entry.grid(row=1, column=1, pady=20, padx=20)

    select_button = ttk.Button(framea_tab, text="Select", command=select_destination)
    select_button.grid(row=1, column=2, pady=20, padx=20)

    threads_label = ttk.Label(framea_tab, text="Number of Threads:")
    threads_label.grid(row=2, column=0, pady=20, padx=20)

    threads = tk.IntVar()
    threads_entry = ttk.Combobox(framea_tab, width=10,textvariable=threads,values=[str(i) for i in range(1, 129)],state="readonly")
    threads_entry.grid(row=2, column=1, pady=20, padx=20)
    threads_entry.current(7)

    choose_label=ttk.Label(framea_tab,text="Choose a File:")
    choose_label.grid(row=3,column=0, pady=20, padx=20)
    choose_file=tk.StringVar()
    choose_file_combobox=ttk.Combobox(framea_tab,textvariable=choose_file,values=[],state="readonly",width=50)
    choose_file_combobox.grid(row=3,column=1,columnspan=3, pady=20, padx=20)
    #DOWNLOAD
    download_button = ttk.Button(framea_tab, text="Download Selected Version", command=download_selected_version)
    download_button.grid(row=4, column=0, columnspan=5, pady=20, padx=20)

    cancel_download_button = ttk.Button(framea_tab, text="Cancel Download", command=cancel_download, state="disabled")
    cancel_download_button.grid_forget()

    
    download_pb=ttk.Progressbar(framea_tab,length=800)
    download_pb.grid(row=6,column=0,pady=80,columnspan=3, padx=20)
    
    status_label = ttk.Label(framea_tab, text="", padding="10")
    status_label.grid(row=7, column=0, columnspan=3, pady=20, padx=20)

    #PIP(UPDRADE)
    pip_upgrade_button = ttk.Button(settings_tab, text="Upgrade pip", command=pip_manager.upgrade_pip)
    pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=20, padx=20)

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

    # Set sv_ttk theme
    threading.Thread(target=python_file_reload, daemon=True).start()
    check_python_installation()
    threading.Thread(target=read_python_list, daemon=True).start()
    root.resizable(False,False)
    settings_manager.load_theme()  # 使用settings_manager中的函数
    root.mainloop()
    #root.after(3000,)
if block_features.block_start()==False:
    from get_system_build import system_build
    messagebox.showerror("Error",f"You can not open Pyquick:\nYour system is not supported. \n(Your version: {system_build.get_system_name()} {system_build.get_system_release_build_version()})\n Please upgrade to macOS 10.13(Darwin 17) or later.")
    exit(1)