import subprocess
import requests
import logging
import threading
import importlib
import sys
import tkinter as tk
from tkinter import ttk

# 全局变量，用于UI引用
package_label = None
root = None
install_button = None
pip_upgrade_button = None
uninstall_button = None
package_entry = None

def init_ui_references(root_window, pkg_label, install_btn, upgrade_btn, uninstall_btn, pkg_entry):
    """初始化UI引用"""
    global package_label, root, install_button, pip_upgrade_button, uninstall_button, package_entry
    package_label = pkg_label
    root = root_window
    install_button = install_btn
    pip_upgrade_button = upgrade_btn
    uninstall_button = uninstall_btn
    package_entry = pkg_entry

def clear_status():
    """清除状态标签"""
    package_label.config(text="")

def disabled_pip():
    """禁用pip相关界面元素"""
    install_button.config(state="disabled")
    pip_upgrade_button.config(state="disabled")
    uninstall_button.config(state="disabled")
    package_entry.config(state="disabled")

def return_pip():
    """恢复pip相关界面元素"""
    install_button.config(state="normal")
    pip_upgrade_button.config(state="normal")
    uninstall_button.config(state="normal")
    package_entry.config(state="normal")

def get_current_pip_version():
    """获取当前pip版本"""
    try:
        result = subprocess.check_output(["python3", "-m", "pip", "--version"])
        version_str = result.decode().strip().split()[1]
        return version_str
    except Exception as e:
        logging.error(f"Error getting pip version: {e}")
        return "Unknown"

def get_latest_pip_version():
    """获取最新pip版本"""
    try:
        response = requests.get("https://pypi.org/pypi/pip/json", verify=False)
        data = response.json()
        version_str = data["info"]["version"]
        return version_str
    except Exception as e:
        logging.error(f"Error getting latest pip version: {e}")
        return "Unknown"

def upgrade_pip():
    """升级pip"""
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
                    result = subprocess.run(["pip3", "install", "--upgrade", "pip", "--break-system-packages"], text=True, capture_output=True)
                    if "Successfully installed" in result.stdout:
                        package_label.config(text=f"Pip has been upgraded to v{latest_version}.")
                except subprocess.CalledProcessError as e:
                    package_label.config(text=f"Error upgrading pip: {e.output}")
        except Exception as e:
            logging.error(f"Error upgrading pip: {e}")
            package_label.config(text=f"Error upgrading pip: {str(e)}")
        return_pip()
        root.after(3000, clear_status)
    
    upgrade_thread = threading.Thread(target=upgrade_pip_thread, daemon=True)
    upgrade_thread.start()

def install_package_thread(package_name):
    """安装包的线程函数"""
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
        package_label.config(text=f"Error running pip command: {e.output}")
    except Exception as e:
        package_label.config(text=f"Error installing package '{package_name}': {str(e)}")
    return_pip()
    root.after(3000, clear_status)

def install_package():
    """安装包的主函数"""
    package_name = package_entry.get()
    install_thread = threading.Thread(target=install_package_thread, args=(package_name,), daemon=True)
    install_thread.start()

def uninstall_package():
    """卸载包的主函数"""
    package_name = package_entry.get()
    
    def uninstall_package_thread():
        disabled_pip()
        try:
            installed_packages = subprocess.check_output(["python3", "-m", "pip", "list", "--format=columns"], text=True)
            if package_name.lower() in installed_packages.lower():
                result = subprocess.run(["python3", "-m", "pip", "uninstall", "-y", package_name], capture_output=True, text=True)
                if "Successfully uninstalled" in result.stdout:
                    package_label.config(text=f"Package '{package_name}' has been uninstalled successfully!")
                else:
                    package_label.config(text=f"Cannot uninstall package '{package_name}': {result.stderr}")
            else:
                package_label.config(text=f"Package '{package_name}' is not installed.")
        except Exception as e:
            package_label.config(text=f"Error uninstalling package '{package_name}': {str(e)}")
        return_pip()
        root.after(3000, clear_status)
    
    uninstall_thread = threading.Thread(target=uninstall_package_thread, daemon=True)
    uninstall_thread.start()

def install_required_package(package):
    """自动安装必需的依赖包"""
    try:
        importlib.import_module(package)
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            logging.error(f"Failed to install {package}")
            return False
    return True 