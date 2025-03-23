import tkinter as tk
from tkinter import ttk, filedialog,messagebox
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
config_path=create_folder.get_path("pyquick","1965")
cancel_event = threading.Event()
create_folder.folder_create("pyquick","1965")
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

def download_file(selected_version, destination_path, num_threads):
    """下载指定版本的Python安装程序"""
    global file_size, executor, futures, downloaded_bytes, is_downloading, destination, url,lock
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
    
    for attempt in range(retries):
        if not is_downloading:
            return False
        try:
            # 获取代理设置

            if proxy.proxy_check_status(1965):
                result = proxy.read_proxy(1965)
                username = result['username'] if proxy.password_check_status(1965) else None
                password = result['password'] if proxy.password_check_status(1965) else None
                proxy_settings = proxy.proxy_address(result['address'], result['port'], username, password, result['key'].encode())
            else:
                proxy_settings = None
            # 发起请求
            with requests.get(url, headers=headers, stream=True,verify=False, proxies=proxy_settings) as response:
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

def disabled_pip():
    install_button.config(state="disabled")
    pip_upgrade_button.config(state="disabled")
    uninstall_button.config(state="disabled")
    package_entry.config(state="disabled")
def return_pip():
    install_button.config(state="normal")
    pip_upgrade_button.config(state="normal")
    uninstall_button.config(state="normal")
    package_entry.config(state="normal")
def get_current_pip_version():
    try:
        result = subprocess.check_output(["python3", "-m", "pip", "--version"])
        version_str = result.decode().strip().split()[1]
        return version_str
    except Exception as e:
        logging.error(f"Error getting pip version: {e}")
        return "Unknown"
def get_latest_pip_version():
    try:
        response = requests.get("https://pypi.org/pypi/pip/json", verify=False)
        data = response.json()
        version_str = data["info"]["version"]
        return version_str
    except Exception as e:
        logging.error(f"Error getting latest pip version: {e}")
        return "Unknown"
def upgrade_pip():
    def upgrade_pip_thread():
        try:
            disabled_pip()
            current_version = get_current_pip_version()
            latest_version = get_latest_pip_version()
            if current_version == "Unknown" or latest_version == "Unknown":
                if current_version == "Unknown":
                    package_label.config(text="Error getting current pip version.")
                if latest_version == "Unknown":
                    package_label.config(text="Error getting latest pip version.")
            if current_version == latest_version:
                package_label.config(text=f"Pip is already up-to-date (v{current_version}).")
            else:
                package_label.config(text=f"Upgrading pip from v{current_version} to v{latest_version}...")
                try:
                    result=subprocess.run(["pip3", "install", "--upgrade", "pip", "--break-system-packages"], text=True,capture_output=True)
                    if "Successfully installed" in result.stdout:
                        package_label.config(text=f"Pip has been upgraded to v{latest_version}.")

                except subprocess.CalledProcessError as e:
                    package_label.config(text=f"Error upgrading pip: {e.output}")
        except Exception as e:
            logging.error(f"Error upgrading pip: {e}")
            package_label.config(text=f"Error upgrading pip: {str(e)}")
        return_pip()
        root.after(3000, clear_a)
    upgrade_thread = threading.Thread(target=upgrade_pip_thread, daemon=True)
    upgrade_thread.start()

    

        
#try_update(["python3","-m","pip3", "install", "--upgrade", "pip", "--break-system-packages"])


def install_package():
    def clear_status_label():
        root.after(3000, clear_a)
    package_name = package_entry.get()
    def install_package_thread():
        disabled_pip()
        try:
            installed_packages = subprocess.check_output(["python3", "-m", "pip", "list", "--format=columns"], text=True)
            if package_name.lower() in installed_packages.lower():
                package_label.config(text=f"Package '{package_name}' is already installed.")
            else:
                result = subprocess.run(["python3", "-m", "pip", "install", package_name], capture_output=True, text=True)
                if "Successfully installed" in result.stdout:
                    package_label.config(text=f"Package '{package_name}' has been installed successfully!")
                else:
                    package_label.config(text=f"Error installing package '{package_name}': {result.stderr}")
        except subprocess.CalledProcessError as e:
            status_label.config(text=f"Error running pip command: {e.output}")
        except Exception as e:
            status_label.config(text=f"Error installing package '{package_name}': {str(e)}")
        return_pip()
        clear_status_label()
    install_thread = threading.Thread(target=install_package_thread, daemon=True)
    install_thread.start()
def uninstall_package():
    package_name = package_entry.get()
    def uninstall_package_thread():
        disabled_pip()
        try:
            installed_packages = subprocess.check_output(["python3", "-m", "pip", "list", "--format=columns"], text=True)
            if package_name.lower() in installed_packages.lower():
                result = subprocess.run(["python3", "-m", "pip", "uninstall", "-y", package_name], capture_output=True, text=True)
                if "Successfully uninstalled" in result.stdout:
                    package_label.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                    root.after(3000,clear_a)
                else:
                    package_label.config(text=f"Cannot uninstall package '{package_name}': {result.stderr}")
                    root.after(3000,clear_a)
            else:
                package_label.config(text=f"Package '{package_name}' is not installed.")
                root.after(3000,clear_a)
        except Exception as e:
            package_label.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
            root.after(3000,clear_a)
        return_pip()
    uninstall_thread = threading.Thread(target=uninstall_package_thread, daemon=True)
    uninstall_thread.start()





def show_about():
    time_lim=(datetime.datetime(2025,5,2)-datetime.datetime.now()).days
    if (datetime.datetime.now()>=datetime.datetime(2025,4,1)):
        messagebox.showwarning("About", f"Version: dev\nBuild: 1962\n{time_lim} days left.")
    else:
        messagebox.showinfo("About", f"Version: dev\nBuild: 1962\n{time_lim} days left.")
def load_theme():
    if block_features.block_theme():
        try:
            theme=sav_path.read_path(config_path,"theme.txt","readline")
            if theme=="light":
                sv_ttk.set_theme("light")
            elif theme=="dark":
                sv_ttk.set_theme("dark")
            else:
                sv_ttk.set_theme(darkdetect.theme())
        except FileNotFoundError:
            sv_ttk.set_theme(darkdetect.theme())
        except Exception as e:
            sv_ttk.set_theme(darkdetect.theme())
    else:
        try:
            sav_path.remove_file(config_path,"theme.txt")
        except:
            pass
def save_theme():
    if block_features.block_theme():
        theme=sv_ttk.get_theme()
        sav_path.save_path(config_path,"theme.txt","w",theme)
def settings():

    def save_proxy():
        import proxy
        def thread():
            try:
                proxy.save_proxy(proxy_entry.get(),port_entry.get(),username_entry.get(),password_entry.get(),1965)
            except Exception as e:
                pass
        while True:
            try:
                a=threading.Thread(target=thread, daemon=True)
                a.start()
                a.join()
                time.sleep(0.2)
            except:
                pass
    def read_proxy():
        import proxy
        def thread():
            try:
                result=proxy.read_proxy(1965)
                if result["address"]!=None:
                    proxy_entry.insert(0,result["address"])
                if result["port"]!=None:
                    port_entry.insert(0,result["port"])
                if result["username"]!=None and result["username"]!="":
                    username_entry.insert(0,result["username"])
                if result["password"]!=None and result["password"]!="":
                    password_entry.insert(0,result["password"])
            except Exception as e:
                print("Error reading proxy: ",str(e))
        a=threading.Thread(target=thread, daemon=True)
        a.start()
        a.join()

    def load_theme():
        if block_features.block_theme():
            try:
                theme=sav_path.read_path(config_path,"theme.txt","readline")
                if theme=="light":
                    sv_ttk.set_theme("light")
                    switch.set(0)
                elif theme=="dark":
                    sv_ttk.set_theme("dark")
                    switch.set(1)
                else:
                    sv_ttk.set_theme(darkdetect.theme())
                    if darkdetect.theme()=="Light":
                        switch.set(0)
                    if darkdetect.theme()=="Dark":
                        switch.set(1)
            except FileNotFoundError:
                sv_ttk.set_theme(darkdetect.theme())
                if darkdetect.theme()=="Light":
                    switch.set(0)
                if darkdetect.theme()=="Dark":
                    switch.set(1)
            except Exception as e:
                sv_ttk.set_theme(darkdetect.theme())
                if darkdetect.theme()=="Light":
                    switch.set(0)
                if darkdetect.theme()=="Dark":        
                    switch.set(1)
        else:
            try:
                sav_path.remove_file(config_path,"theme.txt")
            except:
                pass
    def switch_theme():
        if block_features.block_theme():
            if switch.get():
                sv_ttk.set_theme("dark")
                sav_path.save_path(config_path,"theme.txt","w","dark")
            else:
                sv_ttk.set_theme("light")
                sav_path.save_path(config_path,"theme.txt","w","light")
    def enable_k():
        proxy_label.grid(row=1, column=0, padx=20, pady=20)
        proxy_entry.grid(row=1, column=1, padx=20, pady=20)
        port_label.grid(row=2, column=0, padx=20, pady=20)
        port_entry.grid(row=2, column=1, padx=20, pady=20)
        checkuser.grid(row=5, column=0, columnspan=2, padx=20, pady=20)
        if user.get():
            username_label.grid(row=6, column=0, padx=20, pady=20)
            username_entry.grid(row=6, column=1, padx=20, pady=20)
            password_label.grid(row=7, column=0, padx=20, pady=20)
            password_entry.grid(row=7, column=1, padx=20, pady=20)

    def disable_k():
        proxy_label.grid_forget()
        proxy_entry.grid_forget()
        port_label.grid_forget()
        port_entry.grid_forget()
        checkuser.grid_forget()
        username_label.grid_forget()
        username_entry.grid_forget()
        password_label.grid_forget()
        password_entry.grid_forget()
    def check_proxy_status():
        import proxy
        try:
            result=proxy.proxy_check_status(1965)
            if result==True:
                enabled.set(True)
                enable_k()
            else:
                enabled.set(False)
                disable_k()
        except Exception:
            enabled.set(False)
            disable_k()
    def set_proxy_status():
        import proxy
        def thread():
            try:
                if enabled.get():
                    proxy.proxy_set_status(True,1965)
                    enable_k()
                else:
                    proxy.proxy_set_status(False,1965)
                    disable_k()
            except Exception:
                pass
        while True:
            a=threading.Thread(target=thread, daemon=True)
            a.start()
            a.join()
            time.sleep(0.2)
    window=tk.Toplevel(root)
    window.title("Settings")
    window.resizable(False,False)
    window.protocol("WM_DELETE_WINDOW", lambda: window.destroy())
    
    control = ttk.Notebook(window)
    ftheme= ttk.Frame(window, padding="20")
    proxy=ttk.Frame(window, padding="20")
    if block_features.block_theme():
        control.add(ftheme,text="Switch Theme")
        control.grid(row=0, padx=5, pady=5)
    control.add(proxy,text="Proxy")
    control.grid(row=0, padx=5, pady=5)
    if block_features.block_theme():
        theme_tab=ttk.Frame(ftheme)
        theme_tab.grid(row=0,column=0,padx=5, pady=5)
    proxy_tab=ttk.Frame(proxy)
    proxy_tab.grid(row=0,column=0,padx=5, pady=5)
    if block_features.block_theme():
        switch=tk.BooleanVar()
        sw_theme=ttk.Checkbutton(theme_tab,text="Switch Theme",variable=switch,command=switch_theme,style="Switch.TCheckbutton")
        sw_theme.grid(row=0,column=0,padx=20, pady=20)
    enabled=tk.BooleanVar()
    check=ttk.Checkbutton(proxy_tab,text="Enable Proxy",variable=enabled,style="Switch.TCheckbutton")
    check.grid(row=0,column=0,columnspan=2,padx=20, pady=20)
    # Proxy
    proxy_label=ttk.Label(proxy_tab,text="HTTP(S) Proxy:")
    #proxy_label.grid(row=1,column=0,padx=20, pady=20)
    proxy_entry=ttk.Entry(proxy_tab,width=30)
    #proxy_entry.grid(row=1,column=1,padx=20, pady=20)

    port_label=ttk.Label(proxy_tab,text="Port:")
    #port_label.grid(row=2,column=0,padx=20, pady=20)
    port_entry=ttk.Entry(proxy_tab,width=10)
    #port_entry.grid(row=2,column=1,padx=20, pady=20)
    def uspa():
        import proxy
        try:
            a=user.get()
            if a and enabled.get():
                proxy.password_set_status(True,1965)
                username_label.grid(row=6,column=0,padx=20, pady=20)
                username_entry.grid(row=6,column=1,padx=20, pady=20)
                password_label.grid(row=7,column=0,padx=20, pady=20)
                password_entry.grid(row=7,column=1,padx=20, pady=20)
            else:
                proxy.password_set_status(False,1965)
                username_label.grid_forget()
                username_entry.grid_forget()
                password_label.grid_forget()
                password_entry.grid_forget()
        except:
            pass
    user=tk.BooleanVar()
    checkuser=ttk.Checkbutton(proxy_tab,text="Proxy needs username and password",variable=user,style="Switch.TCheckbutton",command=uspa)
    #checkuser.grid(row=5,column=0,columnspan=2,padx=20, pady=20)

    username_label=ttk.Label(proxy_tab,text="Username:")
    username_entry=ttk.Entry(proxy_tab,width=30)
    password_label=ttk.Label(proxy_tab,text="Password:")
    password_entry=ttk.Entry(proxy_tab,width=30,show="*")
    threading.Thread(target=save_proxy, daemon=True).start()
    threading.Thread(target=read_proxy, daemon=True).start()
    threading.Thread(target=set_proxy_status, daemon=True).start()
    check_proxy_status()
    load_theme()




def on_closing():
    global is_downloading
    if is_downloading:
        cancel_download()
    save_theme()
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
    settings_menu.add_command(label="Settings",command=settings)
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
    pip_upgrade_button = ttk.Button(settings_tab, text="Upgrade pip",command=upgrade_pip)
    pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=20, padx=20)

    upgrade_pip_button = pip_upgrade_button  # Alias for disabling/enabling later
    package_label = ttk.Label(settings_tab, text="Enter Package Name:")
    package_label.grid(row=1, column=0, pady=20, padx=20)

    package_entry = ttk.Entry(settings_tab, width=60)
    package_entry.grid(row=1, column=1, pady=20, padx=20)

    #PIP(INSTALL)
    install_button = ttk.Button(settings_tab, text="Install Package", command=install_package)
    install_button.grid(row=2, column=0, columnspan=3, pady=20, padx=20)

    #PIP(UNINSTALL)
    uninstall_button = ttk.Button(settings_tab, text="Uninstall Package", command=uninstall_package)
    uninstall_button.grid(row=3, column=0, columnspan=3, pady=20, padx=20)

    #progressbar-options:length(number),mode(determinate(从左到右)，indeterminate(来回滚动)),...length=500,mode="indeterminate"
    package_label = ttk.Label(settings_tab, text="", padding="10")
    package_label.grid(row=7, column=0, columnspan=3, pady=20, padx=20)
    
    

    # Set sv_ttk theme
    threading.Thread(target=python_file_reload, daemon=True).start()
    check_python_installation()
    threading.Thread(target=read_python_list, daemon=True).start()
    root.resizable(False,False)
    load_theme()
    root.mainloop()
    #root.after(3000,)
if block_features.block_start()==False:
    from get_system_build import system_build
    messagebox.showerror("Error",f"You can not open Pyquick:\nYour system is not supported. \n(Your version: {system_build.get_system_name()} {system_build.get_system_release_build_version()})\n Please upgrade to macOS 10.13(Darwin 17) or later.")
    exit(1)