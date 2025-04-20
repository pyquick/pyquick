import os
import sys
import threading
import subprocess
import time
import tkinter as tk

# Import local logger
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import get_logger, LogPerformance

logger = get_logger()

def check_package_upgradeable(package_name, config_path):
    """
    Check if a package can be upgraded
    
    Returns:
        tuple: (can_upgrade, current_version, latest_version, package_name) or None if error
    """
    from pip.install_uninstall import get_pip_command_version
    
    if not package_name or package_name == "":
        return None
        
    pip_cmd = get_pip_command_version(config_path)
    if not pip_cmd:
        logger.error("Failed to determine pip command")
        return None
        
    try:
        # Check if package is installed
        find_packages = subprocess.run(
            [pip_cmd, "show", package_name], 
            text=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if f"WARNING: Package(s) not found: {package_name}" in find_packages.stderr:
            return None
            
        # Get current version
        try:
            current_version = find_packages.stdout.split("\n")[1].split(": ")[1]
        except (IndexError, KeyError):
            logger.error(f"Error parsing current version for {package_name}")
            return None
            
        # Check if upgrade is available
        check_upgradeable = subprocess.run(
            [pip_cmd, "install", "--upgrade", "--dry-run", package_name], 
            text=True,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if "Would install" not in check_upgradeable.stdout:
            return (False, current_version, current_version, package_name)
            
        try:
            # Get package name and latest version from output
            latest_version = check_upgradeable.stdout.split("\n")[-2].split("-")[1]
            package_true_name = check_upgradeable.stdout.split("\n")[-2].split("-")[0].split(" ")[-1]
            
            if current_version == latest_version:
                return (False, current_version, latest_version, package_true_name)
            else:
                return (True, current_version, latest_version, package_true_name)
                
        except (IndexError, KeyError):
            logger.error(f"Error parsing latest version for {package_name}")
            return None
    except Exception as e:
        logger.error(f"Error checking upgradeable status: {e}")
        return None

def upgrade_package(package_name, config_path, package_status_label, pip_progress_bar, 
                   upgrade_button, pip_upgrade_button, package_entry, install_button, 
                   uninstall_button, root):
    """Upgrade specified Python package"""
    from pip.install_uninstall import get_pip_command_version
    
    # 安全地在主线程中执行清除状态标签的函数
    def clear_status():
        if root and root.winfo_exists():
            try:
                package_status_label.config(text="")
            except Exception as e:
                logger.error(f"清除状态标签失败: {e}")
    
    # 获取pip命令
    pip_cmd = get_pip_command_version(config_path)
    if not pip_cmd:
        # 在主线程中更新UI
        if root and root.winfo_exists():
            root.after(0, lambda: update_ui_for_pip_command_error())
        return
    
    # 当pip命令获取失败时更新UI
    def update_ui_for_pip_command_error():
        try:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text="Failed to determine pip command version")
            package_entry.config(state="normal")
            install_button.config(state="normal")
            uninstall_button.config(state="normal")
            upgrade_button.grid_forget()
            root.after(5000, clear_status)
        except Exception as e:
            logger.error(f"更新UI显示pip命令错误失败: {e}")
    
    # 升级包的工作线程
    def upgrade_package_thread():
        package_status = None
        output_text = None
        error_text = None
        success = False
        
        try:
            with LogPerformance(logger, f"Upgrading package {package_name}"):
                # Check if package is installed
                find_packages = subprocess.run(
                    [pip_cmd, "show", package_name], 
                    text=True,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if f"WARNING: Package(s) not found: {package_name}" in find_packages.stderr:
                    package_status = f"Package '{package_name}' is not installed."
                    logger.info(f"Package '{package_name}' is not installed")
                    return
                
                # Perform upgrade
                result = subprocess.run(
                    [pip_cmd, "install", "--upgrade", package_name], 
                    capture_output=True,
                    text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                output_text = result.stdout
                error_text = result.stderr
                
                if "Successfully installed" in result.stdout:
                    package_status = f"Package '{package_name}' has been upgraded successfully!"
                    logger.info(f"Package '{package_name}' upgraded successfully")
                    success = True
                elif f"Requirement already satisfied: {package_name}" in result.stdout:
                    package_status = f"Package '{package_name}' is already up to date."
                    logger.info(f"Package '{package_name}' is already up to date")
                    success = True
                else:
                    package_status = f"Error upgrading package '{package_name}': {result.stderr}"
                    logger.error(f"Error upgrading package '{package_name}': {result.stderr}")
        except Exception as e:
            package_status = f"Error upgrading package '{package_name}': {str(e)}"
            logger.error(f"Exception upgrading package '{package_name}': {e}")
        
        # 在主线程中更新UI
        if root and root.winfo_exists():
            root.after(0, lambda: update_ui_with_result(package_status, success))
    
    # 更新UI显示升级结果
    def update_ui_with_result(status_text, success):
        try:
            pip_progress_bar.stop()
            pip_progress_bar.grid_forget()
            package_status_label.config(text=status_text)
            upgrade_button.grid_forget()
            package_entry.config(state="normal")
            install_button.config(state="normal")
            uninstall_button.config(state="normal")
            root.after(5000, clear_status)
        except Exception as e:
            logger.error(f"更新UI显示升级结果失败: {e}")
    
    # 首先在主线程中禁用UI元素
    if root and root.winfo_exists():
        root.after(0, lambda: disable_ui_before_upgrade())
    
    # 禁用UI元素
    def disable_ui_before_upgrade():
        try:
            package_entry.config(state="disabled")
            install_button.config(state="disabled")
            uninstall_button.config(state="disabled")
            upgrade_button.config(state="disabled")
            pip_progress_bar.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
            pip_progress_bar.start(10)
        except Exception as e:
            logger.error(f"禁用UI元素失败: {e}")
    
    # 启动升级线程
    threading.Thread(target=upgrade_package_thread, daemon=True).start()
    
def monitor_package_version(package_entry, upgrade_button, install_button, 
                          uninstall_button, config_path):
    """Monitor package entry field for upgradeable packages"""
    def check_upgradeable_thread():
        last_package_name = ""
        
        while True:
            try:
                # 获取根窗口
                root = tk._default_root
                if not root or not root.winfo_exists():
                    # 如果没有有效的根窗口，休眠后重试
                    time.sleep(0.5)
                    continue
                
                # 安全地获取当前包名
                package_name = ""
                root.after(0, lambda: get_package_name())
                time.sleep(0.1)  # 给一点时间让上面的操作完成
                
                # 用于在主线程中获取包名的函数
                def get_package_name():
                    nonlocal package_name
                    try:
                        package_name = package_entry.get()
                    except Exception as e:
                        logger.error(f"获取包名失败: {e}")
                        package_name = ""
                
                # 如果包名为空或与上次相同，则跳过检查
                if not package_name or package_name == last_package_name:
                    # 隐藏升级按钮
                    if package_name == "":
                        root.after(0, lambda: hide_upgrade_button())
                    time.sleep(0.3)
                    continue
                
                # 存储当前包名以便检测变化
                current_package = package_name
                last_package_name = current_package
                
                # 检查包是否可升级
                upgrade_info = check_package_upgradeable(package_name, config_path)
                
                # 在主线程中更新UI
                if root and root.winfo_exists():
                    root.after(0, lambda: update_upgrade_button(upgrade_info, current_package))
                
                # 等待一段时间再进行下一次检查
                time.sleep(0.3)
            except Exception as e:
                logger.error(f"检查包可升级状态失败: {e}")
                time.sleep(0.5)  # 出错后等待更长时间
    
    # 隐藏升级按钮
    def hide_upgrade_button():
        try:
            upgrade_button.grid_forget()
        except Exception as e:
            logger.error(f"隐藏升级按钮失败: {e}")
    
    # 更新升级按钮
    def update_upgrade_button(upgrade_info, current_package):
        try:
            # 如果包名已经改变，忽略结果
            if current_package != package_entry.get():
                upgrade_button.grid_forget()
                return
                
            if upgrade_info and upgrade_info[0]:  # 可升级
                current_version, latest_version, package_true_name = upgrade_info[1], upgrade_info[2], upgrade_info[3]
                upgrade_button.grid(row=5, column=0, columnspan=3, pady=10, padx=10)
                upgrade_button.config(
                    state="normal",
                    text=f"Upgrade Package: {package_true_name} ({current_version} -> {latest_version})"
                )
            else:
                upgrade_button.grid_forget()
        except Exception as e:
            logger.error(f"更新升级按钮失败: {e}")
    
    # 启动监控线程
    thread = threading.Thread(target=check_upgradeable_thread, daemon=True)
    thread.start()
    return thread
