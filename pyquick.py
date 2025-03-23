import tkinter as tk
from tkinter import ttk, filedialog,messagebox
import subprocess
import os
import threading
import requests
import getpass
import shutil
import re
import time
import sv_ttk
import shlex
import logging
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
cancel_event = threading.Event()
user_name = getpass.getuser()
if os.path.exists(f"/Users/{user_name}/pt_saved/update"):
    shutil.rmtree(f"/Users/{user_name}/pt_saved/update")
    os.system("kill Update")
VERSIONS = [
    "3.13.0","3.13.1",
    "3.12.0","3.12.1","3.12.2","3.12.3","3.12.4","3.12.5","3.12.6","3.12.7","3.12.8",
    "3.11.0","3.11.1","3.11.2","3.11.3","3.11.4","3.11.5","3.11.6","3.11.7","3.11.8","3.11.9",
    "3.10.0","3.10.1","3.10.2","3.10.3","3.10.4","3.10.5","3.10.6","3.10.7","3.10.8","3.10.9","3.10.10","3.10.11",
    "3.9.0","3.9.1","3.9.2","3.9.3","3.9.4","3.9.5","3.9.6","3.9.7","3.9.8","3.9.9",
    "3.8.0","3.8.1","3.8.2","3.8.3","3.8.4","3.8.5","3.8.6","3.8.7","3.8.8","3.8.9","3.8.10",
    "3.7.0","3.7.1","3.7.2","3.7.3","3.7.4","3.7.5","3.7.6","3.7.7","3.7.8","3.7.9",
    "3.6.0","3.6.1","3.6.2","3.6.3","3.6.4","3.6.5","3.6.6","3.6.7","3.6.8",
    "3.5.0","3.5.1","3.5.2","3.5.3","3.5.4",
]
MIRROR_PYTHODOWLOADER = [
    #https://registry.npmmirror.com/-/binary/python/3.10.0
    #https://registry.npmmirror.com/-/binary/python/3.10.0/python-3.10.0-amd64.exe
    "python.org",
    "registry.npmmirror.com(China)"
]
PYTHONTOOL_DOWNLAOD = [
    "github.io",
    "github.com",
    "ghp.ci"
]


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

def sav_ver():
    """
    保存用户选择的Python版本信息到文件。
    """
    try:
        # 获取用户主目录
        user_home = os.path.expanduser("~")

        # 获取用户选择的版本
        selected_version = version_combobox.get()

        # 构建保存文件的完整路径
        save_file_path = os.path.join(user_home, "pt_saved", "version.txt")

        # 确保保存目录存在
        os.makedirs(os.path.dirname(save_file_path), exist_ok=True)

        # 写入版本信息到文件
        with open(save_file_path, "w") as file:
            file.write(selected_version)
    except OSError as e:
        # 捕获并打印文件操作异常
        logging.error(f"File operation error: {e}", exc_info=True)
        messagebox.showerror("Error", f"File operation error: {e}")
    except Exception as e:
        # 捕获并打印其他异常
        logging.error(f"Unknown error   : {e}", exc_info=True)
        messagebox.showerror("Error"    , f"Unknown error: {e}")


def refresh_versions(x):
    while True:
        sav_ver()
        time.sleep(x)

# 启动版本刷新线程


# 主线程可以继续执行其他任务
print("Version refreshing started in the background.")
def clear_a():
    status_label.config(text="")
def clear_b():
    sav_label.config(text="")
def select_destination():
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)


def proxies():
    """
    获取代理服务器的地址和端口，并返回一个包含代理信息的字典。

    从用户界面的输入框中读取代理服务器的地址和端口。如果地址或端口为空，
    或者端口不是一个有效的数字，则返回False。否则，将地址和端口格式化为
    一个代理字符串，并创建一个包含HTTP和HTTPS代理的字典。

    Returns:
        False: 如果地址或端口为空，或端口不是一个有效的数字。
        dict: 包含HTTP和HTTPS代理的字典。
    """
    # 获取用户输入的代理服务器地址和端口
    address = address_entry.get()
    port = port_entry.get()

    # 检查地址是否为空
    if not address:
        return False

    # 检查端口是否为空
    if not port:
        return False

    # 验证地址格式
    if not re.match(r'^[a-zA-Z0-9.-]+$', address):
        return False

    # 尝试将端口转换为整数，并构建代理字符串
    try:
        port = int(port)
        if port <= 0 or port > 65535:
            return False
        proxy = f"http://{address}:{port}"

        # 创建并返回包含代理信息的字典
        proxies = {
            "http": proxy,
            "https": proxy
        }
        return proxies
    except ValueError:
        return False
def get_url(des):
    if des==1:
        #selected version
        selected_version=version_combobox.get()

        selected=selected_version.split(".")

        selea=int(selected[1])
        if selea>=10:
            return f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-macos11.pkg"
        elif selea<=6:
            return f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-macosx10.6.pkg"
        else:
            return f"https://www.python.org/ftp/python/{selected_version}/python-{selected_version}-macosx10.9.pkg"
    elif des==2:
        return "https://githubtohaoyangli.github.io/info/info.json"
    elif des==3:
        return "https://githubtohaoyangli.github.io/download/python_tool/Mac/Latest/python_tool.dmg"


def download_chunk(url, start, end, destination, chunk_size=1024 * 100):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
        'Range': f'bytes={start}-{end}'
    }
    proxie = proxies()
    response = requests.get(url, headers=headers, stream=True, proxies=proxie)
    with open(destination, "r+b") as file:
        file.seek(start)
        for data in response.iter_content(chunk_size=chunk_size):
            file.write(data)
            yield len(data)

def download_file(destination_path, num_threads=8):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }
    url = get_url(1)
    file_name = url.split("/")[-1]
    destination = os.path.join(destination_path, file_name)
    if os.path.exists(destination):
        os.remove(destination)
    download_button.config(state="disabled")
    for attempt in range(3):
        try:
            response = requests.head(url, headers=headers, proxies=proxies())
            response.raise_for_status()
            file_size = int(response.headers.get('content-length', 0))
            chunk_size = file_size // num_threads
            with open(destination, "wb") as file:
                file.truncate(file_size)

            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = []
                for i in range(num_threads):
                    start = i * chunk_size
                    end = start + chunk_size - 1 if i < num_threads - 1 else file_size - 1
                    futures.append(executor.submit(download_chunk, url, start, end, destination, chunk_size))

                downloaded = 0
                for future in as_completed(futures):
                    for chunk_size in future.result():
                        downloaded += chunk_size
                        percentage = (downloaded / file_size) * 100
                        downloaded_mb = downloaded / (1024 * 1024)
                        status_label.config(
                            text=f"Downloading: {percentage:.3f}% | {downloaded_mb:.3f} MB | {file_size / (1024 * 1024):.3f} MB ｜ ")
                        status_label.update()
                        download_pb["value"] = percentage
                        download_pb.update()

            status_label.config(text="Download Complete!")
            root.after(3000, clear_a)
            cancel_download_button.config(state="disabled")
            download_button.config(state="normal")
            break
        except Exception as e:
            status_label.config(text=f"Download Failed: {str(e)}. Retrying...")
            time.sleep(2)
    else:
        status_label.config(text="Download Failed after 3 attempts.")
        root.after(3000, clear_a)
        cancel_download_button.config(state="disabled")
        download_button.config(state="normal")

def cancel_download():
    cancel_event.set()
    status_label.config(text="Cancelling download...")
    download_pb['value'] = 0  # 重置进度条

    destination_path = destination_entry.get()
    url = get_url(1)
    file_name = url.split("/")[-1]
    destination = os.path.join(destination_path, file_name)

    if os.path.exists(destination):
        os.remove(destination)
        status_label.config(text="Download cancelled and incomplete file removed.")
        download_button.config(state="normal")
    else:
        status_label.config(text="Download cancelled.")
        download_button.config(state="normal")
    root.after(3000, clear_a)

def download_selected_version():
    destination_path = destination_entry.get()
    num_threads = int(threads_entry.get())

    if not os.path.exists(destination_path):
        status_label.config(text="Invalid path!")
        root.after(2000, clear_a)
        return

    if num_threads < 1 or num_threads > 128:
        status_label.config(text="Invalid number of threads. Must be between 1 and 128.")
        root.after(2000, clear_a)
        return

    cancel_event.clear()
    cancel_download_button.config(state="enabled")
    down_thread = threading.Thread(target=download_file, args=(destination_path, num_threads), daemon=True)
    down_thread.start()
status_label = None
upgrade_pip_button = None
root = None
pip_upgrade_button = None



# 配置日志记录
logging.basicConfig(level=logging.INFO)

def get_current_pip_version():
    """
    获取当前安装的 pip 版本。
    
    Returns:
        str: 当前 pip 版本号。
    """
    try:
        pipver=[]
        for i in range(0,14,1):
            try:
                command = f"python3.{i} -m pip --version"
                args = shlex.split(command)
                output = subprocess.check_output(args).decode().strip()
                logging.info(f"Command output: {output}")
                match = re.search(r'pip (\d+\.\d+\.\d+)', output)
                if match:
                    pip_version = match.group(1)
                    pipver.append(str(pip_version)+f":Python3.{i}")
                    continue
                else:
                    raise ValueError("Unexpected output format from pip --version.")
            except Exception:
                pass
        return list(pipver)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to get current pip version due to a command error.", exc_info=True)
        raise RuntimeError("Failed to get current pip version due to a command error.") from e
    except OSError as e:
        logging.error("Failed to get current pip version due to an OS error.", exc_info=True)
        raise RuntimeError("Failed to get current pip version due to an OS error.") from e
    except ValueError as e:
        logging.error("Failed to parse the pip version.", exc_info=True)
        raise RuntimeError("Failed to parse the pip version.") from e



# 创建一个线程池，最大工作线程数为 5
executor = ThreadPoolExecutor(max_workers=5)

def update_pip_button_text():
    """
    更新 pip 升级按钮的文本。
    """
    def update_pip_button():
        """
        更新按钮文本的具体逻辑。
        """
        try:
            # 获取当前 pip 版本
            current_version = get_current_pip_version()
            your_version = ""

            for i in range(len(current_version)):
                pver = ""
                try:
                    pver = current_version[i].split(":")[1]
                    if(i==len(current_version)-1):
                        your_version += current_version[i].split(":")[0]+"("+str(pver)+")"
                    else:
                        your_version += current_version[i].split(":")[0]+"("+str(pver)+")"+";"
                except:
                    pass

            # 更新按钮文本
            pip_upgrade_button.config(text=f"Pip Version: {your_version}")
        except Exception as e:
            # 记录错误日志
            logging.error(f"Error updating pip button text: {str(e)}")
            # 设置按钮文本为错误提示
            pip_upgrade_button.config(text="Error: Failed to update pip version")
        # 每 5 秒钟再次调用此函数
        root.after(100, update_pip_button_text)
    # 提交任务到线程池
    def th():
        executor.submit(update_pip_button)
    threading.Thread(target=th,daemon=True).start()
    
@functools.lru_cache(maxsize=1)
def get_latest_pip_version():
    """
    获取最新可用的 pip 版本。
    
    Returns:
        str: 最新的 pip 版本号。
    """
    try:
        # 发起 HTTP GET 请求获取 pip 的最新版本信息
        response = requests.get("https://pypi.org/pypi/pip/json")
        response.raise_for_status()
        
        # 检查响应头中的 Content-Type 是否为 application/json
        if 'application/json' not in response.headers.get('Content-Type', ''):
            raise ValueError("Unexpected content type. Expected application/json.")
        
        # 解析 JSON 响应并提取最新版本号
        latest_version = response.json()["info"]["version"]
        return latest_version
    except requests.RequestException as e:
        # 处理网络请求异常
        raise RuntimeError("Failed to get latest pip version due to network error.") from e
    except ValueError as e:
        # 处理解析 JSON 数据时的异常
        raise RuntimeError("Failed to parse response data.") from e
SUCCESS_MSG = "pip has been updated to {}"
FAILURE_MSG = "Failed to update pip: we don't know why"
def update_pip(latest_version,pver):
    """
    更新 pip 到最新版本。
    
    Args:
        latest_version (str): 最新的 pip 版本号。
    """
    # 检查 latest_version 是否符合版本号格式
    if not re.match(r'^\d+\.\d+\.\d+$', latest_version) and not re.match(r'^\d+\.\d+$', latest_version):
        raise ValueError("Invalid version format")

    def try_update(command):
        try:
            up_pip = subprocess.run(command, capture_output=True, text=True, check=True)
            if "Successfully installed" in up_pip.stdout:
                status_label.config(text=SUCCESS_MSG.format(latest_version))
                update_pip_button_text()
            else:
                status_label.config(text=FAILURE_MSG)
                update_pip_button_text()
            root.after(3000, clear_a)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update pip with '{command[0]}': {str(e)}")
            raise

    try:
        try_update(["python3","-m","pip", "install", "--upgrade", "pip", "--break-system-packages"])
    except subprocess.CalledProcessError:
        try_update(["python3","-m","pip3", "install", "--upgrade", "pip", "--break-system-packages"])
        
def get_versions():
    """
    获取当前和最新的 pip 版本。在前面有函数
    """
    try:
        current_version = get_current_pip_version()
        latest_version = get_latest_pip_version()
        return current_version, latest_version
    except (ValueError, TypeError) as e:
        logging.error(f"Data Error: {str(e)}")
        raise
    except ConnectionError as e:
        logging.error(f"Connection Error: {str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unknown Error: {str(e)}")
        raise

def update_status(text):
    """
    更新状态标签。
    """
    root.after(0, lambda: status_label.config(text=text))

def update_pip_if_needed(current_version, latest_version,pver):
    """
    如果需要，更新 pip 版本。
    """
    if current_version != latest_version:
        update_status(f"{pver}\nCurrent pip version: {current_version}\nLatest pip version: {latest_version}\nUpdating pip...")
        update_pip(latest_version,pver)
    else:
        update_status(f"pip is up to date: {current_version}({pver})")
        root.after(3000, clear_a)
    time.sleep(3)

def check_pip_version():
    """
    检查当前 pip 版本是否为最新版本，如果不是则进行更新。
    """
    upgrade_pip_button.config(state="disabled")
    try:
        current_version, latest_version = get_versions()
        current_version = list(current_version)
        for i in range(len(current_version)):
            your_version = current_version[i].split(":")[0]
            pver=current_version[i].split(":")[1]
            update_pip_if_needed(your_version, latest_version,pver)


    except Exception as e:
        update_status(f"Error: {str(e)}")
    finally:
        root.after(0, lambda: upgrade_pip_button.config(state="enabled"))

def upgrade_pip():
    """
    启动一个线程来检查并更新 pip。
    """
    try:
        subprocess.check_output(["python3", "--version"])
        upgrade_thread = threading.Thread(target=check_pip_version, daemon=True)
        upgrade_thread.start()
    except FileNotFoundError:
        status_label.config(text="Python is not installed.")
        root.after(3000, clear_a)
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")
        root.after(3000, clear_a)


def install_package():
    def clear_status_label():
        root.after(3000, clear_a)
    install_button.config(state="disabled")
    try:
        # pip freeze > python_modules.txt
        subprocess.check_output(["python3", "--version"])
        package_name = package_entry.get()
        
        if not re.match(r'^[a-zA-Z0-9\-_]+$', package_name):
            status_label.config(text="Invalid package name.")
            clear_status_label()
            return

        def install_package_thread():
            try:
                installed_packages = subprocess.check_output(["python3", "-m", "pip", "list", "--format=columns"], text=True)
                if package_name.lower() in installed_packages.lower():
                    status_label.config(text=f"Package '{package_name}' is already installed.")
                else:
                    result = subprocess.run(["python3", "-m", "pip", "install", package_name], capture_output=True, text=True)
                    if "Successfully installed" in result.stdout:
                        status_label.config(text=f"Package '{package_name}' has been installed successfully!")
                    else:
                        status_label.config(text=f"Error installing package '{package_name}': {result.stderr}")
            except subprocess.CalledProcessError as e:
                status_label.config(text=f"Error running pip command: {e.output}")
            except Exception as e:
                status_label.config(text=f"Error installing package '{package_name}': {str(e)}")
            finally:
                clear_status_label()
        install_thread = threading.Thread(target=install_package_thread, daemon=True)
        install_thread.start()
    except FileNotFoundError:
        status_label.config(text="Python is not installed.")
        clear_status_label()
    except subprocess.CalledProcessError as e:
        status_label.config(text=f"Error checking Python version: {e.output}")
        clear_status_label()
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")
        clear_status_label()
    install_button.config(state="enabled")
def uninstall_package():
    uninstall_button.config(state="disabled")
    try:
        subprocess.check_output(["python3", "--version"])
        package_name = package_entry.get()
        def uninstall_package_thread():
            try:
                installed_packages = subprocess.check_output(["python3", "-m", "pip", "list", "--format=columns"], text=True)
                if package_name.lower() in installed_packages.lower():
                    result = subprocess.run(["python3", "-m", "pip", "uninstall", "-y", package_name], capture_output=True, text=True)
                    if "Successfully uninstalled" in result.stdout:
                        status_label.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                        root.after(3000,clear_a)
                    else:
                        status_label.config(text=f"Cannot uninstall package '{package_name}': {result.stderr}")
                        root.after(3000,clear_a)
                else:
                    status_label.config(text=f"Package '{package_name}' is not installed.")
                    root.after(3000,clear_a)
            except Exception as e:
                status_label.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
                root.after(3000,clear_a)
        uninstall_thread = threading.Thread(target=uninstall_package_thread, daemon=True)
        uninstall_thread.start()
    except FileNotFoundError:
        status_label.config(text="Python is not installed.")
        root.after(3000,clear_a)
    except Exception as e:
        status_label.config(text=f"Error: {str(e)}")
        root.after(3000,clear_a)
    uninstall_button.config(state="enabled")
def load():
    user_name = getpass.getuser() 
    if os.path.exists(f"/Users/{user_name}/pt_saved/proxy.txt"):
        with open(f"/Users/{user_name}/pt_saved/proxy.txt","r") as re:
            ree=re.readlines()
            reee=len(ree)
            for i in range(reee):
                if "address:" in ree[i]:
                    add=ree[i].split(":")
                    addlen=len(add)
                    address=add[addlen-1]
                    address=address.strip()
                    address_entry.insert(0,address)
                if "port" in ree[i]:
                    poo=ree[i].split(":")
                    poolen=len(poo)
                    port=poo[poolen-1]
                    port=port.strip()
                    port_entry.insert(0,port)
    else:
        address_entry.insert(0,"")
        port_entry.insert(0,"")
def save():
    address=address_entry.get()
    port=port_entry.get()
    try:
        user_name = getpass.getuser() 
        if os.path.exists(f"/Users/{user_name}/pt_saved/proxy.txt"):
            os.remove(f"/Users/{user_name}/pt_saved/proxy.txt")
        if os.path.exists(f"/Users/{user_name}/pt_saved/")==False:
            os.mkdir(f"/Users/{user_name}/pt_saved/")
        with open(f"/Users/{user_name}/pt_saved/proxy.txt","w")as wr:
            wr.write(f"address:{address}\n")
            wr.write(f"port:{port}\n")
            sav_label.config(text="Proxy settings has been saved successfully!")
            root.after(1000,clear_b)
    except Exception as e:
        sav_label.config(text=f"Error: Cannot save proxy settings {str(e)}")
        root.after(1000,clear_b)
def load_com():
    #f"/Users/{user_name}/pt_saved/"
    try:
        user_name = getpass.getuser()
        version_len=len(VERSIONS)
        with open(f"/Users/{user_name}/pt_saved/version.txt","r") as r:
            re=r.read()
        for i in range(version_len):
            if re in VERSIONS[i]:
                return int(i)
    except Exception:
        return 0
user_name = getpass.getuser()

def switch_theme():
    user_name = getpass.getuser()

    if switch.get():
        sv_ttk.set_theme("dark")
        if os.path.exists(f"/Users/{user_name}/pt_saved/") == False:
            os.mkdir(f"/Users/{user_name}/pt_saved/")
        if os.path.exists(f"/Users/{user_name}/pt_saved/theme/") == False:
            os.mkdir(f"/Users/{user_name}/pt_saved/theme")
        with open(f"/Users/{user_name}/pt_saved/theme/theme.txt", "w") as a:
            a.write("dark")
    else:
        sv_ttk.set_theme("light")
        if os.path.exists(f"/Users/{user_name}/pt_saved/") == False:
            os.mkdir(f"/Users/{user_name}/pt_saved/")
        if os.path.exists(f"/Users/{user_name}/pt_saved/theme/") == False:
            os.mkdir(f"/Users/{user_name}/pt_saved/theme")
        with open(f"/Users/{user_name}/pt_saved/theme/theme.txt", "w") as a:
            a.write("light")


def load_theme():
    try:
        user_name = getpass.getuser()
        with open(f"/Users/{user_name}/pt_saved/theme/theme.txt", "r") as r:
            theme = r.read()
        if theme == "dark":
            switch.set(True)
            sv_ttk.set_theme("dark")
        elif theme == "light":
            switch.set(False)
            sv_ttk.set_theme("light")
    except Exception:
        sv_ttk.set_theme("light")
def show_about():
    time_lim=(datetime.datetime(2025,3,29)-datetime.datetime.now()).days
    if (datetime.datetime.now()>=datetime.datetime(2025,2,1)):
        messagebox.showwarning("About", f"Version: dev\nBuild: 1927\n{time_lim} days left.")
    else:
        messagebox.showinfo("About", f"Version: dev\nBuild: 1927\n{time_lim} days left.")
#GUI
if __name__ == "__main__":
    if(datetime.datetime.now()>=datetime.datetime(2025,7,13)):
        messagebox.showerror("Error","This software will not be available after 2025,7,13")
        exit(1)
    elif(datetime.datetime.now()>=datetime.datetime(2025,2,1)):
        messagebox.showwarning("up","Will cannot open on 2025,3,13")
    
    root = tk.Tk()
    root.title("Python Tool")
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    help_menu = tk.Menu(menu_bar, tearoff=0)

    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=show_about)
    help_menu.add_separator()
    #TAB CONTROL
    tab_control = ttk.Notebook(root)
    #MODE TAB
    fmode = ttk.Frame(root, padding="20")
    tab_control.add(fmode,text="Mode")
    tab_control.pack(expand=1, fill='both', padx=10, pady=10)
    framea_tab = ttk.Frame(fmode)
    framea_tab.pack(padx=20, pady=20)
    #PYTHON VERSION
    version_label = ttk.Label(framea_tab, text="Select Python Version:")
    version_label.grid(row=0, column=0, pady=10)
    selected_version = tk.StringVar()
    version_combobox = ttk.Combobox(framea_tab, textvariable=selected_version, values=VERSIONS, state="read")
    version_combobox.grid(row=0, column=1, pady=10)
    ins=load_com()
    version_combobox.current(ins)
    #SAVE PATH
    destination_label = ttk.Label(framea_tab, text="Select Destination:")
    destination_label.grid(row=1, column=0, pady=10)
    destination_entry = ttk.Entry(framea_tab, width=40)
    destination_entry.grid(row=1, column=1, pady=10)
    select_button = ttk.Button(framea_tab, text="Select", command=select_destination)
    select_button.grid(row=1, column=2, pady=10,padx=10)
    #DOWNLOAD
    download_button = ttk.Button(framea_tab, text="Download Selected Version", command=download_selected_version)
    download_button.grid(row=2, column=0, columnspan=5, pady=10)
    cancel_download_button = ttk.Button(framea_tab, text="Cancel Download", command=cancel_download, state="disabled")
    cancel_download_button.grid(row=3, column=0, columnspan=3, pady=10)
    threads_label = ttk.Label(framea_tab, text="Number of Threads:")
    threads_label.grid(row=4, column=0, pady=10)
    threads = tk.IntVar()
    threads_entry = ttk.Combobox(framea_tab, width=10,textvariable=threads,values=[str(i) for i in range(1, 129)],state="readonly")
    threads_entry.grid(row=4, column=1, pady=10)
    threads_entry.current(7)
    #PIP(UPDRADE)
    pip_upgrade_button = ttk.Button(framea_tab, text="Pip Version: Checking...", command=upgrade_pip)
    pip_upgrade_button.grid(row=5, column=0, columnspan=3, pady=20)
    upgrade_pip_button = pip_upgrade_button  # Alias for disabling/enabling later
    package_label = ttk.Label(framea_tab, text="Enter Package Name:")
    package_label.grid(row=6, column=0, pady=10)
    package_entry = ttk.Entry(framea_tab, width=40)
    package_entry.grid(row=6, column=1, pady=10)
    #PIP(INSTALL)
    install_button = ttk.Button(framea_tab, text="Install Package", command=install_package)
    install_button.grid(row=7, column=0, columnspan=3, pady=10)
    #PIP(UNINSTALL)
    uninstall_button = ttk.Button(framea_tab, text="Uninstall Package", command=uninstall_package)
    uninstall_button.grid(row=8, column=0, columnspan=3, pady=10)
    #progressbar-options:length(number),mode(determinate(从左到右)，indeterminate(来回滚动)),...length=500,mode="indeterminate"
    download_pb=ttk.Progressbar(framea_tab,length=500,mode="determinate")
    download_pb.grid(row=9,column=0,pady=20,columnspan=3)
    #TEXT(TAB1)
    status_label = ttk.Label(framea_tab, text="", padding="10")
    status_label.grid(row=10, column=0, columnspan=3)

    #SETTINGS TAB
    fsetting = ttk.Frame(root, padding="20")
    tab_control.add(fsetting,text="Settings")
    tab_control.pack(expand=1, fill='both', padx=10, pady=10)
    frameb_tab = ttk.Frame(fsetting)
    frameb_tab.pack(padx=20, pady=20)

    address=ttk.Label(frameb_tab,text="Address:")
    address.grid(row=1,column=0,padx=10,pady=10)

    address_entry=ttk.Entry(frameb_tab,width=15)
    address_entry.grid(row=1,column=1,columnspan=2,pady=10)

    port=ttk.Label(frameb_tab,text="Port:")
    port.grid(row=2,column=0,padx=0,pady=10)

    port_entry=ttk.Entry(frameb_tab,width=5)
    port_entry.grid(row=2,column=1,pady=10,columnspan=2)

    sav=ttk.Button(frameb_tab,text="Apply",command=save)
    sav.grid(row=3,column=0,padx=10,pady=10,columnspan=3)


    switch = tk.BooleanVar()  # 创建一个BooleanVar变量，用于检测复选框状态
    themes = ttk.Checkbutton(frameb_tab, text="dark mode", variable=switch, style="Switch.TCheckbutton",command=switch_theme)
    themes.grid(row=5,column=0,padx=10,pady=10,columnspan=3)
    def allow_refresh_base():
        if (refresh.get() == False):
            refresh_entry.config(state=tk.DISABLED)
        if (refresh.get()==True):
            refresh_entry.config(state="enabled")
    def allow_refresh():
        if(refresh.get() and refresh_entry.get().isdigit()):
            ind = float(refresh_entry.get())
            if(ind!=None or ind > 0):
                while True:
                    threading.Thread(target=refresh_versions,args=(ind,)).start()
                    time.sleep(ind)
    def allow_refresh_thread():
        while True:
            if(refresh.get() and refresh_entry.get().isdigit()):
                threading.Thread(target=allow_refresh,daemon=True).start()
                break
            else:
                time.sleep(1)
                continue
    refresh=tk.BooleanVar()
    refresh_button=ttk.Checkbutton(frameb_tab,text="refresh-python-versions(BETA)",variable=refresh,onvalue=True,offvalue=False,command=allow_refresh_base)
    refresh_button.grid(row=6,column=0,padx=10,pady=10,columnspan=3)
    reentry=tk.StringVar()
    refresh_entry=ttk.Entry(frameb_tab,width=10)
    refresh_entry.grid(row=6,column=4,pady=10,columnspan=2)
    sav_label = ttk.Label(frameb_tab, text="")
    sav_label.grid(row=7, column=0,columnspan=3)
    #update(not available)
    threading.Thread(target=allow_refresh_thread,daemon=True).start()

    load()
    load_theme()
    # Set sv_ttk theme
    update_pip_button_text()
    check_python_installation()


    root.resizable(False,False)
    root.mainloop()
    #root.after(3000,)