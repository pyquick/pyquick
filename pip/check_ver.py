import os
import sys
import threading
import subprocess
import requests
import time
import logging

# Import local logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger
# and a
logger = get_logger()

def get_pip_version(config_path):
    """Get current pip version directly from the Python environment"""
    try:
        # 方法1: 直接通过python -m pip --version
        try:
            result = subprocess.run(["python", "-m", "pip", "--version"], 
                                  capture_output=True, 
                                  text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                version = result.stdout.strip().split()[1]
                logger.info(f"通过python -m pip获取到版本: {version}")
                return version
        except Exception as e:
            logger.warning(f"通过python -m pip获取版本失败: {e}")
        
        # 方法2: 使用pip.exe --version
        try:
            result = subprocess.run(["pip", "--version"], 
                                  capture_output=True, 
                                  text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                version = result.stdout.strip().split()[1]
                logger.info(f"通过pip获取到版本: {version}")
                return version
        except Exception as e:
            logger.warning(f"通过pip获取版本失败: {e}")
            
        # 如果以上方法都失败，表示无法获取版本
        logger.error("无法获取pip版本")
        return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"获取pip版本过程出错: {e}")
        return None
    except FileNotFoundError as e:
        logger.error(f"未找到pip可执行文件: {e}")
        return None
    except Exception as e:
        logger.error(f"获取pip版本时发生未知错误: {e}")
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
    with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
        fw.write("True")
        fw.write("\n")

    def thread():
        # 使用root对象的after方法在主线程中更新GUI
        import tkinter as tk
        root = tk._default_root  # 获取默认根窗口

        # 在主线程中更新GUI
        root.after(0, lambda: pip_upgrade_button.config(text="Checking...", state="disabled"))
        try:
            # 获取当前pip版本
            version_pip = get_pip_version(config_path)
            if not version_pip:
                raise Exception("无法获取pip版本")
                
            # 获取Python版本信息
            python_version = sys.version.split()[0]  # 如 "3.10.0"
            python_name = f"Python {python_version}"
            
            # 获取最新pip版本
            latest_version = get_latest_pip_version()
            if not latest_version:
                raise Exception("无法获取最新pip版本")
            
            # 成功获取版本后隐藏重试按钮
            root.after(0, lambda: pip_retry_button.grid_forget())
            
            if version_pip == latest_version:
                # 使用root.after在主线程中更新GUI
                root.after(0, lambda: pip_upgrade_button.config(text=f"Pip is up to date({python_name}, Ver:{version_pip})", state="disabled"))
                with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                    fw.write("False")
                    fw.write("\n")
            else:
                # 将状态更新放在主线程中执行
                def update_pip_button():
                    pip_upgrade_button.config(text=f"New version available({python_name}:{version_pip}-->{latest_version})")
                    if "disabled" in install_button.state() and "disabled" in uninstall_button.state(): 
                        pip_upgrade_button.config(state="disabled")
                    elif install_button.state() == () or uninstall_button.state() == ():
                        pip_upgrade_button.config(state="normal")
                
                root.after(0, update_pip_button)
                with open(os.path.join(config_path, "allowupdatepip.txt"), "w") as fw:
                    fw.write("False")
                    fw.write("\n")
                    
            # 确保成功后不可见重试按钮
            root.after(0, lambda: pip_retry_button.grid_forget())
            
        except Exception as e:
            logger.error(f"Failed to get pip version: {e}")
            
            # 使用root.after在主线程中更新GUI
            def handle_error():
                pip_upgrade_button.config(text=f"Failed to get pip version", state="disabled")
                pip_retry_button.grid(row=1, column=0, columnspan=3, pady=10, padx=10)
            
            root.after(0, handle_error)
            return "error"
    
    while True:
        # 使用写入标志文件的方式来控制更新逻辑
        with open(os.path.join(config_path, "allowupdatepip.txt"), "r") as rw:
            a = rw.readline()
            allow = str(a).strip("\n")
        
        if allow == "True":
            a = threading.Thread(target=thread, daemon=True)
            a.start()
            a.join()
            time.sleep(1)
        
        with open(os.path.join(config_path, "allowupdatepip.txt"), "r") as rw:
            a = rw.readline()
            allow = str(a).strip("\n")
        
        if allow == "False":
            # 只需等待标志变化，不再检测版本变化
            time.sleep(0.1)

def retry_pip(pip_retry_button, show_pip_version_func):
    """Retry checking pip version"""
    pip_retry_button.grid_forget()
    threading.Thread(target=show_pip_version_func, daemon=True).start()
