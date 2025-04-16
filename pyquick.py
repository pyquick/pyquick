import datetime
import logging
import os
import re
import sys
import multiprocessing
import subprocess
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from tkinter import ttk, filedialog, messagebox
import ssl
import requests
import sv_ttk
from bs4 import BeautifulSoup
import urllib3
import platform
import ctypes
import math
import psutil  # 用于获取系统信息
from collections import deque  # 用于计算下载速度
import random  # 用于随机抖动
import glob    # 用于文件匹配
from ab.expire import show
from ab import about
from log import get_logger, LogPerformance, log_exception
from pip import (
    show_pip_version, retry_pip, upgrade_pip, install_package, 
    uninstall_package, upgrade_package, monitor_package_version, check_package_upgradeable,
    get_pip_version, get_latest_pip_version
)
import concurrent.futures
import json
from lang import set_language, get_text, texts, current_language
import gc  # 添加gc模块导入

# 获取日志记录器，GUI应用禁用控制台输出
logger = get_logger(use_console=False)

requests.packages.urllib3.disable_warnings()
sys.stdout=open(os.devnull,"w")
print(1)
logger.info("PyQuick应用启动")
#allowthread.txt 记录是否允许多线程下载
#allowupdatepip.txt 记录是否允许自动更新
#pythonpath.txt 记录python安装路径
#pythonversion.txt 记录python版本
#theme.txt 记录主题
#pipmirror.txt 记录pip镜像源
#pipversion.txt 记录pip版本
#version.txt 记录python版本
#windowopenorclose.txt 记录窗口是否打开
# 获取当前工作目录
PIP_MIRRORS = [
    "http://pypi.org/simple/",
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.mirrors.ustc.edu.cn/simple",
    "https://pypi.doubanio.com/simple/",
    "https://pypi.hustunique.com/simple/",
    "https://pypi.sdutlinux.org/simple/",
    "https://mirrors.cloud.tencent.com/pypi/simple/",
    "https://mirrors.sustech.edu.cn/pypi/web/simple/",
    "https://mirrors.ustc.edu.cn/pypi/web/simple/",
]
TRUSTED=[
    "pypi.org",
    "pypi.tuna.tsinghua.edu.cn",
    "mirrors.aliyun.com",
    "pypi.mirrors.ustc.edu.cn",
    "pypi.doubanio.com",
    "pypi.hustunique.com",
    "pypi.sdutlinux.org",
    "mirrors.cloud.tencent.com",
    "mirrors.sustech.edu.cn",
    "mirrors.ustc.edu.cn",
]
MY_PATH = os.getcwd()
version_pyquick="2020"
# 获取用户配置目录
config_path_base = os.path.join(os.environ["APPDATA"], f"pyquick")
config_path=os.path.join(config_path_base,version_pyquick)
processes=[]
pip_souc=os.path.join(os.environ["APPDATA"], f"pip","pip.ini")
def get_pip_mirror():
    pip_souc = os.path.join(os.environ["APPDATA"], f"pip", "pip.ini")
    if os.path.exists(pip_souc):
        with open(pip_souc, "r") as f:
            pip_config = f.readlines()
        for line in range(len(pip_config)):
            pip_config[line] = pip_config[line].strip("\n\r")
            if "index-url" in pip_config[line]:
                pip_mirror = pip_config[line].split("=")[1].strip()
                break
        pip_mirror=pip_mirror.strip("\n\r ")
        for i in range(len(PIP_MIRRORS)):
            if PIP_MIRRORS[i]==pip_mirror:
                pip_mirror=i
                return pip_mirror
    else:
        return -1
    return 0

def get_python_version():
    """获取当前Python版本，同时返回 pip 和 python 版本，并去重"""
    versions_dict = {}  # 使用字典防止重复版本
    
    # 获取 Python 安装位置
    versions_base = subprocess.run(["where", "python"], capture_output=True, shell=True, 
                                 creationflags=subprocess.CREATE_NO_WINDOW)
    python_locations = (versions_base.stdout).decode().split("\n")
    name = r"Python\d+"
    
    for location in python_locations:
        if not location or location == "\r":
            continue
            
        location = location.strip("\r\n")
        path_parts = location.split("\\")
        
        # 确保路径包含足够的部分
        if len(path_parts) > 2:
            # 通常 Python 安装文件夹名为 "Python310" 或 "Python39"
            folder_name = path_parts[-2]
            
            # 检查是否匹配 Python 文件夹命名模式
            if re.match(name, folder_name):
                # 提取版本号（如 310 从 Python310）
                version = folder_name.strip("Python")
                
                # 格式化版本号（如 310 -> 3.10）
                if len(version) >= 3:
                    formatted_version = f"{version[0]}.{version[1:]}"
                else:
                    formatted_version = version
                
                # 保存版本信息，使用版本号作为键避免重复
                if version not in versions_dict:
                    # 将版本信息保存为元组 (pip格式, python格式)
                    versions_dict[version] = (f"Pip{version}", f"Python{formatted_version}")
    
    # 如果没有找到版本，返回空列表和空字典
    if not versions_dict:
        logger.warning("未检测到任何 Python 版本")
        return [], {}
    
    # 提取 pip 版本列表
    pip_versions = [v[0] for v in versions_dict.values()]
    logger.info(f"检测到的 Python 版本: {', '.join(pip_versions)}")
    
    # 返回 pip 版本列表和完整的版本映射字典
    return pip_versions, versions_dict

def thread():
    """获取pip版本的线程函数"""
    try:
        # 不要在线程中直接调用root.after
        # 而是将需要更新的操作保存到变量中，然后在外部函数中使用root.after调用
        global pip_version_check_status
        pip_version_check_status = {"action": "checking"}
        
        version_pip = get_pip_version(config_path)
        with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
            b = f.readlines()
            python_name = "Python" + b[-1].strip("\n").strip("Pip")
        
        # 检查成功，需要隐藏重试按钮
        pip_version_check_status["retry_button"] = "hide"
        
        latest_version = get_latest_pip_version()
        if version_pip == latest_version:
            pip_version_check_status["action"] = "up_to_date"
            pip_version_check_status["python_name"] = python_name
            pip_version_check_status["version_pip"] = version_pip
            
            with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                fw.write("False\n")
                fw.write(version_pip)  # 保存当前pip版本
        else:
            pip_version_check_status["action"] = "update_available"
            pip_version_check_status["python_name"] = python_name
            pip_version_check_status["version_pip"] = version_pip
            pip_version_check_status["latest_version"] = latest_version
            
            with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                fw.write("True\n")
                fw.write(version_pip)  # 保存当前pip版本
    except Exception as e:
        logger.error(f"Failed to get pip version: {e}")
        pip_version_check_status = {"action": "error"}
        return "error"

def update_pip_ui():
    """在主线程中更新pip UI"""
    global pip_version_check_status
    
    if not hasattr(globals(), 'pip_version_check_status') or pip_version_check_status is None:
        return
    
    def update_ui(status):
        try:
            if status.get("action") == "checking":
                pip_upgrade_button.config(text=get_text("pip_checking"), state="disabled")
            
            elif status.get("action") == "up_to_date":
                pip_upgrade_button.config(
                    text=get_text("pip_up_to_date").format(
                        status.get("python_name", ""), 
                        status.get("version_pip", "")
                    ), 
                    state="disabled"
                )
                pip_retry_button.grid_forget()
            
            elif status.get("action") == "update_available":
                pip_upgrade_button.config(
                    text=get_text("pip_new_version_available").format(
                        status.get("python_name", ""), 
                        status.get("version_pip", ""), 
                        status.get("latest_version", "")
                    )
                )
                
                if "disabled" in install_button.state() and "disabled" in uninstall_button.state(): 
                    pip_upgrade_button.config(state="disabled")
                elif install_button.state() == () or uninstall_button.state() == ():
                    pip_upgrade_button.config(state="normal")
                
                pip_retry_button.grid_forget()
            
            elif status.get("action") == "error":
                pip_upgrade_button.config(text=get_text("failed_to_get_pip_version"), state="disabled")
                pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
            
            # 清除状态，避免重复处理
            pip_version_check_status = None
        
        except Exception as e:
            logger.error(f"更新pip UI出错: {e}")
    
    # 确保在主线程中更新UI
    root.after(0, lambda: update_ui(pip_version_check_status))

def save_path():
    """后台定期检查pip版本的函数"""
    last_check_version = None
    
    while True:
        try:
            # 检查是否需要检查pip版本
            check_needed = False
            current_version = None
            
            try:
                # 读取当前设置的pip版本
                with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
                    current_version = f.read().strip()
                
                # 读取是否需要自动检查pip版本
                auto_check_enabled = True  # 默认启用
                with open(os.path.join(config_path, "allowupdatepip.txt"), "r") as f:
                    lines = f.readlines()
                    if lines and lines[0].strip().lower() == "false":
                        auto_check_enabled = False
                
                # 如果版本发生变化或允许自动检查，则进行检查
                if current_version != last_check_version or auto_check_enabled:
                    check_needed = True
            except Exception as e:
                logger.error(f"读取pip版本检查设置失败: {e}")
                # 出错时默认需要检查
                check_needed = True
            
            # 如果需要检查，调用show_pip_version函数
            if check_needed:
                last_check_version = current_version
                # 使用主线程中的单次调用更新UI，而不是启动新线程
                root.after(0, show_pip_version)
            
            # 较长时间睡眠，减少资源消耗
            time.sleep(5.0)
        except Exception as e:
            logger.error(f"后台检查pip版本出错: {e}")
            time.sleep(3.0)  # 出错后等待更长时间再重试

def allow_thread():
    def thread_func():
        try:
            thread_file = os.path.join(config_path, "allowthread.txt")
            if not os.path.exists(thread_file):
                with open(thread_file, "w") as f:
                    f.write("True\n")
                return
                
            with open(thread_file, "r") as r:
                lines = r.readlines()
                if not lines:
                    return
                aa = lines[-1].strip("\n")
                if aa == "True":
                    # 使用root.after确保在主线程中更新GUI
                    root.after(0, lambda: thread_label.grid(row=2, column=0, pady=10, padx=10, sticky="e"))
                    root.after(0, lambda: thread_combobox.grid(row=2, column=1, pady=10, padx=10, sticky="w"))
                else:
                    # 使用root.after确保在主线程中更新GUI
                    root.after(0, lambda: thread_label.grid_forget())
                    root.after(0, lambda: thread_combobox.grid_forget())
        except Exception as e:
            logger.error(f"allow_thread 函数出错: {e}")
    
    while True:
        try:
            t = threading.Thread(target=thread_func, daemon=True)
            t.start()
            time.sleep(0.5)  # 增加间隔时间，减少线程创建频率
        except Exception as e:
            logger.error(f"创建线程出错: {e}")
            time.sleep(1.0)  # 出错后等待更长时间再重试

def on_closing():
    try:
        if is_downloading:
            messagebox.askokcancel("Exit", "Do you want to quit?")
            cancel_download()
        root.destroy()
        sys.exit(0)
        subprocess.run(["taskkill","/IM","python.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True)
        subprocess.run(["taskkill","/IM","python_tool.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True)
        subprocess.run(["taskkill","/IM","pyquick.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True)
        subprocess.run(["taskkill","/IM","pythonw.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True) 
        subprocess.run(["taskkill","/IM","pythonw.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True) 
    except:
        subprocess.run(["taskkill","/IM","python.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True)
        subprocess.run(["taskkill","/IM","python_tool.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True)
        subprocess.run(["taskkill","/IM","pyquick.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True)
        subprocess.run(["taskkill","/IM","pythonw.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True) 
        subprocess.run(["taskkill","/IM","pythonw.exe","/F"],creationflags=subprocess.CREATE_NO_WINDOW,text=True,capture_output=True) 

def cancel_download():
    """取消下载"""
    global is_downloading, is_paused, futures, executor, destination
    
    if is_downloading:
        try:
            is_downloading = False
            is_paused = False
            
            # 取消所有任务
            for future in futures:
                future.cancel()
            
            # 关闭线程池
            if executor:
                executor.shutdown(wait=False)
            
            # 删除未完成的文件
            if 'destination' in globals() and destination and os.path.exists(destination):
                try:
                    os.remove(destination)
                except Exception as e:
                    logger.error(f"删除未完成的文件失败: {e}")
                    error_msg = get_text("delete_file_error").format(e)
                    root.after(0, lambda msg=error_msg: messagebox.showerror(get_text("error"), msg))
            
            # 在主线程中安全地更新UI
            def update_ui():
                status_label.config(text=get_text("download_canceled"))
                progress_bar.grid_forget()  # 隐藏进度条
                download_button.config(state="normal")  # 恢复下载按钮
                cancel_button.grid_forget()  # 隐藏取消按钮
                pause_button.grid_forget()  # 隐藏暂停按钮
            
            # 总是使用after调度到主线程
            root.after(0, update_ui)
                
        except Exception as e:
            logger.error(f"取消下载时出错: {e}")
            # 确保在主线程中显示错误消息
            error_msg = get_text("cancel_error").format(e)
            root.after(0, lambda msg=error_msg: messagebox.showerror(get_text("error"), msg))
    
    return_normal()

def get_system_build():
    """获取系统版本"""
    system_build=int(str(platform.platform().split("-")[2]).split(".")[2])
    return system_build
build=get_system_build()
#print(build)查看系统build版本是否达标，如果不是Windows11(build>=22000)则无sv_ttk使用权，只能使用ttk 
PYTHON_MIRRORS=[
    "https://www.python.org/ftp/python",
    "https://mirrors.huaweicloud.com/python"
]
ssl.create_default_context=ssl._create_unverified_context()

# 禁用 SSL 警告
urllib3.disable_warnings()

if not os.path.exists(config_path):
    os.makedirs(config_path)
if not os.path.exists(os.path.join(config_path,"pythonmirror.txt")):
    with open(os.path.join(config_path,"pythonmirror.txt"),"w+") as f:
        pass
if not os.path.exists(os.path.join(config_path,"pipmirror.txt")):
    with open(os.path.join(config_path,"pipmirror.txt"),"w+") as f:
        pass

# 如果保存目录不存在，则创建它

if not os.path.exists(os.path.join(config_path_base, "path.txt")):
    with open(os.path.join(config_path_base, "path.txt"), "a"):
        pass
if not os.path.exists(os.path.join(config_path, "allowthread.txt")):
    with open(os.path.join(config_path, "allowthread.txt"), "a")as fw:
        fw.write("False")
        fw.write("\n") 
if not os.path.exists(os.path.join(config_path, "pipmirror.txt")):
    pipmirror=subprocess.run(["pip","config","get","global.index-url"],capture_output=True,shell=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with open(os.path.join(config_path, "pipmirror.txt"), "a")as fw:
        fw.write(pipmirror.stdout.strip("\n"))
if not os.path.exists(os.path.join(config_path, "allowupdatepip.txt")):
    with open(os.path.join(config_path, "allowupdatepip.txt"), "w")as fw:
        pass
if not os.path.exists(os.path.join(config_path, "pythonversion.txt")):
    with open(os.path.join(config_path, "pythonversion.txt"), "w") as fw:
        # 使用当前执行的Python版本
        version = sys.version.split()[0]  # 获取如 "3.10.0" 的版本号
        # 提取主要版本号（例如 3.10.0 -> 310）
        parts = version.split('.')
        major_minor = parts[0] + (parts[1] if len(parts) > 1 else "0")
        fw.write(f"Pip{major_minor}")
if not os.path.exists(os.path.join(config_path, "theme.txt")):
    with open(os.path.join(config_path, "theme.txt"), "w")as fw:
        fw.write("light")

# 如果语言配置文件不存在，则创建
if not os.path.exists(os.path.join(config_path, "language.txt")):
    with open(os.path.join(config_path, "language.txt"), "w") as fw:
        fw.write("zh_CN")  # 默认简体中文

# 如果日志大小配置文件不存在，则创建
if not os.path.exists(os.path.join(config_path, "log_size.txt")):
    with open(os.path.join(config_path, "log_size.txt"), "w") as fw:
        fw.write("10")  # 默认10MB

def abou():
    subprocess.Popen(about.show(),shell=True,creationflags=subprocess.CREATE_NO_WINDOW)

def show_about():
    multiprocessing.Process(target=abou, daemon=True).start()

# 全局变量
file_size = 0
executor = None  # 确保初始值为None
futures = []
lock = threading.Lock()
downloaded_bytes = [0]
is_downloading = False
is_paused = False  # 新增暂停状态变量
download_speeds = deque(maxlen=10)  # 存储最近10次的下载速度
last_downloaded = 0
last_time = 0



def clear():
    """清除状态标签和包标签的文本"""
    status_label.config(text="")
    package_status_label.config(text="")
    package_label.config(text="Enter Package Name:")
    progress_bar['value']=0


def select_destination():
    """选择目标路径"""
    destination_path = filedialog.askdirectory()
    if destination_path:
        destination_entry.delete(0, tk.END)
        destination_entry.insert(0, destination_path)


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
def read_python_version():
    """读取保存的Python版本列表"""
    try:
        with open(os.path.join(config_path, "version.txt"), "r") as f:
            version_text = f.read().strip()
            if not version_text:
                logger.warning("版本文件为空")
                return
            
            # 解析版本列表字符串为列表
            version_text = version_text.strip("[]")
            if not version_text:
                return
                
            version1 = version_text.split(",")
            if not version1:
                return
                
            # 处理版本字符串
            version2 = []
            for i in version1:
                cleaned = i.strip("'").strip(" ").strip("'")
                if cleaned:
                    version2.append(cleaned)
            print(version2)
            if version2:
                logger.info(f"从文件加载了 {len(version2)} 个Python版本")
                version_combobox.configure(values=version2)
            else:
                logger.warning("解析版本列表后为空")
    except FileNotFoundError:
        logger.warning("Python版本文件不存在，将尝试在线加载")
        # 在初始化阶段尝试在线加载
        threading.Thread(target=python_version_reload, daemon=True).start()
    except Exception as e:
        logger.error(f"读取Python版本文件失败: {e}")

def python_dowload_url_reload(url):
    """
    获取指定URL中的Python下载文件列表
    
    参数:
        url (str): Python版本下载目录URL
        
    返回:
        list: 可下载文件名列表，失败返回空列表
    """
    try:
        logger.info(f"从URL加载文件列表: {url}")
        r11 = r'\S+/'
        r1 = r'INDEX'
        r10 = r'README'
        r2 = r'README.html'
        
        # 获取镜像源设置
        with open(os.path.join(config_path, "pythonmirror.txt"), "r") as f:
            mirrors = f.readlines()
            if mirrors == [] or len(mirrors) < 1:
                mirror = "https://www.python.org/ftp/python"
            elif len(mirrors) > 1:
                mirror = mirrors[len(mirrors) - 1].strip("\n")
            else:
                mirror = mirrors[0].strip("\n")
        
        # 获取选定的版本
        select_version = version_combobox.get()
        
        # 验证URL是否与选择的版本匹配
        expected_url = f"{mirror}/{select_version}/"
        if url != expected_url and select_version and mirror != "默认源":
            logger.warning(f"URL不匹配: 期望 {expected_url}, 实际 {url}")
            url = expected_url
        
        # 发送请求获取页面内容
        logger.info(f"正在请求URL: {url}")
        with requests.get(url, verify=False, timeout=30) as r:
            if r.status_code != 200:
                logger.error(f"HTTP请求失败，状态码: {r.status_code}")
                return []
            
            logger.info("成功获取页面内容，开始解析")
            bs = BeautifulSoup(r.content, "lxml")
            
        # 提取文件链接
            results = []
            for i in bs.find_all("a"):
                # 排除目录、索引文件和README文件
                if (re.match(r11, i.text) is None and 
                    re.match(r1, i.text) is None and 
                    re.match(r10, i.text) is None and 
                    re.match(r2, i.text) is None):
                        results.append(i.text)
        
        # 根据文件类型过滤结果
            if results:
                # 过滤Windows安装程序
                windows_files = results
                if windows_files:
                    logger.info(f"找到 {len(windows_files)} 个Windows安装文件")
                    return windows_files
                
                # 如果没有Windows文件，返回所有文件
                logger.info(f"未找到Windows安装文件，返回所有 {len(results)} 个文件")
                return results
            else:
                logger.warning("未找到任何文件")
                return []
    except requests.RequestException as e:
        logger.error(f"请求异常: {e}")
        return []
    except Exception as e:
        logger.error(f"Python文件名加载失败: {e}", exc_info=True)
        return []

# 获取可下载版本列表
def python_version_reload():
    """获取可下载的Python版本列表"""
    def python_version_reload_thread():
        try:
            with LogPerformance(logger, "重新加载Python版本列表"):
                # 在主线程中更新UI状态
                def update_ui_state(state, text):
                    version_reload_button.configure(state=state, text=text)
                root.after(0, lambda: update_ui_state("disabled", get_text("reload")))
                
                # 获取镜像源
                mirror = None
                try:
                    with open(os.path.join(config_path, "pythonmirror.txt"), "r") as f:
                        mirrors = f.readlines()
                        if mirrors == [] or len(mirrors) < 1:
                            mirror = "https://www.python.org/ftp/python"
                        elif len(mirrors) > 1:
                            mirror = mirrors[len(mirrors) - 1].strip("\n")
                        else:
                            mirror = mirrors[0].strip("\n")
                except Exception as e:
                    logger.error(f"读取镜像源配置失败: {e}")
                    mirror = "https://www.python.org/ftp/python"  # 使用默认镜像
                
                if mirror == get_text("default_source") or not mirror:
                    mirror = "https://www.python.org/ftp/python"
                
                # 请求URL获取版本列表
                url = f"{mirror}/"
                logger.info(f"从 {url} 加载Python版本列表")
                
                response = requests.get(url, verify=False, timeout=30)
                if response.status_code != 200:
                    logger.error(f"HTTP请求失败，状态码: {response.status_code}")
                    root.after(0, lambda: update_ui_state("normal", get_text("reload")))
                    return
                
                bs = BeautifulSoup(response.content, "lxml")
                results = []
                
                # 解析版本目录
                for i in bs.find_all("a"):
                    if i.text[0].isnumeric():
                        # 移除末尾的斜杠
                        version = i.text[:-1] if i.text.endswith('/') else i.text
                        results.append(version)
                
                if results:
                    logger.info(f"找到 {len(results)} 个Python版本")
                    root.after(0, lambda: update_ui_state("disabled", get_text("sorting")))
                    
                    # 排序版本
                    sort_results(results)
                    
                    # 保存版本列表到文件
                    with open(os.path.join(config_path, "version.txt"), "w") as f:
                        f.write(str(results))
                else:
                    logger.warning("未找到任何Python版本")
                    warning_msg = get_text("no_python_versions")
                    root.after(0, lambda msg=warning_msg: messagebox.showwarning(
                        get_text("warning_msg"), msg
                    ))
        except Exception as e:
            logger.error(f"Python版本重新加载失败: {e}", exc_info=True)
            # 使用after方法将GUI操作调度到主线程
            error_msg = get_text("python_version_load_failed").format(str(e))
            root.after(0, lambda msg=error_msg: messagebox.showerror(
                get_text("error"), msg
            ))
        finally:
            # 恢复按钮状态，使用after方法调度到主线程
            def update_button_state():
                if is_downloading:
                    version_reload_button.configure(state="disabled", text=get_text("reload"))
                else:
                    version_reload_button.configure(state="normal", text=get_text("reload"))
            root.after(0, update_button_state)
    
    # 启动加载线程
    threading.Thread(target=python_version_reload_thread, daemon=True).start()


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


def validate_path(path):
    """
    验证路径是否存在

    参数:
    path (str): 需要验证的路径

    返回:
    bool: 如果路径存在返回True，否则返回False
    """
    return os.path.isdir(path)

def calculate_optimal_threads(file_size, connection_type="normal"):
    """
    根据文件大小和连接类型计算最优线程数
    
    参数:
        file_size (int): 文件大小（字节）
        connection_type (str): 连接类型，可选值："slow", "normal", "fast"
        
    返回:
        int: 推荐的线程数
    """
    # 获取系统CPU核心数
    cpu_count = psutil.cpu_count(logical=False) or 2
    available_memory = psutil.virtual_memory().available
    
    # 根据连接类型设置基础线程数
    if connection_type == "slow":
        base_threads = 2
    elif connection_type == "fast":
        base_threads = cpu_count * 2
    else:  # normal
        base_threads = cpu_count
    
    # 根据文件大小调整线程数
    if file_size < 1024 * 1024:  # 小于1MB
        threads = 1  # 小文件用单线程
    elif file_size < 10 * 1024 * 1024:  # 小于10MB
        threads = min(4, base_threads)
    elif file_size < 100 * 1024 * 1024:  # 小于100MB
        threads = min(8, base_threads)
    elif file_size < 1024 * 1024 * 1024:  # 小于1GB
        threads = base_threads
    else:  # 大于1GB
        threads = base_threads * 2
    
    # 确保线程数不会导致内存问题
    max_memory_based_threads = available_memory // (10 * 1024 * 1024)  # 假设每个线程消耗约10MB内存
    
    # 取较小的值作为最终线程数
    optimal_threads = min(threads, max_memory_based_threads, 32)  # 上限32线程
    
    logger.debug(f"计算的最优线程数: {optimal_threads} (文件大小: {file_size/1024/1024:.2f}MB, CPU: {cpu_count}, 内存可用: {available_memory/1024/1024:.2f}MB)")
    return max(1, int(optimal_threads))

def download_chunk(url, start_byte, end_byte, destination, chunk_id=0, retries=5):
    """
    下载文件的指定部分，使用智能重试机制

    :param url: 文件的URL
    :param start_byte: 开始下载的字节位置
    :param end_byte: 结束下载的字节位置
    :param destination: 文件保存的目标路径
    :param chunk_id: 分块ID，用于日志记录
    :param retries: 最大重试次数
    :return: 如果下载成功返回True，否则返回False
    """
    global is_downloading, is_paused
   
    # 构造请求头，指定下载的字节范围
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    attempt = 0
    retry_delay = 1  # 初始重试延迟（秒）
    total_chunk_size = end_byte - start_byte + 1
    chunk_downloaded = 0  # 当前分块已下载的字节数
    
    # 尝试下载文件，如果失败则重试
    while attempt < retries:
        try:
            # 计算当前分块的实际起始位置（考虑已下载部分）
            current_start = start_byte + chunk_downloaded
            
            if current_start > end_byte:
                return True  # 该分块已完全下载
            
            # 更新请求头，只下载剩余部分
            headers['Range'] = f'bytes={current_start}-{end_byte}'
            
            # 发起HTTP请求，包含自定义请求头，启用流式响应，设置超时
            response = requests.get(url, headers=headers, stream=True, timeout=15, verify=False)
            
            # 检查响应状态码，如果状态码表示错误，则抛出异常
            response.raise_for_status()
            
            # 使用文件锁确保并发安全，打开文件准备写入
            with lock:
                with open(destination, 'r+b') as f:
                    f.seek(current_start)
                    # 遍历响应内容，写入到文件中
                    for chunk in response.iter_content(chunk_size=8192):
                        # 如果下载被取消，则退出
                        if not is_downloading:
                            return False
                        
                        # 如果下载被暂停，则等待
                        while is_paused and is_downloading:
                            time.sleep(0.1)
                        
                        # 如果恢复后下载被取消，则退出
                        if not is_downloading:
                            return False
                        
                        f.write(chunk)
                        chunk_size = len(chunk)
                        downloaded_bytes[0] += chunk_size
                        chunk_downloaded += chunk_size
            
            # 如果完成了下载，返回成功
            if chunk_downloaded >= total_chunk_size:
                logger.debug(f"分块 {chunk_id} 下载完成 ({current_start}-{end_byte})")
            return True
            
        except requests.RequestException as e:
            # 如果发生网络请求异常，使用指数退避策略重试
            with lock:
                if not is_downloading:
                    return False
                
                if attempt + 1 < retries:
                    # 使用指数退避策略增加重试延迟
                    jitter = random.uniform(0, 0.1 * retry_delay)  # 添加随机抖动
                    wait_time = retry_delay + jitter
                    
                    logger.warning(f"分块 {chunk_id} 下载失败，将在 {wait_time:.2f} 秒后重试 ({attempt + 1}/{retries}): {e}")
                    
                    if is_downloading:
                        status_label.config(text=f"Chunk {chunk_id}: Retry in {wait_time:.1f}s ({attempt + 1}/{retries})")
                
                # 准备下一次重试
                attempt += 1
                retry_delay = min(retry_delay * 2, 60)  # 指数增长，上限为60秒
                
                # 在重试之前等待
                time.sleep(wait_time)
    
    # 如果重试次数用尽仍然失败，记录错误并返回失败
    with lock:
        if is_downloading:
            logger.error(f"分块 {chunk_id} 下载失败，重试次数已用尽: {e}", exc_info=True)
    
    return False

def pause_resume_download():
    """Pause or resume download"""
    global is_paused
    
    def update_ui():
        if is_paused:
            # Pause download UI
            pause_button.config(text=get_text("resume_download"))
            status_label.config(text=get_text("download_paused"))
        else:
            # Resume download UI
            pause_button.config(text=get_text("pause_download"))
            status_label.config(text=get_text("download_resumed"))
    
    # Toggle pause state
    is_paused = not is_paused
    logger.info("Download paused" if is_paused else "Download resumed")
    
    # Update UI in main thread
    root.after(0, update_ui)

def calculate_download_speed(bytes_received, elapsed_time):
    """
    Calculate download speed and return formatted string
    
    Parameters:
        bytes_received (int): Number of bytes received
        elapsed_time (float): Elapsed time in seconds
        
    Returns:
        str: Formatted download speed string
    """
    if elapsed_time <= 0:
        return "N/A"
    
    speed = bytes_received / elapsed_time  # bytes/second
    
    if speed < 1024:
        return f"{speed:.2f} B/s"
    elif speed < 1024 * 1024:
        return f"{speed/1024:.2f} KB/s"
    elif speed < 1024 * 1024 * 1024:
        return f"{speed/1024/1024:.2f} MB/s"
    else:
        return f"{speed/1024/1024/1024:.2f} GB/s"

def estimate_remaining_time(downloaded, total, speed):
    """
    Estimate remaining download time
    
    Parameters:
        downloaded (int): Number of bytes downloaded
        total (int): Total number of bytes
        speed (float): Current download speed (bytes/second)
        
    Returns:
        str: Formatted remaining time string
    """
    if speed <= 0:
        return "Calculating..."
    
    remaining_bytes = total - downloaded
    remaining_seconds = remaining_bytes / speed
    
    if remaining_seconds < 60:
        return f"{remaining_seconds:.0f} sec"
    elif remaining_seconds < 3600:
        return f"{remaining_seconds/60:.1f} min"
    else:
        return f"{remaining_seconds/3600:.1f} hours"

def update_progress():
    """Update progress bar and status label in a thread-safe manner"""
    global file_size, is_downloading, is_paused, last_downloaded, last_time, download_speeds
    
    def update_ui(progress, status_text, speed_text):
        """Update UI elements in main thread"""
        progress_bar['value'] = progress
        status_label.config(text=status_text)
        logger.debug(status_text.replace("Progress: ", ""))
    
    # Initialize progress bar
    root.after(0, lambda: [
        progress_bar.config(mode="indeterminate"),
        progress_bar.start(10)
    ])
    
    last_downloaded = 0
    last_time = time.time()
    
    # Continue updating progress while any download task is not completed
    while any(not future.done() for future in futures):
        if not is_downloading:
            break
        
        current_time = time.time()
        elapsed = current_time - last_time
        
        # Update speed once per second
        if elapsed >= 1.0:
            current_downloaded = downloaded_bytes[0]
            bytes_diff = current_downloaded - last_downloaded
            
            if bytes_diff > 0 and elapsed > 0:
                speed = bytes_diff / elapsed
                download_speeds.append(speed)
                avg_speed = sum(download_speeds) / len(download_speeds)
                speed_str = calculate_download_speed(bytes_diff, elapsed)
                remaining_time = estimate_remaining_time(current_downloaded, file_size, avg_speed)
                logger.debug(f"Current speed: {speed_str}, remaining: {remaining_time}")
            
            last_downloaded = current_downloaded
            last_time = current_time
        
        # Calculate progress
        progress = int(downloaded_bytes[0] / file_size * 100)
        
        # Prepare status text
        downloaded_mb = downloaded_bytes[0] / (1024 * 1024)
        total_mb = file_size / (1024 * 1024)
        speed_text = ""
        
        if len(download_speeds) > 0:
            avg_speed = sum(download_speeds) / len(download_speeds)
            speed_str = calculate_download_speed(avg_speed, 1)
            remaining_time = estimate_remaining_time(downloaded_bytes[0], file_size, avg_speed)
            speed_text = f" - {speed_str} - {get_text('remaining')}: {remaining_time}"
        
        status_text = f"{get_text('progress')}: {progress}%"
        if is_paused:
            status_text += f" ({get_text('paused')})"
        
        if total_mb >= 1:
            status_text += f" ({downloaded_mb:.2f} MB / {total_mb:.2f} MB){speed_text}"
        else:
            downloaded_kb = downloaded_bytes[0] / 1024
            total_kb = file_size / 1024
            status_text += f" ({downloaded_kb:.2f} KB / {total_kb:.2f} KB){speed_text}"
        
        # Update UI in main thread
        root.after(0, lambda p=progress, s=status_text: update_ui(p, s, speed_text))
        time.sleep(0.1)
    
    # Final update when download completes or is cancelled
    def final_update():
        if is_downloading:
            progress_bar['value'] = 100
            status_label.config(text=get_text("download_complete"))
            logger.info(f"Download completed: {destination}")
        else:
            status_label.config(text=get_text("download_cancelled"))
            logger.warning(f"Download cancelled: {destination}")
        
        return_normal()
        root.after(5000, clear)
    
    root.after(0, final_update)

def return_normal():
    """重置下载状态和UI元素"""
    global is_downloading, is_paused
    is_downloading = False
    is_paused = False
    
    # 重置UI元素
    progress_bar['value'] = 0
    status_label.config(text="")
    
    
    # 恢复按钮状态
    download_button.config(state="normal")
    cancel_button.grid_forget()
    pause_button.grid_forget()
    
    # 确保状态标签和进度条正确显示
    progress_bar.grid(row=7, column=0, columnspan=3, pady=10, padx=10)
    status_label.grid(row=8, column=0, columnspan=3, pady=10, padx=10)

def download_selected_version():
    """下载选定的Python版本"""
    if not version_combobox.get() or version_combobox.get() == "Select Python Version":
        messagebox.showwarning(get_text("warning_msg"), get_text("select_python_version_first"))
        return

    if download_file_combobox.get() == "":
        messagebox.showwarning(get_text("warning_msg"), get_text("select_download_file"))
        return

    global destination_dir, destination, executor, futures, is_downloading, downloaded_bytes, last_downloaded, last_time, is_paused
    
    destination_dir = destination_entry.get()
    if not destination_dir:
        messagebox.showwarning(get_text("warning_msg"), get_text("select_destination_dir"))
        return

    if not os.path.exists(destination_dir):
        try:
            os.makedirs(destination_dir)
        except Exception as e:
            messagebox.showerror(get_text("error"), get_text("failed_to_create_dir").format(e))
            return

    version = version_combobox.get().split('-')[0]
    file_name = download_file_combobox.get()
    destination = os.path.join(destination_dir, file_name)

    if os.path.exists(destination):
        response = messagebox.askyesno(get_text("warning_msg"), get_text("file_exists"))
        if not response:
            return
        try:
            os.remove(destination)
        except Exception as e:
            messagebox.showerror(get_text("error"), get_text("failed_to_remove_file").format(e))
            return

    # 更新UI状态
    download_button.config(state="disabled")  # 禁用下载按钮
    cancel_button.grid(row=4, column=0, columnspan=1, pady=10, padx=10, sticky="e")  # 显示取消按钮
    cancel_button.config(state="normal")

    # 调整暂停按钮位置，置于取消按钮下方
    pause_button.grid(row=5, column=0, columnspan=1, pady=10, padx=10, sticky="e")  # 显示暂停按钮
    pause_button.config(text="Pause Download", state="normal")
    
    # 确保进度条和状态标签正确显示
    progress_bar.grid(row=7, column=0, columnspan=3, pady=10, padx=10)
    status_label.grid(row=8, column=0, columnspan=3, pady=10, padx=10)
    
    selected_url = None
    python_mirror = read_python_mirror()
    
    if python_mirror and python_mirror != "":
        download_url = f"{python_mirror}/{version}/{file_name}"
        selected_url = download_url
    else:
        # 尝试所有镜像
        status_label.config(text=get_text("finding_mirror"))
        for mirror in PYTHON_MIRRORS:
            download_url = f"{mirror}/{version}/{file_name}"
            try:
                response = requests.head(download_url, timeout=5, verify=False)
                if response.status_code == 200:
                    selected_url = download_url
                    break
            except requests.RequestException:
                continue

    if not selected_url:
        messagebox.showerror(get_text("error"), get_text("failed_to_find_mirror"))
        download_button.config(state="normal")  # 恢复下载按钮
        cancel_button.grid_forget()  # 隐藏取消按钮
        pause_button.grid_forget()  # 隐藏暂停按钮
        return

    # 重置下载状态
    is_downloading = True
    is_paused = False
    downloaded_bytes[0] = 0
    last_downloaded = 0
    last_time = time.time()
    download_speeds.clear()

    try:
        # 创建线程池
        threads = int(thread_combobox.get()) if thread_combobox.get() else 10
        
        global file_size
        response = requests.head(selected_url, timeout=10, verify=False)
        file_size = int(response.headers.get('content-length', 0))
        
        if file_size == 0:
            messagebox.showerror(get_text("error"), get_text("failed_to_get_file_size"))
            download_button.config(state="normal")  # 恢复下载按钮
            cancel_button.grid_forget()  # 隐藏取消按钮
            pause_button.grid_forget()  # 隐藏暂停按钮
            return
        
        status_label.config(text=get_text("starting_download").format(file_name))
        
        # 计算每个线程应下载的文件块大小
        chunk_size = file_size // threads
        
        # 创建线程池
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=threads)
        futures.clear()
        
        # 分配下载任务给每个线程
        for i in range(threads):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < threads - 1 else file_size
            futures.append(executor.submit(download_file_chunk, selected_url, destination, start, end))
        
        # 启动进度更新线程
        threading.Thread(target=update_progress, daemon=True).start()
        
    except Exception as e:
        messagebox.showerror(get_text("error"), get_text("download_start_failed").format(e))
        download_button.config(state="normal")  # 恢复下载按钮
        cancel_button.grid_forget()  # 隐藏取消按钮
        pause_button.grid_forget()  # 隐藏暂停按钮
        is_downloading = False

def show_pip_version():
    """显示pip版本，安全地避免线程问题"""
    # 不要在这里直接更新UI
    
    # 在主线程中安全地更新UI的函数
    def update_pip_ui_safely(action, button_text, button_state):
        try:
            pip_upgrade_button.config(text=button_text, state=button_state)
            pip_retry_button.grid_forget()  # 隐藏重试按钮
        except Exception as e:
            logger.error(f"更新pip UI失败: {e}")
    
    # 在主线程中安全地显示错误消息
    def update_pip_ui_error():
        try:
            pip_upgrade_button.config(text=get_text("failed_to_get_pip_version"), state="disabled")
            pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
        except Exception as e:
            logger.error(f"更新pip错误UI失败: {e}")
    
    # 首先在主线程中设置检查中状态
    root.after(0, lambda: update_pip_ui_safely("checking", get_text("pip_checking"), "disabled"))
    
    # 定义线程函数
    def check_pip_version_thread():
        try:
            # 获取pip版本信息
            version_pip = get_pip_version(config_path)
            with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
                b = f.readlines()
                python_name = "Python" + b[-1].strip("\n").strip("Pip")
            
            latest_version = get_latest_pip_version()
            
            # 准备更新UI的数据
            if version_pip == latest_version:
                action = "up_to_date"
                button_text = get_text("pip_up_to_date").format(python_name, version_pip)
                button_state = "disabled"
                update_flag = "False"
            else:
                action = "update_available"
                button_text = get_text("pip_new_version_available").format(
                    python_name, version_pip, latest_version
                )
                button_state = "normal"
                # 检查其他按钮状态
                if "disabled" in install_button.state() and "disabled" in uninstall_button.state():
                    button_state = "disabled"
                update_flag = "True"
            
            # 保存pip检查结果
            with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                fw.write(update_flag + "\n")
                fw.write(version_pip if version_pip else "")
            
            # 安全地在主线程中更新UI
            root.after(0, lambda: update_pip_ui_safely(action, button_text, button_state))
            
        except Exception as e:
            logger.error(f"Failed to get pip version: {e}")
            # 安全地在主线程中更新错误UI
            root.after(0, lambda: update_pip_ui_error())
    
    # 如果从主线程调用，直接启动检查线程
    if threading.current_thread() is threading.main_thread():
        threading.Thread(target=check_pip_version_thread, daemon=True).start()
    else:
        # 如果已经在线程中，则让主线程启动检查线程
        root.after(0, lambda: threading.Thread(target=check_pip_version_thread, daemon=True).start())

def retry_pip_ui():
    """重试检查pip版本"""
    try:
        # 直接调用show_pip_version()函数
        if threading.current_thread() is threading.main_thread():
            show_pip_version()
        else:
            # 如果从非主线程调用，则使用root.after确保在主线程中执行
            root.after(0, show_pip_version)
    except Exception as e:
        logger.error(f"重试检查pip版本失败: {e}")
        # 确保错误信息在UI上显示
        try:
            root.after(0, lambda: pip_upgrade_button.config(
                text=get_text("failed_to_get_pip_version"), 
                state="disabled"
            ))
        except Exception:
            pass

def monitor_package_ui():
    """监控包版本更新"""
    # 调用模块化的监控函数
    monitor_package_version(
        package_entry, upgrade_button, install_button, 
        uninstall_button, config_path
    )

def read_python_mirror():
    """读取Python镜像源配置"""
    try:
        config_path_base = os.path.join(os.environ["APPDATA"], "pyquick")
        mirror_file = os.path.join(config_path_base, "pythonmirror.txt")
        if os.path.exists(mirror_file):
            with open(mirror_file, 'r') as f:
                mirror = f.read().strip()
                if mirror == get_text("default_source"):
                    return "https://www.python.org/ftp/python"
                return mirror
        return "https://www.python.org/ftp/python"  # 默认返回官方源
    except Exception as e:
        logger.error(f"读取Python镜像源配置失败: {e}")
        return "https://www.python.org/ftp/python"

def download_file_chunk(url, destination, start_byte, end_byte):
    """下载文件的一个分块"""
    try:
        headers = {'Range': f'bytes={start_byte}-{end_byte}'}
        response = requests.get(url, headers=headers, stream=True, verify=False, timeout=30)
        
        with open(destination, 'r+b') as f:
            f.seek(start_byte)
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        return True
    except Exception as e:
        logger.error(f"下载分块失败: {e}")
        return False

def load_theme():
    """加载主题设置"""
    try:
        # 确保主题设置目录存在
        if not os.path.exists(config_path):
            os.makedirs(config_path)
            
        theme_file = os.path.join(config_path, "theme.txt")
        theme = "light"  # 默认主题
        
        # 读取主题设置
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r') as f:
                    file_theme = f.read().strip()
                    if file_theme in ["light", "dark"]:
                        theme = file_theme
                    logger.info(f"从文件加载主题: {theme}")
            except Exception as e:
                logger.error(f"读取主题文件失败: {e}")
        else:
            # 如果主题文件不存在，创建默认主题文件
            try:
                with open(theme_file, 'w') as f:
                    f.write(theme)
                logger.info(f"创建默认主题文件: {theme}")
            except Exception as e:
                logger.error(f"创建主题文件失败: {e}")
        
        # 使用全局字典保存设置
        global settings
        settings["theme"] = theme
        
        # 应用主题
        try:
            sv_ttk.set_theme(theme)
            logger.info(f"成功应用主题: {theme}")
            return theme
        except Exception as e:
            logger.error(f"应用主题失败，请确保sv_ttk正确安装: {e}")
            return theme
    except Exception as e:
        logger.error(f"加载主题过程中发生错误: {e}")
        return "light"  # 出错时返回默认主题

def show_name():
    """显示应用名称 - 支持多语言"""
    try:
        # 使用get_text函数获取当前语言的应用标题
        return get_text("app_title")
    except Exception as e:
        logger.error(f"获取应用名称失败: {e}")
        # 出错时返回默认标题
        return "PyQuick"

def check_python_installation():
    """检查Python安装情况"""
    try:
        installed_versions = []
        # 检查常见的Python安装位置
        possible_paths = [
            os.path.join(os.environ.get("ProgramFiles", ""), "Python*"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Python*"),
            os.path.join(os.environ.get("LocalAppData", ""), "Programs", "Python", "Python*")
        ]
        
        for path_pattern in possible_paths:
            for path in glob.glob(path_pattern):
                if os.path.isdir(path) and os.path.exists(os.path.join(path, "python.exe")):
                    version = os.path.basename(path).replace("Python", "")
                    installed_versions.append((version, path))
        
        return installed_versions
    except Exception as e:
        logger.error(f"检查Python安装失败: {e}")
        return []

def install_package_ui():
    """安装包UI处理函数"""
    package_name = package_entry.get()
    if not package_name:
        messagebox.showwarning(get_text("warning_msg"), get_text("enter_package_name_first"))
        return

    pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
    pip_progress_bar.start(10)

    package_entry.config(state="disabled")
    install_button.config(state="disabled")
    uninstall_button.config(state="disabled")
    upgrade_button.config(state="disabled")
    
    install_package(package_name, config_path, package_status_label, pip_progress_bar, 
                  install_button, pip_upgrade_button, package_entry, uninstall_button, 
                  upgrade_button, root)

def uninstall_package_ui():
    """卸载包UI处理函数"""
    package_name = package_entry.get()
    if not package_name:
        messagebox.showwarning(get_text("warning_msg"), get_text("enter_package_name_first"))
        return
    
    pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
    pip_progress_bar.start(10)
    
    package_entry.config(state="disabled")
    install_button.config(state="disabled")
    uninstall_button.config(state="disabled")
    upgrade_button.config(state="disabled")
    
    uninstall_package(package_name, config_path, package_status_label, pip_progress_bar, 
                    uninstall_button, upgrade_button, pip_upgrade_button, package_entry, 
                    install_button, root)

def upgrade_package_ui():
    """升级包UI处理函数"""
    package_name = package_entry.get()
    if not package_name:
        messagebox.showwarning(get_text("warning_msg"), get_text("enter_package_name_first"))
        return
    
    pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
    pip_progress_bar.start(10)
    
    package_entry.config(state="disabled")
    install_button.config(state="disabled")
    uninstall_button.config(state="disabled")
    upgrade_button.config(state="disabled")
    
    upgrade_package(package_name, config_path, package_status_label, pip_progress_bar, 
                  upgrade_button, pip_upgrade_button, package_entry, install_button, 
                  uninstall_button, root)

# 添加全局设置字典
settings = {
    "theme": "light",
    "python_mirror": get_text("default_source"),
    "pip_mirror": get_text("default_source"),
    "allow_multithreading": True,
    "language": "zh_CN",  # 默认简体中文
    "max_log_size": 10    # 默认最大日志大小(MB)
}

def settings1():
    """打开设置窗口，配置程序设置和日志选项"""
    global settings_window
    
    # 读取allowthread.txt文件获取多线程下载设置
    try:
        thread_file = os.path.join(config_path, "allowthread.txt")
        allow_multithreading = True  # 默认启用
        if os.path.exists(thread_file):
            with open(thread_file, "r") as r:
                lines = r.readlines()
                if lines:
                    value = lines[-1].strip().lower()
                    allow_multithreading = (value == "true")
        settings["allow_multithreading"] = allow_multithreading
        
        # 读取语言设置
        language_file = os.path.join(config_path, "language.txt")
        if os.path.exists(language_file):
            with open(language_file, "r") as r:
                lang = r.read().strip() or "zh_CN"
                settings["language"] = lang
                set_language(lang)  # 设置当前语言
        
        # 读取日志大小设置
        log_size_file = os.path.join(config_path, "log_size.txt")
        if os.path.exists(log_size_file):
            with open(log_size_file, "r") as r:
                size_str = r.read().strip()
                if size_str and size_str.isdigit():
                    settings["max_log_size"] = int(size_str)
    except Exception as e:
        logger.error(f"{get_text('settings_read_fail')}: {e}")
    
    # 简单、直接地创建窗口
    settings_window = tk.Toplevel(root)
    settings_window.title(get_text("settings"))
    #settings_window.geometry("500x520")  # 增加窗口高度以容纳新选项
    settings_window.resizable(True, True)  # 允许调整窗口大小
    
    # 设置为模态窗口
    settings_window.transient(root)
    settings_window.grab_set()
    
    # 创建主框架
    main_frame = ttk.Frame(settings_window, padding=20)
    main_frame.pack(expand=True, fill="both")
    
    # ===== 语言设置 =====
    language_frame = ttk.LabelFrame(main_frame, text=get_text("language_settings"), padding=10)
    language_frame.pack(fill="x", pady=(0, 15))
    
    language_var = tk.StringVar(value=settings.get("language", "zh_CN"))
    ttk.Radiobutton(language_frame, text=get_text("simplified_chinese"), value="zh_CN", variable=language_var).pack(side="left", padx=20)
    ttk.Radiobutton(language_frame, text=get_text("english"), value="en_US", variable=language_var).pack(side="left", padx=20)
    
    # ===== 主题设置 =====
    theme_frame = ttk.LabelFrame(main_frame, text=get_text("theme_settings"), padding=10)
    theme_frame.pack(fill="x", pady=(0, 15))
    
    theme_var = tk.StringVar(value=settings.get("theme", "light"))
    ttk.Radiobutton(theme_frame, text=get_text("light_theme"), value="light", variable=theme_var).pack(side="left", padx=20)
    ttk.Radiobutton(theme_frame, text=get_text("dark_theme"), value="dark", variable=theme_var).pack(side="left", padx=20)
    
    # ===== 镜像设置 =====
    mirror_frame = ttk.LabelFrame(main_frame, text=get_text("download_mirror_settings"), padding=10)
    mirror_frame.pack(fill="x", pady=(0, 15))
    
    # 获取镜像列表（不显示默认源）
    python_default_mirror = "https://www.python.org/ftp/python"
    # 获取其他预定义镜像和自定义镜像
    python_other_mirrors = [m for m in PYTHON_MIRRORS if m != python_default_mirror]
    custom_python_mirrors = get_custom_python_mirrors()
    
    python_all_mirrors = [get_text("default_source")] + python_other_mirrors + custom_python_mirrors
    
    # Python镜像选择
    ttk.Label(mirror_frame, text=get_text("python_download_mirror")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
    python_mirror_var = tk.StringVar(value=settings.get("python_mirror", get_text("default_source")))
    python_mirror_combo = ttk.Combobox(mirror_frame, textvariable=python_mirror_var, width=35, state="readonly")
    python_mirror_combo["values"] = python_all_mirrors
    python_mirror_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
    mirror_frame.columnconfigure(1, weight=1)
    
    # 添加Python默认源提示
    ttk.Label(mirror_frame, text=f"{get_text('default_source')}: {python_default_mirror}").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5), padx=5)
    
    # 添加测试Python镜像按钮
    ttk.Button(mirror_frame, text=get_text("test_python_mirror"), command=lambda: show_mirror_test_window("python")).grid(row=0, column=2, padx=5, pady=5)
    
    # Pip镜像
    # 获取pip镜像列表（不显示默认源）
    pip_default_mirror = PIP_MIRRORS[0]
    pip_other_mirrors = PIP_MIRRORS[1:]
    custom_pip_mirrors = get_custom_pip_mirrors()
    
    pip_all_mirrors = [get_text("default_source")] + pip_other_mirrors + custom_pip_mirrors
    
    ttk.Label(mirror_frame, text=get_text("pip_mirror")).grid(row=2, column=0, sticky="w", pady=5, padx=5)
    pip_mirror_var = tk.StringVar(value=settings.get("pip_mirror", get_text("default_source")))
    pip_mirror_combo = ttk.Combobox(mirror_frame, textvariable=pip_mirror_var, width=35, state="readonly")
    pip_mirror_combo["values"] = pip_all_mirrors
    pip_mirror_combo.grid(row=2, column=1, sticky="w", pady=5, padx=5)
    
    # 添加测试Pip镜像按钮
    ttk.Button(mirror_frame, text=get_text("test_pip_mirror"), command=lambda: show_mirror_test_window("pip")).grid(row=2, column=2, padx=5, pady=5)
    
    # 添加Pip默认源提示
    ttk.Label(mirror_frame, text=f"{get_text('default_source')}: {pip_default_mirror}").grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 5), padx=5)
    
    # ===== 日志设置 =====
    log_frame = ttk.LabelFrame(main_frame, text=get_text("log_settings"), padding=10)
    log_frame.pack(fill="x", pady=(0, 15))
    
    ttk.Label(log_frame, text=get_text("max_log_size")).grid(row=0, column=0, sticky="w", pady=5, padx=5)
    log_size_var = tk.StringVar(value=str(settings.get("max_log_size", 10)))
    log_size_combo = ttk.Combobox(log_frame, textvariable=log_size_var, width=10, state="readonly")
    log_size_combo["values"] = ["5", "10", "20", "50", "100"]
    log_size_combo.grid(row=0, column=1, sticky="w", pady=5, padx=5)
    
    # ===== 多线程设置 =====
    other_frame = ttk.LabelFrame(main_frame, text=get_text("download_settings"), padding=10)
    other_frame.pack(fill="x", pady=(0, 15))
    
    multithreading_var = tk.BooleanVar(value=settings.get("allow_multithreading", True))
    ttk.Checkbutton(other_frame, text=get_text("enable_multithreading"), variable=multithreading_var).pack(anchor="w", padx=5)
    
    # 读取pip版本检查设置
    auto_check_pip_var = tk.BooleanVar(value=True)  # 默认启用
    try:
        with open(os.path.join(config_path, "allowupdatepip.txt"), "r") as f:
            lines = f.readlines()
            if lines:
                auto_check_pip_var.set(lines[0].strip().lower() == "true")
    except Exception as e:
        logger.error(f"读取pip版本检查设置失败: {e}")
    
    # 添加pip版本检查选项
    ttk.Checkbutton(other_frame, text=get_text("enable_pip_version_check"), variable=auto_check_pip_var).pack(anchor="w", padx=5)
    
    # ===== 底部按钮 =====
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(side="bottom", fill="x", pady=(10, 0))
    
    # 保存函数
    def save_settings_func():
        try:
            old_language = settings.get("language", "zh_CN")
            
            # 更新设置字典
            settings["theme"] = theme_var.get()
            settings["python_mirror"] = python_mirror_var.get() if python_mirror_var.get() else get_text("default_source")
            settings["pip_mirror"] = pip_mirror_var.get() if pip_mirror_var.get() else get_text("default_source")
            settings["allow_multithreading"] = multithreading_var.get()
            settings["language"] = language_var.get()
            settings["max_log_size"] = int(log_size_var.get())
            settings["auto_check_pip"] = auto_check_pip_var.get()
            
            # 保存设置到文件
            with open(os.path.join(config_path, "theme.txt"), "w") as f:
                f.write(settings["theme"])
            
            with open(os.path.join(config_path, "pythonmirror.txt"), "w") as f:
                f.write(settings["python_mirror"])
            
            with open(os.path.join(config_path, "pipmirror.txt"), "w") as f:
                f.write(settings["pip_mirror"])
            
            with open(os.path.join(config_path, "allowthread.txt"), "w") as f:
                # 将布尔值转换为"True"或"False"字符串
                f.write("True" if settings["allow_multithreading"] else "False")
            
            # 保存语言设置
            with open(os.path.join(config_path, "language.txt"), "w") as f:
                f.write(settings["language"])
                
            # 保存日志大小设置
            with open(os.path.join(config_path, "log_size.txt"), "w") as f:
                f.write(str(settings["max_log_size"]))
            
            # 保存pip版本检查设置
            try:
                # 保持当前版本信息不变
                current_version = ""
                with open(os.path.join(config_path, "allowupdatepip.txt"), "r") as f:
                    lines = f.readlines()
                    if len(lines) > 1:
                        current_version = lines[1].strip()
                
                with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as f:
                    f.write("True" if settings["auto_check_pip"] else "False")
                    f.write("\n")
                    if current_version:
                        f.write(current_version)
            except Exception as e:
                logger.error(f"保存pip版本检查设置失败: {e}")
            
            # 应用主题
            sv_ttk.set_theme(settings["theme"])
            
            # 检查语言是否更改，如果更改了，设置新语言
            if old_language != settings["language"]:
                set_language(settings["language"])
                # 显示需要重启的提示
                restart_msg = get_text("language_changed")
                
                # 语言变更时强制重启应用以确保所有UI元素正确更新
                messagebox.showinfo(get_text("success"), restart_msg, parent=settings_window)
                settings_window.destroy()
                # 重启应用程序
                python = sys.executable
                script = os.path.abspath(sys.argv[0])
                root.destroy()  # 确保主窗口关闭
                os.execl(python, python, script)
            else:
                # 没有更改语言，使用当前语言显示消息
                messagebox.showinfo(get_text("success"), get_text("settings_saved"), parent=settings_window)
        except Exception as e:
            logger.error(f"{get_text('settings_save_fail')}: {e}")
            messagebox.showwarning(get_text("warning_code"), get_text("save_failed").format(e), parent=settings_window)
    
    # 添加按钮
    ttk.Button(button_frame, text=get_text("cancel"), command=settings_window.destroy).pack(side="right", padx=5)
    ttk.Button(button_frame, text=get_text("save"), command=save_settings_func).pack(side="right", padx=5)
    
    # 居中显示窗口
    settings_window.update_idletasks()
    width = settings_window.winfo_width()
    height = settings_window.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    #settings_window.geometry(f'{width}x{height}+{x}+{y}')
    
    # 设置窗口关闭事件并设置焦点
    settings_window.protocol("WM_DELETE_WINDOW", settings_window.destroy)
    settings_window.focus_set()

def show_debug_info():
    """显示调试信息窗口，包含系统信息和应用信息"""
    debug_window = tk.Toplevel(root)
    debug_window.title(get_text("debug_info"))
    debug_window.resizable(True, True)  # 允许调整窗口大小
    
    # 设置为模态窗口
    debug_window.transient(root)
    debug_window.grab_set()
    
    # 创建主框架
    main_frame = ttk.Frame(debug_window, padding=20)
    main_frame.pack(expand=True, fill="both")
    
    # 创建选项卡
    notebook = ttk.Notebook(main_frame)
    notebook.pack(expand=True, fill="both")
    
    # 当前主题
    current_theme = settings.get("theme", "light")
    is_dark_theme = current_theme == "dark"
    
    # 定义颜色方案 - 根据主题设置不同的颜色
    colors = {
        "title": "#0066cc" if not is_dark_theme else "#66b2ff",
        "section": "#555555" if not is_dark_theme else "#ffffff",
        "label": "#333333" if not is_dark_theme else "#cccccc", 
        "value": "#000000" if not is_dark_theme else "#ffffff",
        "config_section": "#996633" if not is_dark_theme else "#ffcc99",
        "dynamic_section": "#009933" if not is_dark_theme else "#66ff99",
        "info_log": "#000000" if not is_dark_theme else "#ffffff"
    }
    
    # ===== 系统信息选项卡 =====
    system_frame = ttk.Frame(notebook, padding=10)
    notebook.add(system_frame, text=get_text("system_info"))
    
    # 创建含滚动条的系统信息框架
    system_info_frame = ttk.Frame(system_frame)
    system_info_frame.pack(fill="both", expand=True)
    
    # 创建文本框显示系统信息
    system_info_text = tk.Text(system_info_frame, wrap=tk.WORD, width=70, height=20)
    system_info_text.pack(side=tk.LEFT, fill="both", expand=True)
    system_info_text.config(state=tk.DISABLED)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(system_info_frame, command=system_info_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    system_info_text.config(yscrollcommand=scrollbar.set)
    
    # ===== 应用信息选项卡 =====
    app_frame = ttk.Frame(notebook, padding=10)
    notebook.add(app_frame, text=get_text("app_info"))
    
    # 创建刷新按钮
    app_refresh_frame = ttk.Frame(app_frame)
    app_refresh_frame.pack(fill="x", pady=5)
    
    def refresh_app_info():
        # 创建一个单独的函数来更新应用信息
        update_app_info_display()
        # 执行垃圾回收
        gc.collect()
    
    ttk.Button(app_refresh_frame, text=get_text("refresh_info"), command=refresh_app_info).pack(side=tk.RIGHT, padx=5)
    
    # 创建含滚动条的应用信息框架
    app_info_frame = ttk.Frame(app_frame)
    app_info_frame.pack(fill="both", expand=True)
    
    app_info_text = tk.Text(app_info_frame, wrap=tk.WORD, width=70, height=20)
    app_info_text.pack(side=tk.LEFT, fill="both", expand=True)
    app_info_text.config(state=tk.DISABLED)
    
    # 添加滚动条
    app_scrollbar = ttk.Scrollbar(app_info_frame, command=app_info_text.yview)
    app_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    app_info_text.config(yscrollcommand=app_scrollbar.set)
    
    # ===== 日志信息选项卡 =====
    log_frame = ttk.Frame(notebook, padding=10)
    notebook.add(log_frame, text=get_text("log_info"))
    
    # 创建日志控制面板
    log_control_frame = ttk.Frame(log_frame)
    log_control_frame.pack(fill="x", pady=5)
    
    # 添加日志级别选择
    log_level_var = tk.StringVar(value="all")
    
    ttk.Label(log_control_frame, text=get_text("log_filter")).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(log_control_frame, text=get_text("show_errors_only"), variable=log_level_var, value="error").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(log_control_frame, text=get_text("show_errors_warnings"), variable=log_level_var, value="warning").pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(log_control_frame, text=get_text("show_all_logs"), variable=log_level_var, value="all").pack(side=tk.LEFT, padx=5)
    
    # 刷新日志按钮
    def refresh_log_info():
        update_log_info_display(log_level_var.get())
        # 执行垃圾回收
        gc.collect()
    
    ttk.Button(log_control_frame, text=get_text("refresh_log"), command=refresh_log_info).pack(side=tk.RIGHT, padx=5)
    
    # 创建含滚动条的日志信息框架
    log_info_frame = ttk.Frame(log_frame)
    log_info_frame.pack(fill="both", expand=True, pady=5)
    
    log_info_text = tk.Text(log_info_frame, wrap=tk.WORD, width=70, height=18)
    log_info_text.pack(side=tk.LEFT, fill="both", expand=True)
    log_info_text.config(state=tk.DISABLED)
    
    # 添加滚动条
    log_scrollbar = ttk.Scrollbar(log_info_frame, command=log_info_text.yview)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_info_text.config(yscrollcommand=log_scrollbar.set)
    
    # ===== 网络诊断选项卡 =====
    network_frame = ttk.Frame(notebook, padding=10)
    notebook.add(network_frame, text=get_text("network_diagnostics"))
    
    # 创建网络诊断控制面板
    network_control_frame = ttk.Frame(network_frame)
    network_control_frame.pack(fill="x", pady=5)
    
    # 创建一个子框架用于放置按钮
    network_buttons_frame = ttk.Frame(network_control_frame)
    network_buttons_frame.pack(pady=5)
    
    # 创建进度条和状态标签
    network_status_var = tk.StringVar(value=get_text("network_test_ready"))
    network_status_label = ttk.Label(network_control_frame, textvariable=network_status_var)
    network_status_label.pack(pady=2)
    
    network_progress_var = tk.DoubleVar()
    network_progress_bar = ttk.Progressbar(network_control_frame, variable=network_progress_var, maximum=100)
    network_progress_bar.pack(fill="x", pady=5)
    
    # 创建网络诊断文本框
    network_info_frame = ttk.Frame(network_frame)
    network_info_frame.pack(fill="both", expand=True, pady=5)
    
    network_info_text = tk.Text(network_info_frame, wrap=tk.WORD, width=70, height=15)
    network_info_text.pack(side=tk.LEFT, fill="both", expand=True)
    network_info_text.config(state=tk.DISABLED)
    
    # 添加滚动条
    network_scrollbar = ttk.Scrollbar(network_info_frame, command=network_info_text.yview)
    network_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    network_info_text.config(yscrollcommand=network_scrollbar.set)
    
    # 网络诊断任务变量
    network_test_running = False
    network_test_paused = False
    network_test_cancel = False
    
    # 网络诊断函数
    def run_network_diagnostics():
        nonlocal network_test_running, network_test_paused, network_test_cancel
        
        # 如果已经在运行则不重复启动
        if network_test_running:
            return
        
        network_test_running = True
        network_test_paused = False
        network_test_cancel = False
        
        # 更新UI状态
        run_diagnostics_button.config(state=tk.DISABLED)
        pause_diagnostics_button.config(state=tk.NORMAL)
        cancel_diagnostics_button.config(state=tk.NORMAL)
        
        def run_diagnostics_thread():
            nonlocal network_test_running, network_test_paused, network_test_cancel
            
            # 清空文本框
            network_info_text.config(state=tk.NORMAL)
            network_info_text.delete(1.0, tk.END)
            network_info_text.insert(tk.END, get_text("network_test_preparing") + "\n\n")
            network_info_text.config(state=tk.DISABLED)
            
            # 测试的网站列表
            websites = [
                "https://www.google.com",
                "https://www.python.org",
                "https://pypi.org",
                "https://github.com",
                "https://mirrors.tuna.tsinghua.edu.cn",
                "https://mirrors.aliyun.com"
            ]
            
            # 更新状态和进度条
            network_status_var.set(get_text("network_test_initializing"))
            network_progress_var.set(0)
            
            # 更新文本框标题
            network_info_text.config(state=tk.NORMAL)
            network_info_text.delete(1.0, tk.END)
            
            # 添加标题和样式
            network_info_text.tag_configure("title", font=("微软雅黑", 12, "bold"), justify="center")
            network_info_text.tag_configure("subtitle", font=("微软雅黑", 10), justify="center", foreground="gray")
            network_info_text.tag_configure("normal", font=("微软雅黑", 9))
            network_info_text.tag_configure("success", foreground="green", font=("微软雅黑", 9, "bold"))
            network_info_text.tag_configure("error", foreground="red", font=("微软雅黑", 9, "bold"))
            network_info_text.tag_configure("warning", foreground="orange", font=("微软雅黑", 9, "bold"))
            network_info_text.tag_configure("info", foreground="blue", font=("微软雅黑", 9))
            
            network_info_text.insert(tk.END, get_text("network_test_results") + "\n", "title")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            network_info_text.insert(tk.END, get_text("network_test_time").format(timestamp) + "\n\n", "subtitle")
            network_info_text.config(state=tk.DISABLED)
            
            # 遍历并测试每个网站
            for i, site in enumerate(websites):
                # 检查是否取消
                if network_test_cancel:
                        break
                        
                # 更新进度和状态
                progress = (i / len(websites)) * 100
                network_progress_var.set(progress)
                network_status_var.set(get_text("network_test_in_progress").format(i+1, len(websites), site))
                
                # 显示当前测试的网站
                network_info_text.config(state=tk.NORMAL)
                network_info_text.insert(tk.END, get_text("network_test_site").format(i+1, len(websites), site), "normal")
                network_info_text.see(tk.END)
                network_info_text.config(state=tk.DISABLED)
                debug_window.update()  # 刷新UI
                
                # 等待，如果暂停
                while network_test_paused and not network_test_cancel:
                    network_status_var.set(get_text("network_test_paused"))
                    time.sleep(0.1)
                    debug_window.update()
                
                # 如果已取消，则退出循环
                if network_test_cancel:
                    break
                
                try:
                    # 发送请求并计时
                    start_time = time.time()
                    response = requests.get(site, timeout=5, verify=False)
                    elapsed = time.time() - start_time
                    
                    # 判断状态
                    status_code = response.status_code
                    if 200 <= status_code < 400:
                        status = get_text("network_test_status_normal")
                        tag = "success"
                    else:
                        status = get_text("network_test_status_error")
                        tag = "error"
                    
                    # 更新结果
                    network_info_text.config(state=tk.NORMAL)
                    network_info_text.delete("end-1l", "end")  # 删除"测试中"行
                    
                    # 插入结果行
                    network_info_text.insert(tk.END, f"[{status}] ", tag)
                    network_info_text.insert(tk.END, f"{site} ")
                    network_info_text.insert(tk.END, get_text("network_test_status_code").format(status_code) + "\n", "normal")
                    network_info_text.insert(tk.END, get_text("network_test_response_time").format(elapsed) + "\n\n", "info")
                    
                    # 确保滚动到最新内容
                    network_info_text.see(tk.END)
                    network_info_text.config(state=tk.DISABLED)
                    
                except requests.exceptions.RequestException as e:
                    # 更新失败结果
                    network_info_text.config(state=tk.NORMAL)
                    network_info_text.delete("end-1l", "end")  # 删除"测试中"行
                    
                    # 插入错误信息
                    network_info_text.insert(tk.END, f"[{get_text('network_test_status_failed')}] ", "error")
                    network_info_text.insert(tk.END, f"{site}\n", "normal")
                    network_info_text.insert(tk.END, get_text("network_test_error").format(str(e)) + "\n\n", "warning")
                    
                    # 确保滚动到最新内容
                    network_info_text.see(tk.END)
                    network_info_text.config(state=tk.DISABLED)
            
            # 完成所有测试或取消测试
            network_progress_var.set(100)
            
            # 添加摘要
            network_info_text.config(state=tk.NORMAL)
            if network_test_cancel:
                network_info_text.insert(tk.END, "\n" + get_text("network_test_canceled") + "\n", "warning")
                network_status_var.set(get_text("network_test_status_canceled"))
            else:
                network_info_text.insert(tk.END, "\n" + get_text("network_test_completed") + "\n", "success")
                network_status_var.set(get_text("network_test_status_completed"))
            network_info_text.config(state=tk.DISABLED)
            
            # 恢复UI状态
            run_diagnostics_button.config(state=tk.NORMAL)
            pause_diagnostics_button.config(state=tk.DISABLED)
            cancel_diagnostics_button.config(state=tk.DISABLED)
            
            # 标记测试已完成
            network_test_running = False
        
        # 在单独的线程中运行诊断以避免阻塞UI
        threading.Thread(target=run_diagnostics_thread, daemon=True).start()
    
    def pause_resume_network_diagnostics():
        nonlocal network_test_paused
        
        if not network_test_running:
            return
        
        # 切换暂停状态
        network_test_paused = not network_test_paused
        
        # 更新按钮文本
        if network_test_paused:
            pause_diagnostics_button.config(text=get_text("resume_test"))
        else:
            pause_diagnostics_button.config(text=get_text("pause_test"))
    
    def cancel_network_diagnostics():
        nonlocal network_test_cancel
        
        if not network_test_running:
            return
        
        # 设置取消标志
        network_test_cancel = True
        
        # 如果当前处于暂停状态，取消暂停以便线程可以进行并检测取消状态
        if network_test_paused:
            network_test_paused = False
            pause_diagnostics_button.config(text=get_text("pause_test"))
    
    # 添加按钮
    run_diagnostics_button = ttk.Button(
        network_buttons_frame, 
        text=get_text("start_test"),
        command=run_network_diagnostics
    )
    run_diagnostics_button.pack(side=tk.LEFT, padx=5)
    
    pause_diagnostics_button = ttk.Button(
        network_buttons_frame, 
        text=get_text("pause_test"),
        command=pause_resume_network_diagnostics,
        state=tk.DISABLED
    )
    pause_diagnostics_button.pack(side=tk.LEFT, padx=5)
    
    cancel_diagnostics_button = ttk.Button(
        network_buttons_frame, 
        text=get_text("cancel_test"),
        command=cancel_network_diagnostics,
        state=tk.DISABLED
    )
    cancel_diagnostics_button.pack(side=tk.LEFT, padx=5)
    
    # 添加关闭按钮
    close_button = ttk.Button(main_frame, text=get_text("close"), command=debug_window.destroy)
    close_button.pack(pady=10)

    # 获取信息的函数
    def update_system_info():
        # 设置文本标签样式
        system_info_text.tag_configure("title", font=("微软雅黑", 11, "bold"), foreground=colors["title"])
        system_info_text.tag_configure("section", font=("微软雅黑", 10, "bold"), foreground=colors["section"])
        system_info_text.tag_configure("label", font=("微软雅黑", 9), foreground=colors["label"])
        system_info_text.tag_configure("value", font=("微软雅黑", 9, "bold"), foreground=colors["value"])
        system_info_text.tag_configure("dynamic_section", font=("微软雅黑", 10, "bold"), foreground=colors["dynamic_section"])
        
        # 系统信息
        system_info = []
        
        # 基本系统信息部分
        system_info.append(get_text("basic_system_info") + "\n")
        system_info.append(f"{get_text('os')}{platform.system()} {platform.version()}\n")
        system_info.append(f"{get_text('system_arch')}{platform.machine()}\n")
        system_info.append(f"{get_text('processor')}{platform.processor()}\n")
        system_info.append(f"{get_text('python_version')}{sys.version}\n")
        system_info.append(f"{get_text('tkinter_version')}{tk.TkVersion}\n")
        system_info.append(f"{get_text('cpu_cores')}{psutil.cpu_count(logical=False)} ({get_text('physical_cores')}), {psutil.cpu_count()} ({get_text('logical_cores')})\n")
        
        # 实时更新的信息
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 更新CPU使用率信息，根据使用率高低显示不同颜色
        system_info.append("\n" + get_text("realtime_system_info") + "\n")
        system_info.append(f"{get_text('cpu_usage')}{cpu_percent}%\n")
        
        # 内存信息
        memory_percent = memory.percent
        system_info.append(f"{get_text('memory')}{memory.used / (1024 * 1024 * 1024):.2f} GB / {memory.total / (1024 * 1024 * 1024):.2f} GB ({memory_percent}%)\n")
        
        # 应用程序自身的内存使用
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / (1024 * 1024)  # 转换为MB
        system_info.append(f"{get_text('pyquick_memory')}{process_memory:.2f} MB\n")
        
        # 磁盘信息
        system_info.append(f"{get_text('disk')}{disk.used / (1024 * 1024 * 1024):.2f} GB / {disk.total / (1024 * 1024 * 1024):.2f} GB ({disk.percent}%)\n")
        
        # 清空并更新文本框
        system_info_text.config(state=tk.NORMAL)
        system_info_text.delete(1.0, tk.END)
        
        # 插入标题
        system_info_text.insert(tk.END, get_text("basic_system_info") + "\n", "title")
        
        # 插入基本系统信息
        system_info_text.insert(tk.END, get_text("os"), "label")
        system_info_text.insert(tk.END, f"{platform.system()} {platform.version()}\n", "value")
        
        system_info_text.insert(tk.END, get_text("system_arch"), "label")
        system_info_text.insert(tk.END, f"{platform.machine()}\n", "value")
        
        system_info_text.insert(tk.END, get_text("processor"), "label")
        system_info_text.insert(tk.END, f"{platform.processor()}\n", "value")
        
        system_info_text.insert(tk.END, get_text("python_version"), "label")
        system_info_text.insert(tk.END, f"{sys.version.split()[0]}\n", "value")
        
        system_info_text.insert(tk.END, get_text("tkinter_version"), "label")
        system_info_text.insert(tk.END, f"{tk.TkVersion}\n", "value")
        
        system_info_text.insert(tk.END, get_text("cpu_cores"), "label")
        system_info_text.insert(tk.END, f"{psutil.cpu_count(logical=False)} ({get_text('physical_cores')}), {psutil.cpu_count()} ({get_text('logical_cores')})\n\n", "value")
        
        # 插入动态信息标题
        system_info_text.insert(tk.END, get_text("realtime_system_info") + "\n", "dynamic_section")
        
        # 插入CPU信息
        system_info_text.insert(tk.END, get_text("cpu_usage"), "label")
        cpu_text = f"{cpu_percent}%\n"
        system_info_text.insert(tk.END, cpu_text)
        
        # 为CPU使用率添加颜色标签
        if cpu_percent > 90:
            tag_name = "high_cpu"
            color = "red"
        elif cpu_percent > 70:
            tag_name = "medium_cpu"
            color = "orange"
        else:
            tag_name = "normal_cpu"
            color = "green"
        
        # 设置颜色标签
        start_line = int(system_info_text.index("end-2l").split(".")[0])
        cpu_label_len = len(get_text("cpu_usage"))
        system_info_text.tag_add(tag_name, f"{start_line}.{cpu_label_len}", f"{start_line}.end")
        system_info_text.tag_config(tag_name, foreground=color, font=("微软雅黑", 9, "bold"))
        
        # 插入内存信息
        system_info_text.insert(tk.END, get_text("memory"), "label")
        memory_text = f"{memory.used / (1024 * 1024 * 1024):.2f} GB / {memory.total / (1024 * 1024 * 1024):.2f} GB ({memory_percent}%)\n"
        system_info_text.insert(tk.END, memory_text)
        
        # 为内存使用率添加颜色标签
        if memory_percent > 90:
            tag_name = "high_mem"
            color = "red"
        elif memory_percent > 70:
            tag_name = "medium_mem"
            color = "orange"
        else:
            tag_name = "normal_mem"
            color = "green"
        
        # 设置颜色标签
        start_line = int(system_info_text.index("end-2l").split(".")[0])
        memory_label_len = len(get_text("memory"))
        system_info_text.tag_add(tag_name, f"{start_line}.{memory_label_len}", f"{start_line}.end")
        system_info_text.tag_config(tag_name, foreground=color, font=("微软雅黑", 9, "bold"))
        
        # 插入应用内存信息
        system_info_text.insert(tk.END, get_text("pyquick_memory"), "label")
        app_memory_text = f"{process_memory:.2f} MB\n"
        system_info_text.insert(tk.END, app_memory_text)
        
        # 为应用内存使用添加颜色
        if process_memory > 200:
            tag_name = "high_app_mem"
            color = "red"
        elif process_memory > 100:
            tag_name = "medium_app_mem"
            color = "orange"
        else:
            tag_name = "normal_app_mem"
            color = "green"
        
        # 设置颜色标签
        start_line = int(system_info_text.index("end-2l").split(".")[0])
        app_memory_label_len = len(get_text("pyquick_memory"))
        system_info_text.tag_add(tag_name, f"{start_line}.{app_memory_label_len}", f"{start_line}.end")
        system_info_text.tag_config(tag_name, foreground=color, font=("微软雅黑", 9, "bold"))
        
        # 插入磁盘信息
        system_info_text.insert(tk.END, get_text("disk"), "label")
        disk_text = f"{disk.used / (1024 * 1024 * 1024):.2f} GB / {disk.total / (1024 * 1024 * 1024):.2f} GB ({disk.percent}%)\n"
        system_info_text.insert(tk.END, disk_text)
        
        # 为磁盘使用率添加颜色
        if disk.percent > 90:
            tag_name = "high_disk"
            color = "red"
        elif disk.percent > 70:
            tag_name = "medium_disk"
            color = "orange"
        else:
            tag_name = "normal_disk"
            color = "green"
        
        # 设置颜色标签
        start_line = int(system_info_text.index("end-2l").split(".")[0])
        disk_label_len = len(get_text("disk"))
        system_info_text.tag_add(tag_name, f"{start_line}.{disk_label_len}", f"{start_line}.end")
        system_info_text.tag_config(tag_name, foreground=color, font=("微软雅黑", 9, "bold"))
        
        system_info_text.config(state=tk.DISABLED)
        
        # 每秒更新一次
        debug_window.after(1000, update_system_info)
    
    # 应用信息更新函数
    def update_app_info_display():
        # 设置文本标签样式
        app_info_text.tag_configure("title", font=("微软雅黑", 11, "bold"), foreground=colors["title"])
        app_info_text.tag_configure("section", font=("微软雅黑", 10, "bold"), foreground=colors["section"])
        app_info_text.tag_configure("label", font=("微软雅黑", 9), foreground=colors["label"])
        app_info_text.tag_configure("value", font=("微软雅黑", 9, "bold"), foreground=colors["value"])
        app_info_text.tag_configure("config_section", font=("微软雅黑", 10, "bold"), foreground=colors["config_section"])
        
        # 应用信息
        app_info_text.config(state=tk.NORMAL)
        app_info_text.delete(1.0, tk.END)
        
        # 插入标题
        app_info_text.insert(tk.END, get_text("app_info_title") + "\n", "title")
        
        # 基本应用信息
        app_info_text.insert(tk.END, get_text("app_name"), "label")
        app_info_text.insert(tk.END, f"{show_name()}\n", "value")
        
        app_info_text.insert(tk.END, get_text("app_version"), "label")
        app_info_text.insert(tk.END, f"{version_pyquick}\n", "value")
        
        app_info_text.insert(tk.END, get_text("config_path"), "label")
        app_info_text.insert(tk.END, f"{config_path}\n", "value")
        
        app_info_text.insert(tk.END, get_text("working_dir"), "label")
        app_info_text.insert(tk.END, f"{MY_PATH}\n\n", "value")
        
        # 配置文件信息
        app_info_text.insert(tk.END, get_text("config_file_info") + "\n", "config_section")
        
        # 检查并显示allowthread.txt内容
        thread_file = os.path.join(config_path, "allowthread.txt")
        if os.path.exists(thread_file):
            try:
                with open(thread_file, "r") as f:
                    thread_enabled = f.read().strip()
                app_info_text.insert(tk.END, get_text("multithread_enabled"), "label")
                app_info_text.insert(tk.END, f"{thread_enabled}\n", "value")
            except Exception as e:
                app_info_text.insert(tk.END, get_text("multithread_read_fail"), "label")
                app_info_text.insert(tk.END, f"{str(e)}\n", "value")
        else:
            app_info_text.insert(tk.END, get_text("multithread_config"), "label")
            app_info_text.insert(tk.END, get_text("config_not_found") + "\n", "value")
        
        # 检查并显示theme.txt内容
        theme_file = os.path.join(config_path, "theme.txt")
        if os.path.exists(theme_file):
            try:
                with open(theme_file, "r") as f:
                    theme = f.read().strip()
                app_info_text.insert(tk.END, get_text("theme_setting"), "label")
                app_info_text.insert(tk.END, f"{theme}\n", "value")
            except Exception as e:
                app_info_text.insert(tk.END, get_text("theme_read_fail"), "label")
                app_info_text.insert(tk.END, f"{str(e)}\n", "value")
        
        # Python镜像设置
        python_mirror_file = os.path.join(config_path, "pythonmirror.txt")
        if os.path.exists(python_mirror_file):
            try:
                with open(python_mirror_file, "r") as f:
                    python_mirror = f.read().strip()
                app_info_text.insert(tk.END, get_text("python_mirror"), "label")
                app_info_text.insert(tk.END, f"{python_mirror}\n", "value")
            except Exception as e:
                app_info_text.insert(tk.END, get_text("python_mirror_read_fail"), "label")
                app_info_text.insert(tk.END, f"{str(e)}\n", "value")
        
        # Pip镜像设置
        pip_mirror_file = os.path.join(config_path, "pipmirror.txt")
        if os.path.exists(pip_mirror_file):
            try:
                with open(pip_mirror_file, "r") as f:
                    pip_mirror = f.read().strip()
                app_info_text.insert(tk.END, get_text("pip_mirror_config"), "label")
                app_info_text.insert(tk.END, f"{pip_mirror}\n", "value")
            except Exception as e:
                app_info_text.insert(tk.END, get_text("pip_mirror_read_fail"), "label")
                app_info_text.insert(tk.END, f"{str(e)}\n", "value")
        
        # 语言设置
        language_file = os.path.join(config_path, "language.txt")
        if os.path.exists(language_file):
            try:
                with open(language_file, "r") as f:
                    language = f.read().strip()
                app_info_text.insert(tk.END, get_text("language_setting"), "label")
                app_info_text.insert(tk.END, f"{language}\n", "value")
            except Exception as e:
                app_info_text.insert(tk.END, get_text("language_read_fail"), "label")
                app_info_text.insert(tk.END, f"{str(e)}\n", "value")
        
        # 日志大小设置
        log_size_file = os.path.join(config_path, "log_size.txt")
        if os.path.exists(log_size_file):
            try:
                with open(log_size_file, "r") as f:
                    log_size = f.read().strip()
                app_info_text.insert(tk.END, get_text("log_size_limit"), "label")
                app_info_text.insert(tk.END, f"{log_size} MB\n", "value")
            except Exception as e:
                app_info_text.insert(tk.END, get_text("log_size_read_fail"), "label")
                app_info_text.insert(tk.END, f"{str(e)}\n", "value")
                
        app_info_text.config(state=tk.DISABLED)
    
    # 日志信息更新函数
    def update_log_info_display(log_level="all"):
        # 设置文本标签样式
        log_info_text.tag_configure("title", font=("微软雅黑", 11, "bold"), foreground=colors["title"])
        log_info_text.tag_configure("section", font=("微软雅黑", 10, "bold"), foreground=colors["section"])
        log_info_text.tag_configure("info_log", foreground=colors["info_log"])
        log_info_text.tag_configure("warning_log", foreground="#FF9900", font=("微软雅黑", 9, "bold"))
        log_info_text.tag_configure("error_log", foreground="#CC0000", font=("微软雅黑", 9, "bold"))
        log_info_text.tag_configure("debug_log", foreground="#009900" if not is_dark_theme else "#66ff66")
        
        # 日志信息
        log_info = []
        
        # 清空日志文本框
        log_info_text.config(state=tk.NORMAL)
        log_info_text.delete(1.0, tk.END)
        
        # 添加标题
        log_info_text.insert(tk.END, get_text("log_info") + "\n", "title")
        
        # 尝试读取最近的日志文件
        try:
            log_dir = os.path.join(config_path, "log")
            if os.path.exists(log_dir):
                log_files = glob.glob(os.path.join(log_dir, "*.log"))
                if log_files:
                    # 按修改时间排序，获取最新的日志文件
                    latest_log = max(log_files, key=os.path.getmtime)
                    log_info_text.insert(tk.END, get_text("latest_log_file"), "section")
                    log_info_text.insert(tk.END, f"{os.path.basename(latest_log)}\n\n")
                    
                    # 读取日志文件并应用过滤
                    with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                        
                        filtered_lines = []
                        for line in lines:
                            line_lower = line.lower()
                            if log_level == "error" and "error" in line_lower:
                                filtered_lines.append((line, "error_log"))
                            elif log_level == "warning" and ("error" in line_lower or "warn" in line_lower):
                                if "error" in line_lower:
                                    filtered_lines.append((line, "error_log"))
                                else:
                                    filtered_lines.append((line, "warning_log"))
                            elif log_level == "all":
                                if "error" in line_lower:
                                    filtered_lines.append((line, "error_log"))
                                elif "warn" in line_lower:
                                    filtered_lines.append((line, "warning_log"))
                                elif "debug" in line_lower:
                                    filtered_lines.append((line, "debug_log"))
                                else:
                                    filtered_lines.append((line, "info_log"))
                        
                        # 限制显示的日志行数
                        last_lines = filtered_lines[-100:] if len(filtered_lines) > 100 else filtered_lines
                        
                        if last_lines:
                            log_info_text.insert(tk.END, get_text("log_entries").format(log_level) + "\n", "section")
                            for line, tag in last_lines:
                                log_info_text.insert(tk.END, line, tag)
                        else:
                            log_info_text.insert(tk.END, get_text("no_log_entries").format(log_level) + "\n")
                else:
                    log_info_text.insert(tk.END, get_text("no_log_files") + "\n")
            else:
                log_info_text.insert(tk.END, get_text("no_log_dir") + "\n")
        except Exception as e:
            log_info_text.insert(tk.END, get_text("log_read_error").format(e) + "\n", "error_log")
        
        log_info_text.config(state=tk.DISABLED)

    # 初始化各个信息显示
    update_system_info()
    update_app_info_display()
    update_log_info_display()
    
    # 定期执行垃圾回收
    def perform_gc():
        gc.collect()
        debug_window.after(30000, perform_gc)  # 每30秒执行一次垃圾回收
    
    # 启动垃圾回收定时器
    perform_gc()
    
    # 窗口关闭时执行清理
    def on_debug_window_close():
        gc.collect()  # 执行一次垃圾回收
        debug_window.destroy()
    
    # 绑定窗口关闭事件
    debug_window.protocol("WM_DELETE_WINDOW", on_debug_window_close)

# 获取当前用户自定义的Python镜像源列表
def get_custom_python_mirrors():
    """获取用户自定义的Python镜像源列表"""
    try:
        custom_mirrors_file = os.path.join(config_path, "custom_python_mirrors.txt")
        if os.path.exists(custom_mirrors_file):
            with open(custom_mirrors_file, 'r') as f:
                mirrors = [line.strip() for line in f.readlines() if line.strip()]
                return mirrors
        return []
    except Exception as e:
        logger.error(f"读取自定义Python镜像源失败: {e}")
        return []

# 获取当前用户自定义的Pip镜像源列表
def get_custom_pip_mirrors():
    """获取用户自定义的Pip镜像源列表"""
    try:
        custom_mirrors_file = os.path.join(config_path, "custom_pip_mirrors.txt")
        if os.path.exists(custom_mirrors_file):
            with open(custom_mirrors_file, 'r') as f:
                mirrors = [line.strip() for line in f.readlines() if line.strip()]
                return mirrors
        return []
    except Exception as e:
        logger.error(f"读取自定义Pip镜像源失败: {e}")
        return []

# 保存自定义Python镜像源列表
def save_custom_python_mirror(mirror_url):
    """保存自定义Python镜像源"""
    if not mirror_url.strip():
        return False
    
    try:
        custom_mirrors = get_custom_python_mirrors()
        if mirror_url not in custom_mirrors:
            custom_mirrors.append(mirror_url)
            
            custom_mirrors_file = os.path.join(config_path, "custom_python_mirrors.txt")
            with open(custom_mirrors_file, 'w') as f:
                for mirror in custom_mirrors:
                    f.write(f"{mirror}\n")
            return True
        return False  # 已存在
    except Exception as e:
        logger.error(f"保存自定义Python镜像源失败: {e}")
        return False

# 保存自定义Pip镜像源列表
def save_custom_pip_mirror(mirror_url):
    """保存自定义Pip镜像源"""
    if not mirror_url.strip():
        return False
    
    try:
        custom_mirrors = get_custom_pip_mirrors()
        if mirror_url not in custom_mirrors:
            custom_mirrors.append(mirror_url)
            
            custom_mirrors_file = os.path.join(config_path, "custom_pip_mirrors.txt")
            with open(custom_mirrors_file, 'w') as f:
                for mirror in custom_mirrors:
                    f.write(f"{mirror}\n")
            return True
        return False  # 已存在
    except Exception as e:
        logger.error(f"保存自定义Pip镜像源失败: {e}")
        return False

# 测试镜像延迟
def test_mirror_delay(mirror_url, mirror_type="python"):
    """测试镜像延迟和可用性
    
    参数:
        mirror_url (str): 要测试的镜像URL
        mirror_type (str): 镜像类型，'python'或'pip'
        
    返回:
        dict: 包含测试结果的字典，包括延迟时间、连接是否成功、下载测试是否成功
    """
    result = {"delay": -1, "connection_success": False, "download_success": False}
    
    # 1. 测试基本连接和延迟
    try:
        start_time = time.time()
        response = requests.get(mirror_url, timeout=5, verify=False)
        if response.status_code == 200:
            result["delay"] = time.time() - start_time
            result["connection_success"] = True
        else:
            logger.warning(get_text("mirror_connection_test_failed").format(response.status_code))
            return result
    except requests.RequestException as e:
        logger.warning(get_text("mirror_connection_test_exception").format(e))
        return result
    
    # 2. 测试是否能下载包
    try:
        if mirror_type == "python":
            # 尝试获取Python版本页面，检查是否存在关键文件
            version_test_url = f"{mirror_url}/3.10.0"
            test_response = requests.get(version_test_url, timeout=5, verify=False)
            # 检查页面是否包含常见安装文件模式
            result["download_success"] = (test_response.status_code == 200 and 
                                         (b"python-3.10.0" in test_response.content or
                                          b"Python-3.10.0" in test_response.content))
        else:  # pip
            # 尝试获取某个常见包的信息，确认Pip镜像可用
            test_url = f"{mirror_url}/pip"
            test_response = requests.get(test_url, timeout=5, verify=False)
            result["download_success"] = (test_response.status_code == 200)
    except requests.RequestException as e:
        logger.warning(get_text("mirror_download_test_exception").format(e))
        # 连接成功但下载测试失败
        
    return result

# 显示镜像测试窗口
def show_mirror_test_window(mirror_type="python"):
    """显示镜像测试窗口
    
    参数:
        mirror_type (str): 镜像类型，'python'或'pip'
    """
    test_window = tk.Toplevel(root)
    test_window.title(get_text("test_mirror_delay").format("Python" if mirror_type == "python" else "Pip"))
    test_window.resizable(True, True)  # 允许调整窗口大小
    test_window.transient(root)
    test_window.grab_set()
    
    # 创建主框架
    main_frame = ttk.Frame(test_window, padding=20)
    main_frame.pack(expand=True, fill="both")
    
    # 添加标题
    title_text = get_text("test_mirror_delay").format("Python" if mirror_type == "python" else "Pip")
    ttk.Label(main_frame, text=title_text, font=("微软雅黑", 12, "bold")).pack(pady=(0, 10))
    
    # 获取镜像列表
    if mirror_type == "python":
        default_mirror = "https://www.python.org/ftp/python"
        mirrors = [mirror for mirror in PYTHON_MIRRORS if mirror != default_mirror]
        custom_mirrors = get_custom_python_mirrors()
    else:
        default_mirror = PIP_MIRRORS[0]
        mirrors = PIP_MIRRORS[1:]  # 排除默认源
        custom_mirrors = get_custom_pip_mirrors()
    
    all_mirrors = [default_mirror] + mirrors + custom_mirrors
    
    # 创建结果框架
    result_frame = ttk.Frame(main_frame)
    result_frame.pack(fill="both", expand=True, pady=10)
    
    # 创建表格标题
    ttk.Label(result_frame, text=get_text("mirror_address"), width=40, anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ttk.Label(result_frame, text=get_text("delay"), width=10, anchor="center").grid(row=0, column=1, sticky="w", padx=5, pady=5)
    ttk.Label(result_frame, text=get_text("status"), width=10, anchor="center").grid(row=0, column=2, sticky="w", padx=5, pady=5)
    
    ttk.Separator(result_frame, orient="horizontal").grid(row=1, column=0, columnspan=3, sticky="ew", pady=5)
    
    # 创建进度条
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100)
    progress_bar.pack(fill="x", pady=10)
    
    status_var = tk.StringVar(value=get_text("ready_to_test"))
    status_label = ttk.Label(main_frame, textvariable=status_var)
    status_label.pack(pady=5)
    
    
    # 创建按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)
    
    # 添加自定义镜像框架
    custom_frame = ttk.LabelFrame(main_frame, text=get_text("add_custom_mirror"))
    custom_frame.pack(fill="x", pady=10)
    
    ttk.Label(custom_frame, text=get_text("mirror_url")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    custom_entry = ttk.Entry(custom_frame, width=40)
    custom_entry.grid(row=0, column=1, padx=5, pady=5)
    
    # 添加自定义镜像
    def add_custom_mirror():
        url = custom_entry.get().strip()
        if not url:
            messagebox.showerror(get_text("error"), get_text("enter_valid_mirror"))
            return
        
        # 验证URL格式
        if not url.startswith(("http://", "https://")):
            messagebox.showerror(get_text("error"), get_text("url_format_error"))
            return
        
        # 保存自定义镜像
        if mirror_type == "python":
            success = save_custom_python_mirror(url)
        else:
            success = save_custom_pip_mirror(url)
        
        if success:
            messagebox.showinfo(get_text("success"), get_text("custom_mirror_added"))
            custom_entry.delete(0, tk.END)
            # 关闭当前窗口并重新打开测试窗口，以刷新镜像列表
            test_window.destroy()
            show_mirror_test_window(mirror_type)
        else:
            messagebox.showinfo(get_text("info"), get_text("mirror_exists"))
    
    add_button = ttk.Button(custom_frame, text=get_text("add"), command=add_custom_mirror)
    add_button.grid(row=0, column=2, padx=5, pady=5)
    
    # 设置最佳镜像
    def set_best_mirror(best_mirror):
        if best_mirror:
            if mirror_type == "python":
                with open(os.path.join(config_path, "pythonmirror.txt"), "w") as f:
                    f.write(best_mirror)
                settings["python_mirror"] = best_mirror
            else:
                with open(os.path.join(config_path, "pipmirror.txt"), "w") as f:
                    f.write(best_mirror)
                settings["pip_mirror"] = best_mirror
            
            messagebox.showinfo(get_text("success"), get_text("set_mirror_success").format(mirror_type.upper(), best_mirror))
            test_window.destroy()
    
    # 执行测试
    def run_test():
        # 禁用添加和测试按钮
        add_button.config(state="disabled")
        test_button.config(state="disabled")
        set_button.config(state="disabled")
        
        # 清理之前的结果
        for widget in result_frame.winfo_children()[3:]:  # 跳过标题和分隔线
            widget.destroy()
        
        results = []
        progress_step = 100.0 / len(all_mirrors)
        
        def test_thread():
            best_mirror = None
            best_delay = float('inf')
            
            for i, mirror in enumerate(all_mirrors):
                current_progress = progress_step * i
                test_window.after(0, lambda p=current_progress, m=mirror: 
                                 [progress_var.set(p), 
                                  status_var.set(get_text("testing").format(m))])
                
                result = test_mirror_delay(mirror, mirror_type)
                
                # 如果连接成功且下载测试成功，且延迟比当前最佳镜像短，更新最佳镜像
                if (result["connection_success"] and result["download_success"] and 
                    result["delay"] > 0 and result["delay"] < best_delay):
                    best_delay = result["delay"]
                    best_mirror = mirror
                
                results.append((mirror, result))
                
                # 更新UI (必须从主线程调用)
                test_window.after(0, lambda m=mirror, r=result, row=i+2: update_result(m, r, row))
            
            # 完成所有测试
            test_window.after(0, lambda: [
                progress_var.set(100),
                status_var.set(get_text("test_completed")),
                add_button.config(state="normal"),
                test_button.config(state="normal"),
                set_button.config(state="normal", command=lambda b=best_mirror: set_best_mirror(b))
            ])
        
        # 更新结果表格
        def update_result(mirror, result, row):
            ttk.Label(result_frame, text=mirror, width=40, anchor="w").grid(
                row=row, column=0, sticky="w", padx=5, pady=2)
            
            # 解析测试结果
            delay = result["delay"]
            connection_success = result["connection_success"]
            download_success = result["download_success"]
            
            # 根据测试结果设置显示内容和颜色
            if connection_success and download_success:
                # 连接成功且可下载
                delay_str = f"{delay:.2f}{get_text('second')}"
                status_str = get_text("normal")
                color = "#009900"  # 绿色
            elif connection_success and not download_success:
                # 连接成功但下载测试失败
                delay_str = f"{delay:.2f}{get_text('second')}"
                status_str = get_text("connect_ok_but_download_failed")
                color = "#FF9900"  # 橙色
                
                # 询问用户是否删除不可下载的镜像
                if mirror in get_custom_python_mirrors() or mirror in get_custom_pip_mirrors():
                    if messagebox.askyesno(get_text("warning"), 
                                        get_text("mirror_connection_success_but_download_failed").format(mirror),
                                        parent=test_window):
                        if mirror_type == "python":
                            custom_mirrors = get_custom_python_mirrors()
                            if mirror in custom_mirrors:
                                custom_mirrors.remove(mirror)
                                custom_mirrors_file = os.path.join(config_path, "custom_python_mirrors.txt")
                                with open(custom_mirrors_file, 'w') as f:
                                    for m in custom_mirrors:
                                        f.write(f"{m}\n")
                                messagebox.showinfo(get_text("success"), get_text("mirror_deleted").format(mirror), parent=test_window)
                        else:
                            custom_mirrors = get_custom_pip_mirrors()
                            if mirror in custom_mirrors:
                                custom_mirrors.remove(mirror)
                                custom_mirrors_file = os.path.join(config_path, "custom_pip_mirrors.txt")
                                with open(custom_mirrors_file, 'w') as f:
                                    for m in custom_mirrors:
                                        f.write(f"{m}\n")
                                messagebox.showinfo(get_text("success"), get_text("mirror_deleted").format(mirror), parent=test_window)
            else:
                # 连接失败
                delay_str = get_text("timeout")
                status_str = get_text("failed")
                color = "#CC0000"  # 红色
                
                # 询问用户是否删除不可用的镜像
                if mirror in get_custom_python_mirrors() or mirror in get_custom_pip_mirrors():
                    if messagebox.askyesno(get_text("warning"), 
                                        get_text("mirror_connection_failed").format(mirror),
                                        parent=test_window):
                        if mirror_type == "python":
                            custom_mirrors = get_custom_python_mirrors()
                            if mirror in custom_mirrors:
                                custom_mirrors.remove(mirror)
                                custom_mirrors_file = os.path.join(config_path, "custom_python_mirrors.txt")
                                with open(custom_mirrors_file, 'w') as f:
                                    for m in custom_mirrors:
                                        f.write(f"{m}\n")
                                messagebox.showinfo(get_text("success"), get_text("mirror_deleted").format(mirror), parent=test_window)
                        else:
                            custom_mirrors = get_custom_pip_mirrors()
                            if mirror in custom_mirrors:
                                custom_mirrors.remove(mirror)
                                custom_mirrors_file = os.path.join(config_path, "custom_pip_mirrors.txt")
                                with open(custom_mirrors_file, 'w') as f:
                                    for m in custom_mirrors:
                                        f.write(f"{m}\n")
                                messagebox.showinfo(get_text("success"), get_text("mirror_deleted").format(mirror), parent=test_window)
            
            # 更新UI显示
            delay_label = ttk.Label(result_frame, text=delay_str, width=10, anchor="center")
            delay_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
            
            status_label = ttk.Label(result_frame, text=status_str, width=10, anchor="center", foreground=color)
            status_label.grid(row=row, column=2, sticky="w", padx=5, pady=2)
        
        # 启动测试线程
        threading.Thread(target=test_thread, daemon=True).start()
    
    # 底部按钮
    test_button = ttk.Button(button_frame, text=get_text("start_test"), command=run_test)
    test_button.pack(side="left", padx=5)
    
    set_button = ttk.Button(button_frame, text=get_text("set_best_mirror"), state="disabled")
    set_button.pack(side="left", padx=5)
    
    ttk.Button(button_frame, text=get_text("close"), command=test_window.destroy).pack(side="right", padx=5)
    
    # 设置居中
    test_window.update_idletasks()
    width = test_window.winfo_width()
    height = test_window.winfo_height()
    x = (test_window.winfo_screenwidth() // 2) - (width // 2)
    y = (test_window.winfo_screenheight() // 2) - (height // 2)
    test_window.geometry('+{}+{}'.format(x, y))  # 只设置窗口位置，不限制大小

# 添加一个新函数在main代码部分之前
def update_interface_language():
    """更新界面上所有元素的语言"""
    global version_label, destination_label, thread_label, download_label
    global version_reload_button, select_button, download_button
    global cancel_button, pause_button, note, root
    global pip_upgrade_button, pip_retry_button, package_label
    global install_button, uninstall_button, upgrade_button
    global menubar, help_menu, settings_menu, status_label, package_status_label, download_frame, pip_frame
    
    try:
        # 更新窗口标题
        root.title(show_name())
        
        # Notebook标签不能直接更新，需要移除再添加
        # 保存当前选中的标签索引
        current_tab = note.index("current")
        
        # 保存所有当前标签页
        tabs = note.tabs()
        if tabs:
            # 移除所有标签页
            for tab in tabs:
                note.forget(0)  # 总是移除第一个
                
            # 重新添加标签页，使用新的翻译文本
            note.add(download_frame, text=get_text("python_download"))
            note.add(pip_frame, text=get_text("pip_management"))
            
            # 恢复之前选中的标签
            if current_tab < len(tabs):
                note.select(current_tab)
        
        # 更新菜单文本
        menubar.entryconfig(0, label=get_text("settings_menu"))
        menubar.entryconfig(1, label=get_text("help_menu"))
        
        help_menu.entryconfig(0, label=get_text("about"))
        help_menu.entryconfig(2, label=get_text("debug_info"))
        
        settings_menu.entryconfig(0, label=get_text("settings"))
        
        # 更新Python下载标签
        version_label.config(text=get_text("select_python_version"))
        destination_label.config(text=get_text("select_destination"))
        thread_label.config(text=get_text("select_thread_number"))
        download_label.config(text=get_text("choose_download_file"))
        
        # 更新按钮文本
        version_reload_button.config(text=get_text("reload"))
        select_button.config(text=get_text("select_path"))
        download_button.config(text=get_text("download"))
        cancel_button.config(text=get_text("cancel_download"))
        pause_button.config(text=get_text("pause_download"))
        
        # 更新Pip管理界面
        pip_upgrade_button.config(text=get_text("pip_version"))
        pip_retry_button.config(text=get_text("retry"))
        package_label.config(text=get_text("enter_package_name"))
        install_button.config(text=get_text("install_package"))
        uninstall_button.config(text=get_text("uninstall_package"))
        upgrade_button.config(text=get_text("upgrade_package"))
        
        # 更新状态标签文本，如果当前显示的是语言字典中的文本
        def update_label_text(label):
            if not label:
                return
                
            current_text = label.cget("text")
            if current_text:
                # 检查当前文本是否能在当前语言中找到
                for lang in texts:
                    for key, value in texts[lang].items():
                        if current_text == value:
                            # 找到匹配项，更新为新语言的文本
                            label.config(text=get_text(key))
                            break
        
        # 更新两个状态标签
        update_label_text(status_label)
        update_label_text(package_status_label)
        
        logger.info(f"界面语言已更新为: {current_language}")
    except Exception as e:
        logger.error(f"更新界面语言失败: {e}")
        messagebox.showerror(get_text("error"), get_text("update_language_failed").format(str(e)))

if __name__ == "__main__":
    if datetime.datetime.now() >= datetime.datetime(2025, 8, 13):
        subprocess.Popen([sys.executable,show(code="0x0000001A", mode="err", info="Pyquick is expired.")],creationflags=subprocess.CREATE_NO_WINDOW,shell=True)
        # 使用线程保持主程序运行
        exit(1)
    if build<9600:
        subprocess.Popen([show(code="0x0000002A", mode="err", info="Uxexpected Happened.")],creationflags=subprocess.CREATE_NO_WINDOW,shell=True)
        exit(1)
    elif build>=9600 and build<=18363:
        threading.Thread(target=lambda: logger.warning(get_text("app_warning")), daemon=True).start()
    elif build<22000 and build>18363:
        threading.Thread(target=lambda: logger.info(get_text("app_info_log")), daemon=True).start()
    root = tk.Tk()

    root.title(show_name())
    #root.attributes('-topmost', True)
    root.resizable(False, False)
    icon_path = os.path.join(MY_PATH, 'pyquick.ico')
    
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    menubar = tk.Menu(root)
    root.config(menu=menubar)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    # 添加 Help 菜单项
    help_menu = tk.Menu(menubar, tearoff=0)
    settings_menu = tk.Menu(menubar, tearoff=0)
    
    menubar.add_cascade(label=get_text("settings_menu"), menu=settings_menu)
    menubar.add_cascade(label=get_text("help_menu"), menu=help_menu)

    help_menu.add_command(label=get_text("about"), command=show_about)
    help_menu.add_separator()
    help_menu.add_command(label=get_text("debug_info"), command=show_debug_info)
    
    # 同时添加两个设置选项，一个复杂一个简单
    settings_menu.add_command(label=get_text("settings"), command=settings1)
    

    note = ttk.Notebook(root)
    download_frame = ttk.Frame(note, padding="10")
    pip_frame = ttk.Frame(note, padding="10")
    note.add(download_frame, text=get_text("python_download"))
    note.add(pip_frame, text=get_text("pip_management"))
    note.grid(padx=10, pady=10, row=0, column=0)

    # Python Download Frame
    version_label = ttk.Label(download_frame, text=get_text("select_python_version"))
    version_label.grid(row=0, column=0, pady=10,padx=10, sticky="e")

    



    version_combobox = ttk.Combobox(download_frame, values=[''], state="readonly")
    version_combobox.grid(row=0, column=1, pady=10, padx=10, sticky="w")
    version_combobox.current(0)

    version_reload_button = ttk.Button(download_frame, text=get_text("reload"), command=python_version_reload)
    version_reload_button.grid(row=0, column=2, pady=10, padx=10, sticky="w")


    destination_label = ttk.Label(download_frame, text=get_text("select_destination"))
    destination_label.grid(row=1, column=0, pady=10,padx=10, sticky="e")


    destination_entry = ttk.Entry(download_frame, width=60)
    destination_entry.grid(row=1, column=1, pady=10, padx=10, sticky="w")


    select_button = ttk.Button(download_frame, text=get_text("select_path"), command=select_destination)
    select_button.grid(row=1, column=2, pady=10, padx=10, sticky="w")

    thread_label = ttk.Label(download_frame, text=get_text("select_thread_number"))
    thread_label.grid(row=2, column=0, pady=10,padx=10, sticky="e")

    thread_combobox = ttk.Combobox(download_frame, values=[str(i) for i in range(1, 129)], state="readonly")
    thread_combobox.grid(row=2, column=1, pady=10, padx=10, sticky="w")
    thread_combobox.current(9)  # Default to 32 threads

    download_label= ttk.Label(download_frame, text=get_text("choose_download_file"))
    download_label.grid(row=3, column=0, pady=10,padx=10, sticky="e")

    
    download_file_combobox = ttk.Combobox(download_frame, values=[''], state="readonly",width=40)
    download_file_combobox.grid(row=3, column=1, pady=10, padx=10, sticky="w")
    

    download_button = ttk.Button(download_frame, text=get_text("download"), command=download_selected_version)
    download_button.grid(row=4, column=0, columnspan=3, pady=10, padx=10)

    
    # 取消下载按钮
    cancel_button = ttk.Button(download_frame, text=get_text("cancel_download"), command=cancel_download)
    cancel_button.grid_forget()
    
    # 暂停/恢复下载按钮
    pause_button = ttk.Button(download_frame, text=get_text("pause_download"), command=pause_resume_download)
    pause_button.grid_forget()

    # 下载进度
    progress_bar = ttk.Progressbar(download_frame, orient='horizontal', length=300, mode='determinate')
    progress_bar.grid(row=7, column=0, columnspan=3, pady=10, padx=10)


    # 下载状态
    status_label = ttk.Label(download_frame, text="", padding="5")
    status_label.grid(row=8, column=0, columnspan=3, pady=10, padx=10)







    # pip Management Frame
    pip_upgrade_button = ttk.Button(pip_frame, text=get_text("pip_version"), command=lambda: upgrade_pip(pip_upgrade_button, package_entry, install_button, uninstall_button, upgrade_button, pip_progress_bar, package_status_label, config_path, root))
    pip_upgrade_button.grid(row=0, column=0, columnspan=3, pady=10, padx=10)

    # 创建重试按钮但默认不显示
    pip_retry_button = ttk.Button(pip_frame, text=get_text("retry"), command=retry_pip_ui)
    # pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
    # 默认不显示重试按钮，只有在需要时才显示



    package_label = ttk.Label(pip_frame, text=get_text("enter_package_name"))
    package_label.grid(row=2, column=0, pady=10, padx=10, sticky="e")


    package_entry = ttk.Entry(pip_frame, width=80)
    package_entry.grid(row=2, column=1, pady=10, padx=10, sticky="w")


    install_button = ttk.Button(pip_frame, text=get_text("install_package"), command=install_package_ui)
    install_button.grid(row=3, column=0, columnspan=3, pady=10, padx=10)


    uninstall_button = ttk.Button(pip_frame, text=get_text("uninstall_package"), command=uninstall_package_ui)
    uninstall_button.grid(row=4, column=0, columnspan=3, pady=10, padx=10)

    upgrade_button=ttk.Button(pip_frame,text=get_text("upgrade_package"),command=upgrade_package_ui)
    upgrade_button.grid_forget()

    pip_progress_bar=ttk.Progressbar(pip_frame, orient='horizontal', length=300, mode='indeterminate')
    pip_progress_bar.grid_forget()
    pip_progress_bar['value']=0


    package_status_label = ttk.Label(pip_frame, text="", padding="5")
    package_status_label.grid(row=7, column=0, columnspan=3, pady=10, padx=10)
    
    

    
    if build>22000:
        try:
            # 全局初始化sv_ttk
            sv_ttk.set_theme("light")  # 默认先设置为light主题
            # 然后再调用load_theme来加载用户设置
            theme = load_theme()
            logger.info(f"初始化主题: {theme}")
        except Exception as e:
            logger.error(f"初始化主题失败: {e}")
            
    # 确保版本加载和UI部分其他线程在同一块
    # 确保自动加载版本列表和文件列表
    if os.path.exists(os.path.join(config_path, "version.txt")):
        read_python_version()  # 直接同步调用
    else:
        # 如果版本文件不存在，进行在线加载
        threading.Thread(target=python_version_reload, daemon=True).start()
    
    threading.Thread(target=show_name, daemon=True).start()
    threading.Thread(target=check_python_installation, daemon=True).start()
    threading.Thread(target=lambda: check_package_upgradeable("", config_path), daemon=True).start()
    threading.Thread(target=allow_thread, daemon=True).start()
    # 直接在主线程中调用show_pip_version，而不是在单独的线程中
    root.after(100, show_pip_version)  # 使用延迟确保GUI已完全初始化
    threading.Thread(target=save_path, daemon=True).start()
    threading.Thread(target=get_pip_mirror, daemon=True).start()

    # 加载语言设置并更新UI
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
    
    # 添加版本选择事件处理
    def on_version_selected(event):
        """版本选择处理函数，加载对应版本的文件列表"""
        selected_version = version_combobox.get()
        if selected_version:
            # 清空文件列表并禁用下拉框
            download_file_combobox.set("")
            download_file_combobox.config(values=[""], state="disabled")
            
            # 显示进度条（不定时模式）
            progress_bar.config(mode="indeterminate")
            progress_bar.start(15)  # 设置更快的速度
            
            # 更新状态标签
            status_label.config(text=get_text("loading_files"))
            
            # 使用线程加载文件列表，避免UI冻结
            def load_files_thread():
                try:
                    logger.info(f"加载版本 {selected_version} 的文件列表")
                    python_mirror = read_python_mirror()
                    if python_mirror and python_mirror != "https://www.python.org/ftp/python":
                        url = f"{python_mirror}/{selected_version}/"
                    else:
                        # 使用默认镜像
                        url = f"https://www.python.org/ftp/python/{selected_version}/"
                    
                    file_list = python_dowload_url_reload(url)
                    
                    # 更新UI (在主线程中)
                    root.after(0, lambda: update_file_list(file_list))
                except Exception as e:
                    logger.error(f"加载文件列表失败: {e}")
                    # 更新UI显示错误
                    root.after(0, lambda: progress_bar.stop())
                    root.after(0, lambda: progress_bar.config(mode="determinate", value=0))
                    root.after(0, lambda: status_label.config(text=get_text("loading_file_failed").format(e)))
                    root.after(0, lambda: download_file_combobox.config(state="readonly"))
                    root.after(5000, lambda: status_label.config(text=""))
            
            # 启动线程
            threading.Thread(target=load_files_thread, daemon=True).start()
    
    def update_file_list(file_list):
        """更新文件列表下拉框"""
        # 停止进度条
        progress_bar.stop()
        progress_bar.config(mode="determinate", value=0)
        
        if file_list and len(file_list) > 0:
            # 过滤掉含有"macos"的文件
            filtered_list = [f for f in file_list if "macos" not in f.lower()]
            
            if filtered_list:
                download_file_combobox.config(values=filtered_list)
                download_file_combobox.set("")  # 清空当前选择
                status_label.config(text=get_text("found_files").format(len(filtered_list)))
                logger.info(f"加载了 {len(filtered_list)} 个可下载文件")
            else:
                download_file_combobox.config(values=[get_text("no_files_found")])
                status_label.config(text=get_text("no_files_found"))
                logger.warning("过滤后没有可用的安装文件")
        else:
            download_file_combobox.config(values=[get_text("no_files_found")])
            status_label.config(text=get_text("no_files_found"))
            logger.warning("未找到任何文件")
        
        # 启用下拉框
        download_file_combobox.config(state="readonly")
        
        # 5秒后清除状态
        root.after(5000, lambda: status_label.config(text=""))
    
    # 绑定版本选择事件
    version_combobox.bind("<<ComboboxSelected>>", on_version_selected)

    root.mainloop()
