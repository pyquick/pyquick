import os
import sys
import threading
import subprocess
import requests
import time
import logging
import tkinter as tk
import multiprocessing
from multiprocessing import Process, Queue
from typing import List, Dict, Optional

# Import local logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger
from utils import safe_config, safe_grid_forget, safe_grid

logger = get_logger()

def get_python_versions():
    """获取系统中安装的Python版本列表"""
    try:
        versions = []
        # 获取 Python 安装位置
        versions_base = subprocess.run(["where", "python"], capture_output=True, text=True, 
                                    creationflags=subprocess.CREATE_NO_WINDOW)
        python_locations = versions_base.stdout.split("\n")
        
        for location in python_locations:
            if not location or location == "\r" or "WindowsApps" in location:
                continue
                
            location = location.strip("\r\n")
            try:
                result = subprocess.run(
                    [location, "--version"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split()[1]  # 获取版本号
                    major_minor = ".".join(version.split(".")[:2])  # 只保留主版本号
                    if major_minor not in versions:
                        versions.append(major_minor)
            except Exception as e:
                logger.warning(f"检查Python版本失败 {location}: {e}")
                
        versions.sort(key=lambda x: [int(i) for i in x.split(".")])
        return versions
    except Exception as e:
        logger.error(f"获取Python版本列表失败: {e}")
        return []

def check_pip_version_process(python_path: str, queue: Queue) -> None:
    """检查指定Python路径的pip版本(子进程函数)"""
    try:
        result = subprocess.run(
            [python_path, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            version = result.stdout.strip().split()[1]  # 获取版本号
            major_minor = ".".join(version.split(".")[:2])  # 提取主版本号
            queue.put((python_path, f"pip{major_minor}"))
    except Exception as e:
        logger.debug(f"检查{python_path}的pip版本失败: {e}")

def get_all_pip_versions() -> List[str]:
    """获取系统中所有pip版本(多进程方式)"""
    versions = get_python_versions()
    if not versions:
        return []
    
    queue = Queue()
    processes = []
    pip_versions = []
    
    # 为每个Python版本创建检查进程
    for version in versions:
        python_path = f"python{version.split('.')[0]}.{version.split('.')[1]}"
        p = Process(
            target=check_pip_version_process,
            args=(python_path, queue)
        )
        p.start()
        processes.append(p)
    
    # 等待所有进程完成
    for p in processes:
        p.join()
    
    # 收集结果
    while not queue.empty():
        pip_versions.append(queue.get()[1])
    
    # 去重并排序
    pip_versions = list(set(pip_versions))
    pip_versions.sort(key=lambda x: float(x.replace("pip", "")), reverse=True)
    return pip_versions

def get_pip_version(config_path):
    """获取当前pip版本,优化版本检查逻辑"""
    try:
        # 1. 首先检查当前Python版本并尝试用对应的pip3.xx.exe
        try:
            with open(os.path.join(config_path, "pythonversion.txt"), "r") as f:
                version_str = f.readlines()[-1].strip("\n")
                if version_str.startswith("Pip"):
                    version_num = version_str[3:]  # 提取数字部分
                    # 格式化版本号 (如"310" -> "3.10")
                    if len(version_num) >= 3:
                        major = version_num[0]
                        minor = version_num[1:]
                        formatted_version = f"{major}.{minor}"
                        
                        # 构建pip命令名称
                        pip_cmd = f"pip{formatted_version}"
                        pip_cmds = [f"{pip_cmd}.exe", pip_cmd]
                        
                        # 尝试所有可能的pip命令
                        for cmd in pip_cmds:
                            try:
                                result = subprocess.run(
                                    [cmd, "--version"],
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                if result.returncode == 0:
                                    version = result.stdout.strip().split()[1]
                                    logger.info(f"通过{cmd}获取到版本: {version}")
                                    return version
                            except Exception as e:
                                logger.warning(f"通过{cmd}获取版本失败: {e}")
        except Exception as e:
            logger.warning(f"读取Python版本信息失败: {e}")

        # 2. 尝试直接检查pip安装路径
        try:
            python_path = None
            with open(os.path.join(config_path, "pythonpath.txt"), "r") as f:
                python_path = f.read().strip()
            
            if python_path:
                pip_path = os.path.join(os.path.dirname(python_path), "Scripts", "pip.exe")
                if os.path.exists(pip_path):
                    result = subprocess.run(
                        [pip_path, "--version"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip().split()[1]
                        logger.info(f"通过pip路径获取到版本: {version}")
                        return version
        except Exception as e:
            logger.warning(f"通过pip路径获取版本失败: {e}")

        # 3. 通过python -m pip检查
        try:
            result = subprocess.run(
                ["python", "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                version = result.stdout.strip().split()[1]
                logger.info(f"通过python -m pip获取到版本: {version}")
                return version
        except Exception as e:
            logger.warning(f"通过python -m pip获取版本失败: {e}")

        # 4. 最后尝试系统pip
        try:
            result = subprocess.run(
                ["pip", "--version"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                version = result.stdout.strip().split()[1]
                logger.info(f"通过系统pip获取到版本: {version}")
                return version
        except Exception as e:
            logger.warning(f"通过系统pip获取版本失败: {e}")

        logger.error("所有pip版本检查方法均失败")
        return None

    except Exception as e:
        logger.error(f"获取pip版本时出错: {e}")
        return None

def get_latest_pip_version():
    """Get latest pip version"""
    try:
        r = requests.get("https://pypi.org/pypi/pip/json", verify=False)
        return r.json()["info"]["version"]
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return None

def show_pip_version(config_path, pip_upgrade_button, install_button, uninstall_button, pip_retry_button):
    """Check and display current pip version"""
    # 初始化允许更新标志
    try:
        with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
            fw.write("True")
            fw.write("\n")
    except Exception as e:
        logger.error(f"写入pip更新标志失败: {e}")

    # 使用主线程更新UI状态为"检查中"
    safe_config(pip_upgrade_button, text="Checking...", state="disabled")

    # 工作线程函数
    def check_pip_version_thread():
        version_pip = None
        latest_version = None
        python_name = "Unknown Python"
        error_occurred = False
        
        try:
            # 获取当前pip版本
            version_pip = get_pip_version(config_path)
            if not version_pip:
                raise Exception("无法获取pip版本")
                
            # 获取Python版本信息
            try:
                python_version = sys.version.split()[0]  # 如 "3.10.0"
                python_name = f"Python {python_version}"
            except Exception as e:
                logger.warning(f"获取Python版本信息失败: {e}")
                python_name = "Python"
            
            # 获取最新pip版本
            latest_version = get_latest_pip_version()
            if not latest_version:
                raise Exception("无法获取最新pip版本")
            
        except Exception as e:
            logger.error(f"获取pip版本失败: {e}")
            error_occurred = True

        # 准备主线程更新函数
        if error_occurred:
            # 出错情况下的UI更新
            update_ui_error()
        else:
            # 成功情况下的UI更新
            update_ui_success(version_pip, latest_version, python_name)

    # 辅助函数，在主线程中更新UI
    def update_ui_error():
        root = tk._default_root
        if root and root.winfo_exists():
            root.after(0, lambda: _update_ui_error())
    
    def _update_ui_error():
        safe_config(pip_upgrade_button, text="Failed to get pip version", state="disabled")
        safe_grid(pip_retry_button, row=1, column=0, columnspan=3, pady=10, padx=10)

    def update_ui_success(version_pip, latest_version, python_name):
        root = tk._default_root
        if root and root.winfo_exists():
            root.after(0, lambda: _update_ui_success(version_pip, latest_version, python_name))
    
    def _update_ui_success(version_pip, latest_version, python_name):
        # 成功获取版本后隐藏重试按钮
        safe_grid_forget(pip_retry_button)
        
        if version_pip == latest_version:
            # 已是最新版本
            safe_config(pip_upgrade_button, 
                text=f"Pip is up to date({python_name}, Ver:{version_pip})",
                state="disabled"
            )
            try:
                with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                    fw.write("False\n")
                    fw.write(version_pip)
            except Exception as e:
                logger.error(f"写入pip更新标志失败: {e}")
        else:
            # 有新版本可用
            safe_config(pip_upgrade_button, 
                text=f"New version available({python_name}:{version_pip}-->{latest_version})"
            )
            
            # 根据其他按钮状态决定是否启用
            button_state = "normal"
            if install_button is not None and uninstall_button is not None:
                if "disabled" in install_button.state() and "disabled" in uninstall_button.state(): 
                    button_state = "disabled"
            
            safe_config(pip_upgrade_button, state=button_state)
            
            try:
                with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                    fw.write("True\n")
                    fw.write(version_pip)
            except Exception as e:
                logger.error(f"写入pip更新标志失败: {e}")
    
    # 启动后台线程进行检查
    threading.Thread(target=check_pip_version_thread, daemon=True).start()

def retry_pip(pip_retry_button, show_pip_version_func):
    """Retry checking pip version"""
    # 获取根窗口
    root = tk._default_root
    if root and root.winfo_exists():
        # 在主线程中隐藏重试按钮
        root.after(0, lambda: safe_grid_forget(pip_retry_button))
        
        # 调用检查函数
        root.after(100, show_pip_version_func)
    else:
        logger.error("重试时无法获取有效的根窗口")

def update_pip_versions_ui(config_path, pip_version_combobox):
    """更新pip版本选择界面，与Python版本调用方式一致"""
    try:
        if pip_version_combobox.get() == get_text("loading_versions"):
            return
            
        pip_version_combobox.config(values=[get_text("loading_versions")], state="disabled")
        
        def load_thread():
            try:
                # 获取Python版本及对应pip路径
                python_versions = get_python_versions()
                valid_pip_versions = []
                
                for py_version in python_versions:
                    try:
                        # 尝试使用python -m pip方式获取版本
                        result = subprocess.run(
                            ["python" + py_version.replace(".", ""), "-m", "pip", "--version"],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        if result.returncode == 0:
                            pip_version = result.stdout.strip().split()[1]
                            valid_pip_versions.append(f"pip{py_version} (v{pip_version})")
                            continue
                            
                        # 如果上面失败，尝试直接使用pip命令
                        pip_cmd = f"pip{py_version.replace('.', '')}"
                        result = subprocess.run(
                            [pip_cmd, "--version"],
                            capture_output=True,
                            text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        if result.returncode == 0:
                            pip_version = result.stdout.strip().split()[1]
                            valid_pip_versions.append(f"pip{py_version} (v{pip_version})")
                            
                    except Exception as e:
                        logger.debug(f"检查Python {py_version} 的pip版本失败: {e}")
                        continue
                
                def update_ui():
                    try:
                        if not valid_pip_versions:
                            pip_version_combobox.config(
                                values=[get_text("no_pip_versions_found")],
                                state="disabled"
                            )
                        else:
                            pip_version_combobox.config(values=valid_pip_versions, state="readonly")
                            # 保持当前选择
                            current = pip_version_combobox.get()
                            if current in valid_pip_versions:
                                pip_version_combobox.set(current)
                            elif valid_pip_versions:
                                pip_version_combobox.set(valid_pip_versions[0])
                    except Exception as e:
                        logger.error(f"更新pip版本UI失败: {e}")
                
                # 在主线程中更新UI
                if tk._default_root and tk._default_root.winfo_exists():
                    tk._default_root.after(0, update_ui)
                    
            except Exception as e:
                logger.error(f"加载pip版本失败: {e}")
                if tk._default_root and tk._default_root.winfo_exists():
                    tk._default_root.after(0, lambda: pip_version_combobox.config(
                        values=[get_text("load_pip_versions_failed")],
                        state="disabled"
                    ))
                    
        # 启动加载线程
        threading.Thread(target=load_thread, daemon=True).start()
        
    except Exception as e:
        logger.error(f"更新pip版本选择界面失败: {e}")

def get_text(key):
    """获取语言文本"""
    try:
        from lang import get_text
        return get_text(key)
    except Exception:
        # 如果导入失败，返回默认文本
        default_texts = {
            "loading_versions": "Loading versions...",
            "no_pip_versions_found": "No pip versions found",
            "load_pip_versions_failed": "Failed to load pip versions"
        }
        return default_texts.get(key, key)
