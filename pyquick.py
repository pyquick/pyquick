#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyQuick主程序
Python下载器和包管理工具
"""

import os
import re
import sys
import time
import json
import platform
import gc
import queue
import logging
import traceback
import threading
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, Future, as_completed

# 导入tkinter相关模块
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# 添加全局UI组件变量
version_combobox = None
version_reload = None
choose_file_combobox = None
destination_entry = None
threads_entry = None
download_pb = None
status_label = None
download_button = None
pause_button = None
resume_button = None
cancel_button = None
size_label = None
speed_label = None
download_manager = None

from xml.sax.handler import property_xml_string
from cryptography.fernet import Fernet
import requests
import proxy
from get_system_build import block_features
import darkdetect
from save_path import create_folder, sav_path
import sv_ttk
import datetime
from bs4 import BeautifulSoup
import importlib

# 导入内部模块
try:
    from log import app_logger, error_logger, configure_global_loggers
except ImportError:
    # 创建默认的logger
    app_logger = logging.getLogger("app")
    error_logger = logging.getLogger("error")
    
    def configure_global_loggers(**kwargs):
        pass

# 禁用警告
requests.packages.urllib3.disable_warnings()

# 导入外部模块
from get_system_build import block_features
import darkdetect
import sv_ttk
import datetime
from bs4 import BeautifulSoup
import importlib
import json
import traceback
import multiprocessing
from multiprocessing import Process, Queue, Manager, Pool, Event
from functools import partial
from crashes import *
version="1965"
myfilenumber="7079"

# 全局调试模式标志
DEBUG_MODE = False  # 默认为非调试模式

try:
    collect.delete_crashes_folder_all(version)
except Exception as e:
    pass
open.repair_path(version)#修复缓存路径
config_path=create_folder.get_path("pyquick",version)
cancel_event = threading.Event()
create_folder.folder_create("pyquick",version)

def setup_error_logger():
    """设置错误日志记录器"""
    try:
        # 创建一个专门用于记录错误的日志记录器
        error_logger = logging.getLogger("error")
        error_logger.setLevel(logging.ERROR)
        
        # 创建一个处理程序，将错误日志写入文件
        log_dir = os.path.join(os.path.expanduser("~"), ".pyquick", "log")
        os.makedirs(log_dir, exist_ok=True)
        
        error_log_file = os.path.join(log_dir, "error.log")
        file_handler = logging.FileHandler(error_log_file, encoding="utf-8")
        
        # 设置日志格式
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        
        # 将处理程序添加到记录器
        error_logger.addHandler(file_handler)
        
        # 设置一个控制台处理程序，用于在开发过程中调试
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        error_logger.addHandler(console_handler)
        
        return error_logger
    except Exception as e:
        # 如果设置错误日志记录器时出错，回退到标准日志
        print(f"Error setting up error logger: {e}")
        fallback_logger = logging.getLogger("error_fallback")
        fallback_logger.setLevel(logging.ERROR)
        fallback_logger.addHandler(logging.StreamHandler())
        return fallback_logger

# 解析命令行参数获取调试模式标志
def parse_args():
    """解析命令行参数"""
    global DEBUG_MODE, config_path
    
    import argparse
    parser = argparse.ArgumentParser(description='PyQuick Python下载器')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    parser.add_argument('--config', type=str, help='配置文件目录路径')
    parser.add_argument('--version', action='version', version=f'PyQuick v{version}')
    args = parser.parse_args()
    
    # 设置配置目录
    if args.config:
        config_path = args.config
    
    # 临时设置调试模式（命令行参数优先）
    if args.debug:
        DEBUG_MODE = True
        print("已通过命令行参数启用调试模式")
        
    return args

# 从settings.json读取调试模式设置
def update_debug_mode_from_settings():
    """从settings.json读取调试模式设置"""
    global DEBUG_MODE
    try:
        # 导入settings模块
        from settings.settings_manager import get_manager
        settings_manager = get_manager()
        
        if settings_manager:
            # 如果没有通过命令行启用调试模式，则从设置读取
            if not DEBUG_MODE:
                # 从设置中读取调试模式状态
                debug_from_settings = settings_manager.get("advanced.debug_mode", False)
                DEBUG_MODE = debug_from_settings
                print(f"从设置读取调试模式状态: {DEBUG_MODE}")
        else:
            print("未能获取settings_manager实例，使用默认调试模式设置")
    except Exception as e:
        print(f"读取调试模式设置时出错: {e}")
        # 错误情况下，保持当前设置

# 解析命令行参数
parse_args()

# 导入新的日志系统
try:
    from log import app_logger, download_logger, error_logger, configure_global_loggers
    from log import file_manager, json_manager, configure_file_managers
    
    # 设置日志目录
    log_dir = os.path.join(config_path, "log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志系统，根据调试模式设置日志级别
    configure_global_loggers(
        log_level="debug" if DEBUG_MODE else "info", 
        enable_console=True, 
        enable_file=True, 
        log_dir=log_dir,
        debug_mode=DEBUG_MODE  # 传递调试模式标志
    )
    
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
    global version_combobox, version_reload
    
    # 检查组件是否初始化
    if not all([version_combobox, version_reload]):
        app_logger.error("版本选择组件未初始化")
        return
        
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
        # 安全获取version_combobox的值
        if 'version_combobox' not in globals() or not version_combobox or not hasattr(version_combobox, 'winfo_exists') or not version_combobox.winfo_exists():
            error_logger.warning("获取版本值失败: version_combobox不存在或已销毁")
            return []
            
        # 线程安全地获取版本号
        if threading.current_thread() != threading.main_thread():
            value_queue = queue.Queue()
            def get_version_value():
                try:
                    value_queue.put(version_combobox.get())
                except Exception as e:
                    value_queue.put("")
                    error_logger.error(f"获取版本号失败: {e}")
            if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                root.after(0, get_version_value)
                ver = value_queue.get(timeout=1)
                if not ver:
                    error_logger.warning("获取版本号失败: 获取到空值")
                    return []
            else:
                error_logger.warning("获取版本号失败: root不存在或已销毁")
                return []
        else:
            ver = version_combobox.get()
        
        # 确认版本号有效
        if not ver or not isinstance(ver, str):
            error_logger.warning(f"无效的版本号: {ver}")
            return []
            
        # 以下是正常的文件获取逻辑
        response = requests.get(f"https://www.python.org/ftp/python/{ver}/", timeout=10)
        response.raise_for_status()
        
        bs = BeautifulSoup(response.content, "lxml")
        
        # 根据操作系统调整正则表达式
        import platform
        system = platform.system()
        
        if system == "Windows":
            # Windows操作系统下的文件模式
            r1 = r'python-\S+-win\S+.exe'  # 常规Windows安装包
            r2 = r'python-\S+-embed\S+.zip'  # 嵌入式版本
            r3 = r'python-\S+-amd64\S+.exe'  # 64位Windows版本
            r4 = r'python-\S+-webinstall\S+.exe'  # Web安装版本
            r5 = r'python-\S+.msi'  # MSI安装包
            r6 = r'python-\S+.chm'  # CHM帮助文件
            r7 = r'python-\S+.asc'  # 签名文件
            results = []
            for i in bs.find_all("a"):
                # 使用正则匹配版本号格式
                if (re.match(r1, i.text) or re.match(r2, i.text) or 
                    re.match(r3, i.text) or re.match(r4, i.text) or 
                    re.match(r5, i.text) or re.match(r6, i.text) or 
                    re.match(r7, i.text)):
                    packages = i.text.strip(" ")
                    results.append(packages)
        else:
            # macOS/Linux操作系统下的文件模式
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
            if (re.match(r1, i.text) or re.match(r2, i.text) or 
                re.match(r3, i.text) or re.match(r4, i.text) or 
                re.match(r5, i.text) or re.match(r6, i.text) or 
                re.match(r7, i.text)) and "exe" not in i.text and "win" not in i.text and "embed" not in i.text:
                    packages = i.text.strip(" ")
                    results.append(packages)
                    
        app_logger.info(f"找到{len(results)}个Python包文件")
        return results
    except Exception as e:
        # 更新UI显示错误
        error_logger.error(f"刷新Python文件列表失败: {str(e)}")
        return []
def show_name():
    while True:
        try:
            # 检查version_combobox是否存在于全局变量中
            if 'version_combobox' not in globals() or not version_combobox or not hasattr(version_combobox, 'winfo_exists') or not version_combobox.winfo_exists():
                # 如果组件不存在或已被销毁，等待下次检查
                time.sleep(1)
                continue
                
            # 确保在主线程中获取UI值
            if threading.current_thread() != threading.main_thread():
                # 不在主线程时，使用队列获取UI值
                value_queue = queue.Queue()
                def get_ver_value():
                    try:
                        value_queue.put(version_combobox.get())
                    except Exception as e:
                        value_queue.put(None)
                        error_logger.error(f"获取版本值失败: {e}")
                if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                    root.after(0, get_ver_value)
                    ver = value_queue.get(timeout=1)
                    if ver is None:
                        # 获取失败，等待下次检查
                        time.sleep(1)
                        continue
                else:
                    # root不存在，等待下次检查
                    time.sleep(1)
                    continue
            else:
                # 在主线程中直接获取
                ver = version_combobox.get()
            
            # 确保下载目录存在
            download_dir = os.path.join(config_path, "crashes", "download")
            if not os.path.exists(download_dir):
                try:
                    os.makedirs(download_dir, exist_ok=True)
                    app_logger.info(f"创建下载缓存目录: {download_dir}")
                except Exception as e:
                    error_logger.error(f"创建下载缓存目录失败: {e}")
                    
            # 处理版本文件
            ver_file = os.path.join(download_dir, "ver.txt")
            if os.path.exists(ver_file):
                ver1 = edit.read_file(version, "download", "ver.txt")
                if ver1 == ver:
                    app_logger.info("版本号相同")
                else:
                    ver2 = ver  # 直接使用已获取的值
                    edit.edit_file(version, "download", "ver.txt", ver2)
                    app_logger.info("修改版本号")
            else:
                try:
                    # 确保目录存在
                    open.create_crashes_folder(version, "download")
                    open.create_crashes_file(version, "download", "ver.txt")
                except Exception as e:
                    error_logger.error(f"创建版本文件失败: {e}")
            
            # 刷新可用包列表
            a = python_file_reload()
            
            # 安全地更新UI
            def update_ui_combobox():
                try:
                    if 'choose_file_combobox' in globals() and choose_file_combobox and hasattr(choose_file_combobox, 'winfo_exists') and choose_file_combobox.winfo_exists():
                        choose_file_combobox.configure(values=a)
                        app_logger.info(f"更新文件列表: {len(a)}个文件")
                except Exception as ui_ex:
                    error_logger.error(f"更新文件列表UI失败: {ui_ex}")
            
            # 确保在主线程中更新UI
            if threading.current_thread() == threading.main_thread():
                update_ui_combobox()
            else:
                if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                    root.after(0, update_ui_combobox)
                
            time.sleep(0.5)
            gc.collect()
        except Exception as e:
            error_logger.error(f"显示python包失败: {str(e)},Line272,{myfilenumber}")
            time.sleep(1)  # 出错后等待时间延长，减少错误日志量
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
    
    根据当前操作系统，尝试执行Python3命令来检查安装情况。
    如果命令执行出错，说明Python3未安装，则更新界面标签并禁用相关按钮。
    """
    global status_label, download_pb
    
    try:
        # 导入需要的模块 - 将所有导入放在函数最前面
        import platform
        import subprocess
        
        system = platform.system()
        
        # 根据系统选择合适的Python命令
        if system == "Windows":
            # Windows下通常使用python命令
            try:
                version_output = subprocess.check_output(["python", "--version"], stderr=subprocess.STDOUT, text=True)
            except FileNotFoundError:
                # 如果找不到python命令，尝试python3
                version_output = subprocess.check_output(["py", "-3", "--version"], stderr=subprocess.STDOUT, text=True)
        else:
            # macOS和Linux下使用python3命令
            version_output = subprocess.check_output(["python3", "--version"], stderr=subprocess.STDOUT, text=True)
        
        # 验证输出是否包含预期的Python版本信息
        if "Python 3" not in version_output:
            raise ValueError("Unexpected Python version output: " + version_output.strip())
            
        # 检查Python版本管理
        try:
            if settings_mgr and hasattr(settings_mgr, 'settings') and isinstance(settings_mgr.settings, dict):
                # 确保python版本设置初始化
                if "python_versions" not in settings_mgr.settings:
                    settings_mgr.settings["python_versions"] = {
                        "installations": [],
                        "default_version": ""
                    }
                elif not isinstance(settings_mgr.settings["python_versions"], dict):
                    # 如果python_versions不是字典类型，重置为正确的格式
                    app_logger.warning(f"python_versions类型错误，当前类型: {type(settings_mgr.settings['python_versions'])}")
                    settings_mgr.settings["python_versions"] = {
                        "installations": [],
                        "default_version": ""
                    }
                
                # 确保python安装信息是列表
                installations = settings_mgr.settings["python_versions"].get("installations", [])
                if not isinstance(installations, list):
                    app_logger.warning(f"python_installations类型错误，当前类型: {type(installations)}")
                    settings_mgr.settings["python_versions"]["installations"] = []
                
                # 确保python安装信息中没有字符串类型
                if isinstance(settings_mgr.settings["python_versions"], dict) and "installations" in settings_mgr.settings["python_versions"]:
                    if isinstance(settings_mgr.settings["python_versions"]["installations"], str):
                        try:
                            # 尝试将字符串解析为JSON列表
                            import json
                            installations = json.loads(settings_mgr.settings["python_versions"]["installations"])
                            if isinstance(installations, list):
                                settings_mgr.settings["python_versions"]["installations"] = installations
                            else:
                                settings_mgr.settings["python_versions"]["installations"] = []
                        except:
                            # 如果解析失败，设置为空列表
                            settings_mgr.settings["python_versions"]["installations"] = []
        except Exception as check_ex:
            # 记录错误但不中断操作
            error_logger.error(f"检查Python设置时出错: {check_ex}")
            
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        # 如果命令执行失败，说明Python3未安装或命令无法执行
        error_msg = str(e)
        app_logger.warning(f"Python检查失败: {error_msg}")
        
        # 更新UI
        if 'status_label' in globals() and status_label and status_label.winfo_exists():
            # 根据系统显示不同的消息
            if system == "Windows":
                status_label.config(text="未检测到Python3。请从python.org安装")
            else:
                status_label.config(text="未检测到Python3。请使用系统包管理器安装")
            
            # 如果存在HAS_PIP_MANAGER和pip_manager，使用pip_manager中的按钮
            if 'HAS_PIP_MANAGER' in globals() and HAS_PIP_MANAGER and 'pip_manager' in globals() and pip_manager:
                # pip_manager类中可能有自己的按钮，不需要处理这里的按钮
                app_logger.info("使用新的PipManager界面，跳过旧按钮禁用")
            else:
                # 旧界面中的按钮禁用
                # 确保这些按钮在当前存在
                for btn_name in ["pip_upgrade_button", "install_button", "uninstall_button"]:
                    if btn_name in globals() and globals()[btn_name] and globals()[btn_name].winfo_exists():
                        globals()[btn_name].config(state="disabled")
        
        # 延时指定时间后清除当前状态标签的文本
        if 'root' in globals() and root.winfo_exists():
            root.after(delay, clear_a)
    except Exception as ex:
        # 处理其他任何异常
        error_logger.error(f"检查Python安装时出错: {ex}")
        if 'status_label' in globals() and status_label and status_label.winfo_exists():
            status_label.config(text=f"检查Python时出错")
        if 'root' in globals() and root.winfo_exists():
            root.after(delay, clear_a)

def clear_a():
    """清除状态信息和进度条"""
    if 'status_label' in globals() and status_label and status_label.winfo_exists():
        status_label.config(text="")

    # Safely check for package_label existence before accessing
    if 'package_label' in globals() and globals()['package_label'] and globals()['package_label'].winfo_exists():
        globals()['package_label'].config(text="")

    if 'download_pb' in globals() and download_pb and hasattr(download_pb, 'winfo_exists') and download_pb.winfo_exists():
        download_pb['value'] = 0  # 重置进度条
def select_destination():
    """选择下载目标路径"""
    global destination_entry
    
    # 检查组件是否初始化
    if not destination_entry:
        app_logger.error("目标路径输入框未初始化")
        return
        
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

def on_download_status_changed(task):
    """处理下载任务状态变化的回调函数"""
    global current_task_id
    app_logger.info(f"正在更新任务进度: ID={current_task_id}, 状态={task.status}, 进度={task.progress:.1f}%, 速度={task.speed/1024/1024:.2f}MB/s")
    update_download_ui()
    
    # 如果下载出错或完成，更新UI
    if task.status in ['completed', 'error', 'cancelled']:
        update_download_ui()

def init_download_manager(force_reset=False):
    """初始化下载管理器"""
    global download_manager
    
    # 如果需要强制重置
    if force_reset and download_manager:
        reset_download_manager()
        
    # 如果下载管理器为None，创建新的实例
    if download_manager is None:
        try:
        # 优化线程数配置
            thread_count = min(max(2, int(threads_entry.get())), os.cpu_count() * 2)
            
            # 定义下载完成回调函数，确保函数签名匹配downloader中的要求
            def download_complete_callback(file_path=None, total_size=0, speed=0):
                app_logger.info(f"下载完成: {file_path}, 大小: {total_size}, 速度: {speed:.2f}MB/s")
                # 在这里可以添加下载完成后的处理逻辑
            
            # 下载进度回调
            def download_progress_callback(task):
                global is_downloading, current_task_id
                app_logger.info(f"任务状态变更: ID={task.task_id}, 状态={task.status}, 进度={task.progress:.1f}%, 速度={task.speed/1024/1024:.2f}MB/s")
                # 触发UI更新
                update_task_progress(task)
                
                # 如果下载出错或完成，更新UI
                if task.status in ['completed', 'error', 'cancelled']:
                    update_download_ui()
            
            # 创建下载管理器
            from downloader.DownloadManager import DownloadManager
            download_manager = DownloadManager(
                max_concurrent_downloads=1,  # 一次只下载一个Python版本
                num_threads_per_download=thread_count,
                on_task_status_changed=download_progress_callback,
                status_callback=download_complete_callback,  # 添加完成回调
                on_task_progress=download_progress_callback  # 确保进度回调设置
            )
            
            app_logger.info(f"下载管理器创建成功，线程数: {thread_count}")
        except Exception as e:
            error_logger.error(f"初始化下载管理器失败: {e}")
            traceback.print_exc()
            return None

    return download_manager

def update_download_ui():
    """更新下载UI状态"""
    global is_downloading, current_task_id, download_manager
    global status_label, download_pb, size_label, speed_label
    global download_button, pause_button, cancel_button

    # 如果不是下载状态，不更新UI
    if not is_downloading:
            return

    # 使用标志防止重复调用和竞态条件
    if hasattr(update_download_ui, "_is_updating") and update_download_ui._is_updating:
        return
        
    update_download_ui._is_updating = True
    
    # 防抖动机制：记录上次UI状态，只有当状态确实变化时才更新UI
    if not hasattr(update_download_ui, "_last_state"):
        update_download_ui._last_state = {
            "status": "",
            "progress": 0,
            "downloaded": 0,
            "total_size": 0,
            "speed": 0,
            "button_states": {
                "download": tk.DISABLED,
                "pause": tk.NORMAL,
                "cancel": tk.NORMAL,
                "pause_text": "暂停"
            },
            "last_update_time": 0
        }
    
    try:
        # 获取当前时间，用于节流控制
        current_time = time.time()
        min_update_interval = 0.3  # 至少300ms更新一次UI，减少闪烁
        
        # 如果距离上次更新时间太短，不执行更新
        if current_time - update_download_ui._last_state["last_update_time"] < min_update_interval:
            update_download_ui._is_updating = False
            return
        
        # 获取任务状态
        status_str = "unknown"
        percent = 0
        size_str = ""
        speed_str = ""
        status_text = ""
        downloaded = 0
        total_size = 0
        speed = 0

        # 从DownloadManager获取任务信息
        if download_manager and current_task_id:
            task = download_manager.get_task(current_task_id)
            if task:
                # 获取任务状态字符串
                status_str = str(task.status).lower() if hasattr(task, 'status') else 'unknown'
                
                # 获取进度
                percent = task.progress if hasattr(task, 'progress') else 0
                
                # 获取大小信息
                downloaded = task.downloaded_size if hasattr(task, 'downloaded_size') else 0
                total_size = task.total_size if hasattr(task, 'total_size') else 0
                
                if total_size > 0:
                    size_str = f"{downloaded/(1024*1024):.1f}MB / {total_size/(1024*1024):.1f}MB"
                else:
                    size_str = f"{downloaded/(1024*1024):.1f}MB / 未知"
                
                # 获取速度
                speed = task.speed if hasattr(task, 'speed') else 0
                if speed > 0:
                    if speed < 1024:
                        speed_str = f"{speed:.1f}B/s"
                    elif speed < 1024 * 1024:
                        speed_str = f"{speed/1024:.1f}KB/s"
                    else:
                        speed_str = f"{speed/(1024*1024):.2f}MB/s"
                # 状态文本
                if status_str == 'error' and hasattr(task, 'error') and task.error:
                    status_text = f"下载错误: {task.error}"
                elif status_str == 'completed':
                    status_text = "下载完成"
                elif status_str == 'downloading':
                    status_text = "正在下载..."
                elif status_str == 'paused':
                    status_text = "已暂停"
                elif status_str == 'waiting':
                    status_text = "等待下载..."
                elif status_str == 'cancelled':
                    status_text = "已取消"
                elif status_str == 'connecting':
                    status_text = "正在连接..."
                else:
                    status_text = f"状态: {status_str}"
                    
        # 检查状态是否与上次相同
        current_state = {
            "status": status_str,
            "progress": percent,
            "downloaded": downloaded,
            "total_size": total_size,
            "speed": speed
        }
        
        # 比较当前状态和上次状态，仅在状态有显著变化时更新UI
        should_update = False
        
        # 总是更新这些重要状态的变化
        if (status_str != update_download_ui._last_state["status"] or
            abs(percent - update_download_ui._last_state["progress"]) >= 1.0 or
            abs(speed - update_download_ui._last_state["speed"]) > speed * 0.1):  # 速度变化超过10%
            should_update = True
        
        # 每2秒强制更新一次，确保UI不会完全停滞
        if current_time - update_download_ui._last_state["last_update_time"] >= 2.0:
            should_update = True
            
        if not should_update:
            update_download_ui._is_updating = False
            return
            
        # 更新上次状态
        update_download_ui._last_state.update(current_state)
        update_download_ui._last_state["last_update_time"] = current_time
        
        # 更新进度条
        if 'download_pb' in globals() and download_pb and hasattr(download_pb, 'winfo_exists') and download_pb.winfo_exists():
            if percent >= 0:
                download_pb['value'] = percent
        
        # 更新标签
        if 'status_label' in globals() and status_label and hasattr(status_label, 'winfo_exists') and status_label.winfo_exists():
            status_label.config(text=status_text)
            
        if 'size_label' in globals() and size_label and hasattr(size_label, 'winfo_exists') and size_label.winfo_exists():
            size_label.config(text=size_str)
            
        if 'speed_label' in globals() and speed_label and hasattr(speed_label, 'winfo_exists') and speed_label.winfo_exists():
            speed_label.config(text=speed_str)
        
        # 根据下载状态更新按钮
        if status_str == 'downloading':
            # 正在下载状态
            if (download_button['state'] != tk.DISABLED or 
                pause_button['text'] != "暂停" or 
                pause_button['state'] != tk.NORMAL or 
                cancel_button['state'] != tk.NORMAL):
                app_logger.info("正在下载，更新按钮状态")
                download_button.config(state=tk.DISABLED)
                pause_button.config(text="暂停", command=pause_download, state=tk.NORMAL)
                cancel_button.config(state=tk.NORMAL)
        elif status_str == 'paused':
            # 已暂停状态
            if (download_button['state'] != tk.DISABLED or 
                pause_button['text'] != "继续" or 
                pause_button['state'] != tk.NORMAL or 
                cancel_button['state'] != tk.NORMAL):
                app_logger.info("已暂停，更新按钮状态")
                download_button.config(state=tk.DISABLED)
                pause_button.config(text="继续", command=resume_download, state=tk.NORMAL)
                cancel_button.config(state=tk.NORMAL)
        elif status_str == 'completed' or status_str == 'error' or status_str == 'cancelled':
            # 已完成/错误/取消状态
            if (download_button['state'] != tk.NORMAL or 
                pause_button['state'] != tk.DISABLED or 
                cancel_button['state'] != tk.DISABLED):
                app_logger.info("下载已结束，更新按钮状态")
                download_button.config(state=tk.NORMAL)
                pause_button.config(state=tk.DISABLED)
                cancel_button.config(state=tk.DISABLED)
                
                # 下载完成，重置下载状态标志
                
                is_downloading = False
        else:
            # 其他状态（等待、连接等）
            if (download_button['state'] != tk.DISABLED or
                pause_button['state'] != tk.DISABLED or
                cancel_button['state'] != tk.NORMAL):
                app_logger.info("等待中，更新按钮状态")
                download_button.config(state=tk.DISABLED)
                pause_button.config(state=tk.DISABLED)
                cancel_button.config(state=tk.NORMAL)
                
    except Exception as e:
        error_logger.error(f"更新下载UI错误: {str(e)}")
    finally:
        update_download_ui._is_updating = False

def update_button_states(can_download: bool, can_resume: bool, can_cancel: bool):
    """更新下载控制按钮的状态"""
    global download_button, pause_button, resume_button, cancel_button
    
    # 检查组件是否初始化
    if not all([download_button, pause_button, resume_button, cancel_button]):
        app_logger.error("按钮组件未初始化")
        return
    
    try:
        # 安全更新，避免组件已销毁的错误
        if download_button.winfo_exists():
            download_button.config(state=tk.NORMAL if can_download else tk.DISABLED)
        
        if pause_button.winfo_exists():
            pause_button.config(state=tk.NORMAL if not can_resume and can_cancel else tk.DISABLED)
        
        if resume_button.winfo_exists():
            resume_button.config(state=tk.NORMAL if can_resume else tk.DISABLED)
        
        if cancel_button.winfo_exists():
            cancel_button.config(state=tk.NORMAL if can_cancel else tk.DISABLED)
    except Exception as e:
        error_logger.error(f"更新按钮状态失败: {e}")

def update_task_progress(task=None):
    """定期更新下载任务进度
    Args:
        task: DownloadTask对象，当作为回调时自动传入
    """
    global is_downloading, current_task_id, download_manager
    
    # 防止重复调度
    if hasattr(update_task_progress, "_is_scheduled") and update_task_progress._is_scheduled:
        return
        
    update_task_progress._is_scheduled = True
    
    try:
        # 如果根本没有下载中，不执行更新
        if not is_downloading:
            update_task_progress._is_scheduled = False
            return
            
            
        # 安全地获取当前任务
        if task is None and download_manager and current_task_id:
            try:
                task = download_manager.get_task(current_task_id)
            except Exception as e:
                error_logger.error(f"获取任务失败: {e}")
                task = None
                
        # 如果有任务对象，打印任务信息辅助调试
        if task:
            try:
                status_str = str(task.status).lower() if hasattr(task, 'status') else 'unknown'
                progress = task.progress if hasattr(task, 'progress') else 0
                speed = task.speed if hasattr(task, 'speed') else 0
                
                # 记录日志，帮助分析问题（生产环境可删除或调低日志级别）
                app_logger.info(f"正在更新任务进度: ID={current_task_id}, 状态={status_str}, 进度={progress:.1f}%, 速度={speed/1024/1024:.2f}MB/s")
            except Exception as e:
                error_logger.error(f"处理任务信息失败: {e}")
        
        # 使用线程安全方式更新UI
        def safe_update_ui():
            try:
                update_download_ui()
            except Exception as e:
                error_logger.error(f"安全更新UI失败: {e}")
        
        # 检查UI更新的条件
        if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
            # 在主线程中调度UI更新
            if threading.current_thread() == threading.main_thread():
                safe_update_ui()
            else:
                # 确保在主线程中更新UI
                try:
                    root.after(0, safe_update_ui)
                except Exception as e:
                    error_logger.error(f"调度UI更新失败: {e}")
        
        # 计算下一次更新的时间
        try:
            progress = float(download_pb['value']) if download_pb and hasattr(download_pb, 'winfo_exists') and download_pb.winfo_exists() and 'value' in download_pb else 0
        except (ValueError, TypeError, AttributeError):
            progress = 0
            
        # 动态调整刷新间隔
        if progress > 95:
            refresh_interval = 2000  # 接近完成时显著减少刷新频率
        elif progress > 80:
            refresh_interval = 1000  # 高进度时减少刷新频率
        else:
            refresh_interval = 500   # 正常刷新频率
        
        # 始终安排下一次更新，只要is_downloading还是True
        if is_downloading and 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
            root.after(refresh_interval, update_task_progress)
        else:
            update_task_progress._is_scheduled = False
        
    except Exception as e:
        error_logger.error(f"任务进度更新错误: {str(e)}")
        # 即使出错也继续调度下一次更新
        if is_downloading and 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
            root.after(1000, update_task_progress)  # 出错时使用较长的刷新间隔
        else:
            update_task_progress._is_scheduled = False

def validate_download_config():
    """验证下载配置是否有效"""
    global version_combobox, destination_entry, choose_file_combobox, threads_entry
    global status_label, download_button
    
    # 检查组件是否初始化
    if not all([version_combobox, destination_entry, choose_file_combobox, threads_entry, 
                status_label, download_button]):
        app_logger.error("UI组件未初始化")
        return False
    
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
    global current_task_id, is_downloading, download_manager
    global download_pb, status_label, download_button, pause_button, cancel_button, size_label, speed_label
    global version_combobox, destination_entry, choose_file_combobox, threads_entry
    
    # 检查组件是否初始化
    if not all([version_combobox, destination_entry, choose_file_combobox, threads_entry, 
                download_pb, status_label, download_button, pause_button, cancel_button,
                size_label, speed_label]):
        app_logger.error("UI组件未初始化")
        return
        
    # 如果已经在下载，不要重复启动
    if is_downloading:
        app_logger.warning("已有下载任务在进行中，请先取消或等待完成")
        messagebox.showinfo("提示", "已有下载任务在进行中，请先取消或等待完成")
        return
    
    # 验证下载配置
    if not validate_download_config():
        return
    
    selected_version = version_combobox.get()
    destination_path = destination_entry.get()
    file_name = choose_file_combobox.get()
    thread_count = int(threads_entry.get())
    
    # 标准化路径并确保目录存在
    destination_path = normalize_path(destination_path)
    if not ensure_dir_exists(destination_path):
        messagebox.showerror("错误", f"无法创建目录: {destination_path}")
        return
    
    # 准备保存路径
    save_path = os.path.join(destination_path, file_name)
    
    # 检查文件是否已存在
    if os.path.exists(save_path):
        if messagebox.askyesno("文件已存在", f"文件 {file_name} 已存在。\n是否覆盖？"):
            try:
                # 重置下载管理器，确保可以重新创建
                reset_download_manager()
                
                # 尝试删除现有文件
                app_logger.info(f"正在删除已存在的文件: {save_path}")
                os.remove(save_path)
                
                # 确认文件已被删除
                if os.path.exists(save_path):
                    error_logger.error(f"文件删除失败，文件可能被占用: {save_path}")
                    messagebox.showerror("错误", "无法删除现有文件，文件可能被其他程序占用")
                    return
                    
                # 确保界面刷新
                root.update()
                app_logger.info(f"已成功删除文件: {save_path}")
            except Exception as e:
                error_logger.error(f"删除已存在文件失败: {e}")
                messagebox.showerror("错误", f"无法删除现有文件: {e}")
                return
        else:
            return
    
    # 获取下载URL
    url = get_download_url_for_version(selected_version, file_name)
    if not url:
        messagebox.showerror("错误", "无法获取下载URL。请检查网络连接和版本选择。")
        return
    
    # 检查和创建下载管理器
    try:
        # 强制重置下载管理器，确保文件覆盖后能重新创建
        reset_download_manager()
        
        # 重新创建下载管理器
        if not download_manager:
            from downloader.DownloadManager import DownloadManager
            
            
            # 定义下载完成回调函数，确保函数签名匹配downloader中的要求
            def download_complete_callback(file_path=None, total_size=0, speed=0):
                app_logger.info(f"下载完成: {file_path}, 大小: {total_size}, 速度: {speed:.2f}MB/s")
                # 在这里可以添加下载完成后的处理逻辑
            
            # 下载进度回调
            def download_progress_callback(task):
                app_logger.info(f"正在更新任务进度: ID={current_task_id}, 状态={task.status}, 进度={task.progress:.1f}%, 速度={task.speed/1024/1024:.2f}MB/s")
                update_download_ui()
                
                # 如果下载出错或完成，更新UI
                if task.status in ['completed', 'error', 'cancelled']:
                    update_download_ui()
            
            download_manager = DownloadManager(
                max_concurrent_downloads=1,  # 一次只下载一个Python版本
                num_threads_per_download=thread_count,
                on_task_status_changed=download_progress_callback,
                status_callback=download_complete_callback  # 添加完成回调
            )
            app_logger.info("下载管理器创建成功")
        
        # 使用下载管理器添加下载任务
        app_logger.info(f"开始下载: {url} -> {save_path}")
        
        # 重置UI
        download_pb['value'] = 0
        status_label.config(text="准备下载...")
        size_label.config(text="")
        speed_label.config(text="")
        
        # 提前设置下载状态标志，避免竞态条件
        is_downloading = True
        
        # 切换按钮状态
        download_button.config(state=tk.DISABLED)
        pause_button.config(state=tk.NORMAL, text="暂停", command=pause_download)
        cancel_button.config(state=tk.NORMAL)
        
        # 设置下载任务
        current_task_id = download_manager.add_task(url, save_path, thread_count)
        
        # 立即启动任务
        if not download_manager.start_task(current_task_id):
            raise Exception("无法启动下载任务")
            
        # 立即更新UI状态，不等待下一个计划周期
        app_logger.info(f"下载任务创建成功: {current_task_id}")
        
        # 重置更新计时器标志，确保能够启动新的计时器
        if hasattr(update_task_progress, "_is_scheduled"):
            update_task_progress._is_scheduled = False
            
        # 确保任务进度更新定时器在运行
        update_task_progress()
        
        # 保存此次下载目录，下次使用
        try:
            import json
            save_data = {"last_dir": destination_path}
            
            if hasattr(json_manager, 'write_json'):
                json_manager.write_json(os.path.join(config_path, "last_download.json"), save_data)
            else:
                with open(os.path.join(config_path, "last_download.json"), 'w') as f:
                    json.dump(save_data, f)
                    
            app_logger.info(f"保存下载目录: {destination_path}")
        except Exception as save_err:
            error_logger.error(f"保存下载目录失败: {str(save_err)}")
    
    except Exception as e:
        error_logger.error(f"设置下载失败: {str(e)}")
        traceback.print_exc()
        messagebox.showerror("错误", f"设置下载失败: {str(e)}")
        download_button.config(state=tk.NORMAL)
        is_downloading = False  # 确保状态标志被重置

def simple_download(url, save_path, proxies=None):
    """简单的文件下载实现，作为备用方案，使用urllib.request库"""
    global is_downloading, file_size, downloaded_bytes, status_label, download_pb
    global download_button, pause_button, cancel_button, size_label, speed_label
    
    try:
        import urllib.request
        import urllib.error
        import ssl
        
        # 提示开始下载
        app_logger.info(f"开始简单下载模式: {url} -> {save_path}")
        
        # 创建目录（如果不存在）
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
            
        # 更新UI状态
        def update_ui_status(text):
            if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                root.after(0, lambda: status_label.config(text=text) if 'status_label' in globals() and status_label and hasattr(status_label, 'winfo_exists') and status_label.winfo_exists() else None)
                
        update_ui_status("准备下载...")
        
        # 创建SSL上下文，允许不安全连接
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # 创建请求
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        # 配置代理
        if proxies and 'http' in proxies:
            proxy_handler = urllib.request.ProxyHandler(proxies)
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)
            
        # 打开连接
        update_ui_status("连接中...")
        conn = urllib.request.urlopen(req, context=ctx, timeout=30)
        
        # 获取文件大小
        file_size = int(conn.info().get('Content-Length', 0))
        if file_size == 0:
            app_logger.warning("无法获取文件大小信息")
            
        # 更新UI状态
        update_ui_status("正在下载...")
        
        # 创建文件
        with open(save_path, 'wb') as out_file:
            # 重置下载状态
            downloaded = 0
            block_size = 8192  # 8KB
            start_time = time.time()
            
            # 下载文件块
            while is_downloading:
                try:
                    buffer = conn.read(block_size)
                    if not buffer:
                        break
                        
                    # 写入数据
                    out_file.write(buffer)
                    
                    # 更新下载进度
                    downloaded += len(buffer)
                    downloaded_bytes[0] = downloaded
                    
                    # 每10个块才更新UI一次，避免频繁更新
                    elapsed = time.time() - start_time
                    if not hasattr(simple_download, "_update_counter"):
                        simple_download._update_counter = 0
                    
                    simple_download._update_counter += 1
                    if simple_download._update_counter % 10 == 0:
                        if elapsed > 0 and 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
                            # 计算下载速度
                            current_speed = downloaded / elapsed
                            
                            # 更新UI
                            def update_progress_ui():
                                try:
                                    # 更新进度条
                                    if 'download_pb' in globals() and download_pb and hasattr(download_pb, 'winfo_exists') and download_pb.winfo_exists():
                                        if file_size > 0:
                                            progress = min(100, int((downloaded / file_size) * 100))
                                            download_pb['value'] = progress
                                    
                                    # 更新大小标签
                                    if 'size_label' in globals() and size_label and hasattr(size_label, 'winfo_exists') and size_label.winfo_exists():
                                        size_text = f"{downloaded / (1024 * 1024):.2f} MB"
                                        if file_size > 0:
                                            size_text += f" / {file_size / (1024 * 1024):.2f} MB"
                                        size_label.config(text=size_text)
                                    
                                    # 更新速度标签
                                    if 'speed_label' in globals() and speed_label and hasattr(speed_label, 'winfo_exists') and speed_label.winfo_exists():
                                        speed_text = f"{current_speed / (1024 * 1024):.2f} MB/s"
                                        speed_label.config(text=speed_text)
                                        
                                except Exception as ui_err:
                                    app_logger.error(f"更新下载UI出错: {ui_err}")
                                    
                            root.after(0, update_progress_ui)
                            
                except ConnectionResetError:
                    app_logger.error("下载过程中连接被重置")
                    raise
                except TimeoutError:
                    app_logger.error("下载超时")
                    raise
                except Exception as chunk_err:
                    app_logger.error(f"下载数据块时出错: {chunk_err}")
                    raise
        
        # 检查下载是否已取消
        if not is_downloading:
            app_logger.info("下载已被用户取消")
            try:
                os.remove(save_path)  # 删除未完成的文件
            except:
                pass
            return
            
        # 检查下载是否完成
        if file_size > 0 and downloaded < file_size:
            raise Exception(f"下载不完整: {downloaded} / {file_size} 字节")
            
        # 下载完成处理
        is_downloading = False
        app_logger.info(f"下载完成: {save_path}, 大小: {downloaded} 字节")
        
        # 更新UI
        if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
            def show_complete():
                try:
                    # 更新进度条
                    if 'download_pb' in globals() and download_pb and hasattr(download_pb, 'winfo_exists') and download_pb.winfo_exists():
                        download_pb['value'] = 100
                        
                    # 更新状态标签
                    if 'status_label' in globals() and status_label and hasattr(status_label, 'winfo_exists') and status_label.winfo_exists():
                        status_label.config(text="下载完成")
                        
                    # 更新按钮状态
                    update_button_states(True, False, False)
                        
                    # 显示下载完成消息
                    messagebox.showinfo("下载完成", f"文件已成功下载到:\n{save_path}")
                except Exception as ui_err:
                    app_logger.error(f"显示下载完成UI出错: {ui_err}")
                    
            root.after(0, show_complete)
                
    except Exception as error:
        # 下载失败处理
        is_downloading = False
        error_message = str(error)
        app_logger.error(f"下载失败: {error_message}")
        
        # 更新UI
        if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
            def show_error():
                try:
                    # 重置进度条
                    if 'download_pb' in globals() and download_pb and hasattr(download_pb, 'winfo_exists') and download_pb.winfo_exists():
                        download_pb['value'] = 0
                        
                    # 更新状态标签
                    if 'status_label' in globals() and status_label and hasattr(status_label, 'winfo_exists') and status_label.winfo_exists():
                        status_label.config(text=f"下载失败: {error_message}")
                        
                    # 更新按钮状态
                    update_button_states(True, False, False)
                        
                    # 显示错误消息
                    messagebox.showerror("下载失败", f"下载过程中出错:\n{error_message}")
                except Exception as ui_err:
                    app_logger.error(f"显示下载错误UI出错: {ui_err}")
                    
            root.after(0, show_error)
            
        # 尝试删除不完整的下载文件
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
        except:
            pass

def cancel_download():
    """取消当前下载任务"""
    global download_manager, current_task_id, is_downloading
    global download_button, pause_button, resume_button, cancel_button
    global download_pb, status_label, size_label, speed_label
    
    # 检查组件是否初始化
    if not all([download_button, pause_button, resume_button, cancel_button,
                download_pb, status_label, size_label, speed_label]):
        app_logger.error("UI组件未初始化")
        return
    
    try:
        # 确认是否取消
        if messagebox.askyesno("确认取消", "确定要取消当前下载任务吗？"):
            if download_manager and current_task_id:
                # 取消下载任务
                download_manager.cancel_task(current_task_id)
                app_logger.info(f"取消下载任务: {current_task_id}")
                
                # 重置下载状态
                is_downloading = False
                current_task_id = None
                
                # 重置UI状态
                def safe_update_ui():
                    # 重置进度条和状态
                    download_pb["value"] = 0
                    status_label.config(text="下载已取消", foreground="red")
                    size_label.config(text="")
                    speed_label.config(text="")
                    
                    # 更新按钮状态
                    update_button_states(True, False, False)
                
                # 确保在主线程中更新UI
                if threading.current_thread() == threading.main_thread():
                    safe_update_ui()
                else:
                    try:
                        root.after(0, safe_update_ui)
                    except Exception as e:
                        error_logger.error(f"更新UI失败: {e}")
    except Exception as e:
        error_logger.error(f"取消下载失败: {e}")
        messagebox.showerror("错误", f"取消下载失败: {e}")

def resume_download():
    """恢复下载"""
    global download_manager, current_task_id, is_downloading
    global download_button, pause_button, resume_button, cancel_button
    
    # 检查组件是否初始化
    if not all([download_button, pause_button, resume_button, cancel_button]):
        app_logger.error("UI组件未初始化")
        return
    
    try:
        if download_manager and current_task_id:
            # 恢复下载任务
            download_manager.resume_task(current_task_id)
            app_logger.info(f"恢复下载任务: {current_task_id}")
            
            # 更新下载状态
            is_downloading = True
            
            # 更新按钮状态
            update_button_states(False, False, True)
    except Exception as e:
        error_logger.error(f"恢复下载失败: {e}")
        messagebox.showerror("错误", f"恢复下载失败: {e}")

def pause_download():
    """暂停下载"""
    global download_manager, current_task_id
    global download_button, pause_button, resume_button, cancel_button
    
    # 检查组件是否初始化
    if not all([download_button, pause_button, resume_button, cancel_button]):
        app_logger.error("UI组件未初始化")
        return
    
    try:
        if download_manager and current_task_id:
            # 暂停下载任务
            download_manager.pause_task(current_task_id)
            app_logger.info(f"暂停下载任务: {current_task_id}")
            
            # 更新按钮状态（可恢复、可取消）
            update_button_states(False, True, True)
    except Exception as e:
        error_logger.error(f"暂停下载失败: {e}")
        messagebox.showerror("错误", f"暂停下载失败: {e}")

def show_about():
    messagebox.showinfo("About", f"Version: dev\nBuild: 1962\n10086 days left.")

def on_closing():
    """安全关闭程序，清理资源，终止线程和进程"""
    try:
        global is_downloading, file_reload_stop_event
        
        app_logger.info("程序正在关闭...")
        
        # 停止下载任务
        if 'is_downloading' in globals() and is_downloading:
            app_logger.info("正在取消下载任务...")
            try:
                cancel_download()
            except Exception as e:
                error_logger.error(f"取消下载任务失败: {e}")
        
        # 停止文件刷新线程
        if 'file_reload_stop_event' in globals() and file_reload_stop_event:
            app_logger.info("正在停止文件刷新线程...")
            try:
                if isinstance(file_reload_stop_event, dict):
                    file_reload_stop_event["stop_event"].set()
                    if "process" in file_reload_stop_event:
                        file_reload_stop_event["process"].terminate()
                elif isinstance(file_reload_stop_event, threading.Event):
                    file_reload_stop_event.set()
                else:
                    app_logger.warning(f"无法识别的file_reload_stop_event类型: {type(file_reload_stop_event)}")
            except Exception as e:
                error_logger.error(f"停止文件刷新线程失败: {e}")
            
        # 保存设置
        if 'settings_mgr' in globals() and settings_mgr:
            app_logger.info("正在保存设置...")
            try:
                settings_mgr.save_settings()
                app_logger.info("设置已保存")
            except Exception as e:
                error_logger.error(f"保存设置失败: {e}")
        
        # 关闭下载管理器
        if 'download_manager' in globals() and download_manager:
            app_logger.info("正在关闭下载管理器...")
            try:
                # 调用下载管理器的关闭方法（如果存在）
                if hasattr(download_manager, 'shutdown'):
                    download_manager.shutdown()
                elif hasattr(download_manager, 'close'):
                    download_manager.close()
            except Exception as e:
                error_logger.error(f"关闭下载管理器失败: {e}")
        
        # 确保所有线程有机会终止
        app_logger.info("等待线程终止...")
        time.sleep(0.2)
        
        # 清理缓存文件
        try:
            collect.delete_crashes_folder_all(version)
            app_logger.info("缓存文件已清理")
        except Exception as e:
            error_logger.error(f"删除缓存文件夹失败: {e}")
        
        # 安全销毁根窗口
        app_logger.info("正在销毁主窗口...")
        if 'root' in globals() and root and hasattr(root, 'winfo_exists') and root.winfo_exists():
            try:
                root.destroy()
            except Exception as e:
                error_logger.error(f"销毁根窗口失败: {e}")
                
        app_logger.info("程序退出")
        exit(0)
    except Exception as e:
        # 使用跨平台的方式终止进程
        import sys
        import platform
        import subprocess
        
        error_logger.error(f"关闭程序时出错: {e}")
        error_logger.error("异常堆栈:", exc_info=True)
        
        try:
            # 确保安全退出，不管发生什么错误
            if platform.system() == "Windows":
                # Windows下使用taskkill
                subprocess.call("taskkill /f /im python.exe /t", shell=True)
                subprocess.call("taskkill /f /im pythonw.exe /t", shell=True)
            else:
                # MacOS, Linux下使用killall
                subprocess.call("killall Python", shell=True)
                subprocess.call("killall pyquick", shell=True)
                subprocess.call("killall Pyquick", shell=True)
        except Exception as kill_error:
            error_logger.error(f"强制终止进程失败: {kill_error}")
            
        sys.exit(1)

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

def init_pip_manager_old(parent=None):
    """初始化pip_manager"""
    global pip_manager, settings_tab, config_path
    
    try:
        # 使用新的PIP管理器
        # 使用新函数代替
        from pipx.pip_manager import PipManager
        from settings.python_manager import PythonManager
        
        # 创建Python环境管理器
        python_manager = PythonManager(parent=parent, settings_manager=None)
        
        # 创建PIP管理器
        if parent:
            pip_manager = PipManager(parent, python_manager, config_path)
            return pip_manager
        else:
            # 无父窗口时的处理
            app_logger.warning("无法初始化PIP管理器：无父窗口")
            return None
    except Exception as e:
        error_logger.error(f"初始化PIP管理器失败: {e}")
        messagebox.showerror("错误", f"初始化PIP管理器失败: {e}")

# 在合适的位置添加PIP管理器的导入
try:
    from pipx.pip_manager import PipManager
    HAS_PIP_MANAGER = True
except ImportError:
    HAS_PIP_MANAGER = False

def init_settings():
    """初始化设置管理器"""
    global settings_mgr
    try:
        # 仅初始化设置管理器
        settings_mgr = init_manager(config_path)
        app_logger.info("设置管理器初始化成功")
        return True
    except Exception as e:
        error_logger.error(f"初始化设置管理器失败: {e}")
        return False

def show_settings():
    """打开设置窗口"""
    global settings_mgr, root
    
    try:
        # 确保设置管理器已初始化
        if settings_mgr is None:
            if not init_settings():
                messagebox.showerror("错误", "无法初始化设置管理器")
                return
        
        # 使用设置模块中的函数打开设置窗口
        from settings.ui.window import SettingsWindow
        settings_window = SettingsWindow(root, settings_mgr)
        
        app_logger.info("已打开设置窗口")
    except Exception as e:
        error_logger.error(f"打开设置窗口失败: {e},Line830,{myfilenumber},show_settings")
        messagebox.showerror("错误", f"打开设置窗口失败: {e},Line831,{myfilenumber},show_settings")

def apply_theme(refresh=False):
    """
    应用主题到界面
    
    Args:
        refresh: 是否刷新当前窗口的主题
    
    Returns:
        str: 应用的主题名称
    """
    try:
        import ttkbootstrap as tb
        import darkdetect
        
        # 获取当前设置
        theme_setting = "系统默认"
        custom_accent = False
        accent_color = "#1a73e8"  # 默认蓝色强调色
        
        if settings_mgr:
            theme_setting = settings_mgr.get("appearance.theme", "系统默认")
            custom_accent = settings_mgr.get("appearance.use_custom_accent", False)
            accent_color = settings_mgr.get("appearance.custom_accent_color", "#1a73e8")
        
        # 确定要使用的主题
        theme = "litera"  # 默认浅色主题
        
        # 如果是系统默认，则根据系统深色模式决定
        if theme_setting == "系统默认":
            try:
                if darkdetect.isDark():
                        theme = "darkly"  # 深色主题
                else:
                        theme = "litera"  # 浅色主题
            except:
                    theme = "litera"  # 默认浅色主题
        # 明确选择的主题
        elif theme_setting == "浅色":
            theme = "litera"
        elif theme_setting == "深色":
            theme = "darkly"
        elif theme_setting == "蓝色":
            theme = "flatly"
        elif theme_setting == "绿色":
            theme = "yeti"
        elif theme_setting == "彩色":
            theme = "pulse"
        elif theme_setting == "灰色":
            theme = "cosmo"
        elif theme_setting == "科技感":
            theme = "cyborg"
        elif theme_setting == "简约":
            theme = "minty"
        
        # 如果使用自定义强调色，创建自定义主题
        if custom_accent and accent_color:
            # 自定义主题需要额外处理，这里简化为直接使用现有主题
            app_logger.info(f"将使用强调色: {accent_color}，但当前版本不支持完全自定义主题")
        
        # 如果需要刷新主题
        if refresh and 'root' in globals():
            try:
                # 更新当前窗口主题
                app_logger.info(f"正在动态切换主题到: {theme}")
                style = tb.Style(theme=theme)
                style.theme_use(theme)
                root.config(bg=style.colors.bg)
                
                # 配置对话框颜色
                dialog_bg = style.colors.bg
                dialog_fg = style.colors.fg
                root.option_add('*Dialog.msg.background', dialog_bg)
                root.option_add('*Dialog.msg.foreground', dialog_fg)
                
                # 刷新UI
                root.update_idletasks()
            except Exception as refresh_err:
                error_logger.error(f"刷新主题失败: {refresh_err}")
            
        app_logger.info(f"应用ttkbootstrap主题: {theme}")
        return theme
    except Exception as e:
        error_logger.error(f"应用主题失败: {e}")
        return "litera"  # 返回默认主题

def finalize_window_setup():
    """完成窗口设置"""
    root.update_idletasks()
    # 使用ttkbootstrap风格居中窗口
    root.place_window_center()
    app_logger.info("GUI初始化完成")

def get_download_url_for_version(version, file_name):
    """获取指定Python版本的下载URL"""
    try:
        # 基础URL
        base_url = "https://www.python.org/ftp/python"
        
        # 构建完整URL
        url = f"{base_url}/{version}/{file_name}"
        
        app_logger.info(f"构建下载URL: {url}")
        return url
    except Exception as e:
        error_logger.error(f"获取下载URL失败: {str(e)}")
        return None

def normalize_path(path):
    """
    标准化路径，确保在不同操作系统上使用正确的路径分隔符
    
    Args:
        path: 需要标准化的路径
        
    Returns:
        str: 标准化后的路径
    """
    import platform
    
    # 替换路径分隔符
    if platform.system() == "Windows":
        # Windows下使用反斜杠
        return os.path.normpath(path.replace("/", "\\"))
    else:
        # Unix/Linux/Mac下使用正斜杠
        return os.path.normpath(path.replace("\\", "/"))
        
def ensure_dir_exists(path):
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 是否成功确保目录存在
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            app_logger.info(f"创建目录: {path}")
        return True
    except Exception as e:
        error_logger.error(f"创建目录失败: {path}, 错误: {str(e)}")
        return False

def get_python_command(version_suffix="3"):
    """
    根据操作系统返回适当的Python命令
    
    Args:
        version_suffix: Python版本后缀，如'3', '3.9'等
        
    Returns:
        str: Python命令字符串
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows: 尝试多种可能的命令格式
        if version_suffix == "3":
            # 优先使用py启动器
            return "py -3"
        elif version_suffix.startswith("3."):
            # 指定次版本号，如3.9
            minor_version = version_suffix.split(".")[-1]
            return f"py -3.{minor_version}"
        else:
            # 其他自定义情况
            return f"python{version_suffix}"
    else:
        # macOS/Linux
        return f"python{version_suffix}"

def get_pip_command(version_suffix="3"):
    """
    根据操作系统返回适当的pip命令
    
    Args:
        version_suffix: Python版本后缀，如'3', '3.9'等
        
    Returns:
        str: pip命令字符串
    """
    system = platform.system()
    
    if system == "Windows":
        # Windows: 使用py启动器调用pip
        if version_suffix == "3":
            return "py -3 -m pip"
        elif version_suffix.startswith("3."):
            minor_version = version_suffix.split(".")[-1]
            return f"py -3.{minor_version} -m pip"
        else:
            return f"pip{version_suffix}"
    else:
        # macOS/Linux
        return f"pip{version_suffix}"

#GUI
if __name__ == "__main__":
    # 设置错误日志记录器
    error_logger = setup_error_logger()
    
    # 辅助函数定义
    def init_dirs():
        """初始化必要的目录"""
        # 确保配置目录存在
        os.makedirs(config_path, exist_ok=True)
        # 确保日志目录存在
        log_dir = os.path.join(config_path, "log")
        os.makedirs(log_dir, exist_ok=True)
        
    def get_log_dir():
        """获取日志目录路径"""
        return os.path.join(config_path, "log")
    
    # 主函数定义
    def main():
        """主函数"""
        init_dirs()
        
        # 初始化设置管理器
        from settings.settings_manager import init_manager
        init_manager(config_path)
        
        # 从设置中更新调试模式
        update_debug_mode_from_settings()
        
        # 配置日志记录
        configure_global_loggers(
            log_level="debug" if DEBUG_MODE else "info",
            enable_console=True,
            enable_file=True,
            log_dir=get_log_dir(),
            debug_mode=DEBUG_MODE  # 传递调试模式标志
        )
    
    def set_icon(window):
        """设置窗口图标"""
        try:
            # 检查图标文件是否存在
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyquick.icns")
            if os.path.exists(icon_path):
                # 不同平台使用不同的图标设置方法
                if platform.system() == "Windows":
                    window.iconbitmap(icon_path)
                else:
                    # MacOS和Linux使用PhotoImage
                    icon_img = tk.PhotoImage(file=icon_path)
                    window.iconphoto(True, icon_img)
        except Exception as e:
            error_logger.error(f"设置窗口图标失败: {e}")

    def create_ui(root):
        """创建主界面UI组件"""
        global version_combobox, version_reload, choose_file_combobox
        global destination_entry, threads_entry, status_label, download_pb
        global download_button, pause_button, cancel_button, resume_button
        global size_label, speed_label
        
        # 创建顶部菜单栏
        try:
            # 获取ttkbootstrap样式
            style = ttk.Style()
            
            # 获取菜单背景和前景色
            if hasattr(style, 'colors'):
                menu_bg = style.colors.bg
                menu_fg = style.colors.fg
                menu_active_bg = style.colors.selectbg
                menu_active_fg = style.colors.selectfg
            else:
                # 默认颜色
                menu_bg = "#2b2b2b" if "dark" in style.theme_use() else "#ffffff"
                menu_fg = "#ffffff" if "dark" in style.theme_use() else "#000000"
                menu_active_bg = "#007bff"
                menu_active_fg = "#ffffff"
            
            # 创建菜单栏
            menubar = tk.Menu(root, bg=menu_bg, fg=menu_fg, activebackground=menu_active_bg, 
                             activeforeground=menu_active_fg, relief="flat", borderwidth=0)
            
            # 文件菜单
            file_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                              activebackground=menu_active_bg, activeforeground=menu_active_fg)
            file_menu.add_command(label="退出", command=on_closing)
            menubar.add_cascade(label="文件", menu=file_menu)
            
            # 编辑菜单
            edit_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                              activebackground=menu_active_bg, activeforeground=menu_active_fg)
            edit_menu.add_command(label="设置", command=show_settings)
            menubar.add_cascade(label="编辑", menu=edit_menu)
            
            # 窗口菜单
            window_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                                activebackground=menu_active_bg, activeforeground=menu_active_fg)
            window_menu.add_command(label="刷新", command=lambda: python_version_reload())
            menubar.add_cascade(label="窗口", menu=window_menu)
            
            # 帮助菜单
            help_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                              activebackground=menu_active_bg, activeforeground=menu_active_fg)
            help_menu.add_command(label="关于", command=show_about)
            menubar.add_cascade(label="帮助", menu=help_menu)
            
            # 将菜单栏添加到root窗口
            root.config(menu=menubar)
            
            # 记录日志
            app_logger.info("成功创建菜单栏并应用ttkbootstrap样式")
        except Exception as e:
            error_logger.error(f"创建菜单栏失败: {e}")
        
        # 创建标签页控件
        tab_control = ttk.Notebook(root)
        
        # 创建下载标签页
        download_tab = ttk.Frame(tab_control)
        tab_control.add(download_tab, text="Python下载")
        
        # 创建PIP管理标签页
        pip_tab = ttk.Frame(tab_control)
        tab_control.add(pip_tab, text="PIP管理")
        
        # 添加标签页到窗口
        tab_control.pack(expand=1, fill="both")
        
        # 在下载标签页中创建组件
        # 版本选择框架
        version_frame = ttk.LabelFrame(download_tab, text="Python版本选择", bootstyle=PRIMARY)
        version_frame.pack(fill="x", padx=10, pady=5)
        
        # 版本选择标签和下拉框
        ttk.Label(version_frame, text="选择版本:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        version_combobox = ttk.Combobox(version_frame, width=15, bootstyle=INFO)
        version_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 刷新版本按钮
        version_reload = ttk.Button(version_frame, text="刷新版本列表", command=python_version_reload, bootstyle=INFO)
        version_reload.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        # 文件选择框架
        file_frame = ttk.LabelFrame(download_tab, text="文件选择", bootstyle=PRIMARY)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        # 文件选择下拉框
        ttk.Label(file_frame, text="选择文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        choose_file_combobox = ttk.Combobox(file_frame, width=40, bootstyle=INFO)
        choose_file_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 目标路径框架
        dest_frame = ttk.LabelFrame(download_tab, text="目标路径", bootstyle=PRIMARY)
        dest_frame.pack(fill="x", padx=10, pady=5)
        
        # 目标路径输入框和浏览按钮
        ttk.Label(dest_frame, text="保存到:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        destination_entry = ttk.Entry(dest_frame, width=40, bootstyle=INFO)
        destination_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        dest_frame.grid_columnconfigure(1, weight=1)
        
        browse_button = ttk.Button(dest_frame, text="浏览...", command=select_destination, bootstyle=INFO)
        browse_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 下载设置框架
        settings_frame = ttk.LabelFrame(download_tab, text="下载设置", bootstyle=PRIMARY)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # 线程数设置
        ttk.Label(settings_frame, text="线程数:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        threads_entry = ttk.Entry(settings_frame, width=5, bootstyle=INFO)
        threads_entry.insert(0, "4")  # 默认4线程
        threads_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # 下载控制框架
        control_frame = ttk.Frame(download_tab)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # 下载按钮
        download_button = ttk.Button(control_frame, text="下载", command=download_selected_version, bootstyle=SUCCESS)
        download_button.grid(row=0, column=0, padx=5, pady=5)
        
        # 暂停按钮
        pause_button = ttk.Button(control_frame, text="暂停", command=pause_download, state=tk.DISABLED, bootstyle=WARNING)
        pause_button.grid(row=0, column=1, padx=5, pady=5)
        
        # 恢复按钮
        resume_button = ttk.Button(control_frame, text="恢复", command=resume_download, state=tk.DISABLED, bootstyle=INFO)
        resume_button.grid(row=0, column=2, padx=5, pady=5)
        
        # 取消按钮
        cancel_button = ttk.Button(control_frame, text="取消", command=cancel_download, state=tk.DISABLED, bootstyle=DANGER)
        cancel_button.grid(row=0, column=3, padx=5, pady=5)
        
        # 状态框架
        status_frame = ttk.LabelFrame(download_tab, text="下载状态", bootstyle=PRIMARY)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # 进度条
        ttk.Label(status_frame, text="进度:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        download_pb = ttk.Progressbar(status_frame, length=300, bootstyle=SUCCESS)
        download_pb.grid(row=0, column=1, padx=5, pady=5, sticky="we")
        status_frame.grid_columnconfigure(1, weight=1)
        
        # 状态标签
        ttk.Label(status_frame, text="状态:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        status_label = ttk.Label(status_frame, text="")
        status_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # 大小标签
        ttk.Label(status_frame, text="大小:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        size_label = ttk.Label(status_frame, text="")
        size_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # 速度标签
        ttk.Label(status_frame, text="速度:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        speed_label = ttk.Label(status_frame, text="")
        speed_label.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # PIP管理标签页的内容
        global settings_tab
        settings_tab = pip_tab
        
        # 检查是否可以导入PipManager
        try:
            from pipx.pip_manager import PipManager
            global HAS_PIP_MANAGER
            global pip_manager
            HAS_PIP_MANAGER = True
            
            # 初始化PIP管理器
            init_pip_manager_old(pip_tab)
            
            # 初始加载Python版本列表
            try:
                read_python_list()
            except Exception as e:
                error_logger.error(f"加载Python版本列表失败: {e}")
            
            # 启动Python包文件监视线程
            file_reload_thread = threading.Thread(target=show_name, daemon=True)
            file_reload_thread.start()
        except (ImportError, ModuleNotFoundError) as e:
            # 如果无法导入PipManager，创建简单的UI
            HAS_PIP_MANAGER = False
            error_logger.warning(f"无法导入PIP管理器: {e}")
            
            # 创建简单的PIP管理界面
            ttk.Label(pip_tab, text="PIP管理器不可用。请确保pipx模块已正确安装。", bootstyle=DANGER).pack(pady=20)
            ttk.Button(pip_tab, text="安装PIP管理器", command=lambda: messagebox.showinfo("提示", "请安装pipx模块"), bootstyle=PRIMARY).pack(pady=10)
        
        # 设置关闭事件处理
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 自动运行检查
        if 'root' in globals() and root and hasattr(root, 'after'):
            # 检查Python安装情况
            root.after(1000, check_python_installation)
            
            # 配置定时任务检查下载情况
            if 'settings_mgr' in globals() and settings_mgr:
                # 加载上次下载目录
                try:
                    last_dir_config = settings_mgr.get("last_download_directory", "")
                    if last_dir_config and os.path.exists(last_dir_config):
                        destination_entry.delete(0, tk.END)
                        destination_entry.insert(0, last_dir_config)
                except Exception as e:
                    error_logger.error(f"加载下载目录失败: {e}")
            
            # 加载 Python 版本列表
            root.after(500, read_python_list)
            
            # 定期验证下载配置
            validate_config_callback = lambda: root.after(500, validate_download_config)
            root.after(1000, validate_config_callback)
        else:
            app_logger.warning("无法设置自动检查任务：root未定义或不支持after方法")
    
    try:
        # 调用主函数
        main()
        
        # 导入ttkbootstrap
        import ttkbootstrap as tb
        
        # 创建图形界面的主窗口，使用ttkbootstrap的Window
        theme = apply_theme()  # 获取主题
        root = tb.Window(themename=theme)
        
        # 设置窗口图标
        set_icon(root)
        
        # 设置窗口标题和大小
        root.title("PyQuick - Python下载器")
        
        # 创建界面
        create_ui(root)
        
        # 启动事件循环
        root.mainloop()
    except Exception as e:
        error_logger.error(f"程序运行异常: {e}")
        tb_str = traceback.format_exc()
        error_logger.error(tb_str)
        
        # 尝试显示错误消息框
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("错误", f"程序启动异常:\n{e}")
        except:
            pass

if block_features.block_start()==False:
    from get_system_build import system_build
    
    # 根据系统显示不同的错误信息
    system_name = system_build.get_system_name()
    system_version = system_build.get_system_release_build_version()
    
    try:
        import tkinter.messagebox as mb
        mb.showerror("错误", f"无法运行Pyquick:\n您的{system_name}系统版本过低。\n(当前版本: {system_name} {system_version})\n请升级到更高版本。")
    except:
        print(f"错误: 无法运行Pyquick: 您的{system_name}系统版本过低。(当前版本: {system_name} {system_version})")
    
    import sys
    sys.exit(1)

def reset_download_manager():
    """重置下载管理器状态，确保在需要时可以重新创建"""
    global download_manager
    
    try:
        # 如果存在下载管理器，尝试停止所有任务
        if download_manager:
            try:
                # 尝试停止所有任务
                download_manager.cancel_all()
                # 给予一点时间让任务停止
                time.sleep(0.5)
                app_logger.info("已重置下载管理器状态")
            except Exception as e:
                error_logger.error(f"停止下载任务失败: {e}")
                
        # 重置为None，以便下次使用时重新创建
        download_manager = None
    except Exception as e:
        error_logger.error(f"重置下载管理器失败: {e}")

def init_dirs():
    """初始化必要的目录"""
    # 确保配置目录存在
    os.makedirs(config_path, exist_ok=True)
    # 确保日志目录存在
    log_dir = os.path.join(config_path, "log")
    os.makedirs(log_dir, exist_ok=True)
    
def get_log_dir():
    """获取日志目录路径"""
    return os.path.join(config_path, "log")

def set_icon(window):
    """设置窗口图标"""
    try:
        # 检查图标文件是否存在
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pyquick.icns")
        if os.path.exists(icon_path):
            # 不同平台使用不同的图标设置方法
            if platform.system() == "Windows":
                window.iconbitmap(icon_path)
            else:
                # MacOS和Linux使用PhotoImage
                #icon_img = tk.PhotoImage(file=icon_path)
                #window.iconphoto(True, icon_img)
                pass
    except Exception as e:
        error_logger.error(f"设置窗口图标失败: {e}")

def create_ui(root):
    """创建主界面UI组件"""
    global version_combobox, version_reload, choose_file_combobox
    global destination_entry, threads_entry, status_label, download_pb
    global download_button, pause_button, cancel_button, resume_button
    global size_label, speed_label
    
    # 创建顶部菜单栏
    try:
        # 获取ttkbootstrap样式
        style = ttk.Style()
        
        # 获取菜单背景和前景色
        if hasattr(style, 'colors'):
            menu_bg = style.colors.bg
            menu_fg = style.colors.fg
            menu_active_bg = style.colors.selectbg
            menu_active_fg = style.colors.selectfg
        else:
            # 默认颜色
            menu_bg = "#2b2b2b" if "dark" in style.theme_use() else "#ffffff"
            menu_fg = "#ffffff" if "dark" in style.theme_use() else "#000000"
            menu_active_bg = "#007bff"
            menu_active_fg = "#ffffff"
        
        # 创建菜单栏
        menubar = tk.Menu(root, bg=menu_bg, fg=menu_fg, activebackground=menu_active_bg, 
                         activeforeground=menu_active_fg, relief="flat", borderwidth=0)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                          activebackground=menu_active_bg, activeforeground=menu_active_fg)
        file_menu.add_command(label="退出", command=on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                          activebackground=menu_active_bg, activeforeground=menu_active_fg)
        edit_menu.add_command(label="设置", command=show_settings)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 窗口菜单
        window_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                            activebackground=menu_active_bg, activeforeground=menu_active_fg)
        window_menu.add_command(label="刷新", command=lambda: python_version_reload())
        menubar.add_cascade(label="窗口", menu=window_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0, bg=menu_bg, fg=menu_fg, 
                          activebackground=menu_active_bg, activeforeground=menu_active_fg)
        help_menu.add_command(label="关于", command=show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        # 将菜单栏添加到root窗口
        root.config(menu=menubar)
        
        # 记录日志
        app_logger.info("成功创建菜单栏并应用ttkbootstrap样式")
    except Exception as e:
        error_logger.error(f"创建菜单栏失败: {e}")
    
    # 创建标签页控件
    tab_control = ttk.Notebook(root)
    
    # 创建下载标签页
    download_tab = ttk.Frame(tab_control)
    tab_control.add(download_tab, text="Python下载")
    
    # 创建PIP管理标签页
    pip_tab = ttk.Frame(tab_control)
    tab_control.add(pip_tab, text="PIP管理")
    
    # 添加标签页到窗口
    tab_control.pack(expand=1, fill="both")
    
    # 在下载标签页中创建组件
    # 版本选择框架
    version_frame = ttk.LabelFrame(download_tab, text="Python版本选择", bootstyle=PRIMARY)
    version_frame.pack(fill="x", padx=10, pady=5)
    
    # 版本选择标签和下拉框
    ttk.Label(version_frame, text="选择版本:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    version_combobox = ttk.Combobox(version_frame, width=15, bootstyle=INFO)
    version_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # 刷新版本按钮
    version_reload = ttk.Button(version_frame, text="刷新版本列表", command=python_version_reload, bootstyle=INFO)
    version_reload.grid(row=0, column=2, padx=5, pady=5, sticky="w")
    
    # 文件选择框架
    file_frame = ttk.LabelFrame(download_tab, text="文件选择", bootstyle=PRIMARY)
    file_frame.pack(fill="x", padx=10, pady=5)
    
    # 文件选择下拉框
    ttk.Label(file_frame, text="选择文件:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    choose_file_combobox = ttk.Combobox(file_frame, width=40, bootstyle=INFO)
    choose_file_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # 目标路径框架
    dest_frame = ttk.LabelFrame(download_tab, text="目标路径", bootstyle=PRIMARY)
    dest_frame.pack(fill="x", padx=10, pady=5)
    
    # 目标路径输入框和浏览按钮
    ttk.Label(dest_frame, text="保存到:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    destination_entry = ttk.Entry(dest_frame, width=40, bootstyle=INFO)
    destination_entry.grid(row=0, column=1, padx=5, pady=5, sticky="we")
    dest_frame.grid_columnconfigure(1, weight=1)
    
    browse_button = ttk.Button(dest_frame, text="浏览...", command=select_destination, bootstyle=INFO)
    browse_button.grid(row=0, column=2, padx=5, pady=5)
    
    # 下载设置框架
    settings_frame = ttk.LabelFrame(download_tab, text="下载设置", bootstyle=PRIMARY)
    settings_frame.pack(fill="x", padx=10, pady=5)
    
    # 线程数设置
    ttk.Label(settings_frame, text="线程数:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    threads_entry = ttk.Entry(settings_frame, width=5, bootstyle=INFO)
    threads_entry.insert(0, "4")  # 默认4线程
    threads_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    
    # 下载控制框架
    control_frame = ttk.Frame(download_tab)
    control_frame.pack(fill="x", padx=10, pady=5)
    
    # 下载按钮
    download_button = ttk.Button(control_frame, text="下载", command=download_selected_version, bootstyle=SUCCESS)
    download_button.grid(row=0, column=0, padx=5, pady=5)
    
    # 暂停按钮
    pause_button = ttk.Button(control_frame, text="暂停", command=pause_download, state=tk.DISABLED, bootstyle=WARNING)
    pause_button.grid(row=0, column=1, padx=5, pady=5)
    
    # 恢复按钮
    resume_button = ttk.Button(control_frame, text="恢复", command=resume_download, state=tk.DISABLED, bootstyle=INFO)
    resume_button.grid(row=0, column=2, padx=5, pady=5)
    
    # 取消按钮
    cancel_button = ttk.Button(control_frame, text="取消", command=cancel_download, state=tk.DISABLED, bootstyle=DANGER)
    cancel_button.grid(row=0, column=3, padx=5, pady=5)
    
    # 状态框架
    status_frame = ttk.LabelFrame(download_tab, text="下载状态", bootstyle=PRIMARY)
    status_frame.pack(fill="x", padx=10, pady=5)
    
    # 进度条
    ttk.Label(status_frame, text="进度:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    download_pb = ttk.Progressbar(status_frame, length=300, bootstyle=SUCCESS)
    download_pb.grid(row=0, column=1, padx=5, pady=5, sticky="we")
    status_frame.grid_columnconfigure(1, weight=1)
    
    # 状态标签
    ttk.Label(status_frame, text="状态:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    status_label = ttk.Label(status_frame, text="")
    status_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # 大小标签
    ttk.Label(status_frame, text="大小:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
    size_label = ttk.Label(status_frame, text="")
    size_label.grid(row=2, column=1, padx=5, pady=5, sticky="w")
    
    # 速度标签
    ttk.Label(status_frame, text="速度:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
    speed_label = ttk.Label(status_frame, text="")
    speed_label.grid(row=3, column=1, padx=5, pady=5, sticky="w")
    
    # PIP管理标签页的内容
    global settings_tab
    settings_tab = pip_tab
    
    # 检查是否可以导入PipManager
    try:
        from pipx.pip_manager import PipManager
        global HAS_PIP_MANAGER
        global pip_manager
        HAS_PIP_MANAGER = True
        
        # 初始化PIP管理器
        init_pip_manager_old(pip_tab)
        
        # 初始加载Python版本列表
        try:
            read_python_list()
        except Exception as e:
            error_logger.error(f"加载Python版本列表失败: {e}")
        
        # 启动Python包文件监视线程
        file_reload_thread = threading.Thread(target=show_name, daemon=True)
        file_reload_thread.start()
    except (ImportError, ModuleNotFoundError) as e:
        # 如果无法导入PipManager，创建简单的UI
        HAS_PIP_MANAGER = False
        error_logger.warning(f"无法导入PIP管理器: {e}")
        
        # 创建简单的PIP管理界面
        ttk.Label(pip_tab, text="PIP管理器不可用。请确保pipx模块已正确安装。", bootstyle=DANGER).pack(pady=20)
        ttk.Button(pip_tab, text="安装PIP管理器", command=lambda: messagebox.showinfo("提示", "请安装pipx模块"), bootstyle=PRIMARY).pack(pady=10)
    
    # 设置关闭事件处理
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 自动运行检查
    if 'root' in globals() and root and hasattr(root, 'after'):
        # 检查Python安装情况
        root.after(1000, check_python_installation)
        
        # 配置定时任务检查下载情况
        if 'settings_mgr' in globals() and settings_mgr:
            # 加载上次下载目录
            try:
                last_dir_config = settings_mgr.get("last_download_directory", "")
                if last_dir_config and os.path.exists(last_dir_config):
                    destination_entry.delete(0, tk.END)
                    destination_entry.insert(0, last_dir_config)
            except Exception as e:
                error_logger.error(f"加载下载目录失败: {e}")
        
        # 加载 Python 版本列表
        root.after(500, read_python_list)
        
        # 定期验证下载配置
        validate_config_callback = lambda: root.after(500, validate_download_config)
        root.after(1000, validate_config_callback)
    else:
        app_logger.warning("无法设置自动检查任务：root未定义或不支持after方法")

# 添加一个带参数版本的init_pip_manager函数
def init_pip_manager(parent=None):
    """初始化PIP管理器"""
    try:
        from pipx.pip_manager import PipManager
        from settings.python_manager import PythonManager
        
        # 创建Python环境管理器
        python_manager = PythonManager(parent=parent, settings_manager=None)
        
        # 创建PIP管理器
        if parent:
            pip_manager = PipManager(parent, python_manager)
            return pip_manager
        else:
            # 无父窗口时的处理
            app_logger.warning("无法初始化PIP管理器：无父窗口")
            return None
    except Exception as e:
        error_logger.error(f"初始化PIP管理器失败: {e}")
        return None
